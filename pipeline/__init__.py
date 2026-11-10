"""
Módulo de pipeline para as etapas da pesquisa científica:
- Recuperação e Busca Concorrente
- Enriquecimento Cienciométrico (Qualis & OpenAlex)
- Triagem Sistemática (Workflow PRISMA)
- Persistência e Histórico de Sessões
"""

from pipeline.storage import ResearchStorage
from pipeline.enrichment import EnrichmentPipeline
from pipeline.orchestrator import SearchOrchestrator

__all__ = [
    "ResearchStorage",
    "EnrichmentPipeline",
    "SearchOrchestrator",
]

