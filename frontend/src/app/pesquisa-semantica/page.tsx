"use client";
// pesquisa-semantica/page.tsx — A "vitrine" do projecto: pesquisa inteligente.
// Mostra os termos expandidos por inferência E os documentos encontrados, com
// a explicação de PORQUÊ cada resultado é relevante.

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { RespostaSemantica } from "@/types";

const SUGESTOES = ["Inteligência Artificial", "Machine Learning", "Web Semântica"];

export default function PaginaPesquisaSemantica() {
  const [termo, setTermo] = useState("Inteligência Artificial");
  const [resposta, setResposta] = useState<RespostaSemantica | null>(null);
  const [estado, setEstado] = useState<"inicial" | "carregando" | "ok" | "erro">(
    "inicial",
  );

  async function procurar(q: string) {
    setTermo(q);
    setEstado("carregando");
    try {
      setResposta(await api.pesquisaSemantica(q));
      setEstado("ok");
    } catch {
      setEstado("erro");
    }
  }

  // Permite ligações directas para uma pesquisa, ex.: /pesquisa-semantica?q=Machine+Learning
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("q");
    if (q && q.trim()) procurar(q.trim());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-4 py-10">
      <h1 className="text-2xl font-bold text-gray-800">Descobrir</h1>
      <p className="mt-1 text-gray-500">
        Procure um tema e encontre também as obras sobre assuntos relacionados.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          procurar(termo);
        }}
        className="mt-6 flex gap-2"
      >
        <input
          className="campo"
          value={termo}
          onChange={(e) => setTermo(e.target.value)}
          placeholder="Ex.: Inteligência Artificial"
        />
        <button className="btn-primario">Procurar</button>
      </form>

      <div className="mt-3 flex flex-wrap gap-2">
        {SUGESTOES.map((s) => (
          <button key={s} onClick={() => procurar(s)} className="chip hover:bg-blue-100">
            {s}
          </button>
        ))}
      </div>

      {estado === "carregando" && <p className="mt-8 text-gray-500">A pensar…</p>}
      {estado === "erro" && (
        <div className="mt-8 rounded-lg bg-red-50 p-4 text-red-700">
          Não foi possível concluir a pesquisa. Tente novamente.
        </div>
      )}

      {estado === "ok" && resposta && (
        <div className="mt-8 space-y-6">
          {/* Temas relacionados — só quando o termo corresponde a um tema. */}
          {resposta.tema_encontrado && resposta.termos_expandidos.length > 0 && (
            <div className="cartao">
              <h2 className="mb-2 font-semibold text-gray-800">
                Temas relacionados
              </h2>
              <p className="mb-3 text-sm text-gray-500">
                Para além de &quot;{resposta.termo}&quot;, a pesquisa considerou
                os temas ligados a este:
              </p>
              <div className="flex flex-wrap gap-2">
                {resposta.termos_expandidos.map((t) => (
                  <span key={t} className="chip">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Aviso quando recorremos à pesquisa no título/resumo. */}
          {!resposta.tema_encontrado && resposta.resultados.length > 0 && (
            <div className="rounded-lg bg-amber-50 p-4 text-sm text-amber-800">
              &quot;{resposta.termo}&quot; não é um tema da biblioteca. Mostramos
              as obras que mencionam este termo no título ou no resumo.
            </div>
          )}

          {/* Resultados ou estado vazio com sugestões. */}
          {resposta.resultados.length === 0 ? (
            <div className="cartao">
              <h2 className="font-semibold text-gray-800">
                Sem resultados para &quot;{resposta.termo}&quot;
              </h2>
              <p className="mt-1 text-gray-500">
                Não encontrámos obras nem temas com este nome.
              </p>
              {resposta.sugestoes.length > 0 && (
                <>
                  <p className="mt-4 text-sm font-medium text-gray-700">
                    Experimente um destes temas:
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {resposta.sugestoes.map((s) => (
                      <button
                        key={s}
                        onClick={() => procurar(s)}
                        className="chip hover:bg-blue-100"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                </>
              )}
            </div>
          ) : (
            <div>
              <h2 className="mb-3 font-semibold text-gray-800">
                {resposta.resultados.length} documento(s) encontrado(s)
              </h2>
              <ul className="space-y-3">
                {resposta.resultados.map((r, i) => (
                  <li key={i} className="cartao">
                    <h3 className="font-semibold text-gray-800">{r.titulo}</h3>
                    {r.motivo && (
                      <p className="mt-1 text-sm text-primaria">{r.motivo}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
