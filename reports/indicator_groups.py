"""
Configuração de Grupos Temáticos para Relatórios Estruturados
Organiza indicadores por áreas estratégicas com prioridade e descrições.
"""

from typing import Dict, List, Any

# Configuração de grupos temáticos para relatórios
INDICATOR_GROUPS = {
    "Economia": {
        "title": "ECONOMIA E DESENVOLVIMENTO",
        "description": "Análise do desempenho econômico municipal e projeções",
        "indicators": [
            "PIB_TOTAL",
            "PIB_PER_CAPITA", 
            "PIB_ESTIMADO",
            "RECEITA_VAF",
            "RECEITA_ICMS"
        ],
        "priority": 1,
        "color": "#1e3a8a"  # Azul escuro
    },
    "Trabalho": {
        "title": "TRABALHO E ATIVIDADE PRODUTIVA",
        "description": "Mercado de trabalho formal e empreendedorismo",
        "indicators": [
            "EMPREGOS_RAIS",
            "SALDO_CAGED_ANUAL",
            "SEBRAE_GERAL",
            "EMPREGOS_FORMAIS"
        ],
        "priority": 2,
        "color": "#16a34a"  # Verde
    },
    "Educacao": {
        "title": "CAPITAL HUMANO",
        "description": "Educação e desenvolvimento de competências",
        "indicators": [
            "MATRICULAS_TOTAL",
            "ESCOLAS_FUNDAMENTAL",
            "TAXA_APROVACAO_FUNDAMENTAL",
            "IDEB",
            "DOCENTES"
        ],
        "priority": 3,
        "color": "#3b82f6"  # Azul médio
    },
    "Sustentabilidade": {
        "title": "SUSTENTABILIDADE",
        "description": "Indicadores ambientais e desenvolvimento sustentável",
        "indicators": [
            "INDICE_SUSTENTABILIDADE",
            "EMISSOES_GEE",
            "SEEG_AR",
            "SEEG_GASES",
            "IDSC_GERAL"
        ],
        "priority": 4,
        "color": "#d97706"  # Laranja
    }
}

# Mapeamento inverso: indicador → grupo
INDICATOR_TO_GROUP = {}
for group_name, group_config in INDICATOR_GROUPS.items():
    for indicator in group_config["indicators"]:
        INDICATOR_TO_GROUP[indicator] = group_name

def get_group_for_indicator(indicator: str) -> str:
    """Retorna o grupo temático para um indicador."""
    return INDICATOR_TO_GROUP.get(indicator, "Outros")

def get_sorted_groups() -> List[tuple]:
    """Retorna grupos ordenados por prioridade."""
    return sorted(
        INDICATOR_GROUPS.items(),
        key=lambda x: x[1]["priority"]
    )

def get_group_indicators(group_name: str) -> List[str]:
    """Retorna indicadores de um grupo específico."""
    return INDICATOR_GROUPS.get(group_name, {}).get("indicators", [])

def organize_indicators_by_groups(indicators: List[str]) -> Dict[str, List[str]]:
    """Organiza lista de indicadores por grupos temáticos."""
    organized = {}
    
    # Inicializar grupos
    for group_name in INDICATOR_GROUPS:
        organized[group_name] = []
    
    # Adicionar indicadores aos grupos correspondentes
    for indicator in indicators:
        group = get_group_for_indicator(indicator)
        if group != "Outros" and indicator not in organized[group]:
            organized[group].append(indicator)
    
    # Remover grupos vazios
    organized = {k: v for k, v in organized.items() if v}
    
    return organized

def clean_indicators_list(indicators: List[str]) -> List[str]:
    """Remove duplicações e ordena por prioridade temática."""
    # Remover duplicatas mantendo ordem de aparição
    seen = set()
    unique_indicators = []
    for indicator in indicators:
        if indicator not in seen:
            seen.add(indicator)
            unique_indicators.append(indicator)
    
    # Ordenar por grupos temáticos (prioridade)
    ordered_indicators = []
    
    # Primeiro: indicadores que pertencem a grupos
    for group_name, group_config in sorted(INDICATOR_GROUPS.items(), key=lambda x: x[1]["priority"]):
        for indicator in group_config["indicators"]:
            if indicator in unique_indicators and indicator not in ordered_indicators:
                ordered_indicators.append(indicator)
    
    # Depois: indicadores sem grupo (mantém ordem original)
    for indicator in unique_indicators:
        if indicator not in ordered_indicators:
            ordered_indicators.append(indicator)
    
    return ordered_indicators

def get_group_summary(group_name: str, indicators_data: Dict[str, Any]) -> Dict[str, Any]:
    """Gera resumo de um grupo temático."""
    group_config = INDICATOR_GROUPS.get(group_name, {})
    group_indicators = group_config.get("indicators", [])
    
    summary = {
        "title": group_config.get("title", group_name),
        "description": group_config.get("description", ""),
        "total_indicators": len(group_indicators),
        "available_indicators": 0,
        "trends": {
            "crescimento": 0,
            "queda": 0,
            "estavel": 0
        },
        "highlights": [],
        "warnings": []
    }
    
    # Analisar indicadores disponíveis no grupo
    for indicator in group_indicators:
        if indicator in indicators_data:
            summary["available_indicators"] += 1
            
            # Analisar tendência se disponível
            data = indicators_data[indicator]
            if hasattr(data, 'empty') and not data.empty:
                try:
                    from reports.text_engine import TrendAnalyzer
                    analysis = TrendAnalyzer.analyze_trend(data["Valor"])
                    trend = analysis.get("direction", "estavel")
                    summary["trends"][trend] = summary["trends"].get(trend, 0) + 1
                    
                    # Destaques e alertas
                    strength = analysis.get("strength", 0)
                    if trend == "crescimento" and strength > 0.5:
                        summary["highlights"].append(f"{indicator}: {analysis.get('interpretation', '')}")
                    elif trend == "queda" and strength > 0.7:
                        summary["warnings"].append(f"{indicator}: {analysis.get('interpretation', '')}")
                        
                except Exception:
                    continue
    
    return summary
