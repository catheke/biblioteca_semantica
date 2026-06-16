"""repositorio_documentos.py — Acesso a dados de documentos e favoritos."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from app.models.document import Documento, TipoDocumento, EstadoDocumento
from app.models.social import Favorito


class RepositorioDocumentos:
    def __init__(self, db: Session) -> None:
        self.db = db

    def obter_por_id(self, doc_id: int) -> Optional[Documento]:
        return self.db.get(Documento, doc_id)

    def criar(self, documento: Documento) -> Documento:
        self.db.add(documento)
        self.db.commit()
        self.db.refresh(documento)
        return documento

    def actualizar(self, documento: Documento) -> Documento:
        self.db.commit()
        self.db.refresh(documento)
        return documento

    def eliminar(self, documento: Documento) -> None:
        self.db.delete(documento)
        self.db.commit()

    def _aplicar_filtros(
        self,
        stmt,
        tipo: Optional[TipoDocumento] = None,
        area_id: Optional[int] = None,
        autor_id: Optional[int] = None,
        genero: Optional[str] = None,
        q: Optional[str] = None,
        autor: Optional[str] = None,
        ano: Optional[int] = None,
    ):
        """Aplica os filtros comuns a `listar` e `contar` (evita duplicação)."""
        if tipo is not None:
            stmt = stmt.where(Documento.tipo == tipo)
        if area_id is not None:
            stmt = stmt.where(Documento.area_id == area_id)
        if autor_id is not None:
            stmt = stmt.where(Documento.autor_id == autor_id)
        if genero is not None:
            stmt = stmt.where(Documento.genero == genero)
        if q:
            padrao = f"%{q.strip()}%"
            stmt = stmt.where(
                or_(Documento.titulo.ilike(padrao), Documento.resumo.ilike(padrao))
            )
        if autor:
            stmt = stmt.where(Documento.autor_nome.ilike(f"%{autor.strip()}%"))
        if ano is not None:
            stmt = stmt.where(Documento.ano_publicacao == ano)
        return stmt

    def listar(
        self,
        tipo: Optional[TipoDocumento] = None,
        area_id: Optional[int] = None,
        autor_id: Optional[int] = None,
        genero: Optional[str] = None,
        q: Optional[str] = None,
        autor: Optional[str] = None,
        ano: Optional[int] = None,
        limite: int = 20,
        deslocamento: int = 0,
    ) -> list[Documento]:
        stmt = select(Documento).where(Documento.estado == EstadoDocumento.publicado)
        stmt = self._aplicar_filtros(
            stmt, tipo, area_id, autor_id, genero, q, autor, ano
        )
        stmt = stmt.order_by(Documento.created_at.desc()).limit(limite).offset(deslocamento)
        return list(self.db.scalars(stmt).all())

    def contar(
        self,
        tipo: Optional[TipoDocumento] = None,
        area_id: Optional[int] = None,
        autor_id: Optional[int] = None,
        genero: Optional[str] = None,
        q: Optional[str] = None,
        autor: Optional[str] = None,
        ano: Optional[int] = None,
    ) -> int:
        stmt = select(func.count()).select_from(Documento).where(
            Documento.estado == EstadoDocumento.publicado
        )
        stmt = self._aplicar_filtros(
            stmt, tipo, area_id, autor_id, genero, q, autor, ano
        )
        return int(self.db.scalar(stmt) or 0)

    def contagem_por_area(self) -> dict[int, int]:
        """Nº de documentos publicados por secção (area_id -> total)."""
        stmt = (
            select(Documento.area_id, func.count())
            .where(Documento.estado == EstadoDocumento.publicado)
            .group_by(Documento.area_id)
        )
        return {area_id: total for area_id, total in self.db.execute(stmt).all() if area_id is not None}

    def contagem_por_genero(self, area_id: int) -> dict[str, int]:
        """Nº de documentos por género dentro de uma secção (genero -> total)."""
        stmt = (
            select(Documento.genero, func.count())
            .where(
                Documento.estado == EstadoDocumento.publicado,
                Documento.area_id == area_id,
                Documento.genero.is_not(None),
            )
            .group_by(Documento.genero)
        )
        return {genero: total for genero, total in self.db.execute(stmt).all()}

    def pesquisa_textual(self, termo: str, limite: int = 20) -> list[Documento]:
        """
        Pesquisa textual simples (title/resumo).

        NOTA: em PostgreSQL existe o índice GIN full-text (ver schema.sql) que
        torna isto muito mais rápido. Aqui usamos ILIKE para funcionar também em
        SQLite (modo local). Em produção, trocar por to_tsvector/plainto_tsquery.
        """
        padrao = f"%{termo}%"
        stmt = (
            select(Documento)
            .where(or_(Documento.titulo.ilike(padrao), Documento.resumo.ilike(padrao)))
            .limit(limite)
        )
        return list(self.db.scalars(stmt).all())

    def obter_por_uris(self, uris: list[str]) -> list[Documento]:
        """Dado um conjunto de IRIs (vindos do SPARQL), devolve os documentos SQL."""
        if not uris:
            return []
        stmt = select(Documento).where(Documento.uri_semantica.in_(uris))
        return list(self.db.scalars(stmt).all())

    # ---- Favoritos ----
    def adicionar_favorito(self, user_id: int, doc_id: int) -> None:
        existe = self.db.get(Favorito, {"utilizador_id": user_id, "documento_id": doc_id})
        if existe is None:
            self.db.add(Favorito(utilizador_id=user_id, documento_id=doc_id))
            self.db.commit()

    def remover_favorito(self, user_id: int, doc_id: int) -> None:
        fav = self.db.get(Favorito, {"utilizador_id": user_id, "documento_id": doc_id})
        if fav is not None:
            self.db.delete(fav)
            self.db.commit()

    def listar_favoritos(self, user_id: int) -> list[Documento]:
        stmt = (
            select(Documento)
            .join(Favorito, Favorito.documento_id == Documento.id)
            .where(Favorito.utilizador_id == user_id)
        )
        return list(self.db.scalars(stmt).all())
