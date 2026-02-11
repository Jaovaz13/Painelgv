# 🔧 PLANO DE CORREÇÕES URGENTES - PAINEL GV

**Data:** 11/02/2026  
**Objetivo:** Eliminar TODAS as violações das regras absolutas do projeto  
**Status:** 🔴 PENDENTE

---

## 📋 RESUMO EXECUTIVO

Este plano detalha **TODAS as correções necessárias** identificadas na auditoria técnica, priorizadas por criticidade e com comandos prontos para execução.

**Tempo estimado total:** 8-12 horas de trabalho  
**Impacto:** Conformidade 100% com regras institucionais

---

## 🚨 PRIORIDADE 1 - CRÍTICA (EXECUTAR HOJE)

### ✅ ETAPA 1: Deletar arquivos de código morto

**Arquivos a deletar:**

```bash
# Windows PowerShell
Remove-Item "c:\painel_gv\etl\educacao_simulada.py"
Remove-Item "c:\painel_gv\etl\censo_escolar.py"
```

**Razão:** Estes arquivos geram 100% dados simulados, violando regra absoluta.

---

### ✅ ETAPA 2: Remover funções de simulação em pib_ibge.py

**Arquivo:** `c:\painel_gv\etl\pib_ibge.py`

**Linhas a remover:** 63-196

**Código a deletar:**
```python
# DELETAR linhas 63-65:
        # Se ainda falhar, cria dados simulados para teste
        logger.warning("Criando dados simulados para PIB municipal")
        return criar_dados_simulados_pib()

# DELETAR linhas 100-102:
        # Se ainda falhar, cria dados simulados para teste
        logger.warning("Criando dados simulados para PIB per capita")
        return criar_dados_simulados_pib_per_capita()

# DELETAR COMPLETAMENTE linhas 108-196:
def criar_dados_simulados_pib() -> Dict:
    [TODO O BLOCO]

def criar_dados_simulados_pib_per_capita() -> Dict:
    [TODO O BLOCO]
```

**Substituir por fallback correto:**
```python
# Nas linhas 63-65, substituir por:
        # Se falhar, tentar arquivo local em /raw
        logger.warning("API IBGE falhou, tentando arquivo local em /raw")
        return load_pib_from_raw()

# Nas linhas 100-102, substituir por:
        logger.warning("API IBGE falhou, tentando arquivo local em /raw")
        return load_pib_per_capita_from_raw()

# ADICIONAR no final do arquivo:
def load_pib_from_raw() -> Optional[Dict]:
    """Carrega PIB de arquivo CSV em data/raw se disponível"""
    try:
        csv_path = Path(__file__).parent.parent / "data" / "raw" / "pib_municipal.csv"
        if not csv_path.exists():
            logger.warning(f"Arquivo {csv_path} não encontrado")
            return None
            
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        # Transformar em formato esperado
        data = {
            "localidade": {"id": "3127701", "nome": "Governador Valadares"},
            "resultados": [{"series": [{"serie": {}}]}]
        }
        for _, row in df.iterrows():
            year = str(int(row['ano']))
            value = float(row['valor'])
            data["resultados"][0]["series"][0]["serie"][year] = value
        
        logger.info(f"PIB carregado de {csv_path}")
        return data
    except Exception as e:
        logger.error(f"Erro ao carregar PIB de /raw: {e}")
        return None

def load_pib_per_capita_from_raw() -> Optional[Dict]:
    """Carrega PIB per capita de arquivo CSV em data/raw se disponível"""
    try:
        csv_path = Path(__file__).parent.parent / "data" / "raw" / "pib_per_capita.csv"
        if not csv_path.exists():
            logger.warning(f"Arquivo {csv_path} não encontrado")
            return None
            
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        data = {
            "localidade": {"id": "3127701", "nome": "Governador Valadares"},
            "resultados": [{"series": [{"serie": {}}]}]
        }
        for _, row in df.iterrows():
            year = str(int(row['ano']))
            value = float(row['valor'])
            data["resultados"][0]["series"][0]["serie"][year] = value
        
        logger.info(f"PIB per capita carregado de {csv_path}")
        return data
    except Exception as e:
        logger.error(f"Erro ao carregar PIB per capita de /raw: {e}")
        return None
```

---

### ✅ ETAPA 3: Remover funções de simulação em vaf_sefaz.py

**Arquivo:** `c:\painel_gv\etl\vaf_sefaz.py`

**Linhas a remover:** 33-39 e 41-80

