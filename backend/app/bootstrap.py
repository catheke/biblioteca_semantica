"""
bootstrap.py — Preparação automática de dados no arranque (produção).

Em ambientes geridos (ex.: Render) não há passos manuais: a aplicação tem de
ficar funcional logo no primeiro arranque. Este módulo garante, de forma
IDEMPOTENTE, que:

    1. A base de dados relacional tem dados de demonstração (utilizadores, áreas,
       temas, documentos) — via app.seed_local.
    2. O grafo do Fuseki tem a ontologia e as instâncias carregadas — só se o
       Fuseki estiver acessível e ainda estiver vazio.

Tudo é tolerante a falhas: se uma etapa falhar (rede, Fuseki em baixo), regista
o erro e continua, para que a API arranque na mesma (a camada semântica recorre
ao grafo rdflib em memória).

Activado pela variável de ambiente BOOTSTRAP_ON_STARTUP=1.
"""
from __future__ import annotations

import logging
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger("basi.bootstrap")

_RAIZ = Path(__file__).resolve().parents[2]
_FICHEIROS_TTL = [
    _RAIZ / "ontology" / "basi.ttl",
    _RAIZ / "rdf" / "dados_exemplo.ttl",
    _RAIZ / "rdf" / "cdu_classificacao.ttl",
]


def _semear_base_dados() -> None:
    """Popula a BD relacional (idempotente: salta se já houver dados)."""
    try:
        from app import seed_local

        seed_local.executar()
    except Exception as erro:  # noqa: BLE001
        logger.warning("Bootstrap da base de dados falhou (continua): %s", erro)


def _semear_livros_em_falta() -> None:
    """Acrescenta livros novos do catálogo a uma base já povoada (idempotente)."""
    try:
        from app import seed_local

        seed_local.semear_livros_em_falta()
    except Exception as erro:  # noqa: BLE001
        logger.warning("Bootstrap de livros em falta falhou (continua): %s", erro)


def _semear_circulacao() -> None:
    """Popula a circulação (exemplares/empréstimos/reservas/multas), idempotente."""
    try:
        from app import seed_local

        seed_local.semear_circulacao()
    except Exception as erro:  # noqa: BLE001
        logger.warning("Bootstrap da circulação falhou (continua): %s", erro)


def _fuseki_vazio() -> bool | None:
    """
    Devolve True se o grafo do Fuseki estiver vazio, False se já tiver triplos,
    ou None se o Fuseki não estiver acessível.
    """
    consulta = "SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }"
    try:
        resposta = httpx.get(
            settings.FUSEKI_QUERY_ENDPOINT,
            params={"query": consulta},
            headers={"Accept": "application/sparql-results+json"},
            timeout=10.0,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        n = int(dados["results"]["bindings"][0]["n"]["value"])
        return n == 0
    except Exception as erro:  # noqa: BLE001
        logger.info("Fuseki não acessível no arranque (%s) — uso do grafo local.", erro)
        return None


def _carregar_fuseki() -> None:
    """Envia a ontologia + instâncias para o Fuseki (Graph Store Protocol)."""
    vazio = _fuseki_vazio()
    if vazio is None:
        return  # Fuseki indisponível; a API usa o grafo rdflib em memória.
    if not vazio:
        logger.info("Fuseki já tem dados — carregamento ignorado.")
        return

    for caminho in _FICHEIROS_TTL:
        if not caminho.exists():
            continue
        try:
            conteudo = caminho.read_bytes()
            resposta = httpx.post(
                settings.FUSEKI_DATA_ENDPOINT,
                params={"default": ""},
                content=conteudo,
                headers={"Content-Type": "text/turtle"},
                timeout=30.0,
            )
            resposta.raise_for_status()
            logger.info("Carregado para o Fuseki: %s", caminho.name)
        except Exception as erro:  # noqa: BLE001
            logger.warning("Falha ao carregar %s para o Fuseki: %s", caminho.name, erro)


def executar() -> None:
    """Corre o bootstrap completo (semear BD + carregar Fuseki)."""
    logger.info("Bootstrap de arranque iniciado.")
    _semear_base_dados()
    _semear_livros_em_falta()
    _semear_circulacao()
    _carregar_fuseki()
    logger.info("Bootstrap de arranque concluído.")
