# -*- coding: utf-8 -*-
"""Valida o skill de testes do projeto e sua sincronização com a suíte."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / ".opencode" / "skills" / "rag-testing"
SKILL = SKILL_DIR / "SKILL.md"

pytestmark = pytest.mark.skill


def _texto() -> str:
    return SKILL.read_text(encoding="utf-8")


def test_skill_existe_e_tem_id_correto():
    assert SKILL.is_file()
    assert SKILL.parent.name == "rag-testing"


def test_frontmatter_valido():
    texto = _texto()

    assert texto.startswith("---")
    cabecalho = texto.split("---", 2)[1]
    assert "name:" in cabecalho
    assert "description:" in cabecalho
    assert "Testes RAG" in cabecalho


def test_secoes_obrigatorias():
    texto = _texto()

    for secao in (
        "## Quando usar",
        "## Regras invioláveis",
        "## Camadas de teste",
        "## Comandos",
        "## Checklist de aceitação",
        "## Diagnóstico rápido",
    ):
        assert secao in texto


def test_conteudo_cobre_as_camadas():
    texto = _texto()

    for termo in (
        "pytest",
        "RUN_INTEGRATION",
        "AppTest",
        "idempotência",
        "recusa",
        "segredos",
        "desempenho",
        "prompt injection",
        "trocar PDF",
    ):
        assert termo.lower() in texto.lower()


def test_skill_preserva_invariantes_do_desafio():
    texto = _texto()

    assert "CHUNK_SIZE = 1000" in texto
    assert "CHUNK_OVERLAP = 150" in texto
    assert "k = 10" in texto
    assert "Não tenho informações necessárias para responder sua pergunta." in texto


def test_skill_aponta_para_arquivos_existentes():
    texto = _texto()
    esperados = [
        "tests/conftest.py",
        "tests/test_config.py",
        "tests/test_search.py",
        "tests/test_chat.py",
        "tests/test_ingest.py",
        "tests/test_web.py",
        "tests/test_security.py",
        "tests/test_edge_cases.py",
        "tests/test_performance.py",
        "tests/test_integration.py",
        "tests/test_skill.py",
    ]

    for caminho in esperados:
        assert caminho in texto
        assert (ROOT / caminho).is_file(), f"Arquivo citado no skill não existe: {caminho}"


def test_checklist_manual_existe():
    checklist = SKILL_DIR / "references" / "manual-checklist.md"

    assert checklist.is_file()
    texto = checklist.read_text(encoding="utf-8")
    assert "Upload de PDF" in texto
    assert "Limpar base (trocar PDF)" in texto
    assert "frase de recusa" in texto.lower() or "recusa" in texto.lower()


def test_script_runner_existe():
    script = SKILL_DIR / "scripts" / "run-tests.ps1"

    assert script.is_file()
    texto = script.read_text(encoding="utf-8")
    assert "pytest" in texto
    assert "RUN_INTEGRATION" in texto


def test_skill_nao_altera_env():
    texto = _texto().lower()

    assert "nunca alterar o `.env`" in texto or "nunca alterar o .env" in texto
