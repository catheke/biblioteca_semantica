"use client";
// registo/page.tsx — Formulário de criação de conta.

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function PaginaRegisto() {
  const { registar } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({
    nome: "",
    email: "",
    palavra_passe: "",
    perfil: "estudante",
  });
  const [erro, setErro] = useState("");
  const [aGuardar, setAGuardar] = useState(false);

  function actualizar(campo: string, valor: string) {
    setForm((f) => ({ ...f, [campo]: valor }));
  }

  async function submeter(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setAGuardar(true);
    try {
      await registar(form);
      router.push("/dashboard");
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setAGuardar(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <h1 className="text-2xl font-bold text-gray-800">Criar conta</h1>
      <p className="mt-1 text-gray-500">Junte-se à rede académica.</p>

      <form onSubmit={submeter} className="cartao mt-6 space-y-4">
        <div>
          <label className="etiqueta">Nome completo</label>
          <input
            className="campo"
            value={form.nome}
            onChange={(e) => actualizar("nome", e.target.value)}
            required
          />
        </div>
        <div>
          <label className="etiqueta">Email</label>
          <input
            type="email"
            className="campo"
            value={form.email}
            onChange={(e) => actualizar("email", e.target.value)}
            required
          />
        </div>
        <div>
          <label className="etiqueta">Palavra-passe (mín. 8 caracteres)</label>
          <input
            type="password"
            className="campo"
            value={form.palavra_passe}
            onChange={(e) => actualizar("palavra_passe", e.target.value)}
            minLength={8}
            required
          />
        </div>
        <div>
          <label className="etiqueta">Perfil</label>
          <select
            className="campo"
            value={form.perfil}
            onChange={(e) => actualizar("perfil", e.target.value)}
          >
            <option value="estudante">Estudante</option>
            <option value="professor">Professor</option>
            <option value="investigador">Investigador</option>
          </select>
        </div>
        {erro && <p className="text-sm text-red-600">{erro}</p>}
        <button type="submit" className="btn-primario w-full" disabled={aGuardar}>
          {aGuardar ? "A criar…" : "Criar conta"}
        </button>
        <p className="text-center text-sm text-gray-500">
          Já tem conta?{" "}
          <Link href="/login" className="font-medium text-primaria">
            Entrar
          </Link>
        </p>
      </form>
    </div>
  );
}
