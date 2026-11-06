"""
Scraper / Cliente de API para a BRAPCI (Base de Dados Referencial de Artigos de Periódicos em Ciência da Informação).
Utiliza a API oficial v5 JSON (https://cip.brapci.inf.br/api/brapci/search/v5).
"""

from typing import List, Dict, Any, Optional
import requests
import time
import logging
from src.base import BaseScraper, AcademicRecord
from utils.config import DEFAULT_HEADERS, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)

class BrapciScraper(BaseScraper):
    """
    Cliente da API v5 da BRAPCI.
    """

    BASE_URL = "https://cip.brapci.inf.br/api/brapci/search/v5"

    # Mapeamento amigável de campos para os códigos da API v5
    FIELD_MAP = {
        "todos": "FL",
        "all": "FL",
        "palavras-chave": "KW",
        "keywords": "KW",
        "autores": "AU",
        "author": "AU",
        "título": "TI",
        "titulo": "TI",
        "title": "TI",
        "resumo": "AB",
        "abstract": "AB",
        "texto completo": "FL",
        "text": "FL",
    }

    # Coleções disponíveis na BRAPCI:
    # JA = Revistas Brasileiras, JE = Revistas Estrangeiras, EV = Anais de Eventos, BK = Livros e Capítulos
    DEFAULT_COLLECTIONS = "JA,JE,EV,BK"

    def __init__(self, max_por_base: Optional[int] = None, page_size: Optional[int] = None):
        super().__init__(name="BRAPCI", is_api=True, requires_auth=False)
        self.page_size = max_por_base if max_por_base is not None else (page_size if page_size is not None else 20)
        self.max_por_base = self.page_size

    def search(
        self,
        query: str,
        year_start: int,
        year_end: int,
        field: str = "Todos",
        max_results: Optional[int] = None,
        max_por_base: Optional[int] = None,
        page_size: Optional[int] = None,
        collection: Optional[str] = None,
        delay: float = 0.5,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Executa a busca paginada na API v5 da BRAPCI e formata os resultados.
        O limite de registros respeita max_por_base / page_size configurado.
        """
        self.validate_years(year_start, year_end)
        
        if not query or not query.strip():
            return []

        # Determina o limite de registros
        target_limit = (
            max_por_base
            if max_por_base is not None
            else (page_size if page_size is not None else (max_results if max_results is not None else self.page_size))
        )

        field_code = self.FIELD_MAP.get(field.strip().lower(), "FL")
        collections_param = collection or self.DEFAULT_COLLECTIONS

        records: List[Dict[str, Any]] = []
        current_offset = 0

        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        session.headers.update({
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://brapci.inf.br/",
            "Origin": "https://brapci.inf.br",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        })

        # Inicialização suave de sessão para contornar WAF em instâncias de nuvem (Streamlit Cloud / AWS)
        try:
            session.get("https://brapci.inf.br/", timeout=4)
        except Exception:
            pass

        while len(records) < target_limit:
            params = {
                "term": query.strip(),
                "offset": str(current_offset),
                "year_start": str(year_start),
                "year_end": str(year_end),
                "collection": collections_param,
                "field": field_code
            }

            try:
                response = session.get(self.BASE_URL, params=params, timeout=DEFAULT_TIMEOUT)
                if response.status_code != 200:
                    logger.warning(f"BRAPCI API retornou status {response.status_code} no offset {current_offset}.")
                    break

                payload = response.json()
                if not isinstance(payload, dict):
                    break

                works = payload.get("works", [])
                total_reported = payload.get("total", 0)

                if not works:
                    break

                for work in works:
                    data = work.get("data", {})
                    work_id = str(work.get("id") or data.get("ID", "")).strip()
                    
                    title = data.get("TITLE") or "Sem título"
                    authors = data.get("AUTHORS") or "Autor não informado"
                    journal = data.get("JOURNAL") or data.get("LEGEND") or "Revista não informada"
                    year = str(work.get("year") or "").strip()
                    keywords = data.get("KEYWORDS") or ""
                    link = f"https://brapci.inf.br/v/{work_id}" if work_id else ""

                    record = AcademicRecord(
                        title=title.strip(),
                        link_pub=link,
                        autor=authors.strip(),
                        revista_fonte=journal.strip(),
                        ano=year,
                        base=self.name,
                        palavras_chave=keywords.strip(),
                        id_origem=work_id
                    )
                    records.append(record.to_dict())

                    if len(records) >= target_limit:
                        break

                current_offset += len(works)
                if current_offset >= total_reported or len(works) == 0:
                    break

                time.sleep(delay)

            except Exception as e:
                logger.error(f"Erro ao consultar BRAPCI: {e}")
                break

        return records[:target_limit]
