"""
ETL do IDEB - Instituto Nacional de Estudos da Educação Básica
Implementa extração e transformação de dados do IDEB para o município.
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

class IDEBETL:
    """ETL para dados do IDEB."""
    
    def __init__(self):
        self.fallback_manager = fallback_manager
    
    def run(self):
        """Executa ETL do IDEB."""
        try:
            logger.info("Iniciando ETL do IDEB")
            
            # Buscar dados do INEP
            data = self.fallback_manager.get_data_with_fallback(
                'INEP', 'IDEB', 
                {'municipio': MUNICIPIO, 'cod_ibge': COD_IBGE}
            )
            
            if data is None or data.empty:
                logger.warning("Nenhum dado do IDEB encontrado")
                return
            
            # Processar dados do IDEB
            processed_data = self._transform_ideb_data(data)
            
            # Salvar no banco - Separar por tipo de indicador
            indicators_created = 0
            
            # Salvar IDEB anos iniciais
            ideb_iniciais = self._extract_ideb_by_level(processed_data, "anos_iniciais")
            if not ideb_iniciais.empty:
                inserted = upsert_indicators(
                    ideb_iniciais,
                    indicator_key="IDEB_ANOS_INICIAIS",
                    source="INEP",
                    category="Educação",
                    manual=False
                )
                indicators_created += inserted
                logger.info(f"IDEB_ANOS_INICIAIS: {inserted} registros")
            
            # Salvar IDEB anos finais
            ideb_finais = self._extract_ideb_by_level(processed_data, "anos_finais")
            if not ideb_finais.empty:
                inserted = upsert_indicators(
                    ideb_finais,
                    indicator_key="IDEB_ANOS_FINAIS",
                    source="INEP",
                    category="Educação",
                    manual=False
                )
                indicators_created += inserted
                logger.info(f"IDEB_ANOS_FINAIS: {inserted} registros")
            
            # Salvar dados genéricos como IDEB
            if not processed_data.empty:
                inserted = upsert_indicators(
                    processed_data,
                    indicator_key="IDEB",
                    source="INEP",
                    category="Educação",
                    manual=False
                )
                indicators_created += inserted
            
            logger.info(f"IDEB ETL concluído: {indicators_created} registros totais")
            
        except Exception as e:
            logger.error(f"Erro no ETL do IDEB: {e}")
    
    def _extract_ideb_by_level(self, data: pd.DataFrame, level: str) -> pd.DataFrame:
        """Extrai dados do IDEB por nível de ensino."""
        if data.empty:
            return pd.DataFrame(columns=["year", "value", "unit"])
        
        # Filtrar dados relevantes para o nível
        level_data = data[data['unit'].str.contains(level, case=False, na=False)]
        
        # Se não houver dados reais para o nível solicitado, não criar séries simuladas.
        # A ausência de dados deve ser explicitamente tratada no painel/relatórios.
        if level_data.empty:
            logger.warning(
                "Nenhum dado real de IDEB encontrado para o nível '%s'. "
                "Nenhuma série simulada será criada.",
                level,
            )
            return pd.DataFrame(columns=["year", "value", "unit"])
        
        return level_data[["year", "value", "unit"]].copy()
    
    def _transform_ideb_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados do IDEB para o formato padrão."""
        if data.empty:
            return pd.DataFrame(columns=["year", "value", "unit"])
        
        # Normalizar colunas
        data.columns = [col.strip().lower() for col in data.columns]
        
        # Implementar transformação específica para IDEB
        if 'id_escola' in data.columns and 'ano' in data.columns:
            return self._transform_ideb_schools(data)
        elif 'ano_censo' in data.columns:
            return self._transform_ideb_censo(data)
        elif 'rede_media' in data.columns:
            return self._transform_ideb_rede_media(data)
        else:
            # Transformação genérica
            return self._transform_ideb_generic(data)
    
    def _transform_ideb_schools(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados de escolas do IDEB."""
        result_data = []
        
        # Para cada linha, criar registros para diferentes indicadores
        for _, row in data.iterrows():
            year = int(row['ano'])
            
            # IDEB Score
            if 'id_escola' in data.columns and pd.notna(row['id_escola']):
                try:
                    score = float(row['id_escola'])
                    result_data.append({
                        "year": year,
                        "value": score,
                        "unit": "Score IDEB"
                    })
                except:
                    logger.warning(f"Valor IDEB inválido: {row.get('id_escola')}")
            
            # Taxa de aprovação
            if 'tx_aprovacao' in data.columns and pd.notna(row['tx_aprovacao']):
                try:
                    taxa = float(row['tx_aprovacao'])
                    result_data.append({
                        "year": year,
                        "value": taxa,
                        "unit": "Taxa de Aprovação"
                    })
                except:
                    logger.warning(f"Taxa de aprovação inválida: {row.get('taxa_aprovacao')}")
        
        return pd.DataFrame(result_data)
    
    def _transform_ideb_censo(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados do censo escolar do IDEB."""
        result_data = []
        
        for _, row in data.iterrows():
            year = int(row['ano_censo'])
            
            # Número de matrículas
            if 'matriculas' in data.columns and pd.notna(row['matriculas']):
                try:
                    matriculas = int(row['matriculas'])
                    result_data.append({
                        "year": year,
                        "value": matriculas,
                        "unit": "Matrículas"
                    })
                except:
                    logger.warning(f"Número de matrículas inválido: {row.get('matriculas')}")
            
            # Número de docentes
            if 'docentes' in data.columns and pd.notna(row['docentes']):
                try:
                    docentes = int(row['docentes'])
                    result_data.append({
                        "year": year,
                        "value": docentes,
                        "unit": "Docentes"
                    })
                except:
                    logger.warning(f"Número de docentes inválido: {row.get('docentes')}")
            
            # Alunos e turmas
            if 'anos_turma' in data.columns and pd.notna(row['anos_turma']):
                try:
                    anos_turma = int(row['anos_turma'])
                    result_data.append({
                        "year": year,
                        "value": anos_turma,
                        "unit": "Anos/Turma"
                    })
                except:
                    logger.warning(f"Anos/turma inválido: {row.get('anos_turma')}")
            
            # Taxa de aprovação
            if 'tx_aprovacao' in data.columns and pd.notna(row['tx_aprovacao']):
                try:
                    taxa = float(row['tx_aprovacao'])
                    result_data.append({
                        "year": year,
                        "value": taxa,
                        "unit": "Taxa de Aprovação"
                    })
                except:
                    logger.warning(f"Taxa de aprovação inválida: {row.get('tx_aprovacao')}")
        
        return pd.DataFrame(result_data)
    
    def _transform_ideb_rede_media(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transforma dados de redes de mídia do IDEB."""
        result_data = []
        
        for _, row in data.iterrows():
            year = int(row['ano_censo'])
            
            # Taxa de aprovação
            if 'tx_aprovacao' in data.columns and pd.notna(row['tx_aprovacao']):
                try:
                    taxa = float(row['tx_aprovacao'])
                    result_data.append({
                        "year": year,
                        "value": taxa,
                        "unit": "Taxa de Aprovação"
                    })
                except:
                    logger.warning(f"Taxa de aprovação inválida: {row.get('tx_aprovacao')}")
            
            # Número de estudantes
            if 'estudantes' in data.columns and pd.notna(row['estudantes']):
                try:
                    estudantes = int(row['estudantes'])
                    result_data.append({
                        "year": year,
                        "value": estudantes,
                        "unit": "Estudantes"
                    })
                except:
                    logger.warning(f"Número de estudantes inválido: {row.get('estudantes')}")
            
        return pd.DataFrame(result_data)
    
    def _transform_ideb_generic(self, data: pd.DataFrame) -> pd.DataFrame:
        """Transformação genérica para dados do IDEB."""
        result_data = []
        
        for _, row in data.iterrows():
            year = int(row.get('ano', 0))
            
            # Tentar identificar colunas numéricas
            numeric_cols = [col for col in data.columns if col not in ['ano', 'municipio', 'cod_ibge', 'uf']]
            
            for col in numeric_cols:
                if pd.notna(row[col]):
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

# Instância do ETL do IDEB
ideb_etl = IDEBETL()
