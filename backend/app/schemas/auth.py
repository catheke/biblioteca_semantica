"""
auth.py — Schemas de autenticação.

Schemas (Pydantic) são os "contratos" da API: validam o que entra e definem o
que sai. Separá-los dos modelos ORM evita expor a estrutura interna da BD e
permite controlar exactamente que campos o cliente vê (ex.: nunca a palavra-passe).
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.models.user import PerfilUtilizador


class RegistoPedido(BaseModel):
    """Dados necessários para criar uma conta."""

    nome: str = Field(min_length=2, max_length=150, examples=["Maria Sousa"])
    email: EmailStr = Field(examples=["maria@basi.ao"])
    palavra_passe: str = Field(min_length=8, max_length=128, examples=["password123"])
    perfil: PerfilUtilizador = Field(
        default=PerfilUtilizador.estudante,
        description="Perfil pretendido (admin é atribuído manualmente).",
    )
    instituicao: Optional[str] = None


class LoginPedido(BaseModel):
    """Credenciais de início de sessão."""

    email: EmailStr
    palavra_passe: str


class TokenResposta(BaseModel):
    """Par de tokens devolvido após login/registo/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshPedido(BaseModel):
    refresh_token: str
