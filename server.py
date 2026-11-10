"""
AcademicOmniSearch - Servidor FastAPI & Orquestrador de Pesquisa Científica
Fornece API REST, streaming concorrente SSE, persistência local e workflow de triagem PRISMA.
"""

import os
import json
import asyncio
import io
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import pandas as pd

import utils.config  # Garante carregamento do .env
from pipeline import ResearchStorage, EnrichmentPipeline, SearchOrchestrator
from utils.data_export import (
    normalize_dataframe,
    export_to_excel,
    remove_duplicates,
    get_summary_metrics
)
from utils.bibliographic_exporter import BibliographicExporter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("AcademicOmniSearch.API")

# Inicialização da infraestrutura do pipeline científico
storage = ResearchStorage.get_instance()
enrichment = EnrichmentPipeline()
orchestrator = SearchOrchestrator(storage=storage, enrichment=enrichment)

app = FastAPI(
    title="AcademicOmniSearch API",
    description="Backend moderno de colheita, cienciometria e triagem PRISMA multi-base",
    version="2.0.0"
)

# CORS liberado para desenvolvimento com Vite (porta 5173) e produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    query: str = Field(..., description="Termo ou expressão de busca")
    year_start: int = Field(default=2020, ge=1900, le=2030)
    year_end: int = Field(default=2026, ge=1900, le=2030)
    field: str = Field(default="Todos")
    max_per_base: int = Field(default=30, ge=5, le=200)
    bases: List[str] = Field(default=["capes", "pubmed", "brapci", "acm"])


class ExportRequest(BaseModel):
    format: str = Field(..., description="Formato: excel, ris, bibtex ou csv")
    records: List[Dict[str, Any]]
    filename: Optional[str] = None


class ScreeningUpdateRequest(BaseModel):
    status: str = Field(..., description="Status: incluido, excluido, duvida ou pendente")
    reason: Optional[str] = None
    notes: Optional[str] = None


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }


@app.get("/api/bases")
def list_bases():
    """Retorna o catálogo de bases com metadados, categorias e estado de credenciais."""
    ieee_configured = bool(os.getenv("IEEE_API_KEY"))
    scopus_configured = bool(os.getenv("SCOPUS_API_KEY") or os.getenv("ELSEVIER_API_KEY"))
    zyte_configured = bool(os.getenv("ZYTE_API_KEY"))

    bases_info = [
        {
            "id": "capes",
            "name": "Periódicos CAPES",
            "description": "Portal MEC/CAPES multidisciplinar com Qualis & OpenAlex",
            "category": "Multidisciplinar",
            "status": "ready",
            "badge": "Qualis + OpenAlex",
            "requires_key": False,
            "has_key": zyte_configured or True,
            "note": "Bypass CloudFront integrado via Zyte/Proxy" if zyte_configured else "Modo HTTP nativo"
        },
        {
            "id": "pubmed",
            "name": "PubMed (NLM)",
            "description": "Ciências da Saúde, Medicina e Biologia via NCBI E-utilities",
            "category": "Saúde & Biomedicina",
            "status": "ready",
            "badge": "Oficial NCBI",
            "requires_key": False,
            "has_key": bool(os.getenv("NCBI_API_KEY")),
            "note": "Rate limit: 10 req/s com chave ou 3 req/s público"
        },
        {
            "id": "brapci",
            "name": "BRAPCI",
            "description": "Base Referencial de Artigos em Ciência da Informação",
            "category": "Ciência da Informação",
            "status": "ready",
            "badge": "API REST v5",
            "requires_key": False,
            "has_key": True,
            "note": "API pública sem autenticação"
        },
        {
            "id": "acm",
            "name": "ACM Digital Library",
            "description": "Ciência da Computação, Engenharia de Software e IA",
            "category": "Computação",
            "status": "ready",
            "badge": "Parser HTML / WAF",
            "requires_key": False,
            "has_key": True,
            "note": "Suporta dumps locais e requisições HTTP"
        },
        {
            "id": "ieee",
            "name": "IEEE Xplore",
            "description": "Engenharia Elétrica, Eletrônica e Ciência da Computação",
            "category": "Engenharia & Tecnologia",
            "status": "ready" if ieee_configured else "requires_key",
            "badge": "IEEE Search API",
            "requires_key": True,
            "has_key": ieee_configured,
            "note": "Requer IEEE_API_KEY no .env" if not ieee_configured else "Chave configurada"
        },
        {
            "id": "scopus",
            "name": "Scopus (Elsevier)",
            "description": "Maior base referencial global de citações e resumos",
            "category": "Multidisciplinar Global",
            "status": "ready" if scopus_configured else "requires_key",
            "badge": "Elsevier API",
            "requires_key": True,
            "has_key": scopus_configured,
            "note": "Requer SCOPUS_API_KEY no .env" if not scopus_configured else "Chave configurada"
        }
    ]
    return {"bases": bases_info}


