"""
Pipeline universal de enriquecimento cienciométrico e identificação de PDFs.
Processa e enriquece registros colhidos de qualquer base de dados (CAPES, PubMed, BRAPCI, ACM, IEEE, Scopus).
"""

from typing import List, Dict, Any, Optional
import logging
import re
import hashlib

from src.openalex_service import OpenAlexService
from src.qualis_service import QualisService

logger = logging.getLogger("AcademicOmniSearch.Enrichment")


class EnrichmentPipeline:
    """
    Orquestra o enriquecimento pós-busca:
    1. Resolução em lote via OpenAlex (Citações, FWCI, Status OA e link de PDF)
    2. Classificação Qualis (por ISSN primário ou título do periódico)
    3. Atribuição de ID unívoco determinístico
    """

    def __init__(self, qualis_service: Optional[QualisService] = None):
        self.qualis_service = qualis_service or QualisService.get_instance()

    def generate_record_id(self, record: Dict[str, Any]) -> str:
        """Gera um hash estável a partir de título normalizado e ano."""
        title = record.get("Title") or ""
        norm_title = re.sub(r"[^a-zA-Z0-9]", "", title.lower())
        year = str(record.get("Ano") or "").strip()
        raw = f"{norm_title}_{year}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:16]

    def enrich_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aplica enriquecimento cienciométrico a toda a lista de registros."""
        if not records:
            return []

        # 1. Atribui IDs determinísticos aos registros
        for r in records:
            if not r.get("id"):
                r["id"] = self.generate_record_id(r)
            if "screening_status" not in r:
                r["screening_status"] = "pendente"

        # 2. Coleta DOIs válidos para enriquecimento via OpenAlex
        dois_map: Dict[str, List[Dict[str, Any]]] = {}
        for r in records:
            doi = r.get("DOI")
            if doi and isinstance(doi, str) and doi.strip():
                clean_doi = doi.strip().replace("https://doi.org/", "").replace("http://doi.org/", "").lower()
                dois_map.setdefault(clean_doi, []).append(r)

        # 3. Consulta em lote ao OpenAlex se houver DOIs
        if dois_map:
            unique_dois = list(dois_map.keys())
            logger.info(f"Iniciando enriquecimento OpenAlex para {len(unique_dois)} DOIs...")
            try:
                metrics_map = OpenAlexService.get_metrics_by_dois(unique_dois, batch_size=50)
                for clean_doi, matching_records in dois_map.items():
                    metrics = metrics_map.get(clean_doi)
                    if metrics:
                        for r in matching_records:
                            r["cited_by_count"] = metrics.get("cited_by_count", 0)
                            r["fwci"] = metrics.get("fwci")
                            r["is_open_access"] = metrics.get("is_open_access", False)
                            r["oa_status"] = metrics.get("oa_status")
                            if metrics.get("pdf_url") and not r.get("pdf_url"):
                                r["pdf_url"] = metrics.get("pdf_url")
                            if metrics.get("issn") and not r.get("ISSN"):
                                r["ISSN"] = metrics.get("issn")
            except Exception as e:
                logger.error(f"Erro no enriquecimento OpenAlex em lote: {e}")

        # 4. Consulta Qualis para cada registro (por ISSN ou por Título do Periódico)
        if self.qualis_service.is_available():
            for r in records:
                # Evita sobrescrever se já tiver qualis_estrato
                if r.get("qualis_estrato"):
                    continue

                issn = r.get("ISSN")
                qualis_info = None

                # Tentativa por ISSN
                if issn and isinstance(issn, str) and issn.strip():
                    qualis_info = self.qualis_service.get_qualis_by_issn(issn.strip())

                # Tentativa por Nome do Periódico / Fonte
                if not qualis_info:
                    source_name = r.get("Revista / Fonte")
                    if source_name and isinstance(source_name, str) and len(source_name.strip()) > 3:
                        qualis_info = self.qualis_service.get_qualis_by_title(source_name.strip())

                if qualis_info:
                    r["qualis_estrato"] = qualis_info.get("classification")
                    r["qualis_area"] = qualis_info.get("area")

        return records

