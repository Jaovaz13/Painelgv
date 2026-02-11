"""
Melhorador de Texto para Relatórios Institucionais
Implementa melhorias automáticas com linguagem institucional apropriada.
"""

import re
from typing import Dict, Optional

class TextEnhancer:
    """Melhora textos automáticos com linguagem institucional."""
    
    # Mapeamento de melhorias de texto
    ENHANCEMENTS = {
        # Crescimento
        "crescimento moderado": "crescimento moderado, indicando expansão econômica sustentada, porém sem aceleração significativa no período recente",
        "crescimento leve": "crescimento leve, sugerindo expansão econômica modesta com potencial de consolidação futura",
        "crescimento acentuado": "crescimento acentuado, demonstrando robustez econômica e dinamismo no período analisado",
        "crescimento consistente": "crescimento consistente, revelando padrão de desenvolvimento econômico estável e previsível",
        
        # Queda/Declínio
        "queda acentuada": "queda acentuada, sugerindo possível mudança metodológica, reclassificação da base de dados ou impacto conjuntural relevante, recomendando análise complementar",
        "queda moderada": "queda moderada, indicando ajuste econômico setorial ou temporal que merece acompanhamento contínuo",
        "queda leve": "queda leve, representando flutuação normal dentro do padrão histórico do indicador",
        "declínio acentuado": "declínio acentuado, podendo indicar reestruturação setorial ou necessidade de intervenções específicas",
        
        # Estabilidade
        "estável": "estável, demonstrando consolidação do indicador no patamar atual com baixa volatilidade",
        "relativamente estável": "relativamente estável, com variações dentro de margens aceitáveis que não comprometem a tendência geral",
        
        # Dados insuficientes
        "dados insuficientes": "o indicador não dispõe de série histórica suficiente para análise de tendência no período selecionado, o que limita inferências conclusivas",
        "dados insuficientes no período": "o indicador não dispõe de série histórica suficiente para análise de tendência no período selecionado, o que limita inferências conclusivas",
        "série histórica insuficiente": "série histórica insuficiente para análise estatística robusta, recomendando ampliação do período de observação",
        
        # Interpretações genéricas
        "tendência de crescimento": "tendência de crescimento, indicando trajetória expansionista com perspectivas positivas",
        "tendência de queda": "tendência de queda, sinalizando necessidade de atenção e possíveis ações corretivas",
        "tendência estável": "tendência estável, demonstrando equilíbrio e previsibilidade no comportamento do indicador",
        
        # Qualificações técnicas
        "significativo": "significativo, do ponto de vista estatístico e econômico",
        "relevante": "relevante para análise prospectiva e tomada de decisão",
        "notável": "notável, merecendo destaque no contexto geral do desempenho municipal"
    }
    
    # Padrões para substituição com contexto
    CONTEXT_PATTERNS = {
        r"queda.*?(-?\d+\.?\d*?)%": r"queda de \1%, representando variação substancial que requer análise detalhada das causas estruturais e conjunturais",
        r"crescimento.*?(-?\d+\.?\d*?)%": r"crescimento de \1%, indicando dinamismo econômico setorial com reflexos positivos na arrecadação e emprego",
        r"variação.*?(-?\d+\.?\d*?)%": r"variação de \1%, demonstrando movimento característico do indicador no período analisado"
    }
    
    def __init__(self):
        """Inicializa o melhorador de texto."""
        self.cache = {}
    
    def enhance_text(self, text: str, context: str = None) -> str:
        """
        Aplica melhorias no texto mantendo contexto institucional.
        
        Args:
            text: Texto original
            context: Contexto adicional (tipo de indicador, etc.)
            
        Returns:
            Texto melhorado com linguagem institucional
        """
        if text in self.cache:
            return self.cache[text]
        
        enhanced_text = text.lower()
        
        # Aplicar melhorias padrão
        for pattern, enhancement in self.ENHANCEMENTS.items():
            if pattern in enhanced_text:
                enhanced_text = enhanced_text.replace(pattern, enhancement)
                break  # Aplica apenas a primeira correspondência para evitar sobreposição
        
        # Aplicar padrões contextuais
        for pattern, replacement in self.CONTEXT_PATTERNS.items():
            enhanced_text = re.sub(pattern, replacement, enhanced_text, flags=re.IGNORECASE)
        
        # Ajustes finais de capitalização
        enhanced_text = self._fix_capitalization(enhanced_text)
        
        # Cache para melhor performance
        self.cache[text] = enhanced_text
        
        return enhanced_text
    
    def _fix_capitalization(self, text: str) -> str:
        """Ajusta capitalização do texto."""
        # Capitalizar primeira letra após pontuação
        sentences = re.split(r'([.!?]+)', text)
        
        for i in range(0, len(sentences), 2):
            if sentences[i].strip():
                sentences[i] = sentences[i][0].upper() + sentences[i][1:]
        
        return ''.join(sentences)
    
    def enhance_classification(self, classification: str, strength: float = None) -> str:
        """
        Melhora classificação de tendência com contexto.
        
        Args:
            classification: Classificação original (crescimento, queda, estável)
            strength: Força da tendência (0-1)
            
        Returns:
            Classificação melhorada
        """
        base_text = classification.lower()
        
        # Adicionar contexto de força
        if strength is not None:
            if strength > 0.7:
                qualifier = "acentuado"
            elif strength > 0.4:
                qualifier = "moderado"
            else:
                qualifier = "leve"
            
            base_text = f"{qualifier} {base_text}"
        
        return self.enhance_text(base_text)
    
    def enhance_insufficient_data(self, indicator_name: str = None) -> str:
        """
        Gera mensagem institucional para dados insuficientes.
        
        Args:
            indicator_name: Nome do indicador (opcional)
            
        Returns:
            Mensagem apropriada
        """
        base_message = "o indicador não dispõe de série histórica suficiente para análise de tendência no período selecionado"
        
        if indicator_name:
            base_message = f"O indicador {indicator_name} não dispõe de série histórica suficiente para análise conclusiva no período selecionado"
        
        base_message += ", o que limita inferências conclusivas sobre o comportamento temporal"
        
        return base_message.capitalize()
    
    def enhance_strong_decline(self, percentage: float = None, indicator: str = None) -> str:
        """
        Gera interpretação institucional para quedas fortes.
        
        Args:
            percentage: Percentual de queda
            indicator: Nome do indicador
            
        Returns:
            Interpretação apropriada
        """
        base_text = "queda acentuada, sugerindo possível mudança metodológica, reclassificação da base de dados ou impacto conjuntural relevante"
        
        if percentage:
            base_text += f", com variação de {abs(percentage):.1f}% que merece investigação detalhada"
        
        if indicator:
            base_text += f", recomendando análise complementar específica para {indicator}"
        
        base_text += " para compreensão adequada dos fatores determinantes"
        
        return base_text.capitalize()
    
    def enhance_executive_highlight(self, indicator: str, trend: str, strength: float, value: float = None) -> str:
        """
        Gera destaque para resumo executivo.
        
        Args:
            indicator: Nome do indicador
            trend: Tendência (crescimento, queda, estável)
            strength: Força da tendência
            value: Valor atual (opcional)
            
        Returns:
            Destaque formatado
        """
        # Determinar ícone baseado na tendência e força
        if trend == "crescimento" and strength > 0.5:
            icon = "✔"
            qualifier = "positivo"
        elif trend == "queda" and strength > 0.7:
            icon = "⚠"
            qualifier = "atenção"
        elif trend == "estável":
            icon = "●"
            qualifier = "estável"
        else:
            icon = "○"
            qualifier = "monitorar"
        
        # Construir mensagem
        message = f"{icon} {indicator}: desempenho {qualifier}"
        
        if value is not None:
            message += f" (valor atual: {value:.1f})"
        
        # Adicionar interpretação breve
        if trend == "crescimento":
            message += ", indicando expansão favorável"
        elif trend == "queda":
            message += ", requerendo acompanhamento prioritário"
        else:
            message += ", mantendo padrão consistente"
        
        return message

# Instância global do melhorador de texto
text_enhancer = TextEnhancer()
