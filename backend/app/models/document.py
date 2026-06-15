"""
document.py — Modelo ORM do Documento (entidade central).

Cada documento pertence a um autor (Utilizador) e, opcionalmente, a uma área.
O campo `uri_semantica` liga a linha SQL ao recurso correspondente no grafo RDF.
"""
from __future__ import annotations

from typing import Optional

import enum
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, Enum as SAEnum, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TipoDocumento(str, enum.Enum):
    livro = "livro"
    artigo = "artigo"
    tese = "tese"
    monografia = "monografia"
    manual = "manual"
    apresentacao = "apresentacao"
    material_didactico = "material_didactico"


class EstadoDocumento(str, enum.Enum):
    rascunho = "rascunho"
    publicado = "publicado"
    em_revisao = "em_revisao"
    rejeitado = "rejeitado"


class NivelAcesso(str, enum.Enum):
    """
    Quem pode DESCARREGAR/ler o ficheiro de um documento.

    - publico:      qualquer pessoa, mesmo sem sessão (visitante).
    - autenticado:  qualquer utilizador com sessão iniciada (qualquer perfil).
    - academico:    apenas professores, investigadores e administradores
                    (ex.: material científico ou de investigação restrito).
    """

    publico = "publico"
    autenticado = "autenticado"
    academico = "academico"


class Documento(Base):
    __tablename__ = "documentos"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(400), nullable=False, index=True)
    resumo: Mapped[Optional[str]] = mapped_column(String(5000), nullable=True)
    tipo: Mapped[TipoDocumento] = mapped_column(
        SAEnum(TipoDocumento, name="tipo_documento"), nullable=False, index=True
    )
    estado: Mapped[EstadoDocumento] = mapped_column(
        SAEnum(EstadoDocumento, name="estado_documento"),
        default=EstadoDocumento.publicado,
        nullable=False,
    )
    ano_publicacao: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    idioma: Mapped[Optional[str]] = mapped_column(String(40), default="Português")

    autor_id: Mapped[int] = mapped_column(
        ForeignKey("utilizadores.id", ondelete="CASCADE"), index=True
    )
    area_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("areas_cientificas.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Autor/origem REAL da obra (ex.: "Machado de Assis"), distinto do
    # utilizador da plataforma que a publicou (autor_id).
    autor_nome: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)

    # Género literário (só faz sentido na secção de Literatura): "Romance",
    # "Poesia", "Conto", "Teatro". Corresponde aos auxiliares de forma da CDU
    # (82-3 Romance, 82-1 Poesia, 82-32 Conto, 82-2 Teatro) e permite arrumar a
    # estante de Literatura por género, como numa biblioteca real.
    genero: Mapped[Optional[str]] = mapped_column(String(60), nullable=True, index=True)

    ficheiro_objecto: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ficheiro_tamanho: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # URL público para ler/descarregar a obra e imagem de capa.
    ficheiro_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    capa_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    uri_semantica: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    nivel_acesso: Mapped[NivelAcesso] = mapped_column(
        SAEnum(NivelAcesso, name="nivel_acesso"),
        default=NivelAcesso.publico,
        nullable=False,
    )

    num_downloads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    num_visualizacoes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relação N:1 — muitos documentos para um autor.
    autor: Mapped["Utilizador"] = relationship(back_populates="documentos")  # noqa: F821
