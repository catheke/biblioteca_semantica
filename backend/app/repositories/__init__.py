"""
Camada de repositórios: isola o acesso à base de dados.

Os serviços usam os repositórios em vez de falarem directamente com o SQLAlchemy,
concentrando as queries num único sítio.
"""
