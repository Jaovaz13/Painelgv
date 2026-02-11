"""
Texto de metodologia para inclusão no relatório PDF.
Fontes dos dados, definições e periodicidade.
"""
METODOLOGIA_TITULO = "Metodologia"
METODOLOGIA_TEXTO = """
A estimativa do Produto Interno Bruto Municipal foi elaborada a partir de metodologia híbrida, combinando o último dado oficial publicado pelo IBGE com proxies econômicos atualizados, tais como Valor Adicionado Fiscal (SEFAZ-MG) e Massa Salarial (RAIS/CAGED). A projeção foi realizada por meio de modelos de séries temporais, garantindo coerência estatística e aderência à dinâmica econômica local.

Fontes complementares:
• IBGE/SIDRA: PIB e PNAD (Proxy Desemprego).
• Manual/CSV/XLSX: SEBRAE (Empresas), MAPBIOMAS (Uso do Solo), SEEG (Emissões), Novo CAGED (Dez/2025) e RAIS (2024).
• CAGED/RAIS: Mercado de Trabalho e Massa Salarial.
"""


def get_metodologia_paragraphs() -> list[str]:
    """Retorna lista de parágrafos de metodologia para o PDF."""
    return [METODOLOGIA_TITULO, METODOLOGIA_TEXTO.strip()]
