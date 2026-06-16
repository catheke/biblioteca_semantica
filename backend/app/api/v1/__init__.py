"""
Agregador de routers da API v1.

Reúne todos os sub-routers (auth, users, documents, search...) num único
APIRouter que é montado em app/main.py sob o prefixo /api/v1.
"""
from fastapi import APIRouter

from app.api.v1 import (
    routes_auth,
    routes_users,
    routes_documents,
    routes_search,
    routes_semantic,
    routes_recommendations,
    routes_sparql,
    routes_circulacao,
)

api_router = APIRouter()
api_router.include_router(routes_auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(routes_users.router, prefix="/users", tags=["Utilizadores"])
api_router.include_router(routes_documents.router)  # define os seus próprios prefixos
api_router.include_router(routes_search.router, prefix="/search", tags=["Pesquisa"])
api_router.include_router(
    routes_semantic.router, prefix="/semantic-search", tags=["Pesquisa Semântica"]
)
api_router.include_router(
    routes_recommendations.router, prefix="/recommendations", tags=["Recomendações"]
)
api_router.include_router(routes_sparql.router, prefix="/sparql", tags=["SPARQL"])
api_router.include_router(
    routes_circulacao.router, prefix="/circulation", tags=["Circulação"]
)
