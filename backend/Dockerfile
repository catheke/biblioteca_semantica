# =============================================================================
# Dockerfile — Backend FastAPI (BASI)
# -----------------------------------------------------------------------------
# O contexto de build é a RAIZ do repositório (não a pasta backend/), para que a
# imagem inclua também a ontologia e os ficheiros RDF. Assim o backend consegue,
# no arranque, carregar o grafo no Fuseki e usar o grafo rdflib local de reserva.
#   docker build -f backend/Dockerfile .
# A instalação das dependências fica numa camada separada do código para
# aproveitar a cache do Docker.
# =============================================================================
FROM python:3.11-slim

# Evita ficheiros .pyc e garante logs sem buffer (úteis em contentores).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Dependências de sistema mínimas (psycopg precisa de libpq).
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# 1) Instalar dependências (camada cacheável).
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 2) Copiar o código da aplicação e os dados semânticos.
COPY backend/ .
COPY ontology/ /ontology/
COPY rdf/ /rdf/

EXPOSE 8000

# Arranca a API. Respeita a variável $PORT (usada por Render e outros PaaS);
# por omissão usa 8000. Em produção pode acrescentar --workers N.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
