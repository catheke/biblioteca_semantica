// Footer.tsx — Rodapé do site, com navegação, ajuda e contacto.
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
    <footer className="mt-16 border-t border-gray-200 bg-white">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-12 sm:grid-cols-2 lg:grid-cols-4">
        {/* Marca */}
        <div>
          <div className="flex items-center gap-2">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-primaria font-bold text-white">
              B
            </span>
            <span className="text-lg font-semibold text-gray-800">
              Academic Hub
            </span>
          </div>
          <p className="mt-3 text-sm leading-relaxed text-gray-500">
            Biblioteca académica que liga obras, autores e temas de investigação
            para encontrar conhecimento com mais facilidade.
          </p>
        </div>

        {/* Navegação */}
        <div>
          <h3 className="text-sm font-semibold text-gray-800">Navegar</h3>
          <ul className="mt-3 space-y-2">
            {NAVEGACAO.map((l) => (
              <li key={l.href}>
                <Link
                  href={l.href}
                  className="text-sm text-gray-500 hover:text-primaria"
                >
                  {l.rotulo}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Ajuda */}
        <div>
          <h3 className="text-sm font-semibold text-gray-800">Ajuda</h3>
          <ul className="mt-3 space-y-2">
            {AJUDA.map((l) => (
              <li key={l.rotulo}>
                <Link
                  href={l.href}
                  className="text-sm text-gray-500 hover:text-primaria"
                >
                  {l.rotulo}
                </Link>
              </li>
            ))}
          </ul>
        </div>

        {/* Contacto e localização */}
        <div>
          <h3 className="text-sm font-semibold text-gray-800">Contacto</h3>
          <ul className="mt-3 space-y-2 text-sm text-gray-500">
            <li>Faculdade de Ciências da Computação</li>
            <li>Lubango, Huíla — Angola</li>
            <li>
              <a
                href="mailto:biblioteca@basi.ao"
                className="hover:text-primaria"
              >
                biblioteca@basi.ao
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div className="border-t border-gray-100 py-5">
        <p className="mx-auto max-w-6xl px-4 text-center text-xs text-gray-400">
          © {ano} Academic Hub (BASI). Todos os direitos reservados.
        </p>
      </div>
    </footer>
  );
}
