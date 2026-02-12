#!/usr/bin/env python
"""
ETL para cálculo do PIB per capita a partir de dados do IBGE
Fonte: API SIDRA - Tabela 5938 (PIB Municipal) + População

ESTRATÉGIA:
1. Busca PIB total da tabela 5938 (variável 37)
2. Busca população estimada
3. Calcula PIB per capita = (PIB em mil reais * 1000) / População
4. Salva no banco como PIB_PER_CAPITA
"""
import logging
import requests
import pandas as pd
from typing import Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import upsert_indicators
from config import COD_IBGE

logger = logging.getLogger(__name__)

# API SIDRA - Tabela 5938 (PIB Municipal - Referência 2010)
# Variável 37: Produto Interno Bruto a preços correntes (em Mil Reais)
SIDRA_PIB_URL = f"https://apisidra.ibge.gov.br/values/t/5938/p/all/v/37/n6/{COD_IBGE}"


def fetch_pib_total() -> Optional[pd.DataFrame]:
    """
    Busca PIB total do município via API SIDRA.
    
    Returns:
        DataFrame com colunas: Ano, Valor (em reais, já convertido de mil reais)
    """
    try:
        logger.info(f"Buscando PIB total via SIDRA para município {COD_IBGE}...")
        response = requests.get(SIDRA_PIB_URL, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Erro na API SIDRA: status {response.status_code}")
            return None
        
        data = response.json()
        
        # Processa resposta da API SIDRA
        # Formato: lista de dicts com D1N (Ano), V (Valor), MN (Unidade)
        records = []
        for item in data[1:]:  # Pula header
            if isinstance(item, dict) and 'D1N' in item and 'V' in item:
                try:
                    ano = int(item['D1N'])
                    # Filtrar apenas anos >= 2010
                    if ano >= 2010:
                        # Valor vem em "Mil Reais", converter para Reais
                        valor_mil_reais = float(item['V'])
                        valor_reais = valor_mil_reais * 1000
                        records.append({'Ano': ano, 'Valor': valor_reais})
                except (ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar registro: {item} - {e}")
                    continue
        
        if not records:
            logger.error("Nenhum registro válido encontrado na resposta da API")
            return None
        
        df = pd.DataFrame(records)
        logger.info(f"PIB total obtido: {len(df)} anos ({df['Ano'].min()}-{df['Ano'].max()})")
        return df
        
    except Exception as e:
        logger.error(f"Erro ao buscar PIB total: {e}")
        return None


def fetch_populacao() -> Optional[pd.DataFrame]:
    """
    Busca população estimada via API SIDRA.
    Tabela 6579: População residente estimada
    Período: 2010 até o último ano disponível
    
    Returns:
        DataFrame com colunas: Ano, Valor (população)
    """
    try:
        # API SIDRA - Tabela 6579 (População residente estimada)
        # Variável 9324: População residente estimada
        # Período: de 2010 em diante
        url = f"https://apisidra.ibge.gov.br/values/t/6579/p/all/v/9324/n6/{COD_IBGE}"
        
        logger.info(f"Buscando população via SIDRA para município {COD_IBGE}...")
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Erro na API SIDRA (população): status {response.status_code}")
            return None
        
        data = response.json()
        
        # Processa resposta da API SIDRA
        records = []
        for item in data[1:]:  # Pula header
            if isinstance(item, dict) and 'D1N' in item and 'V' in item:
                try:
                    ano = int(item['D1N'])
                    # Filtrar apenas anos >= 2010
                    if ano >= 2010:
                        valor = float(item['V'])
                        records.append({'Ano': ano, 'Valor': valor})
                except (ValueError, TypeError) as e:
                    logger.warning(f"Erro ao processar registro de população: {item} - {e}")
                    continue
        
        if not records:
            logger.error("Nenhum registro válido de população encontrado")
            return None
        
        df = pd.DataFrame(records)
        logger.info(f"População obtida: {len(df)} anos ({df['Ano'].min()}-{df['Ano'].max()})")
        return df
        
    except Exception as e:
        logger.error(f"Erro ao buscar população: {e}")
        return None


def calcular_pib_per_capita(df_pib: pd.DataFrame, df_pop: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula PIB per capita = PIB / População.
    
    Args:
        df_pib: DataFrame com PIB total (em reais)
        df_pop: DataFrame com população
        
    Returns:
        DataFrame com PIB per capita
    """
    try:
        # Merge por ano
        df_merged = pd.merge(
            df_pib,
            df_pop,
            on='Ano',
            how='inner',
            suffixes=('_pib', '_pop')
        )
        
        if df_merged.empty:
            logger.error("Nenhum ano em comum entre PIB e População")
            return pd.DataFrame()
        
        # Calcula PIB per capita
        df_merged['Valor'] = df_merged['Valor_pib'] / df_merged['Valor_pop']
        
        # Prepara DataFrame final
        df_result = df_merged[['Ano', 'Valor']].copy()
        df_result['year'] = df_result['Ano']
        df_result['value'] = df_result['Valor']
        df_result['unit'] = 'R$ / Habitante'
        
        logger.info(f"PIB per capita calculado para {len(df_result)} anos")
        logger.info(f"Valores: min={df_result['value'].min():.2f}, max={df_result['value'].max():.2f}, média={df_result['value'].mean():.2f}")
        
        return df_result[['year', 'value', 'unit']]
        
    except Exception as e:
        logger.error(f"Erro ao calcular PIB per capita: {e}")
        return pd.DataFrame()


def run():
    """Executa o ETL completo de PIB per capita"""
    try:
        logger.info("=" * 60)
        logger.info("Iniciando ETL: PIB per Capita")
        logger.info("=" * 60)
        
        # 1. Busca PIB total
        df_pib = fetch_pib_total()
        if df_pib is None or df_pib.empty:
            logger.error("Falha ao obter PIB total. Abortando ETL.")
            return
        
        # 2. Busca população
        df_pop = fetch_populacao()
        if df_pop is None or df_pop.empty:
            logger.error("Falha ao obter população. Abortando ETL.")
            return
        
        # 3. Calcula PIB per capita
        df_per_capita = calcular_pib_per_capita(df_pib, df_pop)
        if df_per_capita.empty:
            logger.error("Falha ao calcular PIB per capita. Abortando ETL.")
            return
        
        # 4. Salva no banco
        logger.info("Salvando PIB per capita no banco de dados...")
        rows_affected = upsert_indicators(
            df_per_capita,
            indicator_key="PIB_PER_CAPITA",
            source="IBGE",
            category="Economia"
        )
        
        logger.info(f"✓ PIB per capita salvo: {rows_affected} registros")
        logger.info("=" * 60)
        logger.info("ETL PIB per Capita concluído com sucesso!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Erro no ETL de PIB per capita: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    run()
