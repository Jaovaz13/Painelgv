"""
Script para criar ETLs faltantes baseados nos indicadores que o painel espera mas não existem no banco.
"""

import logging
import pandas as pd
from typing import Dict, List
import sys
import os

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import upsert_indicators
from config import COD_IBGE, MUNICIPIO, UF

logger = logging.getLogger(__name__)

def create_pib_crescimento():
    """
    Calcula crescimento do PIB a partir dos dados existentes.
    """
    from database import get_timeseries
    
    # Obter dados do PIB total
    df_pib = get_timeseries("PIB_TOTAL", "IBGE")
    if df_pib.empty or len(df_pib) < 2:
        logger.warning("Dados do PIB insuficientes para calcular crescimento")
        return
    
    # Calcular variação percentual ano a ano
    df_pib = df_pib.sort_values("Ano")
    df_pib["Valor"] = df_pib["Valor"].pct_change() * 100
    
    # Remover primeiro ano (sem dado anterior)
    df_crescimento = df_pib.dropna(subset=["Valor"]).copy()
    df_crescimento["Unidade"] = "%"
    
    # Salvar no banco
    df_crescimento = df_crescimento.rename(columns={"Ano": "year", "Valor": "value", "Unidade": "unit"})
    result = upsert_indicators(
        df_crescimento[["year", "value", "unit"]],
        indicator_key="PIB_CRESCIMENTO",
        source="CALCULADO",
        category="Economia"
    )
    
    logger.info(f"PIB_CRESCIMENTO: {result} registros criados")

def create_empregos_caged():
    """
    Cria indicador de empregos CAGED a partir do saldo mensal.
    """
    from database import get_timeseries
    
    # Obter dados do saldo mensal
    df_saldo = get_timeseries("SALDO_CAGED_MENSAL", "CAGED_MANUAL_MG")
    if df_saldo.empty:
        logger.warning("Dados do CAGED mensal não encontrados")
        return
    
    # Agrupar por ano para criar série anual
    df_anual = df_saldo.groupby("Ano")["Valor"].sum().reset_index()
    df_anual["Unidade"] = "Empregos"
    
    # Salvar no banco
    df_anual = df_anual.rename(columns={"Ano": "year", "Valor": "value", "Unidade": "unit"})
    result = upsert_indicators(
        df_anual[["year", "value", "unit"]],
        indicator_key="EMPREGOS_CAGED",
        source="CAGED_MANUAL_MG",
        category="Trabalho"
    )
    
    logger.info(f"EMPREGOS_CAGED: {result} registros criados")

def create_saldo_caged():
    """
    Cria indicador de saldo CAGED acumulado.
    """
    from database import get_timeseries
    
    # Obter dados do saldo mensal
    df_saldo = get_timeseries("SALDO_CAGED_MENSAL", "CAGED_MANUAL_MG")
    if df_saldo.empty:
        logger.warning("Dados do CAGED mensal não encontrados")
        return
    
    # Calcular saldo acumulado
    df_saldo = df_saldo.sort_values("Ano")
    df_acumulado = df_saldo.copy()
    df_acumulado["Valor"] = df_saldo["Valor"].cumsum()
    df_acumulado["Unidade"] = "Empregos"
    
    # Salvar no banco
    df_acumulado = df_acumulado.rename(columns={"Ano": "year", "Valor": "value", "Unidade": "unit"})
    result = upsert_indicators(
        df_acumulado[["year", "value", "unit"]],
        indicator_key="SALDO_CAGED",
        source="CAGED_MANUAL_MG",
        category="Trabalho"
    )
    
    logger.info(f"SALDO_CAGED: {result} registros criados")

def create_empresas_ativas():
    """
    Cria indicador de empresas ativas a partir de dados existentes.
    """
    from database import get_timeseries
    
    # Tentar obter de múltiplas fontes
    fontes = ["RAIS", "SEBRAE"]
    df_empresas = pd.DataFrame()
    
    for fonte in fontes:
        df_temp = get_timeseries("NUM_EMPRESAS", fonte)
        if not df_temp.empty:
            df_empresas = df_temp
            break
    
    if df_empresas.empty:
        logger.warning("Dados de empresas não encontrados")
        return
    
    # Salvar como EMPRESAS_ATIVAS (somente com dados reais existentes)
    df_empresas = df_empresas.rename(columns={"Ano": "year", "Valor": "value", "Unidade": "unit"})
    result = upsert_indicators(
        df_empresas[["year", "value", "unit"]],
        indicator_key="EMPRESAS_ATIVAS",
        source=df_empresas["source"].iloc[0] if not df_empresas.empty else "RAIS",
        category="Negócios"
    )
    
    logger.info(f"EMPRESAS_ATIVAS (a partir de dados reais): {result} registros criados")

def create_idsc_geral():
    """
    Cria indicador IDSC_GERAL a partir do índice de sustentabilidade.
    """
    from database import get_timeseries
    
    # Obter dados do índice existente
    df_idsc = get_timeseries("INDICE_SUSTENTABILIDADE", "SUSTENTABILIDADE")
    if df_idsc.empty:
        logger.warning("Dados do IDSC não encontrados")
        return
    
    # Salvar como IDSC_GERAL
    df_idsc = df_idsc.rename(columns={"Ano": "year", "Valor": "value", "Unidade": "unit"})
    result = upsert_indicators(
        df_idsc[["year", "value", "unit"]],
        indicator_key="IDSC_GERAL",
        source="SUSTENTABILIDADE",
        category="Sustentabilidade"
    )
    
    logger.info(f"IDSC_GERAL: {result} registros criados")

def create_placeholder_indicators():
    """
    [DESATIVADO] Antes criava indicadores simulados (placeholders) para preencher lacunas.
    
    Por regra institucional do PAINEL GV, é proibido gerar ou carregar dados simulados.
    Esta função foi mantida apenas por compatibilidade, mas não insere mais nenhum dado.
    
    Sempre que um indicador real estiver ausente, essa ausência deve ser tratada
    explicitamente no painel/relatórios (mensagem de falta de dado), nunca com números
    artificiais.
    """
    logger.warning(
        "create_placeholder_indicators() chamado, mas está desativado por política de "
        "dados reais do PAINEL GV. Nenhum dado simulado foi criado."
    )

def run_missing_etls():
    """
    Executa todos os ETLs faltantes.
    """
    logger.info("Iniciando criação de indicadores faltantes...")
    
    # ETLs baseados em dados existentes
    create_pib_crescimento()
    create_empregos_caged()
    create_saldo_caged()
    create_empresas_ativas()
    create_idsc_geral()
    
    # Placeholders para dados que não temos
    create_placeholder_indicators()
    
    logger.info("Criação de indicadores faltantes concluída!")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    run_missing_etls()
