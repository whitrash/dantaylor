"""Registro de dominios. Para sumar un catálogo: escribir la subclase y agregarla acá."""

from .animales import Animales
from .base import Dominio
from .comercios import Comercios
from .curiosidades import Curiosidades

DOMINIOS: dict[str, Dominio] = {d.nombre: d for d in (Animales(), Curiosidades(), Comercios())}


def obtener(nombre: str) -> Dominio:
    try:
        return DOMINIOS[nombre]
    except KeyError:
        raise SystemExit(f"Dominio desconocido: {nombre!r}. Disponibles: {', '.join(DOMINIOS)}") from None
