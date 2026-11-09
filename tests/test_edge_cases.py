# -*- coding: utf-8 -*-
"""Casos de borda: entradas vazias, longas, Unicode e limites."""

from __future__ import annotations

import pytest
from langchain_core.documents import Document

import chat
import config
import ingest
import search


def test_search_com_unicode_e_emoji(monkeypatch):
    class FakeStore:
        def __init__(self):
            self.chamadas = []

        def similarity_search_with_score(self, query, k=10):
            self.chamadas.append((query, k))
            return []

    store = FakeStore()
    monkeypatch.setattr(search, "get_vector_store", lambda: store)

    search.search("Qual é o resumo? 📚🚀")

    assert store.chamadas == [("Qual é o resumo? 📚🚀", 10)]


def test_search_com_quebra_de_linha(monkeypatch):
    class FakeStore:
        def __init__(self):
            self.chamadas = []

        def similarity_search_with_score(self, query, k=10):
            self.chamadas.append((query, k))
            return []

    store = FakeStore()
    monkeypatch.setattr(search, "get_vector_store", lambda: store)

    search.search("linha 1\nlinha 2\ttab")

    assert store.chamadas[0][0] == "linha 1\nlinha 2\ttab"


def test_search_com_pergunta_muito_longa(monkeypatch):
    class FakeStore:
        def __init__(self):
            self.chamadas = []

        def similarity_search_with_score(self, query, k=10):
            self.chamadas.append((query, k))
            return []

    store = FakeStore()
    monkeypatch.setattr(search, "get_vector_store", lambda: store)
    pergunta = "a" * 100_000

    search.search(pergunta)

    assert len(store.chamadas[0][0]) == 100_000


@pytest.mark.parametrize("k", [1, 2, 100])
def test_search_repassa_k_extremos(monkeypatch, k):
    class FakeStore:
        def __init__(self):
            self.chamadas = []

        def similarity_search_with_score(self, query, k=10):
            self.chamadas.append((query, k))
            return []

    store = FakeStore()
    monkeypatch.setattr(search, "get_vector_store", lambda: store)

    search.search("pergunta", k=k)

    assert store.chamadas[0][1] == k


def test_format_context_pagina_zero_vira_um():
    doc = Document(page_content="a", metadata={"source": "a.pdf", "page": 0})

    assert "página 1" in search.format_context([(doc, 0.5)])


def test_format_context_score_inteiro():
    doc = Document(page_content="a", metadata={"source": "a.pdf", "page": 0})

    assert "score 0.0000" in search.format_context([(doc, 0)])


def test_format_context_muitos_trechos():
    resultados = [
        (Document(page_content=f"texto {i}", metadata={"source": "a.pdf", "page": i}), i / 100)
        for i in range(500)
    ]

    formatado = search.format_context(resultados)

    assert "Trecho 1" in formatado
    assert "Trecho 500" in formatado
    assert formatado.count("[Trecho") == 500


def test_build_prompt_contexto_muito_longo():
    contexto = "x" * 1_000_000

    prompt = chat.build_prompt(contexto, "pergunta")

    assert contexto in prompt
    assert "REGRAS:" in prompt


def test_load_settings_aceita_somente_openai(clean_env, monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://rag:rag@localhost:5432/rag")
    monkeypatch.setenv("PG_VECTOR_COLLECTION_NAME", "desafio01")
    monkeypatch.setenv("PDF_PATH", "document.pdf")
    monkeypatch.setenv("CHAT_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-teste")

    settings = config.load_settings()

    assert settings.openai_api_key == "sk-teste"
    assert settings.google_api_key is None


def test_add_metadata_lista_vazia(tmp_path, monkeypatch, settings_factory):
    pdf = tmp_path / "documento.pdf"
    pdf.write_bytes(b"conteudo")
    monkeypatch.setattr(ingest, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))

    assert ingest.add_metadata([]) == []


def test_add_metadata_preserva_metadados_extras(tmp_path, monkeypatch, settings_factory):
    pdf = tmp_path / "documento.pdf"
    pdf.write_bytes(b"conteudo")
    monkeypatch.setattr(ingest, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))
    chunk = Document(page_content="a", metadata={"page": 1, "extra": "mantido"})

    resultado = ingest.add_metadata([chunk])

    assert resultado[0].metadata["extra"] == "mantido"
    assert resultado[0].metadata["page"] == 1


def test_split_documents_texto_sem_separadores():
    pagina = Document(page_content="x" * 5000, metadata={"page": 0})

    chunks = ingest.split_documents([pagina])

    assert chunks
    assert all(len(chunk.page_content) <= ingest.CHUNK_SIZE for chunk in chunks)


def test_split_documents_unicode():
    pagina = Document(page_content="ação 😀 " * 1000, metadata={"page": 0})

    chunks = ingest.split_documents([pagina])

    assert chunks
    assert all(len(chunk.page_content) <= ingest.CHUNK_SIZE for chunk in chunks)
    assert "😀" in "".join(chunk.page_content for chunk in chunks)


def test_load_pdf_caminho_com_espacos(monkeypatch):
    capturado = {}

    class FakeLoader:
        def __init__(self, path, mode=None):
            capturado["path"] = path
            capturado["mode"] = mode

        def load(self):
            return [Document(page_content="ok", metadata={"page": 0})]

    monkeypatch.setattr(ingest, "PyPDFLoader", FakeLoader)

    ingest.load_pdf("pasta com espacos/documento final.pdf")

    assert capturado["path"].endswith("documento final.pdf")
    assert capturado["mode"] == "page"


def test_call_llm_resposta_vazia(monkeypatch, settings_factory):
    class FakeLLM:
        def __init__(self, **kwargs):
            pass

        def invoke(self, prompt):
            return type("Resposta", (), {"content": ""})()

    monkeypatch.setattr(chat, "load_settings", lambda: settings_factory())
    monkeypatch.setattr(chat, "ChatGoogleGenerativeAI", FakeLLM)

    assert chat.call_llm("prompt") == ""


def test_answer_com_trecho_vazio_ainda_chama_llm(monkeypatch):
    doc = Document(page_content="", metadata={"source": "a.pdf", "page": 0})
    monkeypatch.setattr(chat, "search", lambda pergunta: [(doc, 0.1)])
    monkeypatch.setattr(chat, "call_llm", lambda prompt: "ok")

    assert chat.answer("pergunta") == "ok"
