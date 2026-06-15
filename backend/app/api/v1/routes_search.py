"""
routes_search.py — Pesquisa TEXTUAL (rápida, no PostgreSQL).

  GET /api/v1/search?q=...   -> pesquisa por título/resumo

Esta é a pesquisa "clássica" (comparação de texto). Para a pesquisa que
COMPREENDE relações, ver routes_semantic.py.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.repositorio_documentos import RepositorioDocumentos
from app.schemas.search import ResultadoPesquisa

router = APIRouter()


@router.get("", response_model=list[ResultadoPesquisa])
def pesquisa_textual(
    q: str = Query(..., min_length=2, description="Termo a procurar."),
    db: Session = Depends(get_db),
):
    documentos = RepositorioDocumentos(db).pesquisa_textual(q)
    return [
        ResultadoPesquisa(
            titulo=d.titulo,
            uri=d.uri_semantica,
            tipo=d.tipo.value,
            motivo="Correspondência textual no título ou resumo.",
        )
        for d in documentos
    ]
