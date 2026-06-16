"use client";
// admin/circulacao/page.tsx — Painel do bibliotecário (só 'administrador').
// Relatório de circulação, empréstimos a decorrer (com devolução), reservas em
// fila, multas (com pagamento) e criação de exemplares para uma obra.
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  Documento,
  Emprestimo,
  Multa,
  RelatorioCirculacao,
  Reserva,
} from "@/types";

const KZ = (v: number) =>
  new Intl.NumberFormat("pt-PT", { maximumFractionDigits: 0 }).format(v) + " Kz";
const dataPt = (iso?: string | null) =>
  iso ? new Date(iso).toLocaleDateString("pt-PT") : "—";

function Estatistica({
  rotulo,
  valor,
  destaque,
}: {
  rotulo: string;
  valor: string | number;
  destaque?: "alerta" | "ok";
}) {
  const cor =
    destaque === "alerta"
      ? "text-red-600"
      : destaque === "ok"
        ? "text-green-700"
        : "text-gray-900";
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <p className="text-xs uppercase tracking-wide text-gray-500">{rotulo}</p>
      <p className={`mt-1 text-2xl font-bold ${cor}`}>{valor}</p>
    </div>
  );
}

export default function PaginaCirculacaoAdmin() {
  const { utilizador, carregando } = useAuth();
  const router = useRouter();

  const [relatorio, setRelatorio] = useState<RelatorioCirculacao | null>(null);
  const [emprestimos, setEmprestimos] = useState<Emprestimo[]>([]);
  const [reservas, setReservas] = useState<Reserva[]>([]);
  const [multas, setMultas] = useState<Multa[]>([]);
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [aCarregar, setACarregar] = useState(true);
  const [mensagem, setMensagem] = useState("");
  const [erro, setErro] = useState("");

  // Formulário de criação de exemplares
  const [docExemplar, setDocExemplar] = useState("");
  const [qtd, setQtd] = useState("2");
  const [local, setLocal] = useState("Estante Geral");

  const carregar = useCallback(async () => {
    try {
      const [rel, emp, res, mul] = await Promise.all([
        api.relatorioCirculacao(),
        api.todosEmprestimos(),
        api.todasReservas(),
        api.todasMultas(),
      ]);
      setRelatorio(rel);
      setEmprestimos(emp);
      setReservas(res);
      setMultas(mul);
    } catch (ex) {
      setErro((ex as Error).message);
    } finally {
      setACarregar(false);
    }
  }, []);

  useEffect(() => {
    if (!carregando) {
      if (!utilizador) router.push("/login");
      else if (utilizador.perfil !== "administrador") router.push("/dashboard");
      else {
        carregar();
        api
          .listarDocumentos({ por_pagina: 100 })
          .then((p) => setDocumentos(p.itens))
          .catch(() => setDocumentos([]));
      }
    }
  }, [utilizador, carregando, router, carregar]);

  async function devolver(id: number) {
    setMensagem("");
    setErro("");
    try {
      await api.devolver(id);
      setMensagem("Devolução registada.");
      await carregar();
    } catch (ex) {
      setErro((ex as Error).message);
    }
  }

  async function pagar(id: number) {
    setMensagem("");
    setErro("");
    try {
      await api.pagarMulta(id);
      setMensagem("Multa marcada como paga.");
      await carregar();
    } catch (ex) {
      setErro((ex as Error).message);
    }
  }

  async function criarExemplares(e: React.FormEvent) {
    e.preventDefault();
    setMensagem("");
    setErro("");
    if (!docExemplar) {
      setErro("Escolha a obra para a qual quer criar exemplares.");
      return;
    }
    try {
      const novos = await api.criarExemplares(
        Number(docExemplar),
        Number(qtd),
        local || undefined,
      );
      setMensagem(`${novos.length} exemplar(es) criado(s).`);
      await carregar();
    } catch (ex) {
      setErro((ex as Error).message);
    }
  }

  if (carregando || aCarregar)
    return <p className="px-4 py-10 text-gray-500">A carregar…</p>;
  if (!utilizador || utilizador.perfil !== "administrador") return null;

  const activos = emprestimos.filter((e) => e.estado !== "devolvido");
  const reservasActivas = reservas.filter((r) => r.estado === "activa");
  const multasPorPagar = multas.filter((m) => !m.paga);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">
            Circulação — Bibliotecário
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Empréstimos, devoluções, reservas, multas e estatísticas.
          </p>
        </div>
        <Link href="/admin" className="btn-secundario py-1.5 text-sm">
          Voltar ao Admin
        </Link>
      </div>

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

      {/* ----------------------- Relatório / estatísticas ----------------------- */}
      {relatorio && (
        <section className="mt-6">
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            <Estatistica
              rotulo="Exemplares"
              valor={relatorio.total_exemplares}
            />
            <Estatistica
              rotulo="Disponíveis"
              valor={relatorio.exemplares_disponiveis}
              destaque="ok"
            />
            <Estatistica
              rotulo="Empréstimos activos"
              valor={relatorio.emprestimos_activos}
            />
            <Estatistica
              rotulo="Em atraso"
              valor={relatorio.emprestimos_atrasados}
              destaque={relatorio.emprestimos_atrasados > 0 ? "alerta" : undefined}
            />
            <Estatistica
              rotulo="Reservas activas"
              valor={relatorio.reservas_activas}
            />
            <Estatistica
              rotulo="Multas por pagar"
              valor={relatorio.multas_por_pagar}
              destaque={relatorio.multas_por_pagar > 0 ? "alerta" : undefined}
            />
            <Estatistica
              rotulo="Valor em dívida"
              valor={KZ(relatorio.valor_multas_por_pagar)}
              destaque={relatorio.valor_multas_por_pagar > 0 ? "alerta" : undefined}
            />
            <Estatistica
              rotulo="Total histórico"
              valor={relatorio.total_emprestimos_historico}
            />
          </div>

          {relatorio.obras_mais_requisitadas.length > 0 && (
            <div className="mt-4 rounded-lg border border-gray-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-gray-700">
                Obras mais requisitadas
              </h3>
              <ol className="mt-2 space-y-1 text-sm text-gray-600">
                {relatorio.obras_mais_requisitadas.map((o, i) => (
                  <li key={o.documento_id} className="flex justify-between">
                    <Link
                      href={`/documento/${o.documento_id}`}
                      className="hover:text-primaria"
                    >
                      {i + 1}. {o.titulo}
                    </Link>
                    <span className="text-gray-400">
                      {o.total} empréstimo(s)
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          )}
        </section>
      )}

      {/* ----------------------- Criar exemplares ----------------------- */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold text-gray-800">
          Registar exemplares
        </h2>
        <form
          onSubmit={criarExemplares}
          className="mt-3 grid grid-cols-1 gap-3 rounded-lg border border-gray-200 bg-white p-4 md:grid-cols-4"
        >
          <label className="flex flex-col gap-1 text-sm md:col-span-2">
            <span className="font-medium text-gray-700">Obra</span>
            <select
              value={docExemplar}
              onChange={(e) => setDocExemplar(e.target.value)}
              className="campo"
            >
              <option value="">— Escolha a obra —</option>
              {documentos.map((d) => (
                <option key={d.id} value={String(d.id)}>
                  {d.titulo}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-gray-700">Quantidade</span>
            <input
              type="number"
              min={1}
              max={50}
              value={qtd}
              onChange={(e) => setQtd(e.target.value)}
              className="campo"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            <span className="font-medium text-gray-700">Localização</span>
            <input
              value={local}
              onChange={(e) => setLocal(e.target.value)}
              className="campo"
              placeholder="Ex.: Estante A3"
            />
          </label>
          <div className="md:col-span-4">
            <button type="submit" className="btn-primario py-1.5 text-sm">
              Criar exemplares
            </button>
          </div>
        </form>
      </section>

      {/* ----------------------- Empréstimos a decorrer ----------------------- */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold text-gray-800">
          Empréstimos a decorrer ({activos.length})
        </h2>
        <div className="mt-3 overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-2">Obra</th>
                <th className="px-4 py-2">Leitor</th>
                <th className="px-4 py-2">Registo</th>
                <th className="px-4 py-2">Prazo</th>
                <th className="px-4 py-2">Estado</th>
                <th className="px-4 py-2 text-right">Acção</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {activos.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-4 text-center text-gray-500">
                    Nenhum empréstimo a decorrer.
                  </td>
                </tr>
              ) : (
                activos.map((e) => {
                  const atrasado = e.estado === "atrasado" || e.dias_em_atraso > 0;
                  return (
                    <tr key={e.id}>
                      <td className="px-4 py-2 text-gray-800">
                        {e.documento_titulo ?? `#${e.documento_id}`}
                      </td>
                      <td className="px-4 py-2 text-gray-600">
                        {e.leitor_nome ?? `#${e.utilizador_id}`}
                      </td>
                      <td className="px-4 py-2 text-gray-500">
                        {e.numero_registo ?? "—"}
                      </td>
                      <td
                        className={`px-4 py-2 ${atrasado ? "font-medium text-red-600" : "text-gray-600"}`}
                      >
                        {dataPt(e.data_prevista_devolucao)}
                      </td>
                      <td className="px-4 py-2">
                        {atrasado ? (
                          <span className="chip bg-red-50 text-red-700">
                            Atraso {e.dias_em_atraso}d
                          </span>
                        ) : (
                          <span className="chip bg-green-50 text-green-700">
                            Em dia
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2 text-right">
                        <button
                          onClick={() => devolver(e.id)}
                          className="btn-primario py-1 text-xs"
                        >
                          Devolver
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* ----------------------- Reservas (fila) ----------------------- */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold text-gray-800">
          Reservas em espera ({reservasActivas.length})
        </h2>
        <div className="mt-3 overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-2">Obra</th>
                <th className="px-4 py-2">Leitor</th>
                <th className="px-4 py-2">Posição</th>
                <th className="px-4 py-2">Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {reservasActivas.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-4 py-4 text-center text-gray-500">
                    Sem reservas em espera.
                  </td>
                </tr>
              ) : (
                reservasActivas.map((r) => (
                  <tr key={r.id}>
                    <td className="px-4 py-2 text-gray-800">
                      {r.documento_titulo ?? `#${r.documento_id}`}
                    </td>
                    <td className="px-4 py-2 text-gray-600">
                      {r.leitor_nome ?? `#${r.utilizador_id}`}
                    </td>
                    <td className="px-4 py-2 text-gray-500">
                      {r.posicao ?? "—"}
                    </td>
                    <td className="px-4 py-2 text-gray-500">
                      {dataPt(r.data_reserva)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* ----------------------- Multas ----------------------- */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold text-gray-800">
          Multas por pagar ({multasPorPagar.length})
        </h2>
        <div className="mt-3 overflow-x-auto rounded-lg border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 text-left text-xs uppercase text-gray-500">
              <tr>
                <th className="px-4 py-2">Obra</th>
                <th className="px-4 py-2">Leitor</th>
                <th className="px-4 py-2">Dias</th>
                <th className="px-4 py-2">Valor</th>
                <th className="px-4 py-2 text-right">Acção</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {multasPorPagar.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-4 text-center text-gray-500">
                    Sem multas por pagar.
                  </td>
                </tr>
              ) : (
                multasPorPagar.map((m) => (
                  <tr key={m.id}>
                    <td className="px-4 py-2 text-gray-800">
                      {m.documento_titulo ?? "—"}
                    </td>
                    <td className="px-4 py-2 text-gray-600">
                      {m.leitor_nome ?? `#${m.utilizador_id}`}
                    </td>
                    <td className="px-4 py-2 text-gray-500">{m.dias_atraso}</td>
                    <td className="px-4 py-2 text-gray-800">{KZ(m.valor)}</td>
                    <td className="px-4 py-2 text-right">
                      <button
                        onClick={() => pagar(m.id)}
                        className="btn-secundario py-1 text-xs"
                      >
                        Marcar paga
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
