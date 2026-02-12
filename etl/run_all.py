import pandas as pd
import logging
import time
from datetime import datetime
from typing import Dict, List, Any

# Configuração de logging centralizada
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ETL_MASTER")

def run_all() -> Dict[str, Any]:
    """
    Executa todos os processos de ETL de forma padronizada.
    
    POLÍTICA: 100% DADOS REAIS.
    Retorna um relatório de execução dos módulos.
    """
    start_time = time.time()
    logger.info("🚀 Iniciando Ciclo Completo de Automação de Dados (ETL)")
    
    # Importações Lazy para evitar carregamento desnecessário se não for rodar
    import etl.demograficos as demograficos
    import etl.negocios_sebrae as negocios_sebrae
    import etl.educacao_inep as educacao_inep
    import etl.saude as saude
    import etl.sustentabilidade_idsc as sustentabilidade_idsc
    import etl.pib_ibge as pib_ibge
    import etl.pib_per_capita_ibge as pib_per_capita_ibge
    import etl.vaf_sefaz as vaf_sefaz
    import etl.icms_sefaz as icms_sefaz
    import etl.empresas_rais as empresas_rais
    import etl.emissoes_gee as emissoes_gee
    
    # Mapeamento de módulos para execução padronizada
    # Alguns usam .run(), outros usam .run_etl_...
    processos = [
        {"mod": demograficos, "func": demograficos.run, "name": "Demograficos (População/IDH/Gini)"},
        {"mod": negocios_sebrae, "func": negocios_sebrae.run, "name": "Sebrae (Empresas/Empregos)"},
        {"mod": educacao_inep, "func": educacao_inep.run, "name": "INEP (Educação)"},
        {"mod": saude, "func": saude.run, "name": "Saúde (Mortalidade)"},
        {"mod": sustentabilidade_idsc, "func": sustentabilidade_idsc.run, "name": "IDSC (Sustentabilidade)"},
        {"mod": pib_ibge, "func": pib_ibge.run_etl_pib_ibge, "name": "PIB IBGE"},
        {"mod": pib_per_capita_ibge, "func": pib_per_capita_ibge.run, "name": "PIB per Capita IBGE"},
        {"mod": vaf_sefaz, "func": vaf_sefaz.run_etl_vaf_sefaz, "name": "VAF SEFAZ"},
        {"mod": icms_sefaz, "func": icms_sefaz.run_etl_icms_sefaz, "name": "ICMS SEFAZ"},
        {"mod": empresas_rais, "func": empresas_rais.run_etl_empresas_rais, "name": "Empresas/Vínculos RAIS"},
        {"mod": emissoes_gee, "func": emissoes_gee.run_etl_emissoes_gee, "name": "Emissões GEE (SEEG)"},
    ]
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_modules": len(processos),
        "success_count": 0,
        "failure_count": 0,
        "details": [],
        "execution_time_seconds": 0
    }
    
    for p in processos:
        mod_start = time.time()
        mod_status = {"name": p["name"], "status": "success", "error": None, "duration": 0}
        
        try:
            logger.info(f"⏳ Processando: {p['name']}...")
            p["func"]()
            report["success_count"] += 1
        except Exception as e:
            logger.error(f"❌ Erro em {p['name']}: {e}")
            mod_status["status"] = "failed"
            mod_status["error"] = str(e)
            report["failure_count"] += 1
        
        mod_status["duration"] = round(time.time() - mod_start, 2)
        report["details"].append(mod_status)
        
    report["execution_time_seconds"] = round(time.time() - start_time, 2)
    logger.info(f"🏁 Ciclo Finalizado. Sucessos: {report['success_count']}, Falhas: {report['failure_count']}")
    
    return report

if __name__ == "__main__":
    rep = run_all()
    print("\n--- RELATÓRIO DE EXECUÇÃO ETL ---")
    print(f"Duração Total: {rep['execution_time_seconds']}s")
    for d in rep["details"]:
        status_icon = "✅" if d["status"] == "success" else "❌"
        print(f"{status_icon} {d['name']}: {d['status']} ({d['duration']}s)")
