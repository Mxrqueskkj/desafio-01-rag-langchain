# Desafio 01 — Ingestão e busca semântica com LangChain e PostgreSQL

Projeto do Desafio 01 da Full Cycle: uma aplicação Python que lê um PDF, grava
os trechos em uma base vetorial no PostgreSQL (pgvector) e responde perguntas
usando **somente** o conteúdo recuperado do documento.

A entrega oficial é a aplicação de terminal (`python src/chat.py`). A versão web
em Streamlit é um complemento para demonstrar o fluxo com upload de PDF.

## O que o projeto faz

1. Lê o PDF configurado em `PDF_PATH`.
2. Divide o texto em chunks de 1000 caracteres com sobreposição de 150.
3. Gera embeddings e grava os vetores no PostgreSQL com pgvector.
4. Busca os 10 trechos mais próximos da pergunta.
5. Monta um prompt com o contexto e chama a LLM.
6. Se a resposta não estiver no contexto, devolve exatamente:
   `Não tenho informações necessárias para responder sua pergunta.`

## Estrutura

```text
desafio-01-rag-langchain/
├── src/
│   ├── config.py      # ambiente, modelos, embeddings e conexão
│   ├── ingest.py      # leitura do PDF, chunks, metadados e gravação
│   ├── search.py      # busca vetorial e formatação do contexto
│   └── chat.py        # prompt, chamada da LLM e loop do terminal
├── web/
│   ├── app.py         # interface Streamlit (upload, chat e troca de PDF)
│   └── requirements.txt
├── tests/             # suíte pytest (unidade, web, segurança, integração)
├── .opencode/skills/rag-testing/  # skill de testes do projeto
├── docker-compose.yml # PostgreSQL + pgvector
├── document.pdf       # PDF usado na ingestão
├── requirements.txt
├── requirements-dev.txt
└── .env.example
```

## Pré-requisitos

- Python 3.11 ou superior.
- Docker Desktop com o plugin Compose.
- Uma chave de API da OpenAI **ou** do Google Gemini.

## Variáveis de ambiente

Copie `.env.example` para `.env` e preencha:

```env
DATABASE_URL=postgresql+psycopg://rag:rag@localhost:5432/rag
PG_VECTOR_COLLECTION_NAME=desafio01
PDF_PATH=document.pdf

CHAT_MODEL=gemini-3.5-flash
EMBEDDING_MODEL=gemini-embedding-001

GOOGLE_API_KEY=sua_chave_aqui
# ou
# OPENAI_API_KEY=sua_chave_aqui
```

O `.env` é ignorado pelo Git. Nunca faça commit de chaves reais.

## Como executar (CLI — entrega oficial)

```powershell
# 1. Criar e ativar o ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Instalar as dependências
pip install -r requirements.txt

# 3. Subir o PostgreSQL com pgvector
docker compose up -d

# 4. Ingerir o PDF
python src/ingest.py

# 5. Conversar com o documento
python src/chat.py
```

Exemplo de sessão:

```text
Chat RAG. Digite 'sair' para encerrar.

Pergunta: Qual é o tema principal do documento?
Resposta: ...

Pergunta: Qual é a capital da França?
Resposta: Não tenho informações necessárias para responder sua pergunta.
```

## Versão web (complemento)

```powershell
pip install -r web/requirements.txt
streamlit run web/app.py
```

Abra `http://localhost:8501`.

Na barra lateral:

- **Envie um PDF**: seleciona um PDF do computador.
- **Processar PDF (ingerir)**: grava os vetores no banco.
- **Limpar base (trocar PDF)**: apaga a collection, limpa o histórico e permite
  enviar outro PDF sem reiniciar o Streamlit.

A versão web reutiliza os mesmos módulos de `src/`; a lógica do desafio continua
no CLI.

## Política de reingestão

Os IDs dos chunks são determinísticos:

```text
{document_hash}-{chunk_index}
```

Isso significa que rodar `python src/ingest.py` duas vezes com o mesmo PDF
**não duplica** os vetores. Para começar do zero:

```powershell
docker compose down -v
docker compose up -d
python src/ingest.py
```

## Testes

Instale as dependências de desenvolvimento:

```powershell
pip install -r requirements-dev.txt
```

Rodar tudo o que não depende de banco/API:

```powershell
.\venv\Scripts\python.exe -m pytest -m "not integration"
```

Rodar os testes de integração reais (Docker no ar + `.env` válido):

```powershell
$env:RUN_INTEGRATION = "1"
.\venv\Scripts\python.exe -m pytest -m integration
Remove-Item Env:RUN_INTEGRATION
```

Marcadores disponíveis:

| Marcador | Conteúdo |
| --- | --- |
| `web` | funções do Streamlit e renderização com `AppTest` |
| `security` | `.env`, segredos, prompt injection e SQL injection |
| `slow` | desempenho de split, prompt e formatação |
| `integration` | PostgreSQL, API, busca real e HTTP do Streamlit |
| `skill` | validação do skill de testes do projeto |

Cobertura:

```powershell
.\venv\Scripts\python.exe -m pytest -m "not integration" `
  --cov=src --cov=web --cov-report=term-missing
```

O skill `.opencode/skills/rag-testing/SKILL.md` documenta as camadas, comandos e
o checklist de aceitação. O checklist manual está em
`.opencode/skills/rag-testing/references/manual-checklist.md`.

## Exemplos de perguntas

- Qual é o tema principal do documento?
- Quais tecnologias são usadas no projeto?
- Como a ingestão divide o texto?
- O que acontece se a informação não estiver no PDF?

Perguntas fora do contexto ou de opinião devem receber a frase de recusa.

## Limitações conhecidas

- PDFs escaneados (somente imagem) precisam de OCR; o projeto avisa quando não
  extrai texto.
- A qualidade das respostas depende do PDF e do modelo configurado.
- A versão web é um complemento; a entrega avaliada é o CLI.
- `PGVector` é usado para manter o código próximo ao material do curso. A
  biblioteca atual recomenda `PGVectorStore`; a migração pode ser feita depois.
- O `document.pdf` incluído é provisório até a substituição pelo PDF oficial do
  desafio.

## Guia de estudo

O guia detalhado do desafio está no Notion:
<https://app.notion.com/p/Desafio-01-Guia-RAG-40cf6a95700d807eb567e6f98d40b563>
