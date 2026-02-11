"""
ETL da ESF - Sistema de Estabelecimento de Saúde
Implementa extração e transformação de dados da ESF para o município.
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

class ESFETL:
    """ETL para dados da ESF (Estabelecimento de Saúde)."""
    
    def __init__(self):
        self.fallback_manager = fallback_manager
    
    def run(self):
        """Executa ETL da ESF."""
        try:
            logger.info("Iniciando ETL da ESF")
            
            # Buscar dados do DataSUS
            data = self.fallback_manager.get_data_with_fallback(
                'DATASUS', 'MORTALIDADE_INFANTIL', 
                {'municipio': MUNICIPIO, 'cod_ibge': COD_IBGE}
            )
            
            if data is None or data.empty:
                logger.warning("Nenhum dado da ESF encontrado")
                return
            
            # Processar dados da ESF
            processed_data = self._transform_esf_data(data)
            
            # Salvar no banco
            inserted = upsert_indicators(
                processed_data,
                indicator_key="MORTALIDADE_INFANTIL",
                source="DataSUS",
                category="Saúde",
                manual=True
            )
            
            logger.info(f"ESF ETL concluído: {inserted} registros")
            
        except Exception as e:
            logger.error(f"Erro no ETL da ESF: {e}")
    
    def _transform_esf_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados da ESF para o formato padrão."""
        if data.empty:
            return pd.DataFrame(columns=["year", "value", "unit"])
        
        # Normalizar colunas
        data.columns = [col.strip().lower() for col in data.columns]
        
        # Implementar transformação específica para ESF
        if 'municipio' in data.columns and 'obitos' in data.columns:
            return self._transform_esf_obitos(data)
        elif 'cod_ibge' in data.columns:
            return self._transform_esf_municipio(data)
        else:
            # Transformação genérica
            return self._transform_esf_generic(data)
    
    def _transform_esf_obitos(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados de óbitos da ESF."""
        result_data = []
        
        # Filtrar para Governador Valadares
        gv_data = data[data['municipio'].str.contains('Governador Valadares', case=False, na=False)]
        
        for _, row in gv_data.iterrows():
            year = int(row['ano'])
            
            # Mortalidade infantil
            if 'obitos' in data.columns and pd.notna(row['obitos']):
                try:
                    obitos = float(row['obitos'])
                    result_data.append({
                        "year": year,
                        "value": obitos,
                        "unit": "Óbitos/1000 hab."
                    })
                except:
                    logger.warning(f"Valor de óbitos inválido: {row.get('obitos')}")
            
            # Nascidos vivos
            if 'nascidos_vivos' in data.columns and pd.notna(row['nascidos_vivos']):
                try:
                    nascidos = float(row['nascidos_vivos'])
                    result_data.append({
                        "year": year,
                        "value": nascidos,
                        "unit": "Nascidos vivos"
                    })
                except:
                    logger.warning(f"Nascidos vivos inválidos: {row.get('nascidos_vivos')}")
            
            # Taxa de mortalidade
            if 'taxa_mortalidade' in data.columns and pd.notna(row['taxa_mortalidade']):
                try:
                    taxa = float(row['taxa_mortalidade'])
                    result_data.append({
                        "year": year,
                        "value": taxa,
                        "unit": "Taxa/1000 hab."
                    })
                except:
                    logger.warning(f"Taxa de mortalidade inválida: {row.get('taxa_mortalidade')}")
        
        return pd.DataFrame(result_data)
    
    def _transform_esf_municipio(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados de ESF por município."""
        result_data = []
        
        # Filtrar para Governador Valadares
        gv_data = data[data['municipio'].str.contains('Governador Valadares', case=False, na=False)]
        
        for _, row in gv_data.iterrows():
            year = int(row['ano'])
            
            # Diversos tipos de dados de saúde
            if 'leitos' in data.columns:
                try:
                    leitos = float(row['leitos'])
                    result_data.append({
                        "year": year,
                        "value": leitos,
                        "unit": "Leitos"
                    })
                except:
                    logger.warning(f"Leitos inválidos: {row.get('leitos')}")
            
            if 'internacoes' in data.columns:
                try:
                    internacoes = float(row['internacoes'])
                    result_data.append({
                        "year": year,
                        "value": internacoes,
                        "unit": "Internações"
                    })
                except:
                    logger.warning(f"Internações inválidos: {row.get('internacoes')}")
            
            if 'leitos_uti' in data.columns:
                try:
                    leitos_uti = float(row['leitos_uti'])
                    result_data.append({
                        "year": year,
                        "value": leitos_uti,
                        "unit": "Leitos/UTI"
                    })
                except:
                    logger.warning(f"Leitos UTI inválidos: {row.get('leitos_uti')}")
            
            # Outros indicadores de saúde
            other_cols = [col for col in data.columns 
                          if col not in ['municipio', 'cod_ibge', 'uf', 'ano', 'obitos', 
                               'nascidos_vivos', 'taxa_mortalidade', 'leitos', 
                               'internacoes', 'leitos_uti']]
            
            for col in other_cols:
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
    
    def _transform_esf_generic(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transformação genérica para dados da ESF."""
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

# Instância do ETL da ESF
esf_etl = ESFETL()
