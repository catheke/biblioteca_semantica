"""
servico_documentos.py — Regras de negócio dos documentos.

Coordena o repositório relacional (PostgreSQL) e, conceptualmente, o motor
semântico (a publicação de um documento também deveria inserir os triplos
correspondentes no Fuseki — deixado documentado no método `publicar`).
"""
from __future__ import annotations

import mimetypes
import shutil
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.storage import (
    EXTENSOES_PERMITIDAS,
    caminho_capa,
    caminho_livro,
    url_capa,
)
from app.models.document import Documento, TipoDocumento, NivelAcesso
from app.models.user import Utilizador, PerfilUtilizador
from app.repositories.repositorio_documentos import RepositorioDocumentos
from app.schemas.document import DocumentoCriar, DocumentoActualizar

# Perfis considerados "académicos" para efeitos de acesso restrito.
_PERFIS_ACADEMICOS = (
    PerfilUtilizador.professor,
    PerfilUtilizador.investigador,
    PerfilUtilizador.administrador,
)


class ServicoDocumentos:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RepositorioDocumentos(db)

    def _nome_area(self, area_id: Optional[int]) -> Optional[str]:
        """Devolve o nome da área (para os triplos RDF), se existir."""
        if not area_id:
            return None
        from app.models.academic import AreaCientifica

        area = self.db.get(AreaCientifica, area_id)
        return area.nome if area else None

    def listar(
        self,
        tipo=None,
        area_id=None,
        genero=None,
        q=None,
        autor=None,
        ano=None,
        pagina: int = 1,
        por_pagina: int = 20,
    ):
        deslocamento = (pagina - 1) * por_pagina
        itens = self.repo.listar(
            tipo=tipo,
            area_id=area_id,
            genero=genero,
            q=q,
            autor=autor,
            ano=ano,
            limite=por_pagina,
            deslocamento=deslocamento,
        )
        total = self.repo.contar(
            tipo=tipo, area_id=area_id, genero=genero, q=q, autor=autor, ano=ano
        )
        return itens, total

    def seccoes(self) -> list[dict]:
        """
        Devolve a ESTRUTURA da biblioteca: as secções (classes da CDU) com o nº
        de obras e, na Literatura, a repartição por género. É o que permite ao
        frontend desenhar as "estantes" navegáveis.
        """
        from app.core.cdu import CODIGO_LITERATURA, GENEROS_LITERATURA
        from app.models.academic import AreaCientifica

        por_area = self.repo.contagem_por_area()
        areas = list(self.db.scalars(select(AreaCientifica)).all())
        # Ordena pela cota CDU (código), deixando as sem código no fim.
        areas.sort(key=lambda a: (a.codigo is None, a.codigo or "", a.nome))

        seccoes: list[dict] = []
        for area in areas:
            generos: list[dict] = []
            if area.codigo == CODIGO_LITERATURA:
                por_genero = self.repo.contagem_por_genero(area.id)
                # Mantém a ordem fixa dos géneros (Romance, Conto, Poesia, Teatro).
                for nome, codigo in GENEROS_LITERATURA:
                    generos.append(
                        {"codigo": codigo, "nome": nome, "total": int(por_genero.get(nome, 0))}
                    )
            seccoes.append(
                {
                    "area_id": area.id,
                    "codigo": area.codigo,
                    "nome": area.nome,
                    "total": int(por_area.get(area.id, 0)),
                    "generos": generos,
                }
            )
        return seccoes

    def obter(self, doc_id: int) -> Documento:
        doc = self.repo.obter_por_id(doc_id)
        if doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado."
            )
        return doc

    def publicar(self, dados: DocumentoCriar, autor: Utilizador) -> Documento:
        # Regra: só professores/investigadores/admin podem publicar.
        if autor.perfil not in _PERFIS_ACADEMICOS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas professores, investigadores e administradores publicam.",
            )
        doc = Documento(
            titulo=dados.titulo,
            resumo=dados.resumo,
            tipo=dados.tipo,
            ano_publicacao=dados.ano_publicacao,
            idioma=dados.idioma,
            area_id=dados.area_id,
            autor_id=autor.id,
            autor_nome=dados.autor_nome,
            genero=dados.genero,
            ficheiro_url=dados.ficheiro_url,
            capa_url=dados.capa_url,
            nivel_acesso=dados.nivel_acesso,
        )
        doc = self.repo.criar(doc)
        # Atribui um IRI semântico estável baseado no id gerado.
        doc.uri_semantica = f"http://basi.ao/recurso/documento/doc{doc.id}"
        doc = self.repo.actualizar(doc)
        # Aviso global para os leitores (novo documento disponível).
        self._notificar_novo_documento(doc)
        # PASSO SEMÂNTICO (produção): aqui inserir-se-iam os triplos no Fuseki via
        # SPARQL UPDATE (titulo, temAutor, temTema...). Mantido como nota para
        # não acoplar a escrita de testes locais ao serviço RDF.
        return doc

    def _verificar_acesso(self, doc: Documento, utilizador: Optional[Utilizador]) -> None:
        """Aplica o NÍVEL DE ACESSO — é aqui que cada perfil vê coisas diferentes."""
        if doc.nivel_acesso == NivelAcesso.autenticado and utilizador is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inicie sessão para aceder a este documento.",
            )
        if doc.nivel_acesso == NivelAcesso.academico and (
            utilizador is None or utilizador.perfil not in _PERFIS_ACADEMICOS
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso reservado a professores, investigadores e administradores.",
            )

    def ficheiro_para_descarregar(
        self, doc_id: int, utilizador: Optional[Utilizador]
    ) -> tuple[Path, str, str]:
        """
        Verifica o acesso, conta o download e devolve o FICHEIRO LOCAL a servir:
        (caminho_absoluto, nome_para_o_utilizador, tipo_mime).
        O ficheiro está guardado dentro do projecto (backend/storage/livros),
        por isso a leitura/descarga acontece na própria aplicação — sem sair
        para sites externos.
        """
        doc = self.obter(doc_id)
        self._verificar_acesso(doc, utilizador)

        if not doc.ficheiro_objecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Este documento não tem ficheiro associado.",
            )
        caminho = caminho_livro(doc.ficheiro_objecto)
        if not caminho.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="O ficheiro deste documento não foi encontrado no servidor.",
            )

        doc.num_downloads += 1
        self.repo.actualizar(doc)

        mime = mimetypes.guess_type(caminho.name)[0] or "application/octet-stream"
        nome_visivel = f"{doc.titulo}{caminho.suffix}"
        return caminho, nome_visivel, mime

    def carregar(
        self,
        autor: Utilizador,
        ficheiro: UploadFile,
        titulo: str,
        tipo: TipoDocumento,
        nivel_acesso: NivelAcesso,
        autor_nome: Optional[str] = None,
        resumo: Optional[str] = None,
        ano_publicacao: Optional[int] = None,
        idioma: Optional[str] = "Português",
        area_id: Optional[int] = None,
        tema: Optional[str] = None,
        genero: Optional[str] = None,
        capa: Optional[UploadFile] = None,
    ) -> Documento:
        """
        Cria um documento E guarda o ficheiro carregado LOCALMENTE no projecto.
        Usado pelo painel de administração para adicionar livros à plataforma.
        """
        if autor.perfil not in _PERFIS_ACADEMICOS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas professores, investigadores e administradores publicam.",
            )

        extensao = Path(ficheiro.filename or "").suffix.lower()
        if extensao not in EXTENSOES_PERMITIDAS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Formato não permitido. Use: {', '.join(sorted(EXTENSOES_PERMITIDAS))}.",
            )

        # Cria primeiro a linha para obter um id estável; os ficheiros usam esse id.
        doc = Documento(
            titulo=titulo,
            resumo=resumo,
            tipo=tipo,
            ano_publicacao=ano_publicacao,
            idioma=idioma,
            area_id=area_id,
            autor_id=autor.id,
            autor_nome=autor_nome,
            genero=genero,
            nivel_acesso=nivel_acesso,
        )
        doc = self.repo.criar(doc)

        # Guarda o ficheiro da obra: storage/livros/{id}{extensao}
        nome_ficheiro = f"{doc.id}{extensao}"
        with open(caminho_livro(nome_ficheiro), "wb") as destino:
            shutil.copyfileobj(ficheiro.file, destino)
        doc.ficheiro_objecto = nome_ficheiro

        # Capa opcional: storage/capas/{id}{extensao_imagem}
        if capa is not None and capa.filename:
            ext_capa = Path(capa.filename).suffix.lower() or ".jpg"
            nome_capa = f"{doc.id}{ext_capa}"
            with open(caminho_capa(nome_capa), "wb") as destino:
                shutil.copyfileobj(capa.file, destino)
            doc.capa_url = url_capa(nome_capa)

        doc.uri_semantica = f"http://basi.ao/recurso/documento/doc{doc.id}"
        doc = self.repo.actualizar(doc)

        # Aviso global para os leitores (novo documento disponível).
        self._notificar_novo_documento(doc)

        # PASSO SEMÂNTICO: escreve os triplos no grafo RDF para que o documento
        # passe a ser encontrável pela pesquisa semântica e pelo SPARQL.
        self._sincronizar_rdf(doc, tema)
        return doc

    def _notificar_novo_documento(self, doc: Documento) -> None:
        """Cria um aviso global a anunciar a chegada de um novo documento."""
        try:
            from app.services.servico_actividade import ServicoActividade

            ServicoActividade(self.db).criar_notificacao(
                f"Novo documento disponível: {doc.titulo}", documento_id=doc.id
            )
        except Exception:  # noqa: BLE001 — o aviso nunca deve partir a publicação
            pass

    def _sincronizar_rdf(self, doc: Documento, tema: Optional[str] = None) -> None:
        """Reflecte o documento no grafo RDF (não rebenta se o motor falhar)."""
        try:
            from app.services.servico_semantico import servico_semantico

            servico_semantico.sincronizar_documento(
                uri=doc.uri_semantica,
                titulo=doc.titulo,
                tipo=getattr(doc.tipo, "value", str(doc.tipo)),
                resumo=doc.resumo,
                ano=doc.ano_publicacao,
                autor_nome=doc.autor_nome,
                area_nome=self._nome_area(doc.area_id),
                tema_nome=tema,
                genero_nome=getattr(doc, "genero", None),
                num_downloads=doc.num_downloads or 0,
            )
        except Exception:  # noqa: BLE001 — a escrita RDF nunca deve partir o upload
            pass

    def actualizar(self, doc_id: int, dados: DocumentoActualizar, utilizador: Utilizador) -> Documento:
        doc = self.obter(doc_id)
        self._garantir_dono_ou_admin(doc, utilizador)
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(doc, campo, valor)
        return self.repo.actualizar(doc)

    def eliminar(self, doc_id: int, utilizador: Utilizador) -> None:
        doc = self.obter(doc_id)
        self._garantir_dono_ou_admin(doc, utilizador)
        uri = doc.uri_semantica
        self.repo.eliminar(doc)
        # PASSO SEMÂNTICO: remove os triplos do grafo RDF (mantém SQL e RDF alinhados).
        if uri:
            try:
                from app.services.servico_semantico import servico_semantico

                servico_semantico.remover_documento(uri)
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    def _garantir_dono_ou_admin(doc: Documento, utilizador: Utilizador) -> None:
        """Só o autor do documento ou um administrador podem editá-lo/apagá-lo."""
        if (
            doc.autor_id != utilizador.id
            and utilizador.perfil != PerfilUtilizador.administrador
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissão sobre este documento.",
            )
