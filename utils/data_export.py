"""
Módulo de padronização, limpeza e exportação de dados para AcademicOmniSearch.
Garante compatibilidade de schema com Power BI, Excel, Pandas e R.
"""

from typing import List, Dict, Any, Optional
import io
import pandas as pd
from utils.config import STANDARD_COLUMNS, EXTENDED_COLUMNS

__all__ = [
    "normalize_dataframe",
    "export_to_excel",
    "remove_duplicates",
    "get_summary_metrics",
]


def normalize_dataframe(records: Any, keep_extended: bool = True) -> pd.DataFrame:
    """
    Normaliza uma lista de registros brutos ou DataFrame em um DataFrame padronizado.
    Garante a presença das colunas obrigatórias na ordem especificada no README.
    """
    cols = EXTENDED_COLUMNS if keep_extended else STANDARD_COLUMNS

    if isinstance(records, pd.DataFrame):
        if records.empty:
            return pd.DataFrame(columns=cols)
        df = records.copy()
    else:
        if not records:
            return pd.DataFrame(columns=cols)
        df = pd.DataFrame(records)

    # Garante a existência de todas as colunas padrão
    target_columns = EXTENDED_COLUMNS if keep_extended else STANDARD_COLUMNS
    for col in target_columns:
        if col not in df.columns:
            df[col] = ""

    # Limpeza básica em colunas de texto
    for col in ["Title", "Autor", "Revista / Fonte", "Ano", "Base"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"None": "", "nan": "", "NoneType": ""})

    # Ordenação das colunas: colunas padrão primeiro, seguidas de colunas extras
    ordered_cols = [c for c in target_columns if c in df.columns]
    remaining_cols = [c for c in df.columns if c not in ordered_cols]
    df = df[ordered_cols + remaining_cols]

    return df


def remove_duplicates(df: pd.DataFrame, subset_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Remove duplicatas considerando título (case-insensitive) ou link.
    """
    if df.empty:
        return df

    if subset_cols is None:
        subset_cols = ["Title"] if "Title" in df.columns else None

    if subset_cols and "Title" in subset_cols:
        # Cria uma coluna temporária normalizada para comparar títulos
        temp_title = df["Title"].str.lower().str.replace(r"\s+", " ", regex=True).str.strip()
        df_dedup = df.loc[~temp_title.duplicated(keep="first")].copy()
        return df_dedup

    return df.drop_duplicates(subset=subset_cols, keep="first")


def export_to_excel(df: pd.DataFrame, name_table: str = "Resultados", use_bom: bool = True) -> bytes:
    """
    Exporta o DataFrame para bytes de planilha Excel (.xlsx).
    Garante compatibilidade de nomes de abas e retorna bytes prontos para download.
    """
    if df.empty:
        cols = STANDARD_COLUMNS
        df = pd.DataFrame(columns=cols)

    # Sanitiza o nome da planilha (máx 31 caracteres, sem caracteres proibidos pelo Excel)
    clean_name = str(name_table)
    for ch in "[]:*?/\\":
        clean_name = clean_name.replace(ch, "_")
    clean_name = clean_name.strip()[:31] or "Resultados"

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=clean_name)
    
    return output.getvalue()


def get_summary_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Gera métricas agregadas da busca para exibição em dashboard.
    """
    if df.empty:
        return {
            "total_records": 0,
            "bases_count": {},
            "years_range": "N/D",
            "top_journals": {}
        }

    bases_count = df["Base"].value_counts().to_dict() if "Base" in df.columns else {}
    
    # Análise temporal
    years_series = df["Ano"].dropna()
    valid_years = [int(y) for y in years_series if str(y).isdigit() and len(str(y)) == 4]
    if valid_years:
        years_range = f"{min(valid_years)} - {max(valid_years)}"
    else:
        years_range = "N/D"

    # Periódicos/Fontes mais frequentes
    top_journals = {}
    if "Revista / Fonte" in df.columns:
        filtered_sources = df[df["Revista / Fonte"].str.strip() != ""]["Revista / Fonte"]
        top_journals = filtered_sources.value_counts().head(5).to_dict()

    return {
        "total_records": len(df),
        "bases_count": bases_count,
        "years_range": years_range,
        "top_journals": top_journals
    }
