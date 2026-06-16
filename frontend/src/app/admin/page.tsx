"use client";
// admin/page.tsx — Painel de administração (só para perfil 'administrador').
// Gere utilizadores E o catálogo de documentos (inserir / apagar livros).
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Documento, SeccaoBiblioteca, Utilizador } from "@/types";

const ACESSO: Record<string, string> = {
  publico: "bg-green-50 text-green-700",
  autenticado: "bg-amber-50 text-dourado",
  academico: "bg-red-50 text-red-700",
};

const TIPOS = [
  "livro",
  "artigo",
  "tese",
  "monografia",
  "manual",
  "apresentacao",
  "material_didactico",
] as const;

const NIVEIS = [
  { valor: "publico", texto: "Público — qualquer pessoa descarrega" },
  { valor: "autenticado", texto: "Requer sessão iniciada" },
  { valor: "academico", texto: "Académico — professores/investigadores" },
] as const;

// Temas já existentes na ontologia (sugestões). O admin pode escrever um novo —
// nesse caso é criado um tema novo no grafo RDF automaticamente.
const TEMAS_SUGERIDOS = [
  "Inteligência Artificial",
  "Machine Learning",
  "Deep Learning",
  "Redes Neurais",
  "Ciência de Dados",
  "Visão Computacional",
  "Web Semântica",
  "Cardiologia",
];

// Géneros literários (auxiliares de forma da CDU) — só usados na secção 82.
const GENEROS = ["Romance", "Conto", "Poesia", "Teatro"];

const FORM_VAZIO = {
  titulo: "",
  tipo: "livro",
  nivel_acesso: "publico",
  autor_nome: "",
  resumo: "",
  ano_publicacao: "",
  idioma: "Português",
  area_id: "",
  genero: "",
  tema: "",
};

