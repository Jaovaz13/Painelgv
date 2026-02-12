import pandas as pd
import logging
import sys
import os

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import upsert_indicators, get_timeseries

logger = logging.getLogger(__name__)

def run():
    """
    Calcula a Massa Salarial Estimada (Proxy) baseada no Estoque de Empregos (CAGED)
    e no Salário Médio (RAIS/CAGED).
    
    Fórmula: Massa = Estoque de Empregos * Salário Médio
    """
    logger.info("Iniciando cálculo de Massa Salarial (Proxy)...")
    
    # 1. Obter Estoque de Empregos
    # Tentar CAGED Novo primeiro (ideal)
    df_empregos = get_timeseries("EMPREGOS_CAGED", "CAGED_NOVO")
    
    # Se vazio ou muito curto, tentar outras fontes de emprego
    if df_empregos.empty or len(df_empregos) < 2:
        # Tentar RAIS (qualquer fonte)
        df_rais = get_timeseries("EMPREGOS_RAIS") 
        if not df_rais.empty:
            df_empregos = df_rais
        else:
             # Última tentativa: CAGED (qualquer fonte)
             df_caged_any = get_timeseries("EMPREGOS_CAGED")
             if not df_caged_any.empty:
                 df_empregos = df_caged_any

    # 2. Obter Salário Médio
    # Tentar Salário Médio Real (dados locais)
    df_salario = get_timeseries("SALARIO_MEDIO_REAL")
    
    # Se vazio, usar Proxy Regional (Salário Médio MG)
    if df_salario.empty:
        df_salario = get_timeseries("SALARIO_MEDIO_MG")
        
    if df_empregos.empty or df_salario.empty:
        logger.warning("Dados insuficientes para calcular Massa Salarial.")
        return

    # Agregar por Ano (Média) para garantir unicidade
    df_emp_agg = df_empregos.groupby("Ano")["Valor"].mean().reset_index()
    df_sal_agg = df_salario.groupby("Ano")["Valor"].mean().reset_index()

    # Merge por Ano
    df_merged = pd.merge(
        df_emp_agg, 
        df_sal_agg, 
        on="Ano", 
        suffixes=("_emp", "_sal")
    )
    
    if df_merged.empty:
        return

    # Cálculo da Massa Anual (R$ Milhões)
    # Massa Mensal = Emp * Sal
    # Massa Anual = Massa Mensal * 13 (inclui 13º aprox)
    df_merged["Valor"] = (df_merged["Valor_emp"] * df_merged["Valor_sal"] * 13)
    df_merged["unit"] = "R$"
    
    # Renomear colunas para o padrão do banco
    df_save = df_merged[["Ano", "Valor", "unit"]].rename(columns={"Ano": "year", "Valor": "value"})
    
    # Upsert
    upsert_indicators(
        df_save,
        indicator_key="MASSA_SALARIAL_ESTIMADA",
        source="CAGED_ESTIMADO",
        category="Economia"
    )
    logger.info("Massa Salarial calculada e salva com sucesso.")

if __name__ == "__main__":
    run()
