"""
Utilitários de formatação institucional compatível com ABNT (NBR 14724) para DOCX.

Observação:
- ABNT é um conjunto de normas; aqui aplicamos os elementos mais objetivos e
  recorrentes para relatórios: margens, fonte, espaçamento, recuo e alinhamento.
- Não cria conteúdo simulado; apenas formata o documento.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from docx.document import Document as _Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt


@dataclass(frozen=True)
class AbntDocxConfig:
    font_name: str = "Times New Roman"
    font_size_pt: int = 12
    line_spacing: float = 1.5
    first_line_indent_cm: float = 1.25
    margin_top_cm: float = 3.0
    margin_bottom_cm: float = 2.0
    margin_left_cm: float = 3.0
    margin_right_cm: float = 2.0


def apply_abnt_styles(doc: _Document, config: Optional[AbntDocxConfig] = None) -> None:
    """Aplica estilos ABNT básicos ao documento."""
    cfg = config or AbntDocxConfig()

    # Margens
    for section in doc.sections:
        section.top_margin = Cm(cfg.margin_top_cm)
        section.bottom_margin = Cm(cfg.margin_bottom_cm)
        section.left_margin = Cm(cfg.margin_left_cm)
        section.right_margin = Cm(cfg.margin_right_cm)

    # Estilo Normal
    normal = doc.styles["Normal"]
    normal.font.name = cfg.font_name
    normal.font.size = Pt(cfg.font_size_pt)
    normal.paragraph_format.line_spacing = cfg.line_spacing
    normal.paragraph_format.first_line_indent = Cm(cfg.first_line_indent_cm)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    # Títulos (Heading 1..3) – simples e compatível
    for style_name in ("Heading 1", "Heading 2", "Heading 3"):
        if style_name not in doc.styles:
            continue
        st = doc.styles[style_name]
        st.font.name = cfg.font_name
        st.font.bold = True
        st.font.size = Pt(12 if style_name in ("Heading 1", "Heading 2") else 12)
        st.paragraph_format.first_line_indent = Cm(0)
        st.paragraph_format.space_before = Pt(12 if style_name == "Heading 1" else 6)
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.line_spacing = cfg.line_spacing
        st.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def add_figure_caption(doc: _Document, *, figure_number: int, title: str, source: str) -> None:
    """
    Adiciona legenda de figura e fonte, em formato institucional (ABNT).
    Exemplo:
      Figura 1 – Evolução do PIB Municipal (R$ mil).
      Fonte: IBGE. Elaboração: Painel GV. Acesso em: dd/mm/aaaa.
    """
    p1 = doc.add_paragraph(f"Figura {figure_number} – {title}.")
    p1.paragraph_format.first_line_indent = Cm(0)
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p2 = doc.add_paragraph(f"Fonte: {source}.")
    p2.paragraph_format.first_line_indent = Cm(0)
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

