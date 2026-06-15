"use client";
// dashboard/page.tsx — Painel pessoal: saudação, recomendações e atalhos.
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface Recomendacao {
  uri: string;
  titulo: string;
  motivo: string;
}

export default function PaginaDashboard() {
  const { utilizador, carregando } = useAuth();
  const router = useRouter();
  const [recs, setRecs] = useState<Recomendacao[]>([]);

  useEffect(() => {
    if (!carregando && !utilizador) router.push("/login");
    if (utilizador) api.recomendacoes().then(setRecs).catch(() => setRecs([]));
  }, [utilizador, carregando, router]);

  if (!utilizador) return null;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800">
        Olá, {utilizador.nome.split(" ")[0]} 👋
      </h1>
      <p className="mt-1 text-gray-500 capitalize">Perfil: {utilizador.perfil}</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <Link href="/favoritos" className="cartao text-center">
          <p className="text-lg font-semibold text-primaria">Favoritos</p>
          <p className="text-sm text-gray-500">Documentos guardados</p>
        </Link>
        <Link href="/perfil" className="cartao text-center">
          <p className="text-lg font-semibold text-primaria">Perfil</p>
          <p className="text-sm text-gray-500">Editar os meus dados</p>
        </Link>
        <Link href="/pesquisa-semantica" className="cartao text-center">
          <p className="text-lg font-semibold text-primaria">Descobrir</p>
          <p className="text-sm text-gray-500">Pesquisa inteligente</p>
        </Link>
      </div>

      <h2 className="mt-10 text-xl font-semibold text-gray-800">
        Recomendado para si
      </h2>
      <p className="text-sm text-gray-500">
        Sugestões baseadas nos seus interesses (via ontologia).
      </p>
      {recs.length === 0 ? (
        <p className="mt-4 text-gray-500">
          Sem recomendações ainda. Guarde favoritos e carregue a ontologia no
          Fuseki para ver sugestões inteligentes.
        </p>
      ) : (
        <ul className="mt-4 space-y-3">
          {recs.map((r) => (
            <li key={r.uri} className="cartao">
              <h3 className="font-semibold text-gray-800">{r.titulo}</h3>
              <p className="mt-1 text-sm text-primaria">{r.motivo}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
