-- schema.sql — Modelo relacional do BASI (PostgreSQL).
-- O PostgreSQL guarda os dados transaccionais e de identidade: contas, perfis,
-- documentos, favoritos e relações de seguimento. O conhecimento semântico
-- (relações entre temas e inferências) vive no Apache Jena Fuseki; cada
-- documento tem um "uri_semantica" que liga a linha SQL ao recurso RDF.
-- Convenção: tabelas no plural e em português, chave primária "id" BIGINT
-- IDENTITY e campos created_at/updated_at para auditoria.

-- Extensão para gerar UUIDs (usado em tokens e identificadores públicos).
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- TIPOS ENUMERADOS

-- Perfis de utilizador (controlo de acesso baseado em papéis — RBAC).
CREATE TYPE perfil_utilizador AS ENUM (
    'administrador',
    'professor',
    'estudante',
    'investigador',
    'visitante'
);

-- Tipos de documento académico suportados pela plataforma.
CREATE TYPE tipo_documento AS ENUM (
    'livro',
    'artigo',
    'tese',
    'monografia',
    'manual',
    'apresentacao',
    'material_didactico'
);

-- Estado de moderação de um documento.
CREATE TYPE estado_documento AS ENUM (
    'rascunho',
    'publicado',
    'em_revisao',
    'rejeitado'
);

