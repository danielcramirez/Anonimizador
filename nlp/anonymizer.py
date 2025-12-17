"""
Anonimizado simple por reemplazo literal.
"""

from typing import List, Dict
import re


def anonimizar_texto(texto: str, hallazgos: List[Dict[str, str]], token: str) -> str:
    """
    Reemplaza cada valor encontrado por el token.
    Se ordena por longitud para evitar solapes.
    """
    anonimizado = texto
    for valor in sorted({h["value"] for h in hallazgos}, key=len, reverse=True):
        anonimizado = re.sub(re.escape(valor), token, anonimizado)
    return anonimizado
