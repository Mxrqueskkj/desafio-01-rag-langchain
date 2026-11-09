# -*- coding: utf-8 -*-
"""Testes da interface Streamlit (sem banco e sem API)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WEB_APP = ROOT / "web" / "app.py"

pytestmark = pytest.mark.web


def _load_app():
    spec = importlib.util.spec_from_file_location("web_app_test", WEB_APP)
    module = importlib.util.module_from_spec(spec)
    sys.modules["web_app_test"] = module
    spec.loader.exec_module(module)
    return module


class FakeState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class FakeContext:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeSidebar:
    def __init__(self, button_result=False):
        self.button_result = button_result
        self.chamadas = []

    def _registrar(self, nome, *args, **kwargs):
        self.chamadas.append((nome, args, kwargs))

    def title(self, *args, **kwargs):
        self._registrar("title", *args, **kwargs)

    def success(self, *args, **kwargs):
        self._registrar("success", *args, **kwargs)

    def write(self, *args, **kwargs):
        self._registrar("write", *args, **kwargs)

    def error(self, *args, **kwargs):
        self._registrar("error", *args, **kwargs)

    def info(self, *args, **kwargs):
        self._registrar("info", *args, **kwargs)

    def divider(self, *args, **kwargs):
        self._registrar("divider", *args, **kwargs)

    def subheader(self, *args, **kwargs):
        self._registrar("subheader", *args, **kwargs)

    def warning(self, *args, **kwargs):
        self._registrar("warning", *args, **kwargs)

    def button(self, *args, **kwargs):
        self._registrar("button", *args, **kwargs)
        if isinstance(self.button_result, set):
            return bool(args) and args[0] in self.button_result
        return bool(self.button_result)

    def file_uploader(self, *args, **kwargs):
        self._registrar("file_uploader", *args, **kwargs)
        return None


class FakeSt:
    def __init__(self, button_result=False, chat_input=None):
        self.session_state = FakeState(
            messages=[], pdf_path=None, ingested=False, uploader_key=0
        )
        self.sidebar = FakeSidebar(button_result)
        self.chat_input_value = chat_input
        self.markdowns = []
        self.rerun_chamado = False

    def rerun(self):
        self.rerun_chamado = True

    def set_page_config(self, *args, **kwargs):
        pass

    def title(self, *args, **kwargs):
        pass

    def caption(self, *args, **kwargs):
        pass

    def markdown(self, texto, *args, **kwargs):
        self.markdowns.append(texto)

    def chat_message(self, *args, **kwargs):
        return FakeContext()

    def spinner(self, *args, **kwargs):
        return FakeContext()

    def chat_input(self, *args, **kwargs):
        return self.chat_input_value


@pytest.fixture
def app_module():
    return _load_app()


def test_app_importa_e_compila():
    modulo = _load_app()
    assert callable(modulo.main)
    assert callable(modulo.process_pdf)
    assert callable(modulo.clear_base)


def test_init_state_cria_campos(app_module, monkeypatch):
    fake = FakeSt()
    fake.session_state = FakeState()
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(app_module, "base_tem_dados", lambda: False)

    app_module.init_state()

    assert fake.session_state.messages == []
    assert fake.session_state.pdf_path is None
    assert fake.session_state.ingested is False
    assert fake.session_state.uploader_key == 0


def test_init_state_preserva_valores_existentes(app_module, monkeypatch):
    fake = FakeSt()
    fake.session_state = FakeState(messages=[{"role": "user"}], pdf_path="a.pdf", ingested=True)
    monkeypatch.setattr(app_module, "st", fake)

    app_module.init_state()

    assert fake.session_state.messages == [{"role": "user"}]
    assert fake.session_state.pdf_path == "a.pdf"
    assert fake.session_state.ingested is True


def test_init_state_marca_ingerido_quando_base_tem_dados(app_module, monkeypatch):
    fake = FakeSt()
    fake.session_state = FakeState()
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(app_module, "base_tem_dados", lambda: True)

    app_module.init_state()

    assert fake.session_state.ingested is True


def test_base_tem_dados_verdadeiro(app_module, monkeypatch, settings_factory):
    class FakeResult:
        def scalar_one(self):
            return 3

    class FakeConn:
        def execute(self, *args, **kwargs):
            return FakeResult()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class FakeEngine:
        def connect(self):
            return FakeConn()

        def dispose(self):
            pass

    monkeypatch.setattr(app_module, "load_settings", lambda: settings_factory())
    monkeypatch.setattr(app_module, "create_engine", lambda url: FakeEngine())

    assert app_module.base_tem_dados() is True


def test_base_tem_dados_falso(app_module, monkeypatch, settings_factory):
    class FakeResult:
        def scalar_one(self):
            return 0

    class FakeConn:
        def execute(self, *args, **kwargs):
            return FakeResult()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    class FakeEngine:
        def connect(self):
            return FakeConn()

        def dispose(self):
            pass

    monkeypatch.setattr(app_module, "load_settings", lambda: settings_factory())
    monkeypatch.setattr(app_module, "create_engine", lambda url: FakeEngine())

    assert app_module.base_tem_dados() is False


def test_base_tem_dados_com_erro_retorna_false(app_module, monkeypatch):
    def falha():
        raise RuntimeError("banco fora")

    monkeypatch.setattr(app_module, "load_settings", falha)

    assert app_module.base_tem_dados() is False


def test_render_sidebar_configuracao_valida(app_module, monkeypatch, settings_factory):
    fake = FakeSt()
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(app_module, "load_settings", lambda: settings_factory())

    app_module.render_sidebar()

    nomes = [c[0] for c in fake.sidebar.chamadas]
    assert "success" in nomes
    assert "file_uploader" in nomes
    assert "warning" in nomes
    textos = [c[1][0] for c in fake.sidebar.chamadas if c[1]]
    assert any("Configuração carregada" in t for t in textos)
    assert any("desafio01" in t for t in textos)


def test_render_sidebar_configuracao_invalida(app_module, monkeypatch):
    fake = FakeSt()
    monkeypatch.setattr(app_module, "st", fake)

    def falha():
        raise ValueError("faltando chave")

    monkeypatch.setattr(app_module, "load_settings", falha)

    app_module.render_sidebar()

    nomes = [c[0] for c in fake.sidebar.chamadas]
    assert "error" in nomes
    assert "info" in nomes
    assert "file_uploader" not in nomes


def test_render_sidebar_botao_processar(app_module, monkeypatch, settings_factory, tmp_path):
    fake = FakeSt(button_result={"Processar PDF (ingerir)"})
    fake.session_state.pdf_path = str(tmp_path / "enviado.pdf")
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(app_module, "load_settings", lambda: settings_factory())
    chamadas = []
    monkeypatch.setattr(app_module, "process_pdf", lambda path: chamadas.append(path))

    app_module.render_sidebar()

    assert chamadas == [fake.session_state.pdf_path]


def test_process_pdf_sucesso(app_module, monkeypatch, settings_factory, tmp_path):
    pdf = tmp_path / "enviado.pdf"
    pdf.write_bytes(b"pdf")
    fake = FakeSt()
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(app_module, "validate_environment", lambda: None)
    monkeypatch.setattr(app_module, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))
    monkeypatch.setattr(app_module, "load_pdf", lambda path: ["pagina1", "pagina2"])
    monkeypatch.setattr(app_module, "split_documents", lambda pages: ["c1", "c2", "c3"])
    monkeypatch.setattr(app_module, "add_metadata", lambda chunks: chunks)
    monkeypatch.setattr(app_module, "save_to_database", lambda chunks: None)
    monkeypatch.setenv("PDF_PATH", "document.pdf")

    app_module.process_pdf(str(pdf))

    assert fake.session_state.ingested is True
    assert any(
        "Ingestão concluída: 2 páginas, 3 chunks" in c[1][0]
        for c in fake.sidebar.chamadas
        if c[0] == "success"
    )
    import os

    assert os.environ["PDF_PATH"] == "document.pdf"


def test_process_pdf_restaura_env_quando_nao_existia(
    app_module, monkeypatch, settings_factory, tmp_path
):
    pdf = tmp_path / "enviado.pdf"
    pdf.write_bytes(b"pdf")
    fake = FakeSt()
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(app_module, "validate_environment", lambda: None)
    monkeypatch.setattr(app_module, "load_settings", lambda: settings_factory(pdf_path=str(pdf)))
    monkeypatch.setattr(app_module, "load_pdf", lambda path: ["p1"])
    monkeypatch.setattr(app_module, "split_documents", lambda pages: ["c1"])
    monkeypatch.setattr(app_module, "add_metadata", lambda chunks: chunks)
    monkeypatch.setattr(app_module, "save_to_database", lambda chunks: None)
    monkeypatch.delenv("PDF_PATH", raising=False)

    app_module.process_pdf(str(pdf))

    import os

    assert "PDF_PATH" not in os.environ


def test_process_pdf_erro(app_module, monkeypatch):
    fake = FakeSt()
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(app_module, "validate_environment", lambda: None)
    monkeypatch.setattr(app_module, "load_settings", lambda: type("S", (), {"pdf_path": "x.pdf"})())
    monkeypatch.setattr(
        app_module,
        "load_pdf",
        lambda path: (_ for _ in ()).throw(ValueError("PDF inválido")),
    )

    app_module.process_pdf("x.pdf")

    assert fake.session_state.ingested is False
    assert any(
        "Erro na ingestão: PDF inválido" in c[1][0]
        for c in fake.sidebar.chamadas
        if c[0] == "error"
    )


def test_clear_base_sucesso(app_module, monkeypatch, tmp_path):
    fake = FakeSt()
    fake.session_state.messages = [{"role": "user", "content": "oi"}]
    fake.session_state.ingested = True
    fake.session_state.pdf_path = "enviado.pdf"
    monkeypatch.setattr(app_module, "st", fake)

    upload = tmp_path / "uploaded.pdf"
    upload.write_bytes(b"pdf")
    monkeypatch.setattr(app_module, "UPLOADED_PDF", upload)

    chamadas = []

    class FakeStore:
        def delete_collection(self):
            chamadas.append("delete")

        def create_collection(self):
            chamadas.append("create")

    monkeypatch.setattr(app_module, "get_vector_store", lambda: FakeStore())

    app_module.clear_base()

    assert chamadas == ["delete", "create"]
    assert fake.session_state.messages == []
    assert fake.session_state.ingested is False
    assert fake.session_state.pdf_path is None
    assert fake.session_state.uploader_key == 1
    assert fake.rerun_chamado is True
    assert not upload.exists()
    assert fake.session_state.flash == "Base limpa. Envie um novo PDF."


def test_clear_base_erro_mantem_estado(app_module, monkeypatch):
    fake = FakeSt()
    fake.session_state.messages = [{"role": "user"}]
    fake.session_state.ingested = True
    fake.session_state.pdf_path = "x.pdf"
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(app_module, "UPLOADED_PDF", Path("nao_existe_123.pdf"))

    def falha():
        raise RuntimeError("banco fora")

    monkeypatch.setattr(app_module, "get_vector_store", falha)

    app_module.clear_base()

    assert fake.session_state.messages == [{"role": "user"}]
    assert fake.session_state.ingested is True
    assert fake.session_state.pdf_path == "x.pdf"
    assert fake.session_state.uploader_key == 0
    assert fake.rerun_chamado is False
    assert any("Erro ao limpar a base" in c[1][0] for c in fake.sidebar.chamadas if c[0] == "error")


def test_render_sidebar_mostra_flash(app_module, monkeypatch, settings_factory):
    fake = FakeSt()
    fake.session_state.flash = "Base limpa. Envie um novo PDF."
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(app_module, "load_settings", lambda: settings_factory())

    app_module.render_sidebar()

    assert any(
        "Base limpa. Envie um novo PDF." in c[1][0]
        for c in fake.sidebar.chamadas
        if c[0] == "success"
    )
    assert "flash" not in fake.session_state


def test_render_chat_sem_pergunta(app_module, monkeypatch):
    fake = FakeSt(chat_input=None)
    monkeypatch.setattr(app_module, "st", fake)

    app_module.render_chat()

    assert fake.session_state.messages == []


def test_render_chat_responde_e_guarda_historico(app_module, monkeypatch):
    fake = FakeSt(chat_input="Qual o tema?")
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(app_module, "answer", lambda pergunta: "Resposta teste")

    app_module.render_chat()

    assert fake.session_state.messages == [
        {"role": "user", "content": "Qual o tema?"},
        {"role": "assistant", "content": "Resposta teste"},
    ]
    assert "Resposta teste" in fake.markdowns


def test_render_chat_trata_erro(app_module, monkeypatch):
    fake = FakeSt(chat_input="pergunta")
    monkeypatch.setattr(app_module, "st", fake)
    monkeypatch.setattr(
        app_module,
        "answer",
        lambda pergunta: (_ for _ in ()).throw(RuntimeError("API caiu")),
    )

    app_module.render_chat()

    assert fake.session_state.messages[-1]["role"] == "assistant"
    assert "Erro ao responder: API caiu" in fake.session_state.messages[-1]["content"]


@pytest.mark.web
def test_apptest_renderiza_sem_excecao():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(WEB_APP), default_timeout=60)
    at.run()

    assert not at.exception
    textos = [elemento.value for elemento in at.sidebar.success]
    assert any("Configuração carregada" in texto for texto in textos)
