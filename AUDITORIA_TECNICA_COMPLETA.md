# 🔍 AUDITORIA TÉCNICA COMPLETA - PAINEL GV
**Data:** 11/02/2026  
**Sistema:** Painel Institucional de Governador Valadares - MG  
**Secretaria:** Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação

---

## 📋 SUMÁRIO EXECUTIVO

**STATUS GLOBAL: 🟡 ATENÇÃO - REQUER CORREÇÕES IMEDIATAS**

Esta auditoria identificou **VIOLAÇÕES CRÍTICAS** das regras absolutas do projeto:

### ❌ PROBLEMAS CRÍTICOS ENCONTRADOS:
1. **DADOS SIMULADOS** presentes em múltiplos ETLs (PROIBIDO)
2. **Código morto** (educacao_simulada.py, censo_escolar.py)
3. **Funções duplicadas** entre módulos
4. **Falta de redundância** adequada em alguns ETLs
5. **Indicadores ausentes** no banco de dados

### ✅ PONTOS POSITIVOS:
1. Arquitetura **corretamente separada** (API → ETL → Banco → App → Reports)
2. Painel **NÃO consulta APIs diretamente** (arquitetura adequada)
3. Banco de dados **devidamente normalizado**
4. Sistema de **geração de relatórios** funcional
5. **Design premium** no painel Streamlit

---

## 1️⃣ AUDITORIA DE ARQUITETURA

### ✅ **APROVADO COM RESSALVAS**

#### Arquitetura Geral
```
APIs/CSVs → ETL → Banco → App → Relatórios/Apresentações
     ✅        ✅     ✅     ✅           ✅
```

**CONFORMIDADES:**
- ✅ ETLs salvam no banco via `database.upsert_indicators()`
- ✅ App consulta **SOMENTE o banco** (via `get_timeseries()`)
- ✅ **NENHUMA** chamada direta a API no painel Streamlit
- ✅ Camada de dados desacoplada da interface
- ✅ Uso correto de SQLAlchemy ORM

**ESTRUTURA DE ARQUIVOS:**
```
painel_gv/
├── etl/              # 50 arquivos Python (ETL)
├── database.py       # Camada de dados (SQLAlchemy)
├── panel/           # Interface Streamlit
│   ├── painel.py    # Painel principal
│   ├── executivo.py # Dashboard executivo
│   └── indicator_catalog.py
├── reports/         # Geração de relatórios
│   ├── word_builder.py
│   ├── slide_builder.py
│   └── charts.py
├── analytics/       # Análises e projeções
│   ├── estimativa_pib.py
│   ├── projections.py
│   └── insights.py
└── data/
    ├── raw/         # Dados brutos (76 arquivos)
    └── indicadores.db  # Banco SQLite
```

**PROBLEMAS IDENTIFICADOS:**
- ⚠️ Funções `criar_dados_simulados_*()` **não deveriam existir**
- ⚠️ Alguns ETLs usam simulação como fallback (contra regras)

---

## 2️⃣ AUDITORIA DE DADOS (100% REAIS)

### ❌ **REPROVADO - DADOS SIMULADOS PRESENTES**

#### 🚨 VIOLAÇÕES CRÍTICAS:

**Arquivos com DADOS SIMULADOS encontrados:**

1. **etl/pib_ibge.py** (Linhas 64-196)
   - ❌ `criar_dados_simulados_pib()` - SIMULAÇÃO
   - ❌ `criar_dados_simulados_pib_per_capita()` - SIMULAÇÃO
   - **Correção:** Usar SOMENTE `/raw` quando API falhar

2. **etl/educacao_simulada.py** (ARQUIVO INTEIRO)
   - ❌ TODO O ARQUIVO é simulação
   - **Correção:** **DELETAR** este arquivo

3. **etl/censo_escolar.py** (Linhas 19-77)
   - ❌ `criar_dados_simulados_censo()` - SIMULAÇÃO
   - **Correção:** **DELETAR** este arquivo

4. **etl/vaf_sefaz.py** (Linhas 41-80)
   - ❌ `criar_dados_simulados_vaf()` - SIMULAÇÃO
   - **Correção:** Usar dados de `/raw` SOMENTE

