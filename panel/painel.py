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
from typing import Optional

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


def lazy_run_rais_caged_extended():
    """Lazy load do módulo ETL estendido de Trabalho & Renda (RAIS/CAGED)."""
    from etl.rais_caged_extended import run
    return run

# ─── Cache de consultas ao banco (reduz latência e créditos Neon) ────────────
@st.cache_data(ttl=3600, show_spinner="Buscando dados...")
def cached_get_timeseries(indicator_key: str, source: Optional[str] = None) -> pd.DataFrame:
    """Consulta com cache de 1h para reduzir requisições ao banco Neon."""
    return get_timeseries(indicator_key, source)


@st.cache_data(ttl=3600)
def cached_list_indicators() -> list:
    """Lista de indicadores com cache de 1h."""
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

# ─── Visual Components v2 (Design System Institucional) ──────────────────────
try:
    from utils.visual_components_v2 import (
        apply_custom_css,
        plotly_institutional_theme,
        render_kpi_grid,
    )
except ImportError:
    # Fallback seguro: funções mínimas se o módulo não existir
    def apply_custom_css(): pass  # noqa: E704
    def plotly_institutional_theme(fig, title="", source=""):  # noqa: E704
        fig.update_layout(title=title)
        return fig
    def render_kpi_grid(col_data):  # noqa: E704
        cols = st.columns(len(col_data)) if col_data else []
        for col, d in zip(cols, col_data):
            with col:
                st.metric(d.get("label", ""), d.get("value", "—"), d.get("delta"))

# Manter compatibilidade retroativa com código que usa apply_institutional_layout
try:
    from utils.visual_components import metric_card, apply_institutional_layout
except ImportError:
    def metric_card(label, value, sublabel="", border_color="#2563eb"):  # noqa: E704
        st.metric(label, value, sublabel)
    def apply_institutional_layout(fig, title="", source=""):  # noqa: E704
        return plotly_institutional_theme(fig, title, source)

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
    """Obtém PIB per capita do banco. Busca por qualquer fonte disponível."""
    # 1. Tentar buscar dado real (PIB_PER_CAPITA) de qualquer fonte
    df_direto = cached_get_timeseries("PIB_PER_CAPITA") 
    if not df_direto.empty:
        return df_direto.sort_values("Ano")[["Ano", "Valor", "Unidade"]]

    # 2. Fallback: Cálculo manual (PIB / População)
    df_pib = cached_get_timeseries("PIB_TOTAL")
    df_pop = cached_get_timeseries("POPULACAO_DETALHADA")
    if df_pop.empty:
        df_pop = cached_get_timeseries("POPULACAO")

    if df_pib.empty or df_pop.empty:
        return pd.DataFrame()

    merged = pd.merge(df_pib, df_pop, on="Ano", suffixes=("_pib", "_pop"))
    if merged.empty:
        return pd.DataFrame()

    merged = merged.sort_values("Ano")
    merged["Valor"] = merged["Valor_pib"] / merged["Valor_pop"]
    merged["Unidade"] = "R$ / Hab"
    return merged[["Ano", "Valor", "Unidade"]]

def get_pib_growth_df():
    """Calcula a taxa de crescimento a partir do PIB Total disponível no banco."""
    df_pib = cached_get_timeseries("PIB_TOTAL") 
    if df_pib.empty or len(df_pib) < 2:
        return pd.DataFrame()
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

