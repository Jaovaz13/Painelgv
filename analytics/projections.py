"""
Módulo de projeções e cenários para indicadores socioeconômicos.
Implementa modelos estatísticos para previsão e análise de cenários.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any, Union
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from scipy import stats
import logging

logger = logging.getLogger(__name__)

class ProjectionModel:
    """Classe base para modelos de projeção."""
    
    def __init__(self, model_type: str = "linear"):
        """
        Inicializa o modelo de projeção.
        
        Args:
            model_type: Tipo de modelo ('linear', 'polynomial')
        """
        self.model_type = model_type
        self.is_fitted = False
        self.feature_names = []
        self.training_X = None
        self.training_y = None
        
    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: List[str] = None):
        """
        Treina o modelo de projeção.
        
        Args:
            X: Features de treinamento
            y: Variável alvo
            feature_names: Nomes das features
        """
        if feature_names:
            self.feature_names = feature_names
        
        self.training_X = X
        self.training_y = y
        self.is_fitted = True
        
        logger.info(f"Model {self.model_type} trained successfully")
    
    def predict(self, X: np.ndarray, return_confidence: bool = False) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
        """
        Realiza previsões.
        
        Args:
            X: Features para previsão
            return_confidence: Se True, retorna intervalos de confiança
            
        Returns:
            Previsões e opcionalmente intervalos de confiança
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making predictions")
        
        if self.model_type == "linear":
            predictions = self._predict_linear(X)
        elif self.model_type == "polynomial":
            predictions = self._predict_polynomial(X)
        else:
            raise ValueError(f"Model type not supported: {self.model_type}")
        
        if not return_confidence:
            return predictions
        
        # Calcular intervalos de confiança simplificados
        residuals = self.training_y - self._predict_linear(self.training_X)
        std_error = np.std(residuals)
        margin_error = 1.96 * std_error
        lower_bound = predictions - margin_error
        upper_bound = predictions + margin_error
        
        return predictions, lower_bound, upper_bound
    
    def _predict_linear(self, X: np.ndarray) -> np.ndarray:
        """Previsão usando regressão linear."""
        predictions = []
        
        for i in range(X.shape[1]):  # Para cada feature
            x_values = X[:, i]
            y_values = self.training_y
            
            # Regressão linear simples
            slope, intercept, _, _, _ = stats.linregress(x_values, y_values)
            pred = slope * x_values + intercept
            predictions.append(pred)
        
        return np.mean(predictions, axis=0)
    
    def _predict_polynomial(self, X: np.ndarray, degree: int = 2) -> np.ndarray:
        """Previsão usando regressão polinomial."""
        predictions = []
        
        for i in range(X.shape[1]):  # Para cada feature
            x_values = X[:, i]
            y_values = self.training_y
            
            # Ajustar polinômio
            coeffs = np.polyfit(x_values, y_values, degree)
            pred = np.polyval(coeffs, x_values)
            predictions.append(pred)
        
        return np.mean(predictions, axis=0)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """
        Retorna importância das features.
        
        Returns:
            Dicionário com importância de cada feature
        """
        if not self.is_fitted:
            return {}
        
        importance = {}
        for i, name in enumerate(self.feature_names):
            if i < self.training_X.shape[1]:
                x_values = self.training_X[:, i]
                correlation = np.corrcoef(x_values, self.training_y)[0, 1]
                importance[name] = abs(correlation) if not np.isnan(correlation) else 0.0
        
        return importance

