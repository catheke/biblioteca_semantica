#!/usr/bin/env bash
# =============================================================================
# carregar_ontologia.sh — Carrega a ontologia + dados RDF no Apache Jena Fuseki.
# -----------------------------------------------------------------------------
# Envia os ficheiros Turtle para o dataset "basi" via a API HTTP do Fuseki.
# Pré-requisito: o serviço Fuseki tem de estar a correr (docker compose up).
#
# USO:   ./scripts/carregar_ontologia.sh
# =============================================================================
set -euo pipefail

FUSEKI_URL="${FUSEKI_URL:-http://localhost:3030}"
DATASET="${FUSEKI_DATASET:-basi}"
ADMIN_PASS="${FUSEKI_ADMIN_PASSWORD:-admin}"
DATA_ENDPOINT="${FUSEKI_URL}/${DATASET}/data"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ">> A carregar a ONTOLOGIA (TBox) para ${DATA_ENDPOINT} ..."
curl -sf -u "admin:${ADMIN_PASS}" \
     -H "Content-Type: text/turtle" \
     --data-binary "@${DIR}/ontology/basi.ttl" \
     "${DATA_ENDPOINT}?default" \
  && echo "   OK: ontologia carregada."

echo ">> A carregar os DADOS de exemplo (ABox) ..."
curl -sf -u "admin:${ADMIN_PASS}" \
     -H "Content-Type: text/turtle" \
     --data-binary "@${DIR}/rdf/dados_exemplo.ttl" \
     "${DATA_ENDPOINT}?default" \
  && echo "   OK: dados de exemplo carregados."

echo ">> Concluído. Experimente uma consulta em ${FUSEKI_URL}/#/dataset/${DATASET}/query"
