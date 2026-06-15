"""
servico_semantico.py — Ponte entre a API e o grafo RDF (Apache Jena Fuseki).

A pesquisa semântica corre consultas SPARQL sobre o grafo: dado um termo,
expande-o pelos subtemas (propriedade transitiva eSubtemaDe) e devolve os
documentos ligados a qualquer um desses temas.

Se o Fuseki não estiver acessível, recorre a um grafo rdflib em memória, pelo
que a API continua a responder mesmo sem o serviço externo.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional

from SPARQLWrapper import SPARQLWrapper, JSON, POST

from app.core.config import settings

logger = logging.getLogger("basi.semantic")

# Raiz do repositório (…/semantic-academic-hub), a partir deste ficheiro:
# backend/app/services/servico_semantico.py -> sobe 4 níveis.
_RAIZ = Path(__file__).resolve().parents[3]
# Ficheiro gerido pela aplicação: recebe os triplos dos documentos que o admin
# adiciona/elimina. Fica SEPARADO do dados_exemplo.ttl (curado, com comentários
# didácticos) para que a regravação automática não destrua esse material.
_TTL_DINAMICO = _RAIZ / "rdf" / "dados_dinamicos.ttl"
_FICHEIROS_TTL = [
    _RAIZ / "ontology" / "basi.ttl",
    _RAIZ / "rdf" / "dados_exemplo.ttl",
    # Secções da biblioteca (CDU) e géneros literários, em SKOS.
    _RAIZ / "rdf" / "cdu_classificacao.ttl",
    _TTL_DINAMICO,
]

# IRIs base e mapeamento Tipo de documento (SQL) -> Classe da ontologia (OWL).
_NS_BASI = "http://basi.ao/ontologia#"
_NS_REC = "http://basi.ao/recurso/"
_CLASSE_POR_TIPO = {
    "livro": "Livro",
    "artigo": "Artigo",
    "tese": "Tese",
    "monografia": "Monografia",
    "manual": "Manual",
    "apresentacao": "Apresentacao",
    "material_didactico": "MaterialDidactico",
}


def _slug_tema(nome: str) -> str:
    """'Inteligência Artificial' -> 'InteligenciaArtificial' (para mintar IRIs)."""
    import re
    import unicodedata

    base = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", " ", base).title().replace(" ", "")
    return base or "Tema"


@lru_cache(maxsize=1)
def _grafo_local():
    """
    Carrega a ontologia (TBox) + instâncias (ABox) num grafo rdflib em memória.

    Serve de motor SPARQL EM PROCESSO quando o Fuseki não está disponível
    (ex.: execução local sem Docker/Java). O rdflib suporta caminhos de
    propriedade (`eSubtemaDe*`), pelo que a INFERÊNCIA transitiva da pesquisa
    semântica funciona na mesma. Carregado uma única vez (cache).
    """
    from rdflib import Graph

    g = Graph()
    for caminho in _FICHEIROS_TTL:
        if caminho.exists():
            g.parse(str(caminho), format="turtle")
    logger.info("Grafo semântico local carregado: %d triplos", len(g))
    return g


@lru_cache(maxsize=1)
def _grafo_dinamico():
    """
    Grafo SÓ com os triplos geridos pela aplicação (rdf/dados_dinamicos.ttl).

    É este que gravamos em disco quando o admin adiciona/elimina documentos —
    mantém o `dados_exemplo.ttl` curado intacto. As consultas usam o grafo
    completo (`_grafo_local`), que inclui este ficheiro.
    """
    from rdflib import Graph

    g = Graph()
    g.bind("basi", _NS_BASI)
    g.bind("rec", _NS_REC)
    if _TTL_DINAMICO.exists():
        g.parse(str(_TTL_DINAMICO), format="turtle")
    return g

# Prefixos reutilizados em todas as consultas.
PREFIXOS = """
PREFIX basi: <http://basi.ao/ontologia#>
PREFIX rec:  <http://basi.ao/recurso/>
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""


