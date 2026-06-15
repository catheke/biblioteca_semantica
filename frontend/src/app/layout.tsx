// layout.tsx — Layout raiz da aplicação (envolve TODAS as páginas).
import type { Metadata } from "next";
import "./globals.css";
import { ProvedorAuth } from "@/lib/auth";
import Navbar from "@/components/Navbar";

export const metadata: Metadata = {
  title: "Semantic Academic Hub (BASI)",
  description:
    "Rede académica baseada em Web Semântica: publique e descubra conhecimento com pesquisa inteligente.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt">
      <body className="min-h-screen font-sans">
        {/* O ProvedorAuth disponibiliza o utilizador autenticado a toda a app. */}
        <ProvedorAuth>
          <Navbar />
          <main>{children}</main>
          <footer className="mt-16 border-t border-gray-200 bg-white py-6 text-center text-sm text-gray-400">
            Semantic Academic Hub (BASI) — Projecto académico de Web Semântica.
          </footer>
        </ProvedorAuth>
      </body>
    </html>
  );
}
