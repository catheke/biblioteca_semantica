"use client";
// pesquisa/page.tsx — Pesquisa textual clássica (por título/resumo).

import { useState } from "react";
import { api } from "@/lib/api";
import type { ResultadoPesquisa } from "@/types";

export default function PaginaPesquisa() {
  const [termo, setTermo] = useState("");
  const [resultados, setResultados] = useState<ResultadoPesquisa[]>([]);
  const [procurou, setProcurou] = useState(false);

  async function procurar(e: React.FormEvent) {
    e.preventDefault();
    if (termo.trim().length < 2) return;
    setResultados(await api.pesquisaTextual(termo));
    setProcurou(true);
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-bold text-gray-800">Pesquisa</h1>
      <form onSubmit={procurar} className="mt-6 flex gap-2">
        <input
          className="campo"
          value={termo}
          onChange={(e) => setTermo(e.target.value)}
          placeholder="Procurar por título ou resumo…"
        />
        <button className="btn-primario">Procurar</button>
      </form>

      {procurou && (
        <ul className="mt-8 space-y-3">
          {resultados.length === 0 && (
            <p className="text-gray-500">Sem resultados.</p>
          )}
          {resultados.map((r, i) => (
            <li key={i} className="cartao">
              <h3 className="font-semibold text-gray-800">{r.titulo}</h3>
              {r.tipo && <span className="chip mt-1">{r.tipo}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
