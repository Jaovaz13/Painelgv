"""
Análise avançada de insights e correlações entre indicadores.
Identifica padrões, anomalias e oportunidades estratégicas.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from scipy.stats import pearsonr, spearmanr
import logging

logger = logging.getLogger(__name__)

class InsightsAnalyzer:
    """Analisador avançado de insights entre indicadores."""
    
    def __init__(self):
        """Inicializa o analisador."""
        self.correlations = {}
        self.clusters = {}
        self.anomalies = {}
    
    def analyze_correlations(self, indicators_data: Dict[str, pd.DataFrame], 
                           min_periods: int = 3) -> Dict[str, Dict[str, Any]]:
        """
        Analisa correlações entre múltiplos indicadores.
        
        Args:
            indicators_data: Dicionário com DataFrames dos indicadores
            min_periods: Período mínimo para análise
            
        Returns:
            Dicionário com correlações e significância
        """
        correlations = {}
        
        # Preparar dados alinhados por ano
        aligned_data = self._align_indicators_by_year(indicators_data, min_periods)
        
        if len(aligned_data) < 2:
            logger.warning("Dados insuficientes para análise de correlação")
            return correlations
        
        indicator_names = list(aligned_data.keys())
        
        for i, indicator1 in enumerate(indicator_names):
            correlations[indicator1] = {}
            
            for j, indicator2 in enumerate(indicator_names):
                if i >= j:  # Evitar duplicatas e autocorrelação
                    continue
                
                data1 = aligned_data[indicator1]
                data2 = aligned_data[indicator2]
                
                # Calcular correlação de Pearson
                pearson_corr, pearson_p = pearsonr(data1, data2)
                
                # Calcular correlação de Spearman (não paramétrica)
                spearman_corr, spearman_p = spearmanr(data1, data2)
                
                # Determinar força da correlação
                strength = self._classify_correlation_strength(abs(pearson_corr))
                
                correlations[indicator1][indicator2] = {
                    "pearson_correlation": pearson_corr,
                    "pearson_p_value": pearson_p,
                    "spearman_correlation": spearman_corr,
                    "spearman_p_value": spearman_p,
                    "strength": strength,
                    "significance": "significant" if pearson_p < 0.05 else "not_significant",
                    "interpretation": self._interpret_correlation(
                        indicator1, indicator2, pearson_corr, pearson_p
                    )
                }
        
        self.correlations = correlations
        return correlations
    
    def _align_indicators_by_year(self, indicators_data: Dict[str, pd.DataFrame], 
                                 min_periods: int) -> Dict[str, np.ndarray]:
        """Alinha indicadores por ano para análise comparativa."""
        # Criar DataFrame unificado
        combined_df = pd.DataFrame()
        
        for name, df in indicators_data.items():
            if df.empty or len(df) < min_periods:
                continue
            
            # Usar o ano como índice
            df_temp = df.set_index("Ano")["Valor"]
            combined_df[name] = df_temp
        
        # Remover anos com dados faltantes
        combined_df = combined_df.dropna()
        
        if len(combined_df) < min_periods:
            return {}
        
        # Retornar dicionário com arrays
        return {col: combined_df[col].values for col in combined_df.columns}
    
    def _classify_correlation_strength(self, corr_value: float) -> str:
        """Classifica a força da correlação."""
        abs_corr = abs(corr_value)
        
        if abs_corr >= 0.8:
            return "very_strong"
        elif abs_corr >= 0.6:
            return "strong"
        elif abs_corr >= 0.4:
            return "moderate"
        elif abs_corr >= 0.2:
            return "weak"
        else:
            return "very_weak"
    
    def _interpret_correlation(self, indicator1: str, indicator2: str, 
                             corr: float, p_value: float) -> str:
        """Gera interpretação da correlação."""
        if p_value >= 0.05:
            return "Correlação não estatisticamente significativa"
        
        direction = "positiva" if corr > 0 else "negativa"
        strength = self._classify_correlation_strength(abs(corr))
        
        strength_map = {
            "very_strong": "muito forte",
            "strong": "forte",
            "moderate": "moderada",
            "weak": "fraca",
            "very_weak": "muito fraca"
        }
        
        return (f"Correlação {direction} {strength_map[strength]} entre "
                f"{indicator1} e {indicator2} (r={corr:.3f})")
    
    def identify_clusters(self, indicators_data: Dict[str, pd.DataFrame], 
                         n_clusters: int = 3) -> Dict[str, Any]:
        """
        Identifica clusters de indicadores com comportamentos similares.
        
        Args:
            indicators_data: Dicionário com DataFrames dos indicadores
            n_clusters: Número de clusters a identificar
            
        Returns:
            Dicionário com informações dos clusters
        """
        # Preparar dados
        aligned_data = self._align_indicators_by_year(indicators_data, min_periods=3)
        
        if len(aligned_data) < n_clusters:
            logger.warning("Dados insuficientes para análise de clusters")
            return {}
        
        # Criar matriz de dados
        indicator_names = list(aligned_data.keys())
        data_matrix = np.array([aligned_data[name] for name in indicator_names]).T
        
        # Normalizar dados manualmente
        data_normalized = (data_matrix - np.mean(data_matrix, axis=0)) / np.std(data_matrix, axis=0)
        
        # Clusterização simplificada usando K-means do scipy
        from scipy.cluster.vq import kmeans, vq
        
        try:
            # Aplicar K-means
            centroids, _ = kmeans(data_normalized, n_clusters)
            cluster_labels, _ = vq(data_normalized, centroids)
            
            # Organizar resultados
            clusters = {}
            for i in range(n_clusters):
                cluster_indicators = []
                for j, label in enumerate(cluster_labels):
                    if label == i:
                        cluster_indicators.append(indicator_names[j])
                clusters[f"cluster_{i+1}"] = {
                    "indicators": cluster_indicators,
                    "size": len(cluster_indicators),
                    "centroid": centroids[i]
                }
            
            # Calcular silhouette score simplificado
            distances = np.array([np.linalg.norm(data_normalized[j] - centroids[cluster_labels[j]]) 
                                  for j in range(len(data_normalized))])
            silhouette_avg = np.mean(distances)
            
            # Adicionar métricas globais
            clusters["metadata"] = {
                "n_clusters": n_clusters,
                "silhouette_score": silhouette_avg,
                "total_indicators": len(indicator_names),
                "interpretation": self._interpret_clusters(clusters, silhouette_avg)
            }
            
            self.clusters = clusters
            return clusters
            
        except Exception as e:
            logger.error(f"Error in cluster analysis: {e}")
            return {}
    
    def _interpret_clusters(self, clusters: Dict[str, Any], silhouette_score: float) -> str:
        """Interpreta os resultados da análise de clusters."""
        if silhouette_score < 0.3:
            quality = "baixa"
        elif silhouette_score < 0.5:
            quality = "moderada"
        else:
            quality = "alta"
        
        interpretation = f"Qualidade da clusterização: {quality} (silhouette: {silhouette_score:.3f})\n\n"
        
        for cluster_key, cluster_info in clusters.items():
            if cluster_key == "metadata":
                continue
            
            cluster_name = self._generate_cluster_name(cluster_info["indicators"])
            interpretation += f"• {cluster_name}: {', '.join(cluster_info['indicators'])}\n"
        
        return interpretation
    
    def _generate_cluster_name(self, indicators: List[str]) -> str:
        """Gera nome descritivo para o cluster baseado nos indicadores."""
        indicators_lower = [ind.lower() for ind in indicators]
        
        # Heurística para nomear clusters
        if any("pib" in ind for ind in indicators_lower):
            return "Cluster Econômico"
        elif any("emprego" in ind or "trabalho" in ind for ind in indicators_lower):
            return "Cluster Trabalhista"
        elif any("educacao" in ind or "escola" in ind for ind in indicators_lower):
            return "Cluster Educacional"
        elif any("saude" in ind or "mortalidade" in ind for ind in indicators_lower):
            return "Cluster de Saúde"
        elif any("sustent" in ind or "idsc" in ind or "emissao" in ind for ind in indicators_lower):
            return "Cluster de Sustentabilidade"
        else:
            return f"Cluster Temático ({len(indicators)} indicadores)"
    
    def detect_anomalies(self, indicators_data: Dict[str, pd.DataFrame], 
                        z_threshold: float = 2.0) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detecta anomalias nos indicadores usando método Z-score.
        
        Args:
            indicators_data: Dicionário com DataFrames dos indicadores
            z_threshold: Limiar para detecção de anomalias
            
        Returns:
            Dicionário com anomalias detectadas
        """
        anomalies = {}
        
        for indicator_name, df in indicators_data.items():
            if df.empty or len(df) < 3:
                continue
            
            indicator_anomalies = []
            values = df["Valor"].values
            
            # Calcular Z-scores
            z_scores = np.abs(stats.zscore(values))
            
            # Identificar anomalias
            anomaly_indices = np.where(z_scores > z_threshold)[0]
            
            for idx in anomaly_indices:
                year = df.iloc[idx]["Ano"]
                value = df.iloc[idx]["Valor"]
                z_score = z_scores[idx]
                
                # Determinar tipo de anomalia
                if z_score > 3:
                    severity = "extreme"
                elif z_score > 2.5:
                    severity = "high"
                else:
                    severity = "moderate"
                
                indicator_anomalies.append({
                    "year": int(year),
                    "value": float(value),
                    "z_score": float(z_score),
                    "severity": severity,
                    "interpretation": self._interpret_anomaly(value, z_score)
                })
            
            if indicator_anomalies:
                anomalies[indicator_name] = indicator_anomalies
        
        self.anomalies = anomalies
        return anomalies
    
    def _interpret_anomaly(self, value: float, z_score: float) -> str:
        """Interpreta uma anomalia detectada."""
        direction = "acima" if z_score > 0 else "abaixo"
        intensity = "extremamente" if abs(z_score) > 3 else "significativamente" if abs(z_score) > 2.5 else "moderadamente"
        
        return f"Valor {direction} da média ({intensity} incomum)"
    
    def generate_insights_summary(self, indicators_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Gera resumo completo de insights analíticos.
        
        Args:
            indicators_data: Dicionário com DataFrames dos indicadores
            
        Returns:
            Dicionário com insights completos
        """
        insights = {
            "correlations": self.analyze_correlations(indicators_data),
            "clusters": self.identify_clusters(indicators_data),
            "anomalies": self.detect_anomalies(indicators_data),
            "strategic_insights": self._generate_strategic_insights(indicators_data)
        }
        
        return insights
    
    def _generate_strategic_insights(self, indicators_data: Dict[str, pd.DataFrame]) -> List[str]:
        """Gera insights estratégicos baseados nas análises."""
        insights = []
        
        # Insights baseados em correlações
        if self.correlations:
            strong_correlations = []
            
            for indicator1, correlations in self.correlations.items():
                for indicator2, corr_info in correlations.items():
                    if (corr_info["strength"] in ["strong", "very_strong"] and 
                        corr_info["significance"] == "significant"):
                        strong_correlations.append((indicator1, indicator2, corr_info))
            
            if strong_correlations:
                insights.append("Indicadores fortemente correlacionados podem ser usados para previsões e monitoramento conjunto")
        
        # Insights baseados em clusters
        if self.clusters and "metadata" in self.clusters:
            silhouette = self.clusters["metadata"]["silhouette_score"]
            if silhouette > 0.5:
                insights.append("Indicadores agrupam-se em padrões comportamentais distintos, permitindo análise temática eficiente")
        
        # Insights baseados em anomalias
        if self.anomalies:
            total_anomalies = sum(len(anom_list) for anom_list in self.anomalies.values())
            if total_anomalies > 0:
                insights.append(f"Detectadas {total_anomalies} anomalias que requerem investigação e possíveis ações corretivas")
        
        # Insights gerais
        insights.extend([
            "Monitoramento integrado de indicadores permite identificação precoce de tendências",
            "Análise de correlações ajuda a entender relações de causa-efeito entre variáveis",
            "Detecção de anomalias suporta gestão proativa e preventiva"
        ])
        
        return insights

# Funções de conveniência
def analyze_indicator_insights(indicators_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """
    Função de conveniência para análise completa de insights.
    
    Args:
        indicators_data: Dicionário com DataFrames dos indicadores
        
    Returns:
        Dicionário completo com insights analíticos
    """
    analyzer = InsightsAnalyzer()
    return analyzer.generate_insights_summary(indicators_data)

def get_correlation_matrix(indicators_data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Gera matriz de correlações entre indicadores.
    
    Args:
        indicators_data: Dicionário com DataFrames dos indicadores
        
    Returns:
        DataFrame com matriz de correlações
    """
    analyzer = InsightsAnalyzer()
    aligned_data = analyzer._align_indicators_by_year(indicators_data, min_periods=3)
    
    if not aligned_data:
        return pd.DataFrame()
    
    # Criar DataFrame e calcular correlações
    df = pd.DataFrame(aligned_data)
    correlation_matrix = df.corr(method='pearson')
    
    return correlation_matrix

def identify_leading_indicators(indicators_data: Dict[str, pd.DataFrame], 
                               target_indicator: str) -> List[Tuple[str, float, float]]:
    """
    Identifica indicadores líderes (leading indicators) para um indicador alvo.
    
    Args:
        indicators_data: Dicionário com DataFrames dos indicadores
        target_indicator: Nome do indicador alvo
        
    Returns:
        Lista de tuplas (indicador, correlação, p-value)
    """
    analyzer = InsightsAnalyzer()
    correlations = analyzer.analyze_correlations(indicators_data)
    
    leading_indicators = []
    
    if target_indicator in correlations:
        for indicator, corr_info in correlations[target_indicator].items():
            if corr_info["significance"] == "significant":
                leading_indicators.append((
                    indicator,
                    corr_info["pearson_correlation"],
                    corr_info["pearson_p_value"]
                ))
    
    # Ordenar por magnitude da correlação
    leading_indicators.sort(key=lambda x: abs(x[1]), reverse=True)
    
    return leading_indicators
