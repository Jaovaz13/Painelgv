"""
ETL para dados salariais - Salário Médio
Coleta dados de salários para o município.
"""

import logging
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

from config import DATA_DIR, COD_IBGE, MUNICIPIO, UF
from database import upsert_indicators
from utils.fallback_manager import fallback_manager

logger = logging.getLogger(__name__)

class SalariosETL:
    """ETL para dados salariais."""
    
    def __init__(self):
        self.fallback_manager = fallback_manager
    
    def run(self):
        """Executa ETL de salários."""
        try:
            logger.info("Iniciando ETL de Salários")
            
            # Buscar dados salariais do arquivo real
            data = self._load_salarios_data()
            
            if data is None or data.empty:
                logger.warning("Nenhum dado salarial encontrado")
                return
            
            # Processar dados
            processed_data = self._transform_salarios_data(data)
            
            # Salvar no banco
            inserted = upsert_indicators(
                processed_data,
                indicator_key="SALARIO_MEDIO_MG",
                source="SEBRAE",
                category="Trabalho",
                manual=False
            )
            
            logger.info(f"Salários ETL concluído: {inserted} registros")
            
        except Exception as e:
            logger.error(f"Erro no ETL de Salários: {e}")
    
    def _load_salarios_data(self) -> pd.DataFrame:
        """Carrega dados salariais do arquivo real."""
        file_path = DATA_DIR / "raw" / "remuneracao-media-do-trabalhador-por-setor-economico-e-divisoes-economicas-1.csv"
        
        if not file_path.exists():
            logger.warning(f"Arquivo não encontrado: {file_path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"Arquivo de salários encontrado: {file_path}")
            return df
        except Exception as e:
            logger.error(f"Erro ao ler arquivo de salários: {e}")
            return pd.DataFrame()
    
    def _transform_salarios_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados salariais para o formato padrão."""
        if data.empty:
            return pd.DataFrame(columns=["year", "value", "unit"])
        
        # Normalizar colunas
        data.columns = [col.strip().lower() for col in data.columns]
        
        result_data = []
        
        # Para cada linha, extrair ano e valor salarial
        for _, row in data.iterrows():
            year = None
            value = None
            
            # Tentar identificar coluna de ano
            for col in ['ano', 'year', 'periodo', 'data_ano']:
                if col in data.columns and pd.notna(row[col]):
                    year = int(row[col])
                    break
            
            # Tentar identificar coluna de salário
            for col in ['salario_medio', 'salario', 'remuneracao_media', 'valor_medio', 'media_salarial']:
                if col in data.columns and pd.notna(row[col]):
                    value = float(row[col])
                    break
            
            if year is not None and value is not None:
                result_data.append({
                    "year": year,
                    "value": value,
                    "unit": "R$"
                })
        
        return pd.DataFrame(result_data)
    


# Instância do ETL de Salários
salarios_etl = SalariosETL()
