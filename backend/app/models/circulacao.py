"""
circulacao.py — Modelos ORM da gestão bibliotecária (circulação).

Dão ao BASI o funcionamento de uma biblioteca real: cada obra (Documento) pode
ter vários EXEMPLARES físicos/digitais; os leitores fazem EMPRÉSTIMOS com prazo,
podem RENOVAR, e quando uma obra está toda emprestada podem fazer uma RESERVA
(lista de espera). A entrega fora do prazo gera uma MULTA.

Tabelas: exemplares, emprestimos, reservas, multas.
"""
from __future__ import annotations

from typing import Optional

import enum
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SAEnum,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EstadoExemplar(str, enum.Enum):
    """Situação de cada cópia física/digital de uma obra."""

    disponivel = "disponivel"
    emprestado = "emprestado"
    reservado = "reservado"
    manutencao = "manutencao"
    perdido = "perdido"


class EstadoEmprestimo(str, enum.Enum):
    activo = "activo"
    devolvido = "devolvido"
    atrasado = "atrasado"


class EstadoReserva(str, enum.Enum):
    activa = "activa"          # à espera que um exemplar fique livre
    atendida = "atendida"      # já há exemplar reservado para este leitor
    cancelada = "cancelada"
    expirada = "expirada"


class Exemplar(Base):
    """
    Uma cópia concreta de uma obra. O `numero_registo` é a cota/etiqueta única
    do exemplar (como o código de barras numa biblioteca real).
    """

    __tablename__ = "exemplares"

    id: Mapped[int] = mapped_column(primary_key=True)
    documento_id: Mapped[int] = mapped_column(
        ForeignKey("documentos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    numero_registo: Mapped[str] = mapped_column(
        String(40), unique=True, index=True, nullable=False
    )
    estado: Mapped[EstadoExemplar] = mapped_column(
        SAEnum(EstadoExemplar, name="estado_exemplar"),
        default=EstadoExemplar.disponivel,
        nullable=False,
        index=True,
    )
    localizacao: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    documento: Mapped["Documento"] = relationship()  # noqa: F821


class Emprestimo(Base):
    """Requisição de um exemplar por um leitor, com prazo de devolução."""

    __tablename__ = "emprestimos"

    id: Mapped[int] = mapped_column(primary_key=True)
    exemplar_id: Mapped[int] = mapped_column(
        ForeignKey("exemplares.id", ondelete="CASCADE"), index=True, nullable=False
    )
    utilizador_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE"), index=True, nullable=False
    )
    data_emprestimo: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    data_prevista_devolucao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    data_devolucao: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    estado: Mapped[EstadoEmprestimo] = mapped_column(
        SAEnum(EstadoEmprestimo, name="estado_emprestimo"),
        default=EstadoEmprestimo.activo,
        nullable=False,
        index=True,
    )
    renovacoes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    exemplar: Mapped["Exemplar"] = relationship()
    utilizador: Mapped["Utilizador"] = relationship()  # noqa: F821


class Reserva(Base):
    """
    Pedido de uma obra que está toda emprestada. Os leitores entram numa fila
    (lista de espera) e são atendidos por ordem de chegada quando um exemplar
    é devolvido.
    """

    __tablename__ = "reservas"

    id: Mapped[int] = mapped_column(primary_key=True)
    documento_id: Mapped[int] = mapped_column(
        ForeignKey("documentos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    utilizador_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE"), index=True, nullable=False
    )
    data_reserva: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    estado: Mapped[EstadoReserva] = mapped_column(
        SAEnum(EstadoReserva, name="estado_reserva"),
        default=EstadoReserva.activa,
        nullable=False,
        index=True,
    )
    # Quando a reserva é atendida, fica associada ao exemplar guardado.
    exemplar_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("exemplares.id", ondelete="SET NULL"), nullable=True
    )

    documento: Mapped["Documento"] = relationship()  # noqa: F821
    utilizador: Mapped["Utilizador"] = relationship()  # noqa: F821


class Multa(Base):
    """Penalização por devolução fora do prazo (valor em Kwanzas, AOA)."""

    __tablename__ = "multas"

    id: Mapped[int] = mapped_column(primary_key=True)
    emprestimo_id: Mapped[int] = mapped_column(
        ForeignKey("emprestimos.id", ondelete="CASCADE"), index=True, nullable=False
    )
    utilizador_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE"), index=True, nullable=False
    )
    dias_atraso: Mapped[int] = mapped_column(Integer, nullable=False)
    valor: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    paga: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    data_criacao: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    data_pagamento: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    emprestimo: Mapped["Emprestimo"] = relationship()
    utilizador: Mapped["Utilizador"] = relationship()  # noqa: F821
