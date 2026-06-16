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

// ---- Circulação (gestão bibliotecária) ----
export type EstadoExemplar =
  | "disponivel"
  | "emprestado"
  | "reservado"
  | "manutencao"
  | "perdido";

export type EstadoEmprestimo = "activo" | "devolvido" | "atrasado";

export type EstadoReserva = "activa" | "atendida" | "cancelada" | "expirada";

export interface Exemplar {
  id: number;
  documento_id: number;
  numero_registo: string;
  estado: EstadoExemplar;
  localizacao?: string | null;
}

export interface Disponibilidade {
  documento_id: number;
  total_exemplares: number;
  disponiveis: number;
  reservas_em_espera: number;
  pode_requisitar: boolean;
  pode_reservar: boolean;
  ja_tem_emprestimo: boolean;
  ja_reservou: boolean;
  motivo?: string | null;
}

export interface Emprestimo {
  id: number;
  exemplar_id: number;
  utilizador_id: number;
  data_emprestimo: string;
  data_prevista_devolucao: string;
  data_devolucao?: string | null;
  estado: EstadoEmprestimo;
  renovacoes: number;
  documento_id?: number | null;
  documento_titulo?: string | null;
  numero_registo?: string | null;
  leitor_nome?: string | null;
  dias_em_atraso: number;
  multa_valor: number;
}

export interface Reserva {
  id: number;
  documento_id: number;
  utilizador_id: number;
  data_reserva: string;
  estado: EstadoReserva;
  documento_titulo?: string | null;
  leitor_nome?: string | null;
  posicao?: number | null;
}

export interface Multa {
  id: number;
  emprestimo_id: number;
  utilizador_id: number;
  dias_atraso: number;
  valor: number;
  paga: boolean;
  data_criacao: string;
  data_pagamento?: string | null;
  documento_titulo?: string | null;
  leitor_nome?: string | null;
}

export interface ObraMaisRequisitada {
  documento_id: number;
  titulo: string;
  total: number;
}

export interface RelatorioCirculacao {
  total_exemplares: number;
  exemplares_disponiveis: number;
  emprestimos_activos: number;
  emprestimos_atrasados: number;
  reservas_activas: number;
  multas_por_pagar: number;
  valor_multas_por_pagar: number;
  total_emprestimos_historico: number;
  obras_mais_requisitadas: ObraMaisRequisitada[];
}

// ---- Histórico, notificações e estatísticas ----
export interface LeituraHistorico {
  documento_id: number;
  titulo: string;
  tipo?: string | null;
  capa_url?: string | null;
  data: string;
}

export interface PesquisaHistorico {
  termo: string;
  semantica: boolean;
  data: string;
}

export interface Notificacao {
  id: number;
  mensagem: string;
  documento_id?: number | null;
  data: string;
}

export interface Notificacoes {
  nao_lidas: number;
  itens: Notificacao[];
}

export interface ItemContagem {
  documento_id: number;
  titulo: string;
  valor: number;
}

export interface CategoriaContagem {
  nome: string;
  total: number;
}

export interface TermoContagem {
  termo: string;
  total: number;
}

export interface Estatisticas {
  total_documentos: number;
  total_utilizadores: number;
  total_downloads: number;
  total_visualizacoes: number;
  mais_vistos: ItemContagem[];
  mais_descarregados: ItemContagem[];
  por_categoria: CategoriaContagem[];
  termos_mais_pesquisados: TermoContagem[];
}