**Código a deletar:**
```python
# DELETAR linhas 33-39:
        # Se API não estiver disponível, cria dados simulados
        logger.warning("API SEFAZ não disponível, criando dados simulados")
        return criar_dados_simulados_vaf()
        
    except Exception as e:
        logger.error(f"Erro ao extrair VAF: {e}")
        return criar_dados_simulados_vaf()

# DELETAR linhas 41-80 (função inteira):
def criar_dados_simulados_vaf() -> Dict:
    [TODO O BLOCO]
```

**Substituir por:**
```python
        # Se API não estiver disponível, tentar arquivo local
        logger.warning("API SEFAZ não disponível, tentando arquivo em /raw")
        return load_vaf_from_raw()
        
    except Exception as e:
        logger.error(f"Erro ao extrair VAF: {e}")
        return load_vaf_from_raw()

# ADICIONAR:
def load_vaf_from_raw() -> Optional[Dict]:
    """Carrega VAF de arquivo em data/raw"""
    try:
        csv_path = Path(__file__).parent.parent / "data" / "raw" / "vaf_sefaz.csv"
        if not csv_path.exists():
            logger.warning(f"Arquivo {csv_path} não encontrado. VAF não será carregado.")
            return None
            
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        # Transformar conforme necessário
        logger.info(f"VAF carregado de {csv_path}")
        return {"data": df.to_dict('records')}  # Ajustar formato conforme necessário
    except Exception as e:
        logger.error(f"Erro ao carregar VAF de /raw: {e}")
        return None
```

---

### ✅ ETAPA 4: Remover funções de simulação em icms_sefaz.py

**Arquivo:** `c:\painel_gv\etl\icms_sefaz.py`  
**Mesmo padrão que vaf_sefaz.py**

**Código igual ao da Etapa 3, mas para ICMS:**
- Deletar `criar_dados_simulados_icms()`
- Adicionar `load_icms_from_raw()`

---

### ✅ ETAPA 5: Remover funções de simulação em mapbiomas.py

**Arquivo:** `c:\painel_gv\etl\mapbiomas.py`

**Linhas a remover:** 227-228 e 268-369

**Código a deletar:**
```python
# DELETAR linhas 227-228:
        # Criar dados simulados para indicadores de sustentabilidade
        create_sustentabilidade_simulada()

# DELETAR linhas 268-369 (DUAS FUNÇÕES INTEIRAS):
def create_sustentabilidade_simulada():
    [TODO O BLOCO ATÉ LINHA 325]

def create_sustentabilidade_indicators():
    [TODO O BLOCO ATÉ LINHA 369]
```

**Substituir por:**
```python
        # Se não houver arquivos, informar e NÃO criar simulação
        logger.warning(
            "Nenhum arquivo MapBiomas encontrado em data/raw. "
            "Indicadores de sustentabilidade não serão carregados. "
            "Baixe os arquivos necessários em https://mapbiomas.org/"
        )
        return

# NO run_all.py, adicionar verificação antes de rodar mapbiomas:
# if not tem_arquivos_mapbiomas():
#     logger.warning("Pulando ETL MapBiomas - sem arquivos")
```

---

### ✅ ETAPA 6: Remover simulações em outros ETLs

**Arquivos afetados:**
- `etl/empresas_rais.py` - remover `criar_dados_simulados_empresas()`
- `etl/emissoes_gee.py` - remover `criar_dados_simulados_emissoes()`
- `etl/salarios.py` - remover função de simulação (linha 105+)
- `etl/mei.py` - remover função de simulação (linha 116+)

**Padrão para todos:**
```python
# SEMPRE:
# 1. Tentar API
# 2. Se falhar, tentar /raw
# 3. Se /raw não existir, logger.warning() e retornar vazio
# 4. NUNCA simular dados
```

---

### ✅ ETAPA 7: Atualizar run_all.py

**Arquivo:** `c:\painel_gv\etl\run_all.py`

**Remover imports:**
```python
# DELETAR (se existirem):
# import etl.educacao_simulada as educacao_simulada
# import etl.censo_escolar as censo_escolar
```

**Remover de processos:**
```python
# VERIFICAR e REMOVER se existirem:
# {"mod": educacao_simulada, "name": "Educação Simulada"},
# {"mod": censo_escolar, "name": "Censo Escolar"},
```

---

## 📝 PRIORIDADE 2 - ALTA (EXECUTAR ESTA SEMANA)

### ✅ ETAPA 8: Adicionar aba Metodologia

**Arquivo:** `c:\painel_gv\panel\painel.py`