def render_visao_geral(ano_inicio: int, ano_fim: int) -> None:
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

    # ── Grade principal de KPIs ──────────────────────────────────
    pop_det = cached_get_timeseries("POPULACAO_DETALHADA")
    if pop_det.empty:
        pop_det = cached_get_timeseries("POPULACAO")
    pib = cached_get_timeseries("PIB_TOTAL")
    df_pc = get_pib_per_capita_df()
    df_gr = get_pib_growth_df()

    def _val_pop():
        if not pop_det.empty:
            ult = pop_det.sort_values("Ano").iloc[-1]
            return fmt_br(ult["Valor"]), f"Ref. {int(ult['Ano'])}"
        return "N/D", ""

    def _val_pib():
        if not pib.empty:
            ult = pib.sort_values("Ano").iloc[-1]
            return f"R$ {fmt_br(ult['Valor'] / 1_000_000, decimals=2)} bi", f"Ref. {int(ult['Ano'])}"
        return "N/D", ""

    pop_val, pop_sub = _val_pop()
    pib_val, pib_sub = _val_pib()
    pc_val = fmt_br(df_pc.iloc[-1]["Valor"], currency=True) if not df_pc.empty else "N/D"
    gr_val = (
        f"{fmt_br(df_gr.iloc[-1]['Valor'], decimals=2)}%" if not df_gr.empty else "N/D"
    )
    gr_delta = None
    if not df_gr.empty and len(df_gr) >= 2:
        gr_ant = df_gr.sort_values("Ano").iloc[-2]["Valor"]
        gr_ult = df_gr.sort_values("Ano").iloc[-1]["Valor"]
        gr_delta = f"{gr_ult - gr_ant:+.2f} p.p."

    render_kpi_grid([
        {"label": "População", "value": pop_val, "help": pop_sub},
        {"label": "PIB Total", "value": pib_val, "help": "IBGE – Contas Regionais"},
        {"label": "PIB per Capita", "value": pc_val, "help": "Calculado: PIB/População"},
        {"label": "Crescimento PIB", "value": gr_val, "delta": gr_delta,
         "help": "Variação percentual anual"},
    ])

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Segunda grade de KPIs ───────────────────────────────────
    idhm = cached_get_timeseries("IDHM", "ATLAS_BRASIL")
    gini = cached_get_timeseries("GINI", "IBGE")
    vaf  = cached_get_timeseries("RECEITA_VAF", "SEFAZ_MG")
    gee  = cached_get_timeseries("EMISSOES_GEE", "SEEG")

    render_kpi_grid([
        {
            "label": "IDH-M",
            "value": fmt_br(idhm.sort_values("Ano").iloc[-1]["Valor"], decimals=3)
                     if not idhm.empty else "N/D",
            "help": "Atlas Brasil – PNUD",
        },
        {
            "label": "Índice GINI",
            "value": fmt_br(gini.sort_values("Ano").iloc[-1]["Valor"], decimals=4)
                     if not gini.empty else "N/D",
            "help": "Desigualdade de renda – IBGE",
        },
        {
            "label": "VAF",
            "value": f"R$ {fmt_br(vaf.iloc[-1]['Valor'] / 1_000_000, decimals=1)} M"
                     if not vaf.empty else "N/D",
            "help": "Valor Adicionado Fiscal – SEFAZ-MG",
        },
        {
            "label": "Emissões GEE",
            "value": f"{fmt_br(gee.iloc[-1]['Valor'], decimals=0)} t"
                     if not gee.empty else "N/D",
            "help": "Toneladas CO₂e – SEEG",
        },
    ])

