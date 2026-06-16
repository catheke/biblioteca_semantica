// page.tsx — Página inicial (Home). Apresenta a plataforma e o seu diferencial.
import Link from "next/link";

// Ícones (SVG simples, traço — sem emojis).
const Icone = {
  lupa: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
      <circle cx="11" cy="11" r="7" />
      <path d="m21 21-4.3-4.3" />
    </svg>
  ),
  pessoas: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
      <circle cx="9" cy="7" r="4" />
      <path d="M22 21v-2a4 4 0 0 0-3-3.87" />
      <path d="M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  livros: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" className="h-6 w-6">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
    </svg>
  ),
  documento: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6" />
    </svg>
  ),
};

const FUNCIONALIDADES = [
  {
    icone: Icone.lupa,
    titulo: "Encontre mais do que procurou",
    texto:
      "Pesquise por um tema e descubra também os assuntos relacionados. Procure “Inteligência Artificial” e veja igualmente obras sobre aprendizagem automática e redes neurais.",
  },
  {
    icone: Icone.pessoas,
    titulo: "Acompanhe quem lhe interessa",
    texto:
      "Siga professores e investigadores, guarde os seus livros favoritos e receba sugestões de leitura segundo os temas que mais consulta.",
  },
  {
    icone: Icone.livros,
    titulo: "Tudo num só lugar",
    texto:
      "Livros, artigos, teses e materiais de apoio às aulas, organizados por área e por tema — fáceis de ler ou descarregar.",
  },
];

const PASSOS = [
  {
    n: "1",
    titulo: "Escreva um tema",
    texto: "Comece por aquilo que quer estudar — uma palavra basta.",
  },
  {
    n: "2",
    titulo: "Veja o que se relaciona",
    texto: "Mostramos temas próximos que muitas vezes lhe escapariam.",
  },
  {
    n: "3",
    titulo: "Leia e guarde",
    texto: "Abra as obras, descarregue e guarde nos favoritos.",
  },
];

export default function Home() {
  return (
    <div>
      {/* ---------------- HERO ---------------- */}
      <section className="relative overflow-hidden bg-gradient-to-b from-white via-fundo to-fundo">
        {/* Manchas decorativas */}
        <div className="pointer-events-none absolute -left-24 -top-24 h-72 w-72 rounded-full bg-primaria/10 blur-3xl" />
        <div className="pointer-events-none absolute -right-20 top-20 h-72 w-72 rounded-full bg-roxo/10 blur-3xl" />

        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-20 lg:grid-cols-2 lg:py-28">
          {/* Texto */}
          <div className="text-center lg:text-left">
            <span className="chip">Biblioteca digital · Universidade</span>
            <h1 className="mt-4 text-4xl font-extrabold leading-tight tracking-tight text-gray-900 sm:text-5xl">
              A rede académica que{" "}
              <span className="bg-gradient-to-r from-primaria to-roxo bg-clip-text text-transparent">
                compreende
              </span>{" "}
              o que procura
            </h1>
            <p className="mx-auto mt-5 max-w-xl text-lg leading-relaxed text-gray-600 lg:mx-0">
              Descubra as relações entre obras, autores e temas de investigação.
              Uma biblioteca inteligente que lhe mostra também o que está
              relacionado com aquilo que procura.
            </p>
            <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row lg:justify-start">
              <Link href="/pesquisa-semantica" className="btn-primario px-6 py-3 text-base">
                Começar a descobrir
              </Link>
              <Link href="/biblioteca" className="btn-secundario px-6 py-3 text-base">
                Explorar a biblioteca
              </Link>
            </div>
          </div>

          {/* Visual: simulação de pesquisa semântica */}
          <div className="relative mx-auto w-full max-w-md">
            <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-xl shadow-primaria/5">
              <div className="flex items-center gap-2 rounded-lg border border-gray-200 bg-fundo px-3 py-2.5">
                <span className="text-gray-400">{Icone.lupa}</span>
                <span className="text-sm text-gray-700">Inteligência Artificial</span>
              </div>

              <p className="mt-5 text-xs font-medium uppercase tracking-wider text-gray-400">
                Também relacionado com
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {["Machine Learning", "Redes Neurais", "Visão Computacional", "Dados"].map(
                  (t) => (
                    <span key={t} className="chip">
                      {t}
                    </span>
                  ),
                )}
              </div>

              <p className="mt-5 text-xs font-medium uppercase tracking-wider text-gray-400">
                Obras encontradas
              </p>
              <ul className="mt-2 space-y-2">
                {[
                  "Fundamentos de Aprendizagem Automática",
                  "Introdução às Redes Neurais",
                  "IA na Prática",
                ].map((titulo) => (
                  <li
                    key={titulo}
                    className="flex items-center gap-3 rounded-lg border border-gray-100 bg-white px-3 py-2"
                  >
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-md bg-blue-50 text-primaria">
                      {Icone.documento}
                    </span>
                    <span className="truncate text-sm text-gray-700">{titulo}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- COMO FUNCIONA ---------------- */}
      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 sm:text-3xl">
            Encontrar conhecimento em três passos
          </h2>
          <p className="mx-auto mt-2 max-w-2xl text-gray-600">
            Sem jargão, sem complicações. Comece por um tema e deixe a
            biblioteca guiá-lo.
          </p>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-3">
          {PASSOS.map((p) => (
            <div key={p.n} className="cartao text-center">
              <span className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-gradient-to-br from-primaria to-roxo text-lg font-bold text-white">
                {p.n}
              </span>
              <h3 className="mt-4 text-lg font-semibold text-gray-800">{p.titulo}</h3>
              <p className="mt-1 text-gray-600">{p.texto}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ---------------- FUNCIONALIDADES ---------------- */}
      <section className="bg-white">
        <div className="mx-auto max-w-6xl px-4 py-16">
          <div className="grid gap-6 md:grid-cols-3">
            {FUNCIONALIDADES.map((f) => (
              <div key={f.titulo} className="cartao">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-blue-50 text-primaria">
                  {f.icone}
                </span>
                <h3 className="mb-2 mt-4 text-lg font-semibold text-gray-800">
                  {f.titulo}
                </h3>
                <p className="text-gray-600">{f.texto}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- CHAMADA FINAL ---------------- */}
      <section className="mx-auto max-w-6xl px-4 pb-20 pt-4">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-primaria to-roxo px-8 py-14 text-center text-white shadow-xl">
          <h2 className="text-2xl font-bold sm:text-3xl">
            Pronto para descobrir mais?
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-white/90">
            Crie a sua conta gratuita e comece a explorar a biblioteca académica
            da universidade.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/registo"
              className="inline-flex items-center justify-center rounded-lg bg-white px-6 py-3 font-medium text-primaria transition hover:bg-gray-100"
            >
              Criar conta
            </Link>
            <Link
              href="/pesquisa-semantica"
              className="inline-flex items-center justify-center rounded-lg border border-white/70 px-6 py-3 font-medium text-white transition hover:bg-white/10"
            >
              Experimentar a pesquisa
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
