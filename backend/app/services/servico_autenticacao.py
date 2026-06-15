"""
servico_autenticacao.py — Regras de negócio de autenticação.

Responsável por: registar utilizadores, validar credenciais (login), emitir e
renovar tokens JWT. Lança HTTPException com os códigos correctos para o FastAPI
converter em respostas adequadas.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core import security
from app.models.user import Utilizador, PerfilUtilizador
from app.repositories.repositorio_utilizadores import RepositorioUtilizadores
from app.schemas.auth import RegistoPedido, LoginPedido, TokenResposta


class ServicoAutenticacao:
    def __init__(self, db: Session) -> None:
        self.repo = RepositorioUtilizadores(db)

    def registar(self, dados: RegistoPedido) -> Utilizador:
        # Regra: email único.
        if self.repo.obter_por_email(dados.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe uma conta com este email.",
            )
        # Regra de segurança: ninguém se auto-promove a administrador.
        perfil = dados.perfil
        if perfil == PerfilUtilizador.administrador:
            perfil = PerfilUtilizador.estudante

        utilizador = Utilizador(
            nome=dados.nome,
            email=dados.email,
            palavra_passe=security.hash_password(dados.palavra_passe),
            perfil=perfil,
            instituicao=dados.instituicao,
        )
        return self.repo.criar(utilizador)

    def autenticar(self, dados: LoginPedido) -> Utilizador:
        utilizador = self.repo.obter_por_email(dados.email)
        # Mensagem genérica (não revelar se o email existe — boa prática de segurança).
        erro = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou palavra-passe inválidos.",
        )
        if utilizador is None or not utilizador.activo:
            raise erro
        if not security.verify_password(dados.palavra_passe, utilizador.palavra_passe):
            raise erro
        return utilizador

    def emitir_tokens(self, utilizador: Utilizador) -> TokenResposta:
        """Gera o par access+refresh para um utilizador autenticado."""
        return TokenResposta(
            access_token=security.criar_access_token(
                subject=str(utilizador.id), perfil=utilizador.perfil.value
            ),
            refresh_token=security.criar_refresh_token(subject=str(utilizador.id)),
        )

    def renovar(self, refresh_token: str) -> TokenResposta:
        """Valida o refresh token e emite um novo par de tokens."""
        claims = security.descodificar_token(refresh_token)
        if claims is None or claims.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido ou expirado.",
            )
        utilizador = self.repo.obter_por_id(int(claims["sub"]))
        if utilizador is None or not utilizador.activo:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilizador inválido."
            )
        return self.emitir_tokens(utilizador)
