"""
ETL de Leitos por Habitante (RAIS/CAGED)
Implementa extração e transformação de dados de empregos formais.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from config import DATA_DIR, COD_IBGE, MUNICIPIO, UF
from database import upsert_indicators
from utils.fallback_manager import fallback_manager

logger = logging.getLogger(__name__)

class LeitosETL:
    """ETL para dados de empregos formais (RAIS/CAGED)."""
    
    def __init__(self):
        self.fallback_manager = fallback_manager
    
    def run(self):
        """Executa ETL de empregos formais."""
        try:
            logger.info("Iniciando ETL de Empregos Formais")
            
            # Buscar dados do CAGED
            data = self.fallback_manager.get_data_with_fallback(
                'CAGED', 'EMPREGOS_FORMAIS', 
                {'municipio': MUNICIPIO, 'cod_ibge': COD_IBGE}
            )
            
            if data is None or data.empty:
                logger.warning("Nenhum dado de empregos formais encontrado")
                return
            
            # Processar dados de empregos
            processed_data = self._transform_empregos_data(data)
            
            # Salvar no banco
            inserted = upsert_indicators(
                processed_data,
                indicator_key="EMPREGOS_FORMAIS",
                source="CAGED",
                category="Trabalho e Renda",
                manual=True
            )
            
            logger.info(f"Empregos Formais ETL concluído: {inserted} registros")
            
        except Exception as e:
            logger.error(f"Erro no ETL de Empregos Formais: {e}")
    
    def _transform_empregos_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados de empregos formais para o formato padrão."""
        if data.empty:
            return pd.DataFrame(columns=["year", "value", "unit"])
        
        # Normalizar colunas
        data.columns = [col.strip().lower() for col in data.columns]
        
        # Implementar transformação específica para empregos
        if 'municipio' in data.columns and 'empregados' in data.columns:
            return self._transform_empregos_municipio(data)
        elif 'empregados' in data.columns and 'ano' in data.columns:
            return self._transform_empregos_anual(data)
        else:
            # Transformação genérica
            return self._transform_empregos_generic(data)
    
    def _transform_empregos_municipio(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados de empregos por município."""
        result_data = []
        
        # Filtrar para Governador Valadares
        gv_data = data[data['municipio'].str.contains('Governador Valadares', case=False, na=False)]
        
        for _, row in gv_data.iterrows():
            year = int(row['ano'])
            
            # Empregos formais
            if 'empregos' in data.columns and pd.notna(row['empregos']):
                try:
                    empregos = float(row['empregos'])
                    result_data.append({
                        "year": year,
                        "value": empregos,
                        "unit": "Empregos Formais"
                    })
                except:
                    logger.warning(f"Empregos inválidos: {row.get('empregos')}")
            
            # Estabelecimentos
            if 'estabelecimentos' in data.columns and pd.notna(row['estabelecimentos']):
                try:
                    estabelecimentos = float(row['estabelecimentos'])
                    result_data.append({
                        "year": year,
                        "value": estabelecimentos,
                        "unit": "Estabelecimentos"
                    })
                except:
                    logger.warning(f"Estabelecimentos inválidos: {row.get('estabelecimentos')}")
            
            return pd.DataFrame(result_data)
    
    def _transform_empregos_anual(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados de empregos anuais."""
        result_data = []
        
        for _, row in data.iterrows():
            year = int(row['ano'])
            
            # Empregos por ano
            if 'empregos' in data.columns and pd.notna(row['empregos']):
                try:
                    empregos = float(row['empregos'])
                    result_data.append({
                        "year": year,
                        "value": empregos,
                        "unit": "Empregos Anuais"
                    })
                except:
                    logger.warning(f"Empregos anuais inválidos: {row.get('empregos')}")
            
            return pd.DataFrame(result_data)
    
    def _transform_empregos_generic(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transformação genérica de empregos formais."""
        result_data = []
        
        numeric_cols = [col for col in data.columns 
                       if col not in ['municipio', 'cod_ibge', 'uf', 'ano']]
        
        for _, row in data.iterrows():
            year = int(row.get('ano', 0))
            
            for col in numeric_cols:
                if col in data.columns and pd.notna(row[col]):
                    try:
                        value = float(row[col])
                        result_data.append({
                            "year": year,
                            "value": value,
                            "unit": col.title()
                        })
                    except:
                        continue
            
            return pd.DataFrame(result_data)

# Instância do ETL de Empregos
empregos_etl = LeitosETL()
