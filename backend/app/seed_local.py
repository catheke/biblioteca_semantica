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

import urllib.request

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.core.pdf_livro import txt_para_pdf
from app.core.storage import caminho_capa, caminho_livro, url_capa
from app.models.academic import AreaCientifica, Tema
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

        # Livros de domínio público (Project Gutenberg), com capa e ligação para
        # leitura/descarga e níveis de acesso variados.
        # Tuplo: (id_gutenberg, titulo, autor, area, idioma, ano, nivel, genero).
        # `genero` só se aplica à Literatura; nas outras secções fica None.
        catalogo = [
            # Literatura — clássicos em português
            (55752, "Dom Casmurro", "Machado de Assis", literatura, "Português", 1899, NivelAcesso.publico, "Romance"),
            (54829, "Memórias Póstumas de Brás Cubas", "Machado de Assis", literatura, "Português", 1881, NivelAcesso.publico, "Romance"),
            (53101, "A Mão e a Luva", "Machado de Assis", literatura, "Português", 1874, NivelAcesso.publico, "Romance"),
            (3333, "Os Lusíadas", "Luís de Camões", literatura, "Português", 1572, NivelAcesso.publico, "Poesia"),
            (16384, "O Mandarim", "Eça de Queirós", literatura, "Português", 1880, NivelAcesso.publico, "Romance"),
            (67724, "O Guarani", "José de Alencar", literatura, "Português", 1857, NivelAcesso.publico, "Romance"),
            (27364, "A Filha do Arcediago", "Camilo Castelo Branco", literatura, "Português", 1854, NivelAcesso.autenticado, "Romance"),
            # Literatura — clássicos internacionais
            (1342, "Pride and Prejudice", "Jane Austen", literatura, "Inglês", 1813, NivelAcesso.publico, "Romance"),
            (996, "Don Quixote", "Miguel de Cervantes", literatura, "Espanhol", 1605, NivelAcesso.publico, "Romance"),
            (2554, "Crime and Punishment", "Fiódor Dostoiévski", literatura, "Inglês", 1866, NivelAcesso.autenticado, "Romance"),
            (64317, "The Great Gatsby", "F. Scott Fitzgerald", literatura, "Inglês", 1925, NivelAcesso.autenticado, "Romance"),
            (1661, "The Adventures of Sherlock Holmes", "Arthur Conan Doyle", literatura, "Inglês", 1892, NivelAcesso.publico, "Conto"),
            (84, "Frankenstein", "Mary Shelley", literatura, "Inglês", 1818, NivelAcesso.publico, "Romance"),
            (11, "Alice's Adventures in Wonderland", "Lewis Carroll", literatura, "Inglês", 1865, NivelAcesso.publico, "Romance"),
            # Filosofia
            (1497, "The Republic", "Platão", filosofia, "Inglês", None, NivelAcesso.academico, None),
            (1232, "The Prince", "Nicolau Maquiavel", filosofia, "Inglês", 1532, NivelAcesso.publico, None),
            (2680, "Meditations", "Marco Aurélio", filosofia, "Inglês", None, NivelAcesso.publico, None),
            # Ciência
            (1228, "On the Origin of Species", "Charles Darwin", ciencia, "Inglês", 1859, NivelAcesso.academico, None),
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
        print("A descarregar e a gerar os livros em PDF para storage/ ...")
        for doc, id_g in zip(docs_livros, ids_gutenberg):
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


if __name__ == "__main__":
    executar()