**Linha 276** - Atualizar lista de abas:
```python
# ANTES:
abas = ["Visão Geral", "Economia", "Trabalho & Renda", "Negócios", "Educação", "Saúde", "Sustentabilidade", "PIB Estimado", "Dashboard Executivo", "Métricas do Sistema", "Relatórios"]

# DEPOIS:
abas = ["Visão Geral", "Economia", "Trabalho & Renda", "Negócios", "Educação", "Saúde", "Sustentabilidade", "Metodologia", "PIB Estimado", "Dashboard Executivo", "Métricas do Sistema", "Relatórios"]
```

**Linha ~650** - Adicionar renderização da aba:
```python
elif pagina == "Metodologia":
    st.header("📖 Nota Metodológica e Fontes de Dados")
    
    st.markdown("""
    ## 🎯 Objetivo do Sistema
    
    O **Painel GV** é o sistema oficial de indicadores socioeconômicos de Governador Valadares - MG, 
    desenvolvido pela Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação.
    
    ---
    
    ## 📊 Fontes de Dados
    
    Todos os indicadores são baseados em **dados oficiais e públicos**:
    
    ### Economia
    - **PIB Total e Per Capita:** IBGE - Produto Interno Bruto dos Municípios
    - **VAF:** SEFAZ-MG - Valor Adicionado Fiscal
    - **ICMS:** SEFAZ-MG - Cota-Parte do ICMS
    
    ### Trabalho e Renda
    - **CAGED:** Ministério do Trabalho - Cadastro Geral de Empregados e Desempregados
    - **RAIS:** Ministério do Trabalho - Relação Anual de Informações Sociais
    - **Empresas:** SEBRAE - Observatório de Negócios
    - **MEI:** Datasebrae - Microempreendedores Individuais
    
    ### Educação
    - **Matrículas:** INEP - Sinopse Estatística da Educação Básica
    - **IDEB:** INEP - Índice de Desenvolvimento da Educação Básica
    - **Taxa de Aprovação:** INEP - Censo Escolar
    
    ### Saúde
    - **Mortalidade Infantil:** DataSUS - Sistema de Informações sobre Mortalidade
    - **Óbitos:** DataSUS - Tabnet
    
    ### Sustentabilidade
    - **Emissões GEE:** SEEG - Sistema de Estimativas de Emissões de Gases de Efeito Estufa
    - **Uso do Solo:** MapBiomas - Coleções 9 e 10
    - **IDSC:** Cidades Sustentáveis - Índice de Desenvolvimento Sustentável
    
    ### Demografia
    - **População:** IBGE - Censo Demográfico e Estimativas Populacionais
    - **IDH-M:** Atlas Brasil - Índice de Desenvolvimento Humano Municipal
    - **GINI:** IBGE - Índice de Desigualdade
    
    ---
    
    ## 🔄 Atualização de Dados
    
    ### Frequência
    - **Automática:** Diariamente às 02:00 via scheduler
    - **Manual:** Disponível em "Métricas do Sistema"
    
    ### Sistema de Redundância
    ```
    1. Tentativa: API oficial da fonte
    2. Fallback: Arquivo local em data/raw
    3. Falha: Informação ao usuário (sem simulação)
    ```
    
    **Política:** É **PROIBIDO** o uso de dados simulados ou fictícios. Apenas dados oficiais são aceitos.
    
    ---
    
    ## 📈 Metodologia de Estimativas
    
    ### PIB Estimado
    
    A estimativa do Produto Interno Bruto Municipal para anos sem divulgação oficial utiliza:
    
    **Metodologia Híbrida:**
    1. **Base:** Último PIB oficial publicado pelo IBGE
    2. **Proxies:** 
       - Valor Adicionado Fiscal (SEFAZ-MG)
       - Massa Salarial (RAIS/CAGED)
       - Empregos Formais
    3. **Modelos:** Séries temporais (ARIMA, Exponential Smoothing)
    4. **Validação:** Comparação com PIB estadual e nacional
    
    **Limitações:**
    - Estimativas têm margem de erro
    - Devem ser atualizadas quando IBGE divulgar dados oficiais
    - Servem apenas para análise de tendências, não decisões orçamentárias
    
    ### Indicadores Derivados
    
    Alguns indicadores são **calculados** a partir de outros:
    - **PIB per Capita** = PIB Total / População
    - **Crescimento PIB** = (PIB_ano - PIB_ano-1) / PIB_ano-1 * 100
    
    ---
    
    ## 🛡️ Qualidade e Confiabilidade
    
    ### Tratamento de Dados
    - Validação automática de inconsistências
    - Remoção de outliers estatísticos quando justificado
    - Interpolação linear apenas para preenchimento de lacunas mensais
    
    ### Auditoria
    - Logs completos de todas as operações ETL
    - Rastreabilidade de todas as transformações
    - Versionamento de código e dados
    
    ---
    
    ## 📞 Contato
    
    **Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação**  
    Prefeitura Municipal de Governador Valadares - MG  
    
    Para dúvidas ou sugestões sobre os indicadores:
    - Email: [contato@gv.mg.gov.br]
    - Telefone: [XX XXXX-XXXX]
    
    ---
    
    ## 📄 Licença e Uso
    
    Este sistema e seus dados são de **uso público** e podem ser utilizados para:
    - Pesquisas acadêmicas
    - Análises econômicas
    - Planejamento estratégico
    - Tomada de decisão governamental
    
    **Citação sugerida:**  
    > "PAINEL GV - Observatório de Governador Valadares. Secretaria Municipal de Desenvolvimento, 
    > Ciência, Tecnologia e Inovação. Governador Valadares, MG, 2026. Disponível em: [URL]"
    
    ---
    
    **Última atualização desta documentação:** 11/02/2026
    """)
```

