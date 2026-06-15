# Arquitectura do Semantic Academic Hub (BASI)

Documento de apoio aos passos 1 e 16 do enunciado. Explica as decisões
arquitecturais "como se estivéssemos a ensinar".

## 1. Visão lógica

A aplicação segue uma arquitectura em **camadas** com separação clara de
responsabilidades. No backend isto materializa-se em quatro camadas:

```
HTTP  →  API (routers/controllers)   ← traduz HTTP ↔ chamadas de negócio
         Services (regras de negócio) ← orquestra tudo; onde vive a lógica
         Repositories (acesso a dados) ← isola as queries SQL
         Models (ORM)                  ← mapeia tabelas ↔ objectos Python
```

**Porquê camadas?** Para que cada parte mude de forma independente: trocar a base
de dados afecta só os repositórios; mudar uma regra de negócio afecta só os
serviços; a API mantém-se estável. Isto é testável e escalável.

## 2. Visão física (implantação)

Cinco contentores Docker numa rede privada (ver `docker-compose.yml`):

| Serviço | Porta | Função |
|---|---|---|
| frontend | 3000 | Interface Next.js |
| backend | 8000 | API FastAPI |
| postgres | 5432 | Dados relacionais |
| fuseki | 3030 | Triple store RDF + SPARQL |
| minio | 9000/9001 | Ficheiros (S3) |

## 3. Fluxo de dados (pedido típico de leitura)

1. O utilizador abre `/biblioteca` no frontend.
2. O frontend chama `GET /api/v1/documents`.
3. O router delega no `DocumentService`, que usa o `DocumentRepository`.
4. O repositório consulta o PostgreSQL e devolve objectos ORM.
5. O Pydantic serializa para JSON; o frontend renderiza os cartões.

## 4. Fluxo semântico (pesquisa inteligente)

1. O utilizador procura "Inteligência Artificial" em `/pesquisa-semantica`.
2. O frontend chama `GET /api/v1/semantic-search?q=...`.
3. O `SemanticService` constrói uma consulta **SPARQL** com o caminho transitivo
   `eSubtemaDe*` e envia-a ao **Fuseki**.
4. O Fuseki aplica **inferência** sobre a ontologia e devolve os documentos de IA
   e de todos os subtemas.
5. A API devolve os resultados + a lista de termos expandidos (transparência).

## 5. Ligação SQL ↔ RDF

Cada entidade relevante tem um campo `uri_semantica` (um IRI). É a "ponte" entre
os dois mundos: o PostgreSQL guarda a verdade transaccional; o Fuseki guarda o
conhecimento e as relações. O mesmo documento existe nos dois, ligado pelo IRI.

## 6. Segurança

- **Palavras-passe:** apenas hashes **bcrypt** (com sal), nunca texto simples.
- **Autenticação:** **JWT** sem estado. *Access token* curto (30 min) + *refresh
  token* longo (7 dias). O refresh permite renovar sem novo login; a tabela
  `tokens_refresh` suporta revogação futura.
- **Autorização (RBAC):** a dependência `exigir_perfis(...)` protege rotas por
  perfil (ex.: só administradores acedem à gestão).
- **Endpoint SPARQL:** bloqueia operações de escrita (INSERT/DELETE/DROP...) —
  só leitura é permitida ao público autenticado.
- **CORS:** apenas as origens definidas em `CORS_ORIGINS`.

## 7. Optimização e engenharia profissional (passo 16)

- **Cache:** `lru_cache` na configuração; recomenda-se Redis para cache de
  respostas SPARQL frequentes (a inferência é cara).
- **Lazy loading:** o frontend carrega dados por página; a API é paginada
  (`PaginaResposta`). O Next.js faz *code splitting* automático por rota.
- **Indexação:** índices em `documentos(tipo, area_id, autor_id, ano)` e índice
  **GIN full-text** em português para a pesquisa textual (`schema.sql`).
- **Optimização SPARQL:** usar `DISTINCT` com critério, limitar caminhos
  transitivos a sub-árvores conhecidas, e materializar inferências frequentes.
- **Escalabilidade:** backend sem estado → escala horizontalmente (vários
  *workers*/réplicas atrás de um balanceador). Postgres com réplicas de leitura;
  Fuseki pode ser separado para leitura/escrita.
- **Backup e recuperação:** `pg_dump` agendado para o PostgreSQL; *backup* dos
  ficheiros TDB2 do Fuseki e dos *buckets* MinIO. Volumes Docker persistentes.
- **Observabilidade:** *healthchecks* em todos os serviços; `/health` na API.
