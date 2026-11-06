"""
Scraper / Módulo de integração para IEEE Xplore.
"""

from typing import List, Dict, Any, Optional
import os
import requests
import logging
from src.base import BaseScraper, AcademicRecord
from utils.config import DEFAULT_HEADERS, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)

class IeeeScraper(BaseScraper):
    """
    Coletor para IEEE Xplore.
    Suporta o consumo da IEEE Xplore Search API oficial (quando a chave IEEE_API_KEY estiver configurada)
    ou preparação para automação com headless browser.
    """

    API_URL = "https://ieeexploreapi.ieee.org/api/v1/search/articles"

    def __init__(self, api_key: Optional[str] = None):
        key = api_key or os.getenv("IEEE_API_KEY", "")
        super().__init__(name="IEEE Xplore", is_api=True, requires_auth=True)
        self.api_key = key

    def search(
        self,
        query: str,
        year_start: int,
        year_end: int,
        field: str = "Todos",
        max_results: int = 50,
        **kwargs
    ) -> List[Dict[str, Any]]:
        self.logs = []
        self.validate_years(year_start, year_end)

        if not self.api_key:
            msg = (
                "Chave de API oficial (IEEE_API_KEY) não encontrada nas variáveis de ambiente. "
                "Cadastre uma chave gratuita no portal https://developer.ieee.org/ para buscas automatizadas."
            )
            self.log(msg, level="WARNING")
            self.last_status = "Chave IEEE_API_KEY ausente"
            return []

        self.log(f"Iniciando busca IEEE Xplore: '{query}' (Janela: {year_start}-{year_end}, Limite: {max_results})")
        params = {
            "apikey": self.api_key,
            "querytext": query.strip(),
            "start_year": str(year_start),
            "end_year": str(year_end),
            "max_records": str(min(max_results, 100)),
            "format": "json"
        }

        try:
            self.log(f"Consultando IEEE API: {self.API_URL}")
            response = requests.get(self.API_URL, params=params, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
            if response.status_code != 200:
                self.log(f"ERRO: IEEE API retornou HTTP {response.status_code}: {response.text[:200]}", level="ERROR")
                self.last_status = f"Erro HTTP {response.status_code}"
                return []

            data = response.json()
            articles = data.get("articles", [])
            records: List[Dict[str, Any]] = []

            for art in articles:
                title = art.get("title", "Sem título")
                link_pub = art.get("html_url") or art.get("pdf_url") or ""
                authors_raw = art.get("authors", {}).get("authors", [])
                authors_list = [a.get("full_name") for a in authors_raw if a.get("full_name")]
                autor = "; ".join(authors_list) if authors_list else "Autor não informado"
                source = art.get("publication_title") or "IEEE Publication"
                ano = str(art.get("publication_year") or "")
                abstract = art.get("abstract", "")
                doi = art.get("doi", "")

                rec = AcademicRecord(
                    title=title.strip(),
                    link_pub=link_pub.strip(),
                    autor=autor.strip(),
                    revista_fonte=source.strip(),
                    ano=ano.strip(),
                    base=self.name,
                    resumo=abstract.strip(),
                    doi=doi.strip(),
                    id_origem=str(art.get("article_number", ""))
                )
                records.append(rec.to_dict())

            self.last_status = f"Sucesso: {len(records)} registros"
            self.log(f"IEEE Xplore retornou {len(records)} artigos.")
            return records

        except Exception as e:
            self.log(f"ERRO: Exceção ao consultar IEEE Xplore: {type(e).__name__}: {e}", level="ERROR")
            self.last_status = f"Erro {type(e).__name__}"
            return []

