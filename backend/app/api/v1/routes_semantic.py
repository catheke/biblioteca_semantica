"""
routes_semantic.py — PESQUISA SEMÂNTICA (inferência via ontologia/Fuseki).

  GET /api/v1/semantic-search?q=Inteligência Artificial

Demonstra o diferencial do projecto: ao procurar "Inteligência Artificial",
devolve também documentos de Machine Learning, Deep Learning, etc., porque a
ontologia declara estas relações de subtema (propriedade transitiva).
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.schemas.search import RespostaPesquisaSemantica, ResultadoPesquisa
from app.services.servico_semantico import servico_semantico

router = APIRouter()


@router.get("", response_model=RespostaPesquisaSemantica)
def pesquisa_semantica(
    q: str = Query(..., min_length=2, description="Tema a procurar (ex.: 'Inteligência Artificial')."),
):
    # 1) Expande o termo para todos os subtemas (inferência).
    termos_expandidos = servico_semantico.expandir_termo(q)

    # 2) Procura documentos ligados ao tema ou a qualquer subtema.
    linhas = servico_semantico.pesquisar_documentos_por_tema(q)
    resultados = [
        ResultadoPesquisa(
            titulo=linha.get("titulo", "(sem título)"),
            uri=linha.get("doc"),
            tipo=None,
            motivo=f"Encontrado pelo tema relacionado: {linha.get('nomeTema')}.",
        )
        for linha in linhas
    ]

    return RespostaPesquisaSemantica(
        termo=q, termos_expandidos=termos_expandidos, resultados=resultados
    )
