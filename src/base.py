from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import pandas as pd

@dataclass
class AcademicRecord:
    """
    Estrutura padronizada de metadados acadêmicos para todas as bases de dados.
    Segue as diretrizes do schema oficial do AcademicOmniSearch.
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

    def to_dict(self) -> Dict[str, Any]:
        """Converte o registro para o formato tabular padrão do projeto."""
        return {
            "Title": self.title,
            "Link Pub": self.link_pub,
            "Autor": self.autor,
            "Revista / Fonte": self.revista_fonte,
            "Ano": self.ano,
            "Base": self.base,
            "Resumo": self.resumo or "",
            "Palavras-Chave": self.palavras_chave or "",
            "DOI": self.doi or "",
            "ID Origem": self.id_origem or ""
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

