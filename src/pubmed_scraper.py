"""
Scraper / Cliente de API para a base PubMed (NCBI / National Library of Medicine).
Utiliza a API oficial gratuita NCBI E-utilities (esearch e esummary).
"""

from typing import List, Dict, Any, Optional
import os
import requests
import re
import time
import logging
from src.base import BaseScraper, AcademicRecord
from utils.config import DEFAULT_HEADERS, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)

class PubmedScraper(BaseScraper):
    """
    Cliente da API oficial NCBI E-utilities para PubMed.
    Não requer chaves de API pagas e segue as boas práticas do NCBI.
    """

    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    # Mapeamento de campos para qualificadores de busca do PubMed / MeSH
    FIELD_TAGS = {
        "todos": "",
        "all": "",
        "título": "[Title]",
        "titulo": "[Title]",
        "title": "[Title]",
        "resumo": "[Title/Abstract]",
        "abstract": "[Title/Abstract]",
        "palavras-chave": "[Title/Abstract]",
        "keywords": "[Title/Abstract]",
        "autores": "[Author]",
        "author": "[Author]",
        "texto completo": "[Text Word]",
        "text": "[Text Word]"
    }

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__(name="PubMed", is_api=True, requires_auth=False)
        self.email = email or os.getenv("PUBMED_EMAIL", "academicomnisearch@dev.local")
        self.api_key = api_key or os.getenv("NCBI_API_KEY", "")

    def _build_query_term(self, query: str, field: str, year_start: int, year_end: int) -> str:
        """Monta a query formatada com qualificadores do PubMed e janela de anos."""
        tag = self.FIELD_TAGS.get(field.strip().lower(), "")
        base_term = f'"{query.strip()}"{tag}' if tag else query.strip()
        
        # Filtro temporal oficial por data de publicação [pdat]
        date_filter = f'("{year_start}"[Date - Publication] : "{year_end}"[Date - Publication])'
        return f"{base_term} AND {date_filter}"

    def search(
        self,
        query: str,
        year_start: int,
        year_end: int,
        field: str = "Todos",
        max_results: int = 50,
        delay: float = 0.35,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Executa a busca no PubMed: primeiro recupera os PMIDs via esearch,
        depois obtém os metadados bibliográficos em lote via esummary.
        """
        self.validate_years(year_start, year_end)

        if not query or not query.strip():
            return []

        self.logs = []
        self.log(f"Iniciando busca PubMed com query: '{query}' (Janela: {year_start}-{year_end}, Campo: {field}, Limite: {max_results})")
        formatted_term = self._build_query_term(query, field, year_start, year_end)
        self.log(f"Expressão formatada MeSH: {formatted_term}")
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)

        # 1. Esearch para recuperar PMIDs
        esearch_params: Dict[str, Any] = {
            "db": "pubmed",
            "term": formatted_term,
            "retmode": "json",
            "retmax": min(max_results, 250),
            "tool": "AcademicOmniSearch",
            "email": self.email
        }
        if self.api_key:
            esearch_params["api_key"] = self.api_key

        try:
            self.log(f"Consultando esearch.fcgi...")
            r_search = session.get(self.ESEARCH_URL, params=esearch_params, timeout=DEFAULT_TIMEOUT)
            if r_search.status_code != 200:
                self.log(f"ERRO: esearch retornou HTTP {r_search.status_code}: {r_search.text[:200]}", level="ERROR")
                self.last_status = f"Erro HTTP {r_search.status_code}"
                return []

            search_json = r_search.json()
            id_list = search_json.get("esearchresult", {}).get("idlist", [])
            total_count = search_json.get("esearchresult", {}).get("count", 0)
            self.log(f"esearch retornou com sucesso: {total_count} artigos totais na base, {len(id_list)} IDs selecionados para sumário.")

            if not id_list:
                self.last_status = "0 registros encontrados"
                return []

            # 2. Esummary em lote (chunked)
            records: List[Dict[str, Any]] = []
            chunk_size = 50  # Lotes seguros para requisições GET

            for i in range(0, len(id_list), chunk_size):
                chunk = id_list[i : i + chunk_size]
                time.sleep(delay)  # Respeita o limite do NCBI (max 3 req/s)

                esummary_params: Dict[str, Any] = {
                    "db": "pubmed",
                    "id": ",".join(chunk),
                    "retmode": "json",
                    "tool": "AcademicOmniSearch",
                    "email": self.email
                }
                if self.api_key:
                    esummary_params["api_key"] = self.api_key

                self.log(f"Consultando esummary.fcgi para lote de {len(chunk)} PMIDs...")
                r_sum = session.get(self.ESUMMARY_URL, params=esummary_params, timeout=DEFAULT_TIMEOUT)
                if r_sum.status_code != 200:
                    self.log(f"AVISO: Falha no esummary para lote: HTTP {r_sum.status_code}", level="WARNING")
                    continue

                sum_data = r_sum.json().get("result", {})

                for pmid in chunk:
                    doc = sum_data.get(pmid)
                    if not doc:
                        continue

                    # Título
                    title = doc.get("title", "Sem título").rstrip(".")

                    # Link
                    link_pub = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                    # Autores
                    author_list = [a.get("name") for a in doc.get("authors", []) if a.get("name")]
                    autor = "; ".join(author_list) if author_list else "Autor não informado"

                    # Fonte / Revista
                    revista = doc.get("fulljournalname") or doc.get("source") or "PubMed Source"

                    # Ano
                    pubdate = doc.get("pubdate", "")
                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", pubdate)
                    ano = year_match.group(1) if year_match else "Não informado"

                    # Extração de DOI e PMCID (PMC Open Access)
                    doi = ""
                    pmcid = ""
                    for article_id in doc.get("articleids", []):
                        id_type = str(article_id.get("idtype", "")).lower()
                        if id_type == "doi" and not doi:
                            doi = article_id.get("value", "")
                        elif id_type == "pmc" and not pmcid:
                            pmcid = article_id.get("value", "")

                    # Prioriza acesso aberto no PMC se disponível, senão DOI, senão PubMed
                    if pmcid:
                        link_pub = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/"
                    elif doi:
                        link_pub = f"https://doi.org/{doi}"
                    else:
                        link_pub = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

                    id_display = f"PMID:{pmid}" + (f" | {pmcid}" if pmcid else "")

                    record = AcademicRecord(
                        title=title.strip(),
                        link_pub=link_pub,
                        autor=autor.strip(),
                        revista_fonte=revista.strip(),
                        ano=ano,
                        base=self.name,
                        doi=doi,
                        id_origem=id_display
                    )
                    records.append(record.to_dict())

                    if len(records) >= max_results:
                        break

                if len(records) >= max_results:
                    break

            self.last_status = f"Sucesso: {len(records)} registros"
            self.log(f"PubMed concluído: {len(records)} registros processados com sucesso.")
            return records

        except Exception as e:
            self.log(f"ERRO: Exceção inesperada no PubMed: {type(e).__name__}: {e}", level="ERROR")
            self.last_status = f"Erro {type(e).__name__}"
            return []

