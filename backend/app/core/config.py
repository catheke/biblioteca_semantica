"""
config.py — Configuração central, carregada de variáveis de ambiente (.env).

Todas as definições ficam num objecto `settings` validado por pydantic-settings,
o que mantém o código igual em qualquer ambiente e falha cedo se um valor for
inválido.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Todas as definições da aplicação, validadas e tipadas."""

    # O pydantic-settings procura primeiro variáveis de ambiente; depois o .env.
    # `extra="ignore"` evita erros se houver variáveis extra no ambiente.
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Identidade da aplicação ---
    APP_ENV: str = "development"
    APP_NAME: str = "Semantic Academic Hub"
    APP_VERSION: str = "1.0.0"

    # --- Base de dados relacional ---
    # Valor por omissão usa SQLite em ficheiro local, para que a API ARRANQUE e
    # seja testável mesmo sem PostgreSQL/Docker. Em produção, DATABASE_URL aponta
    # para o PostgreSQL (ver .env / docker-compose).
    DATABASE_URL: str = "sqlite:///./basi_local.db"

    @field_validator("DATABASE_URL")
    @classmethod
    def _normalizar_database_url(cls, valor: str) -> str:
        """
        Alguns fornecedores (ex.: Render) entregam o URL do PostgreSQL no formato
        `postgres://...`. O SQLAlchemy com o driver psycopg precisa do prefixo
        `postgresql+psycopg://`. Esta conversão evita ter de editar variáveis à mão.
        """
        if valor.startswith("postgres://"):
            return "postgresql+psycopg://" + valor[len("postgres://"):]
        if valor.startswith("postgresql://"):
            return "postgresql+psycopg://" + valor[len("postgresql://"):]
        return valor

    # Quando True, a aplicação semeia a base de dados e carrega a ontologia no
    # Fuseki no arranque (idempotente). Útil em produção (Render), onde não há
    # passos manuais. Activado por variável de ambiente BOOTSTRAP_ON_STARTUP=1.
    BOOTSTRAP_ON_STARTUP: bool = False

    # --- Motor semântico (Fuseki) ---
    FUSEKI_QUERY_ENDPOINT: str = "http://localhost:3030/basi/query"
    FUSEKI_UPDATE_ENDPOINT: str = "http://localhost:3030/basi/update"
    FUSEKI_DATA_ENDPOINT: str = "http://localhost:3030/basi/data"

    # --- Armazenamento de objectos (MinIO) ---
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ROOT_USER: str = "minioadmin"
    MINIO_ROOT_PASSWORD: str = "minioadmin"
    MINIO_BUCKET: str = "basi-documentos"
    MINIO_SECURE: bool = False

    # --- Segurança / JWT ---
    JWT_SECRET_KEY: str = "dev-secret-troque-em-producao-com-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- CORS (origens autorizadas) ---
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Converte a string separada por vírgulas numa lista para o middleware."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Devolve uma instância única (cache) de Settings.

    Usar `lru_cache` garante que o .env é lido UMA só vez e que toda a aplicação
    partilha a mesma configuração — importante para performance e coerência.
    """
    return Settings()


# Instância global, conveniente para importar: `from app.core.config import settings`
settings = get_settings()
