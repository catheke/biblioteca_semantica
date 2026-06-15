-- seed.sql — Dados iniciais (fictícios) do BASI
-- -----------------------------------------------------------------------------
-- Carregado automaticamente após o schema.sql na primeira inicialização do
-- contentor PostgreSQL. Permite ter o sistema "vivo" logo no primeiro arranque.
--
-- NOTA sobre palavras-passe: os hashes abaixo correspondem todos à palavra-passe
-- "password123" (gerados com bcrypt). NÃO usar em produção — apenas demonstração.

-- -----------------------------------------------------------------------------
-- Universidades, departamentos e cursos
-- -----------------------------------------------------------------------------
INSERT INTO universidades (nome, sigla, pais, uri_semantica) VALUES
 ('Universidade Mandume Ya Ndemufayo', 'UMN', 'Angola', 'http://basi.ao/recurso/universidade/umn'),
 ('Universidade Agostinho Neto', 'UAN', 'Angola', 'http://basi.ao/recurso/universidade/uan');

INSERT INTO departamentos (nome, universidade_id, uri_semantica) VALUES
 ('Departamento de Engenharia Informática', 1, 'http://basi.ao/recurso/departamento/dei'),
 ('Departamento de Medicina', 1, 'http://basi.ao/recurso/departamento/dmed');

INSERT INTO cursos (nome, grau, departamento_id, uri_semantica) VALUES
 ('Engenharia Informática', 'Licenciatura', 1, 'http://basi.ao/recurso/curso/eng-info'),
 ('Medicina Geral', 'Licenciatura', 2, 'http://basi.ao/recurso/curso/medicina');

-- -----------------------------------------------------------------------------
-- Áreas científicas
-- -----------------------------------------------------------------------------
INSERT INTO areas_cientificas (nome, descricao, uri_semantica) VALUES
 ('Informática', 'Ciências da computação e tecnologias de informação.', 'http://basi.ao/recurso/area/informatica'),
 ('Medicina', 'Ciências da saúde e prática clínica.', 'http://basi.ao/recurso/area/medicina'),
 ('Engenharia', 'Engenharias diversas.', 'http://basi.ao/recurso/area/engenharia'),
 ('Economia', 'Ciências económicas e gestão.', 'http://basi.ao/recurso/area/economia');

-- -----------------------------------------------------------------------------
-- Temas (com hierarquia de sub-temas via tema_pai_id)
-- -----------------------------------------------------------------------------
INSERT INTO temas (nome, descricao, area_id, tema_pai_id, uri_semantica) VALUES
 ('Inteligência Artificial', 'Sistemas que simulam capacidades cognitivas.', 1, NULL, 'http://basi.ao/recurso/tema/ia'),
 ('Machine Learning', 'Aprendizagem automática a partir de dados.', 1, 1, 'http://basi.ao/recurso/tema/ml'),
 ('Deep Learning', 'Redes neuronais profundas.', 1, 2, 'http://basi.ao/recurso/tema/dl'),
 ('Redes Neurais', 'Modelos inspirados no cérebro.', 1, 2, 'http://basi.ao/recurso/tema/rn'),
 ('Ciência de Dados', 'Extracção de conhecimento de dados.', 1, 1, 'http://basi.ao/recurso/tema/cd'),
 ('Visão Computacional', 'Interpretação automática de imagens.', 1, 1, 'http://basi.ao/recurso/tema/vc'),
 ('Web Semântica', 'Dados ligados e ontologias.', 1, NULL, 'http://basi.ao/recurso/tema/websem'),
 ('Cardiologia', 'Estudo do coração.', 2, NULL, 'http://basi.ao/recurso/tema/cardio'),
 ('Microeconomia', 'Comportamento de agentes económicos.', 4, NULL, 'http://basi.ao/recurso/tema/micro');

-- -----------------------------------------------------------------------------
-- Palavras-chave
-- -----------------------------------------------------------------------------
INSERT INTO palavras_chave (termo, uri_semantica) VALUES
 ('algoritmos', 'http://basi.ao/recurso/palavra/algoritmos'),
 ('python', 'http://basi.ao/recurso/palavra/python'),
 ('ontologia', 'http://basi.ao/recurso/palavra/ontologia'),
 ('sparql', 'http://basi.ao/recurso/palavra/sparql'),
 ('saude', 'http://basi.ao/recurso/palavra/saude');

