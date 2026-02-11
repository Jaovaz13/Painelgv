import pandas as pd
import logging
from datetime import datetime
from statsmodels.tsa.holtwinters import ExponentialSmoothing
try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False

from database import get_timeseries, upsert_indicators

logger = logging.getLogger(__name__)

def estimar_pib_hibrido(ano_target: int) -> float:
    """
    Calcula PIB Híbrido com pesos institucionais:
    PIB Est = 0.45*IBGE(Last) + 0.25*VAF + 0.20*Massa
    
    Nota: Esta fórmula assume que as variáveis estão na mesma magnitude (R$) ou 
    que usamos a variação delas aplicada ao PIB base.
    Como simplificação robusta para este MVP, vamos calcular a variação média ponderada
    desses indicadores e aplicar ao último PIB oficial.
    """
    # 1. Obter PIB Base (Último Oficial)
    df_pib = get_timeseries("PIB_TOTAL", source="IBGE").sort_values("Ano")
    if df_pib.empty: return 0.0
    
    last_pib_val = df_pib.iloc[-1]["Valor"]
    last_pib_year = int(df_pib.iloc[-1]["Ano"])
    
    # Se já temos oficial para o ano target, retorna ele
    if df_pib[df_pib["Ano"] == ano_target].shape[0] > 0:
        return df_pib[df_pib["Ano"] == ano_target]["Valor"].iloc[0]

    # Só projetamos 1 ano à frente com essa fórmula híbrida direta (ou recursiva para mais)
    if ano_target > last_pib_year + 1:
        # Fallback para Holt-Winters para anos distantes
        return 0.0 

    # 2. Obter proxies para o ano target
    # Precisamos das variações em relação ao ano anterior (last_pib_year)
    
    def get_variation(key, source):
        df = get_timeseries(key, source)
        if df.empty: return 0.0
        v_curr = df[df["Ano"] == ano_target]["Valor"]
        v_prev = df[df["Ano"] == last_pib_year]["Valor"]
        
        if not v_curr.empty and not v_prev.empty:
            val_c = v_curr.iloc[0]
            val_p = v_prev.iloc[0]
            if val_p != 0:
                return (val_c - val_p) / val_p
        return 0.0 # Sem variação conhecida (neutro)

    var_vaf = get_variation("RECEITA_VAF", "SEFAZ_MG") 
    var_massa = get_variation("EMPREGOS_CAGED", "CAGED_MANUAL_XLSX") # Proxy Empregos

    # Pesos na variação (assumindo que o PIB segue a composição dessas variações)
    # A fórmula original (0.45 PIB + ...) sugere composição de valor.
    # Mas como PIB >> proxies, somar direto daria errado sem normalizar.
    # Interpretação técnica: Variação do PIB Estimado =
    # 0.25*Var(VAF) + 0.20*Var(Massa) + 0.45*TendenciaIBGE?
    # Vamos simplificar: Aplicar a média ponderada das variações das proxies disponíveis.
    
    # Pesos relativos das proxies (soma 0.55 do que não é inercia IBGE)
    # Se usarmos variação, aplicamos ao total.
    
    w_vaf = 0.25
    w_massa = 0.20
    w_total = w_vaf + w_massa
    
    weighted_var = (var_vaf * w_vaf + var_massa * w_massa) / w_total if w_total > 0 else 0
    
    # Se todas proxies zeradas (sem dados), assumimos crescimento inercial leve ou zero
    pib_estimado = last_pib_val * (1 + weighted_var)
    
    return pib_estimado
    
def estimar_pib_prophet(anos_frente: int = 3) -> pd.DataFrame:
    """
    Realiza a estimativa do PIB usando Facebook Prophet.
    """
    if not HAS_PROPHET:
        logger.warning("Prophet não instalado. Use Holt-Winters.")
        return pd.DataFrame()

    df_hist = get_timeseries("PIB_TOTAL", source="IBGE")
    if df_hist.empty or len(df_hist) < 4:
        return pd.DataFrame()

    # Preparar dados para o Prophet (colunas ds e y)
    df_p = df_hist.sort_values("Ano").copy()
    df_p["ds"] = pd.to_datetime(df_p["Ano"].astype(str) + "-01-01")
    df_p["y"] = df_p["Valor"]

    try:
        model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
        model.fit(df_p[["ds", "y"]])
        
        future = model.make_future_dataframe(periods=anos_frente, freq='YS')
        forecast = model.predict(future)
        
        # Filtrar apenas o futuro
        forecast_future = forecast[forecast['ds'] > df_p['ds'].max()]
        
        res = []
        for _, row in forecast_future.iterrows():
            res.append({
                "Ano": row["ds"].year,
                "Valor": row["yhat"],
                "Tipo": "Estimado (Prophet)",
                "Lower": row["yhat_lower"],
                "Upper": row["yhat_upper"],
                "Unidade": "R$ mil"
            })
        return pd.DataFrame(res)
    except Exception as e:
        logger.error(f"Erro no Prophet: {e}")
        return pd.DataFrame()

