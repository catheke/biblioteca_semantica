// CartaoDocumento.tsx — Cartão visual que representa um documento numa lista.

import Link from "next/link";
import type { Documento } from "@/types";
import CapaLivro from "@/components/CapaLivro";

const CORES_TIPO: Record<string, string> = {
  livro: "bg-blue-50 text-primaria",
  artigo: "bg-purple-50 text-roxo",
  tese: "bg-amber-50 text-dourado",
  manual: "bg-green-50 text-green-700",
  monografia: "bg-pink-50 text-pink-700",
  apresentacao: "bg-cyan-50 text-cyan-700",
  material_didactico: "bg-gray-100 text-gray-700",
};

// Etiqueta do nível de acesso — mostra quem pode descarregar o ficheiro.
const ACESSO: Record<string, { texto: string; cor: string }> = {
  publico: { texto: "Público", cor: "bg-green-50 text-green-700" },
  autenticado: { texto: "Requer sessão", cor: "bg-amber-50 text-dourado" },
  academico: { texto: "Académico", cor: "bg-red-50 text-red-700" },
};

export default function CartaoDocumento({ doc }: { doc: Documento }) {
  const acesso = ACESSO[doc.nivel_acesso ?? "publico"];
  return (
    <Link href={`/documento/${doc.id}`} className="cartao group block overflow-hidden">
      <div className="mb-3 aspect-[3/4] w-full">
        <CapaLivro
          doc={doc}
          className="h-full transition group-hover:scale-[1.02]"
        />
      </div>
      <div className="mb-2 flex items-center justify-between">
        <span className={`chip ${CORES_TIPO[doc.tipo] ?? ""}`}>
          {doc.tipo.replace("_", " ")}
        </span>
        {doc.ano_publicacao && (
          <span className="text-xs text-gray-400">{doc.ano_publicacao}</span>
        )}
      </div>
      <h3 className="mb-1 font-semibold text-gray-800 line-clamp-2">
        {doc.titulo}
      </h3>
      {doc.autor_nome && (
        <p className="mb-1 text-sm font-medium text-gray-600">{doc.autor_nome}</p>
      )}
      {doc.resumo && (
        <p className="text-sm text-gray-500 line-clamp-2">{doc.resumo}</p>
      )}
      <div className="mt-3 flex items-center justify-between">
        <span className={`chip ${acesso.cor}`}>{acesso.texto}</span>
        <div className="flex gap-3 text-xs text-gray-400">
          <span>{doc.num_visualizacoes} vis.</span>
          <span>{doc.num_downloads} desc.</span>
        </div>
      </div>
    </Link>
  );
}
