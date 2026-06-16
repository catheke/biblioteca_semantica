"""
seed_local.py — Popula a base de dados (modo local) com dados de demonstração.

Ao contrário de database/seed.sql (específico do PostgreSQL e executado pelo
contentor), este script usa o ORM e funciona com QUALQUER base de dados
configurada — incluindo o SQLite local. Assim, quem não tiver Docker consegue
arrancar a API já com utilizadores, áreas, temas e documentos.

Inclui LIVROS REAIS de domínio público (Project Gutenberg) com capa e ligação
para leitura/descarga, e DOCUMENTOS técnicos que servem a demonstração da
PESQUISA SEMÂNTICA (Inteligência Artificial -> Machine Learning -> Deep
Learning...). Cada documento tem um NÍVEL DE ACESSO, para que perfis diferentes
vejam/descarreguem coisas diferentes.

EXECUTAR (a partir da pasta backend/, com o venv activo):
    python -m app.seed_local
"""
from __future__ import annotations

import os
import urllib.request

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.core.pdf_livro import txt_para_pdf
from app.core.storage import caminho_capa, caminho_livro, url_capa
from app.models.academic import AreaCientifica, Tema
from app.models.circulacao import (
    Emprestimo,
    EstadoEmprestimo,
    EstadoExemplar,
    EstadoReserva,
    Exemplar,
    Multa,
    Reserva,
)
from app.models.document import Documento, TipoDocumento, NivelAcesso
from app.models.social import Favorito, Seguidor
from app.models.user import Utilizador, PerfilUtilizador


def _baixar(url: str, destino) -> bool:
    """
    Descarrega `url` para o caminho `destino` (idempotente: salta se já existir).
    Devolve True se o ficheiro ficou disponível. Em caso de falha de rede, devolve
    False e o seed continua (o documento fica sem ficheiro associado).
    """
    if destino.exists() and destino.stat().st_size > 0:
        return True
    try:
        pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (BASI-seed)"})
        with urllib.request.urlopen(pedido, timeout=60) as resposta:
            dados = resposta.read()
        if not dados:
            return False
        with open(destino, "wb") as ficheiro:
            ficheiro.write(dados)
        return True
    except Exception as erro:  # noqa: BLE001 (queremos continuar mesmo com falhas)
        print(f"  ! falha ao descarregar {url}: {erro}")
        return False


