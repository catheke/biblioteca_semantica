"""
validar_ontologia.py — Valida sintacticamente a ontologia e os dados RDF.

Usa a rdflib para carregar os ficheiros Turtle e contar os triplos. Se houver um
erro de sintaxe, a rdflib levanta uma excepção (falha cedo). Útil em CI.

USO (com a rdflib instalada):  python scripts/validar_ontologia.py
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    from rdflib import Graph
except ImportError:
    print("rdflib não está instalada. Instale com: pip install rdflib")
    sys.exit(1)

RAIZ = Path(__file__).resolve().parent.parent
FICHEIROS = [RAIZ / "ontology" / "basi.ttl", RAIZ / "rdf" / "dados_exemplo.ttl"]


def main() -> int:
    grafo = Graph()
    total = 0
    for ficheiro in FICHEIROS:
        g = Graph()
        g.parse(ficheiro, format="turtle")
        print(f"OK  {ficheiro.name}: {len(g)} triplos")
        grafo += g
        total += len(g)
    print(f"--- Total combinado: {len(grafo)} triplos (soma {total}) ---")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
