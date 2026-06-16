"use client";
// pesquisa/page.tsx — Pesquisa no catálogo com filtros (título/resumo, autor, ano).
// Procura primeiro no catálogo (com os filtros indicados). Se uma pesquisa só por
// texto não devolver nada, recorre automaticamente à camada semântica (temas e
// subtemas relacionados), para que o utilizador receba sempre resultados úteis.

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Documento, ResultadoPesquisa } from "@/types";

export default function PaginaPesquisa() {
  const [termo, setTermo] = useState("");
  const [autor, setAutor] = useState("");
  const [ano, setAno] = useState("");
  const [docs, setDocs] = useState<Documento[]>([]);
  const [semanticos, setSemanticos] = useState<ResultadoPesquisa[]>([]);
  const [estado, setEstado] = useState<"inicial" | "carregando" | "ok" | "erro">(
    "inicial",
  );

  async function procurar() {
    const q = termo.trim();
    const a = autor.trim();
    const y = ano.trim();
    if (!q && !a && !y) return;
    setEstado("carregando");
    setSemanticos([]);
    try {
      // 1) Pesquisa no catálogo, com os filtros indicados.
      const params: Record<string, string | number> = { por_pagina: 50 };
      if (q) params.q = q;
      if (a) params.autor = a;
      if (y) params.ano = y;
      const pagina = await api.listarDocumentos(params);
      setDocs(pagina.itens);

      // 2) Sem resultados e a pesquisar só por texto -> camada semântica.
      if (pagina.itens.length === 0 && q && !a && !y) {
        const semantica = await api.pesquisaSemantica(q);
        setSemanticos(semantica.resultados);
      }
      setEstado("ok");
    } catch {
      setEstado("erro");
    }
  }

  // Permite ligações directas, ex.: /pesquisa?q=Machine+Learning
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("q");
    if (q && q.trim()) {
      setTermo(q.trim());
      // pequena espera para o estado actualizar antes de procurar
      setTimeout(() => {
        setEstado("carregando");
        api
          .listarDocumentos({ q: q.trim(), por_pagina: 50 })
          .then(async (pagina) => {
            setDocs(pagina.itens);
            if (pagina.itens.length === 0) {
              const s = await api.pesquisaSemantica(q.trim());
              setSemanticos(s.resultados);
            }
            setEstado("ok");
          })
          .catch(() => setEstado("erro"));
      }, 0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="text-2xl font-bold text-gray-800">Pesquisa</h1>
      <p className="mt-1 text-gray-500">
        Procure por título, assunto, autor ou ano. Se uma pesquisa por texto não
        tiver correspondência, mostramos obras sobre temas relacionados.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          procurar();
        }}
        className="mt-6 space-y-3"
      >
        <input
          className="campo"
          value={termo}
          onChange={(e) => setTermo(e.target.value)}
          placeholder="Título ou assunto (ex.: Inteligência Artificial)"
        />
        <div className="flex flex-col gap-3 sm:flex-row">
          <input
            className="campo"
            value={autor}
            onChange={(e) => setAutor(e.target.value)}
            placeholder="Autor (ex.: Machado de Assis)"
          />
          <input
            className="campo sm:max-w-[160px]"
            value={ano}
            onChange={(e) => setAno(e.target.value)}
            inputMode="numeric"
            placeholder="Ano (ex.: 2020)"
          />
        </div>
        <button className="btn-primario w-full sm:w-auto">Procurar</button>
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
          {docs.length === 0 && semanticos.length === 0 ? (
            <div className="cartao">
              <p className="text-gray-600">Não encontrámos obras para esta pesquisa.</p>
              <p className="mt-2 text-sm text-gray-500">
                Experimente outros termos ou a{" "}
                <Link
                  href={`/pesquisa-semantica?q=${encodeURIComponent(termo)}`}
                  className="text-primaria underline"
                >
                  pesquisa por descoberta
                </Link>
                .
              </p>
            </div>
          ) : docs.length > 0 ? (
            <ul className="space-y-3">
              {docs.map((d) => (
                <li key={d.id} className="cartao">
                  <Link href={`/documento/${d.id}`} className="block">
                    <h3 className="font-semibold text-gray-800 hover:text-primaria">
                      {d.titulo}
                    </h3>
                  </Link>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-sm text-gray-500">
                    <span className="chip">{d.tipo}</span>
                    {d.autor_nome && <span>· {d.autor_nome}</span>}
                    {d.ano_publicacao && <span>· {d.ano_publicacao}</span>}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <>
              <div className="mb-4 rounded-lg bg-amber-50 p-4 text-sm text-amber-800">
                Não houve correspondência no título nem no resumo. Mostramos as
                obras encontradas por significado — temas relacionados com a sua
                pesquisa.
              </div>
              <ul className="space-y-3">
                {semanticos.map((r, i) => (
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
