# -*- coding: utf-8 -*-
"""Interface web simples (Streamlit) para o Desafio 01 - RAG.

Execute a partir da raiz do projeto:
    streamlit run web/app.py

Requisitos (instale em um venv separado ou adicione ao requirements.txt):
    streamlit

O banco PostgreSQL/pgvector precisa estar no ar (docker compose up -d)
e o arquivo .env precisa estar preenchido (chave de API, modelos, etc.).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Garante que a pasta src/ do projeto seja importavel.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from config import get_vector_store, load_settings
from ingest import (
    add_metadata,
    load_pdf,
    save_to_database,
    split_documents,
    validate_environment,
)
from chat import answer

UPLOAD_DIR = PROJECT_ROOT / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
UPLOADED_PDF = UPLOAD_DIR / "uploaded.pdf"


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pdf_path" not in st.session_state:
        st.session_state.pdf_path = None
    if "ingested" not in st.session_state:
        st.session_state.ingested = False


def render_sidebar() -> None:
    st.sidebar.title("Configuração")
    try:
        settings = load_settings()
        st.sidebar.success("Configuração carregada")
        st.sidebar.write(f"**Collection:** {settings.collection_name}")
        st.sidebar.write(f"**Modelo de chat:** {settings.chat_model}")
        st.sidebar.write(f"**Embeddings:** {settings.embedding_model}")
        st.sidebar.write(f"**PDF_PATH:** {settings.pdf_path}")
    except Exception as exc:  # noqa: BLE001
        st.sidebar.error(f"Configuração inválida: {exc}")
        st.sidebar.info(
            "Preencha o arquivo .env na raiz do projeto antes de usar o app."
        )
        return

    st.sidebar.divider()
    st.sidebar.subheader("PDF")
    uploaded = st.sidebar.file_uploader("Envie um PDF", type=["pdf"])
    if uploaded is not None:
        UPLOADED_PDF.write_bytes(uploaded.getvalue())
        st.session_state.pdf_path = str(UPLOADED_PDF)
        st.sidebar.success(f"PDF salvo: {UPLOADED_PDF.name}")

    if st.session_state.pdf_path:
        if st.sidebar.button("Processar PDF (ingerir)"):
            process_pdf(st.session_state.pdf_path)

    st.sidebar.divider()
    if st.sidebar.button("Limpar base (trocar PDF)", type="secondary"):
        clear_base()

    if st.session_state.ingested:
        st.sidebar.success("Base ingerida e pronta para perguntas.")
    else:
        st.sidebar.warning("Ainda não foi ingerido. Processe um PDF primeiro.")


def process_pdf(pdf_path: str) -> None:
    # Garante que a ingestão use o PDF enviado, mesmo com .env apontando para outro.
    os.environ["PDF_PATH"] = pdf_path
    try:
        validate_environment()
        settings = load_settings()
        pages = load_pdf(settings.pdf_path)
        chunks = split_documents(pages)
        chunks = add_metadata(chunks)
        save_to_database(chunks)
        st.session_state.ingested = True
        st.sidebar.success(
            f"Ingestão concluída: {len(pages)} páginas, {len(chunks)} chunks."
        )
    except Exception as exc:  # noqa: BLE001
        st.session_state.ingested = False
        st.sidebar.error(f"Erro na ingestão: {exc}")


def clear_base() -> None:
    try:
        store = get_vector_store()
        store.delete_collection()
        store.create_collection()
        st.sidebar.success("Base limpa. Envie um novo PDF.")
    except Exception as exc:  # noqa: BLE001
        st.sidebar.error(f"Erro ao limpar a base: {exc}")
    finally:
        st.session_state.messages = []
        st.session_state.ingested = False
        st.session_state.pdf_path = None
        if UPLOADED_PDF.exists():
            try:
                UPLOADED_PDF.unlink()
            except OSError:
                pass


def render_chat() -> None:
    st.title("Chat RAG — Pergunte ao seu PDF")
    st.caption(
        "As respostas são geradas somente com base nos trechos recuperados do documento."
    )

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    question = st.chat_input("Digite sua pergunta...")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Buscando e gerando resposta..."):
            try:
                resposta = answer(question)
            except Exception as exc:  # noqa: BLE001
                resposta = f"Erro ao responder: {exc}"
        st.markdown(resposta)

    st.session_state.messages.append({"role": "assistant", "content": resposta})


def main() -> None:
    st.set_page_config(page_title="RAG - Desafio 01", page_icon="📚", layout="wide")
    init_state()
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
