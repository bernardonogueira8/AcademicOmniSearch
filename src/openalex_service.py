"""
Serviço de enriquecimento cienciométrico via API oficial e gratuita da OpenAlex.
Recupera número de citações, FWCI (Field-Weighted Citation Impact) e acesso aberto por DOI.
"""

from typing import List, Dict, Any, Optional
import os
import time
import requests
import logging
from urllib.parse import quote
from utils.config import DEFAULT_HEADERS, DEFAULT_TIMEOUT

logger = logging.getLogger(__name__)


class OpenAlexService:
    """
    Cliente REST para consumo da API pública do OpenAlex (https://openalex.org).
    Suporta consultas individuais e em lote (batches de até 50 DOIs).
    """

    BASE_URL = "https://api.openalex.org"

    @classmethod
    def parse_work(cls, work: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(work, dict):
            return None

        open_access = work.get("open_access") or {}
        best_oa_location = work.get("best_oa_location") or {}
        primary_location = work.get("primary_location") or {}
        source = (primary_location.get("source") or {}) if isinstance(primary_location, dict) else {}

        # Identificação de link direto para o PDF ou localização aberta
        pdf_url = best_oa_location.get("pdf_url")
        if not pdf_url:
            oa_url = open_access.get("oa_url")
            if oa_url and (".pdf" in oa_url.lower() or "download" in oa_url.lower()):
                pdf_url = oa_url

        # Extração de ISSNs para cruzamento Qualis
        issn_list = source.get("issn") or []
        issn_primary = issn_list[0] if (isinstance(issn_list, list) and issn_list) else source.get("issn_l")

        return {
            "cited_by_count": work.get("cited_by_count") or 0,
            "fwci": work.get("fwci"),
            "publication_year": work.get("publication_year"),
            "is_open_access": bool(open_access.get("is_oa", False)),
            "oa_status": open_access.get("oa_status"),
            "pdf_url": pdf_url,
            "landing_page_url": best_oa_location.get("landing_page_url"),
            "issn": issn_primary,
            "journal_name": source.get("display_name"),
        }

    @classmethod
    def get_metrics_by_doi(cls, doi: str, session: Optional[requests.Session] = None) -> Optional[Dict[str, Any]]:
        """Busca métricas cienciométricas de um único DOI."""
        if not doi or not doi.strip():
            return None

        clean_doi = doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")
        email = os.getenv("OPENALEX_EMAIL", "").strip()
        query_param = f"?mailto={quote(email)}" if email else ""
        url = f"{cls.BASE_URL}/works/https://doi.org/{clean_doi}{query_param}"

        req = session or requests
        try:
            resp = req.get(url, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                return cls.parse_work(resp.json())
            elif resp.status_code == 404:
                return None
            else:
                logger.debug(f"OpenAlex retornou HTTP {resp.status_code} para {clean_doi}")
        except Exception as e:
            logger.debug(f"Erro ao consultar OpenAlex para DOI {clean_doi}: {e}")

        return None

    @classmethod
    def get_metrics_by_dois(
        cls, dois: List[str], batch_size: int = 50, session: Optional[requests.Session] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Recupera métricas para múltiplos DOIs em requisições agrupadas (até 50 por chamada).
        Retorna dicionário mapeando DOI -> métricas.
        """
        results: Dict[str, Dict[str, Any]] = {}
        if not dois:
            return results

        clean_dois = [
            d.strip().replace("https://doi.org/", "").replace("http://doi.org/", "")
            for d in dois
            if d and d.strip()
        ]
        # Remove duplicatas preservando ordem
        unique_dois = list(dict.fromkeys(clean_dois))

        req = session or requests.Session()

        for i in range(0, len(unique_dois), batch_size):
            batch = unique_dois[i : i + batch_size]
            doi_filter = f"doi:{'|'.join(batch)}"
            email = os.getenv("OPENALEX_EMAIL", "").strip()
            mailto_param = f"&mailto={quote(email)}" if email else ""
            url = f"{cls.BASE_URL}/works?filter={quote(doi_filter)}&per-page={len(batch)}{mailto_param}"

            try:
                resp = req.get(url, headers=DEFAULT_HEADERS, timeout=DEFAULT_TIMEOUT)
                if resp.status_code == 200:
                    data = resp.json()
                    works = data.get("results", [])
                    for work in works:
                        metrics = cls.parse_work(work)
                        work_doi = work.get("doi")
                        if metrics and work_doi:
                            doi_key = work_doi.replace("https://doi.org/", "").lower()
                            results[doi_key] = metrics
                else:
                    logger.debug(f"OpenAlex batch falhou com HTTP {resp.status_code}")
            except Exception as e:
                logger.debug(f"Erro em lote OpenAlex: {e}")

            if i + batch_size < len(unique_dois):
                time.sleep(0.1)

        return results

