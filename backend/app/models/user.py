"""
user.py — Modelos ORM de identidade: Utilizador e TokenRefresh.

Mapeiam as tabelas `utilizadores` e `tokens_refresh` definidas em schema.sql.
Usamos a sintaxe moderna do SQLAlchemy 2.0 (Mapped / mapped_column), que dá
verificação de tipos e melhor legibilidade.
"""
from __future__ import annotations

from typing import Optional

import enum
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class PerfilUtilizador(str, enum.Enum):
    """Perfis de acesso (RBAC). Herda de str para serializar como texto em JSON."""

    administrador = "administrador"
    professor = "professor"
    estudante = "estudante"
    investigador = "investigador"
    visitante = "visitante"


class Utilizador(Base):
    __tablename__ = "utilizadores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # Guardamos o HASH bcrypt, nunca a palavra-passe original.
    palavra_passe: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[PerfilUtilizador] = mapped_column(
        SAEnum(PerfilUtilizador, name="perfil_utilizador"),
        default=PerfilUtilizador.estudante,
        nullable=False,
    )
    biografia: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    instituicao: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_validado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relação 1:N — um utilizador é autor de muitos documentos.
    documentos: Mapped[list["Documento"]] = relationship(  # noqa: F821
        back_populates="autor", cascade="all, delete-orphan"
    )


class TokenRefresh(Base):
    """
    Guarda o hash de cada refresh token emitido, para permitir REVOGAÇÃO.

    Porquê guardar? Tokens JWT são, por natureza, sem estado. Para conseguir
    "logout real" e revogar sessões comprometidas, mantemos um registo dos
    refresh tokens válidos e marcamos `revogado=True` quando necessário.
    """

    __tablename__ = "tokens_refresh"

    id: Mapped[int] = mapped_column(primary_key=True)
    utilizador_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expira_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revogado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
