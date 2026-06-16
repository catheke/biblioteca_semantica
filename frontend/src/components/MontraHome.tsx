"use client";
// MontraHome.tsx — A "montra" da biblioteca na página inicial: estante de obras
// em destaque e atalhos para as secções (estantes) da CDU. Dá vida à entrada do
// site mostrando capas reais de livros.

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Documento, SeccaoBiblioteca } from "@/types";
import CapaLivro from "@/components/CapaLivro";

// Cor do crachá de cada estante, por classe da CDU.
const COR_SECCAO: Record<string, string> = {
  "0": "bg-blue-50 text-primaria",
  "1": "bg-purple-50 text-roxo",
  "5": "bg-green-50 text-green-700",
  "6": "bg-red-50 text-red-700",
  "82": "bg-amber-50 text-dourado",
};

export default function MontraHome() {
  const [destaques, setDestaques] = useState<Documento[]>([]);
  const [seccoes, setSeccoes] = useState<SeccaoBiblioteca[]>([]);

  useEffect(() => {
    api
      .listarDocumentos({ por_pagina: 18 })
      .then((p) => setDestaques(p.itens))
      .catch(() => setDestaques([]));
    api
      .seccoesBiblioteca()
      .then(setSeccoes)
      .catch(() => setSeccoes([]));
  }, []);

  return (
    <>
      {/* -------- Estante em destaque -------- */}
      {destaques.length > 0 && (
        <section className="mx-auto max-w-6xl px-4 py-14">
          <div className="flex items-end justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 sm:text-3xl">
                Em destaque na estante
              </h2>
              <p className="mt-1 text-gray-600">
                Algumas das obras disponíveis para ler e descarregar.
              </p>
            </div>
            <Link
              href="/biblioteca"
              className="hidden shrink-0 text-sm font-medium text-primaria hover:underline sm:block"
            >
              Ver toda a biblioteca →
            </Link>
          </div>

          {/* Estante com prateleira de madeira por baixo das capas */}
          <div className="mt-8 flex gap-5 overflow-x-auto pb-6">
            {destaques.map((d) => (
              <Link
                key={d.id}
                href={`/documento/${d.id}`}
                className="group w-[150px] shrink-0"
              >
                <div className="aspect-[3/4] w-full transition group-hover:-translate-y-1">
                  <CapaLivro doc={d} className="h-full shadow-md" />
                </div>
                <div className="mt-2 h-2 rounded-b bg-gradient-to-b from-amber-200/70 to-amber-100/40" />
                <h3 className="mt-2 line-clamp-2 text-sm font-semibold text-gray-800">
                  {d.titulo}
                </h3>
                {d.autor_nome && (
                  <p className="line-clamp-1 text-xs text-gray-500">
                    {d.autor_nome}
                  </p>
                )}
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* -------- Secções (estantes da CDU) -------- */}
      {seccoes.length > 0 && (
        <section className="bg-white">
          <div className="mx-auto max-w-6xl px-4 py-14">
            <h2 className="text-2xl font-bold text-gray-900 sm:text-3xl">
              Percorra as estantes
            </h2>
            <p className="mt-1 text-gray-600">
              A biblioteca está arrumada por secções, como numa biblioteca real.
            </p>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {seccoes.map((s) => (
                <Link
                  key={s.area_id}
                  href="/biblioteca"
                  className="cartao flex items-center gap-4"
                >
                  <span
                    className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl text-lg font-bold ${
                      COR_SECCAO[s.codigo ?? ""] ?? "bg-gray-100 text-gray-700"
                    }`}
                  >
                    {s.codigo ?? "—"}
                  </span>
                  <div className="min-w-0">
                    <h3 className="truncate font-semibold text-gray-800">
                      {s.nome}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {s.total} {s.total === 1 ? "obra" : "obras"}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
}
