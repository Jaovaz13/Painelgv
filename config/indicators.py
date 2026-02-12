"""
Catálogo oficial de indicadores do projeto Painel GV.
Centraliza metadados sobre fontes, periodicidade e métodos de coleta.
"""

CATALOGO_INDICADORES = {
    "POPULACAO": {
        "nome": "População Estimada",
        "fonte": "IBGE",
        "api": True,
        "categoria": "Demografia",
        "unidade": "Habitantes"
    },
    "POPULACAO_DETALHADA": {
        "nome": "População por Faixa Etária e Sexo",
        "fonte": "IBGE/SIDRA",
        "api": True,
        "categoria": "Demografia",
        "unidade": "Habitantes"
    },
    "PIB_TOTAL": {
        "nome": "PIB Municipal",
        "fonte": "IBGE",
        "api": True,
        "categoria": "Economia",
        "unidade": "R$ mil"
    },
    "PIB_AGROPECUARIA": {
        "nome": "PIB Agropecuária",
        "fonte": "IBGE",
        "api": True,
        "categoria": "Economia",
        "unidade": "R$ mil"
    },
    "PIB_INDUSTRIA": {
        "nome": "PIB Indústria",
        "fonte": "IBGE",
        "api": True,
        "categoria": "Economia",
        "unidade": "R$ mil"
    },
    "PIB_SERVICOS": {
        "nome": "PIB Serviços",
        "fonte": "IBGE",
        "api": True,
        "categoria": "Economia",
        "unidade": "R$ mil"
    },
    "PIB_ADM_PUBLICA": {
        "nome": "PIB Administração Pública",
        "fonte": "IBGE",
        "api": True,
        "categoria": "Economia",
        "unidade": "R$ mil"
    },
    "EMPREGOS_RAIS": {
        "nome": "Empregos Formais (Estoque)",
        "fonte": "RAIS",
        "api": False,
        "categoria": "Trabalho e Renda",
        "unidade": "Vínculos"
    },
    "EMPRESAS_ATIVAS": {
        "nome": "Empresas Ativas",
        "fonte": "Sebrae",
        "api": False,
        "categoria": "Negócios",
        "unidade": "Empresas"
    },
    "EMPREGOS_SEBRAE": {
        "nome": "Empregados (Sebrae)",
        "fonte": "Sebrae",
        "api": False,
        "categoria": "Negócios",
        "unidade": "Trabalhadores"
    },
    "ESTABELECIMENTOS_SEBRAE": {
        "nome": "Estabelecimentos (Sebrae)",
        "fonte": "Sebrae",
        "api": False,
        "categoria": "Negócios",
        "unidade": "Estabelecimentos"
    },
    "MATRICULAS_TOTAL": {
        "nome": "Matrículas Escolares",
        "fonte": "INEP",
        "api": False,
        "categoria": "Educação",
        "unidade": "Matrículas"
    },
    "MORTALIDADE_INFANTIL": {
        "nome": "Mortalidade Infantil",
        "fonte": "DataSUS",
        "api": False,
        "categoria": "Saúde",
        "unidade": "Óbitos"
    },
    "PIB_PER_CAPITA": {
        "nome": "PIB per Capita",
        "fonte": "IBGE",
        "api": True,
        "categoria": "Economia",
        "unidade": "R$ / Habitante"
    },
    "PIB_CRESCIMENTO": {
        "nome": "Crescimento Real do PIB",
        "fonte": "IBGE (Calculado)",
        "api": False,
        "categoria": "Economia",
        "unidade": "% a.a."
    },
    "RECEITA_VAF": {
        "nome": "Valor Adicionado Fiscal (VAF)",
        "fonte": "SEFAZ-MG",
        "api": False,
        "categoria": "Capacidade Fiscal",
        "unidade": "R$"
    },
    "RECEITA_ICMS": {
        "nome": "Cota-Parte ICMS",
        "fonte": "SEFAZ-MG",
        "api": False,
        "categoria": "Capacidade Fiscal",
        "unidade": "R$"
    },
    "IDSC_GERAL": {
        "nome": "IDSC-BR (Score Geral)",
        "fonte": "IDSC-BR",
        "api": False,
        "categoria": "Sustentabilidade",
        "unidade": "Score"
    },
    "TAXA_APROVACAO_FUNDAMENTAL": {
        "nome": "Taxa de Aprovação (Fundamental)",
        "fonte": "INEP",
        "api": False,
        "categoria": "Educação",
        "unidade": "%"
    },
    "ESCOLAS_FUNDAMENTAL": {
        "nome": "Número de Escolas (Fundamental)",
        "fonte": "INEP",
        "api": False,
        "categoria": "Educação",
        "unidade": "Escolas"
    },
    "IDEB_ANOS_INICIAIS": {
        "nome": "IDEB (Anos Iniciais)",
        "fonte": "INEP",
        "api": False,
        "categoria": "Educação",
        "unidade": "Score"
    },
    "IDEB_ANOS_FINAIS": {
        "nome": "IDEB (Anos Finais)",
        "fonte": "INEP",
        "api": False,
        "categoria": "Educação",
        "unidade": "Score"
    },
    "EMISSOES_GEE": {
        "nome": "Emissões GEE (Total)",
        "fonte": "SEEG",
        "api": False,
        "categoria": "Sustentabilidade",
        "unidade": "tCO2e"
    },
    "SALDO_CAGED": {
        "nome": "Saldo de Empregos (CAGED)",
        "fonte": "CAGED",
        "api": True,
        "categoria": "Trabalho e Renda",
        "unidade": "Vínculos"
    }
}

