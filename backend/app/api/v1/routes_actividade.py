"""
routes_actividade.py — Histórico, notificações e estatísticas.

  Histórico (utilizador autenticado):
    GET    /api/v1/history/reading    -> últimas leituras/descargas
    GET    /api/v1/history/searches   -> últimas pesquisas
    DELETE /api/v1/history            -> limpar histórico

  Notificações:
    GET    /api/v1/notifications       -> avisos + nº de não lidas
    POST   /api/v1/notifications/seen  -> marcar como vistas

  Estatísticas (apenas administrador):
    GET    /api/v1/stats/overview      -> painel de estatísticas
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import obter_utilizador_actual, exigir_perfis
from app.models.user import Utilizador, PerfilUtilizador
from app.schemas.actividade import (
    EstatisticasResposta,
    LeituraResposta,
    NotificacoesResposta,
    PesquisaResposta,
)
from app.services.servico_actividade import ServicoActividade

router = APIRouter()


# ------------------------------- Histórico -----------------------------------
@router.get("/history/reading", response_model=list[LeituraResposta], tags=["Histórico"])
def historico_leituras(
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    return ServicoActividade(db).historico_leituras(utilizador.id)


@router.get("/history/searches", response_model=list[PesquisaResposta], tags=["Histórico"])
def historico_pesquisas(
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    return ServicoActividade(db).historico_pesquisas(utilizador.id)


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT, tags=["Histórico"])
def limpar_historico(
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    ServicoActividade(db).limpar_historico(utilizador.id)
    return None


# ----------------------------- Notificações ----------------------------------
@router.get("/notifications", response_model=NotificacoesResposta, tags=["Notificações"])
def listar_notificacoes(
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    servico = ServicoActividade(db)
    return NotificacoesResposta(
        nao_lidas=servico.contar_nao_lidas(utilizador.id),
        itens=servico.listar_notificacoes(),
    )


@router.post("/notifications/seen", status_code=status.HTTP_204_NO_CONTENT, tags=["Notificações"])
def marcar_vistas(
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    ServicoActividade(db).marcar_vistas(utilizador.id)
    return None


# ----------------------------- Estatísticas ----------------------------------
@router.get("/stats/overview", response_model=EstatisticasResposta, tags=["Estatísticas"])
def estatisticas(
    _: Utilizador = Depends(exigir_perfis(PerfilUtilizador.administrador)),
    db: Session = Depends(get_db),
):
    return ServicoActividade(db).estatisticas()
