"""
routes_auth.py — Endpoints de autenticação.

  POST /api/v1/auth/register  -> criar conta
  POST /api/v1/auth/login     -> obter tokens (JSON ou form OAuth2)
  POST /api/v1/auth/refresh   -> renovar access token
  POST /api/v1/auth/logout    -> terminar sessão (lado do cliente)
  GET  /api/v1/auth/me        -> dados do utilizador autenticado
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import obter_utilizador_actual
from app.models.user import Utilizador
from app.schemas.auth import RegistoPedido, LoginPedido, TokenResposta, RefreshPedido
from app.schemas.user import UtilizadorPublico
from app.services.servico_autenticacao import ServicoAutenticacao

router = APIRouter()


@router.post("/register", response_model=TokenResposta, status_code=status.HTTP_201_CREATED)
def registar(dados: RegistoPedido, db: Session = Depends(get_db)) -> TokenResposta:
    """Cria uma conta e devolve imediatamente os tokens (auto-login)."""
    service = ServicoAutenticacao(db)
    utilizador = service.registar(dados)
    return service.emitir_tokens(utilizador)


@router.post("/login", response_model=TokenResposta)
def login(dados: LoginPedido, db: Session = Depends(get_db)) -> TokenResposta:
    """Login via JSON (usado pelo frontend)."""
    service = ServicoAutenticacao(db)
    utilizador = service.autenticar(dados)
    return service.emitir_tokens(utilizador)


@router.post("/login/form", response_model=TokenResposta, include_in_schema=False)
def login_form(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> TokenResposta:
    """
    Login compatível com o formulário OAuth2 (botão 'Authorize' do Swagger).
    O campo 'username' do formulário recebe o email.
    """
    service = ServicoAutenticacao(db)
    utilizador = service.autenticar(LoginPedido(email=form.username, palavra_passe=form.password))
    return service.emitir_tokens(utilizador)


@router.post("/refresh", response_model=TokenResposta)
def refresh(dados: RefreshPedido, db: Session = Depends(get_db)) -> TokenResposta:
    """Troca um refresh token válido por um novo par de tokens."""
    return ServicoAutenticacao(db).renovar(dados.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    """
    Logout. Com JWT sem estado, o logout faz-se descartando os tokens no cliente.
    (A revogação de refresh tokens server-side está modelada na tabela
    tokens_refresh para uma evolução futura.)
    """
    return None


@router.get("/me", response_model=UtilizadorPublico)
def quem_sou_eu(
    utilizador: Utilizador = Depends(obter_utilizador_actual),
) -> Utilizador:
    """Devolve o perfil do utilizador autenticado."""
    return utilizador
