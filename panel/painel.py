import logging
import sys
import os
from pathlib import Path
from datetime import datetime

# Garantir que o diretório raiz está no sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from config import LOG_FORMAT, LOG_LEVEL, MUNICIPIO, UF
from database import get_timeseries, init_db, list_indicators
from etl.ibge import get_pib_timeseries
from utils.status_check import get_indicator_status

# Imports do mesmo pacote (usar relativo para robustez)
from .executivo import create_executive_dashboard
from .indicator_catalog import get_indicator_info

# Agrupamento de indicadores por seção do painel (para navegação)
SECAO_POR_FONTE = {
    "IBGE": "Visão Geral",
    "CAGED": "Mercado de Trabalho",
    "CAGED_NOVO": "Mercado de Trabalho",
    "RAIS": "Mercado de Trabalho",
    "SEBRAE": "Empreendedorismo",
    "SEFAZ_MG": "Finanças Públicas",
    "SNIS": "Saneamento e Saúde",
    "DATASUS": "Saneamento e Saúde",
    "SUSTENTABILIDADE": "Sustentabilidade",
    "IDSC": "Sustentabilidade",
    "CIDADES_SUSTENTAVEIS": "Sustentabilidade",
    "INEP": "Educação",
    "INEP_RAW": "Educação",
    "IBGE_EDUCACAO": "Educação",
}
SECAO_PADRAO = "Outros"

TITULO_SECRETARIA = "Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação"

# Importar catálogo
try:
    from config.indicators import CATALOGO_INDICADORES
except ImportError:
    CATALOGO_INDICADORES = {}

def configure_logging() -> None:
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)

configure_logging()
logger = logging.getLogger(__name__)

# Inicializar banco
init_db()

# --- Deferir imports pesados ---
def lazy_estimar_pib(*args, **kwargs):
    from analytics.estimativa_pib import estimar_pib
    return estimar_pib(*args, **kwargs)

def lazy_salvar_estimativa(*args, **kwargs):
    from analytics.estimativa_pib import salvar_estimativa
    return salvar_estimativa(*args, **kwargs)

def lazy_get_estimativa_stored(*args, **kwargs):
    from analytics.estimativa_pib import get_estimativa_stored
    return get_estimativa_stored(*args, **kwargs)

def lazy_analisar_tendencia(*args, **kwargs):
    from analytics.tendencias import analisar_tendencia
    return analisar_tendencia(*args, **kwargs)

def lazy_gerar_relatorio_docx(*args, **kwargs):
    from reports.report_docx import gerar_relatorio_docx
    return gerar_relatorio_docx(*args, **kwargs)

def lazy_gerar_apresentacao_ppt(*args, **kwargs):
    from reports.slide_builder import gerar_apresentacao_ppt
    return gerar_apresentacao_ppt(*args, **kwargs)

def lazy_create_metrics_dashboard(*args, **kwargs):
    from monitoring.metrics_dashboard import create_metrics_dashboard
    return create_metrics_dashboard(*args, **kwargs)

# Cache de funções para performance
@st.cache_data(ttl=3600)
def cached_list_indicators():
    return list_indicators()

@st.cache_data(ttl=900)
def cached_get_timeseries(key, source=None):
    return get_timeseries(key, source)

def get_secao_by_key(key):
    # Tenta encontrar no catálogo a fonte
    info = CATALOGO_INDICADORES.get(key, {})
    fonte = info.get("fonte")
    return SECAO_POR_FONTE.get(fonte, SECAO_PADRAO)

INDICATOR_MAPPING = {
    "Visão Geral": ["POPULACAO", "PIB_TOTAL", "PIB_PER_CAPITA"],
    "Economia": ["PIB_TOTAL", "PIB_AGROPECUARIA", "PIB_INDUSTRIA", "PIB_SERVICOS", "PIB_ADM_PUBLICA"],
    "Trabalho & Renda": ["EMPREGOS_RAIS", "SALARIO_MEDIO"],
    "Negócios": ["EMPRESAS_ATIVAS", "EMPREGOS_SEBRAE"],
    "Finanças Públicas": ["RECEITA_VAF", "RECEITA_ICMS"],
    "Saneamento e Saúde": ["MORTALIDADE_INFANTIL", "SNIS_AGUA", "SNIS_ESGOTO"],
    "Educação": ["MATRICULAS_TOTAL", "IDEB_ANOS_INICIAIS"],
    "Sustentabilidade": ["EMISSOES_GEE", "IDSC_GERAL"]
}

