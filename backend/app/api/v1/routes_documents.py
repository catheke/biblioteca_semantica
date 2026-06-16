"""
routes_documents.py — Documentos e atalhos por tipo (livros, artigos, teses).

  GET    /api/v1/documents            -> listar (filtros: tipo, area)
  POST   /api/v1/documents            -> publicar (professor/investigador/admin)
  GET    /api/v1/documents/{id}       -> detalhe (+conta visualização)
  PATCH  /api/v1/documents/{id}       -> editar (dono/admin)
  DELETE /api/v1/documents/{id}       -> apagar (dono/admin)
  GET    /api/v1/books    /articles   /thesis  -> atalhos por tipo (enunciado)
  GET    /api/v1/favorites            -> meus favoritos
  POST   /api/v1/documents/{id}/favorite | DELETE -> gerir favorito
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import obter_utilizador_actual, obter_utilizador_opcional
from app.models.document import TipoDocumento, NivelAcesso
from app.models.user import Utilizador
from app.repositories.repositorio_documentos import RepositorioDocumentos
from app.schemas.document import (
    DocumentoCriar,
    DocumentoActualizar,
    DocumentoResposta,
    PaginaResposta,
    SeccaoBiblioteca,
)
from app.services.servico_actividade import ServicoActividade
from app.services.servico_documentos import ServicoDocumentos

router = APIRouter()


def _pagina(itens, total, pagina, por_pagina):
    return PaginaResposta(total=total, pagina=pagina, por_pagina=por_pagina, itens=itens)


# ----------------------------- CRUD principal --------------------------------
@router.get("/documents", response_model=PaginaResposta[DocumentoResposta], tags=["Documentos"])
def listar_documentos(
    tipo: Optional[TipoDocumento] = None,
    area_id: Optional[int] = None,
    genero: Optional[str] = None,
    q: Optional[str] = Query(None, description="Texto no título ou resumo."),
    autor: Optional[str] = Query(None, description="Nome do autor da obra."),
    ano: Optional[int] = Query(None, description="Ano de publicação."),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    itens, total = ServicoDocumentos(db).listar(
        tipo=tipo,
        area_id=area_id,
        genero=genero,
        q=q,
        autor=autor,
        ano=ano,
        pagina=pagina,
        por_pagina=por_pagina,
    )
    return _pagina(itens, total, pagina, por_pagina)


@router.get("/library/sections", response_model=list[SeccaoBiblioteca], tags=["Biblioteca"])
def listar_seccoes(db: Session = Depends(get_db)):
    """
    Estrutura da biblioteca: as SECÇÕES (classes da CDU) com o nº de obras e,
    na Literatura, a repartição por GÉNERO. Alimenta as "estantes" navegáveis.
    """
    return ServicoDocumentos(db).seccoes()


@router.post("/documents", response_model=DocumentoResposta, status_code=status.HTTP_201_CREATED, tags=["Documentos"])
def publicar_documento(
    dados: DocumentoCriar,
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    return ServicoDocumentos(db).publicar(dados, utilizador)


@router.get("/documents/{doc_id}", response_model=DocumentoResposta, tags=["Documentos"])
def obter_documento(doc_id: int, db: Session = Depends(get_db)):
    service = ServicoDocumentos(db)
    doc = service.obter(doc_id)
    doc.num_visualizacoes += 1  # conta a visualização
    service.repo.actualizar(doc)
    return doc


@router.post(
    "/documents/upload",
    response_model=DocumentoResposta,
    status_code=status.HTTP_201_CREATED,
    tags=["Documentos"],
)
def carregar_documento(
    titulo: str = Form(...),
    tipo: TipoDocumento = Form(...),
    nivel_acesso: NivelAcesso = Form(NivelAcesso.publico),
    autor_nome: Optional[str] = Form(None),
    resumo: Optional[str] = Form(None),
    ano_publicacao: Optional[int] = Form(None),
    idioma: Optional[str] = Form("Português"),
    area_id: Optional[int] = Form(None),
    tema: Optional[str] = Form(None),
    genero: Optional[str] = Form(None),
    ficheiro: UploadFile = File(...),
    capa: Optional[UploadFile] = File(None),
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    """
    Adiciona um documento COM o ficheiro guardado LOCALMENTE no projecto
    (backend/storage/livros). Usado pelo painel de administração. O `tema` liga
    o documento à ontologia, tornando-o encontrável pela pesquisa semântica.
    """
    return ServicoDocumentos(db).carregar(
        autor=utilizador,
        ficheiro=ficheiro,
        titulo=titulo,
        tipo=tipo,
        nivel_acesso=nivel_acesso,
        autor_nome=autor_nome,
        resumo=resumo,
        ano_publicacao=ano_publicacao,
        idioma=idioma,
        area_id=area_id,
        tema=tema,
        genero=genero,
        capa=capa,
    )


@router.get("/documents/{doc_id}/download", tags=["Documentos"])
def descarregar_documento(
    doc_id: int,
    utilizador: Optional[Utilizador] = Depends(obter_utilizador_opcional),
    db: Session = Depends(get_db),
):
    """
    Serve o FICHEIRO LOCAL do documento (lê/descarrega na própria aplicação,
    sem sair para sites externos), respeitando o nível de acesso e contando
    o download.
    """
    caminho, nome, mime = ServicoDocumentos(db).ficheiro_para_descarregar(doc_id, utilizador)
    # Regista a leitura/descarga no histórico do utilizador (se houver sessão).
    if utilizador is not None:
        ServicoActividade(db).registar_leitura(utilizador.id, doc_id)
    return FileResponse(caminho, media_type=mime, filename=nome)


@router.patch("/documents/{doc_id}", response_model=DocumentoResposta, tags=["Documentos"])
def actualizar_documento(
    doc_id: int,
    dados: DocumentoActualizar,
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    return ServicoDocumentos(db).actualizar(doc_id, dados, utilizador)


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Documentos"])
def eliminar_documento(
    doc_id: int,
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    ServicoDocumentos(db).eliminar(doc_id, utilizador)
    return None


# --------------------- Atalhos por tipo (pedidos no enunciado) ---------------
@router.get("/books", response_model=PaginaResposta[DocumentoResposta], tags=["Livros"])
def listar_livros(pagina: int = Query(1, ge=1), por_pagina: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    itens, total = ServicoDocumentos(db).listar(tipo=TipoDocumento.livro, pagina=pagina, por_pagina=por_pagina)
    return _pagina(itens, total, pagina, por_pagina)


@router.get("/articles", response_model=PaginaResposta[DocumentoResposta], tags=["Artigos"])
def listar_artigos(pagina: int = Query(1, ge=1), por_pagina: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    itens, total = ServicoDocumentos(db).listar(tipo=TipoDocumento.artigo, pagina=pagina, por_pagina=por_pagina)
    return _pagina(itens, total, pagina, por_pagina)


@router.get("/thesis", response_model=PaginaResposta[DocumentoResposta], tags=["Teses"])
def listar_teses(pagina: int = Query(1, ge=1), por_pagina: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    itens, total = ServicoDocumentos(db).listar(tipo=TipoDocumento.tese, pagina=pagina, por_pagina=por_pagina)
    return _pagina(itens, total, pagina, por_pagina)


# ------------------------------- Favoritos -----------------------------------
@router.get("/favorites", response_model=list[DocumentoResposta], tags=["Favoritos"])
def meus_favoritos(
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    return RepositorioDocumentos(db).listar_favoritos(utilizador.id)


@router.post("/documents/{doc_id}/favorite", status_code=status.HTTP_204_NO_CONTENT, tags=["Favoritos"])
def adicionar_favorito(
    doc_id: int,
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    ServicoDocumentos(db).obter(doc_id)  # valida existência (404 se não existir)
    RepositorioDocumentos(db).adicionar_favorito(utilizador.id, doc_id)
    return None


@router.delete("/documents/{doc_id}/favorite", status_code=status.HTTP_204_NO_CONTENT, tags=["Favoritos"])
def remover_favorito(
    doc_id: int,
    utilizador: Utilizador = Depends(obter_utilizador_actual),
    db: Session = Depends(get_db),
):
    RepositorioDocumentos(db).remover_favorito(utilizador.id, doc_id)
    return None
