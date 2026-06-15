// page.tsx — Página inicial (Home). Apresenta a plataforma e o diferencial.
import Link from "next/link";

const FUNCIONALIDADES = [
  {
    titulo: "Encontre mais do que procurou",
    texto:
      "Pesquise por um tema e a plataforma sugere também assuntos relacionados. Por exemplo, ao procurar 'Inteligência Artificial' também lhe mostramos obras sobre aprendizagem automática e redes neurais.",
  },
  {
    titulo: "Acompanhe quem lhe interessa",
    texto:
      "Siga professores e investigadores, guarde os seus livros favoritos e receba sugestões de leitura de acordo com os temas que mais consulta.",
  },
  {
    titulo: "Tudo num só lugar",
    texto:
      "Livros, artigos, teses e materiais de apoio às aulas reunidos e organizados por área e tema — fáceis de ler ou descarregar.",
  },
];

export default function Home() {
  return (
    <div>
      {/* Secção principal (hero) */}
      <section className="bg-gradient-to-b from-white to-fundo">
        <div className="mx-auto max-w-6xl px-4 py-20 text-center">
          <span className="chip">Biblioteca digital · Universidade</span>
          <h1 className="mx-auto mt-4 max-w-3xl text-4xl font-bold leading-tight text-gray-900 sm:text-5xl">
            A rede académica que{" "}
            <span className="text-primaria">compreende</span> o que procura
          </h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-600">
            Descubra relações entre obras, autores e temas de investigação. Uma
            biblioteca inteligente para universidades.
          </p>
          <div className="mt-8 flex justify-center gap-4">
            <Link href="/pesquisa-semantica" className="btn-primario">
              Começar a descobrir
            </Link>
            <Link href="/biblioteca" className="btn-secundario">
              Explorar a biblioteca
            </Link>
          </div>
        </div>
      </section>

      {/* Funcionalidades */}
      <section className="mx-auto max-w-6xl px-4 py-16">
        <div className="grid gap-6 md:grid-cols-3">
          {FUNCIONALIDADES.map((f) => (
            <div key={f.titulo} className="cartao">
              <h3 className="mb-2 text-lg font-semibold text-gray-800">
                {f.titulo}
              </h3>
              <p className="text-gray-600">{f.texto}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