# --- Catálogo de livros de domínio público (Project Gutenberg) --------------
# Tuplo: (id_gutenberg, titulo, autor, codigo_cdu, idioma, ano, nivel, genero).
# `codigo_cdu` identifica a SECÇÃO (área) e `genero` só se aplica à Literatura.
# Mantido ao nível do módulo para que tanto o seed inicial (`executar`) como o
# seed aditivo (`semear_livros_em_falta`) partilhem a MESMA lista.
CATALOGO: list[tuple] = [
    # Literatura — clássicos em português
    (55752, "Dom Casmurro", "Machado de Assis", "82", "Português", 1899, NivelAcesso.publico, "Romance"),
    (54829, "Memórias Póstumas de Brás Cubas", "Machado de Assis", "82", "Português", 1881, NivelAcesso.publico, "Romance"),
    (53101, "A Mão e a Luva", "Machado de Assis", "82", "Português", 1874, NivelAcesso.publico, "Romance"),
    (3333, "Os Lusíadas", "Luís de Camões", "82", "Português", 1572, NivelAcesso.publico, "Poesia"),
    (16384, "O Mandarim", "Eça de Queirós", "82", "Português", 1880, NivelAcesso.publico, "Romance"),
    (67724, "O Guarani", "José de Alencar", "82", "Português", 1857, NivelAcesso.publico, "Romance"),
    (27364, "A Filha do Arcediago", "Camilo Castelo Branco", "82", "Português", 1854, NivelAcesso.autenticado, "Romance"),
    # Literatura — clássicos internacionais
    (1342, "Pride and Prejudice", "Jane Austen", "82", "Inglês", 1813, NivelAcesso.publico, "Romance"),
    (996, "Don Quixote", "Miguel de Cervantes", "82", "Espanhol", 1605, NivelAcesso.publico, "Romance"),
    (2554, "Crime and Punishment", "Fiódor Dostoiévski", "82", "Inglês", 1866, NivelAcesso.autenticado, "Romance"),
    (64317, "The Great Gatsby", "F. Scott Fitzgerald", "82", "Inglês", 1925, NivelAcesso.autenticado, "Romance"),
    (1661, "The Adventures of Sherlock Holmes", "Arthur Conan Doyle", "82", "Inglês", 1892, NivelAcesso.publico, "Conto"),
    (84, "Frankenstein", "Mary Shelley", "82", "Inglês", 1818, NivelAcesso.publico, "Romance"),
    (11, "Alice's Adventures in Wonderland", "Lewis Carroll", "82", "Inglês", 1865, NivelAcesso.publico, "Romance"),
    (174, "The Picture of Dorian Gray", "Oscar Wilde", "82", "Inglês", 1890, NivelAcesso.publico, "Romance"),
    (345, "Dracula", "Bram Stoker", "82", "Inglês", 1897, NivelAcesso.publico, "Romance"),
    (1260, "Jane Eyre", "Charlotte Brontë", "82", "Inglês", 1847, NivelAcesso.publico, "Romance"),
    (768, "Wuthering Heights", "Emily Brontë", "82", "Inglês", 1847, NivelAcesso.autenticado, "Romance"),
    (98, "A Tale of Two Cities", "Charles Dickens", "82", "Inglês", 1859, NivelAcesso.publico, "Romance"),
    (1400, "Great Expectations", "Charles Dickens", "82", "Inglês", 1861, NivelAcesso.publico, "Romance"),
    (2701, "Moby Dick", "Herman Melville", "82", "Inglês", 1851, NivelAcesso.autenticado, "Romance"),
    (1184, "The Count of Monte Cristo", "Alexandre Dumas", "82", "Inglês", 1844, NivelAcesso.publico, "Romance"),
    (74, "The Adventures of Tom Sawyer", "Mark Twain", "82", "Inglês", 1876, NivelAcesso.publico, "Romance"),
    (76, "Adventures of Huckleberry Finn", "Mark Twain", "82", "Inglês", 1884, NivelAcesso.publico, "Romance"),
    (16, "Peter Pan", "J. M. Barrie", "82", "Inglês", 1911, NivelAcesso.publico, "Romance"),
    (5200, "A Metamorfose", "Franz Kafka", "82", "Inglês", 1915, NivelAcesso.publico, "Conto"),
    (1952, "The Yellow Wallpaper", "Charlotte Perkins Gilman", "82", "Inglês", 1892, NivelAcesso.publico, "Conto"),
    (2591, "Contos de Grimm", "Irmãos Grimm", "82", "Inglês", 1812, NivelAcesso.publico, "Conto"),
    (1727, "The Odyssey", "Homero", "82", "Inglês", None, NivelAcesso.autenticado, "Poesia"),
    (6130, "The Iliad", "Homero", "82", "Inglês", None, NivelAcesso.autenticado, "Poesia"),
    (1322, "Leaves of Grass", "Walt Whitman", "82", "Inglês", 1855, NivelAcesso.publico, "Poesia"),
    (1524, "Hamlet", "William Shakespeare", "82", "Inglês", 1603, NivelAcesso.publico, "Teatro"),
    (1513, "Romeu e Julieta", "William Shakespeare", "82", "Inglês", 1597, NivelAcesso.publico, "Teatro"),
    # Filosofia
    (1497, "The Republic", "Platão", "1", "Inglês", None, NivelAcesso.academico, None),
    (1232, "The Prince", "Nicolau Maquiavel", "1", "Inglês", 1532, NivelAcesso.publico, None),
    (2680, "Meditations", "Marco Aurélio", "1", "Inglês", None, NivelAcesso.publico, None),
    (1998, "Thus Spake Zarathustra", "Friedrich Nietzsche", "1", "Inglês", 1883, NivelAcesso.academico, None),
    (4363, "Beyond Good and Evil", "Friedrich Nietzsche", "1", "Inglês", 1886, NivelAcesso.academico, None),
    (1080, "A Modest Proposal", "Jonathan Swift", "1", "Inglês", 1729, NivelAcesso.publico, None),
    # Ciência
    (1228, "On the Origin of Species", "Charles Darwin", "5", "Inglês", 1859, NivelAcesso.academico, None),
    (5001, "Relativity: The Special and General Theory", "Albert Einstein", "5", "Inglês", 1916, NivelAcesso.academico, None),
    (37729, "Treatise on Light", "Christiaan Huygens", "5", "Inglês", 1690, NivelAcesso.academico, None),
    (33283, "The Principles of Chemistry", "Dmitri Mendeleev", "5", "Inglês", 1868, NivelAcesso.academico, None),
]


