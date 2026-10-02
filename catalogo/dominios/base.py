"""Contrato de un dominio de catálogo.

El motor (core/) no sabe nada de animales ni de comercios: todo lo específico
vive en una subclase de `Dominio`. Para sumar un catálogo nuevo (p. ej.
"plantas" o "farmacias") alcanza con escribir otra subclase; la logística
(paralelismo, lotes, reintentos, caché, orden, exportación) se reutiliza tal cual.

Convención para los `enum` del esquema: la opción "no se sabe" va siempre
última (NE, otro, desconocido...). El simulador la usa como valor por defecto.
"""

from __future__ import annotations

import base64
import json
import mimetypes
from pathlib import Path

from ..core.modelos import Item, Registro
from ..core.taxonomia import Taxonomia
from ..core.texto import clave_texto

CONFIANZA = ["alta", "media", "baja"]
_CAMPOS_IMAGEN = ("imagen_url", "imagen_archivo")


def nullable(esquema: dict) -> dict:
    return {"anyOf": [esquema, {"type": "null"}]}


def lista(items: dict | None = None) -> dict:
    return {"type": "array", "items": items or {"type": "string"}}


def texto(descripcion: str) -> dict:
    return {"type": "string", "description": descripcion}


def opciones(valores: list[str], descripcion: str = "") -> dict:
    esquema: dict = {"type": "string", "enum": valores}
    if descripcion:
        esquema["description"] = descripcion
    return esquema


