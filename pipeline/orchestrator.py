"""
Orquestrador concorrente de busca e enriquecimento multi-base.
Executa coletores em paralelo, realiza streaming SSE, deduplicação e persistência.
"""

import os
import asyncio
import json
import uuid
import logging
from typing import List, Dict, Any, AsyncGenerator
from datetime import datetime

import pandas as pd

from src import (
    BrapciScraper,
    PubmedScraper,
    AcmScraper,
    IeeeScraper,
    ScopusScraper,
    CapesScraper
)
from utils.data_export import normalize_dataframe, remove_duplicates, get_summary_metrics
from pipeline.enrichment import EnrichmentPipeline
from pipeline.storage import ResearchStorage

logger = logging.getLogger("AcademicOmniSearch.Orchestrator")


class SearchOrchestrator:
    """
    Coordena a execução concorrente dos scrapers acadêmicos,
    consolida os resultados em lote e despacha eventos em tempo real via SSE.
    """

    def __init__(self, storage: ResearchStorage, enrichment: EnrichmentPipeline):
        self.storage = storage
        self.enrichment = enrichment

    def get_scrapers(self, max_per_base: int) -> Dict[str, Any]:
        proxy_val = os.getenv("CAPES_PROXY") or os.getenv("BRAPCI_PROXY")
        zyte_key = os.getenv("ZYTE_API_KEY")

        return {
            "capes": CapesScraper(max_por_base=max_per_base, zyte_api_key=zyte_key, proxy=proxy_val),
            "pubmed": PubmedScraper(),
            "brapci": BrapciScraper(max_por_base=max_per_base, proxy=proxy_val),
            "acm": AcmScraper(),
            "ieee": IeeeScraper(),
            "scopus": ScopusScraper()
        }

    async def execute_search_stream(
        self,
        query: str,
        year_start: int,
        year_end: int,
        field: str,
        max_per_base: int,
        bases: List[str]
    ) -> AsyncGenerator[str, None]:
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        total_bases = len(bases)
        scrapers_map = self.get_scrapers(max_per_base)

        yield f"data: {json.dumps({'type': 'init', 'session_id': session_id, 'total_bases': total_bases, 'query': query})}\n\n"

        async def run_single_base(base_id: str):
            scraper = scrapers_map.get(base_id)
            if not scraper:
                return base_id, "Desconhecido", [], [f"Base {base_id} não encontrada"]
            try:
                records = await asyncio.to_thread(
                    scraper.search,
                    query=query,
                    year_start=year_start,
                    year_end=year_end,
                    field=field,
                    max_results=max_per_base
                )
                return base_id, scraper.name, records, getattr(scraper, "logs", [])
            except Exception as e:
                logger.error(f"Falha ao executar coletor {scraper.name}: {e}")
                return base_id, scraper.name, [], [f"Erro na execução: {str(e)}"]

        tasks = [run_single_base(b) for b in bases if b in scrapers_map]
        all_records: List[Dict[str, Any]] = []
        completed_count = 0

        # Concorrência assíncrona com notificação progressiva
        for future in asyncio.as_completed(tasks):
            base_id, base_name, records, logs = await future
            completed_count += 1
            all_records.extend(records)
            percent = int((completed_count / total_bases) * 100)

            yield f"data: {json.dumps({'type': 'base_done', 'base_id': base_id, 'base_name': base_name, 'count': len(records), 'percent': percent, 'logs': logs, 'records': records})}\n\n"

        # Deduplicação inteligente
        raw_count = len(all_records)
        if all_records:
            df = pd.DataFrame(all_records)
            df = remove_duplicates(df, subset_cols=["Title"])
            df = normalize_dataframe(df)
            dedup_records = df.to_dict(orient="records")
        else:
            dedup_records = []

        # Enriquecimento Cienciométrico Universal (OpenAlex + Qualis + PDF URLs)
        yield f"data: {json.dumps({'type': 'enriching', 'message': 'Aplicando métricas Qualis e OpenAlex aos registros...'})}\n\n"
        try:
            final_records = await asyncio.to_thread(self.enrichment.enrich_records, dedup_records)
        except Exception as e:
            logger.error(f"Erro durante enriquecimento cienciométrico: {e}")
            final_records = dedup_records

        # Cálculo de métricas
        df_final = pd.DataFrame(final_records) if final_records else pd.DataFrame()
        metrics = get_summary_metrics(df_final)

        # Persistência no SQLite
        try:
            self.storage.save_session(
                session_id=session_id,
                query=query,
                year_start=year_start,
                year_end=year_end,
                field=field,
                bases=bases,
                records=final_records,
                raw_count=raw_count,
                dedup_count=len(final_records)
            )
            prisma_stats = self.storage.get_prisma_metrics(session_id)
        except Exception as e:
            logger.error(f"Erro ao persistir sessão {session_id}: {e}")
            prisma_stats = {}

        yield f"data: {json.dumps({'type': 'complete', 'session_id': session_id, 'raw_count': raw_count, 'deduplicated_count': len(final_records), 'records': final_records, 'metrics': metrics, 'prisma_stats': prisma_stats})}\n\n"

