"""
Camada de persistência local SQLite para sessões de busca, artigos e triagem PRISMA.
Arquivo padrão: data/research.db
"""

import os
import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("AcademicOmniSearch.Storage")


class ResearchStorage:
    """
    Gerenciador SQLite para persistência do ciclo de vida das pesquisas científicas:
    - Registro e histórico de sessões de busca
    - Armazenamento de metadados dos artigos colhidos
    - Persistência das decisões de triagem (PRISMA screening) e anotações
    """
    _instance: Optional["ResearchStorage"] = None

    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            self.db_path = os.path.join(data_dir, "research.db")
        else:
            self.db_path = db_path

        self._init_db()

    @classmethod
    def get_instance(cls, db_path: Optional[str] = None) -> "ResearchStorage":
        if cls._instance is None:
            cls._instance = ResearchStorage(db_path)
        return cls._instance

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Cria as tabelas de sessões e artigos se não existirem."""
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS search_sessions (
                        id TEXT PRIMARY KEY,
                        query TEXT NOT NULL,
                        year_start INTEGER,
                        year_end INTEGER,
                        field TEXT,
                        bases TEXT,
                        total_raw INTEGER DEFAULT 0,
                        total_dedup INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL
                    )
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id TEXT PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        title TEXT NOT NULL,
                        link_pub TEXT,
                        autor TEXT,
                        revista_fonte TEXT,
                        ano TEXT,
                        base TEXT,
                        resumo TEXT,
                        palavras_chave TEXT,
                        doi TEXT,
                        id_origem TEXT,
                        issn TEXT,
                        qualis_estrato TEXT,
                        qualis_area TEXT,
                        cited_by_count INTEGER DEFAULT 0,
                        fwci REAL,
                        is_open_access INTEGER DEFAULT 0,
                        oa_status TEXT,
                        pdf_url TEXT,
                        screening_status TEXT DEFAULT 'pendente',
                        screening_reason TEXT,
                        screening_notes TEXT,
                        tags TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (session_id) REFERENCES search_sessions (id) ON DELETE CASCADE
                    )
                """)

                # Índices para consultas rápidas
                conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_session ON articles (session_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_status ON articles (screening_status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_doi ON articles (doi)")
        finally:
            conn.close()

    def save_session(
        self,
        session_id: str,
        query: str,
        year_start: int,
        year_end: int,
        field: str,
        bases: List[str],
        records: List[Dict[str, Any]],
        raw_count: int,
        dedup_count: int,
    ) -> None:
        """Salva a sessão e todos os seus artigos colhidos."""
        now = datetime.now().isoformat()
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO search_sessions 
                    (id, query, year_start, year_end, field, bases, total_raw, total_dedup, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        query,
                        year_start,
                        year_end,
                        field,
                        json.dumps(bases),
                        raw_count,
                        dedup_count,
                        now,
                    ),
                )

                for r in records:
                    record_id = r.get("id") or f"{session_id}_{hash(r.get('Title', ''))}"
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO articles (
                            id, session_id, title, link_pub, autor, revista_fonte, ano, base,
                            resumo, palavras_chave, doi, id_origem, issn,
                            qualis_estrato, qualis_area, cited_by_count, fwci,
                            is_open_access, oa_status, pdf_url, screening_status,
                            screening_reason, screening_notes, tags, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            record_id,
                            session_id,
                            r.get("Title") or "",
                            r.get("Link Pub") or "",
                            r.get("Autor") or "",
                            r.get("Revista / Fonte") or "",
                            str(r.get("Ano") or ""),
                            r.get("Base") or "",
                            r.get("Resumo") or "",
                            r.get("Palavras-Chave") or "",
                            r.get("DOI") or "",
                            r.get("ID Origem") or "",
                            r.get("ISSN") or "",
                            r.get("qualis_estrato"),
                            r.get("qualis_area"),
                            r.get("cited_by_count") or 0,
                            r.get("fwci"),
                            1 if r.get("is_open_access") else 0,
                            r.get("oa_status"),
                            r.get("pdf_url"),
                            r.get("screening_status") or "pendente",
                            r.get("screening_reason"),
                            r.get("screening_notes"),
                            json.dumps(r.get("tags") or []),
                            now,
                        ),
                    )
        finally:
            conn.close()

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Lista as sessões de busca mais recentes."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM search_sessions ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "query": row["query"],
                    "year_start": row["year_start"],
                    "year_end": row["year_end"],
                    "field": row["field"],
                    "bases": json.loads(row["bases"]) if row["bases"] else [],
                    "total_raw": row["total_raw"],
                    "total_dedup": row["total_dedup"],
                    "created_at": row["created_at"],
                }
                for row in rows
            ]
        finally:
            conn.close()

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retorna uma sessão específica e todos os seus artigos."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM search_sessions WHERE id = ?", (session_id,))
            session_row = cursor.fetchone()
            if not session_row:
                return None

            cursor.execute(
                "SELECT * FROM articles WHERE session_id = ? ORDER BY Ano DESC, title ASC",
                (session_id,),
            )
            article_rows = cursor.fetchall()

            articles = []
            for a in article_rows:
                articles.append({
                    "id": a["id"],
                    "Title": a["title"],
                    "Link Pub": a["link_pub"],
                    "Autor": a["autor"],
                    "Revista / Fonte": a["revista_fonte"],
                    "Ano": a["ano"],
                    "Base": a["base"],
                    "Resumo": a["resumo"],
                    "Palavras-Chave": a["palavras_chave"],
                    "DOI": a["doi"],
                    "ID Origem": a["id_origem"],
                    "ISSN": a["issn"],
                    "qualis_estrato": a["qualis_estrato"],
                    "qualis_area": a["qualis_area"],
                    "cited_by_count": a["cited_by_count"],
                    "fwci": a["fwci"],
                    "is_open_access": bool(a["is_open_access"]),
                    "oa_status": a["oa_status"],
                    "pdf_url": a["pdf_url"],
                    "screening_status": a["screening_status"] or "pendente",
                    "screening_reason": a["screening_reason"],
                    "screening_notes": a["screening_notes"],
                    "tags": json.loads(a["tags"]) if a["tags"] else [],
                })

            return {
                "id": session_row["id"],
                "query": session_row["query"],
                "year_start": session_row["year_start"],
                "year_end": session_row["year_end"],
                "field": session_row["field"],
                "bases": json.loads(session_row["bases"]) if session_row["bases"] else [],
                "total_raw": session_row["total_raw"],
                "total_dedup": session_row["total_dedup"],
                "created_at": session_row["created_at"],
                "records": articles,
            }
        finally:
            conn.close()

    def update_screening(
        self,
        article_id: str,
        status: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """Atualiza a decisão de triagem de um artigo."""
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE articles 
                    SET screening_status = ?, screening_reason = ?, screening_notes = ?
                    WHERE id = ?
                    """,
                    (status, reason, notes, article_id),
                )
                return cursor.rowcount > 0
        finally:
            conn.close()

    def get_prisma_metrics(self, session_id: str) -> Dict[str, Any]:
        """Calcula o resumo para o fluxograma PRISMA da sessão."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT total_raw, total_dedup FROM search_sessions WHERE id = ?", (session_id,))
            session_row = cursor.fetchone()
            if not session_row:
                return {}

            total_raw = session_row["total_raw"]
            total_dedup = session_row["total_dedup"]
            duplicates_removed = max(0, total_raw - total_dedup)

            cursor.execute(
                """
                SELECT screening_status, COUNT(*) as count 
                FROM articles 
                WHERE session_id = ? 
                GROUP BY screening_status
                """,
                (session_id,),
            )
            counts = {row["screening_status"]: row["count"] for row in cursor.fetchall()}

            included = counts.get("incluido", 0)
            excluded = counts.get("excluido", 0)
            uncertain = counts.get("duvida", 0)
            pending = counts.get("pendente", 0)
            screened = included + excluded + uncertain

            return {
                "records_identified": total_raw,
                "duplicates_removed": duplicates_removed,
                "records_screened": screened,
                "records_pending": pending,
                "records_excluded": excluded,
                "records_uncertain": uncertain,
                "records_included": included,
            }
        finally:
            conn.close()

