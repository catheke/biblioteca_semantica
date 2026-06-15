// CartaoPessoa.tsx — Cartão visual de um utilizador (autor/professor).
import type { Utilizador } from "@/types";

export default function CartaoPessoa({ pessoa }: { pessoa: Utilizador }) {
  const iniciais = pessoa.nome
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("");

  return (
    <div className="cartao flex items-center gap-4">
      <div className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-primaria font-semibold text-white">
        {iniciais}
      </div>
      <div className="min-w-0">
        <h3 className="truncate font-semibold text-gray-800">{pessoa.nome}</h3>
        <p className="text-sm capitalize text-gray-500">{pessoa.perfil}</p>
        {pessoa.instituicao && (
          <p className="truncate text-xs text-gray-400">{pessoa.instituicao}</p>
        )}
      </div>
    </div>
  );
}
