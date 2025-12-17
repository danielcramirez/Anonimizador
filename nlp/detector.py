"""
Deteccion de PII combinando spaCy (NER) y reglas regex basicas.
Licencia spaCy: MIT (compatible).
"""

from typing import List, Dict, Pattern
import re
import spacy

# Carga del modelo español en proceso principal (evita recarga por request)
NLP = spacy.load("es_core_news_md")

# Patrones basicos; se pueden extender segun la guia del AGN.
PATRONES: Dict[str, Pattern] = {
    "EMAIL": re.compile(r"[\w\.\-]+@[\w\.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
    "TELEFONO_CO": re.compile(r"(\+57\s?)?(3\d{9}|[1-9]\d{6,9})"),
    "CEDULA": re.compile(r"\b(\d{6,10})\b"),
    "DIRECCION_CO": re.compile(
        r"(calle|carrera|cra\.?|cl\.?|avenida|av\.?|diagonal|transversal|transv\.?)"
        r"\s*\d+[a-zA-Z]?\s*(#|no\.?)?\s*\d+[\-\s]?\d*",
        re.IGNORECASE,
    ),
}


def detectar_regex(texto: str) -> List[Dict[str, str]]:
    hallazgos: List[Dict[str, str]] = []
    for label, patron in PATRONES.items():
        for match in patron.finditer(texto):
            valor = match.group(0)
            if len(valor.strip()) < 4:
                continue
            hallazgos.append({"label": label, "value": valor.strip(), "origen": "regex"})
    return hallazgos


def detectar_spacy(texto: str) -> List[Dict[str, str]]:
    doc = NLP(texto)
    return [
        {"label": ent.label_, "value": ent.text.strip(), "origen": "spacy"}
        for ent in doc.ents
        if ent.text.strip()
    ]


def detectar_pii(texto: str) -> List[Dict[str, str]]:
    """
    Fusiona hallazgos de spaCy + regex y elimina duplicados.
    """
    hallazgos = detectar_spacy(texto) + detectar_regex(texto)
    vistos = set()
    unicos: List[Dict[str, str]] = []
    for h in hallazgos:
        clave = (h["label"], h["value"])
        if clave in vistos:
            continue
        vistos.add(clave)
        unicos.append(h)
    return unicos
