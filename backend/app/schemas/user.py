"""user.py — Schemas de leitura/escrita de utilizadores."""
from __future__ import annotations

from typing import Optional

from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.user import PerfilUtilizador


class UtilizadorPublico(BaseModel):
    """Vista pública de um utilizador (NUNCA inclui a palavra-passe)."""

    # from_attributes permite criar o schema directamente a partir do objecto ORM.
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    perfil: PerfilUtilizador
    biografia: Optional[str] = None
    instituicao: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: Optional[datetime] = None


class UtilizadorActualizar(BaseModel):
    """Campos editáveis do perfil (todos opcionais)."""

    nome: Optional[str] = None
    biografia: Optional[str] = None
    instituicao: Optional[str] = None
    avatar_url: Optional[str] = None
