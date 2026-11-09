# -*- coding: utf-8 -*-
"""Testes unitários de src/ingest.py (sem rede e sem banco real)."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from langchain_core.documents import Document

import ingest


def test_constantes_do_desafio():
    assert ingest.CHUNK_SIZE == 1000
    assert ingest.CHUNK_OVERLAP == 150


def test_split_documents_lista_vazia():
    assert ingest.split_documents([]) == []


def test_split_documents_respeita_tamanho_maximo():
    pagina = Document(page_content="a" * 5000, metadata={"page": 0})

    chunks = ingest.split_documents([pagina])

    assert len(chunks) >= 5
    assert all(len(chunk.page_content) <= ingest.CHUNK_SIZE for chunk in chunks)


def test_split_documents_preserva_metadados():
    pagina = Document(page_content="texto " * 500, metadata={"page": 7, "source": "a.pdf"})

    chunks = ingest.split_documents([pagina])

    assert chunks
    assert all(chunk.metadata["page"] == 7 for chunk in chunks)
    assert all(chunk.metadata["source"] == "a.pdf" for chunk in chunks)


def test_add_metadata_preenche_campos(tmp_path, monkeypatch, settings_factory):
    pdf = tmp_path / "documento.pdf"
    pdf.write_bytes(b"conteudo do pdf")
    monkeypatch.setattr(ingest, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))

    chunks = [
        Document(page_content="primeiro", metadata={"page": 2}),
        Document(page_content="segundo", metadata={"page": 3}),
    ]

    resultado = ingest.add_metadata(chunks)

    hash_esperado = hashlib.sha256(b"conteudo do pdf").hexdigest()
    assert [c.metadata["chunk_index"] for c in resultado] == [0, 1]
    assert [c.metadata["page"] for c in resultado] == [2, 3]
    assert all(c.metadata["source"] == "documento.pdf" for c in resultado)
    assert all(c.metadata["document_hash"] == hash_esperado for c in resultado)
    assert all(c.metadata["embedding_model"] == "gemini-embedding-001" for c in resultado)


def test_add_metadata_page_padrao_zero(tmp_path, monkeypatch, settings_factory):
    pdf = tmp_path / "documento.pdf"
    pdf.write_bytes(b"x")
    monkeypatch.setattr(ingest, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))

    resultado = ingest.add_metadata([Document(page_content="sem pagina", metadata={})])

    assert resultado[0].metadata["page"] == 0


def test_add_metadata_ids_sao_deterministicos(tmp_path, monkeypatch, settings_factory):
    pdf = tmp_path / "documento.pdf"
    pdf.write_bytes(b"conteudo")
    monkeypatch.setattr(ingest, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))

    primeira = ingest.add_metadata([Document(page_content="a", metadata={})])
    segunda = ingest.add_metadata([Document(page_content="a", metadata={})])

    assert primeira[0].metadata["document_hash"] == segunda[0].metadata["document_hash"]
    assert primeira[0].metadata["chunk_index"] == segunda[0].metadata["chunk_index"]


def test_save_to_database_sem_chunks_falha():
    with pytest.raises(ValueError, match="Nenhum chunk"):
        ingest.save_to_database([])


def test_save_to_database_gera_ids_deterministicos(monkeypatch):
    class FakeStore:
        def __init__(self):
            self.documentos = None
            self.ids = None

        def add_documents(self, documents, ids=None):
            self.documentos = documents
            self.ids = ids
            return ids

    store = FakeStore()
    monkeypatch.setattr(ingest, "get_vector_store", lambda: store)
    chunks = [
        Document(page_content="a", metadata={"document_hash": "hash1", "chunk_index": 0}),
        Document(page_content="b", metadata={"document_hash": "hash1", "chunk_index": 1}),
    ]

    ingest.save_to_database(chunks)

    assert store.documentos == chunks
    assert store.ids == ["hash1-0", "hash1-1"]


def test_load_pdf_devolve_paginas(monkeypatch):
    class FakeLoader:
        def __init__(self, path, mode=None):
            self.path = path
            self.mode = mode

        def load(self):
            return [Document(page_content="pagina um", metadata={"page": 0})]

    monkeypatch.setattr(ingest, "PyPDFLoader", FakeLoader)

    paginas = ingest.load_pdf("documento.pdf")

    assert len(paginas) == 1
    assert paginas[0].page_content == "pagina um"


def test_load_pdf_vazio_falha(monkeypatch):
    class FakeLoader:
        def __init__(self, *args, **kwargs):
            pass

        def load(self):
            return []

    monkeypatch.setattr(ingest, "PyPDFLoader", FakeLoader)

    with pytest.raises(ValueError, match="não produziu texto"):
        ingest.load_pdf("documento.pdf")


def test_load_pdf_apenas_espacos_falha(monkeypatch):
    class FakeLoader:
        def __init__(self, *args, **kwargs):
            pass

        def load(self):
            return [Document(page_content="   \n\t ", metadata={"page": 0})]

    monkeypatch.setattr(ingest, "PyPDFLoader", FakeLoader)

    with pytest.raises(ValueError, match="OCR"):
        ingest.load_pdf("documento.pdf")


def test_validate_environment_pdf_inexistente(monkeypatch, settings_factory):
    monkeypatch.setattr(
        ingest,
        "load_settings",
        lambda: settings_factory(pdf_path="nao_existe_12345.pdf"),
    )

    with pytest.raises(FileNotFoundError, match="PDF não encontrado"):
        ingest.validate_environment()


def test_validate_environment_pdf_vazio(tmp_path, monkeypatch, settings_factory):
    pdf = tmp_path / "vazio.pdf"
    pdf.write_bytes(b"")
    monkeypatch.setattr(ingest, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))

    with pytest.raises(ValueError, match="PDF está vazio"):
        ingest.validate_environment()


def test_validate_environment_banco_indisponivel(tmp_path, monkeypatch, settings_factory):
    pdf = tmp_path / "ok.pdf"
    pdf.write_bytes(b"conteudo")

    class FakeEngine:
        def connect(self):
            raise OSError("banco fora do ar")

        def dispose(self):
            pass

    monkeypatch.setattr(ingest, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))
    monkeypatch.setattr(ingest, "create_engine", lambda _url: FakeEngine())

    with pytest.raises(RuntimeError, match="Não foi possível conectar"):
        ingest.validate_environment()


def test_validate_environment_sucesso(tmp_path, monkeypatch, settings_factory):
    pdf = tmp_path / "ok.pdf"
    pdf.write_bytes(b"conteudo")

    class FakeConnection:
        def execute(self, _sql):
            return None

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class FakeEngine:
        def connect(self):
            return FakeConnection()

        def dispose(self):
            pass

    monkeypatch.setattr(ingest, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))
    monkeypatch.setattr(ingest, "create_engine", lambda _url: FakeEngine())

    assert ingest.validate_environment() is None


def test_ingest_orquestra_o_fluxo(monkeypatch, capsys, settings_factory):
    chamadas = []
    paginas = [Document(page_content="p1", metadata={"page": 0})]
    chunks = [Document(page_content="c1", metadata={"page": 0})]
    chunks_com_meta = [Document(page_content="c1", metadata={"page": 0, "chunk_index": 0})]

    monkeypatch.setattr(ingest, "validate_environment", lambda: chamadas.append("validar"))
    monkeypatch.setattr(ingest, "load_settings", lambda: settings_factory())
    monkeypatch.setattr(ingest, "load_pdf", lambda path: chamadas.append("ler") or paginas)
    monkeypatch.setattr(ingest, "split_documents", lambda docs: chamadas.append("dividir") or chunks)
    monkeypatch.setattr(ingest, "add_metadata", lambda docs: chamadas.append("metadados") or chunks_com_meta)
    monkeypatch.setattr(ingest, "save_to_database", lambda docs: chamadas.append("gravar"))

    resumo = ingest.ingest()

    assert resumo == {"pages": 1, "chunks": 1}
    assert chamadas == ["validar", "ler", "dividir", "metadados", "gravar"]
    assert "Ingestão concluída: 1 páginas, 1 chunks." in capsys.readouterr().out


def test_ingest_nao_grava_quando_validacao_falha(monkeypatch):
    monkeypatch.setattr(
        ingest,
        "validate_environment",
        lambda: (_ for _ in ()).throw(RuntimeError("sem banco")),
    )

    with pytest.raises(RuntimeError, match="sem banco"):
        ingest.ingest()
