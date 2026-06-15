"""
routes_sparql.py — Endpoint SPARQL livre (somente leitura).

  POST /api/v1/sparql   { "query": "SELECT ..." }

Permite a utilizadores avançados / administradores explorar o grafo. Por
segurança, BLOQUEIA operações de escrita (INSERT/DELETE/DROP/CLEAR/LOAD): só
consultas de leitura (SELECT/ASK/CONSTRUCT/DESCRIBE) são aceites.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import exigir_perfis
from app.models.user import Utilizador, PerfilUtilizador
from app.schemas.search import SparqlPedido
from app.services.servico_semantico import servico_semantico

router = APIRouter()

# Palavras-chave de escrita que NÃO são permitidas neste endpoint público.
PALAVRAS_PROIBIDAS = ("INSERT", "DELETE", "DROP", "CLEAR", "LOAD", "CREATE", "ADD", "MOVE", "COPY")


@router.post("")
def executar_sparql(
    pedido: SparqlPedido,
    # Só professores, investigadores e administradores podem consultar livremente.
    _: Utilizador = Depends(
        exigir_perfis(
            PerfilUtilizador.administrador,
            PerfilUtilizador.professor,
            PerfilUtilizador.investigador,
        )
    ),
):
    query_maiusculas = pedido.query.upper()
    if any(palavra in query_maiusculas for palavra in PALAVRAS_PROIBIDAS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas consultas de leitura (SELECT/ASK/CONSTRUCT) são permitidas.",
        )
    resultados = servico_semantico.executar_select(pedido.query)
    return {"total": len(resultados), "resultados": resultados}
