const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, PageBreak, TableOfContents,
  Header, Footer, TabStopType, TabStopPosition, ImageRun,
} = require("docx");

// ---------------------------------------------------------------------------
// Dados do grupo (editar aqui se os nomes/números mudarem)
// ---------------------------------------------------------------------------
const MEMBROS = [
  { n: 1, nome: "Pedro Calenga", num: "2022110222" },
  { n: 2, nome: "Filipe Tchivela", num: "2022142100" },
  { n: 3, nome: "Adriano De Júlio", num: "2022179366" },
];

const CONTENT_W = 9360; // US Letter, margens de 1 polegada

// ---------- helpers ----------
const P = (text, opts = {}) =>
  new Paragraph({
    spacing: { after: 120, line: 360 },
    alignment: opts.align ?? AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, ...opts })],
  });

const H1 = (text) =>
  new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(text)] });
const H2 = (text) =>
  new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(text)] });

const bullet = (text) =>
  new Paragraph({
    numbering: { reference: "lista", level: 0 },
    spacing: { after: 60, line: 360 },
    children: typeof text === "string" ? [new TextRun(text)] : text,
  });

const num = (text) =>
  new Paragraph({
    numbering: { reference: "numerada", level: 0 },
    spacing: { after: 60, line: 360 },
    children: typeof text === "string" ? [new TextRun(text)] : text,
  });

const code = (linhas) =>
  linhas.map((l, i) =>
    new Paragraph({
      spacing: { after: i === linhas.length - 1 ? 120 : 0 },
      shading: { fill: "F2F2F2", type: ShadingType.CLEAR },
      children: [new TextRun({ text: l || " ", font: "Consolas", size: 18 })],
    })
  );

// Captura de ecrã centrada, com legenda. As imagens estão em docs/capturas.
const CAP = "/Users/teste/Documents/TAC/semantic-academic-hub/docs/capturas";
const imagem = (ficheiro, w, h, legenda) => [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 40 },
    children: [
      new ImageRun({
        type: "png",
        data: fs.readFileSync(`${CAP}/${ficheiro}`),
        transformation: { width: w, height: h },
        altText: { title: legenda, description: legenda, name: ficheiro },
      }),
    ],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 200 },
    children: [new TextRun({ text: legenda, italics: true, size: 18, color: "595959" })],
  }),
];

const runB = (t) => new TextRun({ text: t, bold: true });
const run = (t) => new TextRun({ text: t });

