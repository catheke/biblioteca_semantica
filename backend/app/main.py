"""
main.py — Ponto de entrada da API FastAPI do BASI.

Responsabilidades:
    - Criar a aplicação FastAPI (com metadados para o Swagger/OpenAPI).
    - Configurar CORS (permitir que o frontend Next.js chame a API).
    - Montar todos os routers da v1 sob /api/v1.
    - Expor endpoints utilitários: / (info), /health (sondagem), /api/v1/meta.
    - No arranque, garantir que as tabelas existem (útil no modo SQLite local).

Documentação interactiva gerada automaticamente:
    Swagger UI : http://localhost:8000/docs
    ReDoc      : http://localhost:8000/redoc
    OpenAPI    : http://localhost:8000/openapi.json
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.storage import CAPAS_DIR


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Ciclo de vida da aplicação. O código antes do `yield` corre no ARRANQUE.

    Aqui criamos as tabelas (no PostgreSQL elas já vêm do schema.sql; no SQLite
    local isto cria-as automaticamente para que a API funcione sem configuração).

    Em produção (BOOTSTRAP_ON_STARTUP=1) semeamos também a base de dados e
    carregamos a ontologia no Fuseki, de forma idempotente e tolerante a falhas.
    """
    init_db()
    if settings.BOOTSTRAP_ON_STARTUP:
        from app import bootstrap

        bootstrap.executar()
    yield
    # (espaço para limpeza no encerramento, se necessário)


# Descrição rica apresentada no topo do Swagger.
DESCRICAO = """
**Semantic Academic Hub (BASI)** — rede académica baseada em Web Semântica.

Permite publicar e descobrir documentos académicos com **pesquisa que
compreende relações** (ontologia OWL + SPARQL + inferência no Apache Jena Fuseki).

Funcionalidades principais:
* Autenticação JWT (access + refresh) e controlo de acesso por perfis.
* CRUD de documentos (livros, artigos, teses, ...).
* Pesquisa textual **e** pesquisa semântica (expansão por subtemas).
* Recomendações inteligentes baseadas no grafo de conhecimento.
* Endpoint SPARQL para exploração avançada.
"""

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=DESCRICAO,
    lifespan=lifespan,
    contact={"name": "Pedro Calenga, Filipe Tchivela, Adriano De Júlio"},
    license_info={"name": "Uso académico"},
)

# --- CORS: autoriza o frontend a consumir a API a partir do browser. ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Montagem dos routers da versão 1 da API. ---
app.include_router(api_router, prefix="/api/v1")

# --- Ficheiros estáticos: capas dos livros (públicas, sem restrição). ---
# Os ficheiros das obras NÃO são montados aqui: passam pelo endpoint de download
# para que o nível de acesso seja sempre verificado.
app.mount("/static/capas", StaticFiles(directory=str(CAPAS_DIR)), name="capas")


@app.get("/", tags=["Sistema"])
def raiz():
    """Mensagem de boas-vindas e ligações úteis."""
    return {
        "aplicacao": settings.APP_NAME,
        "versao": settings.APP_VERSION,
        "documentacao": "/docs",
        "saude": "/health",
    }


@app.get("/health", tags=["Sistema"])
def health():
    """Sondagem de saúde usada por orquestradores (Docker/Kubernetes)."""
    return {"estado": "ok", "ambiente": settings.APP_ENV}
