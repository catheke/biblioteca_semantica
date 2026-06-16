// CapaLivro.tsx — Capa de um livro com cara de "estante real".
// Se o documento tiver uma imagem de capa (capa_url) usa-a; caso contrário,
// desenha uma capa gerada (gradiente + título + autor + lombada), para que TODA
// a obra tenha aspecto de livro e a biblioteca ganhe vida.

import { urlMedia } from "@/lib/api";
import type { Documento } from "@/types";

// Paletas de gradiente (lombada + capa). Escolhidas de forma determinística a
// partir do título, para que cada livro tenha sempre a mesma cor.
const PALETAS = [
  { de: "#1e3a8a", para: "#2563eb", lombada: "#172554" }, // azul
  { de: "#6d28d9", para: "#8b5cf6", lombada: "#4c1d95" }, // roxo
  { de: "#9a3412", para: "#ea580c", lombada: "#7c2d12" }, // laranja
  { de: "#065f46", para: "#10b981", lombada: "#064e3b" }, // verde
  { de: "#9f1239", para: "#e11d48", lombada: "#881337" }, // carmim
  { de: "#155e75", para: "#06b6d4", lombada: "#164e63" }, // ciano
  { de: "#854d0e", para: "#d98300", lombada: "#713f12" }, // dourado
  { de: "#3730a3", para: "#6366f1", lombada: "#312e81" }, // índigo
];

function hash(texto: string): number {
  let h = 0;
  for (let i = 0; i < texto.length; i++) {
    h = (h << 5) - h + texto.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

export default function CapaLivro({
  doc,
  className = "",
}: {
  doc: Pick<Documento, "titulo" | "autor_nome" | "capa_url" | "tipo">;
  className?: string;
}) {
  const base = "relative w-full overflow-hidden rounded-lg shadow-sm";

  // 1) Capa real (imagem) — quando existe.
  if (doc.capa_url) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={urlMedia(doc.capa_url)}
        alt={`Capa de ${doc.titulo}`}
        className={`${base} object-cover ${className}`}
        loading="lazy"
      />
    );
  }

  // 2) Capa gerada — gradiente + lombada + título/autor.
  const p = PALETAS[hash(doc.titulo) % PALETAS.length];
  return (
    <div
      className={`${base} flex flex-col justify-between p-3 text-white ${className}`}
      style={{
        background: `linear-gradient(135deg, ${p.de} 0%, ${p.para} 100%)`,
        borderLeft: `6px solid ${p.lombada}`,
      }}
      aria-label={`Capa de ${doc.titulo}`}
    >
      {/* brilho suave no topo */}
      <div
        className="pointer-events-none absolute inset-0 opacity-30"
        style={{
          background:
            "radial-gradient(120% 60% at 20% 0%, rgba(255,255,255,0.45), transparent 60%)",
        }}
      />
      <span className="relative text-[10px] font-semibold uppercase tracking-widest text-white/70">
        {doc.tipo?.replace("_", " ") ?? "livro"}
      </span>
      <div className="relative">
        <h3 className="line-clamp-4 text-sm font-bold leading-snug drop-shadow-sm">
          {doc.titulo}
        </h3>
        {doc.autor_nome && (
          <p className="mt-1.5 line-clamp-1 text-xs text-white/80">
            {doc.autor_nome}
          </p>
        )}
      </div>
      <span className="relative mt-2 inline-block h-0.5 w-8 rounded bg-white/50" />
    </div>
  );
}