class TimeSeriesProjection(ProjectionModel):
    """Modelo de projeção para séries temporais."""
    
    def __init__(self, model_type: str = "linear", lags: int = 3):
        """
        Inicializa o modelo de séries temporais.
        
        Args:
            model_type: Tipo de modelo
            lags: Número de lags a usar como features
        """
        super().__init__(model_type)
        self.lags = lags
        self.training_X = None
        self.training_y = None
    
    def prepare_features(self, data: pd.Series) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara features usando lags da série temporal.
        
        Args:
            data: Série temporal
            
        Returns:
            Tupla com features (X) e alvo (y)
        """
        if len(data) <= self.lags:
            raise ValueError(f"Data length ({len(data)}) must be greater than lags ({self.lags})")
        
        X, y = [], []
        
        for i in range(self.lags, len(data)):
            # Usar lags como features
            lag_values = data.iloc[i-self.lags:i].values
            X.append(lag_values)
            y.append(data.iloc[i])
        
        return np.array(X), np.array(y)
    
    def fit(self, data: pd.Series, feature_names: List[str] = None):
        """
        Treina o modelo com dados da série temporal.
        
        Args:
            data: Série temporal com índice temporal
            feature_names: Nomes das features (lags)
        """
        if feature_names is None:
            feature_names = [f"lag_{i+1}" for i in range(self.lags)]
        
        X, y = self.prepare_features(data)
        self.training_X = X
        self.training_y = y
        
        super().fit(X, y, feature_names)
    
    def forecast(self, data: pd.Series, periods: int = 3, 
                return_confidence: bool = True) -> pd.DataFrame:
        """
        Realiza projeção para períodos futuros.
        
        Args:
            data: Série temporal histórica
            periods: Número de períodos para projetar
            return_confidence: Se True, inclui intervalos de confiança
            
        Returns:
            DataFrame com projeções
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before making forecasts")
        
        # Preparar último valor conhecido
        last_values = data.iloc[-self.lags:].values.reshape(1, -1)
        
        forecasts = []
        current_values = last_values.copy()
        
        for i in range(periods):
            # Fazer previsão
            if return_confidence:
                pred, lower, upper = self.predict(current_values, return_confidence=True)
                forecasts.append({
                    "period": i + 1,
                    "prediction": pred[0],
                    "lower_bound": lower[0],
                    "upper_bound": upper[0]
                })
            else:
                pred = self.predict(current_values, return_confidence=False)
                forecasts.append({
                    "period": i + 1,
                    "prediction": pred[0]
                })
            
            # Atualizar valores para próxima previsão
            current_values = np.roll(current_values, -1)
            current_values[0, -1] = pred[0]
        
        # Criar DataFrame
        forecast_df = pd.DataFrame(forecasts)
        
        # Adicionar datas se o índice original for temporal
        if hasattr(data.index, 'freq') or isinstance(data.index, pd.DatetimeIndex):
            last_date = data.index[-1]
            if hasattr(last_date, 'year'):
                # Assumir dados anuais
                future_dates = [last_date + pd.DateOffset(years=i+1) for i in range(periods)]
                forecast_df["date"] = future_dates
                forecast_df.set_index("date", inplace=True)
        
        return forecast_df
    
    def _get_training_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Retorna dados de treinamento."""
        return self.training_X, self.training_y

class ScenarioAnalyzer:
    """Analisador de cenários para projeções."""
    
    def __init__(self):
        """Inicializa o analisador de cenários."""
        self.projections = {}
        self.scenarios = {}
    
    def create_scenarios(self, historical_data: pd.Series, 
                        base_projection: pd.DataFrame,
                        scenarios_config: Dict[str, Dict[str, float]]) -> Dict[str, pd.DataFrame]:
        """
        Cria múltiplos cenários de projeção.
        
        Args:
            historical_data: Dados históricos
            base_projection: Projeção base
            scenarios_config: Configuração dos cenários
            
        Returns:
            Dicionário com DataFrames de cada cenário
        """
        scenarios = {}
        
        for scenario_name, config in scenarios_config.items():
            scenario_df = base_projection.copy()
            
            # Aplicar ajustes do cenário
            for adjustment_type, adjustment_value in config.items():
                if adjustment_type == "growth_factor":
                    scenario_df["prediction"] *= adjustment_value
                elif adjustment_type == "additive_adjustment":
                    scenario_df["prediction"] += adjustment_value
                elif adjustment_type == "volatility_factor":
                    # Aumentar volatilidade dos intervalos de confiança
                    if "lower_bound" in scenario_df.columns:
                        margin = scenario_df["prediction"] - scenario_df["lower_bound"]
                        scenario_df["lower_bound"] = scenario_df["prediction"] - margin * adjustment_value
                        scenario_df["upper_bound"] = scenario_df["prediction"] + margin * adjustment_value
            
            scenarios[scenario_name] = scenario_df
        
        self.scenarios = scenarios
        return scenarios
    
    def compare_scenarios(self, scenarios: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Compara múltiplos cenários.
        
        Args:
            scenarios: Dicionário com cenários
            
        Returns:
            DataFrame comparativo
        """
        if not scenarios:
            return pd.DataFrame()
        
        # Combinar todos os cenários
        comparison_data = []
        
        for scenario_name, df in scenarios.copy().items():
            df_temp = df.copy()
            df_temp["scenario"] = scenario_name
            comparison_data.append(df_temp)
        
        comparison_df = pd.concat(comparison_data, ignore_index=True)
        
        # Pivotar para comparação
        if "period" in comparison_df.columns:
            pivot_df = comparison_df.pivot(index="period", columns="scenario", values="prediction")
            return pivot_df
        
        return comparison_df
    
    def calculate_scenario_risks(self, scenarios: Dict[str, pd.DataFrame]) -> Dict[str, Dict[str, float]]:
        """
        Calcula métricas de risco para cada cenário.
        
        Args:
            scenarios: Dicionário com cenários
            
        Returns:
            Dicionário com métricas de risco
        """
        risk_metrics = {}
        
        for scenario_name, df in scenarios.items():
            metrics = {}
            
            if "prediction" in df.columns:
                predictions = df["prediction"].values
                
                # Volatilidade (desvio padrão)
                metrics["volatility"] = np.std(predictions)
                
                # Tendência (slope da regressão linear)
                x = np.arange(len(predictions))
                slope, _, _, _, _ = stats.linregress(x, predictions)
                metrics["trend_slope"] = slope
                
                # Crescimento médio
                if len(predictions) > 1:
                    growth_rates = np.diff(predictions) / predictions[:-1]
                    metrics["avg_growth_rate"] = np.mean(growth_rates)
                else:
                    metrics["avg_growth_rate"] = 0.0
                
                # Risco (volatilidade * tendência negativa)
                metrics["risk_score"] = metrics["volatility"] * max(0, -metrics["trend_slope"])
            
            risk_metrics[scenario_name] = metrics
        
        return risk_metrics

