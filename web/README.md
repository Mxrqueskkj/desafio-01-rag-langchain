# Interface web (Streamlit)

Esta pasta contém uma interface web opcional sobre a lógica em `src/`.
O desafio original continua sendo a aplicação de terminal (`python src/chat.py`).

## Como rodar

1. Suba o banco: `docker compose up -d`
2. Preencha o `.env` (chave de API, modelos, etc.)
3. Instale as dependências web: `pip install -r web/requirements.txt`
4. Na raiz do projeto: `streamlit run web/app.py`

## Deploy gratuito

- Streamlit Community Cloud: conecte o repositório e aponte para `web/app.py`.
- Lembre-se de configurar as variáveis de ambiente (secrets) no painel do Streamlit Cloud,
  incluindo `DATABASE_URL` apontando para um PostgreSQL com pgvector acessível.
- Para uso pessoal/teste, o banco pode ficar em um serviço gerenciado (ex.: Neon, Supabase)
  com a extensão pgvector habilitada.

## Atenção

- Cada pergunta gasta tokens da sua chave de API.
- O PDF enviado fica salvo em `uploads/uploaded.pdf` (local) e não é versionado.
