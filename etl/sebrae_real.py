"""
ETL para dados SEBRAE reais - Empregos e Estabelecimentos
Coleta dados reais dos arquivos SEBRAE já existentes.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from config import DATA_DIR, COD_IBGE, MUNICIPIO, UF
from database import upsert_indicators

logger = logging.getLogger(__name__)

class SEBRAERealETL:
    """ETL para dados reais do SEBRAE."""
    
    def run(self):
        """Executa ETL de dados reais do SEBRAE."""
        try:
            logger.info("Iniciando ETL SEBRAE Real")
            
            # Processar arquivo de empregos
            self._process_empregos()
            
            # Processar arquivo de estabelecimentos
            self._process_estabelecimentos()
            
            # Processar arquivo de remuneração
            self._process_remuneracao()
            
            logger.info("ETL SEBRAE Real concluído")
            
        except Exception as e:
            logger.error(f"Erro no ETL SEBRAE Real: {e}")
    
    def _process_empregos(self):
        """Processa arquivo de empregos totais."""
        file_path = DATA_DIR / "raw" / "Sebrae empregados-total-1.csv"
        
        if not file_path.exists():
            logger.warning(f"Arquivo não encontrado: {file_path}")
            return
        
        try:
            df = pd.read_csv(file_path)
            
            # Filtrar para o município correto
            df_mun = df[df["Municipality ID"] == int(COD_IBGE)]
            
            if df_mun.empty:
                logger.warning(f"Dados do município {COD_IBGE} não encontrados no arquivo de empregos")
                return
            
            # Preparar dados para o banco
            result_data = []
            for _, row in df_mun.iterrows():
                year = int(row["Year"])
                workers = int(row["Workers"])
                
                result_data.append({
                    "year": year,
                    "value": workers,
                    "unit": "Empregos"
                })
            
            df_result = pd.DataFrame(result_data)
            
            # Salvar no banco
            inserted = upsert_indicators(
                df_result,
                indicator_key="EMPREGOS_SEBRAE",
                source="SEBRAE",
                category="Trabalho"
            )
            
            logger.info(f"EMPREGOS_SEBRAE: {inserted} registros criados")
            
        except Exception as e:
            logger.error(f"Erro ao processar empregos SEBRAE: {e}")
    
    def _process_estabelecimentos(self):
        """Processa arquivo de estabelecimentos por setor."""
        file_path = DATA_DIR / "raw" / "Sebrae estabelecimentos-por-setor-economico-e-divisoes-economicas-1.csv"
        
        if not file_path.exists():
            logger.warning(f"Arquivo não encontrado: {file_path}")
            return
        
        try:
            df = pd.read_csv(file_path)
            
            # Agrupar por ano para obter total de estabelecimentos
            df_totals = df.groupby("Year")["Establishments"].sum().reset_index()
            
            # Preparar dados para o banco
            result_data = []
            for _, row in df_totals.iterrows():
                year = int(row["Year"])
                establishments = int(row["Establishments"])
                
                result_data.append({
                    "year": year,
                    "value": establishments,
                    "unit": "Estabelecimentos"
                })
            
            df_result = pd.DataFrame(result_data)
            
            # Salvar no banco
            inserted = upsert_indicators(
                df_result,
                indicator_key="ESTABELECIMENTOS_SEBRAE",
                source="SEBRAE",
                category="Negócios"
            )
            
            logger.info(f"ESTABELECIMENTOS_SEBRAE: {inserted} registros criados")
            
        except Exception as e:
            logger.error(f"Erro ao processar estabelecimentos SEBRAE: {e}")
    
    def _process_remuneracao(self):
        """Processa arquivo de remuneração média."""
        file_path = DATA_DIR / "raw" / "remuneracao-media-do-trabalhador-por-setor-economico-e-divisoes-economicas-1.csv"
        
        if not file_path.exists():
            logger.warning(f"Arquivo não encontrado: {file_path}")
            return
        
        try:
            df = pd.read_csv(file_path)
            
            # Agrupar por ano para obter média geral
            df_totals = df.groupby("Year")["Remuneration Avg Nominal"].mean().reset_index()
            
            # Preparar dados para o banco
            result_data = []
            for _, row in df_totals.iterrows():
                year = int(row["Year"])
                salary = float(row["Remuneration Avg Nominal"])
                
                result_data.append({
                    "year": year,
                    "value": salary,
                    "unit": "R$"
                })
            
            df_result = pd.DataFrame(result_data)
            
            # Salvar no banco
            inserted = upsert_indicators(
                df_result,
                indicator_key="SALARIO_MEDIO_MG",
                source="SEBRAE",
                category="Trabalho"
            )
            
            logger.info(f"SALARIO_MEDIO_MG: {inserted} registros criados")
            
        except Exception as e:
            logger.error(f"Erro ao processar remuneração SEBRAE: {e}")

# Instância do ETL SEBRAE Real
sebrae_real_etl = SEBRAERealETL()
