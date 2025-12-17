"""
Pipeline de deteccion + anonimizado.
"""

from typing import List, Dict

from nlp.detector import detectar_pii
from nlp.anonymizer import anonimizar_texto
from config import MASK_TOKEN


def analizar_texto(texto: str) -> List[Dict[str, str]]:
    return detectar_pii(texto)


def anonimizar(texto: str, token: str = MASK_TOKEN) -> str:
    hallazgos = detectar_pii(texto)
    return anonimizar_texto(texto, hallazgos, token)
