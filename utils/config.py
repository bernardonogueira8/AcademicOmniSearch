"""
Configurações globais, cabeçalhos HTTP e constantes do AcademicOmniSearch.
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

DEFAULT_TIMEOUT = 20  # segundos

# Colunas padrão do schema CSV / DataFrame
STANDARD_COLUMNS = [
    "Title",
    "Link Pub",
    "Autor",
    "Revista / Fonte",
    "Ano",
    "Base"
]

EXTENDED_COLUMNS = STANDARD_COLUMNS + [
    "Resumo",
    "Palavras-Chave",
    "DOI",
    "ID Origem"
]