-- TABELA: utilizadores
-- Conta de acesso. A palavra-passe é SEMPRE guardada como hash (bcrypt).
CREATE TABLE utilizadores (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uuid_publico    UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    nome            VARCHAR(150) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    palavra_passe   VARCHAR(255) NOT NULL,                 -- hash bcrypt
    perfil          perfil_utilizador NOT NULL DEFAULT 'estudante',
    biografia       TEXT,
    instituicao     VARCHAR(200),
    avatar_url      VARCHAR(500),
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    email_validado  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índice por email (login) — já garantido por UNIQUE, mas explícito p/ clareza.
CREATE INDEX idx_utilizadores_perfil ON utilizadores (perfil);

-- TABELA: areas_cientificas
-- Grandes áreas (ex.: Informática, Medicina). Reflectidas na ontologia.
CREATE TABLE areas_cientificas (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome            VARCHAR(150) NOT NULL UNIQUE,
    descricao       TEXT,
    uri_semantica   VARCHAR(500),                          -- IRI no grafo RDF
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- TABELA: temas
-- Temas de investigação (ex.: Inteligência Artificial). Podem ter sub-temas
-- (auto-relação) — isto espelha a hierarquia "eSubtemaDe" da ontologia.
CREATE TABLE temas (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome            VARCHAR(150) NOT NULL UNIQUE,
    descricao       TEXT,
    area_id         BIGINT REFERENCES areas_cientificas (id) ON DELETE SET NULL,
    tema_pai_id     BIGINT REFERENCES temas (id) ON DELETE SET NULL,  -- sub-tema
    uri_semantica   VARCHAR(500),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_temas_area ON temas (area_id);
CREATE INDEX idx_temas_pai ON temas (tema_pai_id);

-- TABELA: palavras_chave
CREATE TABLE palavras_chave (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    termo           VARCHAR(120) NOT NULL UNIQUE,
    uri_semantica   VARCHAR(500)
);

-- TABELA: departamentos / cursos / universidades
CREATE TABLE universidades (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome            VARCHAR(200) NOT NULL UNIQUE,
    sigla           VARCHAR(30),
    pais            VARCHAR(100) DEFAULT 'Angola',
    uri_semantica   VARCHAR(500)
);

CREATE TABLE departamentos (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome            VARCHAR(200) NOT NULL,
    universidade_id BIGINT REFERENCES universidades (id) ON DELETE CASCADE,
    uri_semantica   VARCHAR(500),
    UNIQUE (nome, universidade_id)
);

CREATE TABLE cursos (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nome            VARCHAR(200) NOT NULL,
    grau            VARCHAR(60),                            -- Licenciatura, Mestrado...
    departamento_id BIGINT REFERENCES departamentos (id) ON DELETE SET NULL,
    uri_semantica   VARCHAR(500)
);

-- TABELA: documentos
-- Entidade central. Cada documento pertence a um autor (utilizador) e a uma
-- área científica; tem um "uri_semantica" que o liga ao recurso RDF no Fuseki.
CREATE TABLE documentos (
    id                  BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uuid_publico        UUID NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    titulo              VARCHAR(400) NOT NULL,
    resumo              TEXT,
    tipo                tipo_documento NOT NULL,
    estado              estado_documento NOT NULL DEFAULT 'publicado',
    ano_publicacao      INTEGER,
    idioma              VARCHAR(40) DEFAULT 'Português',
    autor_id            BIGINT NOT NULL REFERENCES utilizadores (id) ON DELETE CASCADE,
    area_id             BIGINT REFERENCES areas_cientificas (id) ON DELETE SET NULL,
    curso_id            BIGINT REFERENCES cursos (id) ON DELETE SET NULL,
    -- Caminho do ficheiro no MinIO (bucket/objecto).
    ficheiro_objecto    VARCHAR(500),
    ficheiro_tamanho    BIGINT,
    -- IRI do recurso correspondente no grafo RDF (ligação SQL <-> Semântica).
    uri_semantica       VARCHAR(500),
    num_downloads       INTEGER NOT NULL DEFAULT 0,
    num_visualizacoes   INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Índices para os filtros mais comuns (pesquisa por tipo, área, autor, ano).
CREATE INDEX idx_documentos_tipo   ON documentos (tipo);
CREATE INDEX idx_documentos_area   ON documentos (area_id);
CREATE INDEX idx_documentos_autor  ON documentos (autor_id);
CREATE INDEX idx_documentos_ano    ON documentos (ano_publicacao);
CREATE INDEX idx_documentos_estado ON documentos (estado);

-- Índice de texto completo (full-text) para a pesquisa textual rápida.
-- 'portuguese' activa stemming em português (ex.: "redes" ~ "rede").
CREATE INDEX idx_documentos_fts ON documentos
    USING GIN (to_tsvector('portuguese', titulo || ' ' || coalesce(resumo, '')));

-- TABELA: documento_temas (N:N entre documentos e temas)
CREATE TABLE documento_temas (
    documento_id    BIGINT NOT NULL REFERENCES documentos (id) ON DELETE CASCADE,
    tema_id         BIGINT NOT NULL REFERENCES temas (id) ON DELETE CASCADE,
    PRIMARY KEY (documento_id, tema_id)
);

-- TABELA: documento_palavras_chave (N:N)
CREATE TABLE documento_palavras_chave (
    documento_id    BIGINT NOT NULL REFERENCES documentos (id) ON DELETE CASCADE,
    palavra_id      BIGINT NOT NULL REFERENCES palavras_chave (id) ON DELETE CASCADE,
    PRIMARY KEY (documento_id, palavra_id)
);

-- TABELA: coautores (N:N entre documentos e utilizadores)
-- Um documento pode ter vários autores além do autor principal.
CREATE TABLE coautores (
    documento_id    BIGINT NOT NULL REFERENCES documentos (id) ON DELETE CASCADE,
    utilizador_id   BIGINT NOT NULL REFERENCES utilizadores (id) ON DELETE CASCADE,
    ordem           SMALLINT DEFAULT 1,
    PRIMARY KEY (documento_id, utilizador_id)
);

-- TABELA: favoritos (utilizador guarda um documento)
CREATE TABLE favoritos (
    utilizador_id   BIGINT NOT NULL REFERENCES utilizadores (id) ON DELETE CASCADE,
    documento_id    BIGINT NOT NULL REFERENCES documentos (id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (utilizador_id, documento_id)
);

-- TABELA: seguidores (rede social: utilizador segue outro utilizador)
CREATE TABLE seguidores (
    seguidor_id     BIGINT NOT NULL REFERENCES utilizadores (id) ON DELETE CASCADE,
    seguido_id      BIGINT NOT NULL REFERENCES utilizadores (id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (seguidor_id, seguido_id),
    -- Um utilizador não pode seguir-se a si próprio.
    CONSTRAINT chk_nao_auto_seguir CHECK (seguidor_id <> seguido_id)
);

-- TABELA: tokens_refresh (suporte a "refresh tokens" do JWT)
-- Guardamos o hash do refresh token para poder revogá-lo (logout / segurança).
CREATE TABLE tokens_refresh (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    utilizador_id   BIGINT NOT NULL REFERENCES utilizadores (id) ON DELETE CASCADE,
    token_hash      VARCHAR(255) NOT NULL,
    expira_em       TIMESTAMPTZ NOT NULL,
    revogado        BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tokens_utilizador ON tokens_refresh (utilizador_id);

-- GATILHO (TRIGGER): actualizar automaticamente "updated_at"
-- Boa prática: a aplicação não precisa de se preocupar com o carimbo de tempo.
CREATE OR REPLACE FUNCTION fn_actualizar_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_utilizadores_updated
    BEFORE UPDATE ON utilizadores
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_updated_at();

CREATE TRIGGER trg_documentos_updated
    BEFORE UPDATE ON documentos
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_updated_at();

-- VISTA (VIEW): documentos_detalhados
-- Junta documento + autor + área num só lugar, simplificando consultas da API.
CREATE VIEW documentos_detalhados AS
SELECT
    d.id,
    d.uuid_publico,
    d.titulo,
    d.resumo,
    d.tipo,
    d.estado,
    d.ano_publicacao,
    d.num_downloads,
    d.num_visualizacoes,
    d.uri_semantica,
    d.created_at,
    u.id   AS autor_id,
    u.nome AS autor_nome,
    a.id   AS area_id,
    a.nome AS area_nome
FROM documentos d
JOIN utilizadores u ON u.id = d.autor_id
LEFT JOIN areas_cientificas a ON a.id = d.area_id;

-- FIM DO SCHEMA
