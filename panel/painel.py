"""
Painel interno Streamlit – Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação.
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
from etl.ibge import get_pib_timeseries
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

def card_plotly(label, value, delta=None, unit="", fonte=""):
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

def get_secao_by_key(key: str) -> str:
    for secao, keys in INDICATOR_MAPPING.items():
        if key in keys: return secao
    # Tenta encontrar no catálogo a fonte se não estiver no mapping manual
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
            render_indicator_header("POPULACAO", "IBGE", "População")
            st.plotly_chart(card_plotly("População", ult['Valor'], unit="", fonte="IBGE"), use_container_width=True)
        else: st.metric("População", "N/D")

    pib = cached_get_timeseries("PIB_TOTAL", "IBGE")
    with col_pib:
        if not pib.empty:
            ult = pib.sort_values("Ano").iloc[-1]
            pib_bilhoes = ult['Valor'] / 1_000_000
            render_indicator_header("PIB_TOTAL", "IBGE", "PIB Total")
            st.plotly_chart(card_plotly("PIB Total", pib_bilhoes, unit="bi", fonte="IBGE"), use_container_width=True)
        else: st.metric("PIB Total", "N/D")

    with col_pc:
        df_pc = get_pib_per_capita_df()
        if not df_pc.empty:
            render_indicator_header("PIB_PER_CAPITA", "IBGE", "PIB per Capita")
            st.plotly_chart(card_plotly("PIB per Capita", df_pc.iloc[-1]['Valor'], unit="", fonte="IBGE (Calc)"), use_container_width=True)
        else: st.metric("PIB per Capita", "N/D")

    with col_gr:
        df_gr = get_pib_growth_df()
        if not df_gr.empty:
            render_indicator_header("PIB_CRESCIMENTO", "IBGE", "Crescimento PIB")
            st.plotly_chart(card_plotly("Crescimento PIB", df_gr.iloc[-1]['Valor'], unit="%", fonte="IBGE (Calc)"), use_container_width=True)
        else: st.metric("Crescimento", "N/D")

    st.markdown("<br>", unsafe_allow_html=True)

    col_idhm, col_gini, col_vaf, col_gee = st.columns(4)
    idhm = cached_get_timeseries("IDHM", "ATLAS_BRASIL")
    with col_idhm:
        render_indicator_header("IDHM", "ATLAS_BRASIL", "IDH-M")
        if not idhm.empty:
            st.plotly_chart(card_plotly("IDH-M", idhm.sort_values("Ano").iloc[-1]['Valor'], unit="", fonte="Atlas Brasil"), use_container_width=True)
        else: st.metric("IDH-M", "N/D")
    
    gini = cached_get_timeseries("GINI", "IBGE")
    with col_gini:
        render_indicator_header("GINI", "IBGE", "Índice GINI")
        if not gini.empty:
            st.plotly_chart(card_plotly("Índice GINI", gini.sort_values("Ano").iloc[-1]['Valor'], unit="", fonte="IBGE"), use_container_width=True)
        else: st.metric("Índice GINI", "N/D")
    
    vaf = cached_get_timeseries("RECEITA_VAF", "SEFAZ_MG")
    with col_vaf:
        render_indicator_header("RECEITA_VAF", "SEFAZ_MG", "Valor Adicionado (VAF)")
        if not vaf.empty:
            val = vaf.iloc[-1]["Valor"] / 1_000_000
            st.plotly_chart(card_plotly("VAF", val, unit="M", fonte="SEFAZ-MG"), use_container_width=True)
        else: st.metric("VAF", "N/D")
        
    gee = cached_get_timeseries("EMISSOES_GEE", "SEEG")
    with col_gee:
        render_indicator_header("EMISSOES_GEE", "SEEG", "Emissões GEE")
        if not gee.empty:
            st.plotly_chart(card_plotly("GEE", gee.iloc[-1]["Valor"], unit="tCO2e", fonte="SEEG"), use_container_width=True)
        else: st.metric("GEE", "N/D")

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
                st.plotly_chart(card_plotly("PIB Total", val, unit="bi", fonte="IBGE"), use_container_width=True)
            else: st.metric("PIB Total", "N/D")
        
        with col_e2:
            df_pc = get_pib_per_capita_df()
            if not df_pc.empty:
                st.plotly_chart(card_plotly("PIB per Capita", df_pc.iloc[-1]['Valor'], unit="", fonte="IBGE (Calc)"), use_container_width=True)
            else: st.metric("PIB per Capita", "N/D")
        
        with col_e3:
            df_gr = get_pib_growth_df()
            if not df_gr.empty:
                st.plotly_chart(card_plotly("Crescimento PIB", df_gr.iloc[-1]['Valor'], unit="%", fonte="IBGE (Calc)"), use_container_width=True)
            else: st.metric("Crescimento PIB", "N/D")

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
            st.plotly_chart(fig_pie, use_container_width=True)
        else: st.info("Dados setoriais não disponíveis.")

    with tab3:
        st.subheader("Evolução Histórica")
        if not df_pib.empty:
            df_pib_f = df_pib[(df_pib["Ano"] >= ano_inicio) & (df_pib["Ano"] <= ano_fim)]
            fig_evol = px.line(df_pib_f, x="Ano", y="Valor", markers=True, title="Evolução do PIB Nominal")
            st.plotly_chart(fig_evol, use_container_width=True)

    with tab4:
        st.subheader("Indicadores de Capacidade Fiscal")
        col_f1, col_f2 = st.columns(2)
        vaf = cached_get_timeseries("RECEITA_VAF", "SEFAZ_MG")
        with col_f1:
            if not vaf.empty:
                val = vaf.iloc[-1]["Valor"] / 1_000_000
                render_indicator_header("RECEITA_VAF", "SEFAZ_MG", "VAF")
                st.metric("VAF (M)", f"R$ {fmt_br(val, decimals=1)}M", "Valor Adicionado")
            else: st.metric("VAF", "N/D")
        icms = cached_get_timeseries("RECEITA_ICMS", "SEFAZ_MG")
        with col_f2:
            if not icms.empty:
                val = icms.iloc[-1]["Valor"] / 1_000_000
                render_indicator_header("RECEITA_ICMS", "SEFAZ_MG", "ICMS")
                st.metric("Cota-Parte ICMS (M)", f"R$ {fmt_br(val, decimals=1)}M", "Anual")
            else: st.metric("ICMS", "N/D")

def render_trabalho_renda(ano_inicio, ano_fim, modo):
    st.subheader("Análise do Mercado de Trabalho e Renda")
    col1, col2, col3 = st.columns(3)
    saldo_mes = cached_get_timeseries("SALDO_CAGED_MENSAL", "CAGED_MANUAL_MG")
    salario = cached_get_timeseries("SALARIO_MEDIO_MG", "CAGED_MANUAL_MG")
    empresas = cached_get_timeseries("EMPRESAS_ATIVAS", "SEBRAE")

    with col1:
        if not saldo_mes.empty:
            render_indicator_header("SALDO_CAGED_MENSAL", "CAGED_MANUAL_MG", "Saldo Mensal (CAGED)")
            st.metric("🌙 Saldo Mensal", fmt_br(saldo_mes.iloc[-1]["Valor"]), "Último Dado")
    with col2:
        if not salario.empty:
            render_indicator_header("SALARIO_MEDIO_MG", "CAGED_MANUAL_MG", "Salário Médio (MG)")
            st.metric("💵 Salário Médio", fmt_br(salario.iloc[-1]["Valor"], currency=True, decimals=2), "Proxy Regional")
    with col3:
        if not empresas.empty:
            render_indicator_header("EMPRESAS_ATIVAS", "SEBRAE", "Empresas Ativas")
            st.metric("🏢 Empresas", fmt_br(empresas.iloc[-1]["Valor"]), f"{int(empresas.iloc[-1]['Ano'])}")

    st.divider()
    col_caged, col_rais = st.columns(2)
    with col_caged:
        jobs = cached_get_timeseries("EMPREGOS_CAGED", "CAGED_NOVO")
        if jobs.empty: jobs = cached_get_timeseries("EMPREGOS_CAGED", "CAGED")
        if not jobs.empty:
            st.subheader("📈 Estoque de Empregos (CAGED)")
            fig = px.area(jobs, x="Ano", y="Valor")
            st.plotly_chart(fig, use_container_width=True)
    
    with col_rais:
        jobs_rais = cached_get_timeseries("EMPREGOS_RAIS", "RAIS")
        if not jobs_rais.empty:
            st.subheader("👔 Vínculos Formais (RAIS)")
            fig = px.line(jobs_rais, x="Ano", y="Valor", markers=True)
            st.plotly_chart(fig, use_container_width=True)

def render_negocios(ano_inicio, ano_fim, modo):
    st.subheader("Indicadores de Negócios e Empreendedorismo")
    empresas = cached_get_timeseries("EMPRESAS_ATIVAS", "SEBRAE")
    empregos = cached_get_timeseries("EMPREGOS_SEBRAE", "SEBRAE")
    estab = cached_get_timeseries("ESTABELECIMENTOS_SEBRAE", "SEBRAE")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if not empresas.empty:
            st.metric("🏢 Empresas Ativas", fmt_br(empresas.iloc[-1]["Valor"]))
    with col_b:
        if not empregos.empty:
            st.metric("👥 Empregados (Sebrae)", fmt_br(empregos.iloc[-1]["Valor"]))
    with col_c:
        if not estab.empty:
            st.metric("🏬 Estabelecimentos", fmt_br(estab.iloc[-1]["Valor"]))

    if not empresas.empty:
        fig = px.line(empresas, x="Ano", y="Valor", title="Evolução de Empresas Ativas (Sebrae)")
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
            st.subheader("🌱 IDSC (Score Geral)")
            st.metric("Score", f"{idsc.iloc[-1]['Valor']:.2f}")
            st.plotly_chart(px.line(idsc, x="Ano", y="Valor", markers=True), use_container_width=True)
    with col2:
        emissoes = cached_get_timeseries("EMISSOES_GEE", "SEEG")
        if not emissoes.empty:
            st.subheader("🏭 Emissões de GEE")
            st.metric("Total (tCO2e)", f"{emissoes.iloc[-1]['Valor']:,.0f}")
            st.plotly_chart(px.bar(emissoes, x="Ano", y="Valor"), use_container_width=True)

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
    # Fallback para outras categorias dinâmicas
    all_inds = cached_list_indicators()
    inds_to_show = [i for i in all_inds if get_secao_by_key(i["indicator_key"]) == pagina]

    if not inds_to_show:
        st.info("Nenhum indicador disponível nesta categoria.")
        return

    for item in inds_to_show:
        df = cached_get_timeseries(item["indicator_key"], source=item["source"])
        if df.empty: continue
        df = df[(df["Ano"] >= ano_inicio) & (df["Ano"] <= ano_fim)]
        if df.empty: continue
        
        meta = lazy_get_indicator_info(item["indicator_key"])
        st.subheader(meta.get("nome", item["indicator_key"]))
        st.plotly_chart(px.line(df, x="Ano", y="Valor", markers=True), use_container_width=True)
        
        if modo == "Técnico":
            with st.expander("📊 Detalhes Técnicos"):
                st.write(lazy_analisar_tendencia(df))
                st.dataframe(df)

def main() -> None:
    # Integrar Analytics via variável de ambiente
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
    elif pagina == "Negócios": render_negocios(ano_inicio, ano_fim, modo)
    elif pagina == "Sustentabilidade": render_sustentabilidade(ano_inicio, ano_fim, modo)
    elif pagina == "PIB Estimado": render_pib_estimado(ano_inicio, ano_fim)
    elif pagina == "Dashboard Executivo": lazy_create_executive_dashboard()
    elif pagina == "Métricas do Sistema": lazy_create_metrics_dashboard()
    elif pagina == "Relatórios": render_relatorios(ano_inicio, ano_fim)
    elif pagina == "Metodologia": render_metodologia()
    else: render_outras_paginas(pagina, ano_inicio, ano_fim, modo)

if __name__ == "__main__":
    main()
