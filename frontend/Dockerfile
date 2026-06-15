# =============================================================================
# Dockerfile — Frontend Next.js (BASI)
# -----------------------------------------------------------------------------
# Build multi-stage: "deps" instala pacotes, "builder" compila, "runner" corre
# uma imagem mínima de produção (Next.js standalone).
# =============================================================================

# ---- Estágio 1: dependências ----
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# ---- Estágio 2: build ----
FROM node:20-alpine AS builder
WORKDIR /app
# O Next.js inlina as variáveis NEXT_PUBLIC_* no MOMENTO DO BUILD. Por isso o URL
# da API tem de ser passado como argumento de build (ex.: no Render, via env var
# marcada para o build). Por omissão aponta para o backend local.
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ---- Estágio 3: execução ----
FROM node:20-alpine AS runner
WORKDIR /app
# HOSTNAME=0.0.0.0 garante que o servidor aceita ligações externas; o PORT é
# respeitado pelo server.js do Next.js (o Render injecta a porta correcta).
ENV NODE_ENV=production \
    HOSTNAME=0.0.0.0 \
    PORT=3000
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
