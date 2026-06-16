"""
servico_circulacao.py — Regras de negócio da gestão bibliotecária.

Concentra toda a lógica de uma biblioteca real:

  * Políticas por perfil (quantos livros e por quantos dias cada tipo de leitor
    pode requisitar) — estudante vs. docente/investigador.
  * Empréstimo: escolhe um exemplar livre, valida limites e multas em dívida.
  * Devolução: calcula atraso, cria multa se for o caso e atende a próxima
    reserva da fila.
  * Renovação: estende o prazo, desde que não haja reservas à espera.
  * Reservas: lista de espera por ordem de chegada.
  * Multas: cálculo por dia de atraso (em Kwanzas) e pagamento.
  * Relatórios: estatísticas de circulação para o bibliotecário.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.circulacao import (
    Emprestimo,
    EstadoEmprestimo,
    EstadoExemplar,
    EstadoReserva,
    Exemplar,
    Multa,
    Reserva,
)
from app.models.document import Documento
from app.models.user import PerfilUtilizador, Utilizador


# ----------------------------- Políticas de empréstimo -----------------------
@dataclass(frozen=True)
class Politica:
    """Regras de circulação aplicáveis a um perfil de leitor."""

    max_emprestimos: int
    dias_prazo: int
    max_renovacoes: int


# Estudante leva menos livros e por menos tempo; docente/investigador têm mais
# margem (como nas bibliotecas universitárias reais).
POLITICAS: dict[PerfilUtilizador, Politica] = {
    PerfilUtilizador.estudante: Politica(max_emprestimos=3, dias_prazo=14, max_renovacoes=2),
    PerfilUtilizador.professor: Politica(max_emprestimos=5, dias_prazo=30, max_renovacoes=3),
    PerfilUtilizador.investigador: Politica(max_emprestimos=5, dias_prazo=30, max_renovacoes=3),
    PerfilUtilizador.administrador: Politica(max_emprestimos=10, dias_prazo=30, max_renovacoes=5),
}

# Valor da multa por cada dia de atraso, em Kwanzas (AOA).
MULTA_POR_DIA = 100.0


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime | None) -> datetime | None:
    """Garante que a data tem fuso horário (algumas BDs devolvem datas ingénuas)."""
    if dt is None:
        return None
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


class ServicoCirculacao:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------- Auxiliares ------------------------------
    def _politica(self, leitor: Utilizador) -> Politica:
        pol = POLITICAS.get(leitor.perfil)
        if pol is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O seu perfil não permite requisitar obras.",
            )
        return pol

    def _documento(self, documento_id: int) -> Documento:
        doc = self.db.get(Documento, documento_id)
        if doc is None:
            raise HTTPException(status_code=404, detail="Obra não encontrada.")
        return doc

    def _emprestimos_activos(self, utilizador_id: int) -> int:
        return self.db.scalar(
            select(func.count(Emprestimo.id)).where(
                Emprestimo.utilizador_id == utilizador_id,
                Emprestimo.estado != EstadoEmprestimo.devolvido,
            )
        ) or 0

    def _multas_por_pagar(self, utilizador_id: int) -> int:
        return self.db.scalar(
            select(func.count(Multa.id)).where(
                Multa.utilizador_id == utilizador_id, Multa.paga.is_(False)
            )
        ) or 0

    def _dias_atraso(self, emp: Emprestimo, referencia: datetime | None = None) -> int:
        ref = referencia or _agora()
        prazo = _aware(emp.data_prevista_devolucao)
        if prazo and ref > prazo:
            return (ref - prazo).days
        return 0

    # ------------------------------ Exemplares -------------------------------
    def criar_exemplares(
        self, documento_id: int, quantidade: int, localizacao: str | None
    ) -> list[Exemplar]:
        doc = self._documento(documento_id)
        # Sequência contínua por obra: cota = "<id da obra>-<n>".
        existentes = self.db.scalar(
            select(func.count(Exemplar.id)).where(Exemplar.documento_id == documento_id)
        ) or 0
        novos: list[Exemplar] = []
        for i in range(quantidade):
            ex = Exemplar(
                documento_id=doc.id,
                numero_registo=f"BASI-{doc.id:04d}-{existentes + i + 1:02d}",
                estado=EstadoExemplar.disponivel,
                localizacao=localizacao,
            )
            self.db.add(ex)
            novos.append(ex)
        self.db.commit()
        for ex in novos:
            self.db.refresh(ex)
        return novos

    def listar_exemplares(self, documento_id: int) -> list[Exemplar]:
        return list(
            self.db.scalars(
                select(Exemplar)
                .where(Exemplar.documento_id == documento_id)
                .order_by(Exemplar.numero_registo)
            )
        )

    def _exemplar_disponivel(self, documento_id: int) -> Exemplar | None:
        return self.db.scalars(
            select(Exemplar)
            .where(
                Exemplar.documento_id == documento_id,
                Exemplar.estado == EstadoExemplar.disponivel,
            )
            .order_by(Exemplar.id)
            .limit(1)
        ).first()

    # ---------------------------- Disponibilidade ----------------------------
    def disponibilidade(self, documento_id: int, leitor: Utilizador | None) -> dict:
        doc = self._documento(documento_id)
        total = self.db.scalar(
            select(func.count(Exemplar.id)).where(Exemplar.documento_id == doc.id)
        ) or 0
        disponiveis = self.db.scalar(
            select(func.count(Exemplar.id)).where(
                Exemplar.documento_id == doc.id,
                Exemplar.estado == EstadoExemplar.disponivel,
            )
        ) or 0
        reservas = self.db.scalar(
            select(func.count(Reserva.id)).where(
                Reserva.documento_id == doc.id,
                Reserva.estado == EstadoReserva.activa,
            )
        ) or 0

        ja_tem = False
        ja_reservou = False
        pode_requisitar = False
        pode_reservar = False
        motivo: str | None = None

        if leitor is None:
            motivo = "Inicie sessão para requisitar ou reservar."
        elif leitor.perfil not in POLITICAS:
            motivo = "O seu perfil (visitante) não permite requisitar obras."
        else:
            ja_tem = self.db.scalar(
                select(func.count(Emprestimo.id))
                .join(Exemplar, Emprestimo.exemplar_id == Exemplar.id)
                .where(
                    Exemplar.documento_id == doc.id,
                    Emprestimo.utilizador_id == leitor.id,
                    Emprestimo.estado != EstadoEmprestimo.devolvido,
                )
            ) > 0
            ja_reservou = self.db.scalar(
                select(func.count(Reserva.id)).where(
                    Reserva.documento_id == doc.id,
                    Reserva.utilizador_id == leitor.id,
                    Reserva.estado.in_([EstadoReserva.activa, EstadoReserva.atendida]),
                )
            ) > 0
            pol = POLITICAS[leitor.perfil]
            no_limite = self._emprestimos_activos(leitor.id) >= pol.max_emprestimos
            tem_multas = self._multas_por_pagar(leitor.id) > 0

            if ja_tem:
                motivo = "Já tem esta obra requisitada."
            elif tem_multas:
                motivo = "Tem multas por pagar. Regularize para poder requisitar."
            elif no_limite:
                motivo = f"Atingiu o limite de {pol.max_emprestimos} empréstimos em simultâneo."
            elif total == 0:
                motivo = "Esta obra ainda não tem exemplares registados."
            elif disponiveis > 0:
                pode_requisitar = True
            else:
                if ja_reservou:
                    motivo = "Já está na lista de espera desta obra."
                else:
                    pode_reservar = True
                    motivo = "Sem exemplares livres — pode entrar na lista de espera."

        return {
            "documento_id": doc.id,
            "total_exemplares": total,
            "disponiveis": disponiveis,
            "reservas_em_espera": reservas,
            "pode_requisitar": pode_requisitar,
            "pode_reservar": pode_reservar,
            "ja_tem_emprestimo": ja_tem,
            "ja_reservou": ja_reservou,
            "motivo": motivo,
        }

    # ------------------------------ Empréstimos ------------------------------
    def emprestar(
        self, documento_id: int, leitor: Utilizador, exemplar_de_reserva: Exemplar | None = None
    ) -> Emprestimo:
        pol = self._politica(leitor)

        # Bloqueios: multas por pagar e limite de empréstimos.
        if self._multas_por_pagar(leitor.id) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tem multas por pagar. Regularize antes de requisitar.",
            )
        if self._emprestimos_activos(leitor.id) >= pol.max_emprestimos:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Atingiu o limite de {pol.max_emprestimos} empréstimos em simultâneo.",
            )

        # Já tem esta mesma obra?
        ja_tem = self.db.scalar(
            select(func.count(Emprestimo.id))
            .join(Exemplar, Emprestimo.exemplar_id == Exemplar.id)
            .where(
                Exemplar.documento_id == documento_id,
                Emprestimo.utilizador_id == leitor.id,
                Emprestimo.estado != EstadoEmprestimo.devolvido,
            )
        ) > 0
        if ja_tem:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já tem esta obra requisitada.",
            )

        exemplar = exemplar_de_reserva or self._exemplar_disponivel(documento_id)
        if exemplar is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Não há exemplares livres. Pode fazer uma reserva.",
            )

        agora = _agora()
        emp = Emprestimo(
            exemplar_id=exemplar.id,
            utilizador_id=leitor.id,
            data_emprestimo=agora,
            data_prevista_devolucao=agora + timedelta(days=pol.dias_prazo),
            estado=EstadoEmprestimo.activo,
        )
        exemplar.estado = EstadoExemplar.emprestado
        self.db.add(emp)
        self.db.commit()
        self.db.refresh(emp)
        return emp

    def devolver(self, emprestimo_id: int) -> Emprestimo:
        emp = self.db.get(Emprestimo, emprestimo_id)
        if emp is None:
            raise HTTPException(status_code=404, detail="Empréstimo não encontrado.")
        if emp.estado == EstadoEmprestimo.devolvido:
            raise HTTPException(status_code=409, detail="Este empréstimo já foi devolvido.")

        agora = _agora()
        emp.data_devolucao = agora
        emp.estado = EstadoEmprestimo.devolvido

        # Multa por atraso, se aplicável. Só se cria UMA multa por empréstimo —
        # se já existir (ex.: gerada antecipadamente), actualiza-se o valor em vez
        # de duplicar a cobrança.
        dias = self._dias_atraso(emp, agora)
        if dias > 0:
            multa = self.db.scalars(
                select(Multa).where(Multa.emprestimo_id == emp.id).limit(1)
            ).first()
            if multa is None:
                self.db.add(
                    Multa(
                        emprestimo_id=emp.id,
                        utilizador_id=emp.utilizador_id,
                        dias_atraso=dias,
                        valor=dias * MULTA_POR_DIA,
                        paga=False,
                    )
                )
            elif not multa.paga:
                # Acerta o valor final (o atraso pode ter aumentado até à devolução).
                multa.dias_atraso = dias
                multa.valor = dias * MULTA_POR_DIA

        exemplar = self.db.get(Exemplar, emp.exemplar_id)

        # Atende a próxima reserva da fila (se houver) com este exemplar.
        reserva = None
        if exemplar is not None:
            reserva = self.db.scalars(
                select(Reserva)
                .where(
                    Reserva.documento_id == exemplar.documento_id,
                    Reserva.estado == EstadoReserva.activa,
                )
                .order_by(Reserva.data_reserva)
                .limit(1)
            ).first()

        if exemplar is not None:
            if reserva is not None:
                reserva.estado = EstadoReserva.atendida
                reserva.exemplar_id = exemplar.id
                exemplar.estado = EstadoExemplar.reservado
            else:
                exemplar.estado = EstadoExemplar.disponivel

        self.db.commit()
        self.db.refresh(emp)
        return emp

    def renovar(self, emprestimo_id: int, leitor: Utilizador) -> Emprestimo:
        emp = self.db.get(Emprestimo, emprestimo_id)
        if emp is None:
            raise HTTPException(status_code=404, detail="Empréstimo não encontrado.")
        # Só o próprio leitor ou um administrador pode renovar.
        if emp.utilizador_id != leitor.id and leitor.perfil != PerfilUtilizador.administrador:
            raise HTTPException(status_code=403, detail="Não pode renovar este empréstimo.")
        if emp.estado == EstadoEmprestimo.devolvido:
            raise HTTPException(status_code=409, detail="Empréstimo já devolvido.")

        dono = self.db.get(Utilizador, emp.utilizador_id)
        pol = self._politica(dono)
        if emp.renovacoes >= pol.max_renovacoes:
            raise HTTPException(
                status_code=409,
                detail=f"Limite de {pol.max_renovacoes} renovações atingido.",
            )

        exemplar = self.db.get(Exemplar, emp.exemplar_id)
        if exemplar is not None:
            ha_reservas = self.db.scalar(
                select(func.count(Reserva.id)).where(
                    Reserva.documento_id == exemplar.documento_id,
                    Reserva.estado == EstadoReserva.activa,
                )
            ) > 0
            if ha_reservas:
                raise HTTPException(
                    status_code=409,
                    detail="Não pode renovar: há leitores em lista de espera.",
                )

        # Renova a partir de hoje (ou do prazo, o que for mais tarde).
        base = max(_agora(), _aware(emp.data_prevista_devolucao) or _agora())
        emp.data_prevista_devolucao = base + timedelta(days=pol.dias_prazo)
        emp.renovacoes += 1
        emp.estado = EstadoEmprestimo.activo
        self.db.commit()
        self.db.refresh(emp)
        return emp

    def listar_emprestimos(
        self, utilizador_id: int | None = None, apenas_activos: bool = False
    ) -> list[Emprestimo]:
        consulta = select(Emprestimo)
        if utilizador_id is not None:
            consulta = consulta.where(Emprestimo.utilizador_id == utilizador_id)
        if apenas_activos:
            consulta = consulta.where(Emprestimo.estado != EstadoEmprestimo.devolvido)
        consulta = consulta.order_by(Emprestimo.data_emprestimo.desc())
        return list(self.db.scalars(consulta))

    # ------------------------------- Reservas --------------------------------
    def reservar(self, documento_id: int, leitor: Utilizador) -> Reserva:
        if leitor.perfil not in POLITICAS:
            raise HTTPException(status_code=403, detail="O seu perfil não permite reservas.")
        doc = self._documento(documento_id)

        # Só faz sentido reservar se NÃO houver exemplares livres.
        if self._exemplar_disponivel(documento_id) is not None:
            raise HTTPException(
                status_code=409,
                detail="Há exemplares disponíveis — pode requisitar já, sem reservar.",
            )
        # Não duplicar reserva.
        ja = self.db.scalar(
            select(func.count(Reserva.id)).where(
                Reserva.documento_id == doc.id,
                Reserva.utilizador_id == leitor.id,
                Reserva.estado.in_([EstadoReserva.activa, EstadoReserva.atendida]),
            )
        ) > 0
        if ja:
            raise HTTPException(status_code=409, detail="Já está na lista de espera desta obra.")
        # Não reservar uma obra que já tem em mãos.
        tem = self.db.scalar(
            select(func.count(Emprestimo.id))
            .join(Exemplar, Emprestimo.exemplar_id == Exemplar.id)
            .where(
                Exemplar.documento_id == doc.id,
                Emprestimo.utilizador_id == leitor.id,
                Emprestimo.estado != EstadoEmprestimo.devolvido,
            )
        ) > 0
        if tem:
            raise HTTPException(status_code=409, detail="Já tem esta obra requisitada.")

        reserva = Reserva(documento_id=doc.id, utilizador_id=leitor.id, estado=EstadoReserva.activa)
        self.db.add(reserva)
        self.db.commit()
        self.db.refresh(reserva)
        return reserva

    def cancelar_reserva(self, reserva_id: int, leitor: Utilizador) -> None:
        reserva = self.db.get(Reserva, reserva_id)
        if reserva is None:
            raise HTTPException(status_code=404, detail="Reserva não encontrada.")
        if reserva.utilizador_id != leitor.id and leitor.perfil != PerfilUtilizador.administrador:
            raise HTTPException(status_code=403, detail="Não pode cancelar esta reserva.")
        if reserva.estado not in (EstadoReserva.activa, EstadoReserva.atendida):
            raise HTTPException(status_code=409, detail="Esta reserva já não está activa.")

        # Se já tinha um exemplar guardado, liberta-o (volta a ficar disponível).
        if reserva.exemplar_id is not None:
            ex = self.db.get(Exemplar, reserva.exemplar_id)
            if ex is not None and ex.estado == EstadoExemplar.reservado:
                ex.estado = EstadoExemplar.disponivel
        reserva.estado = EstadoReserva.cancelada
        self.db.commit()

    def listar_reservas(self, utilizador_id: int | None = None) -> list[Reserva]:
        consulta = select(Reserva).where(
            Reserva.estado.in_([EstadoReserva.activa, EstadoReserva.atendida])
        )
        if utilizador_id is not None:
            consulta = consulta.where(Reserva.utilizador_id == utilizador_id)
        consulta = consulta.order_by(Reserva.data_reserva)
        return list(self.db.scalars(consulta))

    def posicao_na_fila(self, reserva: Reserva) -> int | None:
        """Lugar de uma reserva activa na fila da obra (1 = próximo a ser servido)."""
        if reserva.estado == EstadoReserva.atendida:
            return 0
        if reserva.estado != EstadoReserva.activa:
            return None
        anteriores = self.db.scalar(
            select(func.count(Reserva.id)).where(
                Reserva.documento_id == reserva.documento_id,
                Reserva.estado == EstadoReserva.activa,
                Reserva.data_reserva < reserva.data_reserva,
            )
        ) or 0
        return anteriores + 1

    # -------------------------------- Multas ---------------------------------
    def listar_multas(
        self, utilizador_id: int | None = None, apenas_por_pagar: bool = False
    ) -> list[Multa]:
        consulta = select(Multa)
        if utilizador_id is not None:
            consulta = consulta.where(Multa.utilizador_id == utilizador_id)
        if apenas_por_pagar:
            consulta = consulta.where(Multa.paga.is_(False))
        consulta = consulta.order_by(Multa.data_criacao.desc())
        return list(self.db.scalars(consulta))

    def pagar_multa(self, multa_id: int) -> Multa:
        multa = self.db.get(Multa, multa_id)
        if multa is None:
            raise HTTPException(status_code=404, detail="Multa não encontrada.")
        if multa.paga:
            raise HTTPException(status_code=409, detail="Esta multa já está paga.")
        multa.paga = True
        multa.data_pagamento = _agora()
        self.db.commit()
        self.db.refresh(multa)
        return multa

    # ------------------------------ Relatórios -------------------------------
    def relatorio(self) -> dict:
        total_exemplares = self.db.scalar(select(func.count(Exemplar.id))) or 0
        disponiveis = self.db.scalar(
            select(func.count(Exemplar.id)).where(
                Exemplar.estado == EstadoExemplar.disponivel
            )
        ) or 0
        emp_activos = self.db.scalar(
            select(func.count(Emprestimo.id)).where(
                Emprestimo.estado != EstadoEmprestimo.devolvido
            )
        ) or 0

        # Atrasados = activos cujo prazo já passou.
        atrasados = 0
        for emp in self.db.scalars(
            select(Emprestimo).where(Emprestimo.estado != EstadoEmprestimo.devolvido)
        ):
            if self._dias_atraso(emp) > 0:
                atrasados += 1

        reservas_activas = self.db.scalar(
            select(func.count(Reserva.id)).where(Reserva.estado == EstadoReserva.activa)
        ) or 0
        multas_por_pagar = self.db.scalar(
            select(func.count(Multa.id)).where(Multa.paga.is_(False))
        ) or 0
        valor_multas = self.db.scalar(
            select(func.coalesce(func.sum(Multa.valor), 0)).where(Multa.paga.is_(False))
        ) or 0
        total_hist = self.db.scalar(select(func.count(Emprestimo.id))) or 0

        # Obras mais requisitadas (top 5).
        linhas = self.db.execute(
            select(
                Exemplar.documento_id,
                Documento.titulo,
                func.count(Emprestimo.id).label("total"),
            )
            .join(Exemplar, Emprestimo.exemplar_id == Exemplar.id)
            .join(Documento, Documento.id == Exemplar.documento_id)
            .group_by(Exemplar.documento_id, Documento.titulo)
            .order_by(func.count(Emprestimo.id).desc())
            .limit(5)
        ).all()
        mais = [
            {"documento_id": did, "titulo": titulo, "total": total}
            for (did, titulo, total) in linhas
        ]

        return {
            "total_exemplares": total_exemplares,
            "exemplares_disponiveis": disponiveis,
            "emprestimos_activos": emp_activos,
            "emprestimos_atrasados": atrasados,
            "reservas_activas": reservas_activas,
            "multas_por_pagar": multas_por_pagar,
            "valor_multas_por_pagar": float(valor_multas),
            "total_emprestimos_historico": total_hist,
            "obras_mais_requisitadas": mais,
        }

    # ---------------------- Construção de respostas ricas --------------------
    def resposta_emprestimo(self, emp: Emprestimo) -> dict:
        exemplar = self.db.get(Exemplar, emp.exemplar_id)
        doc = self.db.get(Documento, exemplar.documento_id) if exemplar else None
        leitor = self.db.get(Utilizador, emp.utilizador_id)
        dias = self._dias_atraso(emp) if emp.estado != EstadoEmprestimo.devolvido else 0
        return {
            "id": emp.id,
            "exemplar_id": emp.exemplar_id,
            "utilizador_id": emp.utilizador_id,
            "data_emprestimo": emp.data_emprestimo,
            "data_prevista_devolucao": emp.data_prevista_devolucao,
            "data_devolucao": emp.data_devolucao,
            "estado": EstadoEmprestimo.atrasado if dias > 0 else emp.estado,
            "renovacoes": emp.renovacoes,
            "documento_id": doc.id if doc else None,
            "documento_titulo": doc.titulo if doc else None,
            "numero_registo": exemplar.numero_registo if exemplar else None,
            "leitor_nome": leitor.nome if leitor else None,
            "dias_em_atraso": dias,
            "multa_valor": dias * MULTA_POR_DIA,
        }

    def resposta_reserva(self, reserva: Reserva) -> dict:
        doc = self.db.get(Documento, reserva.documento_id)
        leitor = self.db.get(Utilizador, reserva.utilizador_id)
        return {
            "id": reserva.id,
            "documento_id": reserva.documento_id,
            "utilizador_id": reserva.utilizador_id,
            "data_reserva": reserva.data_reserva,
            "estado": reserva.estado,
            "documento_titulo": doc.titulo if doc else None,
            "leitor_nome": leitor.nome if leitor else None,
            "posicao": self.posicao_na_fila(reserva),
        }

    def resposta_multa(self, multa: Multa) -> dict:
        leitor = self.db.get(Utilizador, multa.utilizador_id)
        titulo = None
        emp = self.db.get(Emprestimo, multa.emprestimo_id)
        if emp is not None:
            exemplar = self.db.get(Exemplar, emp.exemplar_id)
            if exemplar is not None:
                doc = self.db.get(Documento, exemplar.documento_id)
                titulo = doc.titulo if doc else None
        return {
            "id": multa.id,
            "emprestimo_id": multa.emprestimo_id,
            "utilizador_id": multa.utilizador_id,
            "dias_atraso": multa.dias_atraso,
            "valor": float(multa.valor),
            "paga": multa.paga,
            "data_criacao": multa.data_criacao,
            "data_pagamento": multa.data_pagamento,
            "documento_titulo": titulo,
            "leitor_nome": leitor.nome if leitor else None,
        }
