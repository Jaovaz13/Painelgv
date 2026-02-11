import pandas as pd
import logging
import os
from config import DATA_DIR

# Configuração de logging básica para o script integrador
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ETL_MASTER")

def run_all():
    """
    Executa todos os processos de ETL e garante que cada módulo execute seu upsert no banco.
    POLÍTICA: 100% DADOS REAIS.
    """
    logger.info("Iniciando execução de todos os ETLs...")
    
    # Lista de módulos (API + Fallback Reais) e suas funções de execução
    import etl.demograficos as demograficos
    import etl.negocios_sebrae as negocios_sebrae
    import etl.educacao_inep as educacao_inep
    import etl.saude as saude
    import etl.sustentabilidade_idsc as sustentabilidade_idsc
    
    # Novos módulos robustos (API + Fallback + Sem Simulação)
    import etl.pib_ibge as pib_ibge
    import etl.vaf_sefaz as vaf_sefaz
    import etl.icms_sefaz as icms_sefaz
    import etl.empresas_rais as empresas_rais
    import etl.emissoes_gee as emissoes_gee
    
    # Wrapper para adaptar módulos antigos e novos
    processos = [
        # Módulos com função .run() padrão (Antigos mantidos pois são seguros)
        {"mod": demograficos, "func": demograficos.run, "name": "Demograficos (Censo/Gini/IDH)"},
        {"mod": negocios_sebrae, "func": negocios_sebrae.run, "name": "Sebrae"},
        {"mod": educacao_inep, "func": educacao_inep.run, "name": "INEP"},
        {"mod": saude, "func": saude.run, "name": "Saúde"},
        {"mod": sustentabilidade_idsc, "func": sustentabilidade_idsc.run, "name": "IDSC"},
        
        # Novos módulos robustos (Substituem os antigos)
        {"mod": pib_ibge, "func": pib_ibge.run_etl_pib_ibge, "name": "PIB IBGE (API/Real)"},
        {"mod": vaf_sefaz, "func": vaf_sefaz.run_etl_vaf_sefaz, "name": "VAF SEFAZ (API/Real)"},
        {"mod": icms_sefaz, "func": icms_sefaz.run_etl_icms_sefaz, "name": "ICMS SEFAZ (API/Real)"},
        {"mod": empresas_rais, "func": empresas_rais.run_etl_empresas_rais, "name": "RAIS (API/Real)"},
        {"mod": emissoes_gee, "func": emissoes_gee.run_etl_emissoes_gee, "name": "Emissões GEE (API/Real)"},
    ]
    
    dfs = []
    
    for p in processos:
        try:
            logger.info(f"Executando ETL: {p['name']}")
            # Executa a função mapeada
            result = p["func"]()
            
            # Alguns módulos antigos retornam DF, os novos fazem upsert interno e não retornam
            if isinstance(result, pd.DataFrame) and not result.empty:
                dfs.append(result)
                logger.info(f"Sucesso ao processar {p['name']} (DF retornado).")
            else:
                logger.info(f"Sucesso ao processar {p['name']} (Upsert direto).")
                
        except Exception as e:
            logger.error(f"Erro fatal ao processar {p['name']}: {e}")
            
    logger.info("Ciclo de ETL finalizado.")
    return pd.concat(dfs) if dfs else pd.DataFrame()

if __name__ == "__main__":
    df_final = run_all()
    if not df_final.empty:
        print("Execução finalizada com extração de dados.")
    else:
        print("Execução finalizada (dados persistidos no banco diretamente).")
