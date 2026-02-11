"""
Estrutura institucional padronizada para relatórios e apresentações.
Define seções, schemas e configurações de layout.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

class ReportSection(Enum):
    """Seções padronizadas do relatório institucional."""
    INSTITUCIONAL = "institucional"
    EXECUTIVO = "executivo"
    ECONOMIA = "economia"
    TRABALHO_RENDA = "trabalho_renda"
    EDUCACAO = "educacao"
    SAUDE = "saude"
    SUSTENTABILIDADE = "sustentabilidade"
    COMPARACOES = "comparacoes"
    CONCLUSOES = "conclusoes"
    METODOLOGIA = "metodologia"

class SlideType(Enum):
    """Tipos de slides para apresentação."""
    CAPA = "capa"
    MENSAGEM_CHAVE = "mensagem_chave"
    PANORAMA = "panorama"
    TEMA = "tema"
    TENDENCIAS = "tendencias"
    OPORTUNIDADES = "oportunidades"
    ENCAMINHAMENTO = "encaminhamento"

@dataclass
class SectionSchema:
    """Schema padrão para cada seção do relatório."""
    title: str
    intro: str = ""
    key_indicators: List[str] = None
    tables: List[Dict[str, Any]] = None
    charts: List[Dict[str, Any]] = None
    analysis: str = ""
    notes: List[str] = None
    insights: List[str] = None
    
    def __post_init__(self):
        if self.key_indicators is None:
            self.key_indicators = []
        if self.tables is None:
            self.tables = []
        if self.charts is None:
            self.charts = []
        if self.notes is None:
            self.notes = []
        if self.insights is None:
            self.insights = []

@dataclass
class SlideSchema:
    """Schema padrão para cada slide da apresentação."""
    type: SlideType
    title: str
    subtitle: str = ""
    main_message: str = ""
    chart_type: str = "line"  # line, bar, pie, area
    data_source: str = ""
    insights: List[str] = None
    call_to_action: str = ""
    
    def __post_init__(self):
        if self.insights is None:
            self.insights = []

# Configuração das seções do relatório
REPORT_SECTIONS = {
    ReportSection.INSTITUCIONAL: SectionSchema(
        title="Bloco A – Institucional",
        intro="Apresentação institucional do município com contexto e escopo da análise.",
        key_indicators=["municipio", "populacao", "territorio"],
        notes=[
            "Relatório gerado automaticamente pelo Observatório Socioeconômico",
            "Dados atualizados até a data de emissão deste documento"
        ]
    ),
    
    ReportSection.EXECUTIVO: SectionSchema(
        title="Bloco B – Executivo",
        intro="Síntese dos principais indicadores e tendências para tomada de decisão.",
        key_indicators=["pib_total", "empregos_formais", "idsc_geral"],
        insights=[
            "Principais destaques do período analisado",
            "Pontos de atenção e áreas críticas",
            "Tendências gerais consolidadas"
        ]
    ),
    
    ReportSection.ECONOMIA: SectionSchema(
        title="Bloco C – Análise Temática: Economia",
        intro="Análise detalhada dos indicadores econômicos do município.",
        key_indicators=["pib_total", "pib_per_capita", "vaf", "empresas_ativas"],
        charts=[
            {"type": "line", "indicator": "pib_total", "title": "Evolução do PIB"},
            {"type": "bar", "indicator": "empresas_ativas", "title": "Empresas Ativas"}
        ]
    ),
    
    ReportSection.TRABALHO_RENDA: SectionSchema(
        title="Bloco C – Análise Temática: Trabalho e Renda",
        intro="Mercado de trabalho formal e indicators de renda.",
        key_indicators=["empregos_formais", "salario_medio", "empreendedorismo"],
        charts=[
            {"type": "line", "indicator": "empregos_caged", "title": "Estoque de Empregos"},
            {"type": "area", "indicator": "salario_medio", "title": "Evolução Salarial"}
        ]
    ),
    
    ReportSection.EDUCACAO: SectionSchema(
        title="Bloco C – Análise Temática: Educação",
        intro="Indicadores educacionais e capital humano.",
        key_indicators=["matriculas_escolares", "qualificacao"],
        charts=[
            {"type": "bar", "indicator": "matriculas_total", "title": "Matrículas Escolares"}
        ]
    ),
    
    ReportSection.SAUDE: SectionSchema(
        title="Bloco C – Análise Temática: Saúde",
        intro="Indicadores de saúde e bem-estar da população.",
        key_indicators=["mortalidade_infantil", "acesso_saude"],
        charts=[
            {"type": "line", "indicator": "mortalidade_infantil", "title": "Mortalidade Infantil"}
        ]
    ),
    
    ReportSection.SUSTENTABILIDADE: SectionSchema(
        title="Bloco E – Sustentabilidade e Desenvolvimento",
        intro="Índices compostos de sustentabilidade e desenvolvimento territorial.",
        key_indicators=["idsc_geral", "emissoes_gee", "uso_solo"],
        charts=[
            {"type": "line", "indicator": "idsc_geral", "title": "IDSC-BR Score"},
            {"type": "pie", "indicator": "uso_solo", "title": "Composição do Uso do Solo"}
        ]
    ),
    
    ReportSection.COMPARACOES: SectionSchema(
        title="Bloco D – Comparações e Tendências",
        intro="Análise comparativa entre indicadores e projeções.",
        key_indicators=["crescimento_percentual", "correlacoes"],
        charts=[
            {"type": "combo", "indicator": "comparativo_eixos", "title": "Evolução Comparativa"}
        ]
    ),
    
    ReportSection.CONCLUSOES: SectionSchema(
        title="Bloco F – Conclusões Estratégicas",
        intro="Síntese automática das análises e recomendações estratégicas.",
        insights=[
            "Síntese integrada dos indicadores analisados",
            "Oportunidades identificadas para o desenvolvimento",
            "Alertas e recomendações para gestão municipal"
        ]
    ),
    
    ReportSection.METODOLOGIA: SectionSchema(
        title="Bloco G – Metodologia e Transparência",
        intro="Fontes de dados, métodos de análise e limitações técnicas.",
        notes=[
            "Fontes: IBGE, SEFAZ-MG, SEBRAE, SEEG, MapBiomas, INEP, DataSUS",
            "Métodos: Análise de tendência, projeções estatísticas, correlações",
            "Atualização: Dados coletados automaticamente das fontes oficiais"
        ]
    )
}

# Configuração dos slides da apresentação
PRESENTATION_SLIDES = {
    SlideType.CAPA: SlideSchema(
        type=SlideType.CAPA,
        title="Observatório Socioeconômico",
        subtitle="Resumo Executivo Institucional",
        main_message="Análise integrada para desenvolvimento sustentável"
    ),
    
    SlideType.MENSAGEM_CHAVE: SlideSchema(
        type=SlideType.MENSAGEM_CHAVE,
        title="Mensagem-Chave",
        subtitle="Principais destaques estratégicos",
        main_message="3 insights essenciais para tomada de decisão",
        call_to_action="Foco em oportunidades de crescimento"
    ),
    
    SlideType.PANORAMA: SlideSchema(
        type=SlideType.PANORAMA,
        title="Panorama Geral",
        subtitle="Visão macro do município",
        chart_type="combo",
        data_source="múltiplas fontes",
        insights=[
            "Posicionamento relativo nos indicadores-chave",
            "Principais vetores de desenvolvimento",
            "Desafios estruturais identificados"
        ]
    ),
    
    SlideType.TEMA: [
        SlideSchema(
            type=SlideType.TEMA,
            title="Economia",
            subtitle="PIB e estrutura produtiva",
            chart_type="line",
            data_source="IBGE/SEFAZ-MG",
            insights=["Crescimento econômico sustentável", "Diversificação produtiva"]
        ),
        SlideSchema(
            type=SlideType.TEMA,
            title="Trabalho e Renda",
            subtitle="Mercado formal e empreendedorismo",
            chart_type="area",
            data_source="CAGED/RAIS/SEBRAE",
            insights=["Geração de empregos", "Massa salarial em expansão"]
        ),
        SlideSchema(
            type=SlideType.TEMA,
            title="Capital Humano",
            subtitle="Educação e saúde",
            chart_type="bar",
            data_source="INEP/DataSUS",
            insights=["Investimento em capital humano", "Qualidade de vida"]
        ),
        SlideSchema(
            type=SlideType.TEMA,
            title="Sustentabilidade",
            subtitle="Desenvolvimento sustentável",
            chart_type="pie",
            data_source="IDSC/SEEG/MapBiomas",
            insights=["Equilíbrio ambiental", "Desenvolvimento consciente"]
        )
    ],
    
    SlideType.TENDENCIAS: SlideSchema(
        type=SlideType.TENDENCIAS,
        title="Tendências e Projeções",
        subtitle="Cenários futuros e oportunidades",
        chart_type="forecast",
        data_source="modelos estatísticos",
        insights=[
            "Tendências de médio prazo",
            "Projeções baseadas em modelos",
            "Cenários otimista e pessimista"
        ],
        call_to_action="Preparar o futuro hoje"
    ),
    
    SlideType.OPORTUNIDADES: SlideSchema(
        type=SlideType.OPORTUNIDADES,
        title="Oportunidades Estratégicas",
        subtitle="Áreas prioritárias de investimento",
        chart_type="bubble",
        data_source="análise integrada",
        insights=[
            "Setores com maior potencial",
            "Investimentos prioritários",
            "Parcerias estratégicas"
        ],
        call_to_action="Agir nas oportunidades identificadas"
    ),
    
    SlideType.ENCAMINHAMENTO: SlideSchema(
        type=SlideType.ENCAMINHAMENTO,
        title="Próximos Passos",
        subtitle="Agenda estratégica",
        main_message="Transformar dados em ação",
        call_to_action="Implementar plano de desenvolvimento"
    )
}

def create_empty_report_structure() -> Dict[ReportSection, SectionSchema]:
    """Cria estrutura vazia do relatório com schemas padrão."""
    return {section: schema.copy() for section, schema in REPORT_SECTIONS.items()}

def create_presentation_structure() -> List[SlideSchema]:
    """Cria estrutura completa da apresentação."""
    slides = [PRESENTATION_SLIDES[SlideType.CAPA]]
    slides.append(PRESENTATION_SLIDES[SlideType.MENSAGEM_CHAVE])
    slides.append(PRESENTATION_SLIDES[SlideType.PANORAMA])
    slides.extend(PRESENTATION_SLIDES[SlideType.TEMA])
    slides.append(PRESENTATION_SLIDES[SlideType.TENDENCIAS])
    slides.append(PRESENTATION_SLIDES[SlideType.OPORTUNIDADES])
    slides.append(PRESENTATION_SLIDES[SlideType.ENCAMINHAMENTO])
    return slides

# Configurações de design
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

TYPOGRAPHY = {
    "title_font": "Outfit",
    "title_size": 32,
    "subtitle_font": "Outfit",
    "subtitle_size": 24,
    "body_font": "Outfit",
    "body_size": 14,
    "caption_font": "Outfit",
    "caption_size": 12
}

LAYOUT_CONFIG = {
    "margin": 1.0,           # polegadas
    "spacing": 1.5,          # linhas
    "max_chars_per_line": 80,
    "max_lines_per_slide": 6,
    "chart_height": 4.0,     # polegadas
    "chart_width": 6.0       # polegadas
}
