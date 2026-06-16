// api.ts — Cliente HTTP central para a API do BASI.
// Junta o token JWT, trata erros e descodifica JSON num único sítio, para que as
// páginas não chamem fetch directamente.

import type {
  Disponibilidade,
  Documento,
  Emprestimo,
  Estatisticas,
  Exemplar,
  LeituraHistorico,
  Multa,
  Notificacoes,
  Pagina,
  PesquisaHistorico,
  RelatorioCirculacao,
  Reserva,
  RespostaSemantica,
  ResultadoPesquisa,
  SeccaoBiblioteca,
  Tokens,
  Utilizador,
} from "@/types";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

// Origem do servidor (sem o /api/v1) — usada para servir media local (capas).
const ORIGEM = BASE_URL.replace(/\/api\/v1\/?$/, "");

const CHAVE_TOKEN = "basi_access_token";

/** Constrói o URL completo de um recurso de media local (ex.: capa de livro). */
export function urlMedia(caminho?: string | null): string | undefined {
  if (!caminho) return undefined;
  return caminho.startsWith("http") ? caminho : `${ORIGEM}${caminho}`;
}

// ---- Gestão do token no navegador (localStorage) ----
export function guardarToken(token: string) {
  if (typeof window !== "undefined") localStorage.setItem(CHAVE_TOKEN, token);
}
export function obterToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(CHAVE_TOKEN);
}
export function removerToken() {
  if (typeof window !== "undefined") localStorage.removeItem(CHAVE_TOKEN);
}

// ---- Função base de pedido ----
async function pedir<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const token = obterToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opcoes.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  let resposta: Response;
  try {
    resposta = await fetch(`${BASE_URL}${caminho}`, { ...opcoes, headers });
  } catch {
    // Falha de rede (servidor em baixo, sem ligação, CORS) — mensagem clara.
    throw new Error(
      "Não foi possível contactar o servidor. Verifique a sua ligação e tente novamente.",
    );
  }

  if (resposta.status === 204) return undefined as T;

  if (!resposta.ok) {
    let detalhe = `Erro ${resposta.status}`;
    try {
      const corpo = await resposta.json();
      detalhe = corpo.detail ?? detalhe;
    } catch {
      /* corpo não-JSON */
    }
    throw new Error(detalhe);
  }
  return (await resposta.json()) as T;
}

