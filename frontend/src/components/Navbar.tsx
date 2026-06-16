"use client";
// Navbar.tsx — Barra de navegação superior, presente em todas as páginas.

import Link from "next/link";
import { useAuth } from "@/lib/auth";

// Ligações visíveis a toda a gente (incluindo visitantes).
const LIGACOES = [
  { href: "/biblioteca", rotulo: "Biblioteca" },
  { href: "/pesquisa-semantica", rotulo: "Descobrir" },
  { href: "/pesquisa", rotulo: "Pesquisar" },
  { href: "/autores", rotulo: "Autores" },
];

// Perfis que podem publicar documentos.
const PERFIS_PUBLICADORES = ["professor", "investigador", "administrador"];

export default function Navbar() {
  const { utilizador, logout } = useAuth();
  const podePublicar =
    utilizador && PERFIS_PUBLICADORES.includes(utilizador.perfil);
  const eAdmin = utilizador?.perfil === "administrador";

  return (
    <header className="sticky top-0 z-20 border-b border-gray-200 bg-white/90 backdrop-blur">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link href="/" className="flex items-center gap-2">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-primaria font-bold text-white">
            B
          </span>
          <span className="text-lg font-semibold text-gray-800">
            Academic Hub
          </span>
        </Link>

        <div className="hidden items-center gap-5 md:flex">
          {LIGACOES.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-sm font-medium text-gray-600 hover:text-primaria"
            >
              {l.rotulo}
            </Link>
          ))}
          {utilizador && (
            <Link
              href="/emprestimos"
              className="text-sm font-medium text-gray-600 hover:text-primaria"
            >
              Empréstimos
            </Link>
          )}
          {utilizador && (
            <Link
              href="/favoritos"
              className="text-sm font-medium text-gray-600 hover:text-primaria"
            >
              Favoritos
            </Link>
          )}
          {podePublicar && (
            <Link
              href="/publicar"
              className="text-sm font-medium text-primaria hover:underline"
            >
              Publicar
            </Link>
          )}
          {eAdmin && (
            <Link
              href="/admin"
              className="text-sm font-medium text-roxo hover:underline"
            >
              Admin
            </Link>
          )}
        </div>

        <div className="flex items-center gap-3">
          {utilizador ? (
            <>
              <Link href="/dashboard" className="text-sm font-medium text-gray-700 hover:text-primaria">
                {utilizador.nome.split(" ")[0]}
              </Link>
              <button onClick={logout} className="btn-secundario py-1.5 text-sm">
                Sair
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="btn-secundario py-1.5 text-sm">
                Entrar
              </Link>
              <Link href="/registo" className="btn-primario py-1.5 text-sm">
                Criar conta
              </Link>
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
