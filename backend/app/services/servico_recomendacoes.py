"""
servico_recomendacoes.py — Recomendação baseada em conteúdo e no grafo.

A partir dos favoritos do utilizador, recolhe os respectivos temas, expande-os
pelos subtemas (eSubtemaDe) e procura outros documentos sobre esses temas,
pontuando-os pelo número de temas em comum. As relações entre temas vivem na
ontologia, não no código.
"""
from __future__ import annotations

from collections import Counter

from app.services.servico_semantico import servico_semantico
from app.schemas.search import RecomendacaoItem


class ServicoRecomendacoes:
    def __init__(self) -> None:
        self.semantic = servico_semantico

    def recomendar(self, uri_utilizador: str, limite: int = 10) -> list[RecomendacaoItem]:
        linhas = self.semantic.recomendar_para_utilizador(uri_utilizador)

        # Pontuação: conta quantas vezes cada documento aparece (temas em comum).
        pontuacao: Counter[str] = Counter()
        titulos: dict[str, str] = {}
        temas_por_doc: dict[str, set[str]] = {}
        for linha in linhas:
            uri = linha.get("doc")
            if not uri:
                continue
            pontuacao[uri] += 1
            titulos[uri] = linha.get("titulo", "(sem título)")
            temas_por_doc.setdefault(uri, set()).add(linha.get("nomeTema", ""))

        recomendacoes: list[RecomendacaoItem] = []
        for uri, _ in pontuacao.most_common(limite):
            temas = ", ".join(sorted(t for t in temas_por_doc[uri] if t))
            recomendacoes.append(
                RecomendacaoItem(
                    uri=uri,
                    titulo=titulos[uri],
                    motivo=f"Relacionado com os seus interesses em: {temas}.",
                )
            )
        return recomendacoes


servico_recomendacoes = ServicoRecomendacoes()
