"use client";
// historico/page.tsx — O histórico do leitor: documentos lidos/descarregados e
// termos pesquisados. Permite limpar todo o histórico.
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { LeituraHistorico, PesquisaHistorico } from "@/types";

const dataPt = (iso?: string | null) =>
  iso
    ? new Date(iso).toLocaleDateString("pt-PT", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";

export default function PaginaHistorico() {
  const { utilizador, carregando } = useAuth();
  const router = useRouter();

  const [leituras, setLeituras] = useState<LeituraHistorico[]>([]);
  const [pesquisas, setPesquisas] = useState<PesquisaHistorico[]>([]);
  const [aCarregar, setACarregar] = useState(true);
  const [erro, setErro] = useState("");

  const carregar = useCallback(async () => {
    try {
      const [l, p] = await Promise.all([
        api.historicoLeituras(),
        api.historicoPesquisas(),
      ]);
      setLeituras(l);
      setPesquisas(p);
    } catch (ex) {
      setErro((ex as Error).message);
    } finally {
      setACarregar(false);
    }
  }, []);

  useEffect(() => {
    if (!carregando && !utilizador) {
      router.push("/login");
      return;
    }
    if (utilizador) carregar();
  }, [utilizador, carregando, router, carregar]);

  async function limpar() {
    if (!confirm("Apagar todo o seu histórico de leituras e pesquisas?")) return;
    try {
      await api.limparHistorico();
      setLeituras([]);
      setPesquisas([]);
    } catch (ex) {
      setErro((ex as Error).message);
    }
  }

  if (carregando || aCarregar)
    return <p className="px-4 py-10 text-gray-500">A carregar…</p>;

  const vazio = leituras.length === 0 && pesquisas.length === 0;

  return (
    <section className="mx-auto max-w-4xl px-4 py-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">O meu histórico</h1>
          <p className="mt-1 text-sm text-gray-500">
            Documentos que leu e termos que pesquisou.
          </p>
        </div>
        {!vazio && (
          <button
            onClick={limpar}
            className="rounded-lg border border-red-200 px-4 py-1.5 text-sm font-medium text-red-600 transition hover:bg-red-50"
          >
            Limpar histórico
          </button>
        )}
      </div>

      {erro && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {erro}
        </div>
      )}

      {vazio && (
        <div className="cartao mt-6">
          <p className="text-gray-600">
            Ainda não há nada no seu histórico. Leia ou pesquise documentos para o
            começar a preencher.
          </p>
        </div>
      )}

      {/* Leituras */}
      {leituras.length > 0 && (
        <>
          <h2 className="mt-8 text-lg font-semibold text-gray-800">
            Documentos lidos ({leituras.length})
          </h2>
          <div className="mt-3 space-y-2">
            {leituras.map((l, i) => (
              <div
                key={`${l.documento_id}-${i}`}
                className="flex items-center justify-between rounded-lg border border-gray-100 bg-white px-4 py-3 text-sm"
              >
                <Link
                  href={`/documento/${l.documento_id}`}
                  className="font-medium text-gray-800 hover:text-primaria"
                >
                  {l.titulo}
                </Link>
                <span className="text-xs text-gray-500">{dataPt(l.data)}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Pesquisas */}
      {pesquisas.length > 0 && (
        <>
          <h2 className="mt-8 text-lg font-semibold text-gray-800">
            Pesquisas recentes ({pesquisas.length})
          </h2>
          <div className="mt-3 flex flex-wrap gap-2">
            {pesquisas.map((p, i) => (
              <Link
                key={i}
                href={`/pesquisa?q=${encodeURIComponent(p.termo)}`}
                className="chip transition hover:bg-primaria/10"
                title={dataPt(p.data)}
              >
                {p.termo}
                {p.semantica && (
                  <span className="ml-1 text-roxo">· descoberta</span>
                )}
              </Link>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
