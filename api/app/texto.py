"""Normalización de texto y emparejamiento aproximado de productos.

El cliente escribe "resmas de papel", "tóner", "escritorios en L" o "mouse
inalambricos"; el catálogo dice "Resma papel carta", "Tóner HP 85A",
"Escritorio en L" y "Mouse inalámbrico". Una búsqueda LIKE no basta, así que
se compara por palabras: se quitan tildes, mayúsculas, plurales y palabras
vacías, y se mide cuántas palabras del texto aparecen en cada producto
(tolerando errores de tipeo con difflib).
"""

import re
import unicodedata
from difflib import SequenceMatcher

PALABRAS_VACIAS = {
    "de", "del", "la", "las", "el", "los", "un", "una", "unos", "unas", "en", "con",
    "para", "por", "y", "o", "a", "al", "x", "unidad", "unidades", "und", "uds",
}

UMBRAL_COINCIDENCIA = 0.5   # por debajo de esto se considera que no hay producto
SIMILITUD_PALABRA = 0.8     # "escritrio" ~ "escritorio"


def normalizar(texto: str | None) -> str:
    """Minúsculas, sin tildes y sin espacios repetidos."""
    if texto is None:
        return ""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.lower().split())


def _singular(palabra: str) -> str:
    if len(palabra) > 4 and palabra.endswith("es") and palabra[-3] not in "aeiou":
        return palabra[:-2]          # "monitores" -> "monitor"
    if len(palabra) > 3 and palabra.endswith("s"):
        return palabra[:-1]          # "resmas" -> "resma"
    return palabra


def tokens(texto: str) -> list[str]:
    palabras = re.findall(r"[a-z0-9]+", normalizar(texto))
    return [_singular(p) for p in palabras if p not in PALABRAS_VACIAS]


def _coincide(a: str, b: str) -> bool:
    return a == b or SequenceMatcher(None, a, b).ratio() >= SIMILITUD_PALABRA


def puntaje(texto: str, nombre_producto: str) -> float:
    """0 a 1. Pesa más que las palabras del cliente estén en el producto
    (cobertura del texto) que el producto esté descrito completo."""
    t_texto, t_prod = tokens(texto), tokens(nombre_producto)
    if not t_texto or not t_prod:
        return 0.0
    cubre_texto = sum(any(_coincide(t, p) for p in t_prod) for t in t_texto) / len(t_texto)
    cubre_prod = sum(any(_coincide(p, t) for t in t_texto) for p in t_prod) / len(t_prod)
    return round(0.7 * cubre_texto + 0.3 * cubre_prod, 3)
