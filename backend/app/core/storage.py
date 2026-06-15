"""
storage.py — Armazenamento LOCAL de ficheiros (livros e capas).

Em vez de apontar para sites externos, os ficheiros dos documentos ficam
guardados dentro do próprio projecto, na pasta `backend/storage/`:

    backend/storage/livros/   -> ficheiros das obras (.txt, .pdf, .epub, ...)
    backend/storage/capas/    -> imagens de capa (.jpg, .png, ...)

As capas são servidas como ficheiros estáticos públicos (montagem /static/capas)
porque não têm restrição. Já os ficheiros das obras são servidos SEMPRE através
do endpoint de download, para que o NÍVEL DE ACESSO seja respeitado.
"""
from __future__ import annotations

from pathlib import Path

# backend/  (sobe de app/core/storage.py: core -> app -> backend)
_RAIZ = Path(__file__).resolve().parents[2]

STORAGE_DIR = _RAIZ / "storage"
LIVROS_DIR = STORAGE_DIR / "livros"
CAPAS_DIR = STORAGE_DIR / "capas"

# Garante que as pastas existem (criadas uma vez, ao importar o módulo).
for _d in (LIVROS_DIR, CAPAS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Extensões aceites no upload de obras.
EXTENSOES_PERMITIDAS = {".pdf", ".epub", ".txt", ".doc", ".docx", ".rtf"}


def caminho_livro(nome: str) -> Path:
    """Caminho absoluto de um ficheiro de obra (apenas pelo nome, sem subpastas)."""
    return LIVROS_DIR / Path(nome).name


def caminho_capa(nome: str) -> Path:
    """Caminho absoluto de uma imagem de capa."""
    return CAPAS_DIR / Path(nome).name


def url_capa(nome: str) -> str:
    """URL relativo público da capa (servido pela montagem /static/capas)."""
    return f"/static/capas/{Path(nome).name}"