class Dominio:
    nombre: str = ""
    tema: str = ""
    # Subir la versión cuando cambian el prompt o el esquema: invalida la caché
    # y fuerza a reanalizar (sin esto, los items "listos" no se vuelven a pagar).
    version_prompt: str = "1"
    # None = el análisis no vence (fauna, arte). Un número = días hasta reanalizar.
    ttl_dias: float | None = None
    taxonomia: Taxonomia
    facetas: tuple[str, ...] = ()
    # Ante datos en conflicto entre fuentes, gana la de mayor prioridad.
    prioridad_fuentes: dict[str, int] = {}
    # Campos de `datos` que se miran para la pre-clasificación por palabras clave.
    campos_busqueda: tuple[str, ...] = ("nombre",)
    reglas: str = ""

    # --- 1. recolección y normalización ---------------------------------

    def normalizar(self, fila: dict) -> dict:
        """Fila cruda (CSV/JSON de cualquier fuente) -> registro canónico."""
        raise NotImplementedError

    def clave(self, datos: dict) -> str:
        """Identidad canónica (el "EAN" del dominio)."""
        raise NotImplementedError

    def a_item(self, fila: dict, fuente: str) -> Item | None:
        datos = self.normalizar(fila)
        if not datos:
            return None
        clave = self.clave(datos)
        if not clave:
            return None
        return Item(self.nombre, clave, datos, [fuente])

    def fusionar(self, a: Item, b: Item) -> Item:
        """Dos filas con la misma clave: se completan entre sí y, en conflicto,
        gana la fuente con más prioridad (como cuando un súper recibe la misma
        ficha del fabricante y de un distribuidor)."""
        prioridad = lambda item: max(self.prioridad_fuentes.get(f, 0) for f in item.fuentes)  # noqa: E731
        alta, baja = (a, b) if prioridad(a) >= prioridad(b) else (b, a)
        datos = dict(baja.datos)
        datos.update({k: v for k, v in alta.datos.items() if v not in (None, "", [], {})})
        fuentes = list(dict.fromkeys(a.fuentes + b.fuentes))
        return Item(self.nombre, a.clave, datos, fuentes)

    # --- 2. análisis -----------------------------------------------------

    def propiedades(self) -> dict[str, dict]:
        """Campos propios de la ficha de este dominio (JSON Schema)."""
        raise NotImplementedError

    def esquema(self) -> dict:
        propiedades = {
            "ruta": opciones(self.taxonomia.hojas(), "Categoría hoja de la taxonomía."),
            **self.propiedades(),
            "etiquetas": lista(),
            "confianza": opciones(CONFIANZA),
        }
        return {
            "type": "object",
            "properties": propiedades,
            "required": list(propiedades),
            "additionalProperties": False,
        }

    def instrucciones(self) -> str:
        """Prompt de sistema. Tiene que ser idéntico para todos los items del
        dominio (nada de fechas ni ids) para que la caché de prompts funcione."""
        return f"""Eres un catalogador experto en {self.tema}. Recibes un registro (y a veces una imagen) y devuelves su ficha para un catálogo, en español.

Reglas generales:
1. "ruta": elige exactamente una categoría hoja de la taxonomía de abajo. Si ninguna encaja, usa la categoría "Otros..." que corresponda.
2. No inventes datos. Si algo no se puede determinar con razonable certeza, usa null, la opción "desconocido"/"no evaluado" del campo o una lista vacía.
3. Si hay imagen, úsala para confirmar o corregir el texto. Si texto e imagen se contradicen, quédate con lo inequívoco y baja la confianza.
4. "confianza": "alta" si la identificación es inequívoca, "media" si hay una duda razonable, "baja" si el registro es ambiguo o insuficiente. Los items con confianza baja pasan a revisión humana.
5. "etiquetas": de 3 a 8 palabras clave en minúscula, útiles para buscar y filtrar.

Reglas de este catálogo:
{self.reglas.strip()}

Taxonomía (las hojas son las únicas categorías válidas para "ruta"):
{self.taxonomia.describir()}"""

    def contenido(self, item: Item) -> list[dict]:
        """Mensaje de usuario para un item: imagen opcional + datos en JSON."""
        bloques: list[dict] = []
        if item.datos.get("imagen_url"):
            bloques.append({"type": "image", "source": {"type": "url", "url": item.datos["imagen_url"]}})
        elif item.datos.get("imagen_archivo"):
            ruta = Path(item.datos["imagen_archivo"])
            tipo = mimetypes.guess_type(ruta.name)[0] or "image/jpeg"
            datos = base64.standard_b64encode(ruta.read_bytes()).decode()
            bloques.append({"type": "image", "source": {"type": "base64", "media_type": tipo, "data": datos}})
        visibles = {k: v for k, v in item.datos.items() if k not in _CAMPOS_IMAGEN}
        bloques.append(
            {
                "type": "text",
                "text": "Registro a catalogar:\n" + json.dumps(visibles, ensure_ascii=False, sort_keys=True, indent=2),
            }
        )
        return bloques

    def validar(self, analisis: dict) -> dict:
        faltan = [c for c in self.esquema()["required"] if c not in analisis]
        if faltan:
            raise ValueError(f"faltan campos: {', '.join(faltan)}")
        if not self.taxonomia.es_valida(analisis["ruta"]):
            raise ValueError(f"ruta fuera de la taxonomía: {analisis['ruta']!r}")
        return analisis

    def ruta_por_defecto(self) -> str:
        return self.taxonomia.hojas()[-1]

    def simular(self, item: Item) -> dict:
        """Ficha falsa pero válida, sin red. Sirve para probar la logística de
        punta a punta (y como pre-clasificador gratis por palabras clave)."""
        texto_busqueda = " ".join(str(item.datos.get(c) or "") for c in self.campos_busqueda)
        sugerida = self.taxonomia.sugerir(texto_busqueda)
        ficha = {
            nombre: _valor_simulado(prop, item.datos.get(nombre))
            for nombre, prop in self.esquema()["properties"].items()
        }
        ficha["ruta"] = sugerida or self.ruta_por_defecto()
        ficha["confianza"] = "media" if sugerida else "baja"
        return ficha

    # --- 3. catálogo -----------------------------------------------------

    def titulo(self, registro: Registro) -> str:
        return str(registro.analisis.get("nombre") or registro.item.datos.get("nombre") or registro.item.clave)

    def clave_orden(self, registro: Registro) -> tuple:
        """Orden dentro de una misma categoría hoja."""
        return (clave_texto(self.titulo(registro)),)

    def clave_catalogo(self, registro: Registro) -> str:
        """Identidad después del análisis. Por defecto la misma que al ingresar;
        animales la redefine (dos nombres comunes, una misma especie)."""
        return registro.item.clave

    def valores_faceta(self, registro: Registro, faceta: str) -> list[str]:
        valor = registro.analisis.get(faceta, registro.item.datos.get(faceta))
        if valor in (None, "", []):
            return []
        return [str(v) for v in valor] if isinstance(valor, list) else [str(valor)]


def _valor_simulado(propiedad: dict, valor: object) -> object:
    if "anyOf" in propiedad:
        base = propiedad["anyOf"][0]
        if base.get("type") in ("number", "integer"):
            return valor if isinstance(valor, (int, float)) else None
        return valor if valor not in (None, "") else None
    if "enum" in propiedad:
        return valor if valor in propiedad["enum"] else propiedad["enum"][-1]
    tipo = propiedad.get("type")
    if tipo == "array":
        permitidos = propiedad.get("items", {}).get("enum")
        if not isinstance(valor, list):
            return []
        return [v for v in valor if permitidos is None or v in permitidos]
    if tipo in ("number", "integer"):
        return valor if isinstance(valor, (int, float)) else 0
    return str(valor) if valor not in (None, "") else ""
