// layout.tsx — Layout raiz da aplicação (envolve TODAS as páginas).
import type { Metadata } from "next";
import "./globals.css";
import { ProvedorAuth } from "@/lib/auth";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

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
          <Footer />
        </ProvedorAuth>
      </body>
    </html>
  );
}
