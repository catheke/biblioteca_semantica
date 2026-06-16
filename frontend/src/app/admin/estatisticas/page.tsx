"use client";
// admin/estatisticas/page.tsx — Painel de estatísticas da biblioteca (só para
// perfil 'administrador'). Mostra números gerais, obras mais procuradas e os
// termos que os leitores mais pesquisam.

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Estatisticas } from "@/types";

// Cartão de número grande (KPI).
function Indicador({ rotulo, valor }: { rotulo: string; valor: number }) {
  return (
    <div className="cartao">
      <p className="text-sm text-gray-500">{rotulo}</p>
      <p className="mt-1 text-3xl font-bold text-gray-900">
        {valor.toLocaleString("pt-PT")}
      </p>
    </div>
  );
}

// Barra horizontal simples para comparar valores (sem bibliotecas externas).
function Barra({
  texto,
  valor,
  maximo,
  cor,
}: {
  texto: string;
  valor: number;
  maximo: number;
  cor: string;
}) {
  const largura = maximo > 0 ? Math.max(4, (valor / maximo) * 100) : 0;
  return (
    <li>
      <div className="flex items-center justify-between text-sm">
        <span className="truncate pr-3 text-gray-700">{texto}</span>
        <span className="shrink-0 font-medium text-gray-500">{valor}</span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-gray-100">
        <div
          className={`h-full rounded-full ${cor}`}
          style={{ width: `${largura}%` }}
        />
      </div>
    </li>
  );
}

export default function PaginaEstatisticas() {
  const { utilizador, carregando } = useAuth();
  const router = useRouter();
  const [dados, setDados] = useState<Estatisticas | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    if (carregando) return;
    if (!utilizador || utilizador.perfil !== "administrador") {
      router.replace("/login");
      return;
    }
    api
      .estatisticas()
      .then(setDados)
      .catch((e) => setErro((e as Error).message));
  }, [utilizador, carregando, router]);

  if (carregando) return <p className="px-4 py-10 text-gray-500">A carregar…</p>;

  if (erro)
    return (
      <div className="mx-auto max-w-5xl px-4 py-10">
        <div className="rounded-lg bg-red-50 p-4 text-red-700">{erro}</div>
      </div>
    );

  if (!dados)
    return <p className="px-4 py-10 text-gray-500">A carregar estatísticas…</p>;

  const maxVistos = Math.max(0, ...dados.mais_vistos.map((d) => d.valor));
  const maxDesc = Math.max(0, ...dados.mais_descarregados.map((d) => d.valor));
  const maxCat = Math.max(0, ...dados.por_categoria.map((c) => c.total));
  const maxTermo = Math.max(0, ...dados.termos_mais_pesquisados.map((t) => t.total));

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Estatísticas</h1>
          <p className="mt-1 text-gray-500">
            Uma visão geral da utilização da biblioteca.
          </p>
        </div>
        <Link href="/admin" className="btn-secundario py-1.5 text-sm">
          ← Voltar à administração
        </Link>
      </div>

      {/* Indicadores gerais */}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Indicador rotulo="Documentos" valor={dados.total_documentos} />
        <Indicador rotulo="Utilizadores" valor={dados.total_utilizadores} />
        <Indicador rotulo="Descargas" valor={dados.total_downloads} />
        <Indicador rotulo="Visualizações" valor={dados.total_visualizacoes} />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        {/* Mais vistos */}
        <section className="cartao">
          <h2 className="text-lg font-semibold text-gray-800">Mais vistos</h2>
          {dados.mais_vistos.length === 0 ? (
            <p className="mt-3 text-sm text-gray-500">Ainda sem dados.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {dados.mais_vistos.map((d) => (
                <Barra
                  key={d.documento_id}
                  texto={d.titulo}
                  valor={d.valor}
                  maximo={maxVistos}
                  cor="bg-primaria"
                />
              ))}
            </ul>
          )}
        </section>

        {/* Mais descarregados */}
        <section className="cartao">
          <h2 className="text-lg font-semibold text-gray-800">
            Mais descarregados
          </h2>
          {dados.mais_descarregados.length === 0 ? (
            <p className="mt-3 text-sm text-gray-500">Ainda sem dados.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {dados.mais_descarregados.map((d) => (
                <Barra
                  key={d.documento_id}
                  texto={d.titulo}
                  valor={d.valor}
                  maximo={maxDesc}
                  cor="bg-roxo"
                />
              ))}
            </ul>
          )}
        </section>

        {/* Por categoria/secção */}
        <section className="cartao">
          <h2 className="text-lg font-semibold text-gray-800">
            Obras por secção
          </h2>
          {dados.por_categoria.length === 0 ? (
            <p className="mt-3 text-sm text-gray-500">Ainda sem dados.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {dados.por_categoria.map((c) => (
                <Barra
                  key={c.nome}
                  texto={c.nome}
                  valor={c.total}
                  maximo={maxCat}
                  cor="bg-green-500"
                />
              ))}
            </ul>
          )}
        </section>

        {/* Termos mais pesquisados */}
        <section className="cartao">
          <h2 className="text-lg font-semibold text-gray-800">
            Termos mais pesquisados
          </h2>
          {dados.termos_mais_pesquisados.length === 0 ? (
            <p className="mt-3 text-sm text-gray-500">Ainda sem dados.</p>
          ) : (
            <ul className="mt-4 space-y-3">
              {dados.termos_mais_pesquisados.map((t) => (
                <Barra
                  key={t.termo}
                  texto={t.termo}
                  valor={t.total}
                  maximo={maxTermo}
                  cor="bg-dourado"
                />
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