def render_economia(ano_inicio: int, ano_fim: int) -> None:
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
        df_pc = get_pib_per_capita_df()
        df_gr = get_pib_growth_df()

        render_kpi_grid([
            {
                "label": "PIB Total",
                "value": f"R$ {fmt_br(df_pib.sort_values('Ano').iloc[-1]['Valor'] / 1_000_000, decimals=1)} bi"
                         if not df_pib.empty else "N/D",
                "help": f"Ano: {int(df_pib.sort_values('Ano').iloc[-1]['Ano'])}" if not df_pib.empty else "",
            },
            {
                "label": "PIB per Capita",
                "value": fmt_br(df_pc.iloc[-1]["Valor"], currency=True) if not df_pc.empty else "N/D",
                "help": "Riqueza por habitante",
            },
            {
                "label": "Crescimento PIB",
                "value": f"{fmt_br(df_gr.iloc[-1]['Valor'], decimals=2)}%" if not df_gr.empty else "N/D",
                "help": "Variação anual",
            },
        ])

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
            fig_evol = px.line(
                df_pib_f, x="Ano", y="Valor", markers=True,
                color_discrete_sequence=["#1e3a8a"],
            )
            fig_evol = plotly_institutional_theme(
                fig_evol,
                title="Evolução do PIB Nominal (Série Histórica)",
                source="IBGE – Contas Regionais",
            )
            st.plotly_chart(fig_evol, use_container_width=True)
            st.caption(
                "⚠️ **Nota metodológica:** Dados oficiais do IBGE disponíveis até 2022. "
                "Valores a partir de 2023 são **projeções estatísticas** (Holt-Winters/Híbrido) "
                "e **não representam dados oficiais**."
            )

    with tab4:
        st.subheader("Indicadores de Capacidade Fiscal")
        vaf   = cached_get_timeseries("RECEITA_VAF", "SEFAZ_MG")
        icms  = cached_get_timeseries("RECEITA_ICMS", "SEFAZ_MG")
        massa = cached_get_timeseries("MASSA_SALARIAL_ESTIMADA", "CAGED_ESTIMADO")

        render_kpi_grid([
            {
                "label": "Valor Adic. Fiscal",
                "value": f"R$ {fmt_br(vaf.iloc[-1]['Valor'] / 1_000_000, decimals=1)} M"
                         if not vaf.empty else "N/D",
                "help": f"Ano: {int(vaf.iloc[-1]['Ano'])}" if not vaf.empty else "",
            },
            {
                "label": "Cota-Parte ICMS",
                "value": f"R$ {fmt_br(icms.iloc[-1]['Valor'] / 1_000_000, decimals=1)} M"
                         if not icms.empty else "N/D",
                "help": "Repasse Estadual – SEFAZ-MG",
            },
            {
                "label": "Massa Salarial (Est.)",
                "value": f"R$ {fmt_br(massa.iloc[-1]['Valor'] / 1_000_000, decimals=1)} M"
                         if not massa.empty else "N/D",
                "help": "Proxy: Empregos × Salário Médio × 13",
            },
        ])

