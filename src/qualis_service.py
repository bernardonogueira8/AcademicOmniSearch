"""
Serviço de consulta local ao banco de dados Qualis (CAPES).
Consulta classificações de periódicos científicos brasileiros por ISSN ou Nome do Periódico.
"""

import os
import sqlite3
import re
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class QualisService:
    """
    Serviço singleton para consulta à base local qualis.db (SQLite).
    """
    _instance: Optional["QualisService"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        if getattr(self, "_initialized", False):
            return

        self.db_path = self._locate_db(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
        self._initialized = True

    def _locate_db(self, custom_path: Optional[str]) -> Optional[str]:
        if custom_path and os.path.exists(custom_path):
            return custom_path

        env_path = os.getenv("QUALIS_DB_PATH")
        if env_path and os.path.exists(env_path):
            return os.path.abspath(env_path)

        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "data", "qualis.db"),
            os.path.join(os.getcwd(), "data", "qualis.db"),
            os.path.join(os.getcwd(), "..", "periodicos-capes-mcp", "data", "qualis.db"),
            os.path.join(os.path.dirname(__file__), "..", "..", "periodicos-capes-mcp", "data", "qualis.db"),
        ]
        for path in candidates:
            abs_p = os.path.abspath(path)
            if os.path.exists(abs_p):
                return abs_p

        return None

    def _init_db(self) -> None:
        if not self.db_path or not os.path.exists(self.db_path):
            logger.warning("Banco qualis.db não encontrado. Enriquecimento Qualis desativado.")
            self.conn = None
            return

        try:
            self.conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, check_same_thread=False)
        except Exception as e:
            logger.error(f"Erro ao abrir qualis.db: {e}")
            self.conn = None

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> "QualisService":
        if cls._instance is None:
            cls._instance = QualisService(db_path)
        return cls._instance

    def is_available(self) -> bool:
        return self.conn is not None

    def format_issn(self, issn: str) -> str:
        """Limpa e formata o ISSN com hífen se tiver 8 dígitos."""
        clean = re.sub(r"[^0-9Xx]", "", issn).upper()
        if len(clean) == 8 and "-" not in issn:
            return f"{clean[:4]}-{clean[4:]}"
        return issn.strip().upper()

    def get_qualis_by_issn(self, issn: str) -> Optional[Dict[str, Any]]:
        """
        Consulta o Qualis de um periódico pelo ISSN.
        Tenta formatos com hífen e sem hífen.
        """
        if not self.is_available() or not issn:
            return None

        issn_clean = issn.strip()
        issn_with_hyphen = self.format_issn(issn_clean)
        issn_without_hyphen = re.sub(r"[^0-9Xx]", "", issn_clean).upper()

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT issn, journal_name, area, classification FROM qualis WHERE issn = ? OR issn = ? LIMIT 1",
                (issn_with_hyphen, issn_without_hyphen),
            )
            row = cursor.fetchone()
            if row:
                return {
                    "issn": row[0],
                    "journal_name": row[1],
                    "area": row[2],
                    "classification": row[3],
                }
        except Exception as e:
            logger.debug(f"Erro na consulta Qualis para ISSN {issn}: {e}")

        return None

    def get_qualis_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Consulta o Qualis de um periódico pelo nome ou título aproximado.
        Útil para bases que não fornecem ISSN diretamente.
        """
        if not self.is_available() or not title:
            return None

        clean_title = title.strip().lower()
        if len(clean_title) < 4:
            return None

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT issn, journal_name, area, classification FROM qualis WHERE LOWER(journal_name) = ? LIMIT 1",
                (clean_title,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "issn": row[0],
                    "journal_name": row[1],
                    "area": row[2],
                    "classification": row[3],
                }

            cursor.execute(
                "SELECT issn, journal_name, area, classification FROM qualis WHERE LOWER(journal_name) LIKE ? LIMIT 1",
                (f"{clean_title}%",)
            )
            row_like = cursor.fetchone()
            if row_like:
                return {
                    "issn": row_like[0],
                    "journal_name": row_like[1],
                    "area": row_like[2],
                    "classification": row_like[3],
                }
        except Exception as e:
            logger.debug(f"Erro na consulta Qualis por título {title}: {e}")

        return None

    def close(self) -> None:
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None
