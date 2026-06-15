"""
security.py — Hashing de palavras-passe (bcrypt) e tokens JWT.

As palavras-passe são guardadas apenas como hash bcrypt. A autenticação é sem
estado, com dois tipos de token: access (curta duração, usado em cada pedido) e
refresh (longa duração, usado só para renovar o access).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional, Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Contexto de hashing. bcrypt é o algoritmo recomendado para palavras-passe.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -----------------------------------------------------------------------------
# Palavras-passe
# -----------------------------------------------------------------------------
def hash_password(palavra_passe: str) -> str:
    """Devolve o hash bcrypt de uma palavra-passe em texto simples."""
    return pwd_context.hash(palavra_passe)


def verify_password(palavra_passe: str, hash_guardado: str) -> bool:
    """Confirma se a palavra-passe corresponde ao hash guardado."""
    return pwd_context.verify(palavra_passe, hash_guardado)


# -----------------------------------------------------------------------------
# Tokens JWT
# -----------------------------------------------------------------------------
def _criar_token(dados: dict[str, Any], expira_delta: timedelta, tipo: str) -> str:
    """
    Cria um JWT assinado.

    `dados` -> conteúdo (claims). Acrescentamos:
        exp  -> instante de expiração (obrigatório para tokens com validade)
        iat  -> instante de emissão
        type -> "access" ou "refresh" (para distinguir os dois)
    """
    a_codificar = dados.copy()
    agora = datetime.now(timezone.utc)
    a_codificar.update({"exp": agora + expira_delta, "iat": agora, "type": tipo})
    return jwt.encode(
        a_codificar, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def criar_access_token(subject: str, perfil: str) -> str:
    """Token de curta duração usado em cada pedido autenticado."""
    return _criar_token(
        {"sub": subject, "perfil": perfil},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        tipo="access",
    )


def criar_refresh_token(subject: str) -> str:
    """Token de longa duração usado apenas para renovar o access token."""
    return _criar_token(
        {"sub": subject},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        tipo="refresh",
    )


def descodificar_token(token: str) -> Optional[dict[str, Any]]:
    """
    Verifica a assinatura e a validade do token.

    Devolve os claims se for válido; None se for inválido/expirado.
    """
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None
