"""
Painel interno Streamlit – Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação.
# v1.0.3 - Restored and fixed sources
Exibe todos os indicadores do banco em gráficos e permite gerar relatório em formato Word (.docx).
"""
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
from utils.status_check import get_indicator_status
from utils.analytics import inject_google_analytics

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

# --- Deferir imports pesados (Lazy Loading para Estabilidade no Deploy) ---
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

def lazy_create_executive_dashboard(*args, **kwargs):
    from panel.executivo import create_executive_dashboard
    return create_executive_dashboard(*args, **kwargs)

def lazy_create_metrics_dashboard(*args, **kwargs):
    from monitoring.metrics_dashboard import create_metrics_dashboard
    return create_metrics_dashboard(*args, **kwargs)

def lazy_get_indicator_info(*args, **kwargs):
    from panel.indicator_catalog import get_indicator_info
    return get_indicator_info(*args, **kwargs)

# Cache de funções para performance
@st.cache_data(ttl=3600, show_spinner="Buscando dados...")
def cached_get_timeseries(indicator_key, source=None):
    return get_timeseries(indicator_key, source)

@st.cache_data(ttl=3600)
def cached_list_indicators():
    return list_indicators()

# Mapa de Indicadores para Abas Fixas
INDICATOR_MAPPING = {
    "Visão Geral": ["POPULACAO", "POPULACAO_DETALHADA", "IDHM", "GINI"],
    "Economia": ["PIB_TOTAL", "PIB_PER_CAPITA", "PIB_ESTIMADO", "PIB_CRESCIMENTO", "RECEITA_VAF", "RECEITA_ICMS"],
    "Trabalho & Renda": ["EMPREGOS_RAIS", "EMPREGOS_CAGED", "SALDO_CAGED_MENSAL", "SALDO_CAGED_ANUAL", "SALDO_CAGED", "NUM_EMPRESAS", "EMPRESAS_ATIVAS", "SEBRAE_GERAL", "EMPREGOS_SEBRAE", "EMPREENDEDORES_MEI", "SALARIO_MEDIO_MG"],
    "Educação": ["MATRICULAS_TOTAL", "ESCOLAS_FUNDAMENTAL", "IDEB_ANOS_INICIAIS", "IDEB_ANOS_FINAIS", "TAXA_APROVACAO_FUNDAMENTAL"],
    "Saúde": ["MORTALIDADE_INFANTIL", "OBITOS_TOTAL"],
    "Sustentabilidade": ["IDSC_GERAL", "INDICE_SUSTENTABILIDADE", "EMISSOES_GEE", "SEEG_AR", "SEEG_GASES", "AREA_URBANA", "VEGETACAO_NATIVA", "USO_AGROPECUARIO"],
    "Negócios": ["EMPRESAS_FORMAIS", "SEBRAE_GERAL", "ESTABELECIMENTOS_SEBRAE"],
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
    section[data-testid="stSidebar"] .stSelectbox label, section[data-testid="stSidebar"] .stSelectbox p, section[data-testid="stSidebar"] .stRadio label { color: #cbd5e1 !important; }
    h1, h2, h3 { color: #0f172a !important; font-weight: 700 !important; font-family: 'Outfit', sans-serif !important; }
    hr { margin: 2em 0 !important; border: 0; height: 1px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(0,0,0,0.1), rgba(0,0,0,0)); }
</style>
""", unsafe_allow_html=True)

# Importar componentes visuais premium
try:
    from utils.visual_components import metric_card, apply_institutional_layout
except ImportError:
    # Fallback simples se o arquivo não existir (segurança)
    def metric_card(label, value, sublabel="", border_color="#2563eb"):
        st.metric(label, value, sublabel)
    
    def apply_institutional_layout(fig, title="", source=""):
        fig.update_layout(title=title)
        return fig

def card_plotly(label, value, delta=None, unit="", fonte=""):
    """
    Mantido para retrocompatibilidade onde ainda for usado, 
    mas idealmente deve ser substituído por metric_card nas KPIs.
    """
    fig = go.Figure(go.Indicator(
        mode="number+delta" if delta is not None else "number",
        value=value,
        number={"suffix": f" {unit}" if unit else ""},
        delta={"reference": value - (delta or 0)} if delta is not None else None,
        title={"text": f"{label}<br><span style='font-size:0.8em;color:gray'>{fonte}</span>"},
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=10, t=30, b=10), height=150,
    )
    return fig

def fmt_br(val: float, currency: bool = False, decimals: int = 0) -> str:
    try:
        if pd.isna(val) or val is None: return "N/D"
        if decimals == 0 and abs(val - round(val)) < 1e-9:
            s = f"{int(val):,}".replace(",", ".")
        else:
            fmt_str = "{:,.%df}" % decimals
            s = fmt_str.format(val).replace(",", "X").replace(".", ",").replace("X", ".")
        if currency: return f"R$ {s}"
        return s
    except Exception: return str(val)

def render_indicator_header(indicator_key: str, source: str, title: str):
    status = get_indicator_status(indicator_key, source)
    badge = ""
    if status["status"] == "error":
        badge = f' <span style="color:red;font-size:0.8em;">{status["message"]} — <a href="{status["url"]}" target="_blank">{status["url"]}</a></span>'
    elif status["status"] == "update":
        badge = f' <span style="color:orange;font-size:0.8em;">{status["message"]} — <a href="{status["url"]}" target="_blank">{status["url"]}</a></span>'
    st.markdown(f"### {title}{badge}", unsafe_allow_html=True)

def get_pib_per_capita_df():
    df_pib = cached_get_timeseries("PIB_TOTAL", "IBGE")
    df_pop = cached_get_timeseries("POPULACAO_DETALHADA", "IBGE/SIDRA")
    if df_pop.empty: df_pop = cached_get_timeseries("POPULACAO", "IBGE")
    if df_pib.empty or df_pop.empty: return pd.DataFrame()
    merged = pd.merge(df_pib, df_pop, on="Ano", suffixes=("_pib", "_pop"))
    if merged.empty: return pd.DataFrame()
    merged = merged.sort_values("Ano")
    merged["Valor"] = merged["Valor_pib"] / merged["Valor_pop"]
    merged["Unidade"] = "R$ / Hab"
    return merged[["Ano", "Valor", "Unidade"]]

def get_pib_growth_df():
    df_pib = cached_get_timeseries("PIB_TOTAL", "IBGE")
    if df_pib.empty or len(df_pib) < 2: return pd.DataFrame()
    df_pib = df_pib.sort_values("Ano")
    df_pib["Valor"] = df_pib["Valor"].pct_change() * 100
    df_pib["Unidade"] = "%"
    return df_pib.dropna(subset=["Valor"])

def get_secao_by_key(key: str) -> str:
    for secao, keys in INDICATOR_MAPPING.items():
        if key in keys: return secao
    info = CATALOGO_INDICADORES.get(key, {})
    fonte = info.get("fonte")
    return SECAO_POR_FONTE.get(fonte, SECAO_PADRAO)

# --- PAGE RENDERING FUNCTIONS ---

def render_visao_geral(ano_inicio, ano_fim, modo):
    st.subheader("Destaques do Município")
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px; border-radius: 12px; color: white; margin-bottom: 30px;">
        <h2 style="color: white !important; margin: 0;">Bem-vindo ao Observatório de {MUNICIPIO}</h2>
        <p style="margin: 10px 0 0 0; opacity: 0.9;">Acompanhe em tempo real os principais indicadores econômicos, sociais e de sustentabilidade de nossa cidade.</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📍 Localização Estratégica")
    col_map, col_info = st.columns([2, 1])
    with col_map:
        try:
            import folium
            from streamlit_folium import folium_static
            m = folium.Map(location=[-18.8511, -41.9503], zoom_start=12)
            folium.Marker([-18.8511, -41.9503], popup=MUNICIPIO).add_to(m)
            folium_static(m, width=700, height=300)
        except Exception: st.info("Mapa indisponível no momento.")
    with col_info:
        st.write(f"**Município:** {MUNICIPIO}/{UF}")
        st.write("**Região:** Vale do Rio Doce")
        st.write("**Latitude:** -18.85")
        st.write("**Longitude:** -41.95")

    st.divider()

    col1, col_pib, col_pc, col_gr = st.columns(4)
    
    pop_det = cached_get_timeseries("POPULACAO_DETALHADA", "IBGE/SIDRA")
    if pop_det.empty: pop_det = cached_get_timeseries("POPULACAO", "IBGE")
    with col1:
        if not pop_det.empty:
            ult = pop_det.sort_values("Ano").iloc[-1]
            metric_card(
                "População", 
                fmt_br(ult['Valor']), 
                f"Referência: {int(ult['Ano'])}",
                border_color="#1e3a8a"
            )
        else: metric_card("População", "N/D", "Sem dados")

    pib = cached_get_timeseries("PIB_TOTAL", "IBGE")
    with col_pib:
        if not pib.empty:
            ult = pib.sort_values("Ano").iloc[-1]
            pib_bilhoes = ult['Valor'] / 1_000_000
            metric_card(
                "PIB Total", 
                f"R$ {fmt_br(pib_bilhoes, decimals=2)} bi", 
                f"Referência: {int(ult['Ano'])}", 
                border_color="#3b82f6"
            )
        else: metric_card("PIB Total", "N/D", "Sem dados")

    with col_pc:
        df_pc = get_pib_per_capita_df()
        if not df_pc.empty:
            val = df_pc.iloc[-1]['Valor']
            metric_card(
                "PIB Per Capita", 
                fmt_br(val, currency=True), 
                "IBGE (Calculado)",
                border_color="#2563eb"
            )
        else: metric_card("PIB Per Capita", "N/D", "Sem dados")

    with col_gr:
        df_gr = get_pib_growth_df()
        if not df_gr.empty:
            val = df_gr.iloc[-1]['Valor']
            metric_card(
                "Crescimento PIB", 
                f"{fmt_br(val, decimals=2)}%", 
                "Variação Anual",
                border_color="#10b981" if val >= 0 else "#ef4444"
            )
        else: metric_card("Crescimento PIB", "N/D", "Sem dados")

    st.markdown("<br>", unsafe_allow_html=True)

    col_idhm, col_gini, col_vaf, col_gee = st.columns(4)
    idhm = cached_get_timeseries("IDHM", "ATLAS_BRASIL")
    with col_idhm:
        if not idhm.empty:
            val = idhm.sort_values("Ano").iloc[-1]['Valor']
            metric_card("IDH-M", fmt_br(val, decimals=3), "Alto Desenvolvimento")
        else: metric_card("IDH-M", "N/D", "Sem dados")
    
    gini = cached_get_timeseries("GINI", "IBGE")
    with col_gini:
        if not gini.empty:
            val = gini.sort_values("Ano").iloc[-1]['Valor']
            metric_card("Índice GINI", fmt_br(val, decimals=4), "Desigualdade")
        else: metric_card("GINI", "N/D", "Sem dados")
    
    vaf = cached_get_timeseries("RECEITA_VAF", "SEFAZ_MG")
    with col_vaf:
        if not vaf.empty:
            val = vaf.iloc[-1]["Valor"] / 1_000_000
            metric_card("VAF", f"R$ {fmt_br(val, decimals=1)} M", "Valor Adicionado")
        else: metric_card("VAF", "N/D", "Sem dados")
        
    gee = cached_get_timeseries("EMISSOES_GEE", "SEEG")
    with col_gee:
        if not gee.empty:
            val = gee.iloc[-1]["Valor"]
            metric_card("Emissões GEE", f"{fmt_br(val, decimals=0)} t", "Toneladas CO2e", border_color="#15803d")
        else: metric_card("GEE", "N/D", "Sem dados")

def render_economia(ano_inicio, ano_fim, modo):
    st.title("Estrutura Produtiva e Dinâmica Econômica")
    tab1, tab2, tab3, tab4 = st.tabs([
        "📍 Visão Geral", 
        "🏗️ Estrutura Produtiva", 
        "📈 Dinâmica Temporal", 
        "🏦 Capacidade Fiscal"
    ])
    
    df_pib = cached_get_timeseries("PIB_TOTAL", "IBGE")
    
    with tab1:
        st.subheader("Indicadores Principais de Economia")
        col_e1, col_e2, col_e3 = st.columns(3)
        with col_e1:
            if not df_pib.empty:
                ult = df_pib.sort_values("Ano").iloc[-1]
                val = ult['Valor'] / 1_000_000
                metric_card("PIB Total", f"R$ {fmt_br(val, decimals=1)} bi", f"Ano: {int(ult['Ano'])}", border_color="#3b82f6")
            else: metric_card("PIB Total", "N/D", "Sem dados")
        
        with col_e2:
            df_pc = get_pib_per_capita_df()
            if not df_pc.empty:
                val = df_pc.iloc[-1]['Valor']
                metric_card("PIB per Capita", fmt_br(val, currency=True), "Riqueza/Hab", border_color="#2563eb")
            else: metric_card("PIB per Capita", "N/D", "Sem dados")
        
        with col_e3:
            df_gr = get_pib_growth_df()
            if not df_gr.empty:
                val = df_gr.iloc[-1]['Valor']
                metric_card("Crescimento PIB", f"{fmt_br(val, decimals=2)}%", "Variação Anual", border_color="#10b981" if val >= 0 else "#ef4444")
            else: metric_card("Crescimento PIB", "N/D", "Sem dados")

    with tab2:
        st.subheader("Composição do PIB e Valor Adicionado")
        setores = {
            "Agropecuária": "PIB_AGROPECUARIA",
            "Indústria": "PIB_INDUSTRIA",
            "Serviços": "PIB_SERVICOS",
            "Adm. Pública": "PIB_ADM_PUBLICA"
        }
        df_pie = []
        for label, key in setores.items():
            df_s = cached_get_timeseries(key, "IBGE")
            if not df_s.empty:
                ult = df_s.sort_values("Ano").iloc[-1]
                df_pie.append({"Setor": label, "Valor": ult["Valor"], "Ano": ult["Ano"]})
        
        if df_pie:
            df_pie_pd = pd.DataFrame(df_pie)
            st.write(f"Dados referentes ao ano de {int(df_pie_pd['Ano'].iloc[0])}")
            fig_pie = px.pie(df_pie_pd, values='Valor', names='Setor', title="Participação Setorial no PIB")
            fig_pie = apply_institutional_layout(fig_pie, title="Participação Setorial no PIB", source="IBGE - Contas Regionais")
            st.plotly_chart(fig_pie, use_container_width=True)
        else: st.info("Dados setoriais não disponíveis.")

    with tab3:
        st.subheader("Evolução Histórica")
        if not df_pib.empty:
            df_pib_f = df_pib[(df_pib["Ano"] >= ano_inicio) & (df_pib["Ano"] <= ano_fim)]
            fig_evol = px.line(df_pib_f, x="Ano", y="Valor", markers=True, title="Evolução do PIB Nominal")
            fig_evol = apply_institutional_layout(fig_evol, title="Evolução do PIB Nominal (Série Histórica)", source="IBGE")
            st.plotly_chart(fig_evol, use_container_width=True)

    with tab4:
        st.subheader("Indicadores de Capacidade Fiscal")
        col_f1, col_f2, col_f3 = st.columns(3)
        vaf = cached_get_timeseries("RECEITA_VAF", "SEFAZ_MG")
        with col_f1:
            if not vaf.empty:
                val = vaf.iloc[-1]["Valor"] / 1_000_000
                metric_card("Valor Adic. Fiscal", f"R$ {fmt_br(val, decimals=1)} M", f"Ano: {int(vaf.iloc[-1]['Ano'])}", border_color="#f59e0b")
            else: metric_card("VAF", "N/D", "Sem dados")
        
        icms = cached_get_timeseries("RECEITA_ICMS", "SEFAZ_MG")
        with col_f2:
            if not icms.empty:
                val = icms.iloc[-1]["Valor"] / 1_000_000
                metric_card("Cota-Parte ICMS", f"R$ {fmt_br(val, decimals=1)} M", "Repasse Estadual")
            else: metric_card("ICMS", "N/D", "Sem dados")
            
        massa = cached_get_timeseries("MASSA_SALARIAL_ESTIMADA", "CAGED_ESTIMADO")
        with col_f3:
            if not massa.empty:
                val = massa.iloc[-1]["Valor"] / 1_000_000
                metric_card("Massa Salarial (Est)", f"R$ {fmt_br(val, decimals=1)} M", "Impacto Econômico", border_color="#8b5cf6")
            else: metric_card("Massa Salarial", "N/D", "Sem dados")

def render_trabalho_renda(ano_inicio, ano_fim, modo):
    st.subheader("Análise do Mercado de Trabalho e Renda")
    col1, col2, col3 = st.columns(3)
    saldo_mes = cached_get_timeseries("SALDO_CAGED_MENSAL")
    salario = cached_get_timeseries("SALARIO_MEDIO_MG")
    if salario.empty: salario = cached_get_timeseries("SALARIO_MEDIO_REAL")
    empresas = cached_get_timeseries("EMPRESAS_ATIVAS", "SEBRAE")
    if empresas.empty: empresas = cached_get_timeseries("EMPRESOS_ATIVAS")
    if empresas.empty: empresas = cached_get_timeseries("NUM_EMPRESAS")

    with col1:
        if not saldo_mes.empty:
            val = saldo_mes.iloc[-1]["Valor"]
            metric_card("Saldo Mensal (CAGED)", fmt_br(val), "Vagas C.L.T.", border_color="#10b981" if val >= 0 else "#ef4444")
        else: metric_card("Saldo Mensal", "N/D", "Sem dados")
    
    with col2:
        if not salario.empty:
            metric_card("Salário Médio", fmt_br(salario.iloc[-1]["Valor"], currency=True), "Referência Regional")
        else: metric_card("Salário Médio", "N/D", "Sem dados")
    
    with col3:
        if not empresas.empty:
            metric_card("Empresas Ativas", fmt_br(empresas.iloc[-1]["Valor"]), "Total Cadastrado")
        else: metric_card("Empresas", "N/D", "Sem dados")

    st.divider()
    col_caged, col_rais = st.columns(2)
    with col_caged:
        jobs = cached_get_timeseries("EMPREGOS_CAGED", "CAGED_NOVO")
        if jobs.empty: jobs = cached_get_timeseries("EMPREGOS_CAGED", "CAGED")
        if not jobs.empty:
            st.subheader("📈 Estoque de Empregos (CAGED)")
            fig = px.area(jobs, x="Ano", y="Valor", title="Evolução do Estoque de Empregos")
            fig = apply_institutional_layout(fig, title="Estoque de Empregos Formais", source="Novo CAGED")
            st.plotly_chart(fig, use_container_width=True)
    
    with col_rais:
        jobs_rais = cached_get_timeseries("EMPREGOS_RAIS", "RAIS")
        if not jobs_rais.empty:
            st.subheader("👔 Vínculos Formais (RAIS)")
            fig = px.line(jobs_rais, x="Ano", y="Valor", markers=True, title="Histórico RAIS")
            fig = apply_institutional_layout(fig, title="Vínculos Empregatícios (RAIS)", source="RAIS/MTE")
            st.plotly_chart(fig, use_container_width=True)

def render_pib_estimado(ano_inicio, ano_fim):
    st.subheader("Projeção do PIB Municipal")
    st.info("Visualização de projeções baseadas em modelos estatísticos reais.")
    
    if st.button("🔄 Atualizar Projeção"):
        with st.spinner("Calculando modelos..."):
            lazy_salvar_estimativa()
        st.success("Projeção atualizada!")
    
    df_hist = cached_get_timeseries("PIB_TOTAL", source="IBGE")
    df_prev = lazy_get_estimativa_stored()
    
    if not df_hist.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_hist["Ano"], y=df_hist["Valor"], mode='lines+markers', name='Oficial (IBGE)'))
        if not df_prev.empty:
            fig.add_trace(go.Scatter(x=df_prev["Ano"], y=df_prev["Valor"], mode='lines+markers', name='Projeção', line=dict(dash='dash')))
        fig.update_layout(title="Pivot: Histórico e Projeção", xaxis_title="Ano", yaxis_title="R$ mil")
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        ### 📝 Nota Metodológica
        A estimativa do PIB Municipal utiliza metodologia híbrida que combina o último dado oficial do IBGE com proxies econômicas locais (VAF e Empregos). 
        As projeções futuras utilizam modelos Holt-Winters para garantir robustez mesmo sem bibliotecas pesadas.
        """)

def render_sustentabilidade(ano_inicio, ano_fim, modo):
    st.subheader("Indicadores de Sustentabilidade")
    col1, col2 = st.columns(2)
    with col1:
        idsc = cached_get_timeseries("IDSC_GERAL", "IDSC")
        if not idsc.empty:
            val = idsc.iloc[-1]["Valor"]
            metric_card("IDSC (Score Geral)", f"{val:.2f}", "Índice de Desenv. Sustentável", border_color="#15803d")
            fig = px.line(idsc, x="Ano", y="Valor", markers=True)
            fig = apply_institutional_layout(fig, title="Evolução do IDSC", source="Instituto Cidades Sustentáveis")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Dados do IDSC indisponíveis.")

    with col2:
        emissoes = cached_get_timeseries("EMISSOES_GEE", "SEEG")
        if not emissoes.empty:
            val = emissoes.iloc[-1]["Valor"]
            metric_card("Emissões Totais", f"{fmt_br(val, decimals=0)} t", "Toneladas CO2e", border_color="#ca8a04")
            fig = px.bar(emissoes, x="Ano", y="Valor")
            fig = apply_institutional_layout(fig, title="Emissões de Gases de Efeito Estufa", source="SEEG")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Dados do SEEG indisponíveis.")

def render_metodologia():
    st.header("📖 Nota Metodológica e Fontes de Dados")
    st.markdown("""
    ## 🎯 Objetivo do Sistema
    O **Painel GV** é o console estratégico de indicadores socioeconômicos de Governador Valadares - MG.
    
    ---
    ## 📊 Fontes de Dados
    - **Economia:** IBGE, SEFAZ-MG
    - **Trabalho:** Novo CAGED (MTE), RAIS, SEBRAE
    - **Educação:** INEP (Censo Escolar / IDEB)
    - **Sustentabilidade:** SEEG, MapBiomas, IDSC
    - **Demografia:** IBGE (Censo / Estimativas)
    
    ---
    ## 🔄 Atualização e Segurança
    O sistema utiliza atualização diária automática via GitHub Actions. É estritamente proibido o uso de dados simulados. Todo o backend é hospedado em PostgreSQL (Neon.tech).
    """)

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
        if st.button("Gerar Apresentação PPT"):
             with st.spinner("Processando..."):
                 try:
                     ppt_p = lazy_gerar_apresentacao_ppt(ano_ini, ano_fim)
                     with open(ppt_p, "rb") as f:
                         st.download_button("📥 Baixar PPT", f, file_name=Path(ppt_p).name, mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
                     st.success("Apresentação gerada!")
                 except Exception as e:
                     st.error(f"Erro: {e}")

def render_outras_paginas(pagina, ano_inicio, ano_fim, modo):
    all_inds = cached_list_indicators()
    inds_to_show = [i for i in all_inds if get_secao_by_key(i["indicator_key"]) == pagina]

    # EDUCAÇÃO: por política institucional, exibir apenas séries oriundas de arquivos reais (data/raw)
    if pagina == "Educação":
        st.info("Educação: indicadores exibidos exclusivamente a partir de dados reais no banco (origem INEP).")
        # Filtragem adicional se necessário, mas o catálogo já separa por fonte.
        # Aqui garantimos que apenas fontes reais sejam mostradas se houver fallback manual.
        inds_to_show = [i for i in inds_to_show if str(i.get("source", "")).startswith("INEP")]

    if not inds_to_show:
        st.info("Nenhum indicador disponível nesta categoria.")
        return

    for item in inds_to_show:
        df = cached_get_timeseries(item["indicator_key"], source=item["source"])
        if df.empty: continue
        df = df[(df["Ano"] >= ano_inicio) & (df["Ano"] <= ano_fim)]
        if df.empty: continue
        
        meta = lazy_get_indicator_info(item["indicator_key"])
        title = meta.get("nome", item["indicator_key"])
        unit = item.get('unit', '')
        
        st.subheader(title)
        
        fig = px.line(df, x="Ano", y="Valor", markers=True)
        fig = apply_institutional_layout(fig, title=title, source=f"{item['source']} ({unit})")
        st.plotly_chart(fig, use_container_width=True)
        
        if modo == "Técnico":
            with st.expander("📊 Detalhes Técnicos"):
                st.write(lazy_analisar_tendencia(df))
                st.dataframe(df)

def main() -> None:
    # Integrar Analytics
    ga_id = os.getenv("GA_TAG_ID")
    if ga_id:
        inject_google_analytics(ga_id)

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
    elif pagina == "Economia": render_economia(ano_inicio, ano_fim, modo)
    elif pagina == "Trabalho & Renda": render_trabalho_renda(ano_inicio, ano_fim, modo)
    elif pagina == "Sustentabilidade": render_sustentabilidade(ano_inicio, ano_fim, modo)
    elif pagina == "PIB Estimado": render_pib_estimado(ano_inicio, ano_fim)
    elif pagina == "Dashboard Executivo": lazy_create_executive_dashboard()
    elif pagina == "Métricas do Sistema": lazy_create_metrics_dashboard()
    elif pagina == "Relatórios": render_relatorios(ano_inicio, ano_fim)
    elif pagina == "Metodologia": render_metodologia()
    else: render_outras_paginas(pagina, ano_inicio, ano_fim, modo)

if __name__ == "__main__":
    main()
