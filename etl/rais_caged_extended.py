import pandas as pd
import logging
from database import upsert_indicators, get_timeseries

logger = logging.getLogger(__name__)

def run():
    """
    Calcula a Massa Salarial Estimada (Proxy) baseada no Estoque de Empregos (CAGED)
    e no Salário Médio (RAIS/CAGED).
    
    Fórmula: Massa = Estoque de Empregos * Salário Médio
    """
    logger.info("Iniciando cálculo de Massa Salarial (Proxy)...")
    
    # 1. Obter Estoque de Empregos (Preferência: Novo Caged, Fallback: Rais)
    df_empregos = get_timeseries("EMPREGOS_CAGED", "CAGED_NOVO")
    if df_empregos.empty:
        df_empregos = get_timeseries("EMPREGOS_RAIS", "RAIS")
        
    # 2. Obter Salário Médio
    df_salario = get_timeseries("SALARIO_MEDIO_MG") # Proxy Regional
    if df_salario.empty:
        df_salario = get_timeseries("SALARIO_MEDIO_REAL") # Dados locais se houver
        
    if df_empregos.empty or df_salario.empty:
        logger.warning("Dados insuficientes para calcular Massa Salarial.")
        return

    # Merge por Ano
    df_merged = pd.merge(
        df_empregos[["Ano", "Valor"]], 
        df_salario[["Ano", "Valor"]], 
        on="Ano", 
        suffixes=("_emp", "_sal")
    )
    
    if df_merged.empty:
        return

    # Cálculo da Massa Anual (R$ Milhões)
    # Massa Mensal = Emp * Sal
    # Massa Anual = Massa Mensal * 13.3 (inclui 13º e ferias aprox) ou puramente * 12
    # Adotando * 13 para simplicidade/conservadorismo
    df_merged["Valor"] = (df_merged["Valor_emp"] * df_merged["Valor_sal"] * 13)
    df_merged["unit"] = "R$"
    
    # Upsert
    upsert_indicators(
        df_merged[["Ano", "Valor", "unit"]],
        indicator_key="MASSA_SALARIAL_ESTIMADA",
        source="CAGED_ESTIMADO",
        category="Economia",
        manual=False
    )
    logger.info("Massa Salarial calculada e salva com sucesso.")

if __name__ == "__main__":
    run()
