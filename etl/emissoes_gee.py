#!/usr/bin/env python
"""
ETL para extração de dados de Emissões GEE (Gases de Efeito Estufa)
Fonte: SEEG - Sistema de Estimativa de Emissões de Gases de Efeito Estufa

POLÍTICA: 100% DADOS REAIS
- API SEEG (se disponível)
- Fallback: arquivo em data/raw/emissoes_gee.csv
- NUNCA gera dados simulados
"""
from __future__ import annotations
import logging
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_session, Indicator
from config import DATA_DIR, COD_IBGE, MUNICIPIO, UF

logger = logging.getLogger(__name__)

# URLs da API SEEG
SEEG_API_BASE = "https://seeg.eco.br/api/v1"


def load_emissoes_from_raw() -> Optional[Dict]:
    """
    Carrega emissões de arquivo CSV em data/raw se disponível.
    Formato esperado: ano;valor
    """
    try:
        csv_path = DATA_DIR / "raw" / "emissoes_gee.csv"
        if not csv_path.exists():
            logger.warning(f"Arquivo {csv_path} não encontrado")
            return None
            
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        logger.info(f"Carregando emissões de {csv_path}")
        
        data = {
            "municipio": MUNICIPIO,
            "codigo_ibge": str(COD_IBGE),
            "emissoes": {},
        }
        
        for _, row in df.iterrows():
            year = str(int(row['ano']))
            value = float(row['valor'])
            data["emissoes"][year] = value
        
        logger.info(f"Emissões carregadas de {csv_path}: {len(df)} registros")
        return data
        
    except Exception as e:
        logger.error(f"Erro ao carregar emissões de /raw: {e}")
        return None


def extrair_emissoes_municipais() -> Optional[Dict]:
    """
    Extrai dados de emissões GEE para o município.
    
    Prioridade:
    1. API SEEG (se disponível)
    2. Arquivo local em data/raw/emissoes_gee.csv
    3. Retorna None (sem dados disponíveis)
    """
    try:
        # Tenta URL oficial da API SEEG
        url = f"{SEEG_API_BASE}/municipios/{COD_IBGE}/emissoes"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data:
                logger.info("Dados de emissões obtidos da API SEEG")
                return data
        
        # Se API não estiver disponível, tenta arquivo local
        logger.warning("API SEEG não disponível, tentando arquivo local em data/raw")
        return load_emissoes_from_raw()
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados de emissões: {e}")
        # Tenta arquivo local como último recurso
        return load_emissoes_from_raw()


def processar_serie_emissoes(dados: Dict) -> List[Dict]:
    """Processa série histórica de emissões"""
    serie = []
    
    emissoes = dados.get("emissoes", {})
    for ano, valor in emissoes.items():
        if valor and valor != "null":
            try:
                serie.append({
                    "Ano": int(ano),
                    "Valor": float(valor),
                    "Variavel": "EMISSOES_GEE"
                })
            except (ValueError, TypeError):
                continue
    
    return serie


def salvar_emissoes_no_banco(session: Session, dados: List[Dict]) -> None:
    """Salva dados de emissões no banco de dados."""
    for item in dados:
        existing = (
            session.query(Indicator)
            .filter_by(
                indicator_key="EMISSOES_GEE",
                source="SEEG",
                year=item["Ano"],
                municipality_code=str(COD_IBGE),
            )
            .first()
        )

        if existing:
            existing.value = item["Valor"]
            existing.collected_at = datetime.now()
        else:
            indicator = Indicator(
                indicator_key="EMISSOES_GEE",
                source="SEEG",
                year=item["Ano"],
                value=item["Valor"],
                municipality_code=str(COD_IBGE),
                municipality_name=MUNICIPIO,
                uf=UF,
                unit="tCO2e",
                collected_at=datetime.now(),
            )
            session.add(indicator)

    logger.info("Salvos %s registros de Emissões GEE", len(dados))


def run_etl_emissoes_gee():
    """Executa ETL completo para dados de Emissões GEE"""
    logger.info("Iniciando ETL para dados de Emissões GEE")

    with get_session() as session:
        try:
            logger.info("Extraindo dados de emissões GEE...")
            dados_emissoes = extrair_emissoes_municipais()
            if dados_emissoes:
                serie_emissoes = processar_serie_emissoes(dados_emissoes)
                if serie_emissoes:
                    salvar_emissoes_no_banco(session, serie_emissoes)
                else:
                    logger.warning("Nenhum dado de emissões encontrado")
            else:
                logger.error(
                    "Falha ao extrair dados de emissões. "
                    "Verifique: (1) API SEEG, (2) arquivo data/raw/emissoes_gee.csv"
                )

            logger.info("ETL para dados de Emissões GEE concluído com sucesso")
        except Exception as e:
            logger.error(f"Erro no ETL de Emissões GEE: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
    run_etl_emissoes_gee()
