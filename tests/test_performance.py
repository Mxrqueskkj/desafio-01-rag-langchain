# -*- coding: utf-8 -*-
"""Testes de desempenho com limites generosos (evitam flakiness)."""

from __future__ import annotations

import time

import pytest
from langchain_core.documents import Document

import chat
import ingest
import search

pytestmark = pytest.mark.slow


def _medir(funcao):
    inicio = time.perf_counter()
    resultado = funcao()
    duracao = time.perf_counter() - inicio
    return resultado, duracao


def test_split_de_muitas_paginas():
    paginas = [
        Document(page_content=("conteudo da pagina " * 200), metadata={"page": i})
        for i in range(200)
    ]

    chunks, duracao = _medir(lambda: ingest.split_documents(paginas))

    assert chunks
    assert duracao < 15, f"split demorou {duracao:.2f}s"


def test_format_context_com_muitos_trechos():
    resultados = [
        (Document(page_content=f"texto {i}", metadata={"source": "a.pdf", "page": i}), i / 1000)
        for i in range(5000)
    ]

    formatado, duracao = _medir(lambda: search.format_context(resultados))

    assert formatado.count("[Trecho") == 5000
    assert duracao < 3, f"formatação demorou {duracao:.2f}s"


def test_build_prompt_com_contexto_grande():
    contexto = "palavra " * 150_000

    prompt, duracao = _medir(lambda: chat.build_prompt(contexto, "pergunta"))

    assert len(prompt) > 1_000_000
    assert duracao < 1, f"prompt demorou {duracao:.2f}s"


def test_busca_vazia_e_imediata():
    _, duracao = _medir(lambda: search.search("   "))

    assert duracao < 0.01, f"busca vazia demorou {duracao:.4f}s"


def test_metadados_de_muitos_chunks(tmp_path, monkeypatch, settings_factory):
    pdf = tmp_path / "documento.pdf"
    pdf.write_bytes(b"conteudo pequeno")
    monkeypatch.setattr(ingest, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))
    chunks = [Document(page_content=f"c{i}", metadata={"page": i}) for i in range(2000)]

    resultado, duracao = _medir(lambda: ingest.add_metadata(chunks))

    assert len(resultado) == 2000
    assert duracao < 2, f"metadados demoraram {duracao:.2f}s"
