"""
servico_actividade.py — Histórico, notificações e estatísticas.

Regras de negócio das funcionalidades de acompanhamento:
  - Histórico de leituras e de pesquisas do utilizador.
  - Notificações globais (novos documentos) com contagem de "não lidas" por
    utilizador (via marcador de última visita).
  - Estatísticas para o administrador (mais vistos/descarregados, por categoria,
    termos mais pesquisados).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, func, desc
from sqlalchemy.orm import Session

from app.models.academic import AreaCientifica
from app.models.actividade import (
    HistoricoLeitura,
    HistoricoPesquisa,
    MarcadorNotificacao,
    Notificacao,
)
from app.models.document import Documento, EstadoDocumento
from app.models.user import Utilizador


class ServicoActividade:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------ Histórico --------------------------------
    def registar_leitura(self, utilizador_id: int, documento_id: int) -> None:
        self.db.add(
            HistoricoLeitura(utilizador_id=utilizador_id, documento_id=documento_id)
        )
        self.db.commit()

    def registar_pesquisa(
        self, utilizador_id: int, termo: str, semantica: bool = False
    ) -> None:
        termo = (termo or "").strip()
        if not termo:
            return
        self.db.add(
            HistoricoPesquisa(
                utilizador_id=utilizador_id, termo=termo[:200], semantica=semantica
            )
        )
        self.db.commit()

    def historico_leituras(self, utilizador_id: int, limite: int = 50) -> list[dict]:
        """Últimas leituras, sem repetir o mesmo documento (mais recente conta)."""
        stmt = (
            select(HistoricoLeitura, Documento)
            .join(Documento, Documento.id == HistoricoLeitura.documento_id)
            .where(HistoricoLeitura.utilizador_id == utilizador_id)
            .order_by(desc(HistoricoLeitura.data))
            .limit(300)
        )
        vistos: set[int] = set()
        saida: list[dict] = []
        for hist, doc in self.db.execute(stmt).all():
            if doc.id in vistos:
                continue
            vistos.add(doc.id)
            saida.append(
                {
                    "documento_id": doc.id,
                    "titulo": doc.titulo,
                    "tipo": getattr(doc.tipo, "value", str(doc.tipo)),
                    "capa_url": doc.capa_url,
                    "data": hist.data,
                }
            )
            if len(saida) >= limite:
                break
        return saida

    def historico_pesquisas(self, utilizador_id: int, limite: int = 50) -> list[dict]:
        stmt = (
            select(HistoricoPesquisa)
            .where(HistoricoPesquisa.utilizador_id == utilizador_id)
            .order_by(desc(HistoricoPesquisa.data))
            .limit(limite)
        )
        return [
            {"termo": h.termo, "semantica": h.semantica, "data": h.data}
            for h in self.db.scalars(stmt).all()
        ]

    def limpar_historico(self, utilizador_id: int) -> None:
        self.db.query(HistoricoLeitura).filter(
            HistoricoLeitura.utilizador_id == utilizador_id
        ).delete()
        self.db.query(HistoricoPesquisa).filter(
            HistoricoPesquisa.utilizador_id == utilizador_id
        ).delete()
        self.db.commit()

    # ----------------------------- Notificações ------------------------------
    def criar_notificacao(self, mensagem: str, documento_id: int | None = None) -> None:
        self.db.add(Notificacao(mensagem=mensagem[:300], documento_id=documento_id))
        self.db.commit()

    def listar_notificacoes(self, limite: int = 30) -> list[Notificacao]:
        stmt = select(Notificacao).order_by(desc(Notificacao.data)).limit(limite)
        return list(self.db.scalars(stmt).all())

    def contar_nao_lidas(self, utilizador_id: int) -> int:
        marcador = self.db.get(MarcadorNotificacao, utilizador_id)
        stmt = select(func.count()).select_from(Notificacao)
        if marcador is not None:
            stmt = stmt.where(Notificacao.data > marcador.vistas_em)
        return int(self.db.scalar(stmt) or 0)

    def marcar_vistas(self, utilizador_id: int) -> None:
        agora = datetime.now(timezone.utc)
        marcador = self.db.get(MarcadorNotificacao, utilizador_id)
        if marcador is None:
            self.db.add(
                MarcadorNotificacao(utilizador_id=utilizador_id, vistas_em=agora)
            )
        else:
            marcador.vistas_em = agora
        self.db.commit()

    # ----------------------------- Estatísticas ------------------------------
    def estatisticas(self, limite: int = 5) -> dict:
        pub = Documento.estado == EstadoDocumento.publicado

        total_documentos = int(
            self.db.scalar(select(func.count()).select_from(Documento).where(pub)) or 0
        )
        total_utilizadores = int(
            self.db.scalar(select(func.count()).select_from(Utilizador)) or 0
        )
        total_downloads = int(
            self.db.scalar(select(func.coalesce(func.sum(Documento.num_downloads), 0))) or 0
        )
        total_visualizacoes = int(
            self.db.scalar(
                select(func.coalesce(func.sum(Documento.num_visualizacoes), 0))
            )
            or 0
        )

        mais_vistos = [
            {
                "documento_id": d.id,
                "titulo": d.titulo,
                "valor": d.num_visualizacoes or 0,
            }
            for d in self.db.scalars(
                select(Documento)
                .where(pub)
                .order_by(desc(Documento.num_visualizacoes))
                .limit(limite)
            ).all()
        ]
        mais_descarregados = [
            {"documento_id": d.id, "titulo": d.titulo, "valor": d.num_downloads or 0}
            for d in self.db.scalars(
                select(Documento)
                .where(pub)
                .order_by(desc(Documento.num_downloads))
                .limit(limite)
            ).all()
        ]

        # Documentos por categoria (secção CDU).
        por_area = dict(
            self.db.execute(
                select(Documento.area_id, func.count())
                .where(pub)
                .group_by(Documento.area_id)
            ).all()
        )
        areas = {a.id: a for a in self.db.scalars(select(AreaCientifica)).all()}
        por_categoria = [
            {
                "nome": areas[aid].nome if aid in areas else "Sem secção",
                "total": int(total),
            }
            for aid, total in por_area.items()
            if aid is not None
        ]
        por_categoria.sort(key=lambda x: x["total"], reverse=True)

        # Termos mais pesquisados (histórico de pesquisas).
        termos = [
            {"termo": termo, "total": int(total)}
            for termo, total in self.db.execute(
                select(HistoricoPesquisa.termo, func.count())
                .group_by(HistoricoPesquisa.termo)
                .order_by(desc(func.count()))
                .limit(limite)
            ).all()
        ]

        return {
            "total_documentos": total_documentos,
            "total_utilizadores": total_utilizadores,
            "total_downloads": total_downloads,
            "total_visualizacoes": total_visualizacoes,
            "mais_vistos": mais_vistos,
            "mais_descarregados": mais_descarregados,
            "por_categoria": por_categoria,
            "termos_mais_pesquisados": termos,
        }
