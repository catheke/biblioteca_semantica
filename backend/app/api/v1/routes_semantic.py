"""
routes_semantic.py — PESQUISA SEMÂNTICA (inferência via ontologia/Fuseki).

  GET /api/v1/semantic-search?q=Inteligência Artificial

Demonstra o diferencial do projecto: ao procurar "Inteligência Artificial",
devolve também documentos de Machine Learning, Deep Learning, etc., porque a
ontologia declara estas relações de subtema (propriedade transitiva).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import obter_utilizador_opcional
from app.models.user import Utilizador
from app.schemas.search import RespostaPesquisaSemantica, ResultadoPesquisa
from app.services.servico_actividade import ServicoActividade
from app.services.servico_semantico import servico_semantico

router = APIRouter()


@router.get("", response_model=RespostaPesquisaSemantica)
def pesquisa_semantica(
    q: str = Query(..., min_length=2, description="Tema a procurar (ex.: 'Inteligência Artificial')."),
    utilizador: Optional[Utilizador] = Depends(obter_utilizador_opcional),
    db: Session = Depends(get_db),
):
    termo = q.strip()
    if utilizador is not None:
        ServicoActividade(db).registar_pesquisa(utilizador.id, termo, semantica=True)

    # 1) Expande o termo para o(s) tema(s) correspondente(s) e seus subtemas.
    termos_expandidos = servico_semantico.expandir_termo(termo)
    tema_encontrado = bool(termos_expandidos)

    if tema_encontrado:
        # 2a) O termo é um tema: procura documentos por tema/subtema (inferência).
        linhas = servico_semantico.pesquisar_documentos_por_tema(termo)
        resultados = [
            ResultadoPesquisa(
                titulo=linha.get("titulo", "(sem título)"),
                uri=linha.get("doc"),
                tipo=None,
                motivo=f"Encontrado pelo tema relacionado: {linha.get('nomeTema')}.",
            )
            for linha in linhas
        ]
    else:
        # 2b) O termo não é um tema conhecido: procura no título/resumo (reserva).
        linhas = servico_semantico.pesquisar_documentos_por_texto(termo)
        resultados = [
            ResultadoPesquisa(
                titulo=linha.get("titulo", "(sem título)"),
                uri=linha.get("doc"),
                tipo=None,
                motivo=f"O termo «{termo}» aparece no título ou no resumo.",
            )
            for linha in linhas
        ]

    # 3) Sem resultados? Sugere os temas principais da biblioteca.
    sugestoes = servico_semantico.temas_principais() if not resultados else []

    return RespostaPesquisaSemantica(
        termo=termo,
        tema_encontrado=tema_encontrado,
        termos_expandidos=termos_expandidos,
        resultados=resultados,
        sugestoes=sugestoes,
    )
