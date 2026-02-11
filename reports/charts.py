"""
Geração padronizada de gráficos para relatórios e apresentações.
Implementa design consistente com cores institucionais.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Matplotlib para exportar PNG (necessário para Word e PPT)
import matplotlib
matplotlib.use("Agg")  # backend não-interativo
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)

# Configuração de design institucional
BRAND_COLORS = {
    "primary": "#1e3a8a",      # Blue 900
    "secondary": "#3b82f6",    # Blue 500
    "success": "#16a34a",      # Green 600
    "warning": "#d97706",      # Orange 600
    "error": "#dc2626",        # Red 600
    "neutral": "#64748b",      # Slate 500
    "background": "#f8fafc",   # Slate 50
    "text": "#0f172a",         # Slate 900
}

# Paleta de cores para gráficos
CHART_COLORS = [
    BRAND_COLORS["primary"],
    BRAND_COLORS["secondary"], 
    BRAND_COLORS["success"],
    BRAND_COLORS["warning"],
    BRAND_COLORS["error"],
    "#8b5cf6",  # Purple
    "#06b6d4",  # Cyan
    "#10b981",  # Emerald
]

class ChartGenerator:
    """Gerador de gráficos padronizados com design institucional."""
    
    def __init__(self, style_config: Optional[Dict] = None):
        """
        Inicializa o gerador com configuração de estilo.
        
        Args:
            style_config: Configurações customizadas de estilo
        """
        self.style_config = style_config or self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Retorna configuração padrão de estilo."""
        return {
            "figure_size": (10, 6),
            "dpi": 300,
            "font_family": "Arial",
            "title_size": 14,
            "label_size": 12,
            "tick_size": 10,
            "legend_size": 10,
            "line_width": 2.5,
            "marker_size": 6,
            "alpha": 0.8,
            "grid_alpha": 0.3
        }

    def _apply_mpl_style(self) -> None:
        """Aplica estilo básico ao Matplotlib."""
        plt.rcParams.update(
            {
                "font.family": self.style_config.get("font_family", "Arial"),
                "axes.titlesize": self.style_config.get("title_size", 14),
                "axes.labelsize": self.style_config.get("label_size", 12),
                "xtick.labelsize": self.style_config.get("tick_size", 10),
                "ytick.labelsize": self.style_config.get("tick_size", 10),
                "figure.dpi": self.style_config.get("dpi", 300),
            }
        )

    def _ensure_output_dir(self, output_path: Optional[str | Path]) -> Optional[Path]:
        if not output_path:
            return None
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    
    def create_line_chart(self, data: pd.DataFrame, x_col: str, y_col: str, 
                         title: str, xlabel: str = "", ylabel: str = "",
                         output_path: Optional[str] = None) -> Optional[Path]:
        """
        Cria gráfico de linha padrão e salva como PNG.
        
        Args:
            data: DataFrame com dados
            x_col: Nome da coluna X
            y_col: Nome da coluna Y
            title: Título do gráfico
            xlabel: Label do eixo X
            ylabel: Label do eixo Y
            output_path: Caminho para salvar o gráfico
            
        Returns:
            Path do arquivo salvo ou None se não for possível criar gráfico real
        """
        if data is None or data.empty or x_col not in data.columns or y_col not in data.columns:
            return None

        df = data[[x_col, y_col]].dropna()
        if df.empty or len(df) < 2:
            return None

        out = self._ensure_output_dir(output_path)
        if out is None:
            return None

        self._apply_mpl_style()

        fig, ax = plt.subplots(figsize=self.style_config.get("figure_size", (10, 6)))
        ax.plot(
            df[x_col],
            df[y_col],
            color=BRAND_COLORS["primary"],
            linewidth=self.style_config.get("line_width", 2.5),
            marker="o",
            markersize=self.style_config.get("marker_size", 6),
            alpha=self.style_config.get("alpha", 0.9),
        )
        ax.set_title(title)
        ax.set_xlabel(xlabel or x_col)
        ax.set_ylabel(ylabel or y_col)
        ax.grid(True, alpha=self.style_config.get("grid_alpha", 0.3))

        # Garantir ticks legíveis
        try:
            ax.set_xticks(sorted(df[x_col].unique()))
        except Exception:
            pass

        fig.tight_layout()
        fig.savefig(out, dpi=self.style_config.get("dpi", 300))
        plt.close(fig)
        return out
    
    def create_bar_chart(self, data: pd.DataFrame, x_col: str, y_col: str,
                        title: str, xlabel: str = "", ylabel: str = "",
                        horizontal: bool = False,
                        output_path: Optional[str] = None) -> Optional[Path]:
        """Cria gráfico de barras padrão e salva como PNG."""
        if data is None or data.empty or x_col not in data.columns or y_col not in data.columns:
            return None
        df = data[[x_col, y_col]].dropna()
        if df.empty:
            return None

        out = self._ensure_output_dir(output_path)
        if out is None:
            return None

        self._apply_mpl_style()
        fig, ax = plt.subplots(figsize=self.style_config.get("figure_size", (10, 6)))

        if horizontal:
            ax.barh(df[x_col].astype(str), df[y_col], color=BRAND_COLORS["secondary"], alpha=0.9)
            ax.set_xlabel(ylabel or y_col)
            ax.set_ylabel(xlabel or x_col)
        else:
            ax.bar(df[x_col].astype(str), df[y_col], color=BRAND_COLORS["secondary"], alpha=0.9)
            ax.set_xlabel(xlabel or x_col)
            ax.set_ylabel(ylabel or y_col)

        ax.set_title(title)
        ax.grid(True, axis="y", alpha=self.style_config.get("grid_alpha", 0.3))
        fig.tight_layout()
        fig.savefig(out, dpi=self.style_config.get("dpi", 300))
        plt.close(fig)
        return out
    
    def create_pie_chart(self, data: pd.DataFrame, labels_col: str, values_col: str,
                        title: str, output_path: Optional[str] = None) -> Optional[Path]:
        """Cria gráfico de pizza padrão e salva como PNG."""
        if data is None or data.empty or labels_col not in data.columns or values_col not in data.columns:
            return None
        df = data[[labels_col, values_col]].dropna()
        if df.empty:
            return None

        out = self._ensure_output_dir(output_path)
        if out is None:
            return None

        self._apply_mpl_style()
        fig, ax = plt.subplots(figsize=self.style_config.get("figure_size", (10, 6)))
        labels = df[labels_col].astype(str).tolist()
        values = df[values_col].tolist()

        colors = CHART_COLORS[: max(1, len(values))]
        ax.pie(values, labels=labels, autopct="%1.1f%%", colors=colors)
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(out, dpi=self.style_config.get("dpi", 300))
        plt.close(fig)
        return out
    
    def create_area_chart(self, data: pd.DataFrame, x_col: str, y_col: str,
                         title: str, xlabel: str = "", ylabel: str = "",
                         output_path: Optional[str] = None) -> Optional[Path]:
        """Cria gráfico de área padrão e salva como PNG."""
        if data is None or data.empty or x_col not in data.columns or y_col not in data.columns:
            return None
        df = data[[x_col, y_col]].dropna()
        if df.empty or len(df) < 2:
            return None

        out = self._ensure_output_dir(output_path)
        if out is None:
            return None

        self._apply_mpl_style()
        fig, ax = plt.subplots(figsize=self.style_config.get("figure_size", (10, 6)))
        ax.fill_between(df[x_col], df[y_col], color=BRAND_COLORS["primary"], alpha=0.25)
        ax.plot(df[x_col], df[y_col], color=BRAND_COLORS["primary"], linewidth=self.style_config.get("line_width", 2.5))
        ax.set_title(title)
        ax.set_xlabel(xlabel or x_col)
        ax.set_ylabel(ylabel or y_col)
        ax.grid(True, alpha=self.style_config.get("grid_alpha", 0.3))
        fig.tight_layout()
        fig.savefig(out, dpi=self.style_config.get("dpi", 300))
        plt.close(fig)
        return out
    
    def create_combo_chart(self, data: pd.DataFrame, x_col: str, y1_col: str, y2_col: str,
                          title: str, xlabel: str = "", y1_label: str = "", y2_label: str = "",
                          output_path: Optional[str] = None) -> Optional[Path]:
        """Cria gráfico combinado (duas séries) e salva como PNG."""
        if (
            data is None
            or data.empty
            or x_col not in data.columns
            or y1_col not in data.columns
            or y2_col not in data.columns
        ):
            return None

        df = data[[x_col, y1_col, y2_col]].dropna()
        if df.empty or len(df) < 2:
            return None

        out = self._ensure_output_dir(output_path)
        if out is None:
            return None

        self._apply_mpl_style()
        fig, ax1 = plt.subplots(figsize=self.style_config.get("figure_size", (10, 6)))
        ax1.plot(df[x_col], df[y1_col], color=BRAND_COLORS["primary"], label=y1_label or y1_col)
        ax1.set_xlabel(xlabel or x_col)
        ax1.set_ylabel(y1_label or y1_col, color=BRAND_COLORS["primary"])
        ax1.tick_params(axis="y", labelcolor=BRAND_COLORS["primary"])

        ax2 = ax1.twinx()
        ax2.plot(df[x_col], df[y2_col], color=BRAND_COLORS["secondary"], label=y2_label or y2_col)
        ax2.set_ylabel(y2_label or y2_col, color=BRAND_COLORS["secondary"])
        ax2.tick_params(axis="y", labelcolor=BRAND_COLORS["secondary"])

        ax1.set_title(title)
        ax1.grid(True, alpha=self.style_config.get("grid_alpha", 0.3))
        fig.tight_layout()
        fig.savefig(out, dpi=self.style_config.get("dpi", 300))
        plt.close(fig)
        return out
    
    def create_comparison_chart(self, data_dict: Dict[str, pd.DataFrame], 
                               x_col: str, y_col: str, title: str,
                               output_path: Optional[str] = None) -> Optional[Path]:
        """Cria gráfico comparativo (múltiplas séries) e salva como PNG."""
        if not data_dict:
            return None

        out = self._ensure_output_dir(output_path)
        if out is None:
            return None

        self._apply_mpl_style()
        fig, ax = plt.subplots(figsize=self.style_config.get("figure_size", (10, 6)))

        plotted = 0
        for idx, (name, df) in enumerate(data_dict.items()):
            if df is None or df.empty or x_col not in df.columns or y_col not in df.columns:
                continue
            dff = df[[x_col, y_col]].dropna()
            if dff.empty or len(dff) < 2:
                continue
            color = CHART_COLORS[idx % len(CHART_COLORS)]
            ax.plot(dff[x_col], dff[y_col], marker="o", linewidth=2, label=name, color=color)
            plotted += 1

        if plotted == 0:
            plt.close(fig)
            return None

        ax.set_title(title)
        ax.set_xlabel(x_col)
        ax.set_ylabel(y_col)
        ax.grid(True, alpha=self.style_config.get("grid_alpha", 0.3))
        ax.legend(fontsize=self.style_config.get("legend_size", 10))
        fig.tight_layout()
        fig.savefig(out, dpi=self.style_config.get("dpi", 300))
        plt.close(fig)
        return out

