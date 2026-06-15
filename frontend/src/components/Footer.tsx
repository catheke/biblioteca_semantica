// Footer.tsx — Rodapé do site: marca, navegação, ajuda e instituição.
import Link from "next/link";

const NAVEGACAO = [
  { href: "/biblioteca", rotulo: "Biblioteca" },
  { href: "/pesquisa-semantica", rotulo: "Descobrir" },
  { href: "/pesquisa", rotulo: "Pesquisar" },
  { href: "/autores", rotulo: "Autores" },
];

const AJUDA = [
  { href: "/registo", rotulo: "Criar conta" },
  { href: "/login", rotulo: "Entrar" },
  { href: "/pesquisa-semantica", rotulo: "Como pesquisar" },
];

export default function Footer() {
  const ano = new Date().getFullYear();

  return (
    <footer className="mt-20 bg-gray-900 text-gray-300">
      {/* Faixa de destaque superior */}
      <div className="h-1 w-full bg-gradient-to-r from-primaria via-roxo to-dourado" />

      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-14 md:grid-cols-2 lg:grid-cols-12">
        {/* Marca + instituição */}
        <div className="lg:col-span-5">
          <div className="flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-xl bg-primaria text-lg font-bold text-white shadow-lg shadow-primaria/30">
              B
            </span>
            <div>
              <span className="block text-lg font-semibold text-white">
                Academic Hub
              </span>
              <span className="block text-xs uppercase tracking-widest text-gray-500">
                Biblioteca Semântica
              </span>
            </div>
          </div>
          <p className="mt-5 max-w-sm text-sm leading-relaxed text-gray-400">
            Uma biblioteca académica que liga obras, autores e temas de
            investigação — para encontrar conhecimento com mais facilidade e
            descobrir o que está relacionado.
          </p>
        </div>

        {/* Navegação */}
        <div className="lg:col-span-2">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-200">
            Navegar
          </h3>
          <ul className="mt-4 space-y-2.5">
            {NAVEGACAO.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  className="text-sm text-gray-400 transition hover:text-white"
                >
                  {l.rotulo}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Ajuda */}
        <div className="lg:col-span-2">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-200">
            Ajuda
          </h3>
          <ul className="mt-4 space-y-2.5">
            {AJUDA.map((l) => (
              <li key={l.rotulo}>
                <Link
                  href={l.href}
                  className="text-sm text-gray-400 transition hover:text-white"
                >
                  {l.rotulo}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Instituição e contacto */}
        <div className="lg:col-span-3">
          <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-200">
            Instituição
          </h3>
          <ul className="mt-4 space-y-2.5 text-sm text-gray-400">
            <li className="font-medium text-gray-300">
              Universidade Mandume ya Ndemufayo
            </li>
            <li>Instituto Politécnico da Huíla</li>
            <li>Lubango, Huíla — Angola</li>
            <li className="pt-1">
              <a
                href="mailto:biblioteca@basi.ao"
                className="inline-flex items-center gap-1 text-gray-300 transition hover:text-white"
              >
                biblioteca@basi.ao
              </a>
            </li>
          </ul>
        </div>
      </div>

      {/* Barra inferior */}
      <div className="border-t border-white/10">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-2 px-4 py-6 text-xs text-gray-500 sm:flex-row">
          <p>© {ano} Academic Hub (BASI). Todos os direitos reservados.</p>
          <p>Projecto académico de Web Semântica</p>
        </div>
      </div>
    </footer>
  );
}
