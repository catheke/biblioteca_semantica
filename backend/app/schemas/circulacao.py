"""
circulacao.py — Schemas (Pydantic) da gestão bibliotecária.

Definem o formato dos pedidos e respostas de exemplares, empréstimos, reservas,
multas e relatórios. As respostas enriquecidas (com título da obra e nome do
leitor) facilitam a vida ao frontend, evitando pedidos extra.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict

from app.models.circulacao import (
    EstadoExemplar,
    EstadoEmprestimo,
    EstadoReserva,
)


# ------------------------------- Exemplares ----------------------------------
class ExemplarResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    documento_id: int
    numero_registo: str
    estado: EstadoExemplar
    localizacao: Optional[str] = None


class ExemplaresCriar(BaseModel):
    """Cria N exemplares novos para uma obra (usado pelo bibliotecário)."""

    documento_id: int
    quantidade: int = Field(default=1, ge=1, le=50)
    localizacao: Optional[str] = Field(default=None, max_length=120)


class DisponibilidadeResposta(BaseModel):
    """Resumo de disponibilidade de uma obra, para a página do documento."""

    documento_id: int
    total_exemplares: int
    disponiveis: int
    reservas_em_espera: int
    pode_requisitar: bool      # há exemplar livre e o leitor pode levar
    pode_reservar: bool        # está tudo emprestado -> pode entrar na fila
    ja_tem_emprestimo: bool    # o leitor já tem esta obra emprestada
    ja_reservou: bool          # o leitor já tem reserva activa nesta obra
    motivo: Optional[str] = None  # explicação quando não pode requisitar


# ------------------------------- Empréstimos ---------------------------------
class EmprestimoCriar(BaseModel):
    """Requisição de uma obra. O sistema escolhe um exemplar livre."""

    documento_id: int
    # Opcional: o bibliotecário pode emprestar em nome de outro leitor.
    utilizador_id: Optional[int] = None


class EmprestimoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exemplar_id: int
    utilizador_id: int
    data_emprestimo: datetime
    data_prevista_devolucao: datetime
    data_devolucao: Optional[datetime] = None
    estado: EstadoEmprestimo
    renovacoes: int
    # Campos enriquecidos (preenchidos pelo serviço).
    documento_id: Optional[int] = None
    documento_titulo: Optional[str] = None
    numero_registo: Optional[str] = None
    leitor_nome: Optional[str] = None
    dias_em_atraso: int = 0
    multa_valor: float = 0.0


# -------------------------------- Reservas -----------------------------------
class ReservaCriar(BaseModel):
    documento_id: int


class ReservaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    documento_id: int
    utilizador_id: int
    data_reserva: datetime
    estado: EstadoReserva
    documento_titulo: Optional[str] = None
    leitor_nome: Optional[str] = None
    posicao: Optional[int] = None  # lugar na fila (1 = próximo)


# --------------------------------- Multas ------------------------------------
class MultaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    emprestimo_id: int
    utilizador_id: int
    dias_atraso: int
    valor: float
    paga: bool
    data_criacao: datetime
    data_pagamento: Optional[datetime] = None
    documento_titulo: Optional[str] = None
    leitor_nome: Optional[str] = None


# ------------------------------- Relatórios ----------------------------------
class ObraMaisRequisitada(BaseModel):
    documento_id: int
    titulo: str
    total: int


class RelatorioCirculacao(BaseModel):
    """Painel de estatísticas para o bibliotecário."""

    total_exemplares: int
    exemplares_disponiveis: int
    emprestimos_activos: int
    emprestimos_atrasados: int
    reservas_activas: int
    multas_por_pagar: int
    valor_multas_por_pagar: float
    total_emprestimos_historico: int
    obras_mais_requisitadas: list[ObraMaisRequisitada] = Field(default_factory=list)
