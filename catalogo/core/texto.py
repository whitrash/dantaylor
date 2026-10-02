"""Normalización de texto y medidas.

Esto viene del mundo de los comercios: "Leche 1L" y "leche 1000 ml" tienen que
terminar siendo lo mismo. Sirve igual para "León" / "leon" o "190 kg" / "190000 g".
"""

from __future__ import annotations

import re
import unicodedata

_NO_ALFANUM = re.compile(r"[^a-z0-9]+")

# unidad -> (magnitud, factor a la unidad base). Bases: cm, g, ml.
_UNIDADES = {
    "mm": ("longitud", 0.1),
    "cm": ("longitud", 1.0),
    "m": ("longitud", 100.0),
    "km": ("longitud", 100_000.0),
    "mg": ("masa", 0.001),
    "g": ("masa", 1.0),
    "gr": ("masa", 1.0),
    "kg": ("masa", 1000.0),
    "t": ("masa", 1_000_000.0),
    "ml": ("volumen", 1.0),
    "cc": ("volumen", 1.0),
    "l": ("volumen", 1000.0),
    "lt": ("volumen", 1000.0),
}
_BASE = {"longitud": "cm", "masa": "g", "volumen": "ml"}
_MEDIDA = re.compile(r"^\s*(\d+(?:[.,]\d+)?)\s*([a-zA-Z]+)\s*$")


def sin_acentos(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def clave_texto(texto: object) -> str:
    """'  León Africano ' -> 'leon-africano'. Estable para usar como identidad."""
    if texto is None:
        return ""
    plano = sin_acentos(str(texto)).lower()
    return _NO_ALFANUM.sub("-", plano).strip("-")


def palabras(texto: object) -> str:
    """Texto normalizado con espacios en los bordes, para buscar palabras enteras."""
    return " " + clave_texto(texto).replace("-", " ") + " "


def normalizar_medida(valor: object) -> tuple[float, str] | None:
    """'1,5 kg' -> (1500.0, 'g'); '3 m' -> (300.0, 'cm'). None si no se entiende."""
    if valor is None:
        return None
    coincidencia = _MEDIDA.match(str(valor))
    if not coincidencia:
        return None
    numero, unidad = coincidencia.groups()
    unidad = unidad.lower()
    if unidad not in _UNIDADES:
        return None
    magnitud, factor = _UNIDADES[unidad]
    return round(float(numero.replace(",", ".")) * factor, 6), _BASE[magnitud]


def primero(fila: dict, *nombres: str) -> str | None:
    """Primer valor no vacío entre varios nombres de columna posibles (alias de fuentes)."""
    for nombre in nombres:
        valor = fila.get(nombre)
        if valor is not None and str(valor).strip():
            return str(valor).strip()
    return None
