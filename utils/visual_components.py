import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

def metric_card(label: str, value: str, sublabel: str = "", border_color: str = "#2563eb"):
    """
    Componente visual customizado para exibir métricas (KPIs) com identidade visual institucional.
    """
    st.markdown(f"""
    <div style="
        background: white; 
        padding: 24px; 
        border-radius: 12px; 
        border-left: 5px solid {border_color}; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        transition: transform 0.2s;
    ">
        <div style="font-size: 0.85rem; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em;">
            {label}
        </div>
        <div style="font-size: 2rem; color: #0f172a; font-weight: 700; margin: 8px 0;">
            {value}
        </div>
        <div style="font-size: 0.85rem; color: #94a3b8; font-weight: 500;">
            {sublabel}
        </div>
    </div>
    """, unsafe_allow_html=True)

def apply_institutional_layout(fig, title: str = "", source: str = ""):
    """
    Aplica o layout padrão institucional (Azul Marinho/Cinza) a gráficos Plotly.
    """
    # Paleta de cores institucional (Blue 900 base)
    MAIN_COLOR = "#1e3a8a"  # blue-900
    SECONDARY_COLOR = "#64748b" # slate-500
    GRID_COLOR = "#e2e8f0" # slate-200
    
    fig.update_layout(
        title={
            'text': f"<b>{title}</b><br><span style='font-size: 12px; color: gray;'>Fonte: {source}</span>",
            'y': 0.95,
            'x': 0,
            'xanchor': 'left',
            'yanchor': 'top'
        },
        font={'family': "Outfit, sans-serif", 'color': "#1e293b"},
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=40, r=40, t=80, b=40),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            linecolor=SECONDARY_COLOR,
            tickfont=dict(size=12, color=SECONDARY_COLOR),
            title=None
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=GRID_COLOR,
            zeroline=False,
            linecolor="white",
            tickfont=dict(size=12, color=SECONDARY_COLOR),
            title=None,
            tickprefix="   " # padding
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title=None,
            font=dict(size=11, color=SECONDARY_COLOR)
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13,
            font_family="Outfit, sans-serif"
        )
    )
    
    # Atualizar traces para usar a cor institucional se não definida
    fig.update_traces(marker_color=MAIN_COLOR, selector=dict(type='bar'))
    fig.update_traces(line_color=MAIN_COLOR, selector=dict(type='line'))
    
    return fig
