"""
actividade.py — Modelos de actividade do utilizador e avisos da biblioteca.

Reúne quatro tabelas NOVAS (criadas automaticamente por create_all, sem alterar
tabelas existentes):

  - HistoricoLeitura   : registo de cada leitura/descarga de um documento.
  - HistoricoPesquisa  : registo de cada termo pesquisado.
  - Notificacao        : aviso global (ex.: novo documento adicionado).
  - MarcadorNotificacao: por utilizador, guarda quando viu as notificações pela
                         última vez (para calcular as "não lidas" sem criar uma
                         linha por utilizador a cada aviso).
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HistoricoLeitura(Base):
    """Uma entrada por cada vez que um utilizador lê/descarrega um documento."""

    __tablename__ = "historico_leituras"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilizador_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE"), index=True
    )
    documento_id: Mapped[int] = mapped_column(
        ForeignKey("documentos.id", ondelete="CASCADE"), index=True
    )
    data: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class HistoricoPesquisa(Base):
    """Uma entrada por cada termo pesquisado por um utilizador autenticado."""

    __tablename__ = "historico_pesquisas"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilizador_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE"), index=True
    )
    termo: Mapped[str] = mapped_column(String(200), nullable=False)
    semantica: Mapped[bool] = mapped_column(default=False, nullable=False)
    data: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Notificacao(Base):
    """Aviso global da biblioteca (ex.: 'Novo livro: ...')."""

    __tablename__ = "notificacoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    mensagem: Mapped[str] = mapped_column(String(300), nullable=False)
    documento_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("documentos.id", ondelete="SET NULL"), nullable=True
    )
    data: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class MarcadorNotificacao(Base):
    """Guarda, por utilizador, o instante em que viu as notificações."""

    __tablename__ = "marcadores_notificacao"

    utilizador_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE"), primary_key=True
    )
    vistas_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
