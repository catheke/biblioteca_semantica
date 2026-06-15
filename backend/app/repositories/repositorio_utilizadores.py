"""repositorio_utilizadores.py — Acesso a dados de utilizadores e relações sociais."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.user import Utilizador, PerfilUtilizador
from app.models.social import Seguidor


class RepositorioUtilizadores:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obter_por_id(self, user_id: int) -> Optional[Utilizador]:
        return self.db.get(Utilizador, user_id)

    def obter_por_email(self, email: str) -> Optional[Utilizador]:
        stmt = select(Utilizador).where(Utilizador.email == email)
        return self.db.scalars(stmt).first()

    def criar(self, utilizador: Utilizador) -> Utilizador:
        self.db.add(utilizador)
        self.db.commit()
        self.db.refresh(utilizador)
        return utilizador

    def actualizar(self, utilizador: Utilizador) -> Utilizador:
        self.db.commit()
        self.db.refresh(utilizador)
        return utilizador

    def listar(
        self, perfil: Optional[PerfilUtilizador] = None, limite: int = 50, deslocamento: int = 0
    ) -> list[Utilizador]:
        stmt = select(Utilizador)
        if perfil is not None:
            stmt = stmt.where(Utilizador.perfil == perfil)
        stmt = stmt.order_by(Utilizador.nome).limit(limite).offset(deslocamento)
        return list(self.db.scalars(stmt).all())

    def contar(self, perfil: Optional[PerfilUtilizador] = None) -> int:
        stmt = select(func.count()).select_from(Utilizador)
        if perfil is not None:
            stmt = stmt.where(Utilizador.perfil == perfil)
        return int(self.db.scalar(stmt) or 0)

    # ---- Rede social (seguir) ----
    def seguir(self, seguidor_id: int, seguido_id: int) -> None:
        existe = self.db.get(Seguidor, {"seguidor_id": seguidor_id, "seguido_id": seguido_id})
        if existe is None:
            self.db.add(Seguidor(seguidor_id=seguidor_id, seguido_id=seguido_id))
            self.db.commit()

    def deixar_de_seguir(self, seguidor_id: int, seguido_id: int) -> None:
        rel = self.db.get(Seguidor, {"seguidor_id": seguidor_id, "seguido_id": seguido_id})
        if rel is not None:
            self.db.delete(rel)
            self.db.commit()