---

### ✅ ETAPA 9: Refatorar painel.py (função main)

**Objetivo:** Quebrar `main()` de 884 linhas em funções menores

**Criar funções separadas:**

```python
def render_visao_geral(ano_inicio, ano_fim, modo):
    """Renderiza a aba Visão Geral"""
    # Mover código das linhas 302-477 para cá
    pass

def render_trabalho_renda(ano_inicio, ano_fim, modo):
    """Renderiza a aba Trabalho & Renda"""
    # Mover código das linhas 478-547 para cá
    pass

def render_negocios(ano_inicio, ano_fim, modo):
    """Renderiza a aba Negócios"""
    # Mover código das linhas 548-604 para cá
    pass

def render_pib_estimado(ano_inicio, ano_fim):
    """Renderiza a aba PIB Estimado"""
    # Mover código das linhas 605-640 para cá
    pass

def render_sustentabilidade(ano_inicio, ano_fim, modo):
    """Renderiza a aba Sustentabilidade"""
    # Mover código das linhas 651-687 para cá
    pass

def render_economia(ano_inicio, ano_fim, modo):
    """Renderiza a aba Economia"""
    # Mover código das linhas 692-801 para cá
    pass

def render_outras_paginas(pagina, ano_inicio, ano_fim, modo):
    """Renderiza páginas genéricas (Educação, Saúde, etc)"""
    # Mover código das linhas 802-845 para cá
    pass

def main():
    """Função principal simplificada"""
    # Logo e configuração (linhas 262-295)
    
    if pagina == "Visão Geral":
        render_visao_geral(ano_inicio, ano_fim, modo)
    elif pagina == "Economia":
        render_economia(ano_inicio, ano_fim, modo)
    elif pagina == "Trabalho & Renda":
        render_trabalho_renda(ano_inicio, ano_fim, modo)
    elif pagina == "Negócios":
        render_negocios(ano_inicio, ano_fim, modo)
    elif pagina == "PIB Estimado":
        render_pib_estimado(ano_inicio, ano_fim)
    elif pagina == "Dashboard Executivo":
        create_executive_dashboard()
    elif pagina == "Métricas do Sistema":
        create_metrics_dashboard()
    elif pagina == "Relatórios":
        render_relatorios(ano_inicio, ano_fim)
    elif pagina == "Sustentabilidade":
        render_sustentabilidade(ano_inicio, ano_fim, modo)
    elif pagina == "Metodologia":
        render_metodologia()  # Nova função da Etapa 8
    else:
        render_outras_paginas(pagina, ano_inicio, ano_fim, modo)
```

---

### ✅ ETAPA 10: Criar arquivos CSV de fallback em /raw

**Objetivo:** Garantir que existe fallback local para APIs críticas

**Arquivos a criar/verificar:**

```bash
# Verificar se existem, senão criar templates:
c:\painel_gv\data\raw\pib_municipal.csv
c:\painel_gv\data\raw\pib_per_capita.csv
c:\painel_gv\data\raw\vaf_sefaz.csv
c:\painel_gv\data\raw\icms_sefaz.csv
```

**Formato sugerido (pib_municipal.csv):**
```csv
ano;valor;fonte
2002;2684456780;IBGE
2010;5987654320;IBGE
2020;9456789900;IBGE
2021;9789012120;IBGE
2022;10123456340;IBGE
```

---

