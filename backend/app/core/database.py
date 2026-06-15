"""
database.py — Ligação à base de dados relacional via SQLAlchemy 2.0.

Define o engine, a fábrica de sessões e a base declarativa dos modelos. A
dependência `get_db` injecta uma sessão por pedido HTTP e garante o seu fecho,
mesmo em caso de erro.
"""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings

# Para SQLite (modo local) é preciso desactivar a verificação de thread única.
# Para PostgreSQL este argumento é ignorado.
connect_args = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

# `pool_pre_ping=True` testa a ligação antes de a usar, evitando erros com
# ligações que "morreram" (timeout do servidor de BD).
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

# Fábrica de sessões. `autoflush=False` dá-nos controlo explícito sobre quando
# os dados são enviados para a BD.
SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True
)


class Base(DeclarativeBase):
    """Classe base para todos os modelos ORM (tabelas)."""

    pass


def get_db() -> Generator[Session, None, None]:
    """
    Dependência FastAPI: fornece uma sessão de BD e fecha-a no fim do pedido.

    Uso:
        @router.get("/...")
        def endpoint(db: Session = Depends(get_db)): ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Cria as tabelas a partir dos modelos ORM (apenas as que ainda não existem).

    Em PostgreSQL preferimos o database/schema.sql (mais rico: índices, triggers,
    tipos ENUM). Em SQLite local usamos isto para arrancar sem dependências.
    """
    # Importa os modelos para que fiquem registados no metadata da Base.
    from app import models  # noqa: F401  (import com efeito de registo)

    Base.metadata.create_all(bind=engine)