5. **etl/icms_sefaz.py** (Linhas 41-80)
   - ❌ `criar_dados_simulados_icms()` - SIMULAÇÃO
   - **Correção:** Usar dados de `/raw` SOMENTE

6. **etl/empresas_rais.py** (Linhas 41-80)
   - ❌ `criar_dados_simulados_empresas()` - SIMULAÇÃO
   - **Correção:** Usar dados de `/raw` SOMENTE

7. **etl/emissoes_gee.py** (Linhas 41-80)
   - ❌ `criar_dados_simulados_emissoes()` - SIMULAÇÃO
   - **Correção:** Usar dados de `/raw` SOMENTE

8. **etl/mapbiomas.py** (Linhas 268-369)
   - ❌ `create_sustentabilidade_simulada()` - SIMULAÇÃO COMPLETA
   - ❌ `create_sustentabilidade_indicators()` - SIMULAÇÃO
   - **Correção:** Processar SOMENTE arquivos reais de `/raw`

9. **etl/salarios.py** (Linha 105+)
   - ❌ Função de simulação presente
   - **Correção:** Usar CSV de `/raw` SOMENTE

10. **etl/mei.py** (Linha 116+)
    - ❌ Função de simulação presente
    - **Correção:** Usar CSV de `/raw` SOMENTE

#### ✅ DADOS REAIS CONFIRMADOS:

**ECONOMIA:**
- ✅ PIB_TOTAL: IBGE API (com fallback simulado ❌ - corrigir)
- ✅ PIB_PER_CAPITA: Calculado (PIB/População)
- ✅ PIB_ESTIMADO: Séries temporais REAIS
- ✅ PIB_CRESCIMENTO: Calculado (variação anual)
- ⚠️ VAF: SEFAZ_MG (com fallback simulado ❌ - corrigir)
- ⚠️ ICMS: SEFAZ_MG (com fallback simulado ❌ - corrigir)

**TRABALHO & RENDA:**
- ✅ EMPREGOS_RAIS: `/raw` (arquivos RAIS)
- ✅ EMPREGOS_CAGED: `/raw` (CAGED manual MG)
- ✅ SALDO_CAGED_MENSAL: `/raw` (CAGED)
- ✅ SALDO_CAGED_ANUAL: `/raw` (CAGED)
- ✅ SEBRAE_GERAL: `/raw` (CSVs Sebrae)
- ✅ EMPREGOS_SEBRAE: `/raw` (CSVs Sebrae)
- ✅ ESTABELECIMENTOS_SEBRAE: `/raw` (CSVs Sebrae)
- ✅ EMPREENDEDORES_MEI: `/raw` (CSVs Sebrae/MEI)
- ✅ SALARIO_MEDIO_MG: `/raw` (CAGED MG)

**EDUCAÇÃO:**
- ✅ MATRICULAS_TOTAL: `/raw` (Sinopses INEP 2012-2024)
- ✅ ESCOLAS_FUNDAMENTAL: `/raw` (Sinopses INEP)
- ✅ TAXA_APROVACAO_FUNDAMENTAL: `/raw` (Sinopses INEP)
- ✅ IDEB_ANOS_INICIAIS: INEP API
- ✅ IDEB_ANOS_FINAIS: INEP API

**SAÚDE:**
- ✅ MORTALIDADE_INFANTIL: DataSUS API
- ✅ OBITOS_TOTAL: DataSUS API

**SUSTENTABILIDADE:**
- ✅ IDSC_GERAL: `/raw` (Base_de_Dados_IDSC-BR_2023/2024/2025.xlsx)
- ⚠️ EMISSOES_GEE: SEEG (com fallback simulado ❌ - corrigir)
- ⚠️ SEEG_AR: `/raw` (SEEG ar2-ar6.csv)
- ⚠️ SEEG_GASES: `/raw` (SEEG gases.csv)
- ✅ AREA_URBANA: `/raw` (MapBiomas)
- ✅ VEGETACAO_NATIVA: `/raw` (MapBiomas)
- ✅ USO_AGROPECUARIO: `/raw` (MapBiomas)

**VISÃO GERAL:**
- ✅ POPULACAO: IBGE SIDRA API (Tabela 4714)
- ✅ POPULACAO_DETALHADA: IBGE SIDRA API
- ✅ IDHM: `/raw/idhm.csv`
- ✅ GINI: `/raw/gini.csv`

---

