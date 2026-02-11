def _build_thematic_blocks_by_groups(self, indicators_data: Dict[str, pd.DataFrame]):
        """Constrói blocos temáticos organizados por grupos estratégicos."""
        # Organizar indicadores por grupos
        organized_indicators = organize_indicators_by_groups(list(indicators_data.keys()))
        
        # Construir blocos para cada grupo temático
        for group_name, indicator_list in organized_indicators.items():
            if not indicator_list:
                continue
                
            group_config = INDICATOR_GROUPS.get(group_name, {})
            group_title = group_config.get("title", group_name.title())
            group_description = group_config.get("description", "")
            
            # Título do grupo temático
            block_letter = chr(68 + len(organized_indicators) - organized_indicators.keys().index(group_name))  # D, E, F, etc.
            self._add_custom_heading(f"BLOCO {block_letter} – {group_title}", 1, BRAND_COLORS["primary"])
            
            # Descrição do grupo
            if group_description:
                self._format_paragraph(group_description)
            
            # Analisar indicadores do grupo
            for indicator in indicator_list:
                if indicator in indicators_data:
                    self._build_indicator_analysis(indicator, indicators_data[indicator])
            
            self._add_section_break()
    
    def _build_indicator_analysis(self, indicator_name: str, data: pd.DataFrame):
        """Constrói análise individual de um indicador."""
        # Título do indicador
        self._add_custom_heading(f"Análise: {indicator_name}", 2)
        
        # Tabela de dados
        headers = ["Ano", "Valor", "Variação %"]
        table_data = []
        
        for i, row in data.iterrows():
            year = int(row["Ano"])
            value = row["Valor"]
            
            # Calcular variação percentual
            if i > 0:
                prev_value = data.iloc[i-1]["Valor"]
                if prev_value != 0:
                    var_pct = ((value - prev_value) / prev_value) * 100
                    var_str = f"{var_pct:+.1f}%"
                else:
                    var_str = "N/A"
            else:
                var_str = "—"
            
            table_data.append([year, f"{value:,.2f}", var_str])
        
        # Inverter ordem para mostrar mais recente primeiro
        table_data = table_data[::-1]
        self._create_styled_table(headers, table_data, 'Table Grid')
        
        # Análise de tendência
        try:
            analysis = TrendAnalyzer.analyze_trend(data["Valor"])
            
            # Melhorar interpretação
            enhanced_interpretation = text_enhancer.enhance_text(analysis.get("interpretation", ""))
            
            # Formatar análise
            self._format_paragraph("**Análise de Tendência:**")
            self._format_paragraph(f"Direção: {analysis.get('direction', 'estável').title()}")
            self._format_paragraph(f"Força: {analysis.get('strength', 0):.2f}")
            self._format_paragraph(f"Confiança: {analysis.get('confidence', 0):.2f}")
            self._format_paragraph(f"Interpretação: {enhanced_interpretation}")
            
            # Adicionar gráfico
            chart_path = self.charts_dir / f"{indicator_name}_trend.png"
            self.chart_generator.create_line_chart(
                data, "Ano", "Valor", f"Evolução de {indicator_name}",
                output_path=str(chart_path)
            )
            self._add_chart_image(chart_path, width=6.0)
            
        except Exception as e:
            logger.error(f"Erro na análise de {indicator_name}: {e}")
            self._format_paragraph("*Dados insuficientes para análise de tendência*")
        
        self._format_paragraph("")  # Espaçamento
