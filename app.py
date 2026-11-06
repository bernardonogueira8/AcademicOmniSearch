"""
AcademicOmniSearch: Multi-Database Academic Harvester
Interface com design system inspirado na Resend (dark-first, artesanal, minimalista).
"""

import streamlit as st
import pandas as pd
import time
from typing import Dict, List, Any

from src import (
    BrapciScraper,
    PubmedScraper,
    AcmScraper,
    IeeeScraper,
    ScopusScraper
)
from utils.data_export import (
    normalize_dataframe,
    export_to_excel,
    remove_duplicates,
    get_summary_metrics
)
from utils.config import STANDARD_COLUMNS

# --- Configuração da Página ---
st.set_page_config(
    page_title="AcademicOmniSearch",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Design System Resend (Injeção de CSS Customizado) ---
st.markdown(
    """
    <style>
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif !important;
    }
    h1, h2, h3, h4 {
        font-weight: 600 !important;
        letter-spacing: -0.03em !important;
    }

    .stTextInput > div > div > input {
        border-radius: 8px !important;
        padding: 14px 18px !important;
        font-size: 1.05rem !important;
    }

    .params-container {
        border-radius: 10px;
        padding: 20px 24px;
        margin-top: 12px;
        margin-bottom: 20px;
    }
    div.stButton > button[kind="primary"] {
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08) !important;
        transition: all 0.15s ease-in-out !important;
    }

    .resend-status-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px 16px;
        font-size: 13px;
        color: #52525b;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }

    /* 7. Tabela de Metadados Light */
    [data-testid="stDataFrame"] {
        border: 1px solid #e4e4e7 !important;
        border-radius: 8px !important;
        background-color: #ffffff !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Cabeçalho e Identidade Visual (Resend Inspired) ---
st.markdown(
    """
    <div style="padding-top: 10px; margin-bottom: 24px;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
            <span style="font-weight: 600; font-size: 1.15rem; letter-spacing: -0.02em;">AcademicOmniSearch</span>
            <span style="font-size: 11px; border: 1px solid #e4e4e7; border-radius: 4px; padding: 2px 6px;  font-family: monospace;">v0.1.0</span>
        </div>
        <p style="margin: 0; font-size: 0.95rem; color: #52525b;">
            Recuperação massiva e padronizada de metadados em bases acadêmicas nacionais e internacionais.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- 1. Grande Campo de Pesquisa ---
termo_busca = st.text_input(
    label="Chave de pesquisa",
    value="",
    placeholder="Digite palavras-chave, título, autor ou assunto (ex: machine learning, bioinformática, inteligência artificial)...",
    label_visibility="collapsed"
)

# --- 2. Parâmetros de Pesquisa (Abaixo do Campo de Busca) ---
with st.container():  
    # Linha A: Seleção de Bases de Dados
    available_bases = {
        "BRAPCI (Ciência da Informação - API v5)": "brapci",
        "PubMed (Saúde & Biomédica - NCBI API)": "pubmed",
        "ACM Digital Library (Computação - HTML/Dump)": "acm",
        "IEEE Xplore (Engenharia - API Oficial)": "ieee",
        "Scopus (Elsevier - API Oficial)": "scopus"
    }

    selected_labels = st.multiselect(
        "Bases de Dados Alvo",
        options=list(available_bases.keys()),
        default=[
            "BRAPCI (Ciência da Informação - API v5)",
            "PubMed (Saúde & Biomédica - NCBI API)",
            "ACM Digital Library (Computação - HTML/Dump)"
        ],
        help="Escolha as bases para busca agregada e unificada."
    )
    selected_bases = [available_bases[l] for l in selected_labels]

    # Linha B: Campos refinados (Campo, Intervalo de Anos, Limite)
    col_campo, col_periodo, col_limite = st.columns([1.2, 1.2, 1])
    
    with col_campo:
        campo_busca = st.selectbox(
            "Campo a pesquisar",
            ["Todos", "Título", "Palavras-Chave", "Autores", "Resumo", "Texto completo"],
            index=0
        )

    with col_periodo:
        col_ini, col_fim = st.columns(2)
        with col_ini:
            ano_inicial = st.number_input("Ano De", min_value=1950, max_value=2030, value=2020, step=1)
        with col_fim:
            ano_final = st.number_input("Até", min_value=1950, max_value=2030, value=2026, step=1)

    with col_limite:
        max_por_base = st.number_input(
            "Limite por base",
            min_value=10,
            max_value=100,
            value=20,
            step=10,
            help="Define o page_size / limite máximo recuperado em cada base."
        )

    # Linha C: Opções discretas
    col_opt1, col_opt2 = st.columns([2, 1])
    with col_opt1:
        deduplicar = st.checkbox("Remover duplicatas exatas por título", value=True)
    with col_opt2:
        botao_pesquisar = st.button("Iniciar Pesquisa", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)



# --- Função de Coleta Orquestrada ---
def executar_busca_multibase(
    termo: str,
    bases: List[str],
    ano_de: int,
    ano_ate: int,
    campo: str,
    max_reg: int
) -> List[Dict[str, Any]]:
    todos_registros: List[Dict[str, Any]] = []

    progress_bar = st.progress(0)
    status_text = st.empty()

    # Instanciação dos scrapers com passagem do max_por_base para o brapci
    scrapers_map = {
        "brapci": BrapciScraper(max_por_base=max_reg),
        "pubmed": PubmedScraper(),
        "acm": AcmScraper(local_html_path="test/app.html"),
        "ieee": IeeeScraper(),
        "scopus": ScopusScraper()
    }

    total_bases = len(bases)
    for idx, base_key in enumerate(bases):
        scraper = scrapers_map.get(base_key)
        if not scraper:
            continue

        status_text.markdown(f"<span style='color: #71717a; font-size: 13px;'>Consultando <b>{scraper.name}</b>...</span>", unsafe_allow_html=True)
        try:
            records = scraper.search(
                query=termo,
                year_start=ano_de,
                year_end=ano_ate,
                field=campo,
                max_results=max_reg,
                max_por_base=max_reg
            )
            todos_registros.extend(records)
        except Exception as e:
            st.toast(f"Aviso em {scraper.name}: {e}", icon="⚠️")

        progress_bar.progress((idx + 1) / total_bases)

    time.sleep(0.3)
    status_text.empty()
    progress_bar.empty()

    return todos_registros


# --- Processamento da Ação de Busca ---
if botao_pesquisar:
    if not termo_busca.strip():
        st.warning("Informe um termo para pesquisa.")
    elif not selected_bases:
        st.warning("Selecione pelo menos uma base acadêmica.")
    elif ano_inicial > ano_final:
        st.error(f"Ano inicial ({ano_inicial}) maior que o ano final ({ano_final}).")
    else:
        with st.spinner("Extraindo metadados das bases..."):
            raw_records = executar_busca_multibase(
                termo=termo_busca,
                bases=selected_bases,
                ano_de=ano_inicial,
                ano_ate=ano_final,
                campo=campo_busca,
                max_reg=max_por_base
            )

        df = normalize_dataframe(raw_records)

        if deduplicar and not df.empty:
            df = remove_duplicates(df, subset_cols=["Title"])

        st.session_state["dataset"] = df
        st.session_state["termo_pesquisado"] = termo_busca


# --- 4. Exibição Minimalista de Métricas & Tabela Padronizada ---
if "dataset" in st.session_state:
    df_atual = st.session_state["dataset"]

    if not df_atual.empty:
        metrics = get_summary_metrics(df_atual)
        
        # Badges das bases
        badges_html = " ".join([
            f"<span class='resend-badge'>{base}: {count}</span>"
            for base, count in metrics["bases_count"].items()
        ])

        # Barra de status minimalista (estilo Resend Light)
        st.markdown(
            f"""
            <div class="resend-status-bar">
                <div>
                    <span class="resend-status-dot"></span>
                    <strong style="color: #09090b;">{metrics['total_records']} publicações</strong> encontradas
                    <span style="color: #a1a1aa; margin: 0 8px;">·</span>
                    Janela: <span style="color: #09090b; font-weight: 500;">{metrics['years_range']}</span>
                    <span style="color: #a1a1aa; margin: 0 8px;">·</span>
                    {df_atual['Revista / Fonte'].nunique()} fontes catalogadas
                </div>
                <div>
                    {badges_html}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Barra de Ações: Filtro Dinâmico + Download Excel
        col_filtro, col_down_xlsx = st.columns([3.8, 1.2])
        
        with col_filtro:
            filtro_tabela = st.text_input(
                "Filtrar na tabela",
                placeholder="Filtrar por título, autor, periódico ou ano...",
                label_visibility="collapsed"
            )

        nome_arquivo = st.session_state.get("termo_pesquisado", "academico").replace(" ", "_")

        with col_down_xlsx:
            excel_bytes = export_to_excel(df_atual, name_table=nome_arquivo[:31])
            st.download_button(
                label="📥 Baixar Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"metadata_{nome_arquivo}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        
        # Aplicação do filtro na visualização
        if filtro_tabela:
            mask = (
                df_atual["Title"].str.contains(filtro_tabela, case=False, na=False) |
                df_atual["Autor"].str.contains(filtro_tabela, case=False, na=False) |
                df_atual["Revista / Fonte"].str.contains(filtro_tabela, case=False, na=False) |
                df_atual["Ano"].str.contains(filtro_tabela, case=False, na=False)
            )
            df_view = df_atual[mask]
        else:
            df_view = df_atual

        # 5. Tabela de Metadados Padronizada (Foco Central da UI)
        st.dataframe(
            df_view,
            use_container_width=True,
            height=460,
            column_config={
                "Link Pub": st.column_config.LinkColumn(
                    "Link",
                    help="Link direto ou DOI da publicação",
                    display_text="Acessar"
                ),
                "Title": st.column_config.TextColumn("Título", width="large"),
                "Autor": st.column_config.TextColumn("Autor(es)", width="medium"),
                "Revista / Fonte": st.column_config.TextColumn("Revista / Fonte", width="medium"),
                "Ano": st.column_config.TextColumn("Ano", width="small"),
                "Base": st.column_config.TextColumn("Base", width="small")
            }
        )

    else:
        st.markdown(
            """
            <div style="background-color: #ffffff; border: 1px solid #e4e4e7; border-radius: 8px; padding: 28px; text-align: center; color: #71717a; margin-top: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <p style="margin: 0; font-size: 0.95rem; color: #09090b; font-weight: 500;">Nenhum metadado retornado com os parâmetros selecionados.</p>
                <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #71717a;">Tente ampliar a janela temporal ou utilizar palavras-chave mais abrangentes.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
