"""actividade.py — Schemas de histórico, notificações e estatísticas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ------------------------------- Histórico -----------------------------------
class LeituraResposta(BaseModel):
    documento_id: int
    titulo: str
    tipo: Optional[str] = None
    capa_url: Optional[str] = None
    data: datetime


class PesquisaResposta(BaseModel):
    termo: str
    semantica: bool
    data: datetime


# ----------------------------- Notificações ----------------------------------
class NotificacaoResposta(BaseModel):
    id: int
    mensagem: str
    documento_id: Optional[int] = None
    data: datetime

    class Config:
        from_attributes = True


class NotificacoesResposta(BaseModel):
    nao_lidas: int
    itens: list[NotificacaoResposta]


# ----------------------------- Estatísticas ----------------------------------
class ItemContagem(BaseModel):
    documento_id: int
    titulo: str
    valor: int


class CategoriaContagem(BaseModel):
    nome: str
    total: int


class TermoContagem(BaseModel):
    termo: str
    total: int


class EstatisticasResposta(BaseModel):
    total_documentos: int
    total_utilizadores: int
    total_downloads: int
    total_visualizacoes: int
    mais_vistos: list[ItemContagem]
    mais_descarregados: list[ItemContagem]
    por_categoria: list[CategoriaContagem]
    termos_mais_pesquisados: list[TermoContagem]