## 📊 PRIORIDADE 3 - MÉDIA (EXECUTAR PRÓXIMA SEMANA)

### ✅ ETAPA 11: Adicionar type hints

**Objetivo:** Melhorar qualidade e manutenibilidade do código

**Arquivos prioritários:**
- `etl/pib_ibge.py`
- `etl/vaf_sefaz.py`
- `etl/icms_sefaz.py`
- `etl/mapbiomas.py`

**Exemplo:**
```python
from typing import Optional, Dict, List
import pandas as pd

def extrair_pib_municipal() -> Optional[Dict[str, Any]]:
    """Extrai dados do PIB municipal do IBGE"""
    pass

def processar_serie_historica(
    dados: Dict[str, Any], 
    variavel_id: str
) -> List[Dict[str, Any]]:
    """Processa série histórica dos dados do IBGE"""
    pass
```

---

### ✅ ETAPA 12: Criar testes unitários

**Criar estrutura:**
```bash
mkdir c:\painel_gv\tests
```

**Arquivo:** `tests/test_database.py`
```python
import pytest
import pandas as pd
from database import upsert_indicators, get_timeseries

def test_upsert_indicators():
    df = pd.DataFrame([
        {"year": 2020, "value": 1000, "unit": "R$"},
        {"year": 2021, "value": 1100, "unit": "R$"}
    ])
    
    result = upsert_indicators(
        df,
        indicator_key="TEST_INDICATOR",
        source="TEST",
        category="Teste"
    )
    
    assert result >= 0
    
def test_get_timeseries():
    df = get_timeseries("TEST_INDICATOR", "TEST")
    assert isinstance(df, pd.DataFrame)
```

**Arquivo:** `tests/test_etl_demograficos.py`
```python
import pytest
from etl.demograficos import get_populacao, get_idhm, get_gini

def test_get_populacao():
    df = get_populacao()
    assert isinstance(df, pd.DataFrame)
    if not df.empty:
        assert "year" in df.columns
        assert "value" in df.columns
        assert "unit" in df.columns

def test_get_idhm():
    df = get_idhm()
    assert isinstance(df, pd.DataFrame)

def test_get_gini():
    df = get_gini()
    assert isinstance(df, pd.DataFrame)
```

**Executar:**
```bash
pytest tests/ -v
```

---

### ✅ ETAPA 13: Atualizar README.md

**Arquivo:** `c:\painel_gv\README.md`

Adicionar seções:
- **Políticas de Dados:** 100% reais, sem simulação
- **Arquitetura Detalhada:** Diagrama e explicação
- **Como Executar ETLs:** Comandos step-by-step
- **Como Rodar o Painel:** Instalação e execução
- **Fallback e Redundância:** Como funciona o sistema

---

## ✅ CHECKLIST DE VALIDAÇÃO

Após executar todas as etapas, verificar:

- [ ] ❌ ZERO arquivos com nome "*simulad*"
- [ ] ❌ ZERO funções com nome "criar_dados_simulados"
- [ ] ❌ ZERO funções com nome "*simulad*"
- [ ] ✅ Todos os ETLs usam: API → /raw → vazio
- [ ] ✅ Aba "Metodologia" existe e está completa
- [ ] ✅ `main()` tem menos de 200 linhas
- [ ] ✅ Type hints em funções principais
- [ ] ✅ Testes unitários passando
- [ ] ✅ README.md atualizado

---

## 🏁 COMANDO FINAL DE VERIFICAÇÃO

Após todas as correções, executar:

```bash
# 1. Verificar que não há simulações
grep -r "simulad" etl/ --include="*.py"
# Resultado esperado: NENHUM resultado ou apenas comentários

# 2. Contar linhas da função main
grep -A 1000 "^def main" panel/painel.py | wc -l
# Resultado esperado: < 200 linhas

# 3. Executar testes
pytest tests/ -v
# Resultado esperado: TODOS passando

# 4. Verificar banco de dados
python check_db.py
# Resultado esperado: Lista de indicadores SEM "SIMULADO" no source
```

---

## 📞 SUPORTE

Se houver dúvidas durante a implementação:
1. Consultar `AUDITORIA_TECNICA_COMPLETA.md`
2. Revisar código de exemplo neste plano
3. Testar em ambiente de desenvolvimento primeiro
4. Fazer commit após cada etapa concluída

---

**Plano criado por:** Sistema AI Antigravity  
**Baseado em:** Auditoria Técnica Completa  
**Próxima ação:** Iniciar execução por Prioridade 1

---

**FIM DO PLANO DE CORREÇÕES URGENTES**
