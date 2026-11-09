---
name: Testes RAG (Desafio 01)
description: Planeja, executa e diagnostica os testes do projeto RAG do Desafio 01 (LangChain + PostgreSQL/pgvector + Streamlit), cobrindo unidade, integração, web, segurança e desempenho.
---

# Testes RAG — Desafio 01

Use este skill sempre que for testar, revisar ou corrigir o projeto
`desafio-01-rag-langchain`. Ele padroniza as camadas de teste, os comandos e o
checklist de aceitação do desafio.

## Quando usar

- Antes de entregar ou fazer commit de qualquer alteração.
- Ao investigar respostas erradas, recusas indevidas ou falhas de ingestão.
- Ao trocar o PDF, o modelo de chat ou o modelo de embeddings.
- Ao mexer na interface Streamlit (`web/app.py`).
- Ao revisar segurança (chaves, `.env`, prompt injection).

## Regras invioláveis

1. **Nunca alterar o `.env`** durante testes. Leia os valores existentes; para
   cenários de ambiente inválido, use `monkeypatch`/variáveis temporárias.
2. Testes unitários **não** acessam rede, banco nem APIs pagas.
3. Testes de integração só rodam com `RUN_INTEGRATION=1` e exigem Docker,
   PostgreSQL/pgvector e chave de API válidos.
4. Use `tmp_path` do pytest para PDFs temporários; não escreva no
   `document.pdf` real.
5. Faça mock de `load_settings`, `get_vector_store`, `call_llm` e do Streamlit
   quando o teste não for explicitamente de integração.
6. Preserve as invariantes do desafio:
   - `CHUNK_SIZE = 1000` e `CHUNK_OVERLAP = 150`;
   - busca com `k = 10` por padrão;
   - frase de recusa exata:
     `Não tenho informações necessárias para responder sua pergunta.`
7. Nunca grave segredos em testes, fixtures, prints ou arquivos versionados.

## Camadas de teste

| Camada | Marker | O que cobre | Precisa de quê |
| --- | --- | --- | --- |
| Unidade | (nenhum) | `config`, `search`, `chat`, `ingest` com mocks | apenas Python |
| Web | `web` | funções do `web/app.py` e renderização com `AppTest` | Streamlit |
| Segurança | `security` | `.env` ignorado, segredos, prompt injection, SQL injection | Git local |
| Desempenho | `slow` | split, formatação, prompt e busca vazia | apenas Python |
| Integração | `integration` | banco real, ingestão idempotente, busca, resposta e HTTP | Docker + `.env` |

## Comandos

Na raiz do projeto, com o venv ativo:

```powershell
# Tudo que não depende de banco/API
.\venv\Scripts\python.exe -m pytest -m "not integration"

# Só unidade
.\venv\Scripts\python.exe -m pytest -m "not integration and not web and not slow and not security"

# Só web
.\venv\Scripts\python.exe -m pytest -m web

# Segurança
.\venv\Scripts\python.exe -m pytest -m security

# Desempenho
.\venv\Scripts\python.exe -m pytest -m slow

# Integração real (Docker no ar + .env válido)
$env:RUN_INTEGRATION = "1"
.\venv\Scripts\python.exe -m pytest -m integration
Remove-Item Env:RUN_INTEGRATION

# Cobertura
.\venv\Scripts\python.exe -m pytest -m "not integration" --cov=src --cov=web --cov-report=term-missing
```

Atalho opcional:

```powershell
.\.opencode\skills\rag-testing\scripts\run-tests.ps1
.\.opencode\skills\rag-testing\scripts\run-tests.ps1 -Integration
```

## Checklist de aceitação

- [ ] `pytest -m "not integration"` passa sem falhas.
- [ ] `pytest -m integration` passa com banco e chave reais.
- [ ] Ingestão informa páginas e chunks e não duplica ao rodar duas vezes
      (idempotência por IDs determinísticos).
- [ ] Busca devolve até 10 trechos, com `source`, `page` e score.
- [ ] Pergunta fora do contexto devolve a frase de recusa exata.
- [ ] Pergunta de opinião devolve a frase de recusa exata.
- [ ] Upload de PDF funciona no Streamlit.
- [ ] "Limpar base (trocar PDF)" apaga a collection, limpa o chat e permite
      ingerir outro PDF sem reiniciar.
- [ ] `.env` continua fora do Git e nenhuma chave aparece em arquivos versionados.
- [ ] `web/app.py` compila e o app renderiza sem exceção.
- [ ] README e guia no Notion continuam coerentes com o código.

Checklist manual complementar: `references/manual-checklist.md`.

## Mapa dos arquivos

- `tests/conftest.py` — caminhos, fixtures e `Settings` de teste.
- `tests/test_config.py` — leitura do ambiente, provedores e vector store.
- `tests/test_search.py` — busca vazia, `k`, scores e formatação.
- `tests/test_chat.py` — prompt, recusa, provedores e loop do CLI.
- `tests/test_ingest.py` — PDF, split, metadados, IDs e orquestração.
- `tests/test_web.py` — upload, processamento, limpeza e `AppTest`.
- `tests/test_security.py` — segredos, `.gitignore` e prompt injection.
- `tests/test_edge_cases.py` — entradas vazias, longas, Unicode e limites.
- `tests/test_performance.py` — tempos máximos generosos para evitar flakiness.
- `tests/test_integration.py` — banco, API, busca real e HTTP do Streamlit.
- `tests/test_skill.py` — garante que este skill continua válido e sincronizado.

## Diagnóstico rápido

| Sintoma | Onde olhar |
| --- | --- |
| `ValueError: Preencha no .env` | `test_config.py` e `.env.example` |
| Recusa para pergunta que está no PDF | `test_search.py`, score e `k` |
| Resposta inventada | `test_chat.py`, prompt e `temperature=0` |
| Ingestão duplica vetores | `test_ingest.py`, IDs determinísticos |
| Upload não aparece | `test_web.py`, `AppTest` e `web/app.py` |
| Troca de PDF não limpa | `test_web.py`, `clear_base` |
| Teste de integração pulado | defina `RUN_INTEGRATION=1` |
| Chave exposta | `test_security.py` e `git ls-files` |
