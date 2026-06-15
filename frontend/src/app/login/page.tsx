"use client";
// login/page.tsx — Formulário de início de sessão.

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "@/lib/auth";

export default function PaginaLogin() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("admin@basi.ao");
  const [palavra, setPalavra] = useState("password123");
  const [erro, setErro] = useState("");
  const [aGuardar, setAGuardar] = useState(false);

  async function submeter(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setAGuardar(true);
    try {
      await login(email, palavra);
      router.push("/dashboard");
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setAGuardar(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-4 py-16">
      <h1 className="text-2xl font-bold text-gray-800">Entrar</h1>
      <p className="mt-1 text-gray-500">Aceda à sua conta académica.</p>

      <form onSubmit={submeter} className="cartao mt-6 space-y-4">
        <div>
          <label className="etiqueta">Email</label>
          <input
            type="email"
            className="campo"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="etiqueta">Palavra-passe</label>
          <input
            type="password"
            className="campo"
            value={palavra}
            onChange={(e) => setPalavra(e.target.value)}
            required
          />
        </div>
        {erro && <p className="text-sm text-red-600">{erro}</p>}
        <button type="submit" className="btn-primario w-full" disabled={aGuardar}>
          {aGuardar ? "A entrar…" : "Entrar"}
        </button>
        <p className="text-center text-sm text-gray-500">
          Não tem conta?{" "}
          <Link href="/registo" className="font-medium text-primaria">
            Criar conta
          </Link>
        </p>
      </form>
      <p className="mt-4 text-center text-xs text-gray-400">
        Demonstração: admin@basi.ao / password123
      </p>
    </div>
  );
}
