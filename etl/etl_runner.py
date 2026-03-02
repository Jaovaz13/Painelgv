import logging
import time

from database import init_db
from etl import (
    ibge, caged, datasus, snis, sefaz_mg, sustentabilidade,
    pnad, manual_sources, demograficos,
    caged_novo_manual, dados_manuais_extras, saude,
    sebrae, seeg, mapbiomas, esf, empregos,
    mei, salarios, sebrae_real, educacao_real
)
from etl import educacao_inep
import etl.demografia as demografia
import etl.negocios_sebrae as negocios_sebrae
import etl.sustentabilidade_idsc as sustentabilidade_idsc
import etl.pib_ibge as pib_ibge
import etl.pib_per_capita_ibge as pib_per_capita_ibge
import etl.vaf_sefaz as vaf_sefaz
import etl.icms_sefaz as icms_sefaz
import etl.empresas_rais as empresas_rais
import etl.emissoes_gee as emissoes_gee
import etl.caged_setores as caged_setores
import etl.saude_cnes as saude_cnes
from config import LOG_LEVEL, LOG_FORMAT

# Configuração básica de logging se rodar direto
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def run_all() -> None:
    """Executa todos os módulos de ETL sequencialmente."""
    start = time.time()
    logger.info("Iniciando carga completa de dados (ETL Runner).")
    
    init_db()
    
    modules = [
        ("IBGE", ibge),
        ("DEMOGRAFICOS", demograficos),
        ("DEMOGRAFIA_DETALHADA", demografia, "run"),
        ("CAGED_API", caged),
        ("CAGED_NOVO_MANUAL", caged_novo_manual),
        ("MANUAIS_EXTRAS", dados_manuais_extras),
        ("SAUDE_MANUAL", saude),
        ("DATASUS", datasus),
        ("SNIS", snis),
        ("SEFAZ_MG", sefaz_mg),
        ("IDSC", sustentabilidade),
        # EDUCAÇÃO: por política institucional, usar exclusivamente arquivos reais em data/raw
        ("EDUCACAO_INEP_RAW", educacao_inep),
        ("EDUCACAO_REAL_RAW", educacao_real),
        ("PNAD", pnad),
        ("MANUAIS_BASE", manual_sources),
        ("SEBRAE", sebrae),
        ("NEGOCIOS_SEBRAE", negocios_sebrae, "run"),
        ("SEEG", seeg),
        ("MAPBIOMAS", mapbiomas),
        ("SUSTENTABILIDADE_IDSC", sustentabilidade_idsc, "run"),
        ("PIB_IBGE", pib_ibge, "run_etl_pib_ibge"),
        ("PIB_PER_CAPITA", pib_per_capita_ibge, "run"),
        ("VAF_SEFAZ", vaf_sefaz, "run_etl_vaf_sefaz"),
        ("ICMS_SEFAZ", icms_sefaz, "run_etl_icms_sefaz"),
        ("EMPRESAS_RAIS", empresas_rais, "run_etl_empresas_rais"),
        ("EMISSOES_GEE", emissoes_gee, "run_etl_emissoes_gee"),
        ("CAGED_SETORES", caged_setores, "run"),
        ("SAUDE_CNES", saude_cnes, "run"),
        ("ESF", esf),
        ("EMPREGOS", empregos),
        ("MEI", mei),
        ("SALARIOS", salarios),
        ("SEBRAE_REAL", sebrae_real)
    ]

    for entry in modules:
        # Suporta tanto (name, module) quanto (name, module, func_name)
        if len(entry) == 2:
            name, module = entry
            func_name = "run"
        else:
            name, module, func_name = entry
        try:
            logger.info(f"--- Executando ETL {name} ---")
            func = getattr(module, func_name)
            func()
        except AttributeError:
            logger.error("Módulo %s não possui função '%s'", name, func_name)
        except Exception as e:
            logger.exception(f"Falha no módulo {name}: {e}")

    elapsed = time.time() - start
    logger.info("Carga completa finalizada em %.2f segundos.", elapsed)

if __name__ == "__main__":
    run_all()
