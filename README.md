# Painel Observatório GV

Painel de indicadores socioeconômicos do município (Governador Valadares/MG) – Secretaria Municipal de Desenvolvimento, Ciência, Tecnologia e Inovação.

## Arquitetura

- **APIs/CSVs** (IBGE, CAGED, RAIS, Sebrae, SEFAZ, DataSUS, SNIS, Sustentabilidade) → **Python ETL** → **SQLite** (`db/observatorio.db`) → **Streamlit** (painel interno + portal público).

## Estrutura do projeto

- `config.py`, `database.py`, `requirements.txt`
- `etl/` – extração, transformação e carga (ibge, caged, rais, sebrae, datasus, snis, sefaz_mg, sustentabilidade, etl_runner)
- `data/raw/` – arquivos CSV/Excel usados pelos ETLs quando aplicável
- `data/raw/converted/` – cópias XLSX convertidas de CSVs (priorizadas pelos ETLs)
- `db/` – banco SQLite `observatorio.db`
- `analytics/` – análise de tendências (`tendencias.py`)
- `reports/` – relatório PDF customizável (`report_pdf.py`), metodologia (`metodologia.py`)
- `presentations/` – geração de PowerPoint (`presentation_ppt.py`)
- `maps/` – GeoJSON para mapas (uso futuro)
- `panel/` – painel interno Streamlit (`painel_interno.py`)
- `portal_publico/` – portal público Streamlit (`portal_publico.py`)
- `scheduler/` – atualização periódica (24h) dos dados (`update.py`)
- `utils/` – utilitários de status e conversão CSV→XLSX

## Uso local

1. **Instalar dependências**
   ```bash
   pip install -r requirements.txt
   ```

2. **Popular o banco (ETL)**
   ```bash
   python -m etl.etl_runner
   ```
   Ou uma única execução imediata + agendamento a cada 24h:
   ```bash
   python -m scheduler.update
   ```

3. **Painel interno**
   ```bash
   streamlit run app.py
   ```
   Ou diretamente: `streamlit run panel/painel_interno.py`

4. **Portal público**
   ```bash
   streamlit run portal_publico/portal_publico.py`
   ```

## Relatório PDF

No painel interno, abra a seção **Relatório**, informe **ano inicial** e **ano final** e clique em **Gerar Relatório PDF**. O PDF inclui histórico e análise de tendência de todos os indicadores disponíveis no período.

## Deploy (servidor gratuito)

### Streamlit Community Cloud

1. Envie o projeto para um repositório Git (GitHub, GitLab, Bitbucket).
2. Acesse [share.streamlit.io](https://share.streamlit.io), faça login e **New app**.
3. Repositório: `seu-usuario/seu-repo`, Branch: `main`, Main file path: `app.py`.
4. Comando: `streamlit run app.py`.
5. Em **Advanced settings**, defina variáveis de ambiente (opcional):
   - `MUNICIPIO`, `COD_IBGE`, `UF`
   - `DATABASE_URL` – se usar Postgres em vez de SQLite (para persistência entre reinícios)

O Streamlit Community Cloud executa apenas o app; o **scheduler** (atualização a cada 24h) precisa rodar em outro processo. Opções:

- **Cron job** em um VPS ou servidor: `0 * * * * cd /caminho/projeto && python -m etl.etl_runner` (a cada hora) ou agendar `scheduler.update` em um worker.
- **GitHub Actions** (workflow agendado) que chame uma URL de trigger ou rode o ETL em um runner e atualize um banco acessível pelo app.

Para persistência do SQLite no Streamlit Cloud, use o disco efêmero (dados podem ser perdidos ao reiniciar) ou configure um banco externo (Postgres) via `DATABASE_URL`.

### Render (alternativa gratuita)

1. Crie um `requirements.txt` com `streamlit`.
2. No painel do Render, crie um **Web Service**.
3. Conecte o repositório Git.
4. Configure `Build Command`: `pip install -r requirements.txt`.
5. Configure `Start Command`: `streamlit run app.py --server.port=$PORT`.
6. Adicione variáveis de ambiente conforme necessário.

Render permite rodar um processo contínuo, incluindo o scheduler, mas exige manter o app ativo periodicamente no plano gratuito.