st.set_page_config(
    page_title=TITULO_SECRETARIA,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Modern Design System (CSS) ---
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
<style>
    html, body, [class*="st-"] { font-family: 'Outfit', sans-serif !important; }
    .stApp { background-color: #f1f5f9; background-image: radial-gradient(#cbd5e1 0.5px, transparent 0.5px); background-size: 24px 24px; }
    [data-testid="stMetricValue"] { font-size: 2.2rem !important; font-weight: 700 !important; color: #0f172a !important; letter-spacing: -0.02em; }
    [data-testid="stMetricLabel"] { color: #475569 !important; font-size: 0.95rem !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-card { background: white; padding: 24px; border-radius: 16px; border-left: 5px solid #2563eb; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); margin-bottom: 20px; }
    .metric-card:hover { transform: translateY(-4px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); border-left-color: #1d4ed8; }
    .stPlotlyChart { background: white; padding: 15px; border-radius: 16px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }
    section[data-testid="stSidebar"] { background-color: #0f172a !important; }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p { color: #f8fafc !important; }
    section[data-testid="stSidebar"] .stSelectbox label, section[data-testid="stSidebar"] .stSelectbox p { color: #cbd5e1 !important; }
    h1, h2, h3 { color: #0f172a !important; font-weight: 700 !important; font-family: 'Outfit', sans-serif !important; }
    hr { margin: 2em 0 !important; border: 0; height: 1px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(0,0,0,0.1), rgba(0,0,0,0)); }
</style>
""", unsafe_allow_html=True)

def render_visao_geral(ano_inicio, ano_fim, modo):
    st.title(f"📍 {MUNICIPIO} / {UF}")
    st.markdown("### Visão Geral do Município")
    
    col1, col2, col3 = st.columns(3)
    
    keys = INDICATOR_MAPPING["Visão Geral"]
    for i, key in enumerate(keys):
        df = cached_get_timeseries(key)
        if not df.empty:
            df = df[(df["Ano"] >= ano_inicio) & (df["Ano"] <= ano_fim)]
            if not df.empty:
                val = df.iloc[-1]["Valor"]
                unit = df.iloc[-1]["Unidade"]
                with [col1, col2, col3][i]:
                    st.metric(label=CATALOGO_INDICADORES.get(key, {}).get("nome", key), value=f"{val:,.0f} {unit}")

def render_pib_estimado(ano_inicio, ano_fim):
    st.subheader("Estimativa do PIB de Governador Valadares")
    
    df_prev = lazy_get_estimativa_stored()
    if df_prev.empty:
        st.info("Nenhuma estimativa salva no banco. Gerando nova (pode demorar)...")
        df_prev = lazy_estimar_pib()
    
    if not df_prev.empty:
        st.plotly_chart(px.line(df_prev, x="Ano", y="Valor", color="Tipo", markers=True, title="Previsão PIB"), use_container_width=True)
    else:
        st.warning("Não foi possível gerar estimativa.")

def render_relatorios(ano_ini, ano_fim):
    st.subheader("Central de Relatórios e Apresentações")
    col_docx, col_ppt = st.columns(2)
    with col_docx:
        if st.button("Gerar Relatório Word"):
             with st.spinner("Processando..."):
                 try:
                     docx_p = lazy_gerar_relatorio_docx(ano_ini, ano_fim)
                     with open(docx_p, "rb") as f:
                         st.download_button("📥 Baixar DOCX", f, file_name=Path(docx_p).name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                     st.success("Relatório gerado!")
                 except Exception as e:
                     st.error(f"Erro: {e}")

    with col_ppt:
        if st.button("Gerar PPT"):
             with st.spinner("Processando..."):
                 try:
                     ppt_p = lazy_gerar_apresentacao_ppt(ano_ini, ano_fim)
                     with open(ppt_p, "rb") as f:
                         st.download_button("📥 Baixar PPT", f, file_name=Path(ppt_p).name, mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
                     st.success("Apresentação gerada!")
                 except Exception as e:
                     st.error(f"Erro: {e}")

def render_outras_paginas(pagina, ano_inicio, ano_fim, modo):
    keys_secao = INDICATOR_MAPPING.get(pagina, [])
    all_inds = cached_list_indicators()
    inds_to_show = [i for i in all_inds if i["indicator_key"] in keys_secao or get_secao_by_key(i["indicator_key"]) == pagina]

    for item in inds_to_show:
        df = cached_get_timeseries(item["indicator_key"], source=item["source"])
        if df.empty: continue
        df = df[(df["Ano"] >= ano_inicio) & (df["Ano"] <= ano_fim)]
        if df.empty: continue
        
        meta = get_indicator_info(item["indicator_key"])
        st.subheader(meta.get("nome", item["indicator_key"]))
        st.plotly_chart(px.line(df, x="Ano", y="Valor", markers=True), use_container_width=True)
        
        if modo == "Técnico":
            with st.expander("📊 Detalhes Técnicos"):
                st.write(lazy_analisar_tendencia(df))
                st.dataframe(df)

def render_metodologia():
    st.markdown("""
    ## 📈 Metodologia de Estimativas
    ### PIB Estimado
    A estimativa utiliza metodologia híbrida com proxies locais.
    ### Indicadores Derivados
    PIB per Capita = PIB Total / População
    """)

def main() -> None:
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo_prefeitura.png")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)
    
    st.sidebar.title("Painel GV")
    modo = st.sidebar.selectbox("Modo de Visão", ["Institucional", "Técnico", "Divulgação Pública"])
    
    abas = ["Visão Geral", "Economia", "Trabalho & Renda", "Negócios", "Educação", "Saúde", "Sustentabilidade", "Metodologia", "PIB Estimado", "Dashboard Executivo", "Métricas do Sistema", "Relatórios"]
    if modo == "Divulgação Pública":
        abas = [a for a in abas if a not in ["Relatórios", "Dashboard Executivo", "Métricas do Sistema", "PIB Estimado"]]
        
    pagina = st.sidebar.radio("Navegação", abas)
    ano_inicio = st.sidebar.number_input("Ano Inicial", 2000, 2030, 2018)
    ano_fim = st.sidebar.number_input("Ano Final", 2000, 2030, datetime.now().year)

    if pagina == "Visão Geral": render_visao_geral(ano_inicio, ano_fim, modo)
    elif pagina == "PIB Estimado": render_pib_estimado(ano_inicio, ano_fim)
    elif pagina == "Dashboard Executivo": create_executive_dashboard()
    elif pagina == "Métricas do Sistema": lazy_create_metrics_dashboard()
    elif pagina == "Relatórios": render_relatorios(ano_inicio, ano_fim)
    elif pagina == "Metodologia": render_metodologia()
    else: render_outras_paginas(pagina, ano_inicio, ano_fim, modo)

if __name__ == "__main__":
    main()
