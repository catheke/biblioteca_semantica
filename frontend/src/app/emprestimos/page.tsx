"use client";
// emprestimos/page.tsx — A área do leitor: empréstimos a decorrer, reservas em
// fila e multas. Permite renovar empréstimos e cancelar reservas.
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Emprestimo, Multa, Reserva } from "@/types";

const KZ = (v: number) =>
  new Intl.NumberFormat("pt-PT", { maximumFractionDigits: 0 }).format(v) + " Kz";

const dataPt = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleDateString("pt-PT") : "—";

export default function PaginaEmprestimos() {
  const { utilizador, carregando } = useAuth();
  const router = useRouter();

  const [emprestimos, setEmprestimos] = useState<Emprestimo[]>([]);
  const [reservas, setReservas] = useState<Reserva[]>([]);
  const [multas, setMultas] = useState<Multa[]>([]);
  const [aCarregar, setACarregar] = useState(true);
  const [mensagem, setMensagem] = useState("");
  const [erro, setErro] = useState("");

  const carregar = useCallback(async () => {
    try {
      const [e, r, m] = await Promise.all([
        api.meusEmprestimos(),
        api.minhasReservas(),
        api.minhasMultas(),
      ]);
      setEmprestimos(e);
      setReservas(r);
      setMultas(m);
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

  async function renovar(id: number) {
    setMensagem("");
    setErro("");
    try {
      await api.renovar(id);
      setMensagem("Empréstimo renovado.");
      await carregar();
    } catch (ex) {
      setErro((ex as Error).message);
    }
  }

  async function cancelar(id: number) {
    setMensagem("");
    setErro("");
    try {
      await api.cancelarReserva(id);
      setMensagem("Reserva cancelada.");
      await carregar();
    } catch (ex) {
      setErro((ex as Error).message);
    }
  }

  if (carregando || aCarregar)
    return <p className="px-4 py-10 text-gray-500">A carregar…</p>;

  const activos = emprestimos.filter((e) => e.estado !== "devolvido");
  const historico = emprestimos.filter((e) => e.estado === "devolvido");
  const multasPorPagar = multas.filter((m) => !m.paga);
  const totalDivida = multasPorPagar.reduce((s, m) => s + m.valor, 0);

  return (
    <section className="mx-auto max-w-5xl px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800">A minha biblioteca</h1>
      <p className="mt-1 text-sm text-gray-500">
        Os seus empréstimos, reservas e multas.
      </p>

      {mensagem && (
        <div className="mt-4 rounded-lg bg-green-50 p-3 text-sm text-green-700">
          {mensagem}
        </div>
      )}
      {erro && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {erro}
        </div>
      )}

      {/* Aviso de dívida */}
      {totalDivida > 0 && (
        <div className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-dourado">
          Tem {KZ(totalDivida)} em multas por pagar. Regularize na biblioteca para
          poder requisitar novas obras.
        </div>
      )}

      {/* Empréstimos a decorrer */}
      <h2 className="mt-8 text-lg font-semibold text-gray-800">
        Empréstimos a decorrer ({activos.length})
      </h2>
      {activos.length === 0 ? (
        <p className="mt-2 text-sm text-gray-500">
          Não tem obras requisitadas de momento.
        </p>
      ) : (
        <div className="mt-3 space-y-3">
          {activos.map((e) => {
            const atrasado = e.estado === "atrasado" || e.dias_em_atraso > 0;
            return (
              <div
                key={e.id}
                className="flex flex-col gap-2 rounded-lg border border-gray-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between"
              >
                <div>
                  <Link
                    href={`/documento/${e.documento_id}`}
                    className="font-medium text-gray-800 hover:text-primaria"
                  >
                    {e.documento_titulo ?? `Documento #${e.documento_id}`}
                  </Link>
                  <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                    <span>Registo: {e.numero_registo ?? "—"}</span>
                    <span>Requisitado: {dataPt(e.data_emprestimo)}</span>
                    <span
                      className={atrasado ? "font-medium text-red-600" : ""}
                    >
                      Devolver até: {dataPt(e.data_prevista_devolucao)}
                    </span>
                    <span>Renovações: {e.renovacoes}</span>
                  </div>
                  {atrasado && (
                    <p className="mt-1 text-xs font-medium text-red-600">
                      Em atraso {e.dias_em_atraso} dia(s)
                      {e.multa_valor > 0 && ` · multa ${KZ(e.multa_valor)}`}
                    </p>
                  )}
                </div>
                <button
                  onClick={() => renovar(e.id)}
                  className="btn-secundario py-1.5 text-sm"
                >
                  Renovar
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Reservas em espera */}
      <h2 className="mt-8 text-lg font-semibold text-gray-800">
        As minhas reservas ({reservas.length})
      </h2>
      {reservas.length === 0 ? (
        <p className="mt-2 text-sm text-gray-500">Não tem reservas activas.</p>
      ) : (
        <div className="mt-3 space-y-3">
          {reservas.map((r) => (
            <div
              key={r.id}
              className="flex flex-col gap-2 rounded-lg border border-gray-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between"
            >
              <div>
                <Link
                  href={`/documento/${r.documento_id}`}
                  className="font-medium text-gray-800 hover:text-primaria"
                >
                  {r.documento_titulo ?? `Documento #${r.documento_id}`}
                </Link>
                <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                  <span>Reservado: {dataPt(r.data_reserva)}</span>
                  {r.posicao != null && (
                    <span className="chip">
                      {r.posicao === 1
                        ? "É o próximo da fila"
                        : `Posição ${r.posicao} na fila`}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => cancelar(r.id)}
                className="rounded-lg border border-red-200 px-4 py-1.5 text-sm font-medium text-red-600 transition hover:bg-red-50"
              >
                Cancelar
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Multas */}
      <h2 className="mt-8 text-lg font-semibold text-gray-800">
        As minhas multas ({multas.length})
      </h2>
      {multas.length === 0 ? (
        <p className="mt-2 text-sm text-gray-500">Não tem multas. Continue assim!</p>
      ) : (
        <div className="mt-3 overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-2">Obra</th>
                <th className="px-4 py-2">Dias de atraso</th>
                <th className="px-4 py-2">Valor</th>
                <th className="px-4 py-2">Estado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {multas.map((m) => (
                <tr key={m.id}>
                  <td className="px-4 py-2 text-gray-800">
                    {m.documento_titulo ?? "—"}
                  </td>
                  <td className="px-4 py-2 text-gray-600">{m.dias_atraso}</td>
                  <td className="px-4 py-2 text-gray-800">{KZ(m.valor)}</td>
                  <td className="px-4 py-2">
                    {m.paga ? (
                      <span className="chip bg-green-50 text-green-700">Paga</span>
                    ) : (
                      <span className="chip bg-red-50 text-red-700">Por pagar</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Histórico */}
      {historico.length > 0 && (
        <>
          <h2 className="mt-8 text-lg font-semibold text-gray-800">
            Histórico de devoluções ({historico.length})
          </h2>
          <div className="mt-3 space-y-2">
            {historico.map((e) => (
              <div
                key={e.id}
                className="flex items-center justify-between rounded-lg border border-gray-100 bg-gray-50 px-4 py-2 text-sm"
              >
                <span className="text-gray-700">
                  {e.documento_titulo ?? `Documento #${e.documento_id}`}
                </span>
                <span className="text-xs text-gray-500">
                  Devolvido em {dataPt(e.data_devolucao)}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </section>
  );
}
