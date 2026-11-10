from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import hashlib
import re
import logging

logger = logging.getLogger("AcademicOmniSearch")


@dataclass
class AcademicRecord:
    """
    Estrutura padronizada de metadados acadêmicos para todas as bases de dados.
    Projetada para suportar todo o ciclo de vida da pesquisa:
    - Etapa 1: Recuperação / Coleta (Metadados básicos e origens)
    - Etapa 2: Cienciometria (OpenAlex e Qualis)
    - Etapa 3: Triagem & Elegibilidade (PRISMA Screening)
    - Etapa 4: Obtenção de Texto Completo (PDF URLs)
    """
    title: str
    link_pub: str
    autor: str
    revista_fonte: str
    ano: str
    base: str
    resumo: Optional[str] = ""
    palavras_chave: Optional[str] = ""
    doi: Optional[str] = ""
    id_origem: Optional[str] = ""
    issn: Optional[str] = ""
    
    # Cienciometria & Enriquecimento
    qualis_estrato: Optional[str] = None
    qualis_area: Optional[str] = None
    cited_by_count: Optional[int] = None
    fwci: Optional[float] = None
    is_open_access: Optional[bool] = None
    oa_status: Optional[str] = None

    # Texto Completo & Acesso Aberto
    pdf_url: Optional[str] = None

    # Triagem & Elegibilidade (Workflow PRISMA)
    screening_status: str = "pendente"  # 'pendente', 'incluido', 'excluido', 'duvida'
    screening_reason: Optional[str] = None
    screening_notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    @property
    def record_id(self) -> str:
        """Gera um ID hash determinístico baseado no título normalizado e ano."""
        norm_title = re.sub(r"[^a-zA-Z0-9]", "", (self.title or "").lower())
        norm_year = str(self.ano or "").strip()
        raw_key = f"{norm_title}_{norm_year}"
        return hashlib.md5(raw_key.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Converte o registro para o formato tabular padrão do projeto."""
        return {
            "id": self.record_id,
            "Title": self.title,
            "Link Pub": self.link_pub,
            "Autor": self.autor,
            "Revista / Fonte": self.revista_fonte,
            "Ano": self.ano,
            "Base": self.base,
            "Resumo": self.resumo or "",
            "Palavras-Chave": self.palavras_chave or "",
            "DOI": self.doi or "",
            "ID Origem": self.id_origem or "",
            "ISSN": self.issn or "",
            "qualis_estrato": self.qualis_estrato,
            "qualis_area": self.qualis_area,
            "cited_by_count": self.cited_by_count,
            "fwci": self.fwci,
            "is_open_access": self.is_open_access,
            "oa_status": self.oa_status,
            "pdf_url": self.pdf_url,
            "screening_status": self.screening_status,
            "screening_reason": self.screening_reason,
            "screening_notes": self.screening_notes,
            "tags": self.tags,
        }


class BaseScraper(ABC):
    """
    Classe base abstrata para todos os coletores (scrapers e clientes de API).
    Garante uniformidade de interface, tratamento de erros e schema.
    """

    def __init__(self, name: str, is_api: bool = False, requires_auth: bool = False):
        self.name = name
        self.is_api = is_api
        self.requires_auth = requires_auth
        self.last_status: str = "Pronto"
        self.logs: List[str] = []

    def log(self, message: str, level: str = "INFO") -> None:
        """Registra logs simultaneamente no logger do Python e na memória para exibição na UI."""
        formatted = f"[{self.name}] {message}"
        self.logs.append(formatted)
        
        lvl = level.upper()
        if lvl == "WARNING":
            logger.warning(formatted)
        elif lvl == "ERROR":
            logger.error(formatted)
        else:
            logger.info(formatted)

    @abstractmethod
    def search(
        self,
        query: str,
        year_start: int,
        year_end: int,
        field: str = "Todos",
        max_results: int = 50,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Executa a busca na base acadêmica e retorna uma lista de dicionários
        no padrão tabular oficial.
        """
        pass

    def validate_years(self, year_start: int, year_end: int) -> None:
        """Validação básica de intervalo de anos."""
        if year_start > year_end:
            raise ValueError(f"Ano inicial ({year_start}) não pode ser maior que o ano final ({year_end}).")