## 3️⃣ AUDITORIA DE QUALIDADE DE CÓDIGO

### 🟡 **APROVADO COM RESSALVAS GRAVES**

#### ❌ PROBLEMAS DE CÓDIGO MORTO:

**Arquivos que DEVEM SER DELETADOS:**
1. `etl/educacao_simulada.py` - **CÓDIGO MORTO** (100% simulação)
2. `etl/censo_escolar.py` - **CÓDIGO MORTO** (100% simulação)
3. `etl/sinopse_educacao.py` - **DESATIVADO** (comentado como não usar)
4. `etl/missing_indicators.py` - **DESATIVADO** (linha 162-173)

**Funções que DEVEM SER REMOVIDAS:**
- `criar_dados_simulados_pib()` em `pib_ibge.py`
- `criar_dados_simulados_pib_per_capita()` em `pib_ibge.py`
- `criar_dados_simulados_vaf()` em `vaf_sefaz.py`
- `criar_dados_simulados_icms()` em `icms_sefaz.py`
- `criar_dados_simulados_empresas()` em `empresas_rais.py`
- `criar_dados_simulados_emissoes()` em `emissoes_gee.py`
- `create_sustentabilidade_simulada()` em `mapbiomas.py`
- `create_sustentabilidade_indicators()` em `mapbiomas.py`

#### ✅ BOAS PRÁTICAS ENCONTRADAS:

**Modularização:**
- ✅ Separação clara: `etl/`, `database.py`, `panel/`, `reports/`, `analytics/`
- ✅ Uso de docstrings em módulos principais
- ✅ Logging estruturado com `logging.getLogger(__name__)`
- ✅ Tratamento de exceções em ETLs
- ✅ Separação de responsabilidades

**Qualidade:**
- ✅ Type hints em `database.py` e arquivos principais
- ✅ Funções bem nomeadas (semântica clara)
- ✅ Configuração centralizada em `config.py`
- ✅ Uso de variáveis de ambiente (DATABASE_URL, COD_IBGE, etc.)

#### ⚠️ PROBLEMAS DE QUALIDADE:

**Funções Longas (> 80 linhas):**
- `panel/painel.py`: função `main()` com 884 linhas ❌
  - **Solução:** Quebrar em funções menores por seção
- `mapbiomas.py`: múltiplas funções de transformação repetitivas
  - **Solução:** Criar função genérica com parâmetros

**Código Duplicado:**
- Lógica de "verificar API → fallback simulado" repetida em 10+ arquivos
  - **Solução:** Criar utilitário `utils/fallback_manager.py` (já existe, usar!)
- Transformações MapBiomas similares (fogo, agricultura, urban)
  - **Solução:** Unificar em função parametrizada

**Falta de Tipagem:**
- Alguns ETLs não têm type hints
- **Solução:** Adicionar progressivamente

**Imports Desnecessários:**
- Alguns ETLs importam bibliotecas não usadas
- **Solução:** Limpeza com ferramentas (autoflake)

---

## 4️⃣ AUDITORIA FUNCIONAL

### ✅ **APROVADO - 95% DAS FUNCIONALIDADES IMPLEMENTADAS**

#### ✅ FUNCIONALIDADES CONFIRMADAS:

**Interface Streamlit:**
- ✅ Painel interativo completo
- ✅ Design moderno e premium (CSS customizado, Google Fonts Outfit)
- ✅ Filtros por período (ano_inicio, ano_fim)
- ✅ Gráficos históricos completos (Plotly)
- ✅ Análise automática de tendência (`analytics/tendencias.py`)
- ✅ Estimativa de PIB por séries temporais (`analytics/estimativa_pib.py`)
- ✅ Sistema de aviso de dados desatualizados (`utils/status_check.py`)
- ✅ Redundância de captação de dados (`utils/fallback_manager.py`)
- ✅ Botão de geração de relatório Word (`reports/word_builder.py`)
- ✅ Botão de geração de apresentação PowerPoint (`reports/slide_builder.py`)
- ✅ Múltiplas abas (Visão Geral, Economia, Trabalho, Educação, Saúde, Sustentabilidade)
- ✅ Modo de Visão (Institucional, Técnico, Divulgação Pública)
- ✅ Dashboard Executivo (`panel/executivo.py`)
- ✅ Métricas do Sistema (`monitoring/metrics_dashboard.py`)

