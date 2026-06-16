"use client";
// SinoNotificacoes.tsx — Sino de avisos na barra de navegação. Mostra o número
// de notificações não lidas e, ao abrir, a lista dos últimos avisos (e marca-os
// como vistos).

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Notificacao } from "@/types";

const dataPt = (iso: string) =>
  new Date(iso).toLocaleDateString("pt-PT", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });

export default function SinoNotificacoes() {
  const [naoLidas, setNaoLidas] = useState(0);
  const [itens, setItens] = useState<Notificacao[]>([]);
  const [aberto, setAberto] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  async function carregar() {
    try {
      const n = await api.notificacoes();
      setNaoLidas(n.nao_lidas);
      setItens(n.itens);
    } catch {
      /* sem sessão ou rede — ignora */
    }
  }

  useEffect(() => {
    carregar();
    const t = setInterval(carregar, 60_000); // actualiza a cada minuto
    return () => clearInterval(t);
  }, []);

  // Fecha ao clicar fora.
  useEffect(() => {
    function fora(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setAberto(false);
      }
    }
    document.addEventListener("mousedown", fora);
    return () => document.removeEventListener("mousedown", fora);
  }, []);

  async function abrir() {
    const vai = !aberto;
    setAberto(vai);
    if (vai && naoLidas > 0) {
      try {
        await api.marcarNotificacoesVistas();
        setNaoLidas(0);
      } catch {
        /* ignora */
      }
    }
  }

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={abrir}
        className="relative grid h-9 w-9 place-items-center rounded-lg text-gray-600 transition hover:bg-gray-100 hover:text-primaria"
        aria-label="Notificações"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-5 w-5"
        >
          <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
        </svg>
        {naoLidas > 0 && (
          <span className="absolute -right-0.5 -top-0.5 grid h-4 min-w-[16px] place-items-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
            {naoLidas > 9 ? "9+" : naoLidas}
          </span>
        )}
      </button>

      {aberto && (
        <div className="absolute right-0 z-30 mt-2 w-80 rounded-xl border border-gray-200 bg-white shadow-lg">
          <div className="border-b border-gray-100 px-4 py-3">
            <h3 className="text-sm font-semibold text-gray-800">Notificações</h3>
          </div>
          {itens.length === 0 ? (
            <p className="px-4 py-6 text-center text-sm text-gray-500">
              Sem avisos de momento.
            </p>
          ) : (
            <ul className="max-h-96 divide-y divide-gray-100 overflow-y-auto">
              {itens.map((n) => {
                const conteudo = (
                  <>
                    <p className="text-sm text-gray-700">{n.mensagem}</p>
                    <p className="mt-0.5 text-xs text-gray-400">
                      {dataPt(n.data)}
                    </p>
                  </>
                );
                return (
                  <li key={n.id} className="px-4 py-3 hover:bg-gray-50">
                    {n.documento_id ? (
                      <Link
                        href={`/documento/${n.documento_id}`}
                        onClick={() => setAberto(false)}
                        className="block"
                      >
                        {conteudo}
                      </Link>
                    ) : (
                      conteudo
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
