"""
Módulo para geração de narrativas automáticas para slides executivos.
Implementa templates inteligentes baseados em dados reais.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from database import get_timeseries, list_indicators
from reports.text_engine import TrendAnalyzer, analyze_multiple_indicators

class SlideNarrativeGenerator:
    """Gerador de narrativas automáticas para slides."""
    
    def __init__(self):
        """Inicializa o gerador."""
        self.trend_analyzer = TrendAnalyzer()
    
    def generate_executive_summary(self, indicators_data: Dict[str, pd.DataFrame], 
                               ano_inicio: int, ano_fim: int) -> str:
        """
        Gera narrativa curta para o slide executivo.
        
        Args:
            indicators_data: Dicionário com dados dos indicadores
            ano_inicio: Ano inicial da análise
            ano_fim: Ano final da análise
            
        Returns:
            String com narrativa formatada
        """
        # Analisar tendências principais
        all_analyses = analyze_multiple_indicators(indicators_data)
        
        # Identificar principais destaques
        positive_trends = []
        negative_trends = []
        
        for name, analysis in all_analyses.items():
            if analysis.get("strength", 0) > 50:
                direction = analysis.get("direction", "stable")
                if direction == "increasing":
                    positive_trends.append(name)
                elif direction == "decreasing":
                    negative_trends.append(name)
        
        # Gerar narrativa baseada nos padrões
        if positive_trends and not negative_trends:
            return (
                f"Entre {ano_inicio} e {ano_fim}, observou-se tendência de crescimento em indicadores como "
                f"{', '.join(positive_trends[:2])}."
            )
        elif negative_trends and not positive_trends:
            return (
                f"Entre {ano_inicio} e {ano_fim}, observou-se tendência de queda em indicadores como "
                f"{', '.join(negative_trends[:2])}."
            )
        elif positive_trends and negative_trends:
            return (
                f"Entre {ano_inicio} e {ano_fim}, houve sinais mistos: crescimento em {', '.join(positive_trends[:2])} "
                f"e queda em {', '.join(negative_trends[:2])}."
            )
        else:
            return f"Entre {ano_inicio} e {ano_fim}, não foi possível identificar tendências fortes com a série disponível."
    
    def generate_indicator_ranking(self, indicators_data: Dict[str, pd.DataFrame]) -> Tuple[List[str], List[str]]:
        """
        Gera ranking dos melhores e piores indicadores.
        
        Args:
            indicators_data: Dicionário com dados dos indicadores
            
        Returns:
            Tuple com (melhores_indicadores, piores_indicadores)
        """
        indicator_scores = {}
        
        for name, df in indicators_data.items():
            if df.empty or len(df) < 2:
                continue
                
            try:
                # Calcular variação percentual acumulada
                first_value = df.iloc[0]["Valor"]
                last_value = df.iloc[-1]["Valor"]
                
                if first_value != 0:
                    variation = ((last_value - first_value) / first_value) * 100
                    indicator_scores[name] = variation
            except Exception:
                continue
        
        # Ordenar por variação
        sorted_indicators = sorted(indicator_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Separar melhores e piores
        best = [name for name, score in sorted_indicators[:3]]
        worst = [name for name, score in sorted_indicators[-3:]]
        
        return best, worst
    
    def generate_scorecard_data(self, indicators_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        Gera dados para scorecard do slide de panorama.
        
        Args:
            indicators_data: Dicionário com dados dos indicadores
            
        Returns:
            Dicionário com dados do scorecard
        """
        scorecard = {}
        
        # Indicadores principais para o scorecard
        key_indicators = {
            "PIB per capita": ["PIB", "PIB_PER_CAPITA"],
            "Emprego formal": ["EMPREGO_FORMAL", "CAGED_SALDO"],
            "Empresas por mil habitantes": ["EMPRESAS", "EMPREENDEDORISMO"],
            "IDSC-BR": ["IDSC_GERAL", "IDSC_BR"]
        }
        
        for indicator_name, possible_keys in key_indicators.items():
            value = None
            variation = None
            unit = ""
            
            # Tentar encontrar o indicador nos dados
            for key in possible_keys:
                if key in indicators_data:
                    df = indicators_data[key]
                    if not df.empty:
                        latest = df.iloc[-1]
                        value = latest["Valor"]
                        try:
                            unit = str(latest.get("Unidade", "")).strip()
                        except Exception:
                            unit = ""
                        
                        # Calcular variação
                        if len(df) > 1:
                            first = df.iloc[0]["Valor"]
                            if first != 0:
                                variation = ((value - first) / first) * 100
                        break
            
            scorecard[indicator_name] = {
                "value": value,
                "variation": variation,
                "unit": unit,
                "status": self._get_indicator_status(variation),
            }
        
        return scorecard
    
    def _get_indicator_status(self, variation: Optional[float]) -> str:
        """Classifica o status do indicador baseado na variação."""
        if variation is None:
            return "sem_dados"
        elif variation > 5:
            return "crescimento_forte"
        elif variation > 0:
            return "crescimento_moderado"
        elif variation > -5:
            return "estabilidade"
        else:
            return "queda"
    
    def generate_economic_structure_analysis(self, indicators_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Gera análise da estrutura produtiva.
        
        Args:
            indicators_data: Dicionário com dados dos indicadores
            
        Returns:
            Dicionário com análise da estrutura produtiva
        """
        # Estrutura setorial real: calcular participação com base em setores do PIB, quando disponíveis.
        sector_keys = {
            "Agropecuária": "PIB_AGROPECUARIA",
            "Indústria": "PIB_INDUSTRIA",
            "Serviços": "PIB_SERVICOS",
            "Administração Pública": "PIB_ADM_PUBLICA",
        }

        # Encontrar ano mais recente em que todos os setores existam
        sector_series = {}
        for label, key in sector_keys.items():
            df = indicators_data.get(key)
            if df is None or df.empty:
                return {
                    "structure": {},
                    "year": None,
                    "dominant_sector": None,
                }
            sector_series[label] = df

        # Determinar ano comum mais recente
        common_years = None
        for df in sector_series.values():
            years = set(df["Ano"].dropna().astype(int).tolist())
            common_years = years if common_years is None else common_years.intersection(years)
        if not common_years:
            return {"structure": {}, "year": None, "dominant_sector": None}

        year = max(common_years)
        values = {}
        for label, df in sector_series.items():
            v = df[df["Ano"].astype(int) == year]["Valor"]
            if v.empty:
                return {"structure": {}, "year": None, "dominant_sector": None}
            values[label] = float(v.iloc[-1])

        total = sum(values.values())
        if total <= 0:
            return {"structure": {}, "year": year, "dominant_sector": None}

        structure = {k: (v / total) * 100 for k, v in values.items()}
        dominant = max(structure.items(), key=lambda x: x[1])[0] if structure else None
        return {"structure": structure, "year": year, "dominant_sector": dominant}
    
    def generate_labor_market_analysis(self, indicators_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Gera análise do mercado de trabalho.
        
        Args:
            indicators_data: Dicionário com dados dos indicadores
            
        Returns:
            Dicionário com análise do mercado de trabalho
        """
        employment_data = indicators_data.get("SALDO_CAGED_MENSAL", pd.DataFrame())
        
        if not employment_data.empty:
            # Calcular saldo acumulado por ano
            yearly_balance = employment_data.groupby("Ano")["Valor"].sum().reset_index()
            
            # Último ano completo
            latest_year = yearly_balance.iloc[-1]
            total_balance = latest_year["Valor"]
            
            # Tendência
            trend_analysis = self.trend_analyzer.analyze_trend(yearly_balance["Valor"])
            
            return {
                "yearly_balance": yearly_balance.to_dict("records"),
                "latest_balance": total_balance,
                "trend": trend_analysis.get("direction", "stable"),
                "average_monthly": total_balance / 12 if total_balance else 0
            }
        
        return {
            "yearly_balance": [],
            "latest_balance": None,
            "trend": "insufficient_data",
            "average_monthly": None,
        }
    
    def generate_human_capital_analysis(self, indicators_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Gera análise de capital humano (educação + saúde).
        
        Args:
            indicators_data: Dicionário com dados dos indicadores
            
        Returns:
            Dicionário com análise de capital humano
        """
        # Educação (usar apenas se houver séries reais no banco; não inferir status)
        ideb_data = indicators_data.get("IDEB", pd.DataFrame())
        education_analysis = {}
        
        if not ideb_data.empty:
            latest_ideb = ideb_data.iloc[-1]["Valor"]
            education_analysis = {
                "ideb_score": latest_ideb,
                "status": "bom" if latest_ideb >= 6.0 else "regular" if latest_ideb >= 5.0 else "precisa_melhorar"
            }
        
        # Saúde
        health_indicators = ["MORTALIDADE_INFANTIL", "COBERTURA_ESF", "LEITOS_HOSPITALARES"]
        health_analysis = {}
        
        for indicator in health_indicators:
            if indicator in indicators_data:
                df = indicators_data[indicator]
                if not df.empty:
                    latest = df.iloc[-1]["Valor"]
                    health_analysis[indicator] = latest
        
        return {
            "education": education_analysis,
            "health": health_analysis,
            "summary": "",
        }
    
    def generate_sustainability_analysis(self, indicators_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        Gera análise de sustentabilidade (IDSC-BR).
        
        Args:
            indicators_data: Dicionário com dados dos indicadores
            
        Returns:
            Dicionário com análise de sustentabilidade
        """
        idsc_data = indicators_data.get("IDSC_GERAL", pd.DataFrame())
        
        if not idsc_data.empty:
            latest_score = idsc_data.iloc[-1]["Valor"]
            trend_analysis = self.trend_analyzer.analyze_trend(idsc_data["Valor"])
            
            return {
                "overall_score": latest_score,
                "trend": trend_analysis.get("direction", "stable"),
                "status": self._classify_sustainability_status(latest_score),
            }
        
        return {
            "overall_score": None,
            "trend": "insufficient_data",
            "status": "sem_dados",
        }
    
    def _classify_sustainability_status(self, score: float) -> str:
        """Classifica o status de sustentabilidade."""
        if score >= 0.7:
            return "desenvolvimento_sustentavel"
        elif score >= 0.5:
            return "em_transicao"
        elif score >= 0.3:
            return "desafios_significativos"
        else:
            return "situacao_critica"

# Instância global para uso nos slides
narrative_generator = SlideNarrativeGenerator()
