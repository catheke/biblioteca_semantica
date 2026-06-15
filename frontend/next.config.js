/**
 * next.config.js — Configuração do Next.js.
 *
 * `output: "standalone"` gera uma build auto-contida (com um server.js mínimo),
 * ideal para a imagem Docker de produção (ver frontend/Dockerfile).
 */
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
};

module.exports = nextConfig;
