"""
visual_components_v2.py – Design system institucional v2.
Prefeitura de Governador Valadares / Observatório de Dados.

Funções principais:
    apply_custom_css()           – Injeta CSS premium no app Streamlit.
    plotly_institutional_theme() – Aplica tema de cores ao Figure Plotly.
    render_kpi_grid()            – Grade moderna de KPIs com st.metric.
"""

import streamlit as st


# ---------------------------------------------------------------------------
# Paleta institucional
# ---------------------------------------------------------------------------
COLORS = {
    "primary":   "#1e3a8a",   # Azul GV
    "secondary": "#60a5fa",   # Azul claro
    "white":     "#ffffff",
    "bg":        "#f8fafc",
    "border":    "#e2e8f0",
    "text_dark": "#0f172a",
    "text_muted": "#64748b",
    "success":   "#15803d",
    "danger":    "#dc2626",
    "warning":   "#d97706",
}


def apply_custom_css() -> None:
    """Injeta CSS premium para a identidade visual institucional."""
    st.markdown(f"""
<style>
/* ── Base ─────────────────────────────────────────── */
html, body, [class*="st-"] {{ font-family: 'Outfit', sans-serif !important; }}
.stApp {{ background-color: #f1f5f9; }}

/* ── Cards de KPI ────────────────────────────────── */
[data-testid="stMetric"] {{
    background-color: {COLORS["white"]};
    border: 1px solid {COLORS["border"]};
    padding: 18px;
    border-radius: 14px;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
}}
[data-testid="stMetricValue"] {{ font-size: 2.1rem !important; font-weight: 700 !important; color: {COLORS["text_dark"]} !important; }}
[data-testid="stMetricLabel"] {{ color: {COLORS["text_muted"]} !important; font-size: 0.88rem !important; font-weight: 600 !important; text-transform: uppercase; }}

/* ── Títulos e Sidebar ───────────────────────────── */
h1 {{ color: {COLORS["primary"]} !important; font-weight: 800 !important; }}
section[data-testid="stSidebar"] {{ background-color: {COLORS["primary"]} !important; }}
section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label {{ color: #ffffff !important; }}

/* ── Gráficos e Tabs ─────────────────────────────── */
.stPlotlyChart {{ background: #ffffff; padding: 16px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
.stTabs [aria-selected="true"] {{ color: {COLORS["primary"]} !important; border-bottom: 2px solid {COLORS["primary"]} !important; }}
</style>
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

def plotly_institutional_theme(fig, title: str = "", source: str = ""):
    """
    Aplica o tema de cores institucional (Azul #1e3a8a / Azul Claro #60a5fa / Branco)
    a um Figure do Plotly.

    Args:
        fig:    Figure Plotly a ser estilizado.
        title:  Título principal do gráfico (opcional).
        source: Fonte dos dados exibida no subtítulo (opcional).

    Returns:
        Figure com layout atualizado.
    """
    title_text = f"<b>{title}</b>" if title else ""
    if source:
        title_text += (
            f"<br><span style='font-size:11px;color:{COLORS['text_muted']};'>"
            f"Fonte: {source}</span>"
        )

    fig.update_layout(
        title={
            "text": title_text,
            "x": 0,
            "xanchor": "left",
            "y": 0.97,
            "yanchor": "top",
            "font": {"size": 15, "color": COLORS["primary"], "family": "Outfit, sans-serif"},
        },
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font={
            "family": "Outfit, sans-serif",
            "color": COLORS["primary"],
            "size": 12,
        },
        margin=dict(l=20, r=20, t=55, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color=COLORS["text_muted"]),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=COLORS["white"],
            font_size=12,
            font_family="Outfit, sans-serif",
            bordercolor=COLORS["border"],
        ),
    )

    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        linecolor=COLORS["border"],
        tickfont=dict(size=11, color=COLORS["text_muted"]),
        title_text=None,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#f1f5f9",
        zeroline=False,
        linecolor=COLORS["white"],
        tickfont=dict(size=11, color=COLORS["text_muted"]),
        title_text=None,
    )

    # Aplica cor primária em barras e linhas sem cor definida
    fig.update_traces(
        marker_color=COLORS["primary"],
        selector=dict(type="bar"),
    )
    fig.update_traces(
        line=dict(color=COLORS["primary"], width=2),
        marker=dict(color=COLORS["primary"], size=6),
        selector=dict(type="scatter", mode="lines+markers"),
    )
    fig.update_traces(
        line=dict(color=COLORS["primary"], width=2),
        selector=dict(type="scatter", mode="lines"),
    )

    return fig


def render_kpi_grid(col_data: list) -> None:
    """
    Renderiza uma grade horizontal de KPIs usando st.metric nativo do Streamlit,
    com o CSS institucional aplicado via apply_custom_css().

    Args:
        col_data: Lista de dicts com as chaves:
            - 'label'  (str)  – Rótulo do indicador.
            - 'value'  (str)  – Valor formatado para exibição.
            - 'delta'  (str | None) – Variação (ex: '+5.2%'), opcional.
            - 'help'   (str | None) – Tooltip de ajuda, opcional.

    Exemplo:
        render_kpi_grid([
            {'label': 'PIB Total', 'value': 'R$ 8,4 bi', 'delta': '+3,1%'},
            {'label': 'Empregos', 'value': '183.420', 'delta': None},
        ])
    """
    if not col_data:
        return

    cols = st.columns(len(col_data))
    for col, data in zip(cols, col_data):
        with col:
            st.metric(
                label=data.get("label", ""),
                value=data.get("value", "—"),
                delta=data.get("delta"),
                help=data.get("help"),
            )
