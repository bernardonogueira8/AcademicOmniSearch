"""
Scraper / Módulo de integração para Scopus (Elsevier).
"""

from typing import List, Dict, Any, Optional
import os
import requests
import logging
from src.base import BaseScraper, AcademicRecord
from utils.config import DEFAULT_HEADERS, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)

class ScopusScraper(BaseScraper):
    """
    Coletor para Scopus.
    Suporta o consumo da Elsevier Scopus Search API oficial
    (quando as chaves SCOPUS_API_KEY ou ELSEVIER_API_KEY e token institucional estiverem disponíveis).
    """

    API_URL = "https://api.elsevier.com/content/search/scopus"

    def __init__(self, api_key: Optional[str] = None, inst_token: Optional[str] = None):
        key = api_key or os.getenv("SCOPUS_API_KEY") or os.getenv("ELSEVIER_API_KEY", "")
        token = inst_token or os.getenv("ELSEVIER_INST_TOKEN", "")
        super().__init__(name="Scopus", is_api=True, requires_auth=True)
        self.api_key = key
        self.inst_token = token

    def search(
        self,
        query: str,
        year_start: int,
        year_end: int,
        field: str = "Todos",
        max_results: int = 50,
        **kwargs
    ) -> List[Dict[str, Any]]:
        self.validate_years(year_start, year_end)

        if not self.api_key:
            logger.warning(
                "Scopus requer chave de API oficial (SCOPUS_API_KEY) e convênio institucional "
                "cadastrado em https://dev.elsevier.com/."
            )
            return []

        # Formatação de query Scopus Search (ex: TITLE-ABS-KEY(...) AND PUBYEAR > ... AND PUBYEAR < ...)
        scopus_query = f"{query.strip()} AND PUBYEAR AFT {year_start - 1} AND PUBYEAR BEF {year_end + 1}"
        
        headers = dict(DEFAULT_HEADERS)
        headers["X-ELS-APIKey"] = self.api_key
        if self.inst_token:
            headers["X-ELS-Insttoken"] = self.inst_token
        headers["Accept"] = "application/json"

        params = {
            "query": scopus_query,
            "count": str(min(max_results, 25)),
            "httpAccept": "application/json"
        }

        try:
            response = requests.get(self.API_URL, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
            if response.status_code != 200:
                logger.error(f"Erro na API Scopus: HTTP {response.status_code}")
                return []

            data = response.json()
            search_results = data.get("search-results", {})
            entries = search_results.get("entry", [])
            records: List[Dict[str, Any]] = []

            for entry in entries:
                title = entry.get("dc:title", "Sem título")
                creator = entry.get("dc:creator", "Autor não informado")
                source = entry.get("prism:publicationName", "Scopus Source")
                cover_date = entry.get("prism:coverDate", "")
                ano = cover_date[:4] if len(cover_date) >= 4 else ""
                doi = entry.get("prism:doi", "")
                
                # Link Scopus
                link_pub = ""
                for lk in entry.get("link", []):
                    if lk.get("@ref") == "scopus":
                        link_pub = lk.get("@href", "")
                        break
                if not link_pub and doi:
                    link_pub = f"https://doi.org/{doi}"

                rec = AcademicRecord(
                    title=title.strip(),
                    link_pub=link_pub.strip(),
                    autor=creator.strip(),
                    revista_fonte=source.strip(),
                    ano=ano.strip(),
                    base=self.name,
                    doi=doi.strip(),
                    id_origem=str(entry.get("dc:identifier", ""))
                )
                records.append(rec.to_dict())

            return records

        except Exception as e:
            logger.error(f"Exceção ao consultar Scopus: {e}")
            return []

