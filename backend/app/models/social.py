"""
social.py — Modelos da rede social académica: Favorito e Seguidor.

São tabelas de associação (N:N) que dão à plataforma o carácter de "rede"
(estilo ResearchGate/Scholar): guardar documentos e seguir pessoas.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, DateTime, func, PrimaryKeyConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Favorito(Base):
    __tablename__ = "favoritos"
    __table_args__ = (PrimaryKeyConstraint("utilizador_id", "documento_id"),)

    utilizador_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE")
    )
    documento_id: Mapped[int] = mapped_column(
        ForeignKey("documentos.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Seguidor(Base):
    __tablename__ = "seguidores"
    __table_args__ = (
        PrimaryKeyConstraint("seguidor_id", "seguido_id"),
        # Um utilizador não pode seguir-se a si próprio.
        CheckConstraint("seguidor_id <> seguido_id", name="chk_nao_auto_seguir"),
    )

    seguidor_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE")
    )
    seguido_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
