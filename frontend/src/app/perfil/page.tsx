"use client";
// perfil/page.tsx — Vê e mostra os dados do utilizador autenticado.
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function PaginaPerfil() {
  const { utilizador, carregando } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!carregando && !utilizador) router.push("/login");
  }, [utilizador, carregando, router]);

  if (!utilizador) return null;

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-2xl font-bold text-gray-800">O meu perfil</h1>
      <div className="cartao mt-6 space-y-3">
        <Linha rotulo="Nome" valor={utilizador.nome} />
        <Linha rotulo="Email" valor={utilizador.email} />
        <Linha rotulo="Perfil" valor={utilizador.perfil} />
        <Linha rotulo="Instituição" valor={utilizador.instituicao ?? "—"} />
        {utilizador.biografia && (
          <Linha rotulo="Biografia" valor={utilizador.biografia} />
        )}
      </div>
    </div>
  );
}

function Linha({ rotulo, valor }: { rotulo: string; valor: string }) {
  return (
    <div className="flex justify-between border-b border-gray-100 pb-2">
      <span className="text-sm font-medium text-gray-500">{rotulo}</span>
      <span className="text-sm capitalize text-gray-800">{valor}</span>
    </div>
  );
}