def estimar_pib(anos_frente: int = 3, method: str = "auto") -> pd.DataFrame:
    """
    Realiza a estimativa do PIB. 
    Usa o modelo HÍBRIDO para o ano t+1 (se houver proxies) e 
    Prophet/Holt-Winters para a série completa.
    """
    # 1. Obter a projeção base (Série Temporal)
    df_base = pd.DataFrame()
    if (method == "auto" or method == "prophet") and HAS_PROPHET:
        df_base = estimar_pib_prophet(anos_frente)
    
    if df_base.empty:
        df_base = estimar_pib_hw(anos_frente) # Renomeado o corpo de Holt-Winters para função interna se necessário, ou mantido aqui
    
    if df_base.empty:
        return pd.DataFrame()

    # 2. Refinar o primeiro ano com o modelo HÍBRIDO (VAF, ISS, etc.)
    df_hist = get_timeseries("PIB_TOTAL", source="IBGE").sort_values("Ano")
    if not df_hist.empty:
        prox_ano = int(df_hist.iloc[-1]["Ano"]) + 1
        val_hibrido = estimar_pib_hibrido(prox_ano)
        
        if val_hibrido > 0:
            # Substituir o valor do primeiro ano projetado pelo valor híbrido
            mask = df_base["Ano"] == prox_ano
            if mask.any():
                df_base.loc[mask, "Valor"] = val_hibrido
                df_base.loc[mask, "Tipo"] += " + Refinamento Híbrido"

    return df_base

def estimar_pib_hw(anos_frente: int = 3) -> pd.DataFrame:
    """Corpo original do Holt-Winters extraído para organização."""
    df_hist = get_timeseries("PIB_TOTAL", source="IBGE")
    if df_hist.empty or len(df_hist) < 4:
        logger.warning("Dados insuficientes para estimativa do PIB.")
        return pd.DataFrame()

    df_hist = df_hist.sort_values("Ano")
    y = df_hist["Valor"].values
    ultimo_ano = df_hist["Ano"].values[-1]

    try:
        modelo = ExponentialSmoothing(
            y, trend="add", damped_trend=True, seasonal=None, 
            initialization_method="estimated"
        ).fit()
        predicao = modelo.forecast(anos_frente)
        
        novos_anos = [ultimo_ano + i + 1 for i in range(anos_frente)]
        res = []
        for ano, val in zip(novos_anos, predicao):
            res.append({
                "Ano": int(ano),
                "Valor": val,
                "Tipo": "Estimado (HW)",
                "Lower": val * 0.95, # Simplificação para o fallback
                "Upper": val * 1.05,
                "Unidade": "R$ mil"
            })
        return pd.DataFrame(res)
    except Exception as e:
        logger.warning(f"Falha no Holt-Winters: {e}")
        return pd.DataFrame()

def salvar_estimativa():
    """
    Gera a estimativa e salva no banco de dados como indicador 'PIB_ESTIMADO'.
    """
    logger.info("Iniciando estimativa do PIB...")
    df_prev = estimar_pib()
    
    if df_prev.empty:
        logger.warning("Nenhuma estimativa gerada.")
        return

    # Preparar para upsert
    df_save = df_prev[["Ano", "Valor", "Unidade", "Tipo"]].rename(columns={
        "Ano": "year", 
        "Valor": "value",
        "Unidade": "unit",
        "Tipo": "category"
    })
    
    upsert_indicators(
        df_save,
        indicator_key="PIB_ESTIMADO",
        source="PROJECAO_INTERNA"
    )
    logger.info("Estimativa de PIB salva com sucesso.")

def get_estimativa_stored():
    """Recupera a estimativa salva no banco."""
    return get_timeseries("PIB_ESTIMADO", source="PROJECAO_INTERNA")
