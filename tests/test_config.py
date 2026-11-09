# -*- coding: utf-8 -*-
"""Testes unitários de src/config.py (sem rede e sem banco)."""

from __future__ import annotations

import pytest

import config


def _set_required(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://rag:rag@localhost:5432/rag")
    monkeypatch.setenv("PG_VECTOR_COLLECTION_NAME", "desafio01")
    monkeypatch.setenv("PDF_PATH", "document.pdf")
    monkeypatch.setenv("CHAT_MODEL", "gemini-3.5-flash")
    monkeypatch.setenv("EMBEDDING_MODEL", "gemini-embedding-001")


def test_load_settings_le_todos_os_campos(clean_env, monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    _set_required(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "chave-google")

    settings = config.load_settings()

    assert settings.database_url.endswith("/rag")
    assert settings.collection_name == "desafio01"
    assert settings.pdf_path == "document.pdf"
    assert settings.chat_model == "gemini-3.5-flash"
    assert settings.embedding_model == "gemini-embedding-001"
    assert settings.google_api_key == "chave-google"
    assert settings.openai_api_key is None


def test_load_settings_remove_espacos(clean_env, monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    _set_required(monkeypatch)
    monkeypatch.setenv("PG_VECTOR_COLLECTION_NAME", "  desafio01  ")
    monkeypatch.setenv("GOOGLE_API_KEY", "chave")

    assert config.load_settings().collection_name == "desafio01"


def test_load_settings_lista_variaveis_obrigatorias_faltando(clean_env, monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://rag:rag@localhost:5432/rag")
    monkeypatch.setenv("GOOGLE_API_KEY", "chave")

    with pytest.raises(ValueError) as exc:
        config.load_settings()

    mensagem = str(exc.value)
    for nome in (
        "PG_VECTOR_COLLECTION_NAME",
        "PDF_PATH",
        "CHAT_MODEL",
        "EMBEDDING_MODEL",
    ):
        assert nome in mensagem


def test_load_settings_exige_uma_chave_de_provedor(clean_env, monkeypatch):
    monkeypatch.setattr(config, "load_dotenv", lambda: None)
    _set_required(monkeypatch)

    with pytest.raises(ValueError, match="OPENAI_API_KEY ou GOOGLE_API_KEY"):
        config.load_settings()


def test_get_embeddings_usa_openai_quando_chave_existe(monkeypatch, settings_factory):
    criado = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            criado.update(kwargs)

    monkeypatch.setattr(config, "load_settings", lambda: settings_factory(
        openai_api_key="sk-teste", google_api_key=None
    ))
    monkeypatch.setattr(config, "OpenAIEmbeddings", FakeOpenAI)

    resultado = config.get_embeddings()

    assert isinstance(resultado, FakeOpenAI)
    assert criado["model"] == "gemini-embedding-001"
    assert criado["api_key"] == "sk-teste"


def test_get_embeddings_usa_google_como_fallback(monkeypatch, settings_factory):
    criado = {}

    class FakeGoogle:
        def __init__(self, **kwargs):
            criado.update(kwargs)

    monkeypatch.setattr(config, "load_settings", lambda: settings_factory(
        openai_api_key=None, google_api_key="chave-google"
    ))
    monkeypatch.setattr(config, "GoogleGenerativeAIEmbeddings", FakeGoogle)

    resultado = config.get_embeddings()

    assert isinstance(resultado, FakeGoogle)
    assert criado["model"] == "gemini-embedding-001"
    assert criado["google_api_key"] == "chave-google"


def test_get_embeddings_sem_chave_falha(monkeypatch, settings_factory):
    monkeypatch.setattr(config, "load_settings", lambda: settings_factory(
        openai_api_key=None, google_api_key=None
    ))

    with pytest.raises(ValueError, match="Nenhuma chave"):
        config.get_embeddings()


def test_get_vector_store_repassa_parametros(monkeypatch, settings_factory):
    embeddings = object()
    criado = {}

    class FakePGVector:
        def __init__(self, **kwargs):
            criado.update(kwargs)

    monkeypatch.setattr(config, "load_settings", lambda: settings_factory())
    monkeypatch.setattr(config, "get_embeddings", lambda: embeddings)
    monkeypatch.setattr(config, "PGVector", FakePGVector)

    resultado = config.get_vector_store()

    assert isinstance(resultado, FakePGVector)
    assert criado["embeddings"] is embeddings
    assert criado["collection_name"] == "desafio01"
    assert criado["connection"].endswith("/rag")
    assert criado["use_jsonb"] is True
