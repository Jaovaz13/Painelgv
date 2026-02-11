"""
Gerador de Resumo Executivo para Relatórios Institucionais
Cria síntese estratégica com destaques e orientações para gestão.
"""

import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime

from reports.text_engine import TrendAnalyzer
from reports.text_enhancer import text_enhancer
from reports.indicator_groups import INDICATOR_GROUPS, get_group_for_indicator

class ExecutiveSummaryGenerator:
    """Gerador de resumo executivo estratégico."""
    
    def __init__(self):
        """Inicializa o gerador."""
        self.trend_analyzer = TrendAnalyzer()
        self.text_enhancer = text_enhancer
    
    def generate_executive_summary(self, indicators_data: Dict[str, pd.DataFrame], 
                                 period_start: int, period_end: int) -> str:
        """
        Gera resumo executivo completo.
        
        Args:
            indicators_data: Dicionário com DataFrames dos indicadores
            period_start: Ano inicial do período
            period_end: Ano final do período
            
        Returns:
            Texto do resumo executivo
        """
        # Analisar todos os indicadores
        analyses = self._analyze_all_indicators(indicators_data)
        
        # Extrair destaques e alertas
        highlights = self._extract_highlights(analyses)
        warnings = self._extract_warnings(analyses)
        
        # Gerar resumo por grupos temáticos
        group_summaries = self._generate_group_summaries(analyses)
        
        # Compilar resumo executivo
        summary = self._compile_executive_summary(
            highlights, warnings, group_summaries, period_start, period_end
        )
        
        return summary
    
    def _analyze_all_indicators(self, indicators_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """Analisa todos os indicadores disponíveis."""
        analyses = {}
        
        for indicator, data in indicators_data.items():
            if data is not None and not data.empty and len(data) > 1:
                try:
                    # Análise de tendência
                    trend_analysis = self.trend_analyzer.analyze_trend(data["Valor"])

                    # Normalizar direção (TrendAnalyzer usa increasing/decreasing/stable)
                    direction = trend_analysis.get("direction", "stable")
                    direction_map = {
                        "increasing": "crescimento",
                        "decreasing": "queda",
                        "stable": "estavel",
                        "insufficient_data": "sem_dados",
                    }
                    trend_pt = direction_map.get(direction, "estavel")
                    
                    # Análise adicional
                    additional_analysis = self._additional_analysis(data, indicator)
                    
                    analyses[indicator] = {
                        "trend": trend_pt,
                        "strength": trend_analysis.get("strength", 0),
                        "confidence": trend_analysis.get("confidence", 0),
                        "interpretation": trend_analysis.get("interpretation", ""),
                        "latest_value": data.iloc[-1]["Valor"],
                        "latest_year": int(data.iloc[-1]["Ano"]),
                        "data_points": len(data),
                        "group": get_group_for_indicator(indicator),
                        **additional_analysis
                    }
                    
                except Exception as e:
                    print(f"Erro ao analisar {indicator}: {e}")
                    continue
        
        return analyses
    
    def _additional_analysis(self, data: pd.DataFrame, indicator: str) -> Dict[str, Any]:
        """Análise adicional específica por indicador."""
        analysis = {}
        
        try:
            # Variação total no período
            if len(data) >= 2:
                first_value = data.iloc[0]["Valor"]
                last_value = data.iloc[-1]["Valor"]
                
                if first_value != 0:
                    total_variation = ((last_value - first_value) / first_value) * 100
                    analysis["total_variation"] = total_variation
                else:
                    analysis["total_variation"] = 0
            
            # Volatilidade (desvio padrão das variações)
            if len(data) > 2:
                variations = data["Valor"].pct_change().dropna()
                volatility = variations.std()
                analysis["volatility"] = volatility
            
            # Classificação de importância baseada no grupo
            group = get_group_for_indicator(indicator)
            if group == "Economia":
                analysis["importance"] = "alta"
            elif group == "Trabalho":
                analysis["importance"] = "alta"
            elif group == "Educacao":
                analysis["importance"] = "media"
            elif group == "Sustentabilidade":
                analysis["importance"] = "media"
            else:
                analysis["importance"] = "baixa"
                
        except Exception:
            pass
        
        return analysis
    
    def _extract_highlights(self, analyses: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Extrai destaques positivos das análises."""
        highlights = []
        
        for indicator, analysis in analyses.items():
            # Critérios para destaque positivo
            if (analysis["trend"] == "crescimento" and analysis["strength"] > 0.5) or \
               (analysis["trend"] == "estavel" and analysis.get("importance") == "alta"):
                
                highlight = {
                    "indicator": indicator,
                    "group": analysis["group"],
                    "trend": analysis["trend"],
                    "strength": analysis["strength"],
                    "latest_value": analysis["latest_value"],
                    "latest_year": analysis["latest_year"],
                    "interpretation": self.text_enhancer.enhance_text(analysis["interpretation"]),
                    "importance": analysis.get("importance", "media")
                }
                
                highlights.append(highlight)
        
        # Ordenar por importância e força
        highlights.sort(key=lambda x: (
            {"alta": 3, "media": 2, "baixa": 1}.get(x["importance"], 0),
            x["strength"]
        ), reverse=True)
        
        return highlights[:5]  # Top 5 destaques
    
    def _extract_warnings(self, analyses: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Extrai alertas das análises."""
        warnings = []
        
        for indicator, analysis in analyses.items():
            # Critérios para alerta
            if (analysis["trend"] == "queda" and analysis["strength"] > 0.7) or \
               (analysis.get("total_variation", 0) < -50):  # Queda > 50%
                
                warning = {
                    "indicator": indicator,
                    "group": analysis["group"],
                    "trend": analysis["trend"],
                    "strength": analysis["strength"],
                    "latest_value": analysis["latest_value"],
                    "latest_year": analysis["latest_year"],
                    "total_variation": analysis.get("total_variation", 0),
                    "interpretation": self._enhance_warning(analysis),
                    "importance": analysis.get("importance", "media")
                }
                
                warnings.append(warning)
        
        # Ordenar por importância e gravidade
        warnings.sort(key=lambda x: (
            {"alta": 3, "media": 2, "baixa": 1}.get(x["importance"], 0),
            x["strength"]
        ), reverse=True)
        
        return warnings[:5]  # Top 5 alertas
    
    def _enhance_warning(self, analysis: Dict[str, Any]) -> str:
        """Melhora texto de alerta."""
        base_text = analysis["interpretation"]
        
        # Adicionar contexto de variação total
        total_var = analysis.get("total_variation", 0)
        if total_var < -50:
            base_text += f", com variação total de {total_var:.1f}% que requer investigação detalhada"
        
        return self.text_enhancer.enhance_text(base_text)
    
    def _generate_group_summaries(self, analyses: Dict[str, Dict]) -> Dict[str, Dict]:
        """Gera resumos por grupo temático."""
        group_summaries = {}
        
        for group_name, group_config in INDICATOR_GROUPS.items():
            group_indicators = group_config["indicators"]
            group_analyses = {k: v for k, v in analyses.items() if k in group_indicators}
            
            if not group_analyses:
                continue
            
            summary = {
                "total_indicators": len(group_indicators),
                "analyzed_indicators": len(group_analyses),
                "trends": {"crescimento": 0, "queda": 0, "estavel": 0},
                "avg_strength": 0,
                "main_highlights": [],
                "main_concerns": []
            }
            
            # Compilar estatísticas do grupo
            strengths = []
            for indicator, analysis in group_analyses.items():
                summary["trends"][analysis["trend"]] += 1
                strengths.append(analysis["strength"])
                
                # Destaques do grupo
                if analysis["trend"] == "crescimento" and analysis["strength"] > 0.6:
                    summary["main_highlights"].append(indicator)
                elif analysis["trend"] == "queda" and analysis["strength"] > 0.7:
                    summary["main_concerns"].append(indicator)
            
            if strengths:
                summary["avg_strength"] = sum(strengths) / len(strengths)
            
            group_summaries[group_name] = summary
        
        return group_summaries
    
    def _compile_executive_summary(self, highlights: List[Dict], warnings: List[Dict],
                                 group_summaries: Dict[str, Dict], period_start: int, 
                                 period_end: int) -> str:
        """Compila o resumo executivo final."""
        
        # Cabeçalho
        summary_lines = [
            f"RESUMO EXECUTIVO - ANÁLISE SOCIOECONÔMICA",
            f"Período: {period_start} a {period_end}",
            f"Data: {datetime.now().strftime('%d/%m/%Y')}",
            "",
            "PRINCIPAIS DESTAQUES DO PERÍODO",
            ""
        ]
        
        # Destaques positivos
        if highlights:
            for highlight in highlights[:3]:  # Top 3
                line = f"- {highlight['indicator']}: {highlight['interpretation']}"
                summary_lines.append(line)
        else:
            summary_lines.append("- Não foram identificados destaques positivos com força estatística suficiente no período.")
        
        summary_lines.extend(["", ""])
        
        # Alertas e preocupações
        summary_lines.extend(["PONTOS DE ATENÇÃO", ""])
        
        if warnings:
            for warning in warnings[:3]:  # Top 3 alertas
                line = f"- {warning['indicator']}: {warning['interpretation']}"
                summary_lines.append(line)
        else:
            summary_lines.append("- Não foram identificados pontos críticos com força estatística suficiente no período analisado.")
        
        summary_lines.extend(["", ""])
        
        # Síntese por grupos temáticos
        summary_lines.extend(["SÍNTESE POR ÁREAS ESTRATÉGICAS", ""])
        
        for group_name, summary in group_summaries.items():
            group_config = INDICATOR_GROUPS[group_name]
            
            # Status do grupo
            if summary["trends"]["crescimento"] > summary["trends"]["queda"]:
                status = "EXPANSÃO"
            elif summary["trends"]["queda"] > summary["trends"]["crescimento"]:
                status = "AJUSTE"
            else:
                status = "ESTABILIDADE"
            
            line = f"- {group_config['title']}: {status}"
            summary_lines.append(line)
            
            # Detalhes do grupo
            analyzed = summary["analyzed_indicators"]
            total = summary["total_indicators"]
            summary_lines.append(f"   • {analyzed}/{total} indicadores analisados")
            
            if summary["main_highlights"]:
                highlights_str = ", ".join(summary["main_highlights"][:2])
                summary_lines.append(f"   • Destaques: {highlights_str}")
            
            if summary["main_concerns"]:
                concerns_str = ", ".join(summary["main_concerns"][:2])
                summary_lines.append(f"   • Atenção: {concerns_str}")
            
            summary_lines.append("")
        
        # Recomendações estratégicas
        summary_lines.extend(["RECOMENDAÇÕES ESTRATÉGICAS", ""])
        
        recommendations = self._generate_recommendations(highlights, warnings, group_summaries)
        for rec in recommendations:
            summary_lines.append(f"• {rec}")
        
        # Conclusão
        summary_lines.extend([
            "",
            "CONCLUSÃO",
            "",
            "A síntese acima reflete exclusivamente os indicadores disponíveis no período e suas tendências calculadas.",
            "Recomenda-se priorizar o acompanhamento dos pontos de atenção listados e manter a atualização contínua das bases.",
            ""
        ])
        
        return "\n".join(summary_lines)
    
    def _generate_recommendations(self, highlights: List[Dict], warnings: List[Dict],
                                group_summaries: Dict[str, Dict]) -> List[str]:
        """Gera recomendações estratégicas baseadas nas análises."""
        recommendations = []
        
        # Baseado nos alertas
        if warnings:
            high_importance_warnings = [w for w in warnings if w.get("importance") == "alta"]
            if high_importance_warnings:
                recommendations.append("Priorizar análise detalhada dos indicadores de alta importância com desempenho em queda")
        
        # Baseado nos destaques
        if highlights:
            economy_highlights = [h for h in highlights if h["group"] == "Economia"]
            if economy_highlights:
                recommendations.append("Aproveitar momento favorável da economia para implementar políticas de desenvolvimento sustentado")
        
        # Baseado nos grupos
        if "Sustentabilidade" in group_summaries:
            sust_summary = group_summaries["Sustentabilidade"]
            if sust_summary["trends"]["queda"] > 0:
                recommendations.append("Intensificar políticas ambientais e de sustentabilidade para reverter tendências negativas")
        
        # Recomendações genéricas
        recommendations.extend([
            "Manter monitoramento contínuo dos indicadores-chave para gestão municipal",
            "Utilizar análises prospectivas para planejamento de médio e longo prazo",
            "Integrar dados socioeconômicos em sistema de apoio à decisão"
        ])
        
        return recommendations[:5]  # Top 5 recomendações

# Instância global do gerador
executive_summary_generator = ExecutiveSummaryGenerator()
