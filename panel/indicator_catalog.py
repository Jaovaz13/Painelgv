"""
Catálogo de indicadores amigáveis para o painel.
Mapeia chaves técnicas para nomes compreensíveis e descrições.
"""

# Catálogo completo de indicadores com nomes amigáveis
CATALOGO_INDICADORES = {
    # Visão Geral
    "POPULACAO": {
        "nome": "População Total",
        "descricao": "População residente no município",
        "unidade": "Habitantes",
        "categoria": "Demografia"
    },
    "POPULACAO_DETALHADA": {
        "nome": "População Detalhada",
        "descricao": "Dados demográficos detalhados por grupo",
        "unidade": "Habitantes",
        "categoria": "Demografia"
    },
    "IDHM": {
        "nome": "IDH Municipal",
        "descricao": "Índice de Desenvolvimento Humano Municipal",
        "unidade": "Índice",
        "categoria": "Desenvolvimento"
    },
    "GINI": {
        "nome": "Índice de Gini",
        "descricao": "Medida de desigualdade de renda",
        "unidade": "Índice",
        "categoria": "Desenvolvimento"
    },
    
    # Economia
    "PIB_TOTAL": {
        "nome": "PIB Municipal",
        "descricao": "Produto Interno Bruto a preços correntes",
        "unidade": "R$ mil",
        "categoria": "Economia"
    },
    "PIB_PER_CAPITA": {
        "nome": "PIB per capita",
        "descricao": "PIB dividido pela população",
        "unidade": "R$",
        "categoria": "Economia"
    },
    "PIB_ESTIMADO": {
        "nome": "PIB Estimado",
        "descricao": "Projeção do PIB para anos recentes",
        "unidade": "R$ mil",
        "categoria": "Economia"
    },
    "RECEITA_VAF": {
        "nome": "Valor Adicionado Fiscal",
        "descricao": "Receita do VAF - Valor Adicionado Fiscal",
        "unidade": "R$",
        "categoria": "Finanças"
    },
    "RECEITA_ICMS": {
        "nome": "Cota-parte ICMS",
        "descricao": "Receita municipal de ICMS",
        "unidade": "R$",
        "categoria": "Finanças"
    },
    
    # Trabalho e Renda
    "EMPREGOS_RAIS": {
        "nome": "Empregos Formais (RAIS)",
        "descricao": "Número de empregos formais registrados na RAIS",
        "unidade": "Empregos",
        "categoria": "Trabalho"
    },
    "SALDO_CAGED_MENSAL": {
        "nome": "Saldo de Empregos (CAGED Mensal)",
        "descricao": "Saldo mensal de admissões e demissões",
        "unidade": "Vagas",
        "categoria": "Trabalho"
    },
    "SALDO_CAGED_ANUAL": {
        "nome": "Saldo de Empregos (CAGED Anual)",
        "descricao": "Saldo anual de admissões e demissões",
        "unidade": "Vagas",
        "categoria": "Trabalho"
    },
    "NUM_EMPRESAS": {
        "nome": "Número de Empresas",
        "descricao": "Quantidade de empresas estabelecidas",
        "unidade": "Empresas",
        "categoria": "Negócios"
    },
    "SEBRAE_GERAL": {
        "nome": "Indicadores SEBRAE",
        "descricao": "Dados de empreendedorismo e pequenos negócios",
        "unidade": "Unidades",
        "categoria": "Negócios"
    },
    "EMPRESAS_FORMAIS": {
        "nome": "Empresas Formais",
        "descricao": "Empresas formalmente constituídas",
        "unidade": "Empresas",
        "categoria": "Negócios"
    },
    
    # Educação
    "MATRICULAS_TOTAL": {
        "nome": "Matrículas Escolares",
        "descricao": "Total de matrículas na educação básica",
        "unidade": "Alunos",
        "categoria": "Educação"
    },
    "ESCOLAS_FUNDAMENTAL": {
        "nome": "Escolas de Ensino Fundamental",
        "descricao": "Número de escolas de ensino fundamental",
        "unidade": "Escolas",
        "categoria": "Educação"
    },
    "TAXA_APROVACAO_FUNDAMENTAL": {
        "nome": "Taxa de Aprovação - Fundamental",
        "descricao": "Percentual de alunos aprovados no ensino fundamental",
        "unidade": "%",
        "categoria": "Educação"
    },
    
    # Sustentabilidade
    "INDICE_SUSTENTABILIDADE": {
        "nome": "Índice de Sustentabilidade",
        "descricao": "Índice municipal de desenvolvimento sustentável",
        "unidade": "Índice",
        "categoria": "Sustentabilidade"
    },
    "EMISSOES_GEE": {
        "nome": "Emissões de GEE",
        "descricao": "Emissões de gases de efeito estufa",
        "unidade": "toneladas CO2",
        "categoria": "Meio Ambiente"
    },
    "SEEG_AR": {
        "nome": "Emissões - Agropecuária",
        "descricao": "Emissões do setor agropecuário",
        "unidade": "toneladas CO2",
        "categoria": "Meio Ambiente"
    },
    "SEEG_GASES": {
        "nome": "Emissões de Gases",
        "descricao": "Total de emissões de gases",
        "unidade": "toneladas CO2",
        "categoria": "Meio Ambiente"
    }
}

def get_indicator_info(indicator_key: str) -> dict:
    """
    Retorna informações amigáveis sobre um indicador.
    
    Args:
        indicator_key: Chave técnica do indicador
        
    Returns:
        Dicionário com nome, descrição, unidade e categoria
    """
    return CATALOGO_INDICADORES.get(indicator_key, {
        "nome": indicator_key,
        "descricao": "Indicador sem descrição detalhada",
        "unidade": "",
        "categoria": "Outros"
    })

def get_indicators_by_category(category: str) -> list:
    """
    Retorna todos os indicadores de uma categoria.
    
    Args:
        category: Nome da categoria
        
    Returns:
        Lista de chaves de indicadores da categoria
    """
    return [key for key, info in CATALOGO_INDICADORES.items() 
            if info["categoria"] == category]

def get_all_categories() -> list:
    """
    Retorna todas as categorias disponíveis.
    
    Returns:
        Lista de nomes de categorias
    """
    return list(set(info["categoria"] for info in CATALOGO_INDICADORES.values()))
