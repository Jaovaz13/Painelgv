"""
Painel interno Streamlit – Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação.
Exibe todos os indicadores do banco em gráficos e permite gerar relatório em formato Word (.docx).
"""
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os

from config import LOG_FORMAT, LOG_LEVEL, MUNICIPIO, UF
from database import get_timeseries, init_db, list_indicators
from etl.ibge import get_pib_timeseries
from analytics.estimativa_pib import estimar_pib, salvar_estimativa, get_estimativa_stored
from analytics.tendencias import analisar_tendencia
from reports.report_docx import gerar_relatorio_docx
from reports.slide_builder import gerar_apresentacao_ppt
from utils.status_check import get_indicator_status
from panel.executivo import create_executive_dashboard
from monitoring.metrics_dashboard import create_metrics_dashboard
from panel.indicator_catalog import get_indicator_info

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

init_db()

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
    section[data-testid="stSidebar"] .stSelectbox label, section[data-testid="stSidebar"] .stRadio label { color: #cbd5e1 !important; }
    h1, h2, h3 { color: #0f172a !important; font-weight: 700 !important; font-family: 'Outfit', sans-serif !important; }
    hr { margin: 2em 0 !important; border: 0; height: 1px; background-image: linear-gradient(to right, rgba(0,0,0,0), rgba(0,0,0,0.1), rgba(0,0,0,0)); }
</style>
""", unsafe_allow_html=True)

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

@st.cache_data(ttl=3600, show_spinner="Buscando dados...")
def cached_get_timeseries(indicator_key, source=None):
    return get_timeseries(indicator_key, source)

@st.cache_data(ttl=3600)
def cached_list_indicators():
    return list_indicators()

def _secao_indicador(ind: dict) -> str:
    return SECAO_POR_FONTE.get(ind["source"], SECAO_PADRAO)

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

def render_indicator_header(indicator_key: str, source: str, title: str):
    status = get_indicator_status(indicator_key, source)
    badge = ""
    if status["status"] == "error":
        badge = f' <span style="color:red;font-size:0.8em;">{status["message"]} — <a href="{status["url"]}" target="_blank">{status["url"]}</a></span>'
    elif status["status"] == "update":
        badge = f' <span style="color:orange;font-size:0.8em;">{status["message"]} — <a href="{status["url"]}" target="_blank">{status["url"]}</a></span>'
    st.markdown(f"### {title}{badge}", unsafe_allow_html=True)

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

def get_secao_by_key(key: str) -> str:
    for secao, keys in INDICATOR_MAPPING.items():
        if key in keys: return secao
    return "Outros"

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
            render_indicator_header("POPULACAO_DETALHADA", "IBGE", "População")
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

    col_idhm, col_gini, col_empty1, col_empty2 = st.columns(4)
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
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col5, col6, col7, col8 = st.columns(4)
    emp = cached_get_timeseries("EMPRESAS_ATIVAS", "SEBRAE")
    with col5:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not emp.empty:
            ult = emp.iloc[-1]
            render_indicator_header("EMPRESAS_ATIVAS", "SEBRAE", "🏢 Empresas")
            st.metric("🏢 Empresas", fmt_br(ult['Valor']), f"{int(ult['Ano'])}")
        else: st.metric("🏢 Empresas", "N/D", "")
        st.markdown('</div>', unsafe_allow_html=True)
        
    saldo = cached_get_timeseries("SALDO_CAGED_MENSAL", "CAGED_MANUAL_MG")
    with col6:
        render_indicator_header("SALDO_CAGED_MENSAL", "CAGED_MANUAL_MG", "👷 Saldo Vagas")
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not saldo.empty:
            st.metric("👷 Saldo Vagas", fmt_br(saldo.iloc[-1]["Valor"]), "Mensal")
        else: st.metric("👷 Saldo Vagas", "N/D", "")
        st.markdown('</div>', unsafe_allow_html=True)

    gee = cached_get_timeseries("EMISSOES_GEE", "SEEG")
    with col7:
        render_indicator_header("EMISSOES_GEE", "SEEG", "☁️ Emissões GEE")
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not gee.empty:
            st.metric("☁️ Emissões GEE", fmt_br(gee.iloc[-1]["Valor"], decimals=1), "tCO2e")
        else: st.metric("☁️ Emissões GEE", "N/D", "")
        st.markdown('</div>', unsafe_allow_html=True)
        
    vaf = cached_get_timeseries("RECEITA_VAF", "SEFAZ_MG")
    with col8:
        render_indicator_header("RECEITA_VAF", "SEFAZ_MG", "📈 VAF")
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not vaf.empty:
            val = vaf.iloc[-1]["Valor"] / 1_000_000
            st.metric("📈 VAF", f"R$ {fmt_br(val, decimals=1)}M", "Valor Adicionado")
        else: st.metric("📈 VAF", "N/D", "")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        jobs = cached_get_timeseries("EMPREGOS_CAGED", "CAGED_NOVO")
        if jobs.empty: jobs = cached_get_timeseries("EMPREGOS_CAGED", "CAGED")
        if not jobs.empty:
            st.subheader("👷 Evolução do Emprego")
            fig = px.bar(jobs, x="Ano", y="Valor", title="Estoque de Empregos Formais")
            st.plotly_chart(fig, use_container_width=True)
    
        if not pib.empty:
            st.subheader("📈 Histórico do PIB")
            fig = px.line(pib, x="Ano", y="Valor", markers=True, title="PIB Total (Preços Correntes)")
            st.plotly_chart(fig, use_container_width=True)
    st.divider()

def render_trabalho_renda(ano_inicio, ano_fim, modo):
    st.subheader("Análise do Mercado de Trabalho e Renda")
    st.write("Dados baseados no Novo CAGED, RAIS e índices de rendimento médio.")

    col1, col2, col3 = st.columns(3)
    saldo_mes = cached_get_timeseries("SALDO_CAGED_MENSAL", "CAGED_MANUAL_MG")
    salario = cached_get_timeseries("SALARIO_MEDIO_MG", "CAGED_MANUAL_MG")
    empresas = cached_get_timeseries("EMPRESAS_ATIVAS", "SEBRAE")

    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not saldo_mes.empty:
            render_indicator_header("SALDO_CAGED_MENSAL", "CAGED_MANUAL_MG", "🌙 Saldo Mensal (CAGED)")
            st.metric("🌙 Saldo Mensal (CAGED)", fmt_br(saldo_mes.iloc[-1]["Valor"]), "Último Dado")
        else: st.metric("🌙 Saldo Mensal", "N/D", "")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not salario.empty:
            render_indicator_header("SALARIO_MEDIO_MG", "CAGED_MANUAL_MG", "💵 Salário Médio (MG)")
            st.metric("💵 Salário Médio (MG)", fmt_br(salario.iloc[-1]["Valor"], currency=True, decimals=2), "Proxy Regional")
        else: st.metric("💵 Salário Médio", "N/D", "")
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        if not empresas.empty:
            ult = empresas.iloc[-1]
            render_indicator_header("EMPRESAS_ATIVAS", "SEBRAE", "🏢 Empresas Ativas")
            st.metric("🏢 Empresas Ativas", fmt_br(ult["Valor"]), f"{int(ult['Ano'])}")
        else: st.metric("🏢 Empresas Ativas", "N/D", "")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    col_caged, col_rais = st.columns(2)
    with col_caged:
        render_indicator_header("EMPREGOS_CAGED", "CAGED_NOVO", "📈 Evolução dos Empregos (CAGED)")
        st.subheader("📈 Evolução dos Empregos (CAGED)")
        jobs = cached_get_timeseries("EMPREGOS_CAGED", "CAGED_NOVO")
        if jobs.empty: jobs = cached_get_timeseries("EMPREGOS_CAGED", "CAGED")
        if not jobs.empty:
            fig = px.area(jobs, x="Ano", y="Valor", title="Estoque de Empregos ao Longo do Tempo")
            st.plotly_chart(fig, use_container_width=True)
    
    with col_rais:
        render_indicator_header("EMPREGOS_RAIS", "RAIS", "👔 Vínculos Formais (RAIS)")
        st.subheader("👔 Vínculos Formais (RAIS)")
        jobs_rais = cached_get_timeseries("EMPREGOS_RAIS", "RAIS")
        if not jobs_rais.empty:
            fig = px.line(jobs_rais, x="Ano", y="Valor", markers=True, title="Vínculos Totais Declarados")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Dados de RAIS detalhados em processamento.")

    st.divider()
    st.markdown("### 🔍 Perfil do Empreendedorismo (MEI)")
    render_indicator_header("EMPREENDEDORES_MEI", "SEBRAE", "Microempreendedores Individuais")
    mei = cached_get_timeseries("EMPREENDEDORES_MEI", "SEBRAE")
    if not mei.empty:
        fig = px.bar(mei, x="Ano", y="Valor", title="Crescimento de Microempreendedores Individuais")
        st.plotly_chart(fig, use_container_width=True)

def render_negocios(ano_inicio, ano_fim, modo):
    st.subheader("Indicadores de Negócios e Empreendedorismo")
    st.write("Indicadores do Sebrae com base no banco de dados integrado.")

    empresas = cached_get_timeseries("EMPRESAS_ATIVAS", "SEBRAE")
    empregos = cached_get_timeseries("EMPREGOS_SEBRAE", "SEBRAE")
    estab = cached_get_timeseries("ESTABELECIMENTOS_SEBRAE", "SEBRAE")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        render_indicator_header("EMPRESAS_ATIVAS", "SEBRAE", "🏢 Empresas Ativas")
        if not empresas.empty:
            ult = empresas.sort_values("Ano").iloc[-1]
            st.metric("🏢 Empresas Ativas", fmt_br(ult["Valor"]), f"{int(ult['Ano'])}")
        else: st.metric("🏢 Empresas Ativas", "N/D")
    with col_b:
        render_indicator_header("EMPREGOS_SEBRAE", "SEBRAE", "👥 Empregados (Sebrae)")
        if not empregos.empty:
            ult = empregos.sort_values("Ano").iloc[-1]
            st.metric("👥 Empregados (Sebrae)", fmt_br(ult["Valor"]), f"{int(ult['Ano'])}")
        else: st.metric("👥 Empregados (Sebrae)", "N/D")
    with col_c:
        render_indicator_header("ESTABELECIMENTOS_SEBRAE", "SEBRAE", "🏬 Estabelecimentos")
        if not estab.empty:
            ult = estab.sort_values("Ano").iloc[-1]
            st.metric("🏬 Estabelecimentos", fmt_br(ult["Valor"]), f"{int(ult['Ano'])}")
        else: st.metric("🏬 Estabelecimentos", "N/D")

    st.divider()

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        render_indicator_header("EMPRESAS_ATIVAS", "SEBRAE", "📈 Evolução de Empresas Ativas")
        if not empresas.empty:
            fig = px.line(empresas, x="Ano", y="Valor", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sem dados de empresas ativas.")

    with col_g2:
        render_indicator_header("EMPREGOS_SEBRAE", "SEBRAE", "📈 Evolução de Empregados (Sebrae)")
        if not empregos.empty:
            fig = px.line(empregos, x="Ano", y="Valor", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("Sem dados de empregados Sebrae.")

    render_indicator_header("ESTABELECIMENTOS_SEBRAE", "SEBRAE", "📈 Evolução de Estabelecimentos")
    if not estab.empty:
        fig = px.line(estab, x="Ano", y="Valor", markers=True)
        st.plotly_chart(fig, use_container_width=True)
    else: st.info("Sem dados de estabelecimentos Sebrae.")

def render_pib_estimado(ano_inicio, ano_fim):
    render_indicator_header("PIB_ESTIMADO", "IBGE", "Projeção do PIB Municipal")
    st.subheader("Projeção do PIB Municipal")
    st.info("Utilize esta seção para visualizar as projeções baseadas nos modelos de séries temporais.")
    
    if st.button("🔄 Atualizar Projeção"):
        with st.spinner("Calculando modelos..."):
            salvar_estimativa()
        st.success("Projeção atualizada!")
    
    df_hist = cached_get_timeseries("PIB_TOTAL", source="IBGE")
    df_prev = get_estimativa_stored()
    
    if not df_hist.empty:
        df_hist["Tipo"] = "Observado"
        chart_data = df_hist.copy()
        if not df_prev.empty:
            df_prev["Tipo"] = "Estimado"
            chart_data = pd.concat([chart_data, df_prev], ignore_index=True)
        
        chart_data = chart_data[(chart_data["Ano"] >= ano_inicio) & (chart_data["Ano"] <= ano_fim)]
        fig = go.Figure()
        sh = chart_data[chart_data["Tipo"] == "Observado"]
        sp = chart_data[chart_data["Tipo"] == "Estimado"]
        fig.add_trace(go.Scatter(x=sh["Ano"], y=sh["Valor"], mode='lines+markers', name='Oficial (IBGE)'))
        if not sp.empty:
            fig.add_trace(go.Scatter(x=sp["Ano"], y=sp["Valor"], mode='lines+markers', name='Projeção', line=dict(dash='dash')))
        
        fig.update_layout(title="Pivot: Histórico e Projeção", xaxis_title="Ano", yaxis_title="R$ mil")
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        st.markdown("### 📝 Nota Metodológica")
        st.info("A estimativa do Produto Interno Bruto Municipal foi elaborada a partir de metodologia híbrida, combinando o último dado oficial publicado pelo IBGE com proxies econômicos atualizados, tais como Valor Adicionado Fiscal (SEFAZ-MG) e Massa Salarial (RAIS/CAGED). A projeção foi realizada por meio de modelos de séries temporais, garantindo coerência estatística e aderência à dinâmica econômica local.")
    else:
        st.warning("Dados não disponíveis.")

def render_sustentabilidade(ano_inicio, ano_fim, modo):
    st.subheader("Indicadores de Sustentabilidade e Território")
    
    col1, col2 = st.columns(2)
    with col1:
        render_indicator_header("IDSC_GERAL", "IDSC", "🌱 Índice de Desenvolvimento Sustentável (IDSC)")
        st.subheader("🌱 Índice de Desenvolvimento Sustentável (IDSC)")
        idsc = cached_get_timeseries("IDSC_GERAL", "IDSC")
        if not idsc.empty:
            st.metric("Score Geral", f"{idsc.iloc[-1]['Valor']:.2f}", f"Ano {int(idsc.iloc[-1]['Ano'])}")
            fig = px.line(idsc, x="Ano", y="Valor", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        render_indicator_header("EMISSOES_GEE", "SEEG", "🏭 Emissões de GEE (SEEG)")
        st.subheader("🏭 Emissões de GEE (SEEG)")
        emissoes = cached_get_timeseries("EMISSOES_GEE", "SEEG")
        if not emissoes.empty:
            st.metric("Total Emissões (tCO2e)", f"{emissoes.iloc[-1]['Valor']:,.0f}", f"Ano {int(emissoes.iloc[-1]['Ano'])}")
            fig = px.bar(emissoes, x="Ano", y="Valor", title="Histórico de Emissões")
            st.plotly_chart(fig, use_container_width=True)

    st.divider()
    render_indicator_header("AREA_URBANA", "MapBiomas", "🗺️ Uso do Solo (MapBiomas)")
    st.subheader("🗺️ Uso do Solo (MapBiomas)")
    area_urbana = cached_get_timeseries("AREA_URBANA", "MAPBIOMAS")
    vegetacao = cached_get_timeseries("VEGETACAO_NATIVA", "MAPBIOMAS")
    agro = cached_get_timeseries("USO_AGROPECUARIO", "MAPBIOMAS")
    
    if not area_urbana.empty and not vegetacao.empty:
        st.info("Visualização de cobertura vegetal e expansão urbana disponível via MapBiomas.")
        col_u, col_v, col_a = st.columns(3)
        col_u.metric("🌆 Área Urbana", f"{area_urbana.iloc[-1]['Valor']:,.0f} ha")
        col_v.metric("🌳 Veg. Nativa", f"{vegetacao.iloc[-1]['Valor']:,.0f} ha")
        col_a.metric("🚜 Agropecuária", f"{agro.iloc[-1]['Valor']:,.0f} ha")

def render_economia(ano_inicio, ano_fim, modo):
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
        periodo = st.selectbox("Período", ["Série Completa", "Últimos 5 Anos", "Último Ano"], key="p_economico")
        
        current_year = datetime.now().year
        limit_year = 1900
        if periodo == "Últimos 5 Anos": limit_year = current_year - 5
        elif periodo == "Último Ano": limit_year = current_year - 1
        
        if not df_pib.empty:
            df_pib_f = df_pib[df_pib["Ano"] >= limit_year]
            fig_evol = px.line(df_pib_f, x="Ano", y="Valor", markers=True, title="Evolução do PIB Nominal")
            st.plotly_chart(fig_evol, use_container_width=True)

    with tab4:
        st.subheader("Indicadores de Capacidade Fiscal")
        col_f1, col_f2 = st.columns(2)
        vaf = cached_get_timeseries("RECEITA_VAF", "SEFAZ_MG")
        with col_f1:
            if not vaf.empty:
                val = vaf.iloc[-1]["Valor"] / 1_000_000
                st.metric("VAF (M)", f"R$ {fmt_br(val, decimals=1)}M", "Valor Adicionado")
            else: st.metric("VAF", "N/D")
        icms = cached_get_timeseries("RECEITA_ICMS", "SEFAZ_MG")
        with col_f2:
            if not icms.empty:
                val = icms.iloc[-1]["Valor"] / 1_000_000
                st.metric("Cota-Parte ICMS (M)", f"R$ {fmt_br(val, decimals=1)}M", "Anual")
            else: st.metric("ICMS", "N/D")

def render_metodologia():
    st.header("📖 Nota Metodológica e Fontes de Dados")
    st.markdown("""
    ## 🎯 Objetivo do Sistema
    O **Painel GV** é o sistema oficial de indicadores socioeconômicos de Governador Valadares - MG, 
    desenvolvido pela Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação.
    
    ---
    ## 📊 Fontes de Dados
    Todos os indicadores são baseados em **dados oficiais e públicos**:
    
    ### Economia
    - **PIB Total e Per Capita:** IBGE - Produto Interno Bruto dos Municípios
    - **VAF:** SEFAZ-MG - Valor Adicionado Fiscal
    - **ICMS:** SEFAZ-MG - Cota-Parte do ICMS
    
    ### Trabalho e Renda
    - **CAGED:** Ministério do Trabalho - Cadastro Geral de Empregados e Desempregados
    - **RAIS:** Ministério do Trabalho - Relação Anual de Informações Sociais
    - **Empresas:** SEBRAE - Observatório de Negócios
    - **MEI:** Datasebrae - Microempreendedores Individuais
    
    ### Educação
    - **Matrículas:** INEP - Sinopse Estatística da Educação Básica
    - **IDEB:** INEP - Índice de Desenvolvimento da Educação Básica
    - **Taxa de Aprovação:** INEP - Censo Escolar
    
    ### Saúde
    - **Mortalidade Infantil:** DataSUS - Sistema de Informações sobre Mortalidade
    - **Óbitos:** DataSUS - Tabnet
    
    ### Sustentabilidade
    - **Emissões GEE:** SEEG - Sistema de Estimativas de Emissões de Gases de Efeito Estufa
    - **Uso do Solo:** MapBiomas - Coleções 9 e 10
    - **IDSC:** Cidades Sustentáveis - Índice de Desenvolvimento Sustentável
    
    ### Demografia
    - **População:** IBGE - Censo Demográfico e Estimativas Populacionais
    - **IDH-M:** Atlas Brasil - Índice de Desenvolvimento Humano Municipal
    - **GINI:** IBGE - Índice de Desigualdade
    
    ---
    ## 🔄 Atualização de Dados
    ### Frequência
    - **Automática:** Diariamente às 02:00 via scheduler
    - **Manual:** Disponível em "Métricas do Sistema"
    
    ### Sistema de Redundância
    ```
    1. Tentativa: API oficial da fonte
    2. Fallback: Arquivo local em data/raw
    3. Falha: Informação ao usuário (sem simulação)
    ```
    **Política:** É **PROIBIDO** o uso de dados simulados ou fictícios. Apenas dados oficiais são aceitos.
    
    ---
    ## 📈 Metodologia de Estimativas
    ### PIB Estimado
    A estimativa do Produto Interno Bruto Municipal para anos sem divulgação oficial utiliza:
    **Metodologia Híbrida:**
    1. **Base:** Último PIB oficial publicado pelo IBGE
    2. **Proxies:** Valor Adicionado Fiscal (SEFAZ-MG), Massa Salarial, Empregos Formais
    3. **Modelos:** Séries temporais (ARIMA, Exponential Smoothing)
    
    ### Indicadores Derivados
    - **PIB per Capita** = PIB Total / População
    - **Crescimento PIB** = (PIB_ano - PIB_ano-1) / PIB_ano-1 * 100
    
    ---
    ## 📞 Contato
    **Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação**  
    Prefeitura Municipal de Governador Valadares - MG  
    """)

def render_relatorios(ano_ini, ano_fim):
    st.subheader("Central de Relatórios e Apresentações")
    st.write("Baixe as análises consolidadas em formato institucional.")
    
    col_docx, col_ppt = st.columns(2)
    with col_docx:
        st.markdown("#### 📄 Relatório Técnico Word (DOCX)")
        if st.button("Gerar Relatório Word"):
             with st.spinner("Processando..."):
                 try:
                     docx_p = gerar_relatorio_docx(ano_ini, ano_fim)
                     with open(docx_p, "rb") as f:
                         st.download_button("📥 Baixar DOCX", f, file_name=Path(docx_p).name, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                     st.success("Relatório gerado!")
                 except Exception as e:
                     st.error(f"Erro: {e}")
                     logger.exception("Erro DOCX")

    with col_ppt:
        st.markdown("#### 📊 Apresentação Executiva")
        if st.button("Gerar PPT"):
             with st.spinner("Processando..."):
                 try:
                     ppt_p = gerar_apresentacao_ppt(ano_ini, ano_fim)
                     with open(ppt_p, "rb") as f:
                         st.download_button("📥 Baixar PPT", f, file_name=Path(ppt_p).name, mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")
                     st.success("Apresentação gerada!")
                 except Exception as e:
                     st.error(f"Erro: {e}")
                     logger.exception("Erro PPT")

def render_outras_paginas(pagina, ano_inicio, ano_fim, modo):
    keys_secao = INDICATOR_MAPPING.get(pagina, [])
    all_inds = cached_list_indicators()
    inds_to_show = [i for i in all_inds if i["indicator_key"] in keys_secao or get_secao_by_key(i["indicator_key"]) == pagina]

    # EDUCAÇÃO: por política institucional, exibir apenas séries oriundas de arquivos reais
    if pagina == "Educação":
        st.info("Educação: indicadores exibidos exclusivamente a partir de dados reais em data/raw (fonte INEP_RAW).")
        inds_to_show = [i for i in inds_to_show if i.get("source") == "INEP_RAW"]
    
    if not inds_to_show:
        st.info("Nenhum indicador disponível nesta categoria.")
    
    for item in inds_to_show:
        df = cached_get_timeseries(item["indicator_key"], source=item["source"])
        if df.empty: continue
        df = df[(df["Ano"] >= ano_inicio) & (df["Ano"] <= ano_fim)]
        if df.empty: continue
        
        meta = get_indicator_info(item["indicator_key"])
        nome_amigavel = meta.get("nome", item["indicator_key"])
        
        st.subheader(nome_amigavel)
        st.caption(f"Chave: {item['indicator_key']} | Fonte: {item['source']}")
        
        descricao = meta.get("descricao", "")
        if descricao: st.info(descricao)
        
        fig = px.line(df, x="Ano", y="Valor", markers=True, title=f"{nome_amigavel} - Série Histórica")
        st.plotly_chart(fig, use_container_width=True)
        
        if modo == "Técnico":
            with st.expander("📊 Detalhes Técnicos"):
                st.write(analisar_tendencia(df))
                st.dataframe(df)

def main() -> None:
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo_prefeitura.png")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)
    
    st.sidebar.title("Painel GV")
    
    modo = st.sidebar.selectbox("Modo de Visão", ["Institucional", "Técnico", "Divulgação Pública"])
    st.sidebar.divider()
    
    abas = ["Visão Geral", "Economia", "Trabalho & Renda", "Negócios", "Educação", "Saúde", "Sustentabilidade", "Metodologia", "PIB Estimado", "Dashboard Executivo", "Métricas do Sistema", "Relatórios"]
    if modo == "Divulgação Pública":
        # Esconder itens técnicos/administrativos na visão pública
        abas = [a for a in abas if a not in ["Relatórios", "Dashboard Executivo", "Métricas do Sistema", "PIB Estimado"]]
        
    pagina = st.sidebar.radio("Navegação", abas)
    st.sidebar.divider()
    
    st.sidebar.header("Filtros Globais")
    ano_inicio = st.sidebar.number_input("Ano Inicial", 2000, 2030, 2018)
    ano_fim = st.sidebar.number_input("Ano Final", 2000, 2030, datetime.now().year)

    if pagina != "Visão Geral":
        st.title(f"{TITULO_SECRETARIA}")
    
    st.markdown(f"**Data da última atualização:** {datetime.now().strftime('%d/%m/%Y')} | **Fonte:** Base de Dados Integrada")
    
    if modo == "Técnico":
        st.info("🔧 Modo Técnico Ativado: Exibindo detalhes estatísticos e metadados.")

    if pagina == "Visão Geral":
        render_visao_geral(ano_inicio, ano_fim, modo)
    elif pagina == "Economia":
        render_economia(ano_inicio, ano_fim, modo)
    elif pagina == "Trabalho & Renda":
        render_trabalho_renda(ano_inicio, ano_fim, modo)
    elif pagina == "Negócios":
        render_negocios(ano_inicio, ano_fim, modo)
    elif pagina == "Sustentabilidade":
        render_sustentabilidade(ano_inicio, ano_fim, modo)
    elif pagina == "Metodologia":
        render_metodologia()
    elif pagina == "PIB Estimado":
        render_pib_estimado(ano_inicio, ano_fim)
    elif pagina == "Dashboard Executivo":
        create_executive_dashboard()
    elif pagina == "Métricas do Sistema":
        create_metrics_dashboard()
    elif pagina == "Relatórios":
        render_relatorios(ano_inicio, ano_fim)
    else:
        st.header(pagina)
        render_outras_paginas(pagina, ano_inicio, ano_fim, modo)

if __name__ == "__main__":
    main()
