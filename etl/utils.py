import pandas as pd
from datetime import date

def padronizar(df, indicador, categoria, municipio, uf, fonte, manual):
    """
    Padroniza um DataFrame para o formato esperado pelo banco de dados.
    Recebe um DF com colunas ['ano', 'valor'] (e opcionalmente 'mes').
    """
    df = df.copy()
    df["indicator_key"] = indicador
    df["category"] = categoria
    df["municipality_name"] = municipio
    df["uf"] = uf
    df["source"] = fonte
    df["manual"] = manual
    df["collected_at"] = date.today()
    
    # Garantir nomes de colunas esperados pelo upsert_indicators
    # upsert_indicators espera ["year", "value", "unit"]
    # Mas o usuário sugeriu retornar o schema com indicador, categoria, valor, ano, mes...
    # Vamos adaptar para que o DF final tenha o que o upsert_indicators precisa E o que o usuário quer.
    
    if "year" not in df.columns and "ano" in df.columns:
        df = df.rename(columns={"ano": "year"})
    if "value" not in df.columns and "valor" in df.columns:
        df = df.rename(columns={"valor": "value"})
    if "month" not in df.columns and "mes" in df.columns:
        df = df.rename(columns={"mes": "month"})
    
    if "month" not in df.columns:
        df["month"] = 0
    
    # Preencher unidade se não houver
    if "unit" not in df.columns:
        df["unit"] = None
        
    return df
def calcular_variacao(df):
    """
    Calcula a variação percentual ano a ano.
    df deve ter colunas 'year' e 'value' ordenadas por ano.
    """
    df = df.sort_values("year")
    df["variacao"] = df["value"].pct_change() * 100
    return df

def calcular_per_capita(df, df_pop):
    """
    Calcula valor per capita.
    df e df_pop devem ter coluna 'year'.
    """
    merged = pd.merge(df, df_pop[["year", "value"]], on="year", suffixes=("", "_pop"))
    merged["per_capita"] = merged["value"] / merged["value_pop"]
    return merged
