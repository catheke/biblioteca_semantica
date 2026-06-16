"use client";
// documento/[id]/page.tsx — Detalhe de um documento + leitura/descarga + favorito.
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Disponibilidade, Documento } from "@/types";
import CapaLivro from "@/components/CapaLivro";

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

  // Circulação física: disponibilidade e acções de requisitar/reservar.
  const [disp, setDisp] = useState<Disponibilidade | null>(null);
  const [aProcessar, setAProcessar] = useState(false);
  const [msgCirc, setMsgCirc] = useState("");
  const [erroCirc, setErroCirc] = useState("");

  useEffect(() => {
    api.obterDocumento(id).then(setDoc).catch((e) => setErro(e.message));
  }, [id]);

  const carregarDisp = useCallback(() => {
    api.disponibilidade(id).then(setDisp).catch(() => setDisp(null));
  }, [id]);

  useEffect(() => {
    carregarDisp();
  }, [carregarDisp, utilizador]);

  async function requisitar() {
    setMsgCirc("");
    setErroCirc("");
    setAProcessar(true);
    try {
      const emp = await api.requisitar(id);
      setMsgCirc(
        `Obra requisitada. Devolva até ${new Date(emp.data_prevista_devolucao).toLocaleDateString("pt-PT")}.`,
      );
      carregarDisp();
    } catch (e) {
      setErroCirc((e as Error).message);
    } finally {
      setAProcessar(false);
    }
  }

  async function reservar() {
    setMsgCirc("");
    setErroCirc("");
    setAProcessar(true);
    try {
      const r = await api.reservar(id);
      setMsgCirc(
        r.posicao
          ? `Reserva registada. Está na posição ${r.posicao} da fila.`
          : "Reserva registada.",
      );
      carregarDisp();
    } catch (e) {
      setErroCirc((e as Error).message);
    } finally {
      setAProcessar(false);
    }
  }

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
        <div className="mx-auto h-72 w-52 flex-shrink-0">
          <CapaLivro doc={doc} className="h-full shadow-md" />
        </div>

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

      {/* ----------------------- Disponibilidade física ----------------------- */}
      {disp && disp.total_exemplares > 0 && (
        <section className="mt-10 rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="text-lg font-semibold text-gray-800">
            Requisição na biblioteca
          </h2>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <span
              className={`chip ${
                disp.disponiveis > 0
                  ? "bg-green-50 text-green-700"
                  : "bg-red-50 text-red-700"
              }`}
            >
              {disp.disponiveis > 0
                ? `${disp.disponiveis} de ${disp.total_exemplares} disponíveis`
                : "Todos os exemplares emprestados"}
            </span>
            {disp.reservas_em_espera > 0 && (
              <span className="chip bg-amber-50 text-dourado">
                {disp.reservas_em_espera} em lista de espera
              </span>
            )}
          </div>

          {/* Estado pessoal do leitor */}
          {disp.ja_tem_emprestimo && (
            <p className="mt-3 text-sm text-gray-600">
              Já tem esta obra requisitada. Veja em{" "}
              <Link href="/emprestimos" className="text-primaria hover:underline">
                A minha biblioteca
              </Link>
              .
            </p>
          )}
          {disp.ja_reservou && (
            <p className="mt-3 text-sm text-gray-600">
              Já tem uma reserva activa para esta obra.
            </p>
          )}

          <div className="mt-4 flex flex-wrap gap-3">
            {!utilizador ? (
              <Link href="/login" className="btn-primario">
                Inicie sessão para requisitar
              </Link>
            ) : (
              <>
                {disp.pode_requisitar && (
                  <button
                    onClick={requisitar}
                    disabled={aProcessar}
                    className="btn-primario disabled:opacity-50"
                  >
                    {aProcessar ? "A processar…" : "Requisitar"}
                  </button>
                )}
                {disp.pode_reservar && (
                  <button
                    onClick={reservar}
                    disabled={aProcessar}
                    className="btn-secundario disabled:opacity-50"
                  >
                    {aProcessar ? "A processar…" : "Reservar (entrar na fila)"}
                  </button>
                )}
              </>
            )}
          </div>

          {/* Motivo quando não pode requisitar nem reservar */}
          {utilizador &&
            !disp.pode_requisitar &&
            !disp.pode_reservar &&
            !disp.ja_tem_emprestimo &&
            !disp.ja_reservou &&
            disp.motivo && (
              <p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-dourado">
                {disp.motivo}
              </p>
            )}

          {msgCirc && (
            <div className="mt-4 rounded-lg bg-green-50 p-3 text-sm text-green-700">
              {msgCirc}
            </div>
          )}
          {erroCirc && (
            <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">
              {erroCirc}
            </div>
          )}
        </section>
      )}
    </article>
  );
}
