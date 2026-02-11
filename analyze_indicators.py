from database import list_indicators
import pandas as pd

# Listar todos os indicadores disponíveis
indicators = list_indicators()
print(f'Total de indicadores: {len(indicators)}')
print('\nIndicadores disponíveis:')

for ind in sorted(indicators, key=lambda x: x['indicator_key']):
    print(f'- {ind["indicator_key"]} (fonte: {ind["source"]})')

# Verificar dados por categoria
print('\n' + '='*50)
print('ANÁLISE POR CATEGORIA')
print('='*50)

# Agrupar por categoria
categories = {}
for ind in indicators:
    key = ind["indicator_key"]
    
    # Identificar categoria baseada na chave
    if any(x in key.upper() for x in ['PIB', 'ECONOMIA', 'INDUSTRIA', 'SERVICOS', 'AGRO']):
        cat = 'Economia'
    elif any(x in key.upper() for x in ['EMPREGO', 'CAGED', 'RAIS', 'TRABALHO', 'SALARIO']):
        cat = 'Trabalho e Renda'
    elif any(x in key.upper() for x in ['IDEB', 'EDUCACAO', 'ESCOLA', 'MATRICULA']):
        cat = 'Educação'
    elif any(x in key.upper() for x in ['SAUDE', 'MORTALIDADE', 'ESF', 'LEITO']):
        cat = 'Saúde'
    elif any(x in key.upper() for x in ['IDSC', 'SUSTENTABILIDADE', 'AMBIENTAL']):
        cat = 'Sustentabilidade'
    elif any(x in key.upper() for x in ['POPULACAO', 'DEMOGRAFIA']):
        cat = 'Demografia'
    else:
        cat = 'Outros'
    
    if cat not in categories:
        categories[cat] = []
    categories[cat].append(ind)

# Exibir por categoria
for cat, inds in categories.items():
    print(f'\n{cat.upper()} ({len(inds)} indicadores):')
    for ind in sorted(inds, key=lambda x: x['indicator_key']):
        print(f'  - {ind["indicator_key"]} (fonte: {ind["source"]})')

# Salvar análise em arquivo
print('\n' + '='*50)
print('SALVANDO ANÁLISE COMPLETA...')
print('='*50)

# Criar DataFrame completo
df_indicators = pd.DataFrame(indicators)
df_indicators.to_csv('c:/painel_gv/data/analysis_indicators_disponiveis.csv', index=False, encoding='utf-8')
print('Análise salva em: c:/painel_gv/data/analysis_indicators_disponiveis.csv')

# Comparar com mapeamento do painel
print('\n' + '='*50)
print('COMPARAÇÃO COM PAINEL.PY')
print('='*50)

# Mapeamento atual do painel (baseado no código)
painel_mapping = {
    "Visão Geral": ["POPULACAO", "POPULACAO_DETALHADA", "IDHM", "GINI"],
    "Economia": ["PIB_TOTAL", "PIB_PER_CAPITA", "PIB_CRESCIMENTO", "RECEITA_VAF", "RECEITA_ICMS", "PIB_ESTIMADO"],
    "Trabalho & Renda": ["EMPREGOS_CAGED", "EMPREGOS_RAIS", "SALDO_CAGED", "EMPREENDEDORES_MEI", "SALARIO_MEDIO_MG", "SALDO_CAGED_MENSAL", "SALDO_CAGED_ANUAL"],
    "Educação": ["MATRICULAS_TOTAL", "IDEB_ANOS_INICIAIS", "IDEB_ANOS_FINAIS"],
    "Saúde": ["OBITOS_TOTAL", "MORTALIDADE_INFANTIL"],
    "Sustentabilidade": ["IDSC_GERAL", "EMISSOES_GEE", "AREA_URBANA", "VEGETACAO_NATIVA", "USO_AGROPECUARIO"],
    "Negócios": ["EMPRESAS_ATIVAS", "EMPREGOS_SEBRAE", "ESTABELECIMENTOS_SEBRAE"],
}

# Verificar quais indicadores do painel existem no banco
painel_keys = []
for section_keys in painel_mapping.values():
    painel_keys.extend(section_keys)

available_keys = [ind["indicator_key"] for ind in indicators]

print(f'Indicadores no painel.py: {len(painel_keys)}')
print(f'Indicadores no banco: {len(available_keys)}')

# Indicadores do painel que não existem no banco
missing_in_db = [key for key in painel_keys if key not in available_keys]
print(f'\n❌ Indicadores do painel que NÃO existem no banco ({len(missing_in_db)}):')
for key in missing_in_db:
    print(f'  - {key}')

# Indicadores no banco que não estão no painel
missing_in_painel = [key for key in available_keys if key not in painel_keys]
print(f'\n✅ Indicadores no banco que NÃO estão no painel ({len(missing_in_painel)}):')
for key in sorted(missing_in_painel):
    print(f'  - {key}')

print('\n' + '='*50)
print('ANÁLISE CONCLUÍDA')
print('='*50)
