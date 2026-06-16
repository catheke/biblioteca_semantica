"use client";
// pesquisa/page.tsx — Pesquisa por título/resumo com recurso à camada semântica.
// Procura primeiro no texto (títulos/resumos). Se não encontrar nada, recorre
// automaticamente à pesquisa por significado (temas e subtemas relacionados),
// para que o utilizador receba sempre resultados úteis.

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { ResultadoPesquisa } from "@/types";

type Origem = "texto" | "semantica";

export default function PaginaPesquisa() {
  const [termo, setTermo] = useState("");
  const [resultados, setResultados] = useState<ResultadoPesquisa[]>([]);
  const [origem, setOrigem] = useState<Origem>("texto");
  const [estado, setEstado] = useState<"inicial" | "carregando" | "ok" | "erro">(
    "inicial",
  );

  async function procurar(e: React.FormEvent) {
    e.preventDefault();
    const q = termo.trim();
    if (q.length < 2) return;
    setEstado("carregando");
    try {
      // 1) Pesquisa textual (rápida, no catálogo).
      const textuais = await api.pesquisaTextual(q);
      if (textuais.length > 0) {
        setResultados(textuais);
        setOrigem("texto");
        setEstado("ok");
        return;
      }
      // 2) Sem correspondência textual -> recorre à camada semântica.
      const semantica = await api.pesquisaSemantica(q);
      setResultados(semantica.resultados);
      setOrigem("semantica");
      setEstado("ok");
    } catch {
      setEstado("erro");
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-bold text-gray-800">Pesquisa</h1>
      <p className="mt-1 text-gray-500">
        Procure por título ou assunto. Se não houver correspondência exacta,
        mostramos obras sobre temas relacionados.
      </p>

      <form onSubmit={procurar} className="mt-6 flex gap-2">
        <input
          className="campo"
          value={termo}
          onChange={(e) => setTermo(e.target.value)}
          placeholder="Ex.: Inteligência Artificial, Machine Learning…"
        />
        <button className="btn-primario">Procurar</button>
      </form>

      {estado === "carregando" && (
        <p className="mt-8 text-gray-500">A procurar…</p>
      )}

      {estado === "erro" && (
        <div className="mt-8 rounded-lg bg-red-50 p-4 text-red-700">
          Não foi possível concluir a pesquisa. Tente novamente.
        </div>
      )}

      {estado === "ok" && (
        <div className="mt-8">
          {resultados.length === 0 ? (
            <div className="cartao">
              <p className="text-gray-600">
                Não encontrámos obras para &quot;{termo}&quot;.
              </p>
              <p className="mt-2 text-sm text-gray-500">
                Experimente a{" "}
                <Link
                  href={`/pesquisa-semantica?q=${encodeURIComponent(termo)}`}
                  className="text-primaria underline"
                >
                  pesquisa por descoberta
                </Link>{" "}
                para ver temas relacionados.
              </p>
            </div>
          ) : (
            <>
              {origem === "semantica" && (
                <div className="mb-4 rounded-lg bg-amber-50 p-4 text-sm text-amber-800">
                  Não houve correspondência no título nem no resumo. Mostramos as
                  obras encontradas por significado — sobre &quot;{termo}&quot; e
                  os seus temas relacionados.
                </div>
              )}
              <ul className="space-y-3">
                {resultados.map((r, i) => (
                  <li key={i} className="cartao">
                    <h3 className="font-semibold text-gray-800">{r.titulo}</h3>
                    {r.tipo && <span className="chip mt-1">{r.tipo}</span>}
                    {r.motivo && (
                      <p className="mt-1 text-sm text-primaria">{r.motivo}</p>
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