def render_trabalho_renda(ano_inicio: int, ano_fim: int) -> None:
    """Aba Trabalho & Renda: indicadores de mercado de trabalho e renda."""
    st.subheader("Análise do Mercado de Trabalho e Renda")

    # ── KPIs principais ─────────────────────────────────────
    saldo_mes = cached_get_timeseries("SALDO_CAGED_MENSAL")
    salario   = cached_get_timeseries("SALARIO_MEDIO_MG", "SEBRAE")
    if salario.empty:
        salario = cached_get_timeseries("SALARIO_MEDIO_REAL")
    empresas  = cached_get_timeseries("EMPRESAS_ATIVAS", "SEBRAE")
    if empresas.empty:
        empresas = cached_get_timeseries("EMPRESOS_ATIVAS")
    if empresas.empty:
        empresas = cached_get_timeseries("NUM_EMPRESAS")
    massa = cached_get_timeseries("MASSA_SALARIAL_ESTIMADA", "CAGED_ESTIMADO")

    saldo_val   = fmt_br(saldo_mes.iloc[-1]["Valor"]) if not saldo_mes.empty else "N/D"
    saldo_delta = None
    if not saldo_mes.empty and len(saldo_mes) >= 2:
        d = saldo_mes.sort_values("Ano")
        saldo_delta = f"{d.iloc[-1]['Valor'] - d.iloc[-2]['Valor']:+.0f}"

    render_kpi_grid([
        {
            "label": "Saldo Mensal (CAGED)",
            "value": saldo_val,
            "delta": saldo_delta,
            "help": "Admissões − Demissões (CLT)",
        },
        {
            "label": "Salário Médio",
            "value": fmt_br(salario.iloc[-1]["Valor"], currency=True)
                     if not salario.empty else "N/D",
            "help": "Referência regional (RAIS/SEBRAE)",
        },
        {
            "label": "Empresas Ativas",
            "value": fmt_br(empresas.iloc[-1]["Valor"]) if not empresas.empty else "N/D",
            "help": "Total cadastrado – SEBRAE/RAIS",
        },
        {
            "label": "Massa Salarial (Est.)",
            "value": f"R$ {fmt_br(massa.iloc[-1]['Valor'] / 1_000_000, decimals=1)} M"
                     if not massa.empty else "N/D",
            "help": "Proxy: Empregos × Salário × 13 (CAGED/RAIS)",
        },
    ])

    st.divider()

    # ── Séries Históricas ─────────────────────────────────────
    col_caged, col_rais = st.columns(2)
    with col_caged:
        jobs = cached_get_timeseries("EMPREGOS_CAGED", "CAGED_NOVO")
        if jobs.empty:
            jobs = cached_get_timeseries("EMPREGOS_CAGED", "CAGED")
        if not jobs.empty:
            st.subheader("📈 Estoque de Empregos (CAGED)")
            fig = px.area(
                jobs, x="Ano", y="Valor",
                color_discrete_sequence=["#60a5fa"],
            )
            fig = plotly_institutional_theme(
                fig,
                title="Estoque de Empregos Formais",
                source="Novo CAGED – MTE",
            )
            st.plotly_chart(fig, use_container_width=True)

    with col_rais:
        jobs_rais = cached_get_timeseries("EMPREGOS_RAIS", "RAIS")
        if not jobs_rais.empty:
            st.subheader("👔 Vínculos Formais (RAIS)")
            fig = px.line(
                jobs_rais, x="Ano", y="Valor", markers=True,
                color_discrete_sequence=["#1e3a8a"],
            )
            fig = plotly_institutional_theme(
                fig,
                title="Vínculos Empregatícios (RAIS)",
                source="RAIS – MTE",
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Novos Indicadores: Massa Salarial e Escolaridade (RAIS Estendido) ──
    st.divider()
    st.subheader("📊 Massa Salarial e Escolaridade (RAIS Estendido)")

    # Atualizar indicadores antes de exibir (lazy load do ETL)
    with st.expander("🔄 Recalcular indicadores de Massa Salarial", expanded=False):
        if st.button("Executar ETL Estendido (RAIS/CAGED)", key="btn_rais_ext"):
            with st.spinner("Calculando Massa Salarial..."):
                try:
                    run_fn = lazy_run_rais_caged_extended()
                    run_fn()
                    st.cache_data.clear()
                    st.success("✔️ Massa Salarial atualizada! Recarregue a página.")
                except Exception as exc:
                    st.error(f"Erro no ETL estendido: {exc}")

    col_ms, col_esc = st.columns(2)
    with col_ms:
        df_massa = cached_get_timeseries("MASSA_SALARIAL_ESTIMADA", "CAGED_ESTIMADO")
        if not df_massa.empty:
            df_massa_f = df_massa[
                (df_massa["Ano"] >= ano_inicio) & (df_massa["Ano"] <= ano_fim)
            ]
            fig_ms = px.bar(
                df_massa_f, x="Ano", y="Valor",
                color_discrete_sequence=["#1e3a8a"],
            )
            fig_ms = plotly_institutional_theme(
                fig_ms,
                title="Massa Salarial Estimada (R$)",
                source="CAGED/RAIS – Proxy Interno",
            )
            st.plotly_chart(fig_ms, use_container_width=True)
            st.caption(
                "ℹ️ **Metodologia:** Massa Salarial = Estoque de Empregos × Salário Médio × 13 (inclui 13º). "
                "Trata-se de estimativa proxy e não de valor oficial."
            )
        else:
            st.info("Dados de Massa Salarial não disponíveis. Execute o ETL Estendido acima.")

    with col_esc:
        df_esc = cached_get_timeseries("ESCOLARIDADE_TRABALHO", "RAIS_DETALHADA")
        if not df_esc.empty:
            df_esc_f = df_esc[
                (df_esc["Ano"] >= ano_inicio) & (df_esc["Ano"] <= ano_fim)
            ]
            fig_esc = px.bar(
                df_esc_f, x="Ano", y="Valor",
                color_discrete_sequence=["#60a5fa"],
            )
            fig_esc = plotly_institutional_theme(
                fig_esc,
                title="Distribuição de Escolaridade (RAIS)",
                source="RAIS – MTE",
            )
            st.plotly_chart(fig_esc, use_container_width=True)
            st.caption(
                "ℹ️ **Metodologia:** Distribuição de vínculos por nível de escolaridade "
                "conforme classificação RAIS/MTE."
            )
        else:
            st.info("Dados de Escolaridade não disponíveis no banco.")

def render_pib_estimado(ano_inicio: int, ano_fim: int) -> None:
    """Exibe as projeções do PIB com notas metodológicas claras."""
    st.subheader("Projeção do PIB Municipal")
    st.info(
        "📊 Visualização de projeções baseadas em modelos estatísticos. "
        "Dados oficiais disponíveis até 2022 (IBGE)."
    )

    if st.button("🔄 Atualizar Projeção"):
        with st.spinner("Calculando modelos..."):
            lazy_salvar_estimativa()
        st.success("Projeção atualizada!")

    df_hist = cached_get_timeseries("PIB_TOTAL", source="IBGE")
    df_prev = lazy_get_estimativa_stored()

    if not df_hist.empty:
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=df_hist["Ano"], y=df_hist["Valor"],
                mode="lines+markers",
                name="Oficial (IBGE)",
                line=dict(color="#1e3a8a", width=2),
                marker=dict(color="#1e3a8a", size=7),
            )
        )
        if not df_prev.empty:
            fig.add_trace(
                go.Scatter(
                    x=df_prev["Ano"], y=df_prev["Valor"],
                    mode="lines+markers",
                    name="Projeção Estatística",
                    line=dict(color="#60a5fa", width=2, dash="dash"),
                    marker=dict(color="#60a5fa", size=7),
                )
            )
        fig = plotly_institutional_theme(
            fig,
            title="PIB Municipal: Histórico e Projeção",
            source="IBGE (oficial) + Modelo Holt-Winters/Híbrido (estimado)",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Notas metodológicas obrigatórias
        st.caption(
            "⚠️ **Atenção:** Os dados a partir de **2023 são projeções estatísticas** e "
            "**não representam valores oficiais do IBGE**. "
            "As estimativas foram geradas por modelo Holt-Winters com Refinamento Híbrido "
            "(VAF + Empregos CAGED)."
        )
        st.markdown("""
        ### 📝 Nota Metodológica
        A estimativa do PIB Municipal utiliza **metodologia híbrida** que combina:
        - ✅ Último dado **oficial do IBGE** (base)
        - 📈 Modelo **Holt-Winters** (média móvel exponencial amortecida) para projeções
        - 🏛️ **Refinamento** com proxies econômicas locais (VAF/SEFAZ e Empregos/CAGED)

        > Os dados de **2023 em diante** são **projeções** e devem ser interpretados
        > com cautela. Para fins institucionais, utilize apenas os dados oficiais.
        """)

def render_sustentabilidade(ano_inicio: int, ano_fim: int) -> None:
    """Aba Sustentabilidade."""
    st.subheader("Indicadores de Sustentabilidade")
    col1, col2 = st.columns(2)
    with col1:
        idsc = cached_get_timeseries("IDSC_GERAL", "IDSC")
        if not idsc.empty:
            val = idsc.iloc[-1]["Valor"]
            render_kpi_grid([
                {
                    "label": "IDSC (Score Geral)",
                    "value": f"{val:.2f}",
                    "help": "Índice de Desenvolvimento Sustentável das Cidades",
                }
            ])
            fig = px.line(
                idsc, x="Ano", y="Valor", markers=True,
                color_discrete_sequence=["#1e3a8a"],
            )
            fig = plotly_institutional_theme(
                fig,
                title="Evolução do IDSC",
                source="Instituto Cidades Sustentáveis",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados do IDSC indisponíveis.")

    with col2:
        emissoes = cached_get_timeseries("EMISSOES_GEE", "SEEG")
        if not emissoes.empty:
            val = emissoes.iloc[-1]["Valor"]
            render_kpi_grid([
                {
                    "label": "Emissões Totais",
                    "value": f"{fmt_br(val, decimals=0)} t CO₂e",
                    "help": "SEEG – Sistema de Estimativas de Emissões",
                }
            ])
            fig = px.bar(
                emissoes, x="Ano", y="Valor",
                color_discrete_sequence=["#1e3a8a"],
            )
            fig = plotly_institutional_theme(
                fig,
                title="Emissões de Gases de Efeito Estufa",
                source="SEEG",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados do SEEG indisponíveis.")

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

def render_outras_paginas(pagina: str, ano_inicio: int, ano_fim: int) -> None:
    """Renderiza abas genéricas (Educação, Saúde, Negócios, etc.) com gráficos institucionais."""
    all_inds = cached_list_indicators()
    inds_to_show = [i for i in all_inds if get_secao_by_key(i["indicator_key"]) == pagina]

    # Educação: exibir apenas dados reais do INEP (sem placeholders)
    if pagina == "Educação":
        st.info("Indicadores exibidos exclusivamente a partir de dados reais (origem INEP).")
        inds_to_show = [i for i in inds_to_show if str(i.get("source", "")).startswith("INEP")]

    if not inds_to_show:
        st.info("Nenhum indicador disponível nesta categoria no banco de dados.")
        return

    for item in inds_to_show:
        df = cached_get_timeseries(item["indicator_key"], source=item["source"])
        if df.empty:
            continue
        df = df[(df["Ano"] >= ano_inicio) & (df["Ano"] <= ano_fim)]
        if df.empty:
            continue

        meta = lazy_get_indicator_info(item["indicator_key"])
        title = meta.get("nome", item["indicator_key"])
        unit = item.get("unit", "")

        st.subheader(title)
        fig = px.line(
            df, x="Ano", y="Valor", markers=True,
            color_discrete_sequence=["#1e3a8a"],
        )
        fig = plotly_institutional_theme(
            fig,
            title=title,
            source=f"{item['source']} ({unit})" if unit else item["source"],
        )
        st.plotly_chart(fig, use_container_width=True)

        # Detalhes técnicos sempre disponíveis no painel interno
        with st.expander("📊 Dados e Tendência", expanded=False):
            try:
                st.write(lazy_analisar_tendencia(df))
            except Exception:
                pass
            st.dataframe(
                df[["Ano", "Valor", "Unidade"]].rename(columns={"Valor": unit or "Valor"}),
                use_container_width=True,
            )

def main() -> None:
    """Ponto de entrada principal do Painel GV (Uso Interno – Secretarias)."""
    # ── CSS institucional v2 ──────────────────────────────────────────────────
    apply_custom_css()

    # ── Google Analytics (opcional) ───────────────────────────────────────────
    ga_id = os.getenv("GA_TAG_ID")
    if ga_id:
        inject_google_analytics(ga_id)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo_prefeitura.png")
    if os.path.exists(logo_path):
        st.sidebar.image(logo_path, use_container_width=True)

    st.sidebar.title("Painel GV")
    st.sidebar.caption("Uso interno – Secretarias Municipais")

    # Painel exclusivamente interno: todas as abas sempre disponíveis
    ABAS = [
        "Visão Geral",
        "Economia",
        "Trabalho & Renda",
        "Negócios",
        "Educação",
        "Saúde",
        "Sustentabilidade",
        "PIB Estimado",
        "Dashboard Executivo",
        "Métricas do Sistema",
        "Relatórios",
        "Metodologia",
    ]

    pagina = st.sidebar.radio("Navegação", ABAS)
    st.sidebar.divider()
    ano_inicio = st.sidebar.number_input("Ano Inicial", min_value=2000, max_value=2030, value=2018)
    ano_fim = st.sidebar.number_input("Ano Final",   min_value=2000, max_value=2030, value=datetime.now().year)

    # ── Roteamento ────────────────────────────────────────────────────────────
    if pagina == "Visão Geral":
        render_visao_geral(ano_inicio, ano_fim)
    elif pagina == "Economia":
        render_economia(ano_inicio, ano_fim)
    elif pagina == "Trabalho & Renda":
        render_trabalho_renda(ano_inicio, ano_fim)
    elif pagina == "Sustentabilidade":
        render_sustentabilidade(ano_inicio, ano_fim)
    elif pagina == "PIB Estimado":
        render_pib_estimado(ano_inicio, ano_fim)
    elif pagina == "Dashboard Executivo":
        lazy_create_executive_dashboard()
    elif pagina == "Métricas do Sistema":
        lazy_create_metrics_dashboard()
    elif pagina == "Relatórios":
        render_relatorios(ano_inicio, ano_fim)
    elif pagina == "Metodologia":
        render_metodologia()
    else:
        render_outras_paginas(pagina, ano_inicio, ano_fim)


if __name__ == "__main__":
    main()