# Funções de conveniência
def create_standard_chart(chart_type: str, data: pd.DataFrame, **kwargs) -> Path:
    """
    Cria gráfico padrão baseado no tipo.
    
    Args:
        chart_type: Tipo do gráfico (line, bar, pie, area, combo)
        data: DataFrame com dados
        **kwargs: Argumentos específicos do gráfico
        
    Returns:
        Path do arquivo salvo
    """
    generator = ChartGenerator()
    
    chart_methods = {
        "line": generator.create_line_chart,
        "bar": generator.create_bar_chart,
        "pie": generator.create_pie_chart,
        "area": generator.create_area_chart,
        "combo": generator.create_combo_chart,
        "comparison": generator.create_comparison_chart
    }
    
    if chart_type not in chart_methods:
        raise ValueError(f"Tipo de gráfico não suportado: {chart_type}")
    
    return chart_methods[chart_type](data, **kwargs)

def create_thematic_charts(theme_data: Dict[str, pd.DataFrame], 
                          output_dir: Path) -> Dict[str, Optional[Path]]:
    """
    Cria múltiplos gráficos para um tema específico.
    
    Args:
        theme_data: Dicionário com dados do tema
        output_dir: Diretório para salvar os gráficos
        
    Returns:
        Dicionário com paths dos gráficos gerados
    """
    generator = ChartGenerator()
    chart_paths = {}
    
    for indicator_name, df in theme_data.items():
        if df.empty or len(df) < 2:
            chart_paths[indicator_name] = None
            continue
        
        # Determinar tipo de gráfico baseado no indicador
        chart_type = determine_chart_type(indicator_name, df)
        
        # Gerar nome do arquivo
        chart_filename = f"{indicator_name.lower().replace(' ', '_')}.png"
        chart_path = output_dir / chart_filename
        
        # Criar gráfico
        try:
            if chart_type == "line":
                chart_paths[indicator_name] = generator.create_line_chart(
                    df, "Ano", "Valor", f"Evolução de {indicator_name}",
                    output_path=chart_path
                )
            elif chart_type == "bar":
                chart_paths[indicator_name] = generator.create_bar_chart(
                    df, "Ano", "Valor", f"{indicator_name} por Ano",
                    output_path=chart_path
                )
            elif chart_type == "area":
                chart_paths[indicator_name] = generator.create_area_chart(
                    df, "Ano", "Valor", f"{indicator_name} - Tendência",
                    output_path=chart_path
                )
            elif chart_type == "pie":
                chart_paths[indicator_name] = generator.create_pie_chart(
                    df, "Ano", "Valor", f"{indicator_name} por Ano",
                    output_path=chart_path
                )
            else:
                chart_paths[indicator_name] = generator.create_line_chart(
                    df, "Ano", "Valor", f"Evolução de {indicator_name}",
                    output_path=chart_path
                )
        except Exception as e:
            logger.error(f"Erro ao criar gráfico para {indicator_name}: {e}")
            chart_paths[indicator_name] = None
    
    return chart_paths

def determine_chart_type(indicator_name: str, data: pd.DataFrame) -> str:
    """
    Determina o tipo mais adequado de gráfico para o indicador.
    
    Args:
        indicator_name: Nome do indicador
        data: DataFrame com dados
        
    Returns:
        Tipo de gráfico recomendado
    """
    # Heurística simples para determinar tipo de gráfico
    name_lower = indicator_name.lower()
    
    if any(keyword in name_lower for keyword in ["composição", "distribuição", "participação"]):
        return "pie"
    elif any(keyword in name_lower for keyword in ["comparativo", "comparação", "vs"]):
        return "comparison"
    elif any(keyword in name_lower for keyword in ["acumulado", "estoque", "total"]):
        return "area"
    elif len(data) <= 5:
        return "bar"
    else:
        return "line"
