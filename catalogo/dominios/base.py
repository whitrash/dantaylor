"""Contrato de un dominio de catálogo.

El motor (core/) no sabe nada de animales ni de comercios: todo lo específico
vive en una subclase de `Dominio`. Para sumar un catálogo nuevo (p. ej.
"plantas" o "farmacias") alcanza con escribir otra subclase; la logística
(paralelismo, lotes, reintentos, caché, orden, exportación) se reutiliza tal cual.

Convención para los `enum` del esquema: la opción "no se sabe" va siempre
última (NE, otro, desconocido...). El simulador la usa como valor por defecto.

Política web (`politica_web`): cuándo el modelo puede buscar en internet.
  * "nunca": solo con lo que sabe y los datos del registro.
  * "si_dudoso": primera pasada sin web (barata, en lote); segunda pasada con
    web solo para lo que quedó con confianza media/baja o con campos volátiles
    sin dato. Enciclopedias.
  * "siempre": una sola pasada con web, acotada a `max_busquedas`. Comercios.
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
POLITICAS_WEB = ("nunca", "si_dudoso", "siempre")
_CAMPOS_IMAGEN = ("imagen_url", "imagen_archivo")
_VACIOS = (None, "", [], "NE", "desconocido", "Desconocida", "desconocida")


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
    politica_web: str = "nunca"
    max_busquedas: int = 3
    # Campos de la ficha que cambian con el tiempo: si quedan vacíos en la
    # primera pasada, el item va a la segunda (con web). Se nombran en el prompt.
    campos_volatiles: tuple[str, ...] = ()
    reglas_web: str = ""

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
            "fuentes_web": lista(),
        }
        return {
            "type": "object",
            "properties": propiedades,
            "required": list(propiedades),
            "additionalProperties": False,
        }

    def herramienta_ficha(self) -> dict:
        """Herramienta estricta por la que el modelo entrega la ficha cuando
        también tiene herramientas de búsqueda."""
        from ..core.analizador import HERRAMIENTA_FICHA  # evita import circular

        return {
            "name": HERRAMIENTA_FICHA,
            "description": "Entrega la ficha final del registro. Llamar exactamente una vez, al terminar.",
            "strict": True,
            "input_schema": self.esquema(),
        }

    def instrucciones(self, con_web: bool = False) -> str:
        """Prompt de sistema. Tiene que ser idéntico para todos los items del
        dominio (nada de fechas ni ids) para que la caché de prompts funcione."""
        base = f"""Eres un catalogador experto en {self.tema}. Recibes un registro (y a veces una imagen) y devuelves su ficha para un catálogo, en español.

Reglas generales:
1. "ruta": elige exactamente una categoría hoja de la taxonomía de abajo. Si ninguna encaja, usa la categoría "Otros..." que corresponda.
2. No inventes datos. Si algo no se puede determinar con razonable certeza, usa null, la opción "desconocido"/"no evaluado" del campo o una lista vacía.
3. Si hay imagen, úsala para confirmar o corregir el texto. Si texto e imagen se contradicen, quédate con lo inequívoco y baja la confianza.
4. "confianza": "alta" si la identificación es inequívoca, "media" si hay una duda razonable, "baja" si el registro es ambiguo o insuficiente. Los items con confianza baja pasan a revisión humana.
5. "etiquetas": de 3 a 8 palabras clave en minúscula, útiles para buscar y filtrar.
6. "fuentes_web": URLs de las fuentes que consultaste; lista vacía si no consultaste ninguna.

Reglas de este catálogo:
{self.reglas.strip()}
"""
        if con_web:
            volatiles = ", ".join(f'"{c}"' for c in self.campos_volatiles) or "los que el registro deje en duda"
            base += f"""
Búsqueda web:
- Tienes búsqueda web. Haz al menos una búsqueda y como máximo {self.max_busquedas}: úsalas para confirmar y completar los campos en duda, no para explorar.
- Prioriza fuentes oficiales o de referencia (sitio propio, Wikipedia/Wikidata, organismos). Desconfía de agregadores.
- Verifica sobre todo: {volatiles}.
- Si no encuentras nada confiable, deja el campo vacío y baja la confianza; no completes por inferencia.
- Anota en "fuentes_web" las URLs que consultaste.
- Al terminar, entrega la ficha llamando a la herramienta `entregar_ficha` exactamente una vez (si la tienes); si no, responde solo con el JSON de la ficha.
{self.reglas_web.strip()}
"""
        else:
            base += "\nNo tienes acceso a internet: trabaja con tu conocimiento y con los datos del registro.\n"
        return (
            base
            + f'\nTaxonomía (las hojas son las únicas categorías válidas para "ruta"):\n{self.taxonomia.describir()}'
        )

    def contenido_texto(self, item: Item) -> str:
        visibles = {k: v for k, v in item.datos.items() if k not in _CAMPOS_IMAGEN}
        return "Registro a catalogar:\n" + json.dumps(visibles, ensure_ascii=False, sort_keys=True, indent=2)

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
        bloques.append({"type": "text", "text": self.contenido_texto(item)})
        return bloques

    def validar(self, analisis: dict) -> dict:
        analisis.setdefault("fuentes_web", [])
        faltan = [c for c in self.esquema()["required"] if c not in analisis]
        if faltan:
            raise ValueError(f"faltan campos: {', '.join(faltan)}")
        if not self.taxonomia.es_valida(analisis["ruta"]):
            raise ValueError(f"ruta fuera de la taxonomía: {analisis['ruta']!r}")
        return analisis

    def necesita_web(self, con_web_disponible: bool = True) -> bool:
        """Si la primera (o única) pasada de este dominio va con web."""
        return con_web_disponible and self.politica_web == "siempre"

    def estado_tras_analisis(self, ficha: dict, con_web: bool) -> str:
        """`listo`, o `verificar` si corresponde una segunda pasada con web."""
        if con_web or self.politica_web != "si_dudoso":
            return "listo"
        if ficha.get("confianza") != "alta":
            return "verificar"
        if any(ficha.get(c) in _VACIOS for c in self.campos_volatiles):
            return "verificar"
        return "listo"

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

    def completar(self, ficha: dict, item: Item) -> dict:
        """Rellena lo que falte de una ficha importada con valores neutros válidos."""
        base = self.simular(item)
        for campo, valor in base.items():
            if campo not in ficha:
                ficha[campo] = valor
        if not self.taxonomia.es_valida(ficha.get("ruta", "")):
            pista = " ".join(str(ficha.get(c) or "") for c in ("ruta", "categoria", "categoría", "rubro"))
            ficha["ruta"] = self.taxonomia.sugerir(pista + " " + self.titulo_item(item)) or base["ruta"]
        if ficha.get("confianza") not in CONFIANZA:
            ficha["confianza"] = "media"
        return {k: ficha[k] for k in self.esquema()["properties"]}

    # --- 3. catálogo -----------------------------------------------------

    def titulo(self, registro: Registro) -> str:
        return str(registro.analisis.get("nombre") or registro.item.datos.get("nombre") or registro.item.clave)

    def titulo_item(self, item: Item) -> str:
        """Nombre legible antes de tener ficha (para el panel)."""
        return str(item.datos.get("nombre") or item.datos.get("titulo") or item.clave)

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
