"use client";
// auth.tsx — Contexto de autenticação.
// Disponibiliza o utilizador autenticado e as acções de login/registo/logout a
// toda a aplicação.

import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { api, guardarToken, obterToken, removerToken } from "@/lib/api";
import type { Utilizador } from "@/types";

interface ContextoAuth {
  utilizador: Utilizador | null;
  carregando: boolean;
  login: (email: string, palavra_passe: string) => Promise<void>;
  registar: (dados: {
    nome: string;
    email: string;
    palavra_passe: string;
    perfil?: string;
  }) => Promise<void>;
  logout: () => void;
}

const Contexto = createContext<ContextoAuth | undefined>(undefined);

export function ProvedorAuth({ children }: { children: ReactNode }) {
  const [utilizador, setUtilizador] = useState<Utilizador | null>(null);
  const [carregando, setCarregando] = useState(true);

  // Ao montar, se houver token guardado, recupera o utilizador.
  useEffect(() => {
    async function iniciar() {
      if (obterToken()) {
        try {
          setUtilizador(await api.eu());
        } catch {
          removerToken();
        }
      }
      setCarregando(false);
    }
    iniciar();
  }, []);

  async function login(email: string, palavra_passe: string) {
    const tokens = await api.login(email, palavra_passe);
    guardarToken(tokens.access_token);
    setUtilizador(await api.eu());
  }

  async function registar(dados: {
    nome: string;
    email: string;
    palavra_passe: string;
    perfil?: string;
  }) {
    const tokens = await api.registar(dados);
    guardarToken(tokens.access_token);
    setUtilizador(await api.eu());
  }

  function logout() {
    removerToken();
    setUtilizador(null);
  }

  return (
    <Contexto.Provider
      value={{ utilizador, carregando, login, registar, logout }}
    >
      {children}
    </Contexto.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(Contexto);
  if (!ctx) throw new Error("useAuth deve ser usado dentro de <ProvedorAuth>.");
  return ctx;
}
