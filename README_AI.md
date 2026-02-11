# 🤖 AI Assistant Guidelines - Painel GV

Este arquivo fornece contexto estruturado para que assistentes de IA possam analisar e sugerir melhorias para este projeto.

## 🏗️ Arquitetura do Sistema
- **Frontend:** Streamlit (Python)
- **Backend:** PostgreSQL (Hospedado no Neon.tech)
- **ETL:** Automatizado via GitHub Actions (roda diariamente às 03:00 UTC)
- **Política de Dados:** 100% dados reais. Proibido o uso de dados simulados (Simulations prohibited).

## 🗄️ Esquema do Banco de Dados (PostgreSQL)
Tabela principal: `indicators`
- `municipality_code`: Código IBGE (Ex: 3127701)
- `indicator_key`: Chave técnica (Ex: PIB_TOTAL, RECEITA_VAF)
- `source`: Fonte oficial (IBGE, SEFAZ, RAIS, SEEG)
- `year`/`month`: Temporalidade
- `value`: Valor numérico (Float)

## 📊 Principais Indicadores e Chaves
- **Economia:** `PIB_TOTAL`, `PIB_PER_CAPITA`, `RECEITA_VAF`, `RECEITA_ICMS`
- **Trabalho:** `EMPREGOS_RAIS`, `SALARIO_MEDIO`, `NUM_EMPRESAS`
- **Sustentabilidade:** `EMISSOES_GEE`, `IDSC_GERAL`
- **Demografia:** `POPULACAO`, `GINI`, `IDHM`

## 🛠️ Como sugerir melhorias
Ao analisar este repositório, FOQUE em:
1. **Performance de Consultas SQL:** Verifique o arquivo `database.py`.
2. **Robustez dos ETLs:** Analise os scripts em `etl/` e verifique os mecanismos de fallback.
3. **UX/UI no Streamlit:** Sugira melhorias de layout no `panel/painel.py`.
4. **Novas Fontes de Dados:** Sugira APIs que usem o `municipality_code` (3127701) para expandir o observatório.

---
*Este projeto é o Observatório Socioeconômico de Governador Valadares/MG.*
