"""
routes_users.py — Endpoints de utilizadores, professores e rede social.

  GET   /api/v1/users                -> listar (com filtro de perfil)
  GET   /api/v1/users/professors     -> atalho: listar só professores
  GET   /api/v1/users/{id}           -> detalhe
  PATCH /api/v1/users/me             -> editar o meu perfil
  POST  /api/v1/users/{id}/follow    -> seguir
  DELETE/api/v1/users/{id}/follow    -> deixar de seguir
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import obter_utilizador_actual
from app.models.user import Utilizador, PerfilUtilizador
from app.repositories.repositorio_utilizadores import RepositorioUtilizadores
from app.schemas.document import PaginaResposta
from app.schemas.user import UtilizadorPublico, UtilizadorActualizar

router = APIRouter()


@router.get("", response_model=PaginaResposta[UtilizadorPublico])
def listar_utilizadores(
    perfil: Optional[PerfilUtilizador] = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    repo = RepositorioUtilizadores(db)
    deslocamento = (pagina - 1) * por_pagina
    itens = repo.listar(perfil=perfil, limite=por_pagina, deslocamento=deslocamento)
    total = repo.contar(perfil=perfil)
    return PaginaResposta(total=total, pagina=pagina, por_pagina=por_pagina, itens=itens)


@router.get("/professors", response_model=list[UtilizadorPublico])
def listar_professores(db: Session = Depends(get_db)):
    """Atalho pedido no enunciado: /professors."""
    return RepositorioUtilizadores(db).listar(perfil=PerfilUtilizador.professor, limite=100)


@router.patch("/me", response_model=UtilizadorPublico)
def actualizar_meu_perfil(
    dados: UtilizadorActualizar,
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(utilizador, campo, valor)
    return RepositorioUtilizadores(db).actualizar(utilizador)


@router.get("/{user_id}", response_model=UtilizadorPublico)
def obter_utilizador(user_id: int, db: Session = Depends(get_db)):
    utilizador = RepositorioUtilizadores(db).obter_por_id(user_id)
    if utilizador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilizador não encontrado.")
    return utilizador


@router.post("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def seguir(
    user_id: int,
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    if user_id == utilizador.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Não pode seguir-se a si próprio.")
    RepositorioUtilizadores(db).seguir(utilizador.id, user_id)
    return None


@router.delete("/{user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def deixar_de_seguir(
    user_id: int,
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    RepositorioUtilizadores(db).deixar_de_seguir(utilizador.id, user_id)
    return None
