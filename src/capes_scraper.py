"""
Scraper e extrator de metadados para o Portal de Periódicos CAPES (MEC/CAPES).
Baseado na arquitetura do periodicos-capes-mcp, adaptado nativamente para Python
e integrado ao ecossistema do AcademicOmniSearch com suporte a Zyte API, Qualis e OpenAlex.
"""

from typing import List, Dict, Any, Optional
import os
import re
import time
import base64
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

from src.base import BaseScraper, AcademicRecord
from src.qualis_service import QualisService
from src.openalex_service import OpenAlexService
from utils.config import DEFAULT_HEADERS, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


class CapesScraper(BaseScraper):
    """
    Coletor para o Portal de Periódicos CAPES (https://www.periodicos.capes.gov.br).
    Suporta busca direta via HTTP e bypass de WAF via Zyte API (quando ZYTE_API_KEY estiver configurada).
    Enriquece automaticamente os registros com Qualis (via SQLite local) e cienciometria OpenAlex (via API pública).
    """

    BASE_URL = "https://www.periodicos.capes.gov.br/index.php/acervo/buscador.html"
    DETAIL_URL_PATTERN = "https://www.periodicos.capes.gov.br/index.php/acervo/buscador.html?task=detalhes&source=all&id={}"

    # Mapeamento amigável de campos para qualificadores de busca do Portal CAPES
    FIELD_MAP = {
        "todos": "all",
        "all": "all",
        "título": "title",
        "titulo": "title",
        "title": "title",
        "autores": "author",
        "autor": "author",
        "author": "author",
        "resumo": "abstract",
        "abstract": "abstract",
        "assunto": "subject",
        "palavras-chave": "subject",
        "keywords": "subject",
        "texto completo": "all",
    }

    def __init__(
        self,
        max_por_base: Optional[int] = None,
        page_size: Optional[int] = None,
        zyte_api_key: Optional[str] = None,
        proxy: Optional[str] = None,
        qualis_db_path: Optional[str] = None,
    ):
        super().__init__(name="Periódicos CAPES", is_api=False, requires_auth=False)
        self.page_size = max_por_base or page_size or 20
        self.max_por_base = self.page_size
        self.zyte_api_key = zyte_api_key or os.getenv("ZYTE_API_KEY", "")
        self.proxy = proxy or os.getenv("CAPES_PROXY") or os.getenv("HTTPS_PROXY")
        self.qualis_service = QualisService.get_instance(qualis_db_path)

        # Configuração de sessão HTTP com headers compatíveis com CloudFront
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.periodicos.capes.gov.br/",
            "Sec-Ch-Ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
        })
        if self.proxy:
            self.session.proxies = {"http": self.proxy, "https": self.proxy}

    def _fetch_page(self, url: str, max_retries: int = 3) -> str:
        """
        Recupera o HTML da URL informada.
        Prioriza Zyte API se ZYTE_API_KEY estiver configurada; caso contrário, faz requisição direta via requests.
        """
        if self.zyte_api_key:
            return self._fetch_with_zyte(url, max_retries=max_retries)

        # Requisição direta via requests.Session
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.get(url, timeout=DEFAULT_TIMEOUT)
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code in (403, 520, 503):
                    msg = (
                        f"Acesso bloqueado por WAF/CloudFront (HTTP {resp.status_code}). "
                        "Dica: Configure ZYTE_API_KEY em .env ou secrets para bypass automático de proteções."
                    )
                    self.log(msg, level="WARNING")
                    if attempt < max_retries:
                        time.sleep(2 * attempt)
                        continue
                    raise requests.HTTPError(msg, response=resp)
                else:
                    resp.raise_for_status()
            except Exception as e:
                if attempt == max_retries:
                    self.log(f"Falha ao acessar {url}: {e}", level="ERROR")
                    raise e
                time.sleep(1.5 * attempt)

        return ""

    def _fetch_with_zyte(self, target_url: str, max_retries: int = 3) -> str:
        """Consome o endpoint /v1/extract da Zyte API para contornar CloudFront/WAF."""
        auth_bytes = f"{self.zyte_api_key}:".encode("utf-8")
        auth_header = f"Basic {base64.b64encode(auth_bytes).decode('ascii')}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_header,
        }
        payload = {
            "url": target_url,
            "httpResponseBody": True,
        }

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.post(
                    "https://api.zyte.com/v1/extract",
                    headers=headers,
                    json=payload,
                    timeout=45,
                )
                if resp.status_code == 520:
                    wait_time = min(2 ** (attempt - 1), 30)
                    self.log(f"Zyte HTTP 520 (ban temporário) - Tentativa {attempt}/{max_retries} após {wait_time}s", level="WARNING")
                    time.sleep(wait_time)
                    continue

                resp.raise_for_status()
                data = resp.json()
                body_b64 = data.get("httpResponseBody", "")
                return base64.b64decode(body_b64).decode("utf-8", errors="replace")
            except Exception as e:
                if attempt >= max_retries:
                    self.log(f"Zyte API falhou definitivamente para {target_url}: {e}", level="ERROR")
                    raise e
                time.sleep(2 * attempt)

        return ""

    def construct_search_url(
        self,
        query: str,
        year_start: int,
        year_end: int,
        field: str = "Todos",
        page: int = 1,
        document_types: Optional[List[str]] = None,
        open_access_only: Optional[bool] = None,
        peer_reviewed_only: Optional[bool] = None,
        languages: Optional[List[str]] = None,
    ) -> str:
        """Monta a URL completa de busca para o portal CAPES com parâmetros compatíveis."""
        field_scope = self.FIELD_MAP.get(field.strip().lower(), "all")

        # Formata a query no padrão all:contains(...) ou com operadores booleanos
        clean_query = query.strip()
        parts = re.split(r"\b(AND|OR|NOT)\b", clean_query, flags=re.IGNORECASE)
        query_elements = []
        for part in parts:
            item = part.strip()
            if not item:
                continue
            if item.upper() in ("AND", "OR", "NOT"):
                query_elements.append(item.upper())
            else:
                query_elements.append(f"{field_scope}:contains({item})")

        formatted_query = " ".join(query_elements) if query_elements else clean_query

        # Monta parâmetros de query
        params = [
            ("q", formatted_query),
            ("source", "all"),
            ("mode", "advanced"),
        ]

        if page > 1:
            params.append(("page", str(page)))

        if year_start:
            params.append(("publishyear_min[]", str(year_start)))
        if year_end:
            params.append(("publishyear_max[]", str(year_end)))

        if document_types:
            for dt in document_types:
                params.append(("type[]", f"type=={dt}"))

        if open_access_only is True:
            params.append(("open_access[]", "open_access==1"))
        elif open_access_only is False:
            params.append(("open_access[]", "open_access==0"))

        if peer_reviewed_only is True:
            params.append(("peer_reviewed[]", "peer_reviewed==1"))
        elif peer_reviewed_only is False:
            params.append(("peer_reviewed[]", "peer_reviewed==0"))

        if languages:
            for lang in languages:
                params.append(("language[]", f"language=={lang}"))

        req = requests.models.PreparedRequest()
        req.prepare_url(self.BASE_URL, params)
        return req.url

    def _extract_article_id(self, url: str) -> Optional[str]:
        match = re.search(r"id=([A-Z0-9]+)", url)
        return match.group(1) if match else None

    def _extract_doi(self, text: str) -> Optional[str]:
        if not text:
            return None
        match = re.search(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b", text)
        return match.group(1) if match else None

    def parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """Extrai a lista de itens da página de resultados de busca."""
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        items = soup.select(".result-busca")
        results = []

        for section in items:
            try:
                title_elem = section.select_one(".titulo-busca")
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")
                if href.startswith("http"):
                    detail_url = href
                else:
                    detail_url = f"https://www.periodicos.capes.gov.br{href}"

                article_id = self._extract_article_id(detail_url)

                # Extrai autores
                authors = [
                    a.get_text(strip=True)
                    for a in section.select("a.view-autor")
                    if a.get_text(strip=True)
                ]

                # Extrai dados do parágrafo text-down-01 (Ano, Editora, Periódico)
                journal = ""
                publisher = ""
                year = ""
                for p in section.select("p.text-down-01"):
                    text = p.get_text(" ", strip=True)
                    if "|" in text:
                        parts = text.split("|")
                        if len(parts) >= 2:
                            journal = parts[1].strip()
                            left_side = parts[0]
                            # Tenta ano no início (ex: "2024 - Elsevier BV")
                            year_match = re.search(r"\b(19\d\d|20\d\d)\b", left_side)
                            if year_match:
                                year = year_match.group(1)
                            if "-" in left_side:
                                publisher = left_side.split("-", 1)[1].strip()

                # Tipo de documento
                doc_type_el = section.select_one(".fw-semibold")
                doc_type = doc_type_el.get_text(strip=True) if doc_type_el else "Artigo"

                # Flags
                is_oa = bool(
                    section.select(".text-green-cool-vivid-50, .open-access, [title*='open access']")
                    or "open access" in section.get_text().lower()
                    or "acesso aberto" in section.get_text().lower()
                )
                is_peer = bool(
                    section.select(".text-violet-50, .peer-reviewed, [title*='peer']")
                    or "peer" in section.get_text().lower()
                    or "revisado por pares" in section.get_text().lower()
                )

                results.append({
                    "title": title,
                    "detail_url": detail_url,
                    "article_id": article_id,
                    "authors": authors,
                    "journal": journal,
                    "publisher": publisher,
                    "year": year,
                    "document_type": doc_type,
                    "is_open_access": is_oa,
                    "is_peer_reviewed": is_peer,
                })
            except Exception as e:
                logger.debug(f"Erro ao processar item do resultado CAPES: {e}")

        return results

    def scrape_article_detail(self, detail_url: str) -> Dict[str, Any]:
        """
        Acessa a página de detalhes de uma publicação para extrair metadados aprofundados
        (Resumo, ISSN, DOI, Volume, Idioma, etc.).
        """
        try:
            html = self._fetch_page(detail_url)
            if not html:
                return {}

            soup = BeautifulSoup(html, "html.parser")
            details: Dict[str, Any] = {}

            # 1. Extração estruturada da tabela de propriedades (<tr><th>Campo</th><td>Valor</td></tr>)
            for tr in soup.select("table tr, tr"):
                th = tr.find(["th", "td"])
                td = th.find_next_sibling(["td", "th"]) if th else None
                if th and td:
                    label = th.get_text(strip=True).rstrip(":")
                    val = td.get_text(" ", strip=True)
                    if label and val:
                        details[label] = val

            # 2. Resumo
            abstract_el = soup.select_one("#item-resumo") or soup.find("meta", {"name": "abstract"})
            if abstract_el:
                details["abstract"] = (
                    abstract_el.get("content", "").strip()
                    if abstract_el.name == "meta"
                    else abstract_el.get_text(strip=True)
                )

            # 3. Autores na página de detalhes (se houver)
            authors_detail = [
                a.get_text(strip=True)
                for a in soup.select("a.view-autor")
                if a.get_text(strip=True)
            ]
            if authors_detail:
                details["authors_detail"] = authors_detail

            # 4. DOI direto
            doi_link = soup.select_one('a[href*="doi.org"]')
            if doi_link:
                details["doi"] = self._extract_doi(doi_link.get("href", ""))
            elif "DOI" in details:
                details["doi"] = self._extract_doi(details["DOI"])

            # 5. ISSN
            if "ISSN" in details:
                details["issn"] = details["ISSN"]
            else:
                issn_match = re.search(r"\b(\d{4}-?\d{3}[\dXx])\b", html)
                if issn_match:
                    details["issn"] = issn_match.group(1)

            # 6. Ano
            if "Ano" in details and re.match(r"^\d{4}$", details["Ano"]):
                details["year"] = details["Ano"]
            elif "#item-ano" in html:
                ano_el = soup.select_one("#item-ano")
                if ano_el:
                    m = re.search(r"\d{4}", ano_el.get_text())
                    if m:
                        details["year"] = m.group(0)

            return details
        except Exception as e:
            logger.debug(f"Falha ao extrair detalhes de {detail_url}: {e}")
            return {}

    def search(
        self,
        query: str,
        year_start: int,
        year_end: int,
        field: str = "Todos",
        max_results: Optional[int] = None,
        max_por_base: Optional[int] = None,
        fetch_details: Optional[bool] = None,
        include_metrics: bool = True,
        max_workers: int = 4,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Executa a pesquisa no Portal CAPES, paginação se necessário, extração de detalhes
        e enriquecimento com Qualis e OpenAlex.
        """
        self.logs = []
        self.validate_years(year_start, year_end)

        if not query or not query.strip():
            self.last_status = "Consulta vazia"
            return []

        # Se fetch_details não for especificado, ativa apenas se houver Zyte API configurada,
        # evitando o envio de dezenas de requisições concorrentes que ativam o WAF/CloudFront (HTTP 403)
        if fetch_details is None:
            fetch_details = bool(self.zyte_api_key)

        limit = max_por_base if max_por_base is not None else (max_results or self.max_por_base)
        limit = max(1, int(limit))

        self.log(f"Iniciando busca por '{query}' no período {year_start}-{year_end} (limite: {limit})")

        all_listings: List[Dict[str, Any]] = []
        page = 1
        items_per_page = 30
        max_pages = (limit + items_per_page - 1) // items_per_page

        while len(all_listings) < limit and page <= max_pages:
            search_url = self.construct_search_url(
                query=query,
                year_start=year_start,
                year_end=year_end,
                field=field,
                page=page,
                document_types=kwargs.get("document_types"),
                open_access_only=kwargs.get("open_access_only"),
                peer_reviewed_only=kwargs.get("peer_reviewed_only"),
                languages=kwargs.get("languages"),
            )

            try:
                html = self._fetch_page(search_url)
            except Exception as e:
                self.log(f"Interrompendo busca na página {page}: {e}", level="WARNING")
                if "403" in str(e) or "WAF" in str(e):
                    self.last_status = "Bloqueio WAF (CloudFront 403)"
                break

            page_items = self.parse_search_results(html)
            if not page_items:
                self.log(f"Nenhum item retornado na página {page}.")
                break

            all_listings.extend(page_items)
            self.log(f"Página {page}: {len(page_items)} itens encontrados.")
            page += 1

        target_items = all_listings[:limit]
        if not target_items:
            if not self.last_status or self.last_status == "Iniciando":
                self.last_status = "Nenhum resultado encontrado"
            return []

        # Fase de detalhes em paralelo (ThreadPoolExecutor) se fetch_details for ativado
        detailed_records = []
        if fetch_details:
            self.log(f"Extraindo metadados aprofundados para {len(target_items)} publicações...")

            def process_item(item: Dict[str, Any]) -> Dict[str, Any]:
                d = dict(item)
                if item.get("detail_url"):
                    det = self.scrape_article_detail(item["detail_url"])
                    d["resumo"] = det.get("abstract", "")
                    d["issn"] = det.get("issn", "")
                    if det.get("doi"):
                        d["doi"] = det["doi"]
                    if det.get("year"):
                        d["year"] = det["year"]
                    if det.get("Periódico"):
                        d["journal"] = det["Periódico"]
                    if det.get("Editora"):
                        d["publisher"] = det["Editora"]
                    if det.get("Volume (v.)"):
                        d["volume"] = det["Volume (v.)"]
                    if det.get("Tópico(s)"):
                        d["topicos"] = det["Tópico(s)"]
                    if det.get("authors_detail"):
                        d["authors"] = det["authors_detail"]
                return d

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(process_item, it): it for it in target_items}
                for fut in as_completed(futures):
                    try:
                        detailed_records.append(fut.result())
                    except Exception as ex:
                        detailed_records.append(futures[fut])
        else:
            detailed_records = target_items

        # Fase de enriquecimento: Qualis e OpenAlex
        if include_metrics:
            self._enrich_records(detailed_records)

        # Montagem dos registros padronizados AcademicRecord
        final_records: List[Dict[str, Any]] = []
        for it in detailed_records:
            authors_str = "; ".join(it.get("authors") or [])
            journal_or_pub = it.get("journal") or it.get("publisher") or "Portal CAPES"
            year_str = str(it.get("year") or "")
            doi_val = it.get("doi") or ""
            abstract_val = it.get("resumo") or ""
            keywords_val = it.get("topicos") or ""

            rec = AcademicRecord(
                title=it.get("title", ""),
                link_pub=it.get("detail_url", ""),
                autor=authors_str,
                revista_fonte=journal_or_pub,
                ano=year_str,
                base="Periódicos CAPES",
                resumo=abstract_val,
                palavras_chave=keywords_val,
                doi=doi_val,
                id_origem=it.get("article_id", ""),
            )

            rec_dict = rec.to_dict()

            # Metadados adicionais para análise cienciométrica no AcademicOmniSearch
            if it.get("issn"):
                rec_dict["ISSN"] = it["issn"]
            if it.get("qualis"):
                rec_dict["Qualis"] = it["qualis"]
            if it.get("qualis_area"):
                rec_dict["Qualis Área"] = it["qualis_area"]
            if it.get("cited_by_count") is not None:
                rec_dict["Citações (OpenAlex)"] = it["cited_by_count"]
            if it.get("fwci") is not None:
                rec_dict["FWCI"] = it["fwci"]
            if it.get("document_type"):
                rec_dict["Tipo Documento"] = it["document_type"]

            final_records.append(rec_dict)

        self.last_status = f"Sucesso ({len(final_records)} registros)"
        self.log(f"Busca finalizada com sucesso. {len(final_records)} publicações recuperadas.")
        return final_records

    def _enrich_records(self, items: List[Dict[str, Any]]) -> None:
        """Enriquece lista de itens in-place com dados de Qualis e OpenAlex."""
        # 1. Qualis por ISSN
        if self.qualis_service and self.qualis_service.is_available():
            qualis_count = 0
            for it in items:
                issn = it.get("issn")
                if issn:
                    q_info = self.qualis_service.get_qualis_by_issn(issn)
                    if q_info:
                        it["qualis"] = q_info.get("classification")
                        it["qualis_area"] = q_info.get("area")
                        qualis_count += 1
            if qualis_count > 0:
                self.log(f"Qualis: {qualis_count} registros enriquecidos com classificação da CAPES.")

        # 2. OpenAlex por DOI (em lote)
        dois_to_query = [it.get("doi") for it in items if it.get("doi")]
        if dois_to_query:
            try:
                metrics_map = OpenAlexService.get_metrics_by_dois(dois_to_query, session=self.session)
                oa_count = 0
                for it in items:
                    doi = it.get("doi")
                    if doi:
                        clean_d = doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "").lower()
                        metrics = metrics_map.get(clean_d)
                        if metrics:
                            it["cited_by_count"] = metrics.get("cited_by_count")
                            it["fwci"] = metrics.get("fwci")
                            oa_count += 1
                if oa_count > 0:
                    self.log(f"OpenAlex: {oa_count} publicações enriquecidas com métricas de citação e FWCI.")
            except Exception as e:
                self.log(f"Falha ao consultar métricas no OpenAlex: {e}", level="WARNING")

