"""document.py — Schemas de documentos e respostas paginadas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Generic, TypeVar

from pydantic import BaseModel, Field, ConfigDict

from app.models.document import TipoDocumento, EstadoDocumento, NivelAcesso


class DocumentoCriar(BaseModel):
    """Payload para publicar um novo documento."""

    titulo: str = Field(min_length=3, max_length=400)
    resumo: Optional[str] = Field(default=None, max_length=5000)
    tipo: TipoDocumento
    ano_publicacao: Optional[int] = Field(default=None, ge=1, le=2100)
    idioma: Optional[str] = "Português"
    area_id: Optional[int] = None
    genero: Optional[str] = Field(default=None, max_length=60, description="Género literário (Romance, Poesia, Conto, Teatro).")
    autor_nome: Optional[str] = Field(default=None, max_length=300)
    ficheiro_url: Optional[str] = Field(default=None, max_length=1000)
    capa_url: Optional[str] = Field(default=None, max_length=1000)
    nivel_acesso: NivelAcesso = NivelAcesso.publico
    temas: list[str] = Field(default_factory=list, description="Nomes de temas associados.")
    palavras_chave: list[str] = Field(default_factory=list)


class DocumentoActualizar(BaseModel):
    titulo: Optional[str] = None
    resumo: Optional[str] = None
    estado: Optional[EstadoDocumento] = None
    ano_publicacao: Optional[int] = None
    area_id: Optional[int] = None


class DocumentoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    resumo: Optional[str]
    tipo: TipoDocumento
    estado: EstadoDocumento
    ano_publicacao: Optional[int]
    idioma: Optional[str]
    autor_id: int
    autor_nome: Optional[str] = None
    area_id: Optional[int]
    genero: Optional[str] = None
    ficheiro_url: Optional[str] = None
    ficheiro_objecto: Optional[str] = None  # nome do ficheiro local (storage/livros)
    capa_url: Optional[str] = None
    nivel_acesso: NivelAcesso = NivelAcesso.publico
    uri_semantica: Optional[str]
    num_downloads: int
    num_visualizacoes: int
    created_at: Optional[datetime] = None


# ------- Secções da biblioteca (estrutura CDU) -------
class GeneroSeccao(BaseModel):
    """Género literário dentro da secção de Literatura (auxiliar de forma CDU)."""

    codigo: str  # notação CDU, ex.: "82-3"
    nome: str    # ex.: "Romance"
    total: int


class SeccaoBiblioteca(BaseModel):
    """Uma secção da biblioteca (classe da CDU) com a sua contagem de obras."""

    area_id: int
    codigo: Optional[str] = None  # cota CDU, ex.: "0", "82"
    nome: str
    total: int
    generos: list[GeneroSeccao] = Field(default_factory=list)


# ------- Resposta paginada genérica (reutilizável em várias rotas) -------
T = TypeVar("T")


class PaginaResposta(BaseModel, Generic[T]):
    """Envelope de paginação: itens + metadados."""

    total: int
    pagina: int
    por_pagina: int
    itens: list[T]
