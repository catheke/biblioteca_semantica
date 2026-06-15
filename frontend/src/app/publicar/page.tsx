"use client";
// publicar/page.tsx — Formulário para professores/investigadores/admin
// publicarem um novo documento. Visitantes e estudantes não têm acesso.

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { NivelAcesso, TipoDocumento } from "@/types";

const PERFIS_PUBLICADORES = ["professor", "investigador", "administrador"];

const TIPOS: TipoDocumento[] = [
  "livro",
  "artigo",
  "tese",
  "monografia",
  "manual",
  "apresentacao",
  "material_didactico",
];

const NIVEIS: { valor: NivelAcesso; rotulo: string }[] = [
  { valor: "publico", rotulo: "Público — qualquer pessoa descarrega" },
  { valor: "autenticado", rotulo: "Autenticado — só com sessão iniciada" },
  { valor: "academico", rotulo: "Académico — professores/investigadores/admin" },
];

export default function PaginaPublicar() {
  const { utilizador, carregando } = useAuth();
  const router = useRouter();

  const [titulo, setTitulo] = useState("");
  const [autorNome, setAutorNome] = useState("");
  const [tipo, setTipo] = useState<TipoDocumento>("livro");
  const [ano, setAno] = useState("");
  const [resumo, setResumo] = useState("");
  const [ficheiroUrl, setFicheiroUrl] = useState("");
  const [capaUrl, setCapaUrl] = useState("");
  const [nivel, setNivel] = useState<NivelAcesso>("publico");
  const [erro, setErro] = useState("");
  const [aGuardar, setAGuardar] = useState(false);

  // ---- Controlo de acesso na própria UI (o backend valida na mesma) ----
  if (carregando)
    return <p className="px-4 py-16 text-gray-500">A carregar…</p>;

  if (!utilizador || !PERFIS_PUBLICADORES.includes(utilizador.perfil))
    return (
      <div className="mx-auto max-w-md px-4 py-16 text-center">
        <h1 className="text-2xl font-bold text-gray-800">Acesso restrito</h1>
        <p className="mt-2 text-gray-500">
          Só professores, investigadores e administradores podem publicar
          documentos.
        </p>
        <Link href="/biblioteca" className="btn-primario mt-6 inline-block">
          Voltar à biblioteca
        </Link>
      </div>
    );

  async function submeter(e: React.FormEvent) {
    e.preventDefault();
    setErro("");
    setAGuardar(true);
    try {
      const doc = await api.publicarDocumento({
        titulo,
        autor_nome: autorNome || null,
        tipo,
        ano_publicacao: ano ? Number(ano) : null,
        resumo: resumo || null,
        ficheiro_url: ficheiroUrl || null,
        capa_url: capaUrl || null,
        nivel_acesso: nivel,
      });
      router.push(`/documento/${doc.id}`);
    } catch (err) {
      setErro((err as Error).message);
    } finally {
      setAGuardar(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <h1 className="text-2xl font-bold text-gray-800">Publicar documento</h1>
      <p className="mt-1 text-gray-500">
        Adicione uma obra ao catálogo da biblioteca.
      </p>

      <form onSubmit={submeter} className="cartao mt-6 space-y-4">
        <div>
          <label className="etiqueta">Título *</label>
          <input
            className="campo"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
            required
            minLength={3}
          />
        </div>

        <div>
          <label className="etiqueta">Autor da obra</label>
          <input
            className="campo"
            value={autorNome}
            onChange={(e) => setAutorNome(e.target.value)}
            placeholder="Ex.: Machado de Assis"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="etiqueta">Tipo</label>
            <select
              className="campo"
              value={tipo}
              onChange={(e) => setTipo(e.target.value as TipoDocumento)}
            >
              {TIPOS.map((t) => (
                <option key={t} value={t}>
                  {t.replace("_", " ")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="etiqueta">Ano</label>
            <input
              type="number"
              className="campo"
              value={ano}
              onChange={(e) => setAno(e.target.value)}
              placeholder="2024"
            />
          </div>
        </div>

        <div>
          <label className="etiqueta">Resumo</label>
          <textarea
            className="campo"
            rows={3}
            value={resumo}
            onChange={(e) => setResumo(e.target.value)}
          />
        </div>

        <div>
          <label className="etiqueta">URL do ficheiro (leitura/descarga)</label>
          <input
            className="campo"
            value={ficheiroUrl}
            onChange={(e) => setFicheiroUrl(e.target.value)}
            placeholder="https://…"
          />
        </div>

        <div>
          <label className="etiqueta">URL da capa</label>
          <input
            className="campo"
            value={capaUrl}
            onChange={(e) => setCapaUrl(e.target.value)}
            placeholder="https://…"
          />
        </div>

        <div>
          <label className="etiqueta">Nível de acesso</label>
          <select
            className="campo"
            value={nivel}
            onChange={(e) => setNivel(e.target.value as NivelAcesso)}
          >
            {NIVEIS.map((n) => (
              <option key={n.valor} value={n.valor}>
                {n.rotulo}
              </option>
            ))}
          </select>
        </div>

        {erro && <p className="text-sm text-red-600">{erro}</p>}

        <button
          type="submit"
          className="btn-primario w-full"
          disabled={aGuardar}
        >
          {aGuardar ? "A publicar…" : "Publicar documento"}
        </button>
      </form>
    </div>
  );
}