def _descarregar_ficheiros(doc: Documento, id_g: int, descarregar: bool) -> None:
    """
    Descarrega o PDF de leitura e a capa do livro Gutenberg `id_g` para o
    documento `doc` (idempotente). Respeita SEED_DOWNLOAD_LIVROS via `descarregar`.
    """
    if not descarregar:
        return
    url_txt = f"https://www.gutenberg.org/cache/epub/{id_g}/pg{id_g}.txt"
    origem_txt = caminho_livro(f"{doc.id}.txt")  # texto-fonte (intermédio)
    destino_pdf = caminho_livro(f"{doc.id}.pdf")
    if destino_pdf.exists() and destino_pdf.stat().st_size > 0:
        # Já temos o PDF de leitura (ex.: re-seed) — não voltar a descarregar.
        doc.ficheiro_objecto = f"{doc.id}.pdf"
    elif _baixar(url_txt, origem_txt):
        if txt_para_pdf(origem_txt, destino_pdf, doc.titulo, doc.autor_nome or ""):
            doc.ficheiro_objecto = f"{doc.id}.pdf"
        # Remove o texto-fonte; ficamos só com o PDF de leitura.
        try:
            origem_txt.unlink()
        except OSError:
            pass

    url_capa_g = f"https://www.gutenberg.org/cache/epub/{id_g}/pg{id_g}.cover.medium.jpg"
    nome_capa = f"{doc.id}.jpg"
    if _baixar(url_capa_g, caminho_capa(nome_capa)):
        doc.capa_url = url_capa(nome_capa)
    print(f"  · {doc.titulo[:40]:40s} -> pdf={'ok' if doc.ficheiro_objecto else '—'} capa={'ok' if doc.capa_url else '—'}")


