"""
AcademicOmniSearch: Multi-Database Academic Harvester
Interface com design system inspirado na Resend (dark-first, artesanal, minimalista).
"""

import os
import streamlit as st
import pandas as pd
import time
import logging
from typing import Dict, List, Any

# Configuração de logging estruturado para console e Streamlit Cloud
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("AcademicOmniSearch.App")

from src import (
    BrapciScraper,
    PubmedScraper,
    AcmScraper,
    IeeeScraper,
    ScopusScraper,
    CapesScraper
)
from utils.data_export import (
    normalize_dataframe,
    export_to_excel,
    remove_duplicates,
    get_summary_metrics
)
from utils.bibliographic_exporter import BibliographicExporter
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
        "Periódicos CAPES (MEC/CAPES)": "capes",
        "BRAPCI (Ciência da Informação)": "brapci",
        "PubMed (Saúde & Biomédica)": "pubmed",
        "ACM Digital Library (Computação)": "acm",
        "IEEE Xplore (Engenharia)": "ieee",
        "Scopus (Elsevier)": "scopus"
    }

    selected_labels = st.multiselect(
        "Bases de Dados Alvo",
        options=list(available_bases.keys()),
        default=[
            "Periódicos CAPES (MEC/CAPES)",
            "BRAPCI (Ciência da Informação)",
            "PubMed (Saúde & Biomédica)"
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
        botao_pesquisar = st.button("Iniciar Pesquisa", type="primary", width="stretch")

    st.markdown('</div>', unsafe_allow_html=True)



# --- Função de Coleta Orquestrada ---
def executar_busca_multibase(
    termo: str,
    bases: List[str],
    ano_de: int,
    ano_ate: int,
    campo: str,
    max_reg: int
) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
    todos_registros: List[Dict[str, Any]] = []
    diagnostics: Dict[str, Any] = {
        "bases": {},
        "all_logs": []
    }

    progress_bar = st.progress(0)
    status_text = st.empty()

    # Verificação de proxy e Zyte API em st.secrets ou variáveis de ambiente
    proxy_val = None
    zyte_key = None
    try:
        proxy_val = st.secrets.get("BRAPCI_PROXY") or st.secrets.get("CAPES_PROXY")
    except Exception:
        pass
    if not proxy_val:
        proxy_val = os.getenv("CAPES_PROXY") or os.getenv("BRAPCI_PROXY")

    try:
        zyte_key = st.secrets.get("ZYTE_API_KEY")
    except Exception:
        pass
    if not zyte_key:
        zyte_key = os.getenv("ZYTE_API_KEY")

    # Instanciação dos scrapers com passagem do max_por_base para os coletores
    scrapers_map = {
        "capes": CapesScraper(max_por_base=max_reg, zyte_api_key=zyte_key, proxy=proxy_val),
        "brapci": BrapciScraper(max_por_base=max_reg, proxy=proxy_val),
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
            diagnostics["bases"][scraper.name] = {
                "status": getattr(scraper, "last_status", f"Concluído ({len(records)} registros)"),
                "count": len(records),
                "logs": getattr(scraper, "logs", [])
            }
            diagnostics["all_logs"].extend(getattr(scraper, "logs", []))
        except Exception as e:
            err_msg = f"Exceção inesperada: {type(e).__name__}: {e}"
            logger.error(f"Erro em {scraper.name}: {err_msg}")
            diagnostics["bases"][scraper.name] = {
                "status": f"Falha ({type(e).__name__})",
                "count": 0,
                "logs": [f"[{scraper.name}] {err_msg}"]
            }
            diagnostics["all_logs"].append(f"[{scraper.name}] {err_msg}")
            st.toast(f"Aviso em {scraper.name}: {e}", icon="⚠️")

        progress_bar.progress((idx + 1) / total_bases)

    time.sleep(0.3)
    status_text.empty()
    progress_bar.empty()

    return todos_registros, diagnostics


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
            raw_records, diagnostics = executar_busca_multibase(
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
        st.session_state["diagnostics"] = diagnostics


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

        # Barra de Ações: Filtro Dinâmico + Downloads (Excel, RIS, BibTeX)
        col_filtro, col_down_xlsx, col_down_ris, col_down_bib = st.columns([2.2, 1.1, 0.9, 0.9])
        
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
                label="📥 Excel (.xlsx)",
                data=excel_bytes,
                file_name=f"metadata_{nome_arquivo}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch"
            )

        with col_down_ris:
            ris_text = BibliographicExporter.to_ris(df_atual.to_dict(orient="records"))
            st.download_button(
                label="📥 RIS (.ris)",
                data=ris_text.encode("utf-8"),
                file_name=f"export_{nome_arquivo}.ris",
                mime="application/x-research-info-systems",
                width="stretch",
                help="Formato compatível com Zotero, Mendeley e EndNote."
            )

        with col_down_bib:
            bib_text = BibliographicExporter.to_bibtex(df_atual.to_dict(orient="records"))
            st.download_button(
                label="📥 BibTeX (.bib)",
                data=bib_text.encode("utf-8"),
                file_name=f"export_{nome_arquivo}.bib",
                mime="application/x-bibtex",
                width="stretch",
                help="Formato compatível com LaTeX e Overleaf."
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
            width="stretch",
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
                "Base": st.column_config.TextColumn("Base", width="small"),
                "Qualis": st.column_config.TextColumn("Qualis", width="small"),
                "Citações (OpenAlex)": st.column_config.NumberColumn("Citações", width="small"),
                "FWCI": st.column_config.NumberColumn("FWCI", format="%.2f", width="small"),
                "ISSN": st.column_config.TextColumn("ISSN", width="small")
            }
        )

    else:
        st.markdown(
            """
            <div style="background-color: #ffffff; border: 1px solid #e4e4e7; border-radius: 8px; padding: 28px; text-align: center; color: #71717a; margin-top: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                <p style="margin: 0; font-size: 0.95rem; color: #09090b; font-weight: 500;">Nenhum metadado retornado com os parâmetros selecionados.</p>
                <p style="margin: 4px 0 0 0; font-size: 0.85rem; color: #71717a;">Verifique os logs detalhados abaixo para identificar se alguma base retornou bloqueio ou restrição de rede.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 6. Painel de Diagnóstico Técnico e Logs das Bases
    if "diagnostics" in st.session_state:
        diag = st.session_state["diagnostics"]
        all_logs = diag.get("all_logs", [])
        bases_info = diag.get("bases", {})

        with st.expander("🔍 Logs e Diagnóstico Detalhado das Requisições", expanded=df_atual.empty):
            # Status cards das bases consultadas
            if bases_info:
                cols = st.columns(len(bases_info))
                for idx, (b_name, b_data) in enumerate(bases_info.items()):
                    with cols[idx]:
                        b_status = b_data.get("status", "")
                        is_ok = "Sucesso" in b_status or b_data.get("count", 0) > 0
                        color = "#10b981" if is_ok else "#ef4444"
                        st.markdown(
                            f"""
                            <div style="background-color: #ffffff; border: 1px solid #e4e4e7; border-radius: 6px; padding: 10px 14px; margin-bottom: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                                <div style="font-size: 11px; text-transform: uppercase; color: #71717a; font-weight: 600;">{b_name}</div>
                                <div style="font-size: 13px; font-weight: 500; color: {color}; margin-top: 2px;">
                                    {b_status}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            # Alerta explicativo caso haja bloqueio de datacenter/cloud na BRAPCI
            brapci_data = bases_info.get("BRAPCI", {})
            if "Bloqueio de IP da Nuvem" in brapci_data.get("status", "") or any("cip.brapci.inf.br Port 443" in str(log) for log in all_logs):
                st.markdown(
                    """
                    <div style="background-color: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #f59e0b; border-radius: 6px; padding: 12px 16px; margin: 12px 0; font-size: 0.88rem; color: #92400e;">
                        <strong style="color: #b45309;">💡 Nota Técnica sobre a BRAPCI em Nuvem (Streamlit Cloud):</strong>
                        <p style="margin: 4px 0 0 0; line-height: 1.45;">
                            O servidor Apache da UFPR (<code>cip.brapci.inf.br</code>) bloqueia conexões diretas vindas de datacenters da <strong>Amazon AWS</strong> (onde o Streamlit Cloud executa seus containers).<br>
                            O scraper e o código estão 100% corretos: para pesquisar na BRAPCI sem restrições, <strong>execute a aplicação localmente no seu computador</strong> (<code>uv run streamlit run app.py</code>) onde seu IP residencial/brasileiro é aceito sem bloqueio, ou adicione um proxy em <code>st.secrets["BRAPCI_PROXY"]</code>.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if all_logs:
                log_content = "\n".join(all_logs)
                st.code(log_content, language="text")
            else:
                st.caption("Nenhum log gerado na execução.")