class ProjectionEngine:
    """Motor integrado de projeções e cenários."""
    
    def __init__(self):
        """Inicializa o motor de projeções."""
        self.models = {}
        self.projections = {}
        self.scenario_analyzer = ScenarioAnalyzer()
    
    def create_projection_model(self, indicator_name: str, data: pd.Series,
                             model_type: str = "linear", lags: int = 3) -> TimeSeriesProjection:
        """
        Cria e treina modelo de projeção para um indicador.
        
        Args:
            indicator_name: Nome do indicador
            data: Série temporal do indicador
            model_type: Tipo de modelo
            lags: Número de lags
            
        Returns:
            Modelo treinado
        """
        if len(data) < lags + 2:
            logger.warning(f"Insufficient data for {indicator_name}: {len(data)} points")
            return None
        
        model = TimeSeriesProjection(model_type=model_type, lags=lags)
        
        try:
            model.fit(data)
            self.models[indicator_name] = model
            logger.info(f"Projection model created for {indicator_name}")
            return model
        except Exception as e:
            logger.error(f"Error creating model for {indicator_name}: {e}")
            return None
    
    def project_indicator(self, indicator_name: str, data: pd.Series,
                        periods: int = 3, model_type: str = "linear") -> Optional[pd.DataFrame]:
        """
        Projeta um indicador para períodos futuros.
        
        Args:
            indicator_name: Nome do indicador
            data: Série temporal histórica
            periods: Número de períodos para projetar
            model_type: Tipo de modelo
            
        Returns:
            DataFrame com projeções
        """
        model = self.create_projection_model(indicator_name, data, model_type)
        
        if model is None:
            return None
        
        try:
            projection = model.forecast(data, periods=periods, return_confidence=True)
            self.projections[indicator_name] = projection
            return projection
        except Exception as e:
            logger.error(f"Error projecting {indicator_name}: {e}")
            return None
    
    def create_multiple_scenarios(self, indicator_name: str, historical_data: pd.Series,
                               base_projection: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Cria múltiplos cenários para um indicador.
        
        Args:
            indicator_name: Nome do indicador
            historical_data: Dados históricos
            base_projection: Projeção base
            
        Returns:
            Dicionário com cenários
        """
        # Configurações padrão de cenários
        scenarios_config = {
            "otimista": {
                "growth_factor": 1.10,  # 10% acima da projeção base
                "volatility_factor": 0.8   # 20% menos volatilidade
            },
            "base": {
                "growth_factor": 1.00,  # Projeção base
                "volatility_factor": 1.0
            },
            "pessimista": {
                "growth_factor": 0.90,  # 10% abaixo da projeção base
                "volatility_factor": 1.2   # 20% mais volatilidade
            }
        }
        
        scenarios = self.scenario_analyzer.create_scenarios(
            historical_data, base_projection, scenarios_config
        )
        
        return scenarios
    
    def validate_projections(self, indicator_name: str, historical_data: pd.Series,
                           test_size: int = 2) -> Dict[str, float]:
        """
        Valida projeções usando backtesting.
        
        Args:
            indicator_name: Nome do indicador
            historical_data: Dados históricos completos
            test_size: Tamanho do conjunto de teste
            
        Returns:
            Métricas de validação
        """
        if len(historical_data) <= test_size + 3:
            return {"error": "Insufficient data for validation"}
        
        # Separar dados de treino e teste
        train_data = historical_data.iloc[:-test_size]
        test_data = historical_data.iloc[-test_size:]
        
        # Criar modelo com dados de treino
        model = self.create_projection_model(indicator_name, train_data)
        
        if model is None:
            return {"error": "Failed to create validation model"}
        
        # Fazer projeções para o período de teste
        try:
            projections = model.forecast(train_data, periods=test_size, return_confidence=False)
            
            # Calcular métricas
            actual_values = test_data.values
            predicted_values = projections["prediction"].values
            
            mae = mean_absolute_error(actual_values, predicted_values)
            mse = mean_squared_error(actual_values, predicted_values)
            rmse = np.sqrt(mse)
            mape = np.mean(np.abs((actual_values - predicted_values) / actual_values)) * 100
            
            return {
                "mae": mae,
                "mse": mse,
                "rmse": rmse,
                "mape": mape,
                "validation_points": test_size
            }
        except Exception as e:
            return {"error": f"Validation failed: {str(e)}"}
    
    def generate_projection_report(self, indicators_data: Dict[str, pd.Series],
                                 periods: int = 3) -> Dict[str, Any]:
        """
        Gera relatório completo de projeções.
        
        Args:
            indicators_data: Dicionário com séries temporais
            periods: Períodos para projeção
            
        Returns:
            Relatório completo de projeções
        """
        report = {
            "projections": {},
            "scenarios": {},
            "validation": {},
            "summary": {}
        }
        
        for indicator_name, data in indicators_data.items():
            if data.empty or len(data) < 5:
                continue
            
            # Projeção base
            projection = self.project_indicator(indicator_name, data, periods)
            
            if projection is not None:
                report["projections"][indicator_name] = projection
                
                # Cenários
                scenarios = self.create_multiple_scenarios(indicator_name, data, projection)
                report["scenarios"][indicator_name] = scenarios
                
                # Validação
                validation = self.validate_projections(indicator_name, data)
                report["validation"][indicator_name] = validation
        
        # Resumo geral
        total_projections = len(report["projections"])
        successful_validations = sum(1 for v in report["validation"].values() 
                                   if "error" not in v)
        
        report["summary"] = {
            "total_indicators": total_projections,
            "successful_validations": successful_validations,
            "projection_periods": periods,
            "generated_at": datetime.now().isoformat()
        }
        
        return report

# Funções de conveniência
def project_indicator_series(data: pd.Series, periods: int = 3,
                           model_type: str = "linear") -> Optional[pd.DataFrame]:
    """
    Função de conveniência para projetar uma série temporal.
    
    Args:
        data: Série temporal
        periods: Períodos para projetar
        model_type: Tipo de modelo
        
    Returns:
        DataFrame com projeções
    """
    engine = ProjectionEngine()
    return engine.project_indicator("temp_indicator", data, periods, model_type)

def create_standard_scenarios(base_projection: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Cena cenários padrão (otimista, base, pessimista).
    
    Args:
        base_projection: Projeção base
        
    Returns:
        Dicionário com cenários
    """
    analyzer = ScenarioAnalyzer()
    
    scenarios_config = {
        "otimista": {"growth_factor": 1.10, "volatility_factor": 0.8},
        "base": {"growth_factor": 1.00, "volatility_factor": 1.0},
        "pessimista": {"growth_factor": 0.90, "volatility_factor": 1.2}
    }
    
    return analyzer.create_scenarios(pd.Series(), base_projection, scenarios_config)