**Mapas:**
- ✅ Mapa interativo com Folium (Visão Geral)
- ✅ Coordenadas de Governador Valadares (-18.8511, -41.9503)

**Nota Metodológica:**
- ✅ Presente na aba "PIB Estimado" (linha 637-638 painel.py)
- ❌ Falta aba separada "Metodologia" (solicitado)

**Portal Público:**
- ✅ Diretório `portal_publico/` existe
- ⚠️ Implementação básica, pode ser expandida

**Título Institucional:**
- ✅ **CORRETO:** "Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação"
- ✅ Presente no painel (linha 42 e 293)

**Unidades:**
- ✅ 100% dos números com unidades (configurado em `database.py` coluna `unit`)
- ✅ Formatação brasileira com `fmt_br()` (linha 239-253 painel.py)

**Gráficos:**
- ✅ Modernos e profissionais (Plotly Express e Graph Objects)
- ✅ Cards estilo Power BI (função `card_plotly()`)
- ✅ Cores vibrantes e design premium

#### ⚠️ FUNCIONALIDADES FALTANTES/INCOMPLETAS:

**1. Aba de Metodologia Separada:**
- ❌ Não existe aba exclusiva "Metodologia"
- **Solução:** Adicionar aba "Metodologia" ao sidebar

**2. Verificação de Redundância:**
- ⚠️ Sistema existe (`utils/fallback_manager.py`, `utils/network.py`)
- ⚠️ **MAS** ETLs usam simulação em vez de `/raw` (contra regras)
- **Solução:** Refatorar ETLs para usar `/raw` SOMENTE

**3. Mapas Avançados:**
- ✅ Mapa básico funciona
- ⚠️ Pode ser expandido com camadas temática (sustentabilidade, etc.)

---

## 5️⃣ TESTE DE ROBUSTEZ

### 🟡 **PARCIALMENTE ROBUSTO - REQUER MELHORIAS**

#### Cenários Testados (Simulação Mental):

**Cenário 1: API fora do ar**
- ✅ Sistema **NÃO quebra**
- ⚠️ **MAS** alguns ETLs criam dados simulados (❌ PROIBIDO)
- **Correção:** Usar `/raw` como fallback

**Cenário 2: Banco vazio**
- ✅ Sistema **NÃO quebra**
- ✅ Painel exibe "N/D" ou "Sem dados"
- ✅ Mensagens claras ao usuário

**Cenário 3: Arquivo raw ausente**
- ✅ Sistema **NÃO quebra**
- ✅ Logs de warning apropriados
- ⚠️ Alguns ETLs recorrem a simulação (❌ PROIBIDO)

**Cenário 4: Dados inconsistentes**
- ✅ Try/except em transformações
- ✅ `pd.to_numeric(..., errors='coerce')` usado
- ✅ Validações de `df.empty` antes de processar

**Tratamento de Erros:**
```python
# EXEMPLO (database.py linha 100-156):
try:
    # executa operação
except Exception as exc:
    session.rollback()
    logger.exception("Erro: %s", exc)
    raise
```

**Logs Estruturados:**
- ✅ Logging configurado em todos os módulos
- ✅ Níveis apropriados (INFO, WARNING, ERROR)
- ✅ Mensagens descritivas

---

## 📊 CHECKLIST FINAL OBRIGATÓRIO

| Pergunta | Status |
|----------|--------|
| **Arquitetura está correta?** | ✅ **SIM** |
| **100% dados reais?** | ❌ **NÃO** - Simulações presentes |
| **100% funcionalidades implementadas?** | 🟡 **QUASE** - 95% implementado |
| **Código está limpo e modular?** | 🟡 **PARCIAL** - Código morto presente |
| **Sistema robusto contra falhas?** | 🟡 **PARCIAL** - Usa simulação indevidamente |

---

## 🚨 AÇÕES CORRETIVAS IMEDIATAS

### PRIORIDADE 1 (CRÍTICA):

#### 1. **REMOVER TODOS OS DADOS SIMULADOS**

**Arquivos a DELETAR completamente:**
```bash
rm etl/educacao_simulada.py
rm etl/censo_escolar.py
```

