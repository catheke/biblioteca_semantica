"use client";
// documento/[id]/page.tsx — Detalhe de um documento + leitura/descarga + favorito.
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, urlMedia } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Documento } from "@/types";

const ACESSO: Record<string, { texto: string; cor: string; nota: string }> = {
  publico: {
    texto: "Acesso público",
    cor: "bg-green-50 text-green-700",
    nota: "Qualquer pessoa pode ler e descarregar.",
  },
  autenticado: {
    texto: "Requer sessão",
    cor: "bg-amber-50 text-dourado",
    nota: "É preciso iniciar sessão para descarregar.",
  },
  academico: {
    texto: "Acesso académico",
    cor: "bg-red-50 text-red-700",
    nota: "Reservado a professores, investigadores e administradores.",
  },
};

export default function PaginaDetalhe() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const { utilizador } = useAuth();
  const [doc, setDoc] = useState<Documento | null>(null);
  const [erro, setErro] = useState("");
  const [favorito, setFavorito] = useState(false);
  const [aDescarregar, setADescarregar] = useState(false);
  const [avisoAcesso, setAvisoAcesso] = useState("");

  useEffect(() => {
    api.obterDocumento(id).then(setDoc).catch((e) => setErro(e.message));
  }, [id]);

  async function alternarFavorito() {
    if (!utilizador) return;
    if (favorito) {
      await api.removerFavorito(id);
      setFavorito(false);
    } else {
      await api.adicionarFavorito(id);
      setFavorito(true);
    }
  }

  async function lerOuDescarregar() {
    setAvisoAcesso("");
    setADescarregar(true);
    try {
      // O ficheiro é servido localmente pela API (respeitando o nível de
      // acesso). Trazemo-lo como Blob — assim o token segue no cabeçalho — e
      // abrimo-lo numa nova aba a partir de um URL temporário do navegador.
      const blob = await api.descarregar(id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      // Liberta o URL temporário passado um minuto (tempo de abrir a aba).
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
      if (doc) setDoc({ ...doc, num_downloads: doc.num_downloads + 1 });
    } catch (e) {
      // 401 -> precisa de sessão; 403 -> sem perfil suficiente.
      setAvisoAcesso((e as Error).message);
    } finally {
      setADescarregar(false);
    }
  }

  if (erro)
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-lg bg-red-50 p-4 text-red-700">{erro}</div>
      </div>
    );
  if (!doc) return <p className="px-4 py-10 text-gray-500">A carregar…</p>;

  const acesso = ACESSO[doc.nivel_acesso ?? "publico"];
  const temFicheiro = Boolean(doc.ficheiro_objecto || doc.ficheiro_url);

  return (
    <article className="mx-auto max-w-4xl px-4 py-10">
      <div className="flex flex-col gap-8 md:flex-row">
        {doc.capa_url && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={urlMedia(doc.capa_url)}
            alt={`Capa de ${doc.titulo}`}
            className="mx-auto h-72 w-52 flex-shrink-0 rounded-lg object-cover shadow-md"
          />
        )}

        <div className="flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="chip capitalize">{doc.tipo.replace("_", " ")}</span>
            <span className={`chip ${acesso.cor}`}>{acesso.texto}</span>
          </div>

          <h1 className="mt-3 text-3xl font-bold text-gray-900">{doc.titulo}</h1>
          {doc.autor_nome && (
            <p className="mt-1 text-lg text-gray-600">por {doc.autor_nome}</p>
          )}

          <div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-400">
            {doc.ano_publicacao && <span>{doc.ano_publicacao}</span>}
            {doc.idioma && <span>{doc.idioma}</span>}
            <span>{doc.num_visualizacoes} visualizações</span>
            <span>{doc.num_downloads} downloads</span>
          </div>

          <p className="mt-3 text-xs text-gray-500">{acesso.nota}</p>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              className="btn-primario disabled:opacity-50"
              onClick={lerOuDescarregar}
              disabled={!temFicheiro || aDescarregar}
            >
              {aDescarregar
                ? "A abrir…"
                : temFicheiro
                  ? "Ler / Descarregar"
                  : "Sem ficheiro disponível"}
            </button>
            {utilizador && (
              <button onClick={alternarFavorito} className="btn-secundario">
                {favorito ? "Remover dos favoritos" : "Guardar nos favoritos"}
              </button>
            )}
          </div>

          {avisoAcesso && (
            <div className="mt-4 rounded-lg bg-amber-50 p-3 text-sm text-dourado">
              {avisoAcesso}
            </div>
          )}
        </div>
      </div>

      {doc.resumo && (
        <p className="mt-8 leading-relaxed text-gray-700">{doc.resumo}</p>
      )}

      {doc.uri_semantica && (
        <p className="mt-6 break-all rounded-lg bg-gray-50 p-3 text-xs text-gray-500">
          Recurso semântico: {doc.uri_semantica}
        </p>
      )}
    </article>
  );
}