# Metadados de fontes para checagem de status e atualização
SOURCES_METADATA = {
    "IBGE": {
        "url": "https://apisidra.ibge.gov.br/",
        "auto_update": True,
        "manual_check": False,
        "data_format": "api"
    },
    "IBGE/SIDRA": {
        "url": "https://apisidra.ibge.gov.br/",
        "auto_update": True,
        "manual_check": False,
        "data_format": "api"
    },
    "SEEG": {
        "url": "https://seeg.eco.br/dados/",
        "auto_update": False,
        "manual_check": True,
        "data_format": "csv"
    },
    "SEBRAE": {
        "url": "https://datasebrae.com.br/municipios/",
        "auto_update": False,
        "manual_check": True,
        "data_format": "csv"
    },
    "MapBiomas": {
        "url": "https://mapbiomas.org/download",
        "auto_update": False,
        "manual_check": True,
        "data_format": "xlsx"
    },
    "INEP": {
        "url": "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/educacao-basica",
        "auto_update": False,
        "manual_check": True,
        "data_format": "xlsx"
    },
    "DataSUS": {
        "url": "https://datasus.saude.gov.br/informacoes-de-saude-tabnet/",
        "auto_update": False,
        "manual_check": True,
        "data_format": "csv"
    },
    "SEFAZ-MG": {
        "url": "https://www.fazenda.mg.gov.br/empresas/vaf/",
        "auto_update": False,
        "manual_check": True,
        "data_format": "csv"
    },
    "IDSC-BR": {
        "url": "https://idsc.cidadessustentaveis.org.br",
        "auto_update": False,
        "manual_check": True,
        "data_format": "xlsx"
    },
    "RAIS": {
        "url": "https://www.gov.br/rais/pt-br/estatisticas",
        "auto_update": False,
        "manual_check": True,
        "data_format": "xlsx"
    },
    "CAGED": {
        "url": "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas/novo-caged",
        "auto_update": False,
        "manual_check": True,
        "data_format": "xlsx"
    },
    "CAGED_NOVO": {
        "url": "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas/novo-caged",
        "auto_update": False,
        "manual_check": True,
        "data_format": "xlsx"
    },
    "SNIS": {
        "url": "http://www.snis.gov.br/",
        "auto_update": False,
        "manual_check": True,
        "data_format": "csv"
    }
}
