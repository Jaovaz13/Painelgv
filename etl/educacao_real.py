"""
ETL para dados de Educação reais do INEP/Sinopse
Processa múltiplos anos e formatos de arquivos da educação.
"""

import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import os
import zipfile

from config import DATA_DIR, COD_IBGE, MUNICIPIO, UF
from database import upsert_indicators

logger = logging.getLogger(__name__)

class EducacaoRealETL:
    """ETL para dados reais da Educação."""
    
    def run(self):
        """Executa ETL de dados reais da Educação."""
        try:
            logger.info("Iniciando ETL Educação Real")
            
            # Encontrar todos os arquivos de educação
            edu_files = self._find_educacao_files()
            
            if not edu_files:
                logger.warning("Nenhum arquivo de educação encontrado")
                return
            
            # Processar todos os arquivos encontrados
            total_processed = 0
            for file_path in edu_files:
                processed = self._process_educacao_file(file_path)
                if processed:
                    total_processed += processed
                    logger.info(f"Arquivo processado: {file_path.name} ({processed} registros)")
            
            logger.info(f"ETL Educação Real concluído: {total_processed} registros totais")
            
        except Exception as e:
            logger.error(f"Erro no ETL Educação Real: {e}")
    
    def _find_educacao_files(self) -> list:
        """Encontra todos os arquivos de educação."""
        edu_files = []
        
        for root, dirs, files in os.walk(DATA_DIR / "raw"):
            for file in files:
                if 'Sinopse' in file and 'Educação' in file:
                    file_path = Path(root) / file
                    if file_path.exists():
                        edu_files.append(file_path)
                        logger.info(f"Arquivo de educação encontrado: {file_path}")
        
        return edu_files
    
    def _process_educacao_file(self, file_path: Path) -> int:
        """Processa um arquivo de educação."""
        try:
            # Tentar ler como Excel primeiro
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                return self._process_excel_file(file_path)
            # Tentar ler como ODS
            elif file_path.suffix.lower() in ['.ods']:
                return self._process_ods_file(file_path)
            # Tentar ler como CSV
            elif file_path.suffix.lower() in ['.csv']:
                return self._process_csv_file(file_path)
            # Tentar ler arquivos dentro de ZIP
            elif file_path.suffix.lower() == '.zip':
                return self._process_zip_file(file_path)
            else:
                logger.warning(f"Formato não suportado: {file_path}")
                return 0
                
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_path}: {e}")
            return 0
    
    def _process_excel_file(self, file_path: Path) -> int:
        """Processa arquivo Excel de educação."""
        try:
            xl_file = pd.ExcelFile(file_path)
            
            # Tentar encontrar aba com dados relevantes
            sheet_names = xl_file.sheet_names
            target_sheet = None
            
            for sheet in sheet_names:
                if any(keyword in sheet.lower() for keyword in 
                    ['escola', 'aluno', 'matricula', 'docente', 'turma', 'taxa']):
                    target_sheet = sheet
                    break
            
            if not target_sheet:
                target_sheet = sheet_names[0]  # Usar primeira aba
            
            df = pd.read_excel(file_path, sheet_name=target_sheet)
            
            # Extrair ano do nome do arquivo
            year = self._extract_year_from_filename(file_path.name)
            
            if year and not df.empty:
                return self._save_educacao_indicators(df, year, file_path.name)
            
            return 0
            
        except Exception as e:
            logger.error(f"Erro ao processar Excel {file_path}: {e}")
            return 0
    
    def _process_ods_file(self, file_path: Path) -> int:
        """Processa arquivo ODS de educação."""
        try:
            df = pd.read_excel(file_path, engine='odf')
            
            year = self._extract_year_from_filename(file_path.name)
            
            if year and not df.empty:
                return self._save_educacao_indicators(df, year, file_path.name)
            
            return 0
            
        except Exception as e:
            logger.error(f"Erro ao processar ODS {file_path}: {e}")
            return 0
    
    def _process_csv_file(self, file_path: Path) -> int:
        """Processa arquivo CSV de educação."""
        try:
            df = pd.read_csv(file_path, sep=';', encoding='latin-1')
            
            year = self._extract_year_from_filename(file_path.name)
            
            if year and not df.empty:
                return self._save_educacao_indicators(df, year, file_path.name)
            
            return 0
            
        except Exception as e:
            logger.error(f"Erro ao processar CSV {file_path}: {e}")
            return 0
    
    def _process_zip_file(self, file_path: Path) -> int:
        """Processa arquivo ZIP com múltiplos arquivos de educação."""
        try:
            total_processed = 0
            
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.endswith('.xlsx'):
                        # Extrair arquivo Excel para memória
                        with zip_ref.open(file_info.filename) as excel_file:
                            df = pd.read_excel(excel_file)
                            year = self._extract_year_from_filename(file_info.filename)
                            
                            if year and not df.empty:
                                processed = self._save_educacao_indicators(df, year, file_info.filename)
                                total_processed += processed
                                logger.info(f"Arquivo do ZIP processado: {file_info.filename} ({processed} registros)")
            
            return total_processed
            
        except Exception as e:
            logger.error(f"Erro ao processar ZIP {file_path}: {e}")
            return 0
    
    def _extract_year_from_filename(self, filename: str) -> Optional[int]:
        """Extrai ano de 4 dígitos do nome do arquivo."""
        import re
        
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            return int(year_match.group())
        
        return None
    
    def _save_educacao_indicators(self, df: pd.DataFrame, year: int, source_file: str) -> int:
        """Salva indicadores de educação no banco."""
        try:
            # Normalizar colunas - tratar caso seja Index
            if hasattr(df.columns, 'lower'):
                df.columns = [col.strip().lower() for col in df.columns]
            else:
                df.columns = [str(col).strip().lower() for col in df.columns]
            
            indicators_created = 0
            
            # Matrículas totais
            if any(keyword in str(df.columns).lower() for keyword in ['matricula', 'aluno', 'total']):
                matriculas = self._extract_numeric_value(df, ['matricula', 'aluno', 'total'])
                if matriculas > 0:
                    result_df = pd.DataFrame([{
                        "year": year,
                        "value": matriculas,
                        "unit": "Alunos"
                    }])
                    
                    inserted = upsert_indicators(
                        result_df,
                        indicator_key="MATRICULAS_TOTAL",
                        source="INEP_RAW",
                        category="Educação"
                    )
                    indicators_created += inserted
                    logger.info(f"MATRICULAS_TOTAL {year}: {inserted} registros")
            
            # Escolas
            if any(keyword in str(df.columns).lower() for keyword in ['escola', 'unidade', 'estabelecimento']):
                escolas = self._extract_numeric_value(df, ['escola', 'unidade', 'estabelecimento'])
                if escolas > 0:
                    result_df = pd.DataFrame([{
                        "year": year,
                        "value": escolas,
                        "unit": "Escolas"
                    }])
                    
                    inserted = upsert_indicators(
                        result_df,
                        indicator_key="ESCOLAS_FUNDAMENTAL",
                        source="INEP_RAW",
                        category="Educação"
                    )
                    indicators_created += inserted
                    logger.info(f"ESCOLAS_FUNDAMENTAL {year}: {inserted} registros")
            
            # Taxa de aprovação
            if any(keyword in str(df.columns).lower() for keyword in ['taxa', 'aprovacao', 'aprov']):
                taxa = self._extract_numeric_value(df, ['taxa', 'aprovacao', 'aprov'])
                if taxa > 0:
                    result_df = pd.DataFrame([{
                        "year": year,
                        "value": taxa,
                        "unit": "%"
                    }])
                    
                    inserted = upsert_indicators(
                        result_df,
                        indicator_key="TAXA_APROVACAO_FUNDAMENTAL",
                        source="INEP_RAW",
                        category="Educação"
                    )
                    indicators_created += inserted
                    logger.info(f"TAXA_APROVACAO_FUNDAMENTAL {year}: {inserted} registros")
            
            return indicators_created
            
        except Exception as e:
            logger.error(f"Erro ao salvar indicadores de educação {source_file}: {e}")
            return 0
    
    def _extract_numeric_value(self, df: pd.DataFrame, keywords: list) -> float:
        """Extrai valor numérico do DataFrame baseado em palavras-chave."""
        for col in df.columns:
            if any(keyword in col.lower() for keyword in keywords):
                try:
                    values = pd.to_numeric(df[col], errors='coerce')
                    return values.max() if not values.empty else 0
                except:
                    continue
        
        return 0

# Instância do ETL Educação Real
educacao_real_etl = EducacaoRealETL()


def run():
    """
    Runner padrão do módulo para compatibilidade com orquestradores (etl_runner).
    Utiliza exclusivamente arquivos reais em `data/raw`.
    """
    return educacao_real_etl.run()
