"""
Exportador bibliográfico para formatos RIS (.ris) e BibTeX (.bib).
Facilita a importação dos resultados em gerenciadores como Zotero, Mendeley e EndNote.
"""

from typing import List, Dict, Any, Optional
import re
import unicodedata


class BibliographicExporter:
    """
    Converte listas de registros acadêmicos para RIS e BibTeX.
    """

    DOC_TYPE_RIS = {
        "artigo": "JOUR",
        "journal": "JOUR",
        "livro": "BOOK",
        "book": "BOOK",
        "capítulo de livro": "CHAP",
        "chapter": "CHAP",
        "revisão": "JOUR",
        "review": "JOUR",
        "conferência": "CONF",
        "conference": "CONF",
        "carta": "NEWS",
        "errata": "JOUR",
    }

    @staticmethod
    def _clean_str(text: Any) -> str:
        if text is None:
            return ""
        return str(text).strip()

    @staticmethod
    def _generate_citation_key(record: Dict[str, Any], index: int) -> str:
        """Gera uma chave única e segura para BibTeX (ex: Silva2024Machine)."""
        author = BibliographicExporter._clean_str(record.get("Autor", ""))
        first_author = author.split(";")[0].split(",")[0].strip() or "Anon"
        # Remove acentos
        first_author = "".join(
            c for c in unicodedata.normalize("NFD", first_author) if unicodedata.category(c) != "Mn"
        )
        first_author = re.sub(r"[^A-Za-z0-9]", "", first_author) or "Author"

        year = BibliographicExporter._clean_str(record.get("Ano", ""))
        year_str = re.search(r"\d{4}", year)
        year_clean = year_str.group(0) if year_str else "nd"

        title = BibliographicExporter._clean_str(record.get("Title", ""))
        first_word = title.split()[0] if title.split() else "Paper"
        first_word = re.sub(r"[^A-Za-z0-9]", "", first_word)

        return f"{first_author}_{year_clean}_{first_word}_{index}"

    @classmethod
    def to_ris(cls, records: List[Dict[str, Any]]) -> str:
        """Exporta lista de registros para string no formato RIS."""
        ris_entries = []

        for r in records:
            title = cls._clean_str(r.get("Title"))
            if not title:
                continue

            doc_type = cls._clean_str(r.get("Tipo Documento", r.get("document_type", "artigo"))).lower()
            ris_type = cls.DOC_TYPE_RIS.get(doc_type, "JOUR")

            lines = [f"TY  - {ris_type}", f"TI  - {title}"]

            # Autores
            authors_str = cls._clean_str(r.get("Autor"))
            if authors_str:
                for author in authors_str.split(";"):
                    a = author.strip()
                    if a:
                        lines.append(f"AU  - {a}")

            # Periódico / Fonte
            journal = cls._clean_str(r.get("Revista / Fonte"))
            if journal:
                lines.append(f"JO  - {journal}")
                lines.append(f"T2  - {journal}")

            # Ano
            year = cls._clean_str(r.get("Ano"))
            year_match = re.search(r"\d{4}", year)
            if year_match:
                lines.append(f"PY  - {year_match.group(0)}")

            # Volume & Issue
            if r.get("Volume"):
                lines.append(f"VL  - {r['Volume']}")
            if r.get("Issue"):
                lines.append(f"IS  - {r['Issue']}")

            # DOI
            doi = cls._clean_str(r.get("DOI"))
            if doi:
                lines.append(f"DO  - {doi}")

            # Link / URL
            link = cls._clean_str(r.get("Link Pub"))
            if link:
                lines.append(f"UR  - {link}")

            # ISSN
            issn = cls._clean_str(r.get("ISSN"))
            if issn:
                lines.append(f"SN  - {issn}")

            # Resumo
            abstract = cls._clean_str(r.get("Resumo"))
            if abstract:
                lines.append(f"AB  - {abstract}")

            # Palavras-chave
            keywords = cls._clean_str(r.get("Palavras-Chave"))
            if keywords:
                for kw in re.split(r"[;,]", keywords):
                    kw_clean = kw.strip()
                    if kw_clean:
                        lines.append(f"KW  - {kw_clean}")

            # Base de dados
            base = cls._clean_str(r.get("Base"))
            if base:
                lines.append(f"DB  - {base}")

            lines.append("ER  - ")
            ris_entries.append("\n".join(lines))

        return "\n\n".join(ris_entries) + ("\n" if ris_entries else "")

    @classmethod
    def to_bibtex(cls, records: List[Dict[str, Any]]) -> str:
        """Exporta lista de registros para string no formato BibTeX."""
        bib_entries = []

        for idx, r in enumerate(records, 1):
            title = cls._clean_str(r.get("Title"))
            if not title:
                continue

            doc_type = cls._clean_str(r.get("Tipo Documento", r.get("document_type", "artigo"))).lower()
            entry_type = "article" if "artigo" in doc_type or "journal" in doc_type or "review" in doc_type else "misc"
            citation_key = cls._generate_citation_key(r, idx)

            fields = [f"  title = {{{title}}}"]

            # Autores formatados com 'and' para BibTeX
            authors_str = cls._clean_str(r.get("Autor"))
            if authors_str:
                author_list = [a.strip() for a in authors_str.split(";") if a.strip()]
                if author_list:
                    fields.append(f"  author = {{{' and '.join(author_list)}}}")

            # Periódico
            journal = cls._clean_str(r.get("Revista / Fonte"))
            if journal:
                fields.append(f"  journal = {{{journal}}}")

            # Ano
            year = cls._clean_str(r.get("Ano"))
            year_match = re.search(r"\d{4}", year)
            if year_match:
                fields.append(f"  year = {{{year_match.group(0)}}}")

            # Volume & Issue
            if r.get("Volume"):
                fields.append(f"  volume = {{{r['Volume']}}}")
            if r.get("Issue"):
                fields.append(f"  number = {{{r['Issue']}}}")

            # DOI & URL
            doi = cls._clean_str(r.get("DOI"))
            if doi:
                fields.append(f"  doi = {{{doi}}}")
            link = cls._clean_str(r.get("Link Pub"))
            if link:
                fields.append(f"  url = {{{link}}}")

            # ISSN
            issn = cls._clean_str(r.get("ISSN"))
            if issn:
                fields.append(f"  issn = {{{issn}}}")

            # Resumo
            abstract = cls._clean_str(r.get("Resumo"))
            if abstract:
                # Sanitiza chaves no resumo
                clean_ab = abstract.replace("{", "\\{").replace("}", "\\}")
                fields.append(f"  abstract = {{{clean_ab}}}")

            entry = f"@{entry_type}{{{citation_key},\n" + ",\n".join(fields) + "\n}"
            bib_entries.append(entry)

        return "\n\n".join(bib_entries) + ("\n" if bib_entries else "")

