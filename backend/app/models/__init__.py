"""
Pacote de modelos ORM.

Importamos aqui todos os modelos para que, ao importar `app.models`, todas as
tabelas fiquem registadas no metadata da Base (necessário para create_all).
"""
from app.models.user import Utilizador, TokenRefresh
from app.models.academic import (
    AreaCientifica,
    Tema,
    PalavraChave,
    Universidade,
    Departamento,
    Curso,
)
from app.models.document import Documento
from app.models.social import Favorito, Seguidor
from app.models.circulacao import (
    Exemplar,
    Emprestimo,
    Reserva,
    Multa,
    EstadoExemplar,
    EstadoEmprestimo,
    EstadoReserva,
)

__all__ = [
    "Utilizador",
    "TokenRefresh",
    "AreaCientifica",
    "Tema",
    "PalavraChave",
    "Universidade",
    "Departamento",
    "Curso",
    "Documento",
    "Favorito",
    "Seguidor",
    "Exemplar",
    "Emprestimo",
    "Reserva",
    "Multa",
    "EstadoExemplar",
    "EstadoEmprestimo",
    "EstadoReserva",
]
