# Semantic Academic Hub (BASI)

> **Biblioteca Académica Semântica Inteligente** — uma rede académica baseada em
> **Web Semântica** que *compreende relações* entre obras, autores, áreas e temas
> de investigação.
>
> Projecto da disciplina de **Web Semântica**.
> **Grupo:** Adriano Júlio Sigu · Filipe Tchivela Sigu · Pedro Mendes Sigu.

---

## Índice

1. [O problema e a solução](#1-o-problema-e-a-solução)
2. [Diferencial: pesquisa que compreende](#2-diferencial-pesquisa-que-compreende)
3. [Arquitectura](#3-arquitectura)
4. [Tecnologias](#4-tecnologias)
5. [Estrutura do projecto](#5-estrutura-do-projecto)
6. [Instalação e execução](#6-instalação-e-execução)
   - [Opção A — Tudo com Docker (recomendado)](#opção-a--tudo-com-docker-recomendado)
   - [Opção B — Execução local (sem Docker)](#opção-b--execução-local-sem-docker)
7. [Carregar a ontologia no Fuseki](#7-carregar-a-ontologia-no-fuseki)
8. [Utilizadores de demonstração](#8-utilizadores-de-demonstração)
9. [Testes](#9-testes)
10. [Documentação da API](#10-documentação-da-api)
11. [Deploy](#11-deploy)
12. [Mapa dos 16 passos do enunciado](#12-mapa-dos-16-passos-do-enunciado)

---

## 1. O problema e a solução

**Problema:** *as bibliotecas possuem grandes volumes de informação e dificuldades
na descoberta de relações entre obras, autores, áreas científicas e temas de
investigação.*

**Solução:** uma plataforma onde professores e investigadores publicam documentos
(livros, artigos, teses, monografias, manuais, apresentações, materiais
didácticos) e onde estudantes pesquisam, guardam favoritos, seguem autores e
recebem **recomendações inteligentes**. Por baixo, um **grafo de conhecimento**
(ontologia OWL no Apache Jena Fuseki) liga todos os conceitos e permite
**inferência**.

## 2. Diferencial: pesquisa que compreende

Numa pesquisa textual, procurar *"Inteligência Artificial"* só encontra
documentos que contêm essas palavras. Aqui é diferente:

```
Pesquisa: "Inteligência Artificial"
   │  a ontologia declara (propriedade transitiva eSubtemaDe):
   ▼
Machine Learning → Deep Learning, Redes Neurais
Ciência de Dados
Visão Computacional
   │
   ▼
Resultado: documentos de TODOS estes temas, mesmo sem a palavra "IA".
```

Isto é conseguido com a consulta SPARQL (caminho de propriedade transitivo):

```sparql
SELECT DISTINCT ?titulo WHERE {
  ?temaRaiz basi:nome "Inteligência Artificial" .
  ?tema basi:eSubtemaDe* ?temaRaiz .     # * = zero ou mais saltos
  ?doc basi:temTema ?tema ; basi:titulo ?titulo .
}
```

## 3. Arquitectura

**Persistência poliglota** — cada tipo de dado no motor mais adequado:

```
                         ┌─────────────────────────┐
                         │   Frontend (Next.js)     │  :3000
                         │   React + TypeScript     │
                         └────────────┬─────────────┘
                                      │ HTTP/JSON (REST)
                                      ▼
                         ┌─────────────────────────┐
                         │   Backend (FastAPI)      │  :8000
                         │   auth · CRUD · semântica│
                         └───┬───────────┬───────┬──┘
            dados            │           │       │     ficheiros
         transaccionais      ▼           ▼       ▼     (PDFs)
                   ┌──────────────┐ ┌──────────┐ ┌──────────┐
                   │ PostgreSQL   │ │  Fuseki  │ │  MinIO   │
                   │  :5432       │ │  :3030   │ │  :9000   │
                   │ contas/docs  │ │ RDF/OWL  │ │  S3      │
                   └──────────────┘ └──────────┘ └──────────┘
```

- **Fluxo de dados:** o frontend chama a API REST; a API lê/escreve no PostgreSQL
  (identidade, metadados) e no MinIO (ficheiros).
- **Fluxo semântico:** para pesquisa inteligente e recomendações, a API traduz o
  pedido em **SPARQL** e consulta o **Fuseki**, que aplica **inferência** sobre a
  ontologia. Cada documento SQL tem um `uri_semantica` que o liga ao recurso RDF.

Diagramas UML detalhados (PlantUML) em [`docs/uml/`](docs/uml). Notas de
arquitectura em [`docs/arquitectura.md`](docs/arquitectura.md).

## 4. Tecnologias

| Camada | Tecnologias |
|---|---|
| Frontend | Next.js 14, React 18, TypeScript, TailwindCSS |
| Backend | Python, FastAPI, SQLAlchemy 2, Pydantic v2 |
| BD relacional | PostgreSQL 16 |
| Web Semântica | RDF, RDFS, OWL, SPARQL |
| Motor semântico | Apache Jena Fuseki |
| Modelação | Protégé (ontologia) + PlantUML (UML) |
| Armazenamento | MinIO (compatível S3) |
| Autenticação | JWT (access + refresh), bcrypt |
| Containerização | Docker, docker-compose |
| Documentação | Swagger / OpenAPI (automática) |

## 5. Estrutura do projecto

```
semantic-academic-hub/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── core/            # config, base de dados, segurança, dependências
│   │   ├── models/          # modelos ORM (tabelas)
│   │   ├── schemas/         # contratos Pydantic (entrada/saída)
│   │   ├── repositories/    # acesso a dados (padrão Repository)
│   │   ├── services/        # regras de negócio + motor semântico
│   │   ├── api/v1/          # routers (controllers HTTP)
│   │   ├── main.py          # aplicação FastAPI
│   │   └── seed_local.py    # dados de demonstração (modo local)
│   ├── tests/               # testes pytest
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                # Aplicação Next.js
│   └── src/
│       ├── app/             # páginas (App Router)
│       ├── components/      # componentes reutilizáveis
│       ├── lib/             # cliente API + contexto de auth
│       └── types/           # tipos TypeScript
├── ontology/basi.ttl        # ONTOLOGIA OWL (TBox)
├── rdf/dados_exemplo.ttl    # instâncias RDF (ABox)
├── sparql/consultas.sparql  # 22 consultas SPARQL explicadas
├── database/                # schema.sql + seed.sql (PostgreSQL)
├── docs/                    # arquitectura + UML + relatório
├── scripts/                 # carregar ontologia, validar, etc.
├── docker-compose.yml       # orquestra todos os serviços
└── .env.example
```

## 6. Instalação e execução

### Opção A — Tudo com Docker (recomendado)

Pré-requisitos: **Docker** e **Docker Compose**.

```bash
# 1. Copiar e ajustar variáveis de ambiente
cp .env.example .env

# 2. Levantar todos os serviços (PostgreSQL, Fuseki, MinIO, backend, frontend)
docker compose up --build

# 3. Carregar a ontologia e os dados no Fuseki (noutro terminal)
./scripts/carregar_ontologia.sh
```

Aceda a:
- Frontend: <http://localhost:3000>
- API + Swagger: <http://localhost:8000/docs>
- Fuseki: <http://localhost:3030>
- MinIO (consola): <http://localhost:9001>

### Opção B — Execução local (sem Docker)

Útil para desenvolver. A API arranca com **SQLite** automaticamente (não precisa
de PostgreSQL) — a pesquisa semântica precisa do Fuseki para devolver resultados.

**Backend**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed_local          # cria dados de demonstração
uvicorn app.main:app --reload     # API em http://localhost:8000
```

**Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev                        # http://localhost:3000
```

## 7. Carregar a ontologia no Fuseki

```bash
# Com o Fuseki a correr (Docker), enviar TBox + ABox:
./scripts/carregar_ontologia.sh

# Validar os ficheiros Turtle localmente (sintaxe + contagem de triplos):
python scripts/validar_ontologia.py
```

## 8. Utilizadores de demonstração

Todos com a palavra-passe **`password123`**:

| Email | Perfil |
|---|---|
| `admin@basi.ao` | Administrador |
| `adriano@basi.ao` | Professor |
| `filipe@basi.ao` | Professor |
| `pedro@basi.ao` | Investigador |
| `maria@basi.ao` | Estudante |

## 9. Testes

```bash
cd backend
source .venv/bin/activate
pytest -q
```

Os testes usam SQLite isolado e **não precisam** de PostgreSQL nem Fuseki.

## 10. Documentação da API

Gerada automaticamente pelo FastAPI a partir do código:
- **Swagger UI:** <http://localhost:8000/docs>
- **ReDoc:** <http://localhost:8000/redoc>
- **OpenAPI JSON:** <http://localhost:8000/openapi.json>

Principais grupos de endpoints: `auth`, `users`/`professors`, `documents`/`books`/
`articles`/`thesis`, `search`, `semantic-search`, `recommendations`, `sparql`.

## 11. Deploy

- **Imagens:** `docker compose build` produz imagens de backend e frontend
  (frontend em modo `standalone`, mínima).
- **Produção:** definir `.env` com `APP_ENV=production`, `JWT_SECRET_KEY` forte
  (`openssl rand -hex 32`), `MINIO_SECURE=true` atrás de HTTPS, e correr o backend
  com vários *workers* (`uvicorn ... --workers 4`) atrás de um *reverse proxy*
  (Nginx/Traefik).
- **Persistência:** os volumes `postgres_data`, `fuseki_data` e `minio_data`
  guardam os dados entre reinícios.

## 12. Mapa dos 16 passos do enunciado

| Passo | Onde está |
|---|---|
| 1. Arquitectura | este README §3 · `docs/arquitectura.md` |
| 2. Estrutura de pastas | §5 |
| 3. UML (PlantUML) | `docs/uml/` |
| 4. BD PostgreSQL | `database/schema.sql` + `seed.sql` |
| 5–6. Ontologia OWL | `ontology/basi.ttl` |
| 7. RDF de exemplo | `rdf/dados_exemplo.ttl` |
| 8. 20+ consultas SPARQL | `sparql/consultas.sparql` (22) |
| 9. API FastAPI | `backend/app/` |
| 10. Frontend | `frontend/src/app/` |
| 11. Recomendação semântica | `backend/app/services/recommendation_service.py` |
| 12. Autenticação JWT + RBAC | `backend/app/core/security.py` + `deps.py` |
| 13. Docker | `docker-compose.yml` + Dockerfiles |
| 14. README | este ficheiro |
| 15. Relatório académico | `docs/relatorio_academico.md` |
| 16. Optimização e engenharia | `docs/arquitectura.md` (secção final) |
```
