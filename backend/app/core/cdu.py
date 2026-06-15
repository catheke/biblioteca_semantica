"""
cdu.py — Classificação Decimal Universal (CDU) aplicada à biblioteca.

A CDU é a norma de classificação usada nas bibliotecas de Angola e Portugal.
Divide todo o conhecimento em dez classes (0–9). Aqui guardamos apenas o
vocabulário de que a aplicação precisa para arrumar as obras em SECÇÕES (as
"estantes") e, dentro da Literatura, por GÉNERO — exactamente como numa
biblioteca física.

Este módulo é a ÚNICA fonte de verdade do mapeamento género → notação CDU,
partilhada pelo seed (popular a base) e pela API (montar as secções).
"""
from __future__ import annotations

from typing import Optional

# Classes CDU usadas como secções da biblioteca (código -> rótulo legível).
# Nota: a classe 4 deixou de existir na CDU desde 1961 (a Língua passou para a 8).
SECCOES_CDU: dict[str, str] = {
    "0": "Informática e Generalidades",
    "1": "Filosofia e Psicologia",
    "5": "Ciências Naturais e Matemática",
    "6": "Ciências Aplicadas e Medicina",
    "82": "Literatura",
}

# Géneros literários, na ordem em que devem aparecer na estante. Cada um
# corresponde a um "auxiliar de forma" da CDU dentro de 82 (Literatura).
GENEROS_LITERATURA: list[tuple[str, str]] = [
    ("Romance", "82-3"),   # ficção / prosa narrativa
    ("Conto", "82-32"),    # conto e novela
    ("Poesia", "82-1"),    # poesia / lírica
    ("Teatro", "82-2"),    # teatro / drama
]

# Atalho nome do género -> notação CDU (ex.: "Romance" -> "82-3").
NOTACAO_GENERO: dict[str, str] = {nome: codigo for nome, codigo in GENEROS_LITERATURA}

# Código CDU da secção de Literatura (raiz dos géneros).
CODIGO_LITERATURA = "82"


def notacao_do_genero(genero: Optional[str]) -> Optional[str]:
    """Devolve a notação CDU de um género (ex.: 'Poesia' -> '82-1')."""
    if not genero:
        return None
    return NOTACAO_GENERO.get(genero)