// ---- API pública (funções por domínio) ----
export const api = {
  // Autenticação
  registar: (dados: {
    nome: string;
    email: string;
    palavra_passe: string;
    perfil?: string;
  }) =>
    pedir<Tokens>("/auth/register", {
      method: "POST",
      body: JSON.stringify(dados),
    }),

  login: (email: string, palavra_passe: string) =>
    pedir<Tokens>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, palavra_passe }),
    }),

  eu: () => pedir<Utilizador>("/auth/me"),

  // Documentos
  listarDocumentos: (params: Record<string, string | number> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).map(([k, v]) => [k, String(v)]),
    ).toString();
    return pedir<Pagina<Documento>>(`/documents${qs ? `?${qs}` : ""}`);
  },
  // Estrutura da biblioteca: secções da CDU (+ géneros da Literatura).
  seccoesBiblioteca: () => pedir<SeccaoBiblioteca[]>("/library/sections"),
  obterDocumento: (id: number) => pedir<Documento>(`/documents/${id}`),
  // Descarrega o FICHEIRO LOCAL como Blob (envia o token; respeita o acesso).
  descarregar: async (id: number): Promise<Blob> => {
    const token = obterToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    const r = await fetch(`${BASE_URL}/documents/${id}/download`, { headers });
    if (!r.ok) {
      let detalhe = `Erro ${r.status}`;
      try {
        detalhe = (await r.json()).detail ?? detalhe;
      } catch {
        /* corpo não-JSON */
      }
      throw new Error(detalhe);
    }
    return r.blob();
  },
  publicarDocumento: (dados: Record<string, unknown>) =>
    pedir<Documento>("/documents", {
      method: "POST",
      body: JSON.stringify(dados),
    }),
  // Upload de um livro com ficheiro local (multipart). Usado no painel admin.
  carregarDocumento: async (form: FormData): Promise<Documento> => {
    const token = obterToken();
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    // NB: não definir Content-Type — o browser trata do boundary do multipart.
    const r = await fetch(`${BASE_URL}/documents/upload`, {
      method: "POST",
      body: form,
      headers,
    });
    if (!r.ok) {
      let detalhe = `Erro ${r.status}`;
      try {
        detalhe = (await r.json()).detail ?? detalhe;
      } catch {
        /* corpo não-JSON */
      }
      throw new Error(detalhe);
    }
    return r.json();
  },
  eliminarDocumento: (id: number) =>
    pedir<void>(`/documents/${id}`, { method: "DELETE" }),
  favoritos: () => pedir<Documento[]>("/favorites"),
  adicionarFavorito: (id: number) =>
    pedir<void>(`/documents/${id}/favorite`, { method: "POST" }),
  removerFavorito: (id: number) =>
    pedir<void>(`/documents/${id}/favorite`, { method: "DELETE" }),

  // Utilizadores
  listarUtilizadores: () =>
    pedir<Pagina<Utilizador>>("/users?por_pagina=100"),

  // Pesquisa
  pesquisaTextual: (q: string) =>
    pedir<ResultadoPesquisa[]>(`/search?q=${encodeURIComponent(q)}`),
  pesquisaSemantica: (q: string) =>
    pedir<RespostaSemantica>(`/semantic-search?q=${encodeURIComponent(q)}`),

  // Recomendações
  recomendacoes: () =>
    pedir<{ uri: string; titulo: string; motivo: string }[]>("/recommendations"),

  // ---- Circulação (gestão bibliotecária) ----
  // Leitor
  disponibilidade: (documentoId: number) =>
    pedir<Disponibilidade>(`/circulation/documents/${documentoId}/availability`),
  requisitar: (documentoId: number, utilizadorId?: number) =>
    pedir<Emprestimo>("/circulation/loans", {
      method: "POST",
      body: JSON.stringify({
        documento_id: documentoId,
        ...(utilizadorId ? { utilizador_id: utilizadorId } : {}),
      }),
    }),
  meusEmprestimos: () => pedir<Emprestimo[]>("/circulation/loans/me"),
  renovar: (emprestimoId: number) =>
    pedir<Emprestimo>(`/circulation/loans/${emprestimoId}/renew`, {
      method: "POST",
    }),
  reservar: (documentoId: number) =>
    pedir<Reserva>("/circulation/reservations", {
      method: "POST",
      body: JSON.stringify({ documento_id: documentoId }),
    }),
  minhasReservas: () => pedir<Reserva[]>("/circulation/reservations/me"),
  cancelarReserva: (reservaId: number) =>
    pedir<void>(`/circulation/reservations/${reservaId}`, { method: "DELETE" }),
  minhasMultas: () => pedir<Multa[]>("/circulation/fines/me"),

  // Bibliotecário (administrador)
  exemplares: (documentoId: number) =>
    pedir<Exemplar[]>(`/circulation/documents/${documentoId}/copies`),
  criarExemplares: (
    documentoId: number,
    quantidade: number,
    localizacao?: string,
  ) =>
    pedir<Exemplar[]>("/circulation/copies", {
      method: "POST",
      body: JSON.stringify({
        documento_id: documentoId,
        quantidade,
        ...(localizacao ? { localizacao } : {}),
      }),
    }),
  todosEmprestimos: (apenasActivos = false) =>
    pedir<Emprestimo[]>(
      `/circulation/loans${apenasActivos ? "?apenas_activos=true" : ""}`,
    ),
  devolver: (emprestimoId: number) =>
    pedir<Emprestimo>(`/circulation/loans/${emprestimoId}/return`, {
      method: "POST",
    }),
  todasReservas: () => pedir<Reserva[]>("/circulation/reservations"),
  todasMultas: (apenasPorPagar = false) =>
    pedir<Multa[]>(
      `/circulation/fines${apenasPorPagar ? "?apenas_por_pagar=true" : ""}`,
    ),
  pagarMulta: (multaId: number) =>
    pedir<Multa>(`/circulation/fines/${multaId}/pay`, { method: "POST" }),
  relatorioCirculacao: () =>
    pedir<RelatorioCirculacao>("/circulation/report"),

  // ---- Histórico, notificações e estatísticas ----
  historicoLeituras: () => pedir<LeituraHistorico[]>("/history/reading"),
  historicoPesquisas: () => pedir<PesquisaHistorico[]>("/history/searches"),
  limparHistorico: () => pedir<void>("/history", { method: "DELETE" }),

  notificacoes: () => pedir<Notificacoes>("/notifications"),
  marcarNotificacoesVistas: () =>
    pedir<void>("/notifications/seen", { method: "POST" }),

  estatisticas: () => pedir<Estatisticas>("/stats/overview"),
};
