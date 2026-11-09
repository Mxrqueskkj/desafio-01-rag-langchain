# -*- coding: utf-8 -*-
"""Configuração compartilhada dos testes do Desafio 01 - RAG.

Os testes unitários NÃO acessam rede, banco nem APIs pagas.
Os testes de integração só rodam com RUN_INTEGRATION=1.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

for path in (str(ROOT), str(SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Raiz do projeto."""
    return ROOT


@pytest.fixture(scope="session")
def src_dir() -> Path:
    """Pasta src/ com os módulos do desafio."""
    return SRC


@pytest.fixture
def settings_factory():
    """Cria Settings válidos para testes, permitindo sobrescrever campos."""
    from config import Settings

    def _make(**overrides):
        base = dict(
            database_url="postgresql+psycopg://rag:rag@localhost:5432/rag",
            collection_name="desafio01",
            pdf_path="document.pdf",
            chat_model="gemini-3.5-flash",
            embedding_model="gemini-embedding-001",
            openai_api_key=None,
            google_api_key="chave-de-teste",
        )
        base.update(overrides)
        return Settings(**base)

    return _make


@pytest.fixture
def clean_env(monkeypatch):
    """Remove variáveis do .env para testar cenários de configuração ausente."""
    for key in (
        "DATABASE_URL",
        "PG_VECTOR_COLLECTION_NAME",
        "PDF_PATH",
        "CHAT_MODEL",
        "EMBEDDING_MODEL",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


@pytest.fixture(scope="session")
def integration_enabled() -> bool:
    """Indica se os testes de integração foram habilitados explicitamente."""
    return os.getenv("RUN_INTEGRATION") == "1"
