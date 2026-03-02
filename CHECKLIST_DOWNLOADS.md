# Checklist de Downloads Manuais - Painel GV

Este documento serve como guia para baixar os dados que **não possuem API automática**.

---

## 📋 Checklist de Arquivos

| # | Arquivo | Baixado? | Fonte |
|---|---------|----------|-------|
| 1 | `sebrae.csv` | ☐ | Observatório Sebrae |
| 2 | `mapbiomas.csv` | ☐ | MapBiomas |
| 3 | `seeg.csv` | ☐ | SEEG (Dados) |
| 4 | `vaf.csv` | ☐ | SEFAZ-MG |
| 5 | `icms.csv` | ☐ | SEFAZ-MG |
| 6 | `inep.csv` | ☐ | INEP (Censo Escolar) |
| 7 | `saude.csv` | ☐ | DataSUS (Tabnet) |
| 8 | `idsc.csv` | ☐ | IDSC (Cidades Sustentáveis) |

---

## 🔗 Links e Instruções Detalhadas

### 1. SEBRAE (Empresas Ativas, MEI)
- **Link:** https://datasebrae.com.br/municipios/
- **Salvar como:** `data/raw/sebrae.csv`

### 2. MAPBIOMAS & SEEG
- **MapBiomas:** https://mapbiomas.org/download (Baixar Dados de Cobertura e Uso do Solo - Recorte Municipal)
- **SEEG:** https://seeg.eco.br/dados/
- **Salvar como:** `data/raw/mapbiomas.csv` e `data/raw/seeg.csv`

### 3. RECEITA E FINANÇAS (VAF, ICMS)
- **VAF/ICMS (SEFAZ-MG):** https://www.fazenda.mg.gov.br/empresas/vaf/
- **Salvar como:** `data/raw/vaf.csv`, `data/raw/icms.csv`

### 4. EDUCAÇÃO (INEP)
- **Link:** https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/sinopses-estatisticas/educacao-basica
- **Passos:** Baixe os microdados ou sinopse do Censo Escolar.
- **Salvar como:** `data/raw/inep.csv`

### 5. SAÚDE (DataSUS)
- **Link:** https://datasus.saude.gov.br/informacoes-de-saude-tabnet/
- **Passos:** Selecione "Estatísticas Vitais" ou "Indicadores de Saúde" conforme o dado desejado.
- **Salvar como:** `data/raw/saude.csv`

### 6. IDSC (Sustentabilidade)
- **Link:** https://idsc.cidadessustentaveis.org.br
- **Salvar como:** `data/raw/idsc.csv`

---

## 📂 Onde Salvar

Todos os arquivos devem ser salvos em:
```
c:\painel_gv\data\raw\
```

---

## ▶️ Após Baixar

Execute o comando abaixo para carregar os dados no sistema:
```powershell
cd c:\painel_gv
python -c "from etl.etl_runner import run_all; run_all()"
```

---

## ✅ Verificação Final

Após executar o ETL, verifique no painel:
- [ ] Aba "Economia" mostra PIB e VAF
- [ ] Aba "Sustentabilidade" mostra IDSC e Território
- [ ] Aba "Saúde" mostra Mortalidade Infantil
- [ ] Aba "Educação" mostra Matrículas
- [ ] Aba "Trabalho & Renda" mostra Empresas e MEI
