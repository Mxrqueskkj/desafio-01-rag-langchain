# -*- coding: utf-8 -*-
"""Testes de integração real: PostgreSQL/pgvector + API + Streamlit.

Execute somente com RUN_INTEGRATION=1, Docker no ar e .env válido.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request

import pytest
from sqlalchemy import create_engine, text

import chat
import ingest
import search

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def settings():
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Defina RUN_INTEGRATION=1 para rodar os testes de integração.")

    from config import load_settings

    try:
        configuracao = load_settings()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f".env inválido para integração: {exc}")

    engine = create_engine(configuracao.database_url)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"PostgreSQL indisponível: {exc}")
    finally:
        engine.dispose()

    return configuracao


def _contar_vetores(settings) -> int:
    engine = create_engine(settings.database_url)
    try:
        with engine.connect() as conn:
            return conn.execute(text("SELECT count(*) FROM langchain_pg_embedding")).scalar_one()
    finally:
        engine.dispose()


def test_pdf_tem_paginas(settings):
    paginas = ingest.load_pdf(settings.pdf_path)

    assert len(paginas) > 0
    assert any(pagina.page_content.strip() for pagina in paginas)


def test_ingestao_e_idempotencia(settings):
    resumo = ingest.ingest()

    assert resumo["pages"] > 0
    assert resumo["chunks"] > 0

    antes = _contar_vetores(settings)
    assert antes >= resumo["chunks"]

    ingest.ingest()
    depois = _contar_vetores(settings)

    assert depois == antes, f"Reingestão duplicou vetores: {antes} -> {depois}"


def test_busca_real_retorna_trechos_ordenados(settings):
    resultados = search.search("Qual é o tema principal do documento?", k=10)

    assert 1 <= len(resultados) <= 10
    scores = [score for _, score in resultados]
    assert scores == sorted(scores), "Scores devem vir em ordem crescente (cosseno)"

    for documento, score in resultados:
        assert documento.page_content.strip()
        assert "source" in documento.metadata
        assert isinstance(documento.metadata.get("page"), int)
        assert isinstance(score, float)

    contexto = search.format_context(resultados)
    assert "[Trecho 1" in contexto


def test_busca_respeita_k(settings):
    assert len(search.search("documento", k=1)) <= 1
    assert len(search.search("documento", k=3)) <= 3


def test_resposta_fundamentada(settings):
    resposta = chat.answer("Qual é o tema principal do documento?")

    assert isinstance(resposta, str)
    assert resposta.strip()
    assert resposta != chat.REFUSAL_MESSAGE
    assert len(resposta) < 5000


def test_recusa_fora_do_contexto(settings):
    assert chat.answer("Qual é a capital da França?") == chat.REFUSAL_MESSAGE


def test_recusa_para_opiniao(settings):
    assert chat.answer("Você acha que o desafio é difícil?") == chat.REFUSAL_MESSAGE


def test_streamlit_responde_http(settings):
    try:
        with urllib.request.urlopen("http://localhost:8501", timeout=10) as resposta:
            corpo = resposta.read(5000).decode("utf-8", errors="ignore")
            status = resposta.status
    except (urllib.error.URLError, TimeoutError) as exc:
        pytest.skip(f"Streamlit não está rodando em localhost:8501: {exc}")

    assert status == 200
    assert "RAG" in corpo or "streamlit" in corpo.lower()
