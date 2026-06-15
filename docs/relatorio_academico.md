# Relatório Académico — Semantic Academic Hub (BASI)

> **Biblioteca Académica Semântica Inteligente**
> Disciplina de **Web Semântica**
> **Grupo:** Pedro Calenga (2022110222) · Filipe Tchivela (2022142100) · Adriano De Júlio (2022179366)

---

## Índice

1. Introdução
2. Problema e motivação
3. Objectivos
4. Fundamentação teórica (Web Semântica)
5. Análise de requisitos
6. Arquitectura do sistema
7. Modelação de dados (relacional)
8. Modelação do conhecimento (ontologia OWL)
9. Consultas SPARQL e inferência
10. Implementação do backend
11. Implementação do frontend
12. Segurança
13. Optimização e escalabilidade
14. Testes
15. Conclusão e trabalho futuro

---

## 1. Introdução

Este relatório descreve a concepção e implementação do **Semantic Academic Hub
(BASI)**, uma rede académica que aplica tecnologias de **Web Semântica** para
ligar obras, autores, áreas científicas e temas de investigação. O objectivo é
demonstrar, de forma realista e funcional, como uma ontologia OWL e o motor de
inferência do **Apache Jena Fuseki** transformam uma biblioteca digital comum
numa plataforma que *compreende relações* entre conceitos.

## 2. Problema e motivação

As bibliotecas académicas acumulam grandes volumes de informação, mas têm
dificuldade em **revelar relações** entre os seus conteúdos. Uma pesquisa textual
clássica por *"Inteligência Artificial"* só devolve documentos que contêm
literalmente essas palavras — ignora trabalhos sobre *Machine Learning*, *Deep
Learning* ou *Redes Neurais*, que são subtemas directos.

A motivação do projecto é eliminar esta limitação: representar o conhecimento
num **grafo** onde as relações são explícitas e onde o motor pode **inferir**
factos não escritos directamente (ex.: se *Deep Learning* é subtema de *Machine
Learning* e este é subtema de *IA*, então um documento de *Deep Learning* também
é relevante para uma pesquisa de *IA*).

## 3. Objectivos

**Geral:** construir uma rede académica semântica, profissional e escalável.

**Específicos:**
- Modelar o domínio académico numa ontologia OWL (TBox) com instâncias RDF (ABox).
- Implementar pesquisa semântica com inferência via SPARQL (caminhos transitivos).
- Oferecer recomendações inteligentes baseadas no grafo de conhecimento.
- Disponibilizar autenticação segura (JWT + RBAC) e gestão de documentos.
- Orquestrar tudo com Docker (persistência poliglota).

## 4. Fundamentação teórica (Web Semântica)

- **RDF (Resource Description Framework):** modelo de triplos `sujeito–predicado–objecto`.
- **RDFS / OWL:** linguagens para descrever **classes**, **propriedades** e
  **restrições**, permitindo **inferência**.
- **Propriedades notáveis usadas no projecto:**
  - *Transitiva* (`eSubtemaDe`): se A⊑B e B⊑C então A⊑C — base da expansão de temas.
  - *Simétrica* (`obraRelacionada`): se A↔B então B↔A.
  - *Inversa* (`temAutor` / `ehAutorDe`): navegação nos dois sentidos.
- **SPARQL:** linguagem de consulta sobre grafos RDF; suporta **caminhos de
  propriedade** (`eSubtemaDe*` = zero ou mais saltos).
- **IRI:** identificador global de cada recurso — a "ponte" entre o mundo
  relacional (PostgreSQL) e o semântico (Fuseki) através do campo `uri_semantica`.

## 5. Análise de requisitos

**Actores:** Visitante, Estudante, Professor, Investigador, Administrador.

**Requisitos funcionais (resumo):**
- RF1 Pesquisar conteúdos (textual e semântica).
- RF2 Ver detalhe de documento.
- RF3 Registo / início de sessão.
- RF4 Guardar favoritos e seguir autores.
- RF5 Receber recomendações.
- RF6 Publicar documentos (professor/investigador).
- RF7 Criar linhas de investigação.
- RF8 Administração: gerir utilizadores, moderar, gerir ontologia.
- RF9 Endpoint SPARQL (apenas leitura).

**Requisitos não-funcionais:** segurança (JWT/RBAC/bcrypt), escalabilidade
(backend sem estado), desempenho (índices, paginação, cache), portabilidade
(Docker). Os casos de uso estão em [`uml/casos_de_uso.puml`](uml/casos_de_uso.puml).

## 6. Arquitectura do sistema

Arquitectura em **camadas** com **persistência poliglota** (ver
[`arquitectura.md`](arquitectura.md) e [`uml/componentes.puml`](uml/componentes.puml)):

```
Frontend (Next.js) → API (FastAPI) → Services → Repositories → Models (ORM)
                                         ↘ SemanticService → Fuseki (SPARQL/OWL)
PostgreSQL (identidade/metadados) · Fuseki (conhecimento) · MinIO (ficheiros)
```

