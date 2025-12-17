"""
Extraccion de texto de PDFs con dos caminos:
- Texto embebido via pdfplumber (rapido y preciso).
- OCR opcional con Tesseract cuando no hay texto (para escaneados).
"""

from typing import Iterator, Tuple
import io
import fitz  # PyMuPDF
import pdfplumber
from PIL import Image
import pytesseract

from config import MAX_PAGES_TO_SCAN, OCR_LANGUAGE


def iterar_texto(ruta_pdf: str) -> Iterator[Tuple[int, str]]:
    """
    Devuelve texto por pagina (numero, contenido) usando PyMuPDF.
    """
    with fitz.open(ruta_pdf) as doc:
        total_paginas = len(doc)
        limite = total_paginas if MAX_PAGES_TO_SCAN is None else min(total_paginas, MAX_PAGES_TO_SCAN)

        for num in range(limite):
            pagina = doc.load_page(num)
            contenido = pagina.get_text("text") or ""
            yield num, contenido


def extraer_texto_embebido(ruta_pdf: str) -> str:
    """Extrae texto embebido con pdfplumber (evita OCR si no es necesario)."""
    texto = []
    with pdfplumber.open(ruta_pdf) as pdf:
        for pagina in pdf.pages:
            contenido = pagina.extract_text() or ""
            if contenido:
                texto.append(contenido)
    return "\n".join(texto).strip()


def extraer_texto_ocr(ruta_pdf: str) -> str:
    """Extrae texto via OCR con Tesseract (para PDFs escaneados)."""
    resultado = []
    with fitz.open(ruta_pdf) as doc:
        for pagina in doc:
            pix = pagina.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes()))
            resultado.append(pytesseract.image_to_string(img, lang=OCR_LANGUAGE))
    return "\n".join(resultado).strip()


def extraer_texto(ruta_pdf: str, usar_ocr: bool = False) -> str:
    """
    Extrae texto; si no encuentra y usar_ocr=True, intenta OCR.
    """
    texto = extraer_texto_embebido(ruta_pdf)
    if texto:
        return texto
    if usar_ocr:
        return extraer_texto_ocr(ruta_pdf)
    return ""