def executar() -> None:
    init_db()
    db = SessionLocal()
    try:
        # Evita duplicar se já houver dados.
        if db.query(Utilizador).first() is not None:
            print("Base de dados já contém dados — seed ignorado.")
            return

        # --- Secções da biblioteca (classes da CDU) ---
        # Cada área é uma SECÇÃO com a sua cota CDU, como as estantes de uma
        # biblioteca real. A Literatura (82) subdivide-se depois por género.
        informatica = AreaCientifica(codigo="0", nome="Informática e Generalidades", uri_semantica="http://basi.ao/recurso/cdu/0")
        filosofia = AreaCientifica(codigo="1", nome="Filosofia e Psicologia", uri_semantica="http://basi.ao/recurso/cdu/1")
        ciencia = AreaCientifica(codigo="5", nome="Ciências Naturais e Matemática", uri_semantica="http://basi.ao/recurso/cdu/5")
        medicina = AreaCientifica(codigo="6", nome="Ciências Aplicadas e Medicina", uri_semantica="http://basi.ao/recurso/cdu/6")
        literatura = AreaCientifica(codigo="82", nome="Literatura", uri_semantica="http://basi.ao/recurso/cdu/82")
        db.add_all([informatica, filosofia, ciencia, medicina, literatura])
        db.flush()  # obtém os ids gerados

        # --- Temas (com hierarquia, base da inferência semântica) ---
        ia = Tema(nome="Inteligência Artificial", area_id=informatica.id, uri_semantica="http://basi.ao/recurso/tema/ia")
        db.add(ia)
        db.flush()
        ml = Tema(nome="Machine Learning", area_id=informatica.id, tema_pai_id=ia.id)
        db.add(ml)
        db.flush()
        db.add_all([
            Tema(nome="Deep Learning", area_id=informatica.id, tema_pai_id=ml.id),
            Tema(nome="Redes Neurais", area_id=informatica.id, tema_pai_id=ml.id),
            Tema(nome="Web Semântica", area_id=informatica.id, tema_pai_id=ia.id),
            Tema(nome="Cardiologia", area_id=medicina.id),
        ])
        # NB: na Literatura não usamos "temas" — a arrumação é por GÉNERO
        # (campo `genero` do documento), seguindo os auxiliares de forma da CDU.

        # --- Utilizadores (palavra-passe de todos: "password123") ---
        pw = hash_password("password123")
        admin = Utilizador(nome="Administrador BASI", email="admin@basi.ao", palavra_passe=pw, perfil=PerfilUtilizador.administrador, email_validado=True)
        adriano = Utilizador(nome="Prof. Adriano De Júlio", email="adriano@basi.ao", palavra_passe=pw, perfil=PerfilUtilizador.professor, email_validado=True)
        filipe = Utilizador(nome="Prof. Filipe Tchivela", email="filipe@basi.ao", palavra_passe=pw, perfil=PerfilUtilizador.professor, email_validado=True)
        pedro = Utilizador(nome="Inv. Pedro Calenga", email="pedro@basi.ao", palavra_passe=pw, perfil=PerfilUtilizador.investigador, email_validado=True)
        maria = Utilizador(nome="Estudante Maria Sousa", email="maria@basi.ao", palavra_passe=pw, perfil=PerfilUtilizador.estudante, email_validado=True)
        db.add_all([admin, adriano, filipe, pedro, maria])
        db.flush()

        # Documentos técnicos para a demonstração da pesquisa semântica
        # (sem ficheiro real; o foco é a inferência por temas).
        docs_tecnicos = [
            Documento(titulo="Introdução à Inteligência Artificial", resumo="Fundamentos de IA.", tipo=TipoDocumento.livro, ano_publicacao=2023, autor_id=adriano.id, area_id=informatica.id, autor_nome="Adriano De Júlio", nivel_acesso=NivelAcesso.publico),
            Documento(titulo="Aprendizagem Profunda Aplicada", resumo="Redes neuronais e Deep Learning.", tipo=TipoDocumento.artigo, ano_publicacao=2024, autor_id=adriano.id, area_id=informatica.id, autor_nome="Adriano De Júlio", nivel_acesso=NivelAcesso.autenticado),
            Documento(titulo="Web Semântica e Ontologias OWL", resumo="RDF, OWL e SPARQL.", tipo=TipoDocumento.tese, ano_publicacao=2024, autor_id=filipe.id, area_id=informatica.id, autor_nome="Filipe Tchivela", nivel_acesso=NivelAcesso.academico),
            Documento(titulo="Visão Computacional com Python", resumo="Processamento de imagem.", tipo=TipoDocumento.manual, ano_publicacao=2023, autor_id=pedro.id, area_id=informatica.id, autor_nome="Pedro Calenga", nivel_acesso=NivelAcesso.publico),
            Documento(titulo="Fundamentos de Cardiologia", resumo="Patologias cardíacas.", tipo=TipoDocumento.livro, ano_publicacao=2022, autor_id=filipe.id, area_id=medicina.id, autor_nome="Filipe Tchivela", nivel_acesso=NivelAcesso.academico),
            Documento(titulo="Ciência de Dados para Iniciantes", resumo="Pandas e visualização.", tipo=TipoDocumento.material_didactico, ano_publicacao=2024, autor_id=pedro.id, area_id=informatica.id, autor_nome="Pedro Calenga", nivel_acesso=NivelAcesso.autenticado),
            Documento(titulo="Processamento de Linguagem Natural com Transformers", resumo="Modelos de atenção e tradução automática.", tipo=TipoDocumento.artigo, ano_publicacao=2024, autor_id=pedro.id, area_id=informatica.id, autor_nome="Pedro Calenga", nivel_acesso=NivelAcesso.autenticado),
            Documento(titulo="Big Data e Engenharia de Dados", resumo="Sistemas distribuídos e pipelines de dados.", tipo=TipoDocumento.livro, ano_publicacao=2023, autor_id=filipe.id, area_id=informatica.id, autor_nome="Filipe Tchivela", nivel_acesso=NivelAcesso.publico),
            Documento(titulo="Redes Neurais para Diagnóstico de Doenças Cardíacas", resumo="Aprendizagem profunda aplicada a electrocardiogramas.", tipo=TipoDocumento.tese, ano_publicacao=2024, autor_id=adriano.id, area_id=informatica.id, autor_nome="Adriano De Júlio", nivel_acesso=NivelAcesso.academico),
            Documento(titulo="Deep Learning aplicado à Visão Computacional", resumo="Detecção e segmentação de objectos.", tipo=TipoDocumento.artigo, ano_publicacao=2023, autor_id=pedro.id, area_id=informatica.id, autor_nome="Pedro Calenga", nivel_acesso=NivelAcesso.publico),
            Documento(titulo="Grafos de Conhecimento e Consultas SPARQL", resumo="Ontologias, RDF e interrogação com SPARQL.", tipo=TipoDocumento.manual, ano_publicacao=2024, autor_id=filipe.id, area_id=informatica.id, autor_nome="Filipe Tchivela", nivel_acesso=NivelAcesso.autenticado),
            Documento(titulo="Ética e Aprendizagem por Reforço", resumo="Agentes autónomos, recompensas e ética da IA.", tipo=TipoDocumento.material_didactico, ano_publicacao=2024, autor_id=adriano.id, area_id=informatica.id, autor_nome="Adriano De Júlio", nivel_acesso=NivelAcesso.publico),
        ]

        # Livros de domínio público (Project Gutenberg) — ver constante CATALOGO
        # no topo do módulo. Aqui mapeamos o código da CDU para a área criada.
        area_por_codigo = {
            "0": informatica,
            "1": filosofia,
            "5": ciencia,
            "6": medicina,
            "82": literatura,
        }
        catalogo = [
            (id_g, titulo, autor, area_por_codigo[cod], idioma, ano, nivel, genero)
            for (id_g, titulo, autor, cod, idioma, ano, nivel, genero) in CATALOGO
        ]

        # Distribui os livros pelos professores/investigador como "quem publicou".
        publicadores = [adriano, filipe, pedro]
        docs_livros = []
        ids_gutenberg = []  # paralelo a docs_livros, para descarregar os ficheiros
        for i, (id_g, titulo, autor_real, area, idioma, ano, nivel, genero) in enumerate(catalogo):
            docs_livros.append(Documento(
                titulo=titulo,
                resumo=f"Obra de {autor_real}. Texto integral de domínio público.",
                tipo=TipoDocumento.livro,
                ano_publicacao=ano,
                idioma=idioma,
                autor_id=publicadores[i % len(publicadores)].id,
                area_id=area.id,
                autor_nome=autor_real,
                genero=genero,
                nivel_acesso=nivel,
            ))
            ids_gutenberg.append(id_g)

        docs = docs_tecnicos + docs_livros
        db.add_all(docs)
        db.flush()
        for d in docs:
            d.uri_semantica = f"http://basi.ao/recurso/documento/doc{d.id}"

        # --- Descarrega os FICHEIROS REAIS e guarda-os LOCALMENTE no projecto ---
        # Texto integral é descarregado e CONVERTIDO num PDF de leitura:
        #   storage/livros/{id}.pdf  (página de rosto + corpo paginado)
        # Capa (.jpg)              -> storage/capas/{id}.jpg
        #
        # Pode ser DESLIGADO com SEED_DOWNLOAD_LIVROS=0 — útil em alojamentos
        # gratuitos (ex.: Render) onde o disco é efémero e a descarga no arranque
        # atrasaria o serviço. Sem os ficheiros, o catálogo e a pesquisa semântica
        # funcionam na mesma; apenas a descarga das obras fica indisponível.
        descarregar = os.getenv("SEED_DOWNLOAD_LIVROS", "1") not in ("0", "false", "False")
        if not descarregar:
            print("SEED_DOWNLOAD_LIVROS=0 — a saltar a descarga dos livros (só metadados).")
        for doc, id_g in zip(docs_livros, ids_gutenberg):
            _descarregar_ficheiros(doc, id_g, descarregar)

        # --- Rede social (favoritos e seguidores de demonstração) ---
        db.add_all([
            Favorito(utilizador_id=maria.id, documento_id=docs[0].id),
            Favorito(utilizador_id=maria.id, documento_id=docs_livros[0].id),  # Dom Casmurro
            Favorito(utilizador_id=maria.id, documento_id=docs_livros[7].id),  # Pride and Prejudice
            Seguidor(seguidor_id=maria.id, seguido_id=adriano.id),
            Seguidor(seguidor_id=maria.id, seguido_id=filipe.id),
        ])

        db.commit()
        print(f"Seed concluído: 5 utilizadores, {len(docs)} documentos "
              f"({len(docs_livros)} livros reais), 5 secções CDU, 6 temas.")
        print("Login de demonstração -> email: admin@basi.ao | palavra-passe: password123")
    finally:
        db.close()


