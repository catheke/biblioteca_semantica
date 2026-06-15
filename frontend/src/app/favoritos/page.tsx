"use client";
// favoritos/page.tsx — Documentos guardados pelo utilizador autenticado.
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Documento } from "@/types";
import CartaoDocumento from "@/components/CartaoDocumento";

export default function PaginaFavoritos() {
  const { utilizador, carregando } = useAuth();
  const router = useRouter();
  const [docs, setDocs] = useState<Documento[]>([]);

  useEffect(() => {
    if (!carregando && !utilizador) router.push("/login");
    if (utilizador) api.favoritos().then(setDocs).catch(() => setDocs([]));
  }, [utilizador, carregando, router]);

  return (
    <section className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800">Os meus favoritos</h1>
      {docs.length === 0 ? (
        <p className="mt-6 text-gray-500">Ainda não guardou documentos.</p>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {docs.map((d) => (
            <CartaoDocumento key={d.id} doc={d} />
          ))}
        </div>
      )}
    </section>
  );
}
