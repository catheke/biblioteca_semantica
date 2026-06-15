"""
pdf_livro.py — Converte o texto integral de um livro (.txt) num PDF legível.

Os livros de domínio público chegam como texto simples do Project Gutenberg.
Para que a experiência de leitura seja a de um livro de verdade (e não um bloco
de texto cru do browser), geramos um PDF com:

  * uma página de rosto (título + autor);
  * o corpo do livro paginado, com margens e tipografia de leitura.

A geração é feita "em streaming" com o canvas do reportlab (escreve linha a
linha), por isso lida bem mesmo com obras grandes sem consumir muita memória.
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


def _limpar_gutenberg(texto: str) -> str:
    """Remove o cabeçalho/rodapé de licença do Project Gutenberg, deixando só a obra."""
    inicio = texto.find("*** START OF")
    if inicio != -1:
        quebra = texto.find("\n", inicio)
        if quebra != -1:
            texto = texto[quebra + 1 :]
    fim = texto.find("*** END OF")
    if fim != -1:
        texto = texto[:fim]
    return texto.strip()


def txt_para_pdf(caminho_txt: Path, destino_pdf: Path, titulo: str, autor: str) -> bool:
    """
    Lê o `.txt` em `caminho_txt` e escreve um PDF de leitura em `destino_pdf`.
    Devolve True em caso de sucesso. Idempotente: salta se o PDF já existir.
    """
    if destino_pdf.exists() and destino_pdf.stat().st_size > 0:
        return True
    try:
        texto = Path(caminho_txt).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False

    texto = _limpar_gutenberg(texto)
    if not texto:
        return False

    largura, altura = A4
    margem = 2.2 * cm
    largura_util = largura - 2 * margem
    fonte, tam, entrelinha = "Times-Roman", 11.5, 16

    c = canvas.Canvas(str(destino_pdf), pagesize=A4)
    c.setTitle(titulo)
    c.setAuthor(autor)

    # ---- Página de rosto ----
    c.setFont("Times-Bold", 24)
    for i, linha in enumerate(simpleSplit(titulo, "Times-Bold", 24, largura_util)):
        c.drawCentredString(largura / 2, altura / 2 + 40 - i * 30, linha)
    c.setFont("Times-Roman", 15)
    c.drawCentredString(largura / 2, altura / 2 - 20, autor)
    c.setFont("Times-Italic", 9.5)
    c.drawCentredString(
        largura / 2, margem,
        "Texto integral de domínio público · Project Gutenberg",
    )
    c.showPage()

    # ---- Corpo ----
    y = altura - margem
    c.setFont(fonte, tam)
    for paragrafo in texto.split("\n\n"):
        paragrafo = " ".join(paragrafo.split())  # junta quebras soltas num parágrafo
        if not paragrafo:
            y -= entrelinha
            continue
        for linha in simpleSplit(paragrafo, fonte, tam, largura_util):
            if y < margem:
                c.showPage()
                c.setFont(fonte, tam)
                y = altura - margem
            c.drawString(margem, y, linha)
            y -= entrelinha
        y -= entrelinha * 0.5  # respiro entre parágrafos

    c.save()
    return destino_pdf.exists() and destino_pdf.stat().st_size > 0
