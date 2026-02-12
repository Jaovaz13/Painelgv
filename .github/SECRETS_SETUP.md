# Configuração de Secrets no GitHub Actions

## 📋 Secrets Necessários

Para que o workflow de ETL automático funcione corretamente, você precisa configurar os seguintes secrets no repositório GitHub:

### 1. DATABASE_URL
**Descrição:** URL de conexão com o banco de dados PostgreSQL  
**Formato:** `postgresql://usuario:senha@host:porta/database`  
**Exemplo:** `postgresql://user:pass@db.example.com:5432/painel_gv`  
**Padrão (se não configurado):** `sqlite:///data/painel_gv.db`

### 2. MUNICIPIO
**Descrição:** Nome do município  
**Valor:** `Governador Valadares`  
**Padrão:** `Governador Valadares`

### 3. COD_IBGE
**Descrição:** Código IBGE do município  
**Valor:** `3127701`  
**Padrão:** `3127701`

### 4. UF
**Descrição:** Sigla do estado  
**Valor:** `MG`  
**Padrão:** `MG`

---

## 🔧 Como Configurar os Secrets

### Passo 1: Acessar Configurações do Repositório
1. Acesse seu repositório no GitHub
2. Clique em **Settings** (Configurações)
3. No menu lateral, clique em **Secrets and variables** → **Actions**

### Passo 2: Adicionar Novo Secret
1. Clique em **New repository secret**
2. Preencha:
   - **Name:** Nome do secret (ex: `DATABASE_URL`)
   - **Secret:** Valor do secret
3. Clique em **Add secret**

### Passo 3: Repetir para Todos os Secrets
Repita o processo para cada um dos 4 secrets listados acima.

---

## ✅ Verificação

Após configurar os secrets, você pode verificar se estão corretos:

1. Vá em **Actions** no repositório
2. Clique em **Atualização Automática de Dados (ETL)**
3. Clique em **Run workflow** → **Run workflow**
4. Acompanhe a execução e verifique os logs

O step "Verificar configuração de secrets" mostrará se o DATABASE_URL está configurado.

---

## 🔒 Segurança

- ✅ Secrets são criptografados pelo GitHub
- ✅ Não aparecem nos logs (são mascarados)
- ✅ Apenas workflows autorizados podem acessá-los
- ⚠️ Nunca commite secrets no código-fonte
- ⚠️ Use `.env` apenas para desenvolvimento local

---

## 🚀 Execução Automática

O workflow está configurado para rodar:
- **Automaticamente:** Todos os dias às 03:00 (horário de Brasília)
- **Manualmente:** Via botão "Run workflow" no GitHub Actions

---

## 🐛 Troubleshooting

### Erro: "DATABASE_URL não configurado"
**Solução:** Configure o secret DATABASE_URL conforme instruções acima

### Erro: "Connection refused"
**Solução:** Verifique se o banco de dados está acessível pela internet e se as credenciais estão corretas

### Erro: "Module not found"
**Solução:** Verifique se todas as dependências estão listadas em `requirements.txt`

---

## 📝 Notas

- Os valores padrão são usados apenas se os secrets não estiverem configurados
- Para produção, **sempre configure os secrets** corretamente
- O banco SQLite local é apenas para testes/desenvolvimento
