import pandas as pd

def calcular_cagr(inicio: float, fim: float, anos: int) -> float:
    """Calcula a Taxa de Crescimento Anual Composta (CAGR)."""
    if inicio <= 0 or anos <= 0:
        return 0.0
    return (fim / inicio) ** (1 / anos) - 1

class TendenciaResult:
    def __init__(self, resumo: str, tendencia_texto: str):
        self.resumo = resumo
        self.tendencia_texto = tendencia_texto
    
    def __str__(self):
        return self.tendencia_texto

def analisar_tendencia(
    df: pd.DataFrame, 
    coluna_valor: str = "Valor", 
    coluna_ano: str = "Ano",
    ano_inicio: int = None,
    ano_fim: int = None,
    *,
    text_format: str = "markdown",
    unidade: str | None = None,
) -> TendenciaResult:
    """
    Gera um objeto com resumo e texto detalhado sobre a tendência da série temporal.
    """
    if df.empty:
        msg = "Dados insuficientes para análise de tendência."
        return TendenciaResult(msg, msg)

    df = df.sort_values(by=coluna_ano)
    
    if ano_inicio:
        df = df[df[coluna_ano] >= ano_inicio]
    if ano_fim:
        df = df[df[coluna_ano] <= ano_fim]

    if len(df) < 2:
        msg = "Dados insuficientes no período selecionado para análise."
        return TendenciaResult(msg, msg)

    primeiro_ano = df[coluna_ano].min()
    ultimo_ano = df[coluna_ano].max()
    
    val_inicio = df.loc[df[coluna_ano] == primeiro_ano, coluna_valor].iloc[0]
    val_fim = df.loc[df[coluna_ano] == ultimo_ano, coluna_valor].iloc[0]
    
    delta_anos = ultimo_ano - primeiro_ano
    cagr = calcular_cagr(val_inicio, val_fim, delta_anos)
    percent_total = ((val_fim - val_inicio) / val_inicio) * 100 if val_inicio != 0 else 0
    
    tendencia = "estável"
    if cagr > 0.05: tendencia = "crescimento forte"
    elif cagr > 0.01: tendencia = "crescimento moderado"
    elif cagr < -0.05: tendencia = "queda acentuada"
    elif cagr < -0.01: tendencia = "queda moderada"
    
    resumo = f"{tendencia.capitalize()} ({percent_total:+.1f}%)"
    
    val_ini_fmt = f"{val_inicio:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    val_fim_fmt = f"{val_fim:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    unit_suffix = f" {unidade}" if unidade else ""
    if text_format not in {"markdown", "plain"}:
        text_format = "markdown"

    if text_format == "plain":
        texto = (
            f"No período de {primeiro_ano} a {ultimo_ano}, o indicador apresentou {tendencia}. "
            f"A variação total foi de {percent_total:+.1f}%, com uma taxa anual média (CAGR) de {cagr:1.1%}. "
            f"O valor saiu de {val_ini_fmt}{unit_suffix} para {val_fim_fmt}{unit_suffix}."
        )
    else:
        texto = (
            f"No período de {primeiro_ano} a {ultimo_ano}, o indicador apresentou **{tendencia}**. "
            f"A variação total foi de **{percent_total:+.1f}%**, com uma taxa anual média (CAGR) de **{cagr:1.1%}**. "
            f"O valor saiu de {val_ini_fmt}{unit_suffix} para {val_fim_fmt}{unit_suffix}."
        )
    
    return TendenciaResult(resumo, texto)
