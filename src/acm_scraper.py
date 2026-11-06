"""
Scraper para ACM Digital Library (https://dl.acm.org).
Suporta tanto extração de páginas salvas em HTML (como app.html)
quanto requisições web com tratamento de restrições de WAF/Cloudflare.
"""

from typing import List, Dict, Any, Optional
import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from src.base import BaseScraper, AcademicRecord
from utils.config import DEFAULT_HEADERS, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)

class AcmScraper(BaseScraper):
    """
    Extrator de metadados da ACM Digital Library.
    Capaz de processar dumps de HTML gerados pelo usuário/browser ou requisições HTTP.
    """

    BASE_URL = "https://dl.acm.org/action/doSearch"

    # Mapeamento de campos da busca avançada da ACM
    FIELD_MAP = {
        "todos": "AllField",
        "all": "AllField",
        "título": "Title",
        "titulo": "Title",
        "title": "Title",
        "palavras-chave": "Keyword",
        "keywords": "Keyword",
        "autores": "ContribAuthor",
        "author": "ContribAuthor",
        "resumo": "Abstract",
        "abstract": "Abstract",
        "texto completo": "FullText",
        "text": "FullText"
    }

    def __init__(self, local_html_path: Optional[str] = None):
        super().__init__(name="ACM Digital Library", is_api=False, requires_auth=False)
        if local_html_path:
            self.local_html_path = local_html_path
        elif os.path.exists("test/app.html"):
            self.local_html_path = "test/app.html"
        elif os.path.exists("app.html"):
            self.local_html_path = "app.html"
        else:
            self.local_html_path = None

    def parse_html(self, html_content: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Analisa o HTML de resultados da ACM Digital Library e extrai metadados padronizados.
        """
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, "html.parser")
        items = soup.select(".issue-item")
        records: List[Dict[str, Any]] = []

        for item in items:
            # 1. Título e Link
            title_tag = item.select_one(".issue-item__title a, .hlFld-Title a")
            title = title_tag.get_text(separator=" ", strip=True) if title_tag else "Sem título"
            
            rel_link = title_tag.get("href", "") if title_tag else ""
            if rel_link.startswith("/"):
                link_pub = f"https://dl.acm.org{rel_link}"
            elif rel_link.startswith("http"):
                link_pub = rel_link
            else:
                link_pub = f"https://dl.acm.org/{rel_link}" if rel_link else ""

            # Extração de DOI
            doi = ""
            doi_match = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", rel_link)
            if doi_match:
                doi = doi_match.group(0)

            # 2. Autores
            author_tags = item.select(".loa a span, .hlFld-ContribAuthor a span, .hlFld-ContribAuthor")
            authors_list: List[str] = []
            for at in author_tags:
                author_name = at.get_text(strip=True)
                if author_name and author_name not in authors_list:
                    authors_list.append(author_name)
            autor = "; ".join(authors_list) if authors_list else "Autor não informado"

            # 3. Revista / Conferência / Fonte
            detail_tag = item.select_one(".issue-item__detail")
            source = "ACM Digital Library"
            if detail_tag:
                conf_tag = detail_tag.select_one(".epub-section__title, a:not(.issue-item__doi)")
                if conf_tag:
                    source = conf_tag.get_text(strip=True)
                else:
                    detail_text = " ".join(detail_tag.get_text(separator=" ", strip=True).split())
                    if detail_text:
                        source = detail_text

            # 4. Ano de publicação
            pub_date_tag = item.select_one(".bookPubDate")
            date_attr = pub_date_tag.get("data-title", "") if pub_date_tag else ""
            date_text = pub_date_tag.get_text(strip=True) if pub_date_tag else ""
            
            year_match = re.search(r"\b(19\d{2}|20\d{2})\b", date_attr) or re.search(r"\b(19\d{2}|20\d{2})\b", date_text)
            if not year_match:
                # Fallback no bloco citation
                citation_tag = item.select_one(".issue-item__citation")
                if citation_tag:
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", citation_tag.get_text())

            ano = year_match.group(1) if year_match else "Não informado"

            # 5. Resumo (se disponível no snippet da busca)
            abstract_tag = item.select_one(".issue-item__abstract, .abstract p")
            resumo = " ".join(abstract_tag.get_text(separator=" ", strip=True).split()) if abstract_tag else ""

            record = AcademicRecord(
                title=title.strip(),
                link_pub=link_pub.strip(),
                autor=autor.strip(),
                revista_fonte=source.strip(),
                ano=ano.strip(),
                base=self.name,
                resumo=resumo,
                doi=doi,
                id_origem=doi or rel_link
            )
            records.append(record.to_dict())

            if len(records) >= max_results:
                break

        return records

    def parse_file(self, file_path: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Lê um arquivo HTML salvo e extrai os registros."""
        if not os.path.exists(file_path):
            logger.warning(f"Arquivo HTML '{file_path}' não encontrado.")
            return []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return self.parse_html(content, max_results=max_results)

    def search(
        self,
        query: str,
        year_start: int,
        year_end: int,
        field: str = "Todos",
        max_results: int = 50,
        use_local_file_if_blocked: bool = True,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Executa busca na ACM. Tenta requisição HTTP; caso o Cloudflare WAF bloqueie (HTTP 403),
        avisa e recorre ao arquivo local (ex: app.html) se configurado.
        """
        self.validate_years(year_start, year_end)

        if not query or not query.strip():
            return []

        field_param = self.FIELD_MAP.get(field.strip().lower(), "AllField")
        params = {
            field_param: query.strip(),
            "AfterYear": str(year_start),
            "BeforeYear": str(year_end)
        }

        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        session.headers.update({
            "Referer": "https://dl.acm.org/",
            "Sec-Ch-Ua": '"Chromium";v="125", "Not.A/Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin"
        })

        try:
            response = session.get(self.BASE_URL, params=params, timeout=DEFAULT_TIMEOUT)
            
            # Se a resposta contém resultados HTML
            if response.status_code == 200 and ".issue-item" in response.text:
                return self.parse_html(response.text, max_results=max_results)
            
            # Tratamento de proteção WAF / Cloudflare
            if response.status_code in [403, 503] or "cloudflare" in response.text.lower() or "challenge" in response.text.lower():
                logger.warning(
                    "ACM Digital Library ativou proteção WAF/Cloudflare (HTTP 403/503). "
                    "Para raspagem automatizada contínua da ACM, recomenda-se uso de Playwright "
                    "ou ingestão de dumps HTML salvos pelo pesquisador."
                )
                if use_local_file_if_blocked and self.local_html_path and os.path.exists(self.local_html_path):
                    logger.info(f"Carregando dump local de fallback '{self.local_html_path}'...")
                    return self.parse_file(self.local_html_path, max_results=max_results)
                
            return []

        except Exception as e:
            logger.error(f"Erro na requisição ACM: {e}")
            if use_local_file_if_blocked and self.local_html_path and os.path.exists(self.local_html_path):
                return self.parse_file(self.local_html_path, max_results=max_results)
            return []