def semear_livros_em_falta() -> None:
    """
    Acrescenta ao catálogo os livros de domínio público (CATALOGO) que ainda NÃO
    existam na base de dados — de forma IDEMPOTENTE.

    Ao contrário de `executar()` (que só popula uma base VAZIA), esta função corre
    SEMPRE e serve para introduzir livros NOVOS em bases já povoadas — por exemplo,
    em produção, após um deploy que traga obras adicionais. A comparação é feita
    pelo título, pelo que livros já presentes nunca são duplicados.
    """
    init_db()
    db = SessionLocal()
    try:
        areas = {a.codigo: a for a in db.query(AreaCientifica).all()}
        publicadores = [
            db.query(Utilizador).filter(Utilizador.email == email).first()
            for email in ("adriano@basi.ao", "filipe@basi.ao", "pedro@basi.ao")
        ]
        publicadores = [p for p in publicadores if p is not None]
        # Sem áreas nem publicadores a base ainda não foi semeada; nada a fazer
        # (o seed inicial trata da primeira população).
        if not areas or not publicadores:
            return

        existentes = {titulo for (titulo,) in db.query(Documento.titulo).all()}
        descarregar = os.getenv("SEED_DOWNLOAD_LIVROS", "1") not in ("0", "false", "False")

        novos: list[Documento] = []
        novos_ids_g: list[int] = []
        i = 0
        for (id_g, titulo, autor, cod, idioma, ano, nivel, genero) in CATALOGO:
            if titulo in existentes:
                continue
            area = areas.get(cod)
            if area is None:
                continue
            novos.append(Documento(
                titulo=titulo,
                resumo=f"Obra de {autor}. Texto integral de domínio público.",
                tipo=TipoDocumento.livro,
                ano_publicacao=ano,
                idioma=idioma,
                autor_id=publicadores[i % len(publicadores)].id,
                area_id=area.id,
                autor_nome=autor,
                genero=genero,
                nivel_acesso=nivel,
            ))
            novos_ids_g.append(id_g)
            i += 1

        if not novos:
            print("Catálogo já actualizado — nenhum livro novo a acrescentar.")
            return

        db.add_all(novos)
        db.flush()
        for d in novos:
            d.uri_semantica = f"http://basi.ao/recurso/documento/doc{d.id}"
        for doc, id_g in zip(novos, novos_ids_g):
            _descarregar_ficheiros(doc, id_g, descarregar)

        db.commit()
        print(f"Acrescentados {len(novos)} livros novos ao catálogo.")
    finally:
        db.close()