-- -----------------------------------------------------------------------------
-- Utilizadores (1 admin, professores, estudantes, investigador)
-- -----------------------------------------------------------------------------
INSERT INTO utilizadores (nome, email, palavra_passe, perfil, instituicao, email_validado) VALUES
 ('Administrador BASI', 'admin@basi.ao', '$2b$12$LQ8Q5e7zVZ6m1nQ8YQ8YuO2vJ9kF6cH3wT0pX1bN4dM7sR2aL9eS', 'administrador', 'UMN', TRUE),
 ('Prof. Adriano Sigu', 'adriano@basi.ao', '$2b$12$LQ8Q5e7zVZ6m1nQ8YQ8YuO2vJ9kF6cH3wT0pX1bN4dM7sR2aL9eS', 'professor', 'UMN', TRUE),
 ('Prof. Filipe Tchivela', 'filipe@basi.ao', '$2b$12$LQ8Q5e7zVZ6m1nQ8YQ8YuO2vJ9kF6cH3wT0pX1bN4dM7sR2aL9eS', 'professor', 'UMN', TRUE),
 ('Inv. Pedro Mendes', 'pedro@basi.ao', '$2b$12$LQ8Q5e7zVZ6m1nQ8YQ8YuO2vJ9kF6cH3wT0pX1bN4dM7sR2aL9eS', 'investigador', 'UMN', TRUE),
 ('Estudante Maria Sousa', 'maria@basi.ao', '$2b$12$LQ8Q5e7zVZ6m1nQ8YQ8YuO2vJ9kF6cH3wT0pX1bN4dM7sR2aL9eS', 'estudante', 'UMN', TRUE);

-- -----------------------------------------------------------------------------
-- Documentos
-- -----------------------------------------------------------------------------
INSERT INTO documentos (titulo, resumo, tipo, ano_publicacao, autor_id, area_id, uri_semantica) VALUES
 ('Introdução à Inteligência Artificial', 'Fundamentos de IA, agentes e procura.', 'livro', 2023, 2, 1, 'http://basi.ao/recurso/documento/doc1'),
 ('Aprendizagem Profunda Aplicada', 'Redes neuronais convolucionais e recorrentes.', 'artigo', 2024, 2, 1, 'http://basi.ao/recurso/documento/doc2'),
 ('Web Semântica e Ontologias OWL', 'RDF, RDFS, OWL e inferência com SPARQL.', 'tese', 2024, 3, 1, 'http://basi.ao/recurso/documento/doc3'),
 ('Visão Computacional com Python', 'Processamento de imagem e detecção de objectos.', 'manual', 2023, 4, 1, 'http://basi.ao/recurso/documento/doc4'),
 ('Fundamentos de Cardiologia', 'Anatomia e patologias cardíacas.', 'livro', 2022, 3, 2, 'http://basi.ao/recurso/documento/doc5'),
 ('Ciência de Dados para Iniciantes', 'Pipeline de dados, pandas e visualização.', 'material_didactico', 2024, 4, 1, 'http://basi.ao/recurso/documento/doc6');

-- Relações documento <-> tema
INSERT INTO documento_temas (documento_id, tema_id) VALUES
 (1, 1),            -- doc1 -> IA
 (2, 2), (2, 3), (2, 4),  -- doc2 -> ML, DL, Redes Neurais
 (3, 7),            -- doc3 -> Web Semântica
 (4, 6),            -- doc4 -> Visão Computacional
 (5, 8),            -- doc5 -> Cardiologia
 (6, 5);            -- doc6 -> Ciência de Dados

-- Palavras-chave por documento
INSERT INTO documento_palavras_chave (documento_id, palavra_id) VALUES
 (1, 1), (2, 2), (3, 3), (3, 4), (4, 2), (5, 5), (6, 2);

-- Favoritos e seguidores (rede social)
INSERT INTO favoritos (utilizador_id, documento_id) VALUES (5, 1), (5, 3), (4, 2);
INSERT INTO seguidores (seguidor_id, seguido_id) VALUES (5, 2), (5, 3), (4, 2), (1, 2);

-- FIM DO SEED
