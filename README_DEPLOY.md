# INSTRUÇÕES DE DEPLOY - STREAMLIT CLOUD

Seu projeto está pronto para o Streamlit Cloud!

## 🚀 Passo a Passo Rápido

1. **Suba este projeto para o GitHub.**
   - Crie um repositório novo.
   - Faça o commit de todos os arquivos (incluindo `data/indicadores.db` para ter dados iniciais).
   - Dê push.

2. **No Streamlit Community Cloud:**
   - Clique em "New app".
   - Selecione seu repositório.
   - **Main file path:** `app.py`
   - Clique em **Deploy!**

## ⚙️ Configurações Importantes

### Banco de Dados (SQLite vs PostgreSQL)
Atualmente, o projeto vai subir com um banco SQLite (`data/indicadores.db`) pré-povoado.
**Atenção:** No Streamlit Cloud, o arquivo SQLite será resetado toda vez que o app reiniciar (deploy ou sleep).
Para persistência real e atualizações automáticas, configure um banco PostgreSQL (ex: Neon ou Supabase) e adicione a variável `DATABASE_URL` nos "Secrets" do Streamlit.

### Segredos (Secrets)
Se usar banco externo, adicione no painel do Streamlit (Settings > Secrets):
```toml
DATABASE_URL = "postgresql://usuario:senha@host:5432/database"
```

## 📦 Dependências
O arquivo `requirements.txt` já contém tudo que é necessário.
O arquivo `packages.txt` foi criado (vazio) para compatibilidade.

Boa sorte! 🚀