def semear_circulacao() -> None:
    """
    Popula a CIRCULAÇÃO (exemplares, empréstimos, reservas e multas) com dados
    de demonstração. É IDEMPOTENTE em duas frentes:

      1. Exemplares: cada documento que ainda não tenha exemplares recebe alguns
         (assim, novos documentos passam a ter cópias requisitáveis sem mexer nos
         existentes). Usa-se a numeração `BASI-{doc:04d}-{n:02d}`.
      2. Movimentos demonstrativos (empréstimos/reservas/multas): só são criados
         UMA vez — quando ainda não existe nenhum empréstimo na base. Mostram o
         sistema "vivo": um empréstimo a decorrer, um em atraso (com multa) e uma
         obra esgotada com lista de espera.

    Esta função é chamada no arranque (bootstrap) a seguir ao seed base, e pode
    ser executada à parte com `python -m app.seed_local circulacao`.
    """
    from datetime import datetime, timedelta, timezone

    init_db()
    db = SessionLocal()
    try:
        documentos = db.query(Documento).order_by(Documento.id).all()
        if not documentos:
            print("Sem documentos — circulação ignorada (corra o seed base primeiro).")
            return

        # --- 1) Exemplares para documentos que ainda não os tenham ---------
        criados = 0
        for doc in documentos:
            ja_tem = db.query(Exemplar).filter(Exemplar.documento_id == doc.id).count()
            if ja_tem:
                continue
            # 2 exemplares por obra (suficiente para demonstrar fila de espera).
            for n in range(1, 3):
                db.add(Exemplar(
                    documento_id=doc.id,
                    numero_registo=f"BASI-{doc.id:04d}-{n:02d}",
                    estado=EstadoExemplar.disponivel,
                    localizacao="Estante Geral",
                ))
                criados += 1
        if criados:
            db.commit()
            print(f"Circulação: {criados} exemplares criados.")

        # --- 2) Movimentos demonstrativos (uma única vez) ------------------
        if db.query(Emprestimo).first() is not None:
            print("Circulação já tem movimentos — demonstração ignorada.")
            return

        def _u(email: str):
            return db.query(Utilizador).filter(Utilizador.email == email).first()

        maria = _u("maria@basi.ao")        # estudante
        pedro = _u("pedro@basi.ao")        # investigador
        adriano = _u("adriano@basi.ao")    # professor
        filipe = _u("filipe@basi.ao")      # professor
        if not all([maria, pedro, adriano]):
            print("Utilizadores de demonstração em falta — movimentos ignorados.")
            return

        agora = datetime.now(timezone.utc)

        def _exemplar_livre(documento_id: int):
            return (
                db.query(Exemplar)
                .filter(
                    Exemplar.documento_id == documento_id,
                    Exemplar.estado == EstadoExemplar.disponivel,
                )
                .first()
            )

        def _emprestar(leitor, documento_id, *, dias_decorridos, prazo_dias):
            ex = _exemplar_livre(documento_id)
            if ex is None:
                return None
            inicio = agora - timedelta(days=dias_decorridos)
            previsto = inicio + timedelta(days=prazo_dias)
            atrasado = previsto < agora
            ex.estado = EstadoExemplar.emprestado
            emp = Emprestimo(
                exemplar_id=ex.id,
                utilizador_id=leitor.id,
                data_emprestimo=inicio,
                data_prevista_devolucao=previsto,
                estado=EstadoEmprestimo.atrasado if atrasado else EstadoEmprestimo.activo,
            )
            db.add(emp)
            db.flush()
            return emp

        # (a) Empréstimo a decorrer, dentro do prazo (Maria, estudante).
        _emprestar(maria, documentos[0].id, dias_decorridos=3, prazo_dias=14)

        # (b) Empréstimo EM ATRASO -> gera multa por pagar (Pedro, investigador).
        em_atraso = _emprestar(pedro, documentos[1].id, dias_decorridos=40, prazo_dias=30)
        if em_atraso is not None:
            dias = (agora - _aware(em_atraso.data_prevista_devolucao)).days
            if dias > 0:
                db.add(Multa(
                    emprestimo_id=em_atraso.id,
                    utilizador_id=em_atraso.utilizador_id,
                    dias_atraso=dias,
                    valor=dias * 100.0,  # 100 Kz/dia (ver MULTA_POR_DIA no serviço)
                    paga=False,
                ))

        # (c) Obra ESGOTADA com lista de espera: emprestam-se os 2 exemplares e
        #     ficam reservas em fila.
        esgotada = documentos[2]
        _emprestar(adriano, esgotada.id, dias_decorridos=2, prazo_dias=30)
        _emprestar(filipe or adriano, esgotada.id, dias_decorridos=1, prazo_dias=30)
        # Maria e Pedro entram na fila de espera dessa obra.
        db.add(Reserva(
            documento_id=esgotada.id,
            utilizador_id=maria.id,
            data_reserva=agora - timedelta(hours=5),
            estado=EstadoReserva.activa,
        ))
        db.add(Reserva(
            documento_id=esgotada.id,
            utilizador_id=pedro.id,
            data_reserva=agora - timedelta(hours=2),
            estado=EstadoReserva.activa,
        ))

        db.commit()
        print("Circulação: movimentos de demonstração criados "
              "(1 empréstimo activo, 1 em atraso com multa, 1 obra esgotada com fila).")
    finally:
        db.close()


def _aware(dt):
    """Garante que um datetime tem fuso horário (UTC) para comparações seguras."""
    from datetime import timezone

    if dt is None:
        return dt
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "circulacao":
        semear_circulacao()
    else:
        executar()
        semear_circulacao()
