"""Árbol de categorías del catálogo.

Es el mismo concepto que el árbol de un supermercado (Almacén > Lácteos > Leches):
un vocabulario controlado. El modelo nunca inventa categorías; elige una hoja de
este árbol (el esquema de salida la fuerza con un `enum`), y el orden del catálogo
sale del orden en que se declara el árbol.
"""

from __future__ import annotations

from .texto import palabras

SEPARADOR = " > "


class Taxonomia:
    def __init__(self, arbol: dict):
        """`arbol` es un dict anidado; las hojas son listas de palabras clave.

        {"Mamíferos": {"Felinos": ["león", "tigre"], "Cánidos": ["lobo"]}}
        """
        self.arbol = arbol
        self._hojas: list[str] = []
        self._palabras: dict[str, list[str]] = {}
        self._recorrer(arbol, [])
        if not self._hojas:
            raise ValueError("La taxonomía no tiene hojas")
        self._posicion = {ruta: i for i, ruta in enumerate(self._hojas)}

    def _recorrer(self, nodo: dict, camino: list[str]) -> None:
        for nombre, hijo in nodo.items():
            ruta = camino + [nombre]
            if isinstance(hijo, dict):
                self._recorrer(hijo, ruta)
            else:
                clave = SEPARADOR.join(ruta)
                self._hojas.append(clave)
                # El nombre de la hoja también cuenta ("Cánidos" en una ficha vieja).
                self._palabras[clave] = [palabras(p) for p in hijo] + [palabras(nombre)]

    def hojas(self) -> list[str]:
        return list(self._hojas)

    def es_valida(self, ruta: str) -> bool:
        return ruta in self._posicion

    def posicion(self, ruta: str) -> int:
        """Orden de la hoja en el catálogo; las rutas desconocidas van al final."""
        return self._posicion.get(ruta, len(self._hojas))

    def sugerir(self, texto: str) -> str | None:
        """Clasificación por reglas (palabras clave), como hacen los supermercados
        antes de pagar por algo más caro. Gana la palabra que aparece primero en el
        texto; a igual posición, la más larga."""
        normalizado = palabras(texto)
        mejor: tuple[int, int, int] | None = None
        elegida = None
        for ruta, claves in self._palabras.items():
            for clave in claves:
                pos = normalizado.find(clave)
                if pos < 0:
                    continue
                candidato = (pos, -len(clave), self._posicion[ruta])
                if mejor is None or candidato < mejor:
                    mejor, elegida = candidato, ruta
        return elegida

    def describir(self) -> str:
        """Texto estable (mismo resultado siempre) para poner en el prompt."""
        lineas: list[str] = []

        def bajar(nodo: dict, nivel: int) -> None:
            for nombre, hijo in nodo.items():
                sangria = "  " * nivel
                if isinstance(hijo, dict):
                    lineas.append(f"{sangria}- {nombre}")
                    bajar(hijo, nivel + 1)
                elif hijo:
                    lineas.append(f"{sangria}- {nombre} (p. ej.: {', '.join(hijo[:6])})")
                else:
                    lineas.append(f"{sangria}- {nombre}")

        bajar(self.arbol, 0)
        return "\n".join(lineas)
