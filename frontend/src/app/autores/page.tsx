"use client";
// autores/page.tsx — Lista todos os autores (utilizadores que publicam).
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Utilizador } from "@/types";
import CartaoPessoa from "@/components/CartaoPessoa";

export default function PaginaAutores() {
  const [pessoas, setPessoas] = useState<Utilizador[]>([]);
  const [erro, setErro] = useState("");

  useEffect(() => {
    api
      .listarUtilizadores()
      .then((p) =>
        setPessoas(
          p.itens.filter((u) =>
            ["professor", "investigador"].includes(u.perfil),
          ),
        ),
      )
      .catch((e) => setErro(e.message));
  }, []);

  return (
    <section className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800">Autores</h1>
      <p className="mt-1 text-gray-500">Professores e investigadores que publicam.</p>
      {erro && (
        <div className="mt-6 rounded-lg bg-red-50 p-4 text-red-700">{erro}</div>
      )}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {pessoas.map((p) => (
          <CartaoPessoa key={p.id} pessoa={p} />
        ))}
      </div>
    </section>
  );
}
