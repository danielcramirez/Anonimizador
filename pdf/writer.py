"""
Anonimizacion de PDF aplicando redactions con PyMuPDF.
"""

from typing import List, Dict
import os
import fitz  # PyMuPDF

from config import MASK_TOKEN, OUTPUTS_DIR, HIT_MAX_PER_PAGE


def _aplicar_redacciones_pagina(pagina: fitz.Page, valores: List[str], token: str) -> None:
    if not valores:
        return

    for valor in valores:
        rects = pagina.search_for(valor) or []
        if HIT_MAX_PER_PAGE and HIT_MAX_PER_PAGE > 0:
            rects = rects[:HIT_MAX_PER_PAGE]
        for rect in rects:
            pagina.add_redact_annot(rect, text=token, fill=(0, 0, 0))
    pagina.apply_redactions()


def anonimizar_pdf(ruta_entrada: str, ruta_salida: str, valores: List[str], token: str = MASK_TOKEN) -> str:
    """
    Aplica redacciones para cada valor indicado. Espera valores ya detectados.
    """
    os.makedirs(os.path.dirname(ruta_salida), exist_ok=True)

    with fitz.open(ruta_entrada) as doc:
        for pagina in doc:
            _aplicar_redacciones_pagina(pagina, valores, token)
        doc.save(ruta_salida, garbage=4, deflate=True)

    return ruta_salida