export default function PaginaAdmin() {
  const { utilizador, carregando } = useAuth();
  const router = useRouter();
  const [utilizadores, setUtilizadores] = useState<Utilizador[]>([]);
  const [documentos, setDocumentos] = useState<Documento[]>([]);
  const [seccoes, setSeccoes] = useState<SeccaoBiblioteca[]>([]);
  const [erro, setErro] = useState("");

  // ---- Estado do formulário de carregamento local ----
  const [mostrarForm, setMostrarForm] = useState(false);
  const [campos, setCampos] = useState({ ...FORM_VAZIO });
  const [ficheiro, setFicheiro] = useState<File | null>(null);
  const [capa, setCapa] = useState<File | null>(null);
  const [aEnviar, setAEnviar] = useState(false);
  const [sucesso, setSucesso] = useState("");

  // Secção escolhida no formulário — o género só se aplica à Literatura (82).
  const seccaoSel = seccoes.find((s) => String(s.area_id) === campos.area_id);
  const ehLiteratura = seccaoSel?.codigo === "82";

  function carregarDocumentos() {
    api
      .listarDocumentos({ por_pagina: 100 })
      .then((p) => setDocumentos(p.itens));
  }

  function actualizarCampo(
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >,
  ) {
    setCampos((c) => ({ ...c, [e.target.name]: e.target.value }));
  }

  async function enviarUpload(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setSucesso("");
    if (!ficheiro) {
      setErro("Escolha o ficheiro do livro (PDF, EPUB, TXT, DOC…).");
      return;
    }
    setAEnviar(true);
    try {
      const form = new FormData();
      form.append("titulo", campos.titulo);
      form.append("tipo", campos.tipo);
      form.append("nivel_acesso", campos.nivel_acesso);
      if (campos.autor_nome) form.append("autor_nome", campos.autor_nome);
      if (campos.resumo) form.append("resumo", campos.resumo);
      if (campos.ano_publicacao)
        form.append("ano_publicacao", campos.ano_publicacao);
      if (campos.idioma) form.append("idioma", campos.idioma);
      if (campos.area_id) form.append("area_id", campos.area_id);
      if (ehLiteratura && campos.genero) form.append("genero", campos.genero);
      if (campos.tema) form.append("tema", campos.tema);
      form.append("ficheiro", ficheiro);
      if (capa) form.append("capa", capa);

      const novo = await api.carregarDocumento(form);
      setDocumentos((lista) => [novo, ...lista]);
      setSucesso(`"${novo.titulo}" foi carregado com sucesso.`);
      // Limpar o formulário.
      setCampos({ ...FORM_VAZIO });
      setFicheiro(null);
      setCapa(null);
      setMostrarForm(false);
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setAEnviar(false);
    }
  }

  useEffect(() => {
    if (!carregando) {
      // Protecção de rota: só administradores entram.
      if (!utilizador) router.push("/login");
      else if (utilizador.perfil !== "administrador") router.push("/dashboard");
      else {
        api.listarUtilizadores().then((p) => setUtilizadores(p.itens));
        api.seccoesBiblioteca().then(setSeccoes).catch(() => setSeccoes([]));
        carregarDocumentos();
      }
    }
  }, [utilizador, carregando, router]);

  async function apagar(doc: Documento) {
    if (!confirm(`Apagar "${doc.titulo}"? Esta acção é irreversível.`)) return;
    setErro("");
    try {
      await api.eliminarDocumento(doc.id);
      setDocumentos((lista) => lista.filter((d) => d.id !== doc.id));
    } catch (e) {
      setErro((e as Error).message);
    }
  }

  if (!utilizador || utilizador.perfil !== "administrador") return null;

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Administração</h1>
          <p className="mt-1 text-gray-500">
            Gestão de utilizadores e do catálogo de documentos.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/admin/estatisticas" className="btn-secundario py-1.5 text-sm">
            Estatísticas
          </Link>
          <Link href="/admin/circulacao" className="btn-primario py-1.5 text-sm">
            Circulação (empréstimos e multas)
          </Link>
        </div>
      </div>

      {erro && (
        <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {erro}
        </div>
      )}
      {sucesso && (
        <div className="mt-4 rounded-lg bg-green-50 p-3 text-sm text-green-700">
          {sucesso}
        </div>
      )}

      {/* ----------------------- Catálogo de documentos ----------------------- */}
      <section className="mt-8">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">
            Documentos ({documentos.length})
          </h2>
          <button
            onClick={() => {
              setMostrarForm((v) => !v);
              setSucesso("");
              setErro("");
            }}
            className="btn-primario py-1.5 text-sm"
          >
            {mostrarForm ? "Fechar" : "+ Carregar livro (ficheiro local)"}
          </button>
        </div>

        {/* ----------- Formulário de carregamento de ficheiro local ----------- */}
        {mostrarForm && (
          <form
            onSubmit={enviarUpload}
            className="cartao mt-4 grid grid-cols-1 gap-4 md:grid-cols-2"
          >
            <p className="md:col-span-2 text-sm text-gray-500">
              O ficheiro é guardado <strong>no servidor do projeto</strong> e
              fica disponível para ler/descarregar dentro da plataforma. Use
              apenas livros que possa partilhar legalmente.
            </p>

            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">Título *</span>
              <input
                name="titulo"
                value={campos.titulo}
                onChange={actualizarCampo}
                required
                className="campo"
                placeholder="Ex.: Introdução à Web Semântica"
              />
            </label>

            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">Autor</span>
              <input
                name="autor_nome"
                value={campos.autor_nome}
                onChange={actualizarCampo}
                className="campo"
                placeholder="Nome do autor"
              />
            </label>

            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">Tipo</span>
              <select
                name="tipo"
                value={campos.tipo}
                onChange={actualizarCampo}
                className="campo capitalize"
              >
                {TIPOS.map((t) => (
                  <option key={t} value={t}>
                    {t.replace("_", " ")}
                  </option>
                ))}
              </select>
            </label>

            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">Nível de acesso</span>
              <select
                name="nivel_acesso"
                value={campos.nivel_acesso}
                onChange={actualizarCampo}
                className="campo"
              >
                {NIVEIS.map((n) => (
                  <option key={n.valor} value={n.valor}>
                    {n.texto}
                  </option>
                ))}
              </select>
            </label>

            {/* Secção da biblioteca (estante CDU). Define onde o livro fica
                arrumado. Se for Literatura (82), aparece também o género. */}
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">
                Secção (estante CDU)
              </span>
              <select
                name="area_id"
                value={campos.area_id}
                onChange={actualizarCampo}
                className="campo"
              >
                <option value="">— Sem secção —</option>
                {seccoes.map((s) => (
                  <option key={s.area_id} value={String(s.area_id)}>
                    {s.codigo ? `${s.codigo} · ${s.nome}` : s.nome}
                  </option>
                ))}
              </select>
            </label>

            {ehLiteratura ? (
              <label className="flex flex-col gap-1 text-sm">
                <span className="font-medium text-gray-700">
                  Género literário
                </span>
                <select
                  name="genero"
                  value={campos.genero}
                  onChange={actualizarCampo}
                  className="campo"
                >
                  <option value="">— Escolha o género —</option>
                  {GENEROS.map((g) => (
                    <option key={g} value={g}>
                      {g}
                    </option>
                  ))}
                </select>
              </label>
            ) : (
              <div className="hidden md:block" />
            )}

            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">Ano</span>
              <input
                name="ano_publicacao"
                type="number"
                value={campos.ano_publicacao}
                onChange={actualizarCampo}
                className="campo"
                placeholder="Ex.: 2021"
              />
            </label>

            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">Idioma</span>
              <input
                name="idioma"
                value={campos.idioma}
                onChange={actualizarCampo}
                className="campo"
              />
            </label>

            <label className="flex flex-col gap-1 text-sm md:col-span-2">
              <span className="font-medium text-gray-700">
                Tema (liga à pesquisa semântica)
              </span>
              <input
                name="tema"
                list="temas-sugeridos"
                value={campos.tema}
                onChange={actualizarCampo}
                className="campo"
                placeholder="Ex.: Inteligência Artificial (ou escreva um tema novo)"
              />
              <datalist id="temas-sugeridos">
                {TEMAS_SUGERIDOS.map((t) => (
                  <option key={t} value={t} />
                ))}
              </datalist>
              <span className="text-xs text-gray-400">
                Com tema, o livro passa a aparecer na pesquisa semântica (e nos
                temas relacionados). Sem tema, fica só no catálogo.
              </span>
            </label>

            <label className="flex flex-col gap-1 text-sm md:col-span-2">
              <span className="font-medium text-gray-700">Resumo</span>
              <textarea
                name="resumo"
                value={campos.resumo}
                onChange={actualizarCampo}
                rows={3}
                className="campo"
                placeholder="Breve descrição do conteúdo…"
              />
            </label>

            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">
                Ficheiro do livro * (PDF, EPUB, TXT, DOC…)
              </span>
              <input
                type="file"
                accept=".pdf,.epub,.txt,.doc,.docx,.rtf"
                onChange={(e) => setFicheiro(e.target.files?.[0] ?? null)}
                required
                className="text-sm text-gray-600 file:mr-3 file:rounded-lg file:border-0 file:bg-blue-50 file:px-3 file:py-2 file:text-primaria"
              />
            </label>

            <label className="flex flex-col gap-1 text-sm">
              <span className="font-medium text-gray-700">
                Capa (imagem, opcional)
              </span>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setCapa(e.target.files?.[0] ?? null)}
                className="text-sm text-gray-600 file:mr-3 file:rounded-lg file:border-0 file:bg-blue-50 file:px-3 file:py-2 file:text-primaria"
              />
            </label>

            <div className="md:col-span-2 flex items-center gap-3">
              <button
                type="submit"
                disabled={aEnviar}
                className="btn-primario disabled:opacity-50"
              >
                {aEnviar ? "A carregar…" : "Carregar livro"}
              </button>
              <Link href="/publicar" className="text-sm text-gray-500 hover:underline">
                Inserir sem ficheiro (apenas metadados)
              </Link>
            </div>
          </form>
        )}

        <div className="cartao mt-4 overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 text-gray-500">
              <tr>
                <th className="px-4 py-3">Título</th>
                <th className="px-4 py-3">Autor</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Acesso</th>
                <th className="px-4 py-3 text-right">Acções</th>
              </tr>
            </thead>
            <tbody>
              {documentos.map((d) => (
                <tr key={d.id} className="border-b border-gray-100">
                  <td className="px-4 py-3 font-medium text-gray-800">
                    <Link
                      href={`/documento/${d.id}`}
                      className="hover:text-primaria"
                    >
                      {d.titulo}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-600">
                    {d.autor_nome ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="chip capitalize">
                      {d.tipo.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`chip ${ACESSO[d.nivel_acesso ?? "publico"]}`}>
                      {d.nivel_acesso ?? "publico"}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => apagar(d)}
                      className="text-sm font-medium text-red-600 hover:underline"
                    >
                      Apagar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* ----------------------- Utilizadores ----------------------- */}
      <section className="mt-10">
        <h2 className="text-lg font-semibold text-gray-800">
          Utilizadores ({utilizadores.length})
        </h2>
        <div className="cartao mt-4 overflow-x-auto p-0">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 text-gray-500">
              <tr>
                <th className="px-4 py-3">Nome</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Perfil</th>
              </tr>
            </thead>
            <tbody>
              {utilizadores.map((u) => (
                <tr key={u.id} className="border-b border-gray-100">
                  <td className="px-4 py-3 font-medium text-gray-800">{u.nome}</td>
                  <td className="px-4 py-3 text-gray-600">{u.email}</td>
                  <td className="px-4 py-3">
                    <span className="chip capitalize">{u.perfil}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
