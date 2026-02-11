"""
Motor de geração automática de textos e análise de tendências.
Processa dados numéricos e gera insights estratégicos.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from scipy import stats

from config import MUNICIPIO, UF

class TrendAnalyzer:
    """Analisador de tendências com métodos estatísticos."""
    
    @staticmethod
    def analyze_trend(series: pd.Series) -> Dict[str, any]:
        """
        Analisa tendência de uma série temporal usando métodos estatísticos.
        
        Args:
            series: Série temporal com valores numéricos
            
        Returns:
            Dicionário com análise completa da tendência
        """
        if len(series) < 2:
            return {
                "direction": "insufficient_data",
                "strength": 0.0,
                "confidence": 0.0,
                "slope": 0.0,
                "r_squared": 0.0,
                "interpretation": "Série insuficiente para análise de tendência."
            }
        
        # Preparar dados
        x = np.arange(len(series))
        y = series.values
        
        # Regressão linear usando scipy
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Calcular R²
        r_squared = r_value ** 2
        
        # Determinar direção e força
        if abs(slope) < 0.01:
            direction = "stable"
            strength = abs(slope) * 100
        elif slope > 0:
            direction = "increasing"
            strength = min(slope * 100, 100)
        else:
            direction = "decreasing"
            strength = min(abs(slope) * 100, 100)
        
        # Confiança baseada em R² e p-value
        confidence = r_squared * (1 - p_value) if p_value < 0.05 else r_squared * 0.5
        
        # Interpretação qualitativa
        interpretation = TrendAnalyzer._generate_interpretation(
            direction, strength, confidence, slope, series
        )
        
        return {
            "direction": direction,
            "strength": strength,
            "confidence": confidence,
            "slope": slope,
            "r_squared": r_squared,
            "p_value": p_value,
            "interpretation": interpretation
        }
    
    @staticmethod
    def _generate_interpretation(direction: str, strength: float, confidence: float, 
                               slope: float, series: pd.Series) -> str:
        """Gera interpretação qualitativa da tendência."""
        
        # Qualificadores de força
        if strength < 20:
            strength_qual = "fraca"
        elif strength < 50:
            strength_qual = "moderada"
        elif strength < 80:
            strength_qual = "forte"
        else:
            strength_qual = "muito forte"
        
        # Qualificadores de confiança
        if confidence < 0.3:
            conf_qual = "baixa"
        elif confidence < 0.6:
            conf_qual = "moderada"
        elif confidence < 0.8:
            conf_qual = "alta"
        else:
            conf_qual = "muito alta"
        
        # Construir interpretação
        if direction == "stable":
            return f"Observa-se estabilidade na série com tendência {strength_qual} e confiança {conf_qual}."
        
        direction_text = "crescimento" if direction == "increasing" else "queda"
        
        # Calcular variação percentual
        if len(series) >= 2:
            var_pct = ((series.iloc[-1] - series.iloc[0]) / series.iloc[0]) * 100
            var_text = f"variação total de {var_pct:.1f}%"
        else:
            var_text = "variação não calculável"
        
        return (f"Observa-se tendência de {direction_text} {strength_qual} ao longo do período "
                f"com confiança {conf_qual} ({var_text}). "
                f"A taxa média de variação é de {slope:.2f} unidades por período.")

class TextGenerator:
    """Gerador de textos automáticos para relatórios."""
    
    @staticmethod
    def generate_executive_summary(indicators_analysis: Dict[str, Dict]) -> str:
        """
        Gera resumo executivo consolidando análises de múltiplos indicadores.
        
        Args:
            indicators_analysis: Dicionário com análises de tendências por indicador
            
        Returns:
            Texto do resumo executivo
        """
        # Contar tendências
        increasing = sum(1 for analysis in indicators_analysis.values() 
                        if analysis.get("direction") == "increasing")
        decreasing = sum(1 for analysis in indicators_analysis.values() 
                        if analysis.get("direction") == "decreasing")
        stable = sum(1 for analysis in indicators_analysis.values() 
                    if analysis.get("direction") == "stable")
        
        total = len(indicators_analysis)
        
        # Identificar indicadores mais fortes
        strong_indicators = []
        for indicator, analysis in indicators_analysis.items():
            if analysis.get("strength", 0) > 60:
                strong_indicators.append((indicator, analysis.get("strength", 0)))
        
        strong_indicators.sort(key=lambda x: x[1], reverse=True)
        
        # Gerar texto
        text = f"O período analisado para {MUNICIPIO}/{UF} apresenta o seguinte panorama:\n\n"
        
        # Visão geral das tendências
        text += f"Dos {total} indicadores analisados, {increasing} mostram crescimento, "
        text += f"{decreasing} apresentam queda e {stable} permanecem estáveis.\n\n"
        
        # Destaques
        if strong_indicators:
            text += "Principais destaques:\n"
            for indicator, strength in strong_indicators[:3]:
                direction = indicators_analysis[indicator].get("direction", "stable")
                direction_text = "crescimento" if direction == "increasing" else "queda"
                text += f"• {indicator}: tendência de {direction_text} muito forte\n"
            text += "\n"
        
        # Síntese qualitativa
        if increasing > decreasing:
            text += ("O município apresenta trajetória predominantemente positiva, "
                    "com a maioria dos indicadores em crescimento. "
                    "Isso sugere um cenário de desenvolvimento favorável, "
                    "embora seja necessário monitorar os pontos de atenção identificados.")
        elif decreasing > increasing:
            text += ("O município enfrenta desafios significativos no período analisado, "
                    "com mais indicadores em queda do que em crescimento. "
                    "São necessárias intervenções estratégicas para reverter esse cenário.")
        else:
            text += ("O município apresenta cenário de estabilidade geral, "
                    "com equilíbrio entre indicadores em crescimento e queda. "
                    "Isso sugere um momento de transição que requer atenção especial.")
        
        return text
    
    @staticmethod
    def generate_thematic_analysis(theme: str, indicators_data: Dict[str, pd.DataFrame]) -> str:
        """
        Gera análise temática específica.
        
        Args:
            theme: Nome do tema (economia, trabalho, etc.)
            indicators_data: Dicionário com DataFrames dos indicadores
            
        Returns:
            Texto da análise temática
        """
        text = f"## Análise Temática: {theme.title()}\n\n"
        
        # Contextualização
        context = TextGenerator._get_theme_context(theme)
        text += f"{context}\n\n"
        
        # Análise dos indicadores
        if indicators_data:
            text += "### Indicadores Analisados\n\n"
            
            for indicator_name, df in indicators_data.items():
                if df.empty:
                    continue
                
                # Análise de tendência
                analysis = TrendAnalyzer.analyze_trend(df["Valor"])
                
                # Último valor disponível
                latest = df.iloc[-1]
                year = int(latest["Ano"])
                value = latest["Valor"]
                
                text += f"**{indicator_name}**: {value:,.0f} em {year}. "
                text += f"{analysis['interpretation']}\n\n"
        
        # Síntese temática
        synthesis = TextGenerator._generate_theme_synthesis(theme, indicators_data)
        text += f"### Síntese Temática\n\n{synthesis}\n\n"
        
        # Recomendações
        recommendations = TextGenerator._get_theme_recommendations(theme, indicators_data)
        text += f"### Recomendações Estratégicas\n\n{recommendations}\n"
        
        return text
    
    @staticmethod
    def _get_theme_context(theme: str) -> str:
        """Retorna contextualização específica do tema."""
        contexts = {
            "economia": "A análise econômica avalia a dinâmica produtiva, a capacidade de geração de riqueza e o ambiente de negócios do município.",
            "trabalho_renda": "O mercado de trabalho formal e os indicadores de renda refletem a capacidade de geração de empregos e a distribuição de renda na população.",
            "educacao": "Os indicadores educacionais medem o acesso ao ensino, a qualidade da educação e o desenvolvimento de capital humano.",
            "saude": "Os indicadores de saúde avaliam o acesso aos serviços, os resultados de saúde pública e o bem-estar da população.",
            "sustentabilidade": "A análise de sustentabilidade integra indicadores ambientais, sociais e de desenvolvimento sustentável do município."
        }
        return contexts.get(theme, "Análise temática específica do indicador selecionado.")
    
    @staticmethod
    def _generate_theme_synthesis(theme: str, indicators_data: Dict[str, pd.DataFrame]) -> str:
        """Gera síntese específica do tema."""
        # Analisar tendências gerais do tema
        all_trends = []
        for df in indicators_data.values():
            if not df.empty:
                analysis = TrendAnalyzer.analyze_trend(df["Valor"])
                all_trends.append(analysis["direction"])
        
        if not all_trends:
            return "Dados insuficientes para síntese temática."
        
        increasing = all_trends.count("increasing")
        decreasing = all_trends.count("decreasing")
        stable = all_trends.count("stable")
        
        syntheses = {
            "economia": f"O cenário econômico mostra {'forte expansão' if increasing > decreasing else 'desaceleração'}.",
            "trabalho_renda": f"O mercado de trabalho apresenta {'aquecimento' if increasing > decreasing else 'resfriamento'}.",
            "educacao": f"Os indicadores educacionais demonstram {'melhoria' if increasing > decreasing else 'estagnação'}.",
            "saude": f"Os indicadores de saúde revelam {'avanços' if increasing > decreasing else 'desafios'}.",
            "sustentabilidade": f"O desenvolvimento sustentável mostra {'progresso' if increasing > decreasing else 'retrocesso'}."
        }
        
        return syntheses.get(theme, "Análise temática em desenvolvimento.")
    
    @staticmethod
    def _get_theme_recommendations(theme: str, indicators_data: Dict[str, pd.DataFrame]) -> str:
        """Retorna recomendações específicas do tema."""
        recommendations = {
            "economia": (
                "• Fomentar diversificação econômica\n"
                "• Atrair investimentos em setores estratégicos\n"
                "• Apoiar pequenas e médias empresas"
            ),
            "trabalho_renda": (
                "• Qualificar força de trabalho para setores emergentes\n"
                "• Implementar políticas de geração de emprego\n"
                "• Apoiar empreendedorismo local"
            ),
            "educacao": (
                "• Investir em infraestrutura escolar\n"
                "• Formar professores e profissionais da educação\n"
                "• Expandir acesso ao ensino técnico"
            ),
            "saude": (
                "• Ampliar acesso a serviços de saúde\n"
                "• Investir em prevenção e promoção da saúde\n"
                "• Modernizar unidades de atendimento"
            ),
            "sustentabilidade": (
                "• Implementar políticas de conservação ambiental\n"
                "• Promover economia verde e circular\n"
                "• Monitorar indicadores de sustentabilidade"
            )
        }
        
        return recommendations.get(theme, "• Desenvolver políticas públicas específicas\n• Monitorar indicadores continuamente\n• Avaliar impactos das intervenções")
    
    @staticmethod
    def generate_strategic_conclusions(all_analyses: Dict[str, Dict]) -> str:
        """
        Gera conclusões estratégicas integradas.
        
        Args:
            all_analyses: Análises de todos os indicadores
            
        Returns:
            Texto com conclusões estratégicas
        """
        text = "## Conclusões Estratégicas\n\n"
        
        # Identificar padrões
        patterns = TextGenerator._identify_patterns(all_analyses)
        
        # Oportunidades
        opportunities = TextGenerator._identify_opportunities(all_analyses, patterns)
        
        # Alertas
        alerts = TextGenerator._identify_alerts(all_analyses, patterns)
        
        # Síntese final
        text += "### Síntese Integrada\n\n"
        text += f"A análise integrada dos indicadores de {MUNICIPIO} revela:\n\n"
        
        for pattern, description in patterns.items():
            text += f"• {description}\n"
        
        text += f"\n### Oportunidades Estratégicas\n\n{opportunities}\n\n"
        text += f"### Alertas e Pontos de Atenção\n\n{alerts}\n\n"
        
        # Recomendações finais
        text += "### Recomendações Finais\n\n"
        text += "Com base na análise integrada, recomenda-se:\n\n"
        text += "1. Priorizar investimentos em áreas com maior potencial de retorno\n"
        text += "2. Implementar políticas públicas integradas e intersetoriais\n"
        text += "3. Estabelecer sistema de monitoramento contínuo de indicadores\n"
        text += "4. Fortalecer capacidade técnica para análise de dados\n"
        text += "5. Promover transparência e participação social no planejamento\n"
        
        return text
    
    @staticmethod
    def _identify_patterns(analyses: Dict[str, Dict]) -> Dict[str, str]:
        """Identifica padrões nas análises."""
        patterns = {}
        
        # Analisar direções gerais
        directions = [analysis.get("direction", "stable") for analysis in analyses.values()]
        
        if directions.count("increasing") > len(directions) * 0.6:
            patterns["crescimento_geral"] = "Tendência geral de crescimento na maioria dos indicadores"
        elif directions.count("decreasing") > len(directions) * 0.6:
            patterns["queda_geral"] = "Tendência geral de queda na maioria dos indicadores"
        else:
            patterns["cenario_misto"] = "Cenário misto com indicadores em diferentes direções"
        
        # Analisar forças
        strong_indicators = [name for name, analysis in analyses.items() 
                           if analysis.get("strength", 0) > 70]
        
        if strong_indicators:
            patterns["tendencias_fortes"] = f"Tendências fortes em: {', '.join(strong_indicators[:3])}"
        
        return patterns
    
    @staticmethod
    def _identify_opportunities(analyses: Dict[str, Dict], patterns: Dict[str, str]) -> str:
        """Identifica oportunidades estratégicas."""
        opportunities = []
        
        # Oportunidades baseadas em tendências positivas
        for name, analysis in analyses.items():
            if analysis.get("direction") == "increasing" and analysis.get("strength", 0) > 50:
                opportunities.append(f"• Potencial de expansão em {name}")
        
        # Oportunidades baseadas em estabilidade
        stable_indicators = [name for name, analysis in analyses.items() 
                          if analysis.get("direction") == "stable"]
        if stable_indicators:
            opportunities.append(f"• Base sólida para desenvolvimento em: {', '.join(stable_indicators)}")
        
        return "\n".join(opportunities) if opportunities else "• Avaliar novas oportunidades de desenvolvimento"
    
    @staticmethod
    def _identify_alerts(analyses: Dict[str, Dict], patterns: Dict[str, str]) -> str:
        """Identifica alertas e pontos de atenção."""
        alerts = []
        
        # Alertas baseados em tendências negativas
        for name, analysis in analyses.items():
            if analysis.get("direction") == "decreasing" and analysis.get("strength", 0) > 50:
                alerts.append(f"• Atenção à queda em {name}")
        
        # Alertas baseados em confiança baixa
        low_confidence = [name for name, analysis in analyses.items() 
                        if analysis.get("confidence", 0) < 0.3]
        if low_confidence:
            alerts.append(f"• Dados instáveis requerem atenção em: {', '.join(low_confidence)}")
        
        return "\n".join(alerts) if alerts else "• Manter monitoramento contínuo dos indicadores"

# Funções de conveniência
def analyze_multiple_indicators(indicators_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
    """Analisa múltiplos indicadores simultaneamente."""
    results = {}
    
    for name, df in indicators_data.items():
        if not df.empty and len(df) > 1:
            results[name] = TrendAnalyzer.analyze_trend(df["Valor"])
        else:
            results[name] = {
                "direction": "insufficient_data",
                "interpretation": "Dados insuficientes para análise."
            }
    
    return results

def generate_complete_report(indicators_data: Dict[str, pd.DataFrame]) -> str:
    """Gera relatório completo com todas as seções."""
    # Analisar indicadores
    analyses = analyze_multiple_indicators(indicators_data)
    
    # Gerar seções
    report = TextGenerator.generate_executive_summary(analyses)
    
    # Adicionar análises temáticas
    themes = {
        "economia": {k: v for k, v in indicators_data.items() 
                    if any(econ in k.lower() for econ in ["pib", "vaf", "empresa"])},
        "trabalho_renda": {k: v for k, v in indicators_data.items() 
                          if any(trab in k.lower() for trab in ["emprego", "salario", "caged"])},
        "sustentabilidade": {k: v for k, v in indicators_data.items() 
                           if any(sust in k.lower() for sust in ["idsc", "emissao", "area"])}
    }
    
    for theme, data in themes.items():
        if data:
            report += "\n\n" + TextGenerator.generate_thematic_analysis(theme, data)
    
    # Adicionar conclusões
    report += "\n\n" + TextGenerator.generate_strategic_conclusions(analyses)
    
    return report
