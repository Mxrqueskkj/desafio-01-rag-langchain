# Checklist manual — Desafio 01 RAG

Use este roteiro depois dos testes automatizados. Ele cobre o que o pytest não
consegue validar sozinho (qualidade da resposta, upload real e troca de PDF).

## 1. Preparação

- [ ] Docker Desktop aberto.
- [ ] `docker compose up -d` executado e `db` saudável.
- [ ] `.env` preenchido (não alterar durante o teste).
- [ ] `python src/ingest.py` concluído sem erro.

## 2. CLI (`python src/chat.py`)

- [ ] Pergunta sobre um fato explícito do PDF recebe resposta fundamentada.
- [ ] Pergunta fora do contexto recebe exatamente:
      `Não tenho informações necessárias para responder sua pergunta.`
- [ ] Pergunta de opinião recebe a mesma recusa.
- [ ] `sair`, `exit`, `quit` encerram o chat.
- [ ] `Ctrl+C` encerra sem traceback.
- [ ] Pergunta vazia é ignorada.

## 3. Busca (`python src/search.py` ou teste equivalente)

- [ ] Retorna no máximo 10 trechos.
- [ ] Cada trecho mostra origem, página e score.
- [ ] Scores menores indicam trechos mais próximos.

## 4. Site (`streamlit run web/app.py`)

- [ ] Sidebar mostra "Configuração carregada".
- [ ] Upload de PDF grava o arquivo e mostra "PDF salvo".
- [ ] "Processar PDF (ingerir)" mostra páginas e chunks.
- [ ] Chat responde com base no PDF enviado.
- [ ] "Limpar base (trocar PDF)" limpa a collection, o histórico e o arquivo.
- [ ] Depois de limpar, é possível enviar e processar outro PDF sem reiniciar.
- [ ] Pergunta fora do contexto continua recusando após a troca.

## 5. Reingestão e reset

- [ ] Rodar `python src/ingest.py` duas vezes mantém a mesma quantidade de vetores.
- [ ] `docker compose down -v` + `docker compose up -d` recria a base do zero.
- [ ] Após o reset, a ingestão volta a funcionar.

## 6. Segurança

- [ ] `.env` não aparece em `git ls-files`.
- [ ] Nenhuma chave real aparece em README, testes, prints ou commits.
- [ ] Pergunta maliciosa ("ignore as regras...") não remove a política de recusa.
- [ ] Logs não imprimem a chave da API.

## 7. Entrega

- [ ] `document.pdf` é o PDF oficial do desafio.
- [ ] `README.md` explica pré-requisitos, execução e reingestão.
- [ ] Guia no Notion atualizado.
- [ ] `pytest -m "not integration"` e `pytest -m integration` passam.