// borda de tabela
const bd = { style: BorderStyle.SINGLE, size: 1, color: "BFBFBF" };
const borders = { top: bd, bottom: bd, left: bd, right: bd };
const cell = (text, { w, fill, bold = false, align } = {}) =>
  new TableCell({
    borders,
    width: { size: w, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: { top: 80, bottom: 80, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [
      new Paragraph({
        alignment: align,
        children: [new TextRun({ text, bold })],
      }),
    ],
  });

// ---------- Capa ----------
const capa = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 160 },
    children: [new ImageRun({
      type: "jpg",
      data: fs.readFileSync(`${CAP}/logo_umn.jpeg`),
      transformation: { width: 360, height: 126 },
      altText: {
        title: "Universidade Mandume ya Ndemufayo",
        description: "Logótipo da UMN — Instituto Politécnico da Huíla",
        name: "logo_umn",
      },
    })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [runB("INSTITUTO SUPERIOR POLITÉCNICO DA HUÍLA")] }),
  P("Universidade Mandume ya Ndemufayo", { align: AlignmentType.CENTER }),
  P("Licenciatura em Ciências da Computação — 4.º ano", { align: AlignmentType.CENTER }),
  P("Disciplina: Web Semântica", { align: AlignmentType.CENTER }),
  P("Docente: Faby Sapeth", { align: AlignmentType.CENTER }),
  new Paragraph({ spacing: { before: 500 }, children: [] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 120 },
    children: [new TextRun({ text: "Semantic Academic Hub (BASI)", bold: true, size: 40 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
    children: [new TextRun({ text: "Biblioteca Académica Semântica Integrada", italics: true, size: 26 })] }),
  P("Trabalho académico apresentado no âmbito da disciplina de Web Semântica.",
    { align: AlignmentType.CENTER }),
  new Paragraph({ spacing: { before: 300 }, alignment: AlignmentType.LEFT,
    children: [runB("Discentes:")] }),
  ...MEMBROS.map((m) =>
    P(`${m.nome}  —  Nº ${m.num}`, { align: AlignmentType.LEFT })),
  new Paragraph({ spacing: { before: 500 }, alignment: AlignmentType.CENTER,
    children: [runB("Lubango, junho de 2026")] }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- Epígrafe (citação) ----------
const epigrafe = [
  new Paragraph({ spacing: { before: 3600 }, children: [] }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 160 },
    children: [new TextRun({
      text: "“A ciência é o conhecimento acumulado pela humanidade ao longo de milhares de anos.”",
      italics: true, size: 28, color: "1F3864",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER,
    children: [new TextRun({ text: "— Senku Ishigami, Dr. Stone", size: 22, color: "595959" })],
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- Organograma + tabela de estudantes ----------
const orgBox = (text, fill) => {
  const linhas = text.split("\n");
  return new TableCell({
    borders, width: { size: 3000, type: WidthType.DXA },
    shading: { fill, type: ShadingType.CLEAR },
    margins: { top: 120, bottom: 120, left: 120, right: 120 },
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: linhas.flatMap((l, i) =>
        i === 0
          ? [new TextRun({ text: l, bold: true })]
          : [new TextRun({ text: l, bold: true, break: 1 })]
      ),
    })],
  });
};

const organograma = [
  H1("Organização do Grupo"),
  P("O grupo organizou-se de forma colaborativa. A coordenação ficou a cargo de um dos membros, com repartição das áreas de trabalho (modelação semântica, backend e frontend) por todos os elementos."),
  // topo
  new Table({
    width: { size: 3000, type: WidthType.DXA }, columnWidths: [3000],
    alignment: AlignmentType.CENTER,
    rows: [new TableRow({ children: [orgBox("Coordenação\n" + MEMBROS[0].nome, "D9E2F3")] })],
  }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 0 }, children: [new TextRun("|")] }),
  // base (3 membros)
  new Table({
    width: { size: 9000, type: WidthType.DXA }, columnWidths: [3000, 3000, 3000],
    alignment: AlignmentType.CENTER,
    rows: [new TableRow({ children: [
      orgBox("Modelação\n(Ontologia / SPARQL)\n" + MEMBROS[0].nome, "EAF1FB"),
      orgBox("Backend\n(FastAPI / Fuseki)\n" + MEMBROS[1].nome, "EAF1FB"),
      orgBox("Frontend\n(Next.js / UI)\n" + MEMBROS[2].nome, "EAF1FB"),
    ] })],
  }),
  new Paragraph({ spacing: { before: 240 }, children: [] }),
  H2("Identificação dos Estudantes"),
  new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [900, 4860, 1800, 1800],
    rows: [
      new TableRow({ tableHeader: true, children: [
        cell("Nº", { w: 900, fill: "2E75B6", bold: true, align: AlignmentType.CENTER }),
        cell("Nome do Estudante", { w: 4860, fill: "2E75B6", bold: true }),
        cell("Nº de Estudante", { w: 1800, fill: "2E75B6", bold: true, align: AlignmentType.CENTER }),
        cell("Avaliação", { w: 1800, fill: "2E75B6", bold: true, align: AlignmentType.CENTER }),
      ] }),
      ...MEMBROS.map((m) => new TableRow({ children: [
        cell(String(m.n), { w: 900, align: AlignmentType.CENTER }),
        cell(m.nome, { w: 4860 }),
        cell(m.num, { w: 1800, align: AlignmentType.CENTER }),
        cell("", { w: 1800 }),
      ] })),
    ],
  }),
  new Paragraph({ spacing: { before: 120 }, children: [new TextRun({ text: "Nota: a coluna “Avaliação” destina-se ao preenchimento pelo docente.", italics: true, size: 18 })] }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- Índice ----------
const indice = [
  H1("Índice"),
  new TableOfContents("Sumário", { hyperlink: true, headingStyleRange: "1-2" }),
];

// ---------- Corpo ----------
// A ordem das secções segue a estrutura exigida no enunciado (Secção 5):
// Introdução; Problemática; Objectivos; Fundamentação Teórica; Modelação da
// Ontologia; Arquitectura da Solução; Tecnologias Utilizadas; Implementação;
// Resultados; Dificuldades; Conclusões; Referências. As secções adicionais
// (Análise de Requisitos, Base de Conhecimento/SPARQL, Optimização e Testes)
// reforçam os critérios de avaliação sem quebrar essa ordem.
const corpo = [
  H1("1. Introdução"),
  P("Este relatório descreve a concepção e a implementação do Semantic Academic Hub (BASI), uma biblioteca académica que aplica tecnologias de Web Semântica para ligar obras, autores, áreas científicas e temas de investigação. O objectivo central é demonstrar, de forma realista e funcional, como uma ontologia OWL e a inferência sobre um grafo RDF (Apache Jena Fuseki, com motor rdflib como alternativa) transformam uma biblioteca digital comum numa plataforma capaz de compreender as relações entre conceitos."),
  P("A figura seguinte apresenta a página inicial da aplicação, que comunica desde logo o diferencial do sistema: uma pesquisa que compreende o que se procura."),
  ...imagem("home.png", 400, 439, "Figura 1 — Página inicial do BASI (versão em produção), com demonstração da pesquisa semântica."),
  P("Ao longo do documento apresentam-se o problema que motivou o trabalho, os objectivos, a fundamentação teórica, a modelação da ontologia, a arquitectura adoptada, as tecnologias utilizadas, os detalhes de implementação, os resultados obtidos, as dificuldades encontradas e as conclusões."),

  H1("2. Problemática"),
  P("As bibliotecas académicas acumulam grandes volumes de informação, mas têm dificuldade em revelar as relações entre os seus conteúdos. Uma pesquisa textual clássica por “Inteligência Artificial” devolve apenas os documentos que contêm literalmente essas palavras, ignorando trabalhos sobre Machine Learning, Deep Learning ou Redes Neurais, que são subtemas directos e igualmente relevantes."),
  P("A motivação do projecto é eliminar esta limitação: representar o conhecimento num grafo onde as relações são explícitas e onde o motor pode inferir factos que não foram escritos directamente. Se Deep Learning é subtema de Machine Learning, e este é subtema de Inteligência Artificial, então um documento de Deep Learning também é relevante para uma pesquisa por Inteligência Artificial. Esta é exactamente a problemática do Tema 1 do enunciado: descobrir relações entre obras, autores, áreas científicas e temas de investigação."),

  H1("3. Objectivos"),
  H2("3.1 Objectivo geral"),
  P("Construir uma rede académica semântica, profissional e escalável, que descubra relações entre obras, autores e temas de investigação numa biblioteca universitária."),
  H2("3.2 Objectivos específicos"),
  bullet("Modelar o domínio académico numa ontologia OWL (TBox) com instâncias RDF (ABox)."),
  bullet("Implementar pesquisa semântica com inferência via SPARQL, recorrendo a caminhos transitivos."),
  bullet("Oferecer recomendações inteligentes baseadas no grafo de conhecimento."),
  bullet("Disponibilizar autenticação segura (JWT + RBAC) e gestão de documentos."),
  bullet("Organizar o acervo segundo a Classificação Decimal Universal (CDU), modelada em SKOS."),
  bullet("Orquestrar os componentes com persistência poliglota (relacional, grafo e ficheiros)."),

  H1("4. Fundamentação Teórica"),
  P("A Web Semântica estende a Web actual com significado processável por máquinas, assente num conjunto de normas do W3C e nas boas práticas de modelação de ontologias [5]:"),
  bullet([runB("RDF "), run("(Resource Description Framework): modelo de dados em triplos sujeito–predicado–objecto [1].")]),
  bullet([runB("RDFS / OWL: "), run("linguagens para descrever classes, propriedades e restrições, permitindo inferência [2].")]),
  bullet([runB("SPARQL: "), run("linguagem de consulta sobre grafos RDF; suporta caminhos de propriedade (por exemplo, eSubtemaDe* significa zero ou mais saltos) [3].")]),
  bullet([runB("SKOS: "), run("vocabulário-padrão para representar sistemas de classificação e taxonomias, usado aqui para modelar a CDU [4].")]),
  bullet([runB("IRI: "), run("identificador global de cada recurso — a ponte entre o mundo relacional (PostgreSQL) e o semântico (Fuseki), através do campo uri_semantica.")]),
  P("Propriedades OWL utilizadas no projecto [5]:"),
  bullet([runB("Transitiva "), run("(eSubtemaDe): se A é subtema de B e B é subtema de C, então A é subtema de C — base da expansão de temas.")]),
  bullet([runB("Simétrica "), run("(obraRelacionada): se A está relacionada com B, então B está relacionada com A.")]),
  bullet([runB("Inversa "), run("(temAutor / ehAutorDe): permite navegar a relação nos dois sentidos.")]),
  bullet([runB("Funcional "), run("(email): cada pessoa tem, no máximo, um valor para esta propriedade.")]),

  H1("5. Análise de Requisitos"),
  P("Actores do sistema: Visitante, Estudante, Professor, Investigador e Administrador."),
  H2("5.1 Requisitos funcionais"),
  bullet("RF1 — Pesquisar conteúdos (pesquisa textual e pesquisa semântica)."),
  bullet("RF2 — Consultar o detalhe de um documento e descarregá-lo conforme o nível de acesso."),
  bullet("RF3 — Registar conta e iniciar sessão."),
  bullet("RF4 — Guardar favoritos e seguir autores."),
  bullet("RF5 — Receber recomendações personalizadas."),
  bullet("RF6 — Publicar documentos (professor/investigador)."),
  bullet("RF7 — Administração: gerir utilizadores, documentos e sincronização com o grafo."),
  bullet("RF8 — Endpoint SPARQL apenas de leitura."),
  bullet("RF9 — Filtrar a pesquisa por autor e por ano de publicação."),
  bullet("RF10 — Consultar o histórico pessoal de leituras e de pesquisas."),
  bullet("RF11 — Receber notificações de novos documentos adicionados ao acervo."),
  bullet("RF12 — Consultar estatísticas de utilização (perfil administrador)."),
  bullet("RF13 — Gerir a circulação: exemplares, empréstimos, reservas e multas."),
  H2("5.2 Requisitos não-funcionais"),
  P("Segurança (JWT, RBAC, bcrypt), escalabilidade (backend sem estado), desempenho (índices, paginação e cache) e portabilidade (configuração por variáveis de ambiente)."),

  H1("6. Modelação da Ontologia (OWL)"),
  P("A ontologia (ontology/basi.ttl) define a hierarquia de classes Pessoa → Autor → {Professor, Estudante, Investigador}, as subclasses de Documento (Livro, Artigo, Tese, Monografia, Manual, Apresentação, Material Didáctico) e as classes AreaCientifica, Tema, Genero e PalavraChave."),
  P("As relações entre indivíduos são modeladas como propriedades de objecto, com os axiomas OWL que habilitam a inferência. O excerto seguinte mostra as três propriedades fundamentais — transitiva, simétrica e inversa:"),
  ...code([
    "# Propriedade TRANSITIVA — base da expansão de temas",
    "basi:eSubtemaDe a owl:ObjectProperty, owl:TransitiveProperty ;",
    "    rdfs:domain basi:Tema ; rdfs:range basi:Tema .",
    "",
    "# Propriedade SIMÉTRICA — relação entre obras",
    "basi:obraRelacionada a owl:ObjectProperty, owl:SymmetricProperty ;",
    "    rdfs:domain basi:Documento ; rdfs:range basi:Documento .",
    "",
    "# Propriedade INVERSA — autoria navegável nos dois sentidos",
    "basi:temAutor a owl:ObjectProperty ;",
    "    owl:inverseOf basi:ehAutorDe .",
  ]),
  P("A ontologia inclui ainda restrições OWL e classes inferidas: por owl:Restriction exige-se que cada Documento tenha pelo menos um autor (cardinalidade mínima 1); por owl:equivalentClass define-se DocumentoDeIA (qualquer documento cujo tema seja Inteligência Artificial ou um seu subtema) e ProfessorActivo (professor autor de pelo menos um documento). O axioma owl:AllDisjointClasses garante que um documento não pode ser, em simultâneo, Livro e Tese. A CDU é modelada como um skos:ConceptScheme, em que cada secção e género é um skos:Concept."),

  H1("7. Base de Conhecimento e Consultas SPARQL"),
  P("A base de conhecimento (rdf/dados_exemplo.ttl) materializa as instâncias (ABox): áreas científicas, uma hierarquia de temas com três níveis de profundidade, autores, doze documentos técnicos e as relações entre eles (autoria, tema, citações e obras relacionadas). Estes doze documentos formam o núcleo densamente ligado que sustenta a demonstração da inferência; o catálogo completo da aplicação reúne 55 obras (documentos técnicos e literatura de domínio público), todas classificadas pela CDU. No servidor Fuseki em produção estão carregados 493 triplos. O excerto abaixo ilustra como a hierarquia de temas e a classificação de um documento são declaradas em triplos RDF:"),
  ...code([
    "basi:Tema_DeepLearning a basi:Tema ;",
    "    basi:nome \"Deep Learning\" ;",
    "    basi:eSubtemaDe basi:Tema_MachineLearning .",
    "",
    "rec:documento/doc2 a basi:Artigo ;",
    "    basi:titulo \"Aprendizagem Profunda Aplicada\" ;",
    "    basi:temTema basi:Tema_DeepLearning ;",
    "    basi:temAutor rec:pessoa/adriano .",
  ]),
  P("A consulta-chave da pesquisa semântica usa um caminho de propriedade transitivo (eSubtemaDe*) para percorrer toda a sub-árvore de um tema e devolver os documentos a ele ligados, mesmo que o título não contenha a palavra pesquisada:"),
  ...code([
    "SELECT DISTINCT ?titulo WHERE {",
    "  ?temaRaiz basi:nome \"Inteligência Artificial\" .",
    "  ?tema basi:eSubtemaDe* ?temaRaiz .",
    "  ?doc  basi:temTema ?tema ;",
    "        basi:titulo  ?titulo .",
    "}",
  ]),
  P("Esta consulta é gerada e executada pelo backend, no ServicoSemantico, demonstrando a integração entre a aplicação e a componente semântica:"),
  ...code([
    "def expandir_termo(self, termo: str) -> list[str]:",
    "    nomes: list[str] = []",
    "    for raiz in self.temas_correspondentes(termo):",
    "        query = f'''{PREFIXOS}",
    "        SELECT DISTINCT ?nomeSub WHERE {",
    "            ?temaRaiz basi:nome \"{raiz}\" .",
    "            ?sub basi:eSubtemaDe* ?temaRaiz ;",
    "                 basi:nome ?nomeSub .",
    "        }'''",
    "        for linha in self.executar_select(query):",
    "            nomes.append(linha[\"nomeSub\"])",
    "    return nomes",
  ]),

  H1("8. Arquitectura da Solução"),
  P("A solução adopta uma arquitectura em camadas com persistência poliglota: cada tipo de dado é guardado no repositório mais adequado."),
  ...code([
    "Frontend (Next.js)  ->  API (FastAPI)  ->  Serviços  ->  Repositórios  ->  Modelos (ORM)",
    "                                          \\-> ServicoSemantico -> Fuseki (SPARQL/OWL)",
    "",
    "PostgreSQL (identidade/metadados) · Fuseki (conhecimento) · MinIO (ficheiros)",
  ]),
  P("Cada documento existe nos dois mundos — relacional e semântico — ligados pelo campo uri_semantica. Esta separação mantém o sistema testável e permite escalar cada componente de forma independente."),
  H2("8.1 Modelação da base de dados relacional"),
  P("O esquema PostgreSQL (database/schema.sql) inclui as tabelas utilizadores, areas_cientificas, temas (com auto-referência tema_pai_id), palavras_chave, universidades, departamentos, cursos e documentos, além das tabelas de associação documento_temas, coautores, favoritos e seguidores, e ainda tokens_refresh. Possui um índice GIN de texto completo em português, campos de auditoria (created_at/updated_at) e o campo uri_semantica que estabelece a ligação com o grafo RDF."),
  H2("8.2 Sincronização SQL ↔ RDF"),
  P("Quando o administrador adiciona ou remove um documento, o sistema actualiza simultaneamente a base relacional e o grafo RDF, garantindo que a pesquisa semântica reflecte sempre o estado actual do catálogo."),

  H1("9. Tecnologias Utilizadas"),
  P("As tecnologias foram escolhidas pela maturidade, pela produtividade e pela boa integração com o ecossistema de Web Semântica:"),
  new Table({
    width: { size: CONTENT_W, type: WidthType.DXA }, columnWidths: [3000, 6360],
    rows: [
      new TableRow({ tableHeader: true, children: [
        cell("Camada", { w: 3000, fill: "2E75B6", bold: true }),
        cell("Tecnologias", { w: 6360, fill: "2E75B6", bold: true }),
      ] }),
      new TableRow({ children: [ cell("Frontend", { w: 3000, bold: true, fill: "EAF1FB" }), cell("Next.js 14 (App Router), React, TypeScript, TailwindCSS", { w: 6360 }) ] }),
      new TableRow({ children: [ cell("Backend", { w: 3000, bold: true, fill: "EAF1FB" }), cell("Python, FastAPI, Pydantic, SQLAlchemy 2.0", { w: 6360 }) ] }),
      new TableRow({ children: [ cell("Dados relacionais", { w: 3000, bold: true, fill: "EAF1FB" }), cell("PostgreSQL (SQLite em ambiente local)", { w: 6360 }) ] }),
      new TableRow({ children: [ cell("Web Semântica", { w: 3000, bold: true, fill: "EAF1FB" }), cell("Apache Jena Fuseki, rdflib, RDF, RDFS, OWL, SPARQL, SKOS", { w: 6360 }) ] }),
      new TableRow({ children: [ cell("Ficheiros", { w: 3000, bold: true, fill: "EAF1FB" }), cell("MinIO (armazenamento de objectos)", { w: 6360 }) ] }),
      new TableRow({ children: [ cell("Segurança", { w: 3000, bold: true, fill: "EAF1FB" }), cell("JWT, bcrypt, RBAC", { w: 6360 }) ] }),
    ],
  }),
  new Paragraph({ spacing: { after: 120 }, children: [] }),

  H1("10. Implementação"),
  H2("10.1 Backend"),
  P("O backend, em FastAPI, está organizado em camadas (api/, services/, repositories/, models/, schemas/). O ServicoSemantico constrói e executa consultas SPARQL contra o Fuseki, com degradação graciosa: se o Fuseki estiver indisponível, recorre a um grafo rdflib em memória, mantendo a API a responder. O ServicoRecomendacoes combina sinais de conteúdo e de grafo. A documentação OpenAPI é gerada automaticamente em /docs."),
  H2("10.2 Frontend"),
  P("O frontend, em Next.js 14 com TypeScript e TailwindCSS, concentra as chamadas num cliente HTTP central (lib/api.ts) que gere os tokens; o contexto de autenticação (lib/auth.tsx) protege as rotas. A página de destaque é a de pesquisa semântica, que mostra os termos expandidos para tornar a inferência transparente ao utilizador. A biblioteca é apresentada por secções da CDU, à semelhança das estantes de uma biblioteca física."),
  H2("10.3 Segurança"),
  bullet("Palavras-passe guardadas apenas como hash bcrypt (com sal)."),
  bullet("Autenticação JWT sem estado: token de acesso (30 min) e token de renovação (7 dias)."),
  bullet("Autorização baseada em papéis (RBAC) através da dependência exigir_perfis(...)."),
  bullet("Endpoint SPARQL restrito a leitura (bloqueia INSERT, DELETE, DROP, etc.)."),
  bullet("CORS limitado às origens autorizadas."),

  H1("11. Resultados"),
  P("O sistema cumpre os objectivos propostos e a integração semântica funciona de ponta a ponta. A figura seguinte mostra a pesquisa por “Inteligência Artificial”: o sistema expande o termo, por inferência transitiva, para nove temas relacionados (Machine Learning, Deep Learning, Redes Neurais, Aprendizagem por Reforço, Ciência de Dados, Big Data, Visão Computacional e Processamento de Linguagem Natural) e devolve os nove documentos ligados a qualquer um deles, indicando em cada resultado o tema que o tornou relevante."),
  ...imagem("pesquisa_resultados.png", 360, 448, "Figura 2 — Pesquisa semântica (em produção): nove temas expandidos por inferência e os nove documentos encontrados."),
  P("A pesquisa por título também tira partido da camada semântica: quando um termo não corresponde a nenhum título nem resumo, o sistema recorre automaticamente à pesquisa por significado e mostra as obras dos temas relacionados, indicando o porquê de cada resultado."),
  ...imagem("pesquisa_recurso_semantico.png", 430, 469, "Figura 3 — Recurso à camada semântica: sem correspondência textual, mostram-se obras por significado."),
  P("A biblioteca apresenta o acervo organizado pelas secções da Classificação Decimal Universal (CDU), com contagem de obras por secção e subdivisão da Literatura por género."),
  ...imagem("biblioteca.png", 490, 326, "Figura 4 — Biblioteca (em produção) organizada pelas secções da CDU, com 55 obras no acervo."),
  P("Síntese dos resultados:"),
  bullet("A pesquisa por um tema expande automaticamente para todos os seus subtemas e devolve os documentos ligados a qualquer um deles, mesmo sem a palavra pesquisada no título."),
  bullet("Termos que não correspondem a nenhum tema não são “inventados”: o sistema recorre à pesquisa por título/resumo e sugere temas válidos, evitando respostas sem sentido."),
  bullet("As recomendações partem dos favoritos do utilizador e, através da expansão transitiva, sugerem documentos de temas relacionados."),
  bullet("O controlo de acesso por perfis funciona em toda a aplicação, do backend à interface."),
  bullet("A adição/remoção de documentos pelo administrador reflecte-se imediatamente no grafo e na pesquisa."),
  H2("11.1 Implantação em produção e funcionalidades complementares"),
  P("A aplicação encontra-se publicada e acessível em linha: o frontend em https://basi-frontend-3zod.onrender.com e a API em https://basi-backend-50sv.onrender.com/api/v1, com o endpoint SPARQL e o grafo Apache Jena Fuseki activos (493 triplos carregados). O acervo em produção conta com 55 obras, combinando documentos técnicos e literatura de domínio público classificada pela CDU. As figuras 1, 2 e 4 deste relatório foram captadas directamente do ambiente em produção."),
  P("Em torno do núcleo semântico, o sistema integra ainda funcionalidades próprias de uma biblioteca real, que complementam — sem substituir — a exploração do conhecimento:"),
  bullet("Filtros de pesquisa por autor e por ano, a par da pesquisa textual e da pesquisa semântica."),
  bullet("Histórico pessoal de leituras e de pesquisas, por utilizador."),
  bullet("Notificações de novos documentos adicionados ao acervo."),
  bullet("Painel de estatísticas (administrador): obras mais vistas e descarregadas, distribuição por secção da CDU e termos mais pesquisados."),
  bullet("Módulo de circulação: gestão de exemplares, empréstimos, reservas e multas."),

  H1("12. Dificuldades"),
  bullet("Manter a coerência entre o mundo relacional e o semântico exigiu uma convenção rigorosa de IRIs (uri_semantica) partilhada pelas duas camadas."),
  bullet("A primeira versão das recomendações não devolvia resultados, porque procurava apenas o tema exacto; a solução passou por usar a expansão transitiva eSubtemaDe*, que considera também os subtemas."),
  bullet("Foi necessário garantir o funcionamento sem o Fuseki externo, o que motivou a implementação do grafo rdflib em memória como alternativa."),
  bullet("A modelação da CDU em SKOS, ligando cada secção à área científica já existente, exigiu cuidado para não duplicar conceitos."),

  H1("13. Optimização, Escalabilidade e Testes"),
  P("O backend é sem estado, o que permite escalar horizontalmente. Recorre-se a cache (lru_cache no carregamento do grafo e na configuração), paginação, índices relacionais e de texto completo, e à optimização dos caminhos transitivos. Existem testes automáticos com pytest sobre uma base SQLite isolada, cobrindo verificação de saúde, registo, início de sessão, leitura do utilizador autenticado, rejeição de email duplicado e publicação de documento, sem dependerem de PostgreSQL nem do Fuseki. A ontologia é validada por um script dedicado que confirma a sua boa formação. Como evolução, recomenda-se cache Redis para respostas SPARQL frequentes e réplicas de leitura no PostgreSQL."),

  H1("14. Conclusões"),
  P("O BASI demonstra que a Web Semântica acrescenta valor real a uma biblioteca académica: a pesquisa deixa de ser por palavras e passa a ser por significado. A arquitectura poliglota separa identidade, conhecimento e ficheiros, mantendo o sistema testável e escalável, e a ontologia centraliza as relações entre temas, de modo que melhorar o grafo melhora de imediato a pesquisa e as recomendações, sem alterar o código. O projecto responde directamente à problemática do Tema 1 e cumpre todos os entregáveis exigidos: código-fonte, ontologia, base de conhecimento e este relatório técnico."),
  P("Como trabalho futuro, prevê-se a introdução de cache Redis para a inferência, a importação automática de metadados (DOI/BibTeX), recomendações com embeddings e a materialização das inferências mais frequentes no Fuseki, reduzindo a latência."),

  H1("15. Referências Bibliográficas"),
  num("W3C. RDF 1.1 Concepts and Abstract Syntax. World Wide Web Consortium, 2014."),
  num("W3C. OWL 2 Web Ontology Language — Primer. World Wide Web Consortium, 2012."),
  num("W3C. SPARQL 1.1 Query Language. World Wide Web Consortium, 2013."),
  num("W3C. SKOS Simple Knowledge Organization System Reference. World Wide Web Consortium, 2009."),
  num("ALLEMANG, D.; HENDLER, J. Semantic Web for the Working Ontologist. 2.ª ed. Morgan Kaufmann, 2011."),
  num("Apache Software Foundation. Apache Jena Fuseki — Documentation. Disponível em jena.apache.org."),
  num("FastAPI. FastAPI Documentation. Disponível em fastapi.tiangolo.com."),
  num("Vercel. Next.js Documentation. Disponível em nextjs.org."),
  num("UDC Consortium. Universal Decimal Classification (CDU) — Outline. Disponível em udcc.org."),
];

// ---------- Rodapés ----------
// Rodapé vazio (capa). Rodapé com número de página simples e centrado.
const rodapeVazio = () =>
  new Footer({ children: [new Paragraph({ children: [] })] });
const rodapeNumero = () =>
  new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120 },
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 24, color: "000000" })],
    })],
  });

// ---------- Documento ----------
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Times New Roman", size: 24 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Times New Roman", color: "1F3864" },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Times New Roman", color: "2E5496" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "lista", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { run: { font: "Times New Roman" }, paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numerada", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
        style: { run: { font: "Times New Roman" }, paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [
    // Secção 1 — parte pré-textual. A capa (1.ª página) não mostra número;
    // as restantes páginas mostram um número de página simples e centrado.
    {
      properties: {
        titlePage: true,
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      footers: {
        first: rodapeVazio(),
        default: rodapeNumero(),
      },
      children: [...capa, ...epigrafe, ...organograma, ...indice],
    },
    // Secção 2 — corpo do relatório. A numeração continua de forma contínua,
    // com o mesmo rodapé de número simples e centrado.
    {
      properties: { page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      } },
      footers: { default: rodapeNumero() },
      children: [...corpo],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  const out = process.argv[2] || "Relatorio_BASI.docx";
  fs.writeFileSync(out, buffer);
  console.log("Gerado:", out, "(" + buffer.length + " bytes)");
});
