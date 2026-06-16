"""
routes_circulacao.py — Gestão bibliotecária (circulação).

Empréstimos, devoluções, renovações, reservas (lista de espera), multas e
relatórios. Os leitores (estudante/docente/investigador) gerem os seus próprios
empréstimos e reservas; as operações de gestão (registar exemplares, devolver,
ver tudo, cobrar multas, relatórios) são do administrador/bibliotecário.

  Leitor:
    GET    /circulation/documents/{id}/availability   -> disponibilidade
    POST   /circulation/loans                          -> requisitar
    GET    /circulation/loans/me                       -> os meus empréstimos
    POST   /circulation/loans/{id}/renew               -> renovar
    POST   /circulation/reservations                   -> reservar (fila)
    GET    /circulation/reservations/me                -> as minhas reservas
    DELETE /circulation/reservations/{id}              -> cancelar reserva
    GET    /circulation/fines/me                        -> as minhas multas

  Bibliotecário (administrador):
    GET    /circulation/documents/{id}/copies          -> exemplares da obra
    POST   /circulation/copies                          -> criar exemplares
    GET    /circulation/loans                           -> todos os empréstimos
    POST   /circulation/loans/{id}/return               -> registar devolução
    GET    /circulation/reservations                    -> todas as reservas
    GET    /circulation/fines                           -> todas as multas
    POST   /circulation/fines/{id}/pay                  -> marcar multa paga
    GET    /circulation/report                           -> estatísticas
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import (
    exigir_perfis,
    obter_utilizador_actual,
    obter_utilizador_opcional,
)
from app.models.user import PerfilUtilizador, Utilizador
from app.schemas.circulacao import (
    DisponibilidadeResposta,
    EmprestimoCriar,
    EmprestimoResposta,
    ExemplarResposta,
    ExemplaresCriar,
    MultaResposta,
    RelatorioCirculacao,
    ReservaCriar,
    ReservaResposta,
)
from app.services.servico_circulacao import ServicoCirculacao

router = APIRouter()

_so_admin = exigir_perfis(PerfilUtilizador.administrador)


# ------------------------------- Exemplares ----------------------------------
@router.get(
    "/documents/{documento_id}/copies",
    response_model=list[ExemplarResposta],
    tags=["Circulação"],
)
def listar_exemplares(documento_id: int, db: Session = Depends(get_db)):
    return ServicoCirculacao(db).listar_exemplares(documento_id)


@router.post(
    "/copies",
    response_model=list[ExemplarResposta],
    status_code=status.HTTP_201_CREATED,
    tags=["Circulação"],
)
def criar_exemplares(
    dados: ExemplaresCriar,
    _: Utilizador = Depends(_so_admin),
    db: Session = Depends(get_db),
):
    return ServicoCirculacao(db).criar_exemplares(
        dados.documento_id, dados.quantidade, dados.localizacao
    )


# ---------------------------- Disponibilidade --------------------------------
@router.get(
    "/documents/{documento_id}/availability",
    response_model=DisponibilidadeResposta,
    tags=["Circulação"],
)
def disponibilidade(
    documento_id: int,
    leitor: Optional[Utilizador] = Depends(obter_utilizador_opcional),
    db: Session = Depends(get_db),
):
    return ServicoCirculacao(db).disponibilidade(documento_id, leitor)


# ------------------------------ Empréstimos ----------------------------------
@router.post(
    "/loans",
    response_model=EmprestimoResposta,
    status_code=status.HTTP_201_CREATED,
    tags=["Circulação"],
)
def requisitar(
    dados: EmprestimoCriar,
    actual: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    # O bibliotecário pode emprestar em nome de outro leitor; caso contrário, é
    # para o próprio.
    leitor = actual
    if dados.utilizador_id and actual.perfil == PerfilUtilizador.administrador:
        alvo = db.get(Utilizador, dados.utilizador_id)
        if alvo is not None:
            leitor = alvo
    emp = servico.emprestar(dados.documento_id, leitor)
    return servico.resposta_emprestimo(emp)


@router.get("/loans/me", response_model=list[EmprestimoResposta], tags=["Circulação"])
def meus_emprestimos(
    actual: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    emprestimos = servico.listar_emprestimos(utilizador_id=actual.id)
    return [servico.resposta_emprestimo(e) for e in emprestimos]


@router.get("/loans", response_model=list[EmprestimoResposta], tags=["Circulação"])
def todos_emprestimos(
    apenas_activos: bool = False,
    _: Utilizador = Depends(_so_admin),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    emprestimos = servico.listar_emprestimos(apenas_activos=apenas_activos)
    return [servico.resposta_emprestimo(e) for e in emprestimos]


@router.post(
    "/loans/{emprestimo_id}/return",
    response_model=EmprestimoResposta,
    tags=["Circulação"],
)
def devolver(
    emprestimo_id: int,
    _: Utilizador = Depends(_so_admin),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    emp = servico.devolver(emprestimo_id)
    return servico.resposta_emprestimo(emp)


@router.post(
    "/loans/{emprestimo_id}/renew",
    response_model=EmprestimoResposta,
    tags=["Circulação"],
)
def renovar(
    emprestimo_id: int,
    actual: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    emp = servico.renovar(emprestimo_id, actual)
    return servico.resposta_emprestimo(emp)


# -------------------------------- Reservas -----------------------------------
@router.post(
    "/reservations",
    response_model=ReservaResposta,
    status_code=status.HTTP_201_CREATED,
    tags=["Circulação"],
)
def reservar(
    dados: ReservaCriar,
    actual: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    reserva = servico.reservar(dados.documento_id, actual)
    return servico.resposta_reserva(reserva)


@router.get("/reservations/me", response_model=list[ReservaResposta], tags=["Circulação"])
def minhas_reservas(
    actual: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    reservas = servico.listar_reservas(utilizador_id=actual.id)
    return [servico.resposta_reserva(r) for r in reservas]


@router.get("/reservations", response_model=list[ReservaResposta], tags=["Circulação"])
def todas_reservas(
    _: Utilizador = Depends(_so_admin),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    reservas = servico.listar_reservas()
    return [servico.resposta_reserva(r) for r in reservas]


@router.delete(
    "/reservations/{reserva_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Circulação"],
)
def cancelar_reserva(
    reserva_id: int,
    actual: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    ServicoCirculacao(db).cancelar_reserva(reserva_id, actual)
    return None


# --------------------------------- Multas ------------------------------------
@router.get("/fines/me", response_model=list[MultaResposta], tags=["Circulação"])
def minhas_multas(
    actual: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    multas = servico.listar_multas(utilizador_id=actual.id)
    return [servico.resposta_multa(m) for m in multas]


@router.get("/fines", response_model=list[MultaResposta], tags=["Circulação"])
def todas_multas(
    apenas_por_pagar: bool = False,
    _: Utilizador = Depends(_so_admin),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    multas = servico.listar_multas(apenas_por_pagar=apenas_por_pagar)
    return [servico.resposta_multa(m) for m in multas]


@router.post("/fines/{multa_id}/pay", response_model=MultaResposta, tags=["Circulação"])
def pagar_multa(
    multa_id: int,
    _: Utilizador = Depends(_so_admin),
    db: Session = Depends(get_db),
):
    servico = ServicoCirculacao(db)
    multa = servico.pagar_multa(multa_id)
    return servico.resposta_multa(multa)


# ------------------------------- Relatórios ----------------------------------
@router.get("/report", response_model=RelatorioCirculacao, tags=["Circulação"])
def relatorio(
    _: Utilizador = Depends(_so_admin),
    db: Session = Depends(get_db),
):
    return ServicoCirculacao(db).relatorio()