class ServicoSemantico:
    def __init__(self) -> None:
        self.query_endpoint = settings.FUSEKI_QUERY_ENDPOINT
        self.update_endpoint = settings.FUSEKI_UPDATE_ENDPOINT

    # Execução genérica de SPARQL
    def executar_select(self, query: str) -> list[dict]:
        """
        Executa uma consulta SELECT e devolve uma lista de dicionários simples
        (cada linha -> {variável: valor}).
        """
        try:
            sparql = SPARQLWrapper(self.query_endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(10)
            resposta = sparql.query().convert()
        except Exception as exc:  # ligação falhou, timeout, sintaxe...
            logger.warning("Fuseki indisponível (%s) — a usar grafo local.", exc)
            return self._executar_select_local(query)

        linhas: list[dict] = []
        for binding in resposta.get("results", {}).get("bindings", []):
            linhas.append({chave: campo["value"] for chave, campo in binding.items()})
        return linhas

    def _executar_select_local(self, query: str) -> list[dict]:
        """Executa a mesma consulta SELECT contra o grafo rdflib em memória."""
        try:
            resultado = _grafo_local().query(query)
        except Exception as exc:
            logger.warning("Falha na consulta ao grafo local: %s", exc)
            return []
        variaveis = [str(v) for v in resultado.vars or []]
        linhas: list[dict] = []
        for linha in resultado:
            registo = {}
            for var in variaveis:
                valor = linha[var]
                if valor is not None:
                    registo[var] = str(valor)
            linhas.append(registo)
        return linhas

    # Pesquisa semântica (expansão por subtemas)
    def expandir_termo(self, termo: str) -> list[str]:
        """
        Dado o nome de um tema, devolve esse tema MAIS todos os seus subtemas
        (directos e indirectos), graças ao caminho transitivo `^basi:eSubtemaDe*`.

        Esta é a operação de INFERÊNCIA que distingue pesquisa semântica de
        pesquisa textual.
        """
        # Escapamos aspas para evitar quebrar a consulta (defesa básica).
        termo_seguro = termo.replace('"', '\\"')
        query = f"""{PREFIXOS}
        SELECT DISTINCT ?nomeSub WHERE {{
            ?temaRaiz basi:nome "{termo_seguro}" .
            ?sub basi:eSubtemaDe* ?temaRaiz ;
                 basi:nome ?nomeSub .
        }}
        """
        linhas = self.executar_select(query)
        nomes = [linha["nomeSub"] for linha in linhas if "nomeSub" in linha]
        # Garante que o próprio termo entra mesmo que não haja subtemas.
        if termo not in nomes:
            nomes.insert(0, termo)
        return nomes

    def pesquisar_documentos_por_tema(self, termo: str) -> list[dict]:
        """
        Devolve documentos cujo tema é o termo dado OU um subtema deste.

        Cada resultado inclui o `nomeTema` que o fez aparecer — usado para
        explicar ao utilizador PORQUÊ o resultado é relevante.
        """
        termo_seguro = termo.replace('"', '\\"')
        query = f"""{PREFIXOS}
        SELECT DISTINCT ?doc ?titulo ?nomeTema WHERE {{
            ?temaRaiz basi:nome "{termo_seguro}" .
            ?tema basi:eSubtemaDe* ?temaRaiz ;
                  basi:nome ?nomeTema .
            ?doc basi:temTema ?tema ;
                 basi:titulo ?titulo .
        }}
        ORDER BY ?titulo
        """
        return self.executar_select(query)

    # Recomendações (documentos relacionados com os favoritos de um utilizador)
    def recomendar_para_utilizador(self, uri_utilizador: str) -> list[dict]:
        """
        Recomenda documentos relacionados, por TEMA, com os favoritos do
        utilizador — excluindo os que ele já marcou.

        A relação não é um simples "mesmo tema exacto": usamos o caminho
        TRANSITIVO `eSubtemaDe*` para que um favorito sobre "Inteligência
        Artificial" passe a recomendar também obras sobre os seus subtemas
        (Deep Learning, Visão Computacional, Ciência de Dados...). É a mesma
        inferência da pesquisa semântica, aplicada à recomendação — é isto que
        a torna "inteligente" em vez de um mero emparelhamento de etiquetas.
        """
        query = f"""{PREFIXOS}
        SELECT DISTINCT ?doc ?titulo ?nomeTema WHERE {{
            <{uri_utilizador}> basi:temFavorito ?fav .
            ?fav  basi:temTema ?temaFav .
            ?tema basi:eSubtemaDe* ?temaFav ;
                  basi:nome ?nomeTema .
            ?doc  basi:temTema ?tema ;
                  basi:titulo ?titulo .
            FILTER NOT EXISTS {{ <{uri_utilizador}> basi:temFavorito ?doc }}
        }}
        """
        return self.executar_select(query)

    # Sincronização SQL -> RDF (escrita de triplos quando o catálogo muda)
    def _sujeito_por_nome(self, grafo, nome: str, classe=None):
        """Procura no grafo um indivíduo com basi:nome == `nome` (e tipo opcional)."""
        from rdflib import RDF, URIRef

        nome_pred = URIRef(_NS_BASI + "nome")
        tipo_uri = URIRef(_NS_BASI + classe) if classe else None
        for sujeito, _, valor in grafo.triples((None, nome_pred, None)):
            if str(valor) == nome and (
                tipo_uri is None or (sujeito, RDF.type, tipo_uri) in grafo
            ):
                return sujeito
        return None

    def sincronizar_documento(
        self,
        *,
        uri: str,
        titulo: str,
        tipo: str,
        resumo: Optional[str] = None,
        ano: Optional[int] = None,
        autor_nome: Optional[str] = None,
        area_nome: Optional[str] = None,
        tema_nome: Optional[str] = None,
        genero_nome: Optional[str] = None,
        num_downloads: int = 0,
    ) -> None:
        """
        Escreve (ou actualiza) os triplos de um documento no grafo RDF e
        persiste-os em rdf/dados_dinamicos.ttl. É o "PASSO SEMÂNTICO" que liga o
        que o admin adiciona no catálogo (SQL) ao grafo onde a pesquisa procura.
        """
        from rdflib import Literal, RDF, URIRef
        from rdflib.namespace import XSD

        def P(nome):  # noqa: N802 — atalho para uma propriedade basi:
            return URIRef(_NS_BASI + nome)

        doc = URIRef(uri)
        classe = URIRef(_NS_BASI + _CLASSE_POR_TIPO.get(tipo, "Documento"))

        # Resolvemos autor/área/tema contra o grafo COMPLETO (que tem a ontologia
        # e o dados_exemplo.ttl), para reutilizar os IRIs já existentes em vez de
        # criar duplicados. O tema só é "novo" se não existir em lado nenhum.
        completo = _grafo_local()
        autor = self._sujeito_por_nome(completo, autor_nome) if autor_nome else None
        area = (
            self._sujeito_por_nome(completo, area_nome, "AreaCientifica")
            if area_nome
            else None
        )
        tema = None
        tema_novo = False
        if tema_nome:
            tema = self._sujeito_por_nome(completo, tema_nome, "Tema")
            if tema is None:
                tema = URIRef(_NS_BASI + "Tema_" + _slug_tema(tema_nome))
                tema_novo = True
        # Género literário: resolve o conceito SKOS já declarado em
        # cdu_classificacao.ttl (não criamos géneros novos — são um conjunto fixo).
        genero = (
            self._sujeito_por_nome(completo, genero_nome, "Genero")
            if genero_nome
            else None
        )

        # Aplicamos a MESMA mutação ao grafo de consulta (em memória) e ao grafo
        # dinâmico (que vai para disco), para que a pesquisa reflicta já a mudança.
        for grafo in (completo, _grafo_dinamico()):
            for triplo in list(grafo.triples((doc, None, None))):
                grafo.remove(triplo)  # idempotência: limpa versão anterior

            grafo.add((doc, RDF.type, classe))
            grafo.add((doc, P("titulo"), Literal(titulo)))
            if resumo:
                grafo.add((doc, P("resumo"), Literal(resumo)))
            if ano:
                grafo.add((doc, P("anoPublicacao"), Literal(str(ano), datatype=XSD.gYear)))
            grafo.add((doc, P("numDownloads"), Literal(int(num_downloads), datatype=XSD.integer)))
            if autor is not None:
                grafo.add((doc, P("temAutor"), autor))
            if area is not None:
                grafo.add((doc, P("pertenceAArea"), area))
            if genero is not None:
                grafo.add((doc, P("temGenero"), genero))
            if tema is not None:
                if tema_novo:
                    # Tema inédito: declara o indivíduo (a inferência passa a contá-lo).
                    grafo.add((tema, RDF.type, P("Tema")))
                    grafo.add((tema, P("nome"), Literal(tema_nome)))
                grafo.add((doc, P("temTema"), tema))

        self._gravar_dinamico()

    def remover_documento(self, uri: str) -> None:
        """Remove do grafo (memória + ficheiro) todos os triplos de um documento."""
        from rdflib import URIRef

        doc = URIRef(uri)
        for grafo in (_grafo_local(), _grafo_dinamico()):
            for triplo in list(grafo.triples((doc, None, None))):
                grafo.remove(triplo)
            for triplo in list(grafo.triples((None, None, doc))):
                grafo.remove(triplo)  # ex.: favoritos/citações que apontem para ele
        self._gravar_dinamico()

    def _gravar_dinamico(self) -> None:
        """Persiste o grafo dinâmico em rdf/dados_dinamicos.ttl (Turtle)."""
        try:
            _TTL_DINAMICO.parent.mkdir(parents=True, exist_ok=True)
            _grafo_dinamico().serialize(destination=str(_TTL_DINAMICO), format="turtle")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Não foi possível gravar %s: %s", _TTL_DINAMICO.name, exc)


# Instância partilhada (sem estado interno mutável -> seguro como singleton).
servico_semantico = ServicoSemantico()
