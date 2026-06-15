"""
deps.py — Dependências de autenticação e autorização do FastAPI.

`obter_utilizador_actual` valida o token Bearer e devolve o utilizador, protegendo
qualquer endpoint que dela dependa. `exigir_perfis(...)` gera uma dependência de
controlo de acesso (RBAC) que só admite os perfis indicados.
"""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import descodificar_token
from app.models.user import Utilizador, PerfilUtilizador
from app.repositories.repositorio_utilizadores import RepositorioUtilizadores

# tokenUrl aponta para o endpoint de login (usado pela UI do Swagger).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login", auto_error=False)


def obter_utilizador_actual(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Utilizador:
    """Resolve o utilizador autenticado a partir do access token."""
    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas ou em falta.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credenciais_invalidas

    claims = descodificar_token(token)
    if claims is None or claims.get("type") != "access":
        raise credenciais_invalidas

    user_id = claims.get("sub")
    if user_id is None:
        raise credenciais_invalidas

    utilizador = RepositorioUtilizadores(db).obter_por_id(int(user_id))
    if utilizador is None or not utilizador.activo:
        raise credenciais_invalidas
    return utilizador


def obter_utilizador_opcional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[Utilizador]:
    """
    Versão "suave" de `obter_utilizador_actual`: devolve o utilizador se houver
    um token válido, ou `None` se não houver sessão — sem lançar erro.

    Útil em endpoints que SÃO acessíveis a visitantes mas que mudam de
    comportamento consoante o perfil (ex.: descarregar consoante o nível de
    acesso do documento).
    """
    if not token:
        return None
    claims = descodificar_token(token)
    if claims is None or claims.get("type") != "access":
        return None
    user_id = claims.get("sub")
    if user_id is None:
        return None
    utilizador = RepositorioUtilizadores(db).obter_por_id(int(user_id))
    if utilizador is None or not utilizador.activo:
        return None
    return utilizador


def exigir_perfis(*perfis: PerfilUtilizador):
    """
    Fábrica de dependências para controlo de acesso baseado em papéis (RBAC).

    Uso:
        @router.post("/", dependencies=[Depends(exigir_perfis(PerfilUtilizador.administrador))])
    """

    def verificador(
        utilizador: Utilizador = Depends(obter_utilizador_actual),
    ) -> Utilizador:
        if utilizador.perfil not in perfis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Não tem permissões para esta operação.",
            )
        return utilizador

    return verificador
