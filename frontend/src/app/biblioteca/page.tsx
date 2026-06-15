"use client";
// biblioteca/page.tsx — A biblioteca arrumada por SECÇÕES, como uma estante real.
// As secções seguem a CDU (Classificação Decimal Universal). A secção de
// Literatura abre-se ainda por GÉNERO (Romance, Conto, Poesia, Teatro).

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Documento, SeccaoBiblioteca } from "@/types";
import CartaoDocumento from "@/components/CartaoDocumento";

// Cor do crachá de cada estante, por classe da CDU.
const COR_SECCAO: Record<string, string> = {
  "0": "bg-blue-50 text-primaria",
  "1": "bg-purple-50 text-roxo",
  "5": "bg-green-50 text-green-700",
  "6": "bg-red-50 text-red-700",
  "82": "bg-amber-50 text-dourado",
};

function corDaSeccao(codigo?: string | null): string {
  return COR_SECCAO[codigo ?? ""] ?? "bg-gray-100 text-gray-700";
}

function obras(n: number): string {
  return `${n} ${n === 1 ? "obra" : "obras"}`;
}

export default function PaginaBiblioteca() {
  const [seccoes, setSeccoes] = useState<SeccaoBiblioteca[]>([]);
  const [estado, setEstado] = useState<"carregando" | "ok" | "erro">("carregando");

  // Estante aberta + género activo (só faz sentido na Literatura).
  const [activa, setActiva] = useState<SeccaoBiblioteca | null>(null);
  const [genero, setGenero] = useState<string | null>(null);

  // Documentos da estante aberta.
  const [docs, setDocs] = useState<Documento[]>([]);
  const [aCarregarDocs, setACarregarDocs] = useState(false);

  useEffect(() => {
    api
      .seccoesBiblioteca()
      .then((s) => {
        setSeccoes(s);
        setEstado("ok");
      })
      .catch(() => {
        setEstado("erro");
      });
  }, []);

  // Recarrega os documentos sempre que muda a estante ou o género escolhido.
  useEffect(() => {
    if (!activa) return;
    setACarregarDocs(true);
    const params: Record<string, string | number> = {
      area_id: activa.area_id,
      por_pagina: 100,
    };
    if (genero) params.genero = genero;
    api
      .listarDocumentos(params)
      .then((p) => setDocs(p.itens))
      .catch(() => setDocs([]))
      .finally(() => setACarregarDocs(false));
  }, [activa, genero]);

  function abrir(seccao: SeccaoBiblioteca) {
    setActiva(seccao);
    setGenero(null);
    setDocs([]);
  }
  function voltar() {
    setActiva(null);
    setGenero(null);
    setDocs([]);
  }

  // Vista 1 — grelha de estantes (as secções da biblioteca)
  if (!activa) {
    return (
      <section className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-2xl font-bold text-gray-800">Biblioteca</h1>
        <p className="mt-1 max-w-2xl text-gray-500">
          Escolha uma secção para ver as obras.
        </p>

        {estado === "carregando" && <p className="mt-8 text-gray-500">A carregar…</p>}
        {estado === "erro" && (
          <div className="mt-8 rounded-lg bg-red-50 p-4 text-red-700">
            Não foi possível carregar as secções. Tente novamente.
          </div>
        )}

        {estado === "ok" && (
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {seccoes.map((s) => (
              <button
                key={s.area_id}
                onClick={() => abrir(s)}
                className="cartao text-left transition hover:shadow-md"
              >
                <div className="flex items-start gap-4">
                  <span
                    className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl text-lg font-bold ${corDaSeccao(
                      s.codigo,
                    )}`}
                  >
                    {s.codigo ?? "—"}
                  </span>
                  <div className="min-w-0">
                    <h2 className="font-semibold text-gray-800">{s.nome}</h2>
                    <p className="text-sm text-gray-500">{obras(s.total)}</p>
                    {s.generos.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {s.generos
                          .filter((g) => g.total > 0)
                          .map((g) => (
                            <span
                              key={g.codigo}
                              className="chip bg-gray-100 text-gray-600"
                            >
                              {g.nome} · {g.total}
                            </span>
                          ))}
                      </div>
                    )}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>
    );
  }

  // Vista 2 — dentro de uma estante (com filtro por género na Literatura)
  return (
    <section className="mx-auto max-w-6xl px-4 py-8">
      <button
        onClick={voltar}
        className="text-sm font-medium text-primaria hover:underline"
      >
        ← Todas as secções
      </button>

      <div className="mt-3 flex items-center gap-3">
        <span
          className={`flex h-12 w-12 items-center justify-center rounded-xl text-base font-bold ${corDaSeccao(
            activa.codigo,
          )}`}
        >
          {activa.codigo ?? "—"}
        </span>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">{activa.nome}</h1>
          <p className="text-sm text-gray-500">
            Cota CDU {activa.codigo} · {obras(activa.total)}
          </p>
        </div>
      </div>

      {/* Filtro por género (só na Literatura) */}
      {activa.generos.length > 0 && (
        <div className="mt-5 flex flex-wrap gap-2">
          <button
            onClick={() => setGenero(null)}
            className={`chip ${
              genero === null ? "bg-primaria text-white" : "bg-gray-100 text-gray-600"
            }`}
          >
            Todos · {activa.total}
          </button>
          {activa.generos.map((g) => (
            <button
              key={g.codigo}
              disabled={g.total === 0}
              onClick={() => setGenero(g.nome)}
              title={`CDU ${g.codigo}`}
              className={`chip ${
                genero === g.nome
                  ? "bg-primaria text-white"
                  : "bg-gray-100 text-gray-600"
              } ${g.total === 0 ? "cursor-not-allowed opacity-40" : ""}`}
            >
              {g.nome} · {g.total}
            </button>
          ))}
        </div>
      )}

      {aCarregarDocs && <p className="mt-8 text-gray-500">A carregar…</p>}
      {!aCarregarDocs && docs.length === 0 && (
        <p className="mt-8 text-gray-500">Ainda não há obras nesta estante.</p>
      )}
      {!aCarregarDocs && docs.length > 0 && (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {docs.map((d) => (
            <CartaoDocumento key={d.id} doc={d} />
          ))}
        </div>
      )}
    </section>
  );
}