Cada documento existe nos dois mundos, ligado pelo `uri_semantica`.

## 7. Modelação de dados (relacional)

O esquema PostgreSQL ([`database/schema.sql`](../database/schema.sql)) inclui:
`utilizadores`, `areas_cientificas`, `temas` (auto-referência `tema_pai_id`),
`palavras_chave`, `universidades`, `departamentos`, `cursos`, `documentos`,
tabelas de associação (`documento_temas`, `coautores`, `favoritos`,
`seguidores`) e `tokens_refresh`. Destaques:
- **Índice GIN full-text** em português para pesquisa textual.
- **Triggers** de `updated_at` e **view** `documentos_detalhados`.
- O diagrama de classes está em [`uml/classes.puml`](uml/classes.puml).

## 8. Modelação do conhecimento (ontologia OWL)

A ontologia ([`ontology/basi.ttl`](../ontology/basi.ttl)) define a hierarquia
`Pessoa → Autor → {Professor, Estudante, Investigador}`, as subclasses de
`Documento`, e as classes `AreaCientifica`, `Tema`, `PalavraChave`. Inclui
propriedades de objecto (transitivas, simétricas, inversas) e **restrições OWL**
(ex.: `DocumentoDeIA` como `equivalentClass`, `minCardinality` de autores). As
instâncias de exemplo estão em [`rdf/dados_exemplo.ttl`](../rdf/dados_exemplo.ttl).

## 9. Consultas SPARQL e inferência

O ficheiro [`sparql/consultas.sparql`](../sparql/consultas.sparql) reúne **22
consultas** comentadas. A consulta-chave usa caminho transitivo:

```sparql
SELECT DISTINCT ?titulo WHERE {
  ?temaRaiz basi:nome "Inteligência Artificial" .
  ?tema basi:eSubtemaDe* ?temaRaiz .
  ?doc basi:temTema ?tema ; basi:titulo ?titulo .
}
```

O `*` faz o motor percorrer toda a sub-árvore de temas, devolvendo documentos
relacionados mesmo sem a palavra "IA".

## 10. Implementação do backend

FastAPI organizado em camadas (`api/`, `services/`, `repositories/`, `models/`,
`schemas/`). O `SemanticService` constrói e executa SPARQL contra o Fuseki, com
**degradação graciosa** (devolve lista vazia se o Fuseki estiver indisponível,
mantendo a API de pé). O `RecommendationService` combina sinais de conteúdo e de
grafo. A documentação OpenAPI é gerada automaticamente em `/docs`.

## 11. Implementação do frontend

Next.js 14 (App Router) + TypeScript + TailwindCSS. Um cliente HTTP central
([`frontend/src/lib/api.ts`](../frontend/src/lib/api.ts)) gere tokens e chamadas;
o contexto de autenticação ([`auth.tsx`](../frontend/src/lib/auth.tsx)) protege
rotas. A página de destaque é `/pesquisa-semantica`, que mostra os **termos
expandidos** para tornar a inferência transparente ao utilizador.

## 12. Segurança

- **Palavras-passe:** apenas hashes **bcrypt** (com sal).
- **Autenticação JWT** sem estado: *access* (30 min) + *refresh* (7 dias),
  com tabela `tokens_refresh` para revogação.
- **Autorização (RBAC):** dependência `exigir_perfis(...)` protege rotas.
- **Endpoint SPARQL** bloqueia escrita (INSERT/DELETE/DROP...).
- **CORS** restrito às origens configuradas.

## 13. Optimização e escalabilidade

Cache (`lru_cache`; Redis recomendado para respostas SPARQL frequentes),
paginação e *lazy loading*, índices relacionais e full-text, optimização de
caminhos transitivos, backend **sem estado** (escala horizontal), réplicas de
leitura no Postgres, *backups* (`pg_dump`, TDB2, MinIO) e *healthchecks*. Detalhe
na secção final de [`arquitectura.md`](arquitectura.md).

## 14. Testes

Testes `pytest` ([`backend/tests/test_api.py`](../backend/tests/test_api.py))
sobre SQLite isolado, cobrindo *health*, registo, login, `/me`, email duplicado e
publicação de documento. Não exigem PostgreSQL nem Fuseki. A ontologia é validada
por [`scripts/validar_ontologia.py`](../scripts/validar_ontologia.py).

## 15. Conclusão e trabalho futuro

O BASI demonstra que a Web Semântica acrescenta valor real a uma biblioteca
académica: a pesquisa deixa de ser por palavras e passa a ser por **significado**.
A arquitectura poliglota separa identidade, conhecimento e ficheiros, mantendo o
sistema testável e escalável.

**Trabalho futuro:** cache Redis para inferência, importação automática de
metadados (DOI/BibTeX), recomendações com *embeddings*, e materialização de
inferências frequentes no Fuseki para reduzir latência.
