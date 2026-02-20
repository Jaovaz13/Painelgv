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
    """Aplica CSS customizado para tornar o Streamlit visualmente institucional."""
    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
        /* ── Base ─────────────────────────────────────────── */
        html, body, [class*="st-"] {{
            font-family: 'Outfit', sans-serif !important;
        }}
        .stApp {{
            background-color: #f1f5f9;
            background-image: radial-gradient(#cbd5e1 0.5px, transparent 0.5px);
            background-size: 24px 24px;
        }}

        /* ── Cards de KPI (st.metric) ─────────────────────── */
        [data-testid="stMetric"] {{
            background-color: {COLORS["white"]};
            border: 1px solid {COLORS["border"]};
            padding: 20px 18px;
            border-radius: 14px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.07);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        [data-testid="stMetric"]:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 20px rgba(30, 58, 138, 0.1);
        }}
        [data-testid="stMetricValue"] {{
            font-size: 2.1rem !important;
            font-weight: 700 !important;
            color: {COLORS["text_dark"]} !important;
            letter-spacing: -0.02em;
        }}
        [data-testid="stMetricLabel"] {{
            color: {COLORS["text_muted"]} !important;
            font-size: 0.88rem !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}
        [data-testid="stMetricDelta"] {{
            font-size: 0.85rem !important;
            font-weight: 600 !important;
        }}

        /* ── Títulos ──────────────────────────────────────── */
        h1 {{
            color: {COLORS["primary"]} !important;
            font-weight: 800 !important;
            font-family: 'Outfit', sans-serif !important;
        }}
        h2, h3 {{
            color: {COLORS["text_dark"]} !important;
            font-weight: 700 !important;
            font-family: 'Outfit', sans-serif !important;
        }}

        /* ── Gráficos ─────────────────────────────────────── */
        .stPlotlyChart {{
            background: {COLORS["white"]};
            padding: 16px;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }}

        /* ── Sidebar ──────────────────────────────────────── */
        section[data-testid="stSidebar"] {{
            background-color: {COLORS["primary"]} !important;
        }}
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {{
            color: #e2e8f0 !important;
        }}
        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stRadio label {{
            color: #cbd5e1 !important;
        }}
        section[data-testid="stSidebar"] .stTitle {{
            color: {COLORS["white"]} !important;
        }}

        /* ── Botões ───────────────────────────────────────── */
        .stButton > button {{
            border-radius: 8px;
            background-color: {COLORS["primary"]};
            color: {COLORS["white"]};
            border: none;
            font-weight: 600;
            transition: background-color 0.25s, box-shadow 0.25s;
        }}
        .stButton > button:hover {{
            background-color: #1d4ed8;
            box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
        }}

        /* ── Tabs ─────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 20px;
            border-bottom: 2px solid {COLORS["border"]};
        }}
        .stTabs [data-baseweb="tab"] {{
            height: 48px;
            background-color: transparent;
            border-radius: 6px 6px 0 0;
            padding: 10px 16px;
            font-weight: 600;
            color: {COLORS["text_muted"]};
        }}
        .stTabs [aria-selected="true"] {{
            color: {COLORS["primary"]} !important;
            border-bottom: 3px solid {COLORS["primary"]} !important;
        }}

        /* ── Divisores ────────────────────────────────────── */
        hr {{
            margin: 2em 0 !important;
            border: 0;
            height: 1px;
            background-image: linear-gradient(
                to right,
                rgba(0, 0, 0, 0),
                {COLORS["border"]},
                rgba(0, 0, 0, 0)
            );
        }}

        /* ── Caption / Notas metodológicas ───────────────── */
        .stCaption {{
            color: {COLORS["text_muted"]} !important;
            font-size: 0.78rem !important;
            font-style: italic;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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
