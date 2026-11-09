# -*- coding: utf-8 -*-
"""Testes unitários de src/search.py (sem rede e sem banco)."""

from __future__ import annotations

import pytest
from langchain_core.documents import Document

import search


class FakeStore:
    def __init__(self, resultados=None):
        self.resultados = resultados or []
        self.chamadas = []

    def similarity_search_with_score(self, query, k=10):
        self.chamadas.append((query, k))
        return self.resultados


def test_search_vazia_nao_consulta_o_banco(monkeypatch):
    store = FakeStore()

    def explode():
        raise AssertionError("get_vector_store não deveria ser chamado")

    monkeypatch.setattr(search, "get_vector_store", explode)

    assert search.search("") == []
    assert search.search("   ") == []
    assert search.search("\n\t") == []


def test_search_usa_k_padrao_10(monkeypatch):
    store = FakeStore([(Document(page_content="x"), 0.1)])
    monkeypatch.setattr(search, "get_vector_store", lambda: store)

    search.search("pergunta")

    assert store.chamadas == [("pergunta", 10)]


def test_search_repassa_k_customizado(monkeypatch):
    store = FakeStore([])
    monkeypatch.setattr(search, "get_vector_store", lambda: store)

    assert search.search("pergunta", k=3) == []
    assert store.chamadas == [("pergunta", 3)]


def test_search_devolve_pares_documento_score(monkeypatch):
    doc = Document(page_content="conteudo", metadata={"page": 0})
    store = FakeStore([(doc, 0.25)])
    monkeypatch.setattr(search, "get_vector_store", lambda: store)

    resultado = search.search("pergunta")

    assert resultado == [(doc, 0.25)]
    assert resultado[0][0] is doc


def test_format_context_vazio():
    assert search.format_context([]) == ""


def test_format_context_inclui_origem_pagina_e_score():
    doc = Document(
        page_content="texto de teste",
        metadata={"source": "document.pdf", "page": 2},
    )

    formatado = search.format_context([(doc, 0.123456)])

    assert "[Trecho 1 | document.pdf | página 3 | score 0.1235]" in formatado
    assert "texto de teste" in formatado


def test_format_context_varias_partes():
    docs = [
        (Document(page_content="primeiro", metadata={"source": "a.pdf", "page": 0}), 0.1),
        (Document(page_content="segundo", metadata={"source": "a.pdf", "page": 1}), 0.2),
    ]

    formatado = search.format_context(docs)

    assert "Trecho 1" in formatado
    assert "Trecho 2" in formatado
    assert "primeiro" in formatado
    assert "segundo" in formatado
    assert "\n\n" in formatado


def test_format_context_pagina_ausente_ou_invalida():
    sem_pagina = Document(page_content="a", metadata={"source": "a.pdf"})
    pagina_texto = Document(
        page_content="b",
        metadata={"source": "a.pdf", "page": "dois"},
    )

    formatado = search.format_context([(sem_pagina, 0.1), (pagina_texto, 0.2)])

    assert formatado.count("página ?") == 2


def test_format_context_score_negativo_e_arredondamento():
    doc = Document(page_content="a", metadata={"source": "a.pdf", "page": 0})

    formatado = search.format_context([(doc, -0.00005)])

    assert "score -0.0001" in formatado


@pytest.mark.parametrize("score", [0.0, 0.99999, 1.0])
def test_format_context_limites_de_score(score):
    doc = Document(page_content="a", metadata={"source": "a.pdf", "page": 0})

    formatado = search.format_context([(doc, score)])

    assert f"score {score:.4f}" in formatado
