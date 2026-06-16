// types/index.ts — Tipos partilhados que espelham os schemas da API (backend).

export type Perfil =
  | "administrador"
  | "professor"
  | "estudante"
  | "investigador"
  | "visitante";

export type TipoDocumento =
  | "livro"
  | "artigo"
  | "tese"
  | "monografia"
  | "manual"
  | "apresentacao"
  | "material_didactico";

export interface Utilizador {
  id: number;
  nome: string;
  email: string;
  perfil: Perfil;
  biografia?: string | null;
  instituicao?: string | null;
  avatar_url?: string | null;
}

export type NivelAcesso = "publico" | "autenticado" | "academico";

export interface Documento {
  id: number;
  titulo: string;
  resumo?: string | null;
  tipo: TipoDocumento;
  estado: string;
  ano_publicacao?: number | null;
  idioma?: string | null;
  autor_id: number;
  autor_nome?: string | null;
  area_id?: number | null;
  genero?: string | null;
  ficheiro_url?: string | null;
  ficheiro_objecto?: string | null;
  capa_url?: string | null;
  nivel_acesso?: NivelAcesso;
  uri_semantica?: string | null;
  num_downloads: number;
  num_visualizacoes: number;
}

// Repartição da Literatura por género (auxiliar de forma da CDU).
export interface GeneroSeccao {
  codigo: string; // notação CDU, ex.: "82-3"
  nome: string; // ex.: "Romance"
  total: number;
}

// Uma secção da biblioteca = uma classe da CDU (a "estante").
export interface SeccaoBiblioteca {
  area_id: number;
  codigo?: string | null; // cota CDU, ex.: "0", "82"
  nome: string;
  total: number;
  generos: GeneroSeccao[];
}

export interface Pagina<T> {
  total: number;
  pagina: number;
  por_pagina: number;
  itens: T[];
}

export interface ResultadoPesquisa {
  titulo: string;
  uri?: string | null;
  tipo?: string | null;
  motivo?: string | null;
}

export interface RespostaSemantica {
  termo: string;
  tema_encontrado: boolean;
  termos_expandidos: string[];
  resultados: ResultadoPesquisa[];
  sugestoes: string[];
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
