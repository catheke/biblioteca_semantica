"""search.py — Schemas das pesquisas (textual e semântica) e SPARQL."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ResultadoPesquisa(BaseModel):
    """Item devolvido por uma pesquisa."""

    titulo: str
    uri: Optional[str] = None
    tipo: Optional[str] = None
    motivo: Optional[str] = Field(
        default=None,
        description="Explicação semântica de PORQUÊ este resultado apareceu.",
    )


class RespostaPesquisaSemantica(BaseModel):
    termo: str
    tema_encontrado: bool = Field(
        default=False,
        description="True se o termo corresponde a um tema da biblioteca.",
    )
    termos_expandidos: list[str] = Field(
        default_factory=list,
        description="Temas relacionados encontrados por inferência (subtemas, etc.).",
    )
    resultados: list[ResultadoPesquisa]
    sugestoes: list[str] = Field(
        default_factory=list,
        description="Temas sugeridos quando não há resultados.",
    )


class SparqlPedido(BaseModel):
    """Consulta SPARQL livre submetida pelo cliente (apenas leitura)."""

    query: str = Field(
        examples=[
            "PREFIX basi: <http://basi.ao/ontologia#>\n"
            "SELECT ?titulo WHERE { ?d basi:titulo ?titulo } LIMIT 10"
        ]
    )


class RecomendacaoItem(BaseModel):
    uri: str
    titulo: str
    motivo: str
