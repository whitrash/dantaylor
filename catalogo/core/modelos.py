from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Item:
    """Un registro de cualquier catálogo, ya normalizado.

    `clave` es la identidad canónica del registro dentro de su dominio, el
    equivalente al código de barras (EAN) de un supermercado: dos filas con la
    misma clave son la misma cosa y se analizan una sola vez.
    """

    dominio: str
    clave: str
    datos: dict
    fuentes: list[str] = field(default_factory=list)


@dataclass
class Registro:
    """Un item ya analizado, tal como sale del almacén para armar el catálogo."""

    item: Item
    analisis: dict
    modelo: str
    vigente: bool  # False si el análisis venció (TTL) o los datos cambiaron y falta reanalizar
