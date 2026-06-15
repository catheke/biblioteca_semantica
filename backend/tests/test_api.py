"""
test_api.py — Testes de integração da API (pytest + TestClient).

Usam uma base de dados SQLite isolada em memória/ficheiro temporário, pelo que
NÃO precisam de PostgreSQL nem de Fuseki a correr. Cobrem o fluxo de
autenticação e o CRUD básico de documentos — o "caminho feliz" e um caso de erro.

EXECUTAR (a partir de backend/):  pytest -q
"""
from __future__ import annotations

import os
import tempfile

# Configura uma BD SQLite temporária ANTES de importar a app.
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.core.database import init_db  # noqa: E402

# Cria as tabelas na BD de teste. O TestClient só dispara o evento de arranque
# (lifespan) quando usado como gestor de contexto; criamos aqui explicitamente
# para que os testes não dependam disso.
init_db()

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"


def test_registo_login_e_me():
    # Registo
    r = client.post(
        "/api/v1/auth/register",
        json={"nome": "Teste", "email": "teste@basi.ao", "palavra_passe": "password123", "perfil": "professor"},
    )
    assert r.status_code == 201, r.text
    tokens = r.json()
    assert "access_token" in tokens

    # /me com o token
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    r = client.get("/api/v1/auth/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == "teste@basi.ao"


def test_email_duplicado_falha():
    payload = {"nome": "Dup", "email": "dup@basi.ao", "palavra_passe": "password123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    # Segundo registo com o mesmo email -> 409
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_publicar_e_listar_documento():
    # Cria um professor e publica um documento.
    r = client.post(
        "/api/v1/auth/register",
        json={"nome": "Autor", "email": "autor@basi.ao", "palavra_passe": "password123", "perfil": "professor"},
    )
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/documents",
        headers=headers,
        json={"titulo": "Documento de Teste", "tipo": "livro", "ano_publicacao": 2024},
    )
    assert r.status_code == 201, r.text
    assert r.json()["uri_semantica"].startswith("http://basi.ao/recurso/documento/")

    # Lista pública de livros deve conter pelo menos 1.
    r = client.get("/api/v1/books")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
