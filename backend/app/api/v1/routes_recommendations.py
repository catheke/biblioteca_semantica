"""
routes_recommendations.py — Recomendações semânticas personalizadas.

  GET /api/v1/recommendations   -> documentos sugeridos ao utilizador autenticado

Baseado nos temas dos seus favoritos, expandidos pela ontologia. Ver
services/servico_recomendacoes.py para o algoritmo explicado.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import obter_utilizador_actual
from app.models.user import Utilizador
from app.schemas.search import RecomendacaoItem
from app.services.servico_recomendacoes import servico_recomendacoes

router = APIRouter()


@router.get("", response_model=list[RecomendacaoItem])
def recomendacoes(
    utilizador: Utilizador = Depends(obter_utilizador_actual),
):
    # Constrói o IRI do utilizador no grafo a partir do seu email (convenção).
    # Em produção guardaríamos o uri_semantica do utilizador na tabela.
    nome_recurso = utilizador.email.split("@")[0]
    uri_utilizador = f"http://basi.ao/recurso/pessoa/{nome_recurso}"
    return servico_recomendacoes.recomendar(uri_utilizador)
