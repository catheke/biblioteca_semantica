import type { Config } from "tailwindcss";

/**
 * tailwind.config.ts — Tema visual do BASI.
 *
 * Paleta de tema CLARO (fundo branco/azul claro), alinhada com a identidade
 * académica: azul principal, dourado de destaque e cinzentos suaves.
 */
const config: Config = {
  content: [
    "./src/app/**/*.{ts,tsx}",
    "./src/components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        fundo: "#f4f7fc",
        primaria: "#2563eb",
        "primaria-escura": "#1e40af",
        dourado: "#d98300",
        roxo: "#7c4dd6",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
