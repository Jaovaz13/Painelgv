"""
Portal público Streamlit – visão resumida para cidadãos.
Mesmo título da Secretaria; indicadores principais em gráficos simples.
Sem geração de relatório completo.
"""
import streamlit as st
import plotly.express as px

from config import MUNICIPIO, UF
from database import get_timeseries, init_db, list_indicators

TITULO_SECRETARIA = "Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação"

init_db()

st.set_page_config(
    page_title=f"Observatório de Dados - {MUNICIPIO}",
    layout="wide",
)

st.title(TITULO_SECRETARIA)
st.caption(f"**Observatório Socioeconômico Público** – {MUNICIPIO}/{UF}")
st.markdown("---")

# Indicadores principais: PIB, CAGED, RAIS
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 PIB Municipal (R$ mil)")
    pib = get_timeseries("PIB_TOTAL", source="IBGE")
    if pib.empty:
        st.info("Dados de PIB em atualização.")
    else:
        fig = px.line(pib, x="Ano", y="Valor", markers=True)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("👷 Empregos Formais – CAGED")
    caged = get_timeseries("EMPREGOS_CAGED", source="CAGED_NOVO")
    if caged.empty:
        caged = get_timeseries("EMPREGOS_CAGED", source="CAGED")
    if caged.empty:
        st.info("Dados de CAGED em atualização.")
    else:
        fig = px.bar(caged, x="Ano", y="Valor")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.subheader("🌱 Sustentabilidade")

col3, col4 = st.columns(2)

with col3:
    idsc = get_timeseries("IDSC_GERAL", source="IDSC")
    if not idsc.empty:
        st.metric("Índice IDSC", f"{idsc.iloc[-1]['Valor']:.2f}", f"{idsc.iloc[-1]['Ano']}")
    else:
        st.info("IDSC não disponível.")
        
with col4:
    emissoes = get_timeseries("EMISSOES_GEE", source="SEEG")
    if not emissoes.empty:
        st.metric("Emissões CO₂ (tCO2e)", f"{emissoes.iloc[-1]['Valor']:,.0f}", f"{emissoes.iloc[-1]['Ano']}")
    else:
        st.info("Emissões não disponíveis.")

st.markdown("---")
st.caption("**Fonte:** Base de Dados Integrada – Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação")
st.caption("Dados oficiais de IBGE, CAGED, RAIS, DataSUS, SEFAZ-MG, SEBRAE, MapBiomas, SEEG.")