@app.get("/api/search/stream")
async def search_stream(
    query: str,
    year_start: int = 2020,
    year_end: int = 2026,
    field: str = "Todos",
    max_per_base: int = 30,
    bases: str = "capes,pubmed,brapci,acm"
):
    """
    Stream de eventos em tempo real com execução concorrente de todas as bases selecionadas.
    Salva automaticamente os resultados e o histórico da busca na base de dados SQLite local.
    """
    selected_bases = [b.strip() for b in bases.split(",") if b.strip()]
    return StreamingResponse(
        orchestrator.execute_search_stream(
            query=query,
            year_start=year_start,
            year_end=year_end,
            field=field,
            max_per_base=max_per_base,
            bases=selected_bases
        ),
        media_type="text/event-stream"
    )


# --- Endpoints de Persistência, Histórico & Triagem PRISMA ---

@app.get("/api/sessions")
def list_sessions():
    """Retorna o histórico de buscas anteriores salvas no banco local."""
    return {"sessions": storage.list_sessions(limit=30)}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    """Recupera uma sessão de busca completa com seus registros e status de triagem."""
    data = storage.get_session(session_id)
    if not data:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    
    prisma_stats = storage.get_prisma_metrics(session_id)
    return {
        **data,
        "prisma_stats": prisma_stats
    }


@app.patch("/api/articles/{article_id}/screening")
def update_screening(article_id: str, payload: ScreeningUpdateRequest):
    """Atualiza o status de triagem (incluído, excluído, motivo, notas) de um artigo."""
    success = storage.update_screening(
        article_id=article_id,
        status=payload.status,
        reason=payload.reason,
        notes=payload.notes
    )
    if not success:
        raise HTTPException(status_code=404, detail="Artigo não encontrado para atualização de triagem.")
    return {"status": "updated", "article_id": article_id, "screening_status": payload.status}


@app.get("/api/prisma/{session_id}")
def get_prisma_flow(session_id: str):
    """Retorna o sumário quantitativo para geração do diagrama de fluxo PRISMA."""
    stats = storage.get_prisma_metrics(session_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Sessão não encontrada para cálculo PRISMA.")
    return {"prisma": stats}


# --- Endpoint de Exportação Multi-Formato ---

@app.post("/api/export")
def export_dataset(payload: ExportRequest):
    """
    Exportação rápida sob demanda para Excel (.xlsx), RIS (.ris), BibTeX (.bib) ou CSV (.csv).
    """
    records = payload.records
    fmt = payload.format.lower().strip()
    base_name = payload.filename or f"AcademicOmniSearch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    if not records:
        raise HTTPException(status_code=400, detail="Nenhum registro para exportar.")

    if fmt in ["excel", "xlsx"]:
        df = pd.DataFrame(records)
        df = normalize_dataframe(df)
        excel_bytes = export_to_excel(df, name_table="Resultados")
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.xlsx"'}
        )

    elif fmt == "ris":
        ris_text = BibliographicExporter.to_ris(records)
        return StreamingResponse(
            io.BytesIO(ris_text.encode("utf-8")),
            media_type="application/x-research-info-systems",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.ris"'}
        )

    elif fmt in ["bibtex", "bib"]:
        bib_text = BibliographicExporter.to_bibtex(records)
        return StreamingResponse(
            io.BytesIO(bib_text.encode("utf-8")),
            media_type="application/x-bibtex",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.bib"'}
        )

    elif fmt == "csv":
        df = pd.DataFrame(records)
        df = normalize_dataframe(df)
        csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
        return StreamingResponse(
            io.BytesIO(csv_bytes),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{base_name}.csv"'}
        )

    else:
        raise HTTPException(status_code=400, detail=f"Formato não suportado: {fmt}")


# Servindo o frontend compilado (React SPA)
dist_dir = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Endpoint não encontrado")
        file_path = os.path.join(dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))
else:
    @app.get("/")
    def serve_placeholder():
        return {
            "message": "AcademicOmniSearch API v2.0 ativa.",
            "frontend": "Para compilar o frontend React, execute: cd frontend && npm run build",
            "docs": "/docs"
        }
