"""
ETL para dados de MEI - Microempreendedores Individuais
Coleta dados de empreendedores MEI para o município.
"""

import logging
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime

from config import DATA_DIR, COD_IBGE, MUNICIPIO, UF
from database import upsert_indicators
from utils.fallback_manager import fallback_manager

logger = logging.getLogger(__name__)

class MEIETL:
    """ETL para dados de MEI."""
    
    def __init__(self):
        self.fallback_manager = fallback_manager
    
    def run(self):
        """Executa ETL de MEI."""
        try:
            logger.info("Iniciando ETL de MEI")
            
            # Buscar dados de MEI do arquivo real
            data = self._load_mei_data()
            
            if data is None or data.empty:
                logger.warning("Nenhum dado de MEI encontrado")
                return
            
            # Processar dados
            processed_data = self._transform_mei_data(data)
            
            # Salvar no banco
            inserted = upsert_indicators(
                processed_data,
                indicator_key="EMPREENDEDORES_MEI",
                source="SEBRAE",
                category="Trabalho",
                manual=False
            )
            
            logger.info(f"MEI ETL concluído: {inserted} registros")
            
        except Exception as e:
            logger.error(f"Erro no ETL de MEI: {e}")
    
    def _load_mei_data(self) -> pd.DataFrame:
        """Carrega dados de MEI de arquivos reais."""
        import glob
        
        raw_dir = DATA_DIR / "raw"
        
        # Procurar arquivos que possam conter dados de MEI
        mei_files = []
        for pattern in ["*mei*", "*MEI*", "*microempreendedor*"]:
            mei_files.extend(glob.glob(str(raw_dir / pattern)))
        
        if not mei_files:
            logger.warning("Nenhum arquivo de MEI encontrado em data/raw")
            return pd.DataFrame()
        
        # Tentar carregar o primeiro arquivo encontrado
        for file_path in mei_files:
            try:
                df = pd.read_csv(file_path)
                logger.info(f"Arquivo MEI encontrado: {file_path}")
                return df
            except Exception as e:
                logger.warning(f"Erro ao ler arquivo {file_path}: {e}")
                continue
        
        return pd.DataFrame()
    
    def _transform_mei_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados de MEI para o formato padrão."""
        if data.empty:
            return pd.DataFrame(columns=["year", "value", "unit"])
        
        # Normalizar colunas
        data.columns = [col.strip().lower() for col in data.columns]
        
        result_data = []
        
        # Para cada linha, extrair ano e valor
        for _, row in data.iterrows():
            year = None
            value = None
            
            # Tentar identificar coluna de ano
            for col in ['ano', 'year', 'periodo', 'data_ano']:
                if col in data.columns and pd.notna(row[col]):
                    year = int(row[col])
                    break
            
            # Tentar identificar coluna de valor
            for col in ['mei', 'empreendedores', 'microempreendedores', 'quantidade', 'total']:
                if col in data.columns and pd.notna(row[col]):
                    value = float(row[col])
                    break
            
            if year is not None and value is not None:
                result_data.append({
                    "year": year,
                    "value": value,
                    "unit": "Empreendedores"
                })
        
        return pd.DataFrame(result_data)
    


# Instância do ETL de MEI
mei_etl = MEIETL()