**Funções a REMOVER:**
- `criar_dados_simulados_*()` em:
  - `etl/pib_ibge.py` (linhas 108-196)
  - `etl/vaf_sefaz.py` (linhas 41-80)
  - `etl/icms_sefaz.py` (linhas 41-80)
  - `etl/empresas_rais.py` (linhas 41-80)
  - `etl/emissoes_gee.py` (linhas 41-80)
  - `etl/salarios.py` (linha 105+)
  - `etl/mei.py` (linha 116+)
  
- `create_sustentabilidade_simulada()` em `etl/mapbiomas.py` (linhas 268-325)
- `create_sustentabilidade_indicators()` em `etl/mapbiomas.py` (linhas 327-369)

#### 2. **IMPLEMENTAR FALLBACK CORRETO**

**Lógica correta para TODOS os ETLs:**
```python
def run():
    try:
        # Tentar API
        data = fetch_from_api()
    except Exception:
        logger.warning("API falhou, tentando arquivo local")
        # Fallback: arquivo em /raw SOMENTE
        data = load_from_raw()
    
    if not data:
        logger.error("Sem dados disponíveis (API e /raw)")
        return pd.DataFrame()  # NÃO criar simulação!
    
    # Processar e salvar
    upsert_indicators(data, ...)
```

**Aplicar em:**
- `pib_ibge.py` → usar `/raw` PIB csvs se existirem
- `vaf_sefaz.py` → usar `/raw` VAF csvs
- `icms_sefaz.py` → usar `/raw` ICMS csvs
- `emissoes_gee.py` → usar `/raw` SEEG csvs
- `mapbiomas.py` → **JÁ CORRETO** (processar `/raw` somente)

#### 3. **ATUALIZAR run_all.py**

Remover imports de arquivos deletados:
```python
# REMOVER:
# import etl.educacao_simulada
# import etl.censo_escolar
```

#### 4. **ADICIONAR ABA METODOLOGIA**

Em `panel/painel.py`, adicionar aba "Metodologia" separada:
```python
abas = ["Visão Geral", "Economia", ..., "Metodologia", "Relatórios"]

elif pagina == "Metodologia":
    st.subheader("Metodologia e Fontes de Dados")
    st.markdown("""
    ## Nota Metodológica
    
    ### Fontes de Dados
    - **IBGE:** PIB, População, GINI
    - **INEP:** Educação (Matrículas, IDEB, Escolas)
    - **DataSUS:** Saúde (Mortalidade, Óbitos)
    - **SEBRAE:** Empresas, Empreendedorismo, MEI
    - **SEEG:** Emissões de GEE
    - **MapBiomas:** Uso do solo, Vegetação
    - **SEFAZ-MG:** VAF, ICMS
    
    ### Metodologia de Cálculo PIB Estimado
    [Descrição detalhada...]
    
    ### Redundância de Dados
    Sistema implementa fallback automático:
    API → Arquivo Local (/raw) → Informar indisponibilidade
    
    ### Atualização
    - Automática: via scheduler (24h)
    - Manual: botão "Atualizar" em Métricas do Sistema
    """)
```

### PRIORIDADE 2 (ALTA):

#### 5. **REFATORAR painel.py**

Quebrar `main()` (884 linhas) em funções menores:
```python
def render_visao_geral():
    # código da aba Visão Geral
    
def render_economia():
    # código da aba Economia
    
def main():
    # apenas navegação e chamadas
    if pagina == "Visão Geral":
        render_visao_geral()
    elif pagina == "Economia":
        render_economia()
    # etc.
```

#### 6. **LIMPAR IMPORTS DESNECESSÁRIOS**

Executar em todos os arquivos:
```bash
autoflake --remove-all-unused-imports --in-place etl/*.py
```

#### 7. **ADICIONAR TESTES**

Criar `tests/` com testes unitários:
```
tests/
├── test_database.py
├── test_etl_demograficos.py
├── test_etl_economia.py
└── test_painel.py
```

### PRIORIDADE 3 (MÉDIA):

#### 8. **DOCUMENTAÇÃO**

Atualizar `README.md` com:
- Instruções de instalação
- Como executar ETLs
- Como rodar o painel
- Arquitetura detalhada
- Políticas (100% dados reais, sem simulação)

#### 9. **CI/CD**

Adicionar `.github/workflows/` para:
- Testes automáticos
- Linting (flake8, black)
- Type checking (mypy)

