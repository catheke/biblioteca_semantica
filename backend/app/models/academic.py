"""
academic.py — Modelos da estrutura académica e da taxonomia de assuntos.

Tabelas: areas_cientificas, temas, palavras_chave, universidades, departamentos,
cursos. Estas entidades têm um campo `uri_semantica` que as liga ao recurso
correspondente no grafo RDF (Fuseki).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AreaCientifica(Base):
    """
    Secção da biblioteca, organizada pela CDU (Classificação Decimal Universal —
    a norma usada nas bibliotecas de Angola e Portugal). O campo `codigo` guarda
    a notação CDU da secção (ex.: "0" Informática, "1" Filosofia, "5" Ciências
    Naturais, "6" Medicina, "82" Literatura), tal como a cota numa estante real.
    """

    __tablename__ = "areas_cientificas"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
    nome: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    uri_semantica: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Tema(Base):
    __tablename__ = "temas"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    area_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("areas_cientificas.id", ondelete="SET NULL"), nullable=True
    )
    # Auto-relação: um tema pode ser subtema de outro (hierarquia).
    tema_pai_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("temas.id", ondelete="SET NULL"), nullable=True
    )
    uri_semantica: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    subtemas: Mapped[list["Tema"]] = relationship(
        back_populates="tema_pai", remote_side=lambda: [Tema.tema_pai_id]
    )
    tema_pai: Mapped[Optional["Tema"]] = relationship(
        back_populates="subtemas", remote_side=lambda: [Tema.id]
    )


class PalavraChave(Base):
    __tablename__ = "palavras_chave"

    id: Mapped[int] = mapped_column(primary_key=True)
    termo: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    uri_semantica: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Universidade(Base):
    __tablename__ = "universidades"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    sigla: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    pais: Mapped[Optional[str]] = mapped_column(String(100), default="Angola")
    uri_semantica: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Departamento(Base):
    __tablename__ = "departamentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    universidade_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("universidades.id", ondelete="CASCADE"), nullable=True
    )
    uri_semantica: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)


class Curso(Base):
    __tablename__ = "cursos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    grau: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    departamento_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departamentos.id", ondelete="SET NULL"), nullable=True
    )
    uri_semantica: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