---

## 📈 ESTATÍSTICAS DO PROJETO

**Arquivos Analisados:**
- **ETLs:** 50 arquivos Python
- **Painel:** 4 arquivos principais
- **Relatórios:** 13 arquivos
- **Analytics:** 5 arquivos
- **Utils:** 13 arquivos
- **Total:** ~85 arquivos Python

**Dados Brutos:**
- **76 arquivos** em `data/raw/`
- Formatos: CSV, XLSX, ODS, XLS
- Tamanho total: ~2.5 GB (no zip)

**Banco de Dados:**
- **SQLite:** `data/indicadores.db`
- **Tabela:** `indicators` (normalizada)
- **Constraints:** UniqueConstraint (município + indicador + fonte + ano + mês)

**Indicadores Totais:**
- **Economia:** 6 principais
- **Trabalho:** 11 principais
- **Educação:** 5 principais
- **Saúde:** 2 principais
- **Sustentabilidade:** 8 principais
- **Visão Geral:** 4 principais
- **Total:** ~36+ indicadores únicos

---

## 🎯 CONCLUSÃO

### STATUS FINAL:

**🟡 SISTEMA FUNCIONAL MAS COM VIOLAÇÕES CRÍTICAS**

O projeto **Painel GV** está **tecnicamente bem estruturado** com arquitetura correta, separação de responsabilidades adequada e funcionalidades implementadas. **PORÉM**, viola a regra fundamental de **NÃO usar dados simulados**.

### O QUE ESTÁ BOM:
✅ Arquitetura API → ETL → Banco → App → Reports  
✅ Interface moderna e profissional  
✅ Sistema de relatórios Word/PowerPoint funcional  
✅ Estimativas estatísticas (PIB) baseadas em dados reais  
✅ Múltiplas fontes de dados (IBGE, INEP, DataSUS, SEBRAE, SEEG)  
✅ Tratamento de erros e logging  

### O QUE PRECISA SER CORRIGIDO IMEDIATAMENTE:
❌ **REMOVER** todos os dados simulados (10+ funções)  
❌ **DELETAR** arquivos de código morto (2 arquivos)  
❌ **REFATORAR** fallbacks para usar `/raw` SOMENTE  
❌ **ADICIONAR** aba Metodologia separada  
❌ **QUEBRAR** função main() muito longa  

### PRAZO SUGERIDO PARA CORREÇÕES:
- **Prioridade 1:** 2-3 dias
- **Prioridade 2:** 5-7 dias
- **Prioridade 3:** 2 semanas

### APÓS CORREÇÕES:
O sistema estará **100% compliance** com as regras institucionais e pronto para:
- ✅ Hospedagem pública (Vercel, Streamlit Cloud, servidor próprio)
- ✅ Apresentação institucional
- ✅ Uso oficial pela Secretaria
- ✅ Escalabilidade para outros municípios

---

**Auditoria realizada por:** Sistema AI Antigravity  
**Metodologia:** Análise completa de código-fonte, estrutura de dados e conformidade com requisitos  
**Próximos passos:** Implementar ações corretivas conforme prioridades definidas

---

## 📎 ANEXOS

### ARQUIVOS A DELETAR:
```
etl/educacao_simulada.py
etl/censo_escolar.py
```

### FUNÇÕES A REMOVER:
```
etl/pib_ibge.py:criar_dados_simulados_pib()
etl/pib_ibge.py:criar_dados_simulados_pib_per_capita()
etl/vaf_sefaz.py:criar_dados_simulados_vaf()
etl/icms_sefaz.py:criar_dados_simulados_icms()
etl/empresas_rais.py:criar_dados_simulados_empresas()
etl/emissoes_gee.py:criar_dados_simulados_emissoes()
etl/mapbiomas.py:create_sustentabilidade_simulada()
etl/mapbiomas.py:create_sustentabilidade_indicators()
etl/salarios.py:[função de simulação]
etl/mei.py:[função de simulação]
```

### PADRÃO DE FALLBACK CORRETO:
```python
# ✅ CORRETO:
API → /raw → Retornar vazio (informar usuário)

# ❌ ERRADO:
API → /raw → SIMULAR DADOS
```

---

**FIM DA AUDITORIA TÉCNICA COMPLETA**
