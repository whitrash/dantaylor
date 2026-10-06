from __future__ import annotations

import re

from ..core.modelos import Registro
from ..core.taxonomia import Taxonomia
from ..core.texto import clave_texto, primero
from .base import Dominio, lista, opciones, texto

RANGOS = ["$", "$$", "$$$", "desconocido"]
FORMATOS = ["cadena", "franquicia", "independiente", "desconocido"]
SERVICIOS = [
    "envío a domicilio",
    "retiro en local",
    "venta online",
    "pago con tarjeta",
    "pago con QR",
    "estacionamiento",
    "abierto 24 h",
]
_NO_DIGITOS = re.compile(r"\D+")
# "Avenida Corrientes 1234" y "Av. Corrientes 1234" son el mismo local.
_ABREVIATURAS = {"avenida": "av", "avda": "av", "pasaje": "pje", "calle": "", "boulevard": "bv", "bulevar": "bv"}


def _direccion_canonica(direccion: str | None) -> str:
    partes = [_ABREVIATURAS.get(p, p) for p in clave_texto(direccion).split("-")]
    return "-".join(p for p in partes if p)


TAXONOMIA = Taxonomia(
    {
        "Alimentos y bebidas": {
            "Supermercados": ["supermercado", "hipermercado", "súper", "mayorista"],
            "Almacenes": ["almacén", "autoservicio", "minimercado", "despensa", "kiosco"],
            "Verdulerías": ["verdulería", "frutería"],
            "Carnicerías": ["carnicería", "pollería", "granja", "pescadería"],
            "Panaderías": ["panadería", "confitería", "pastelería"],
            "Dietéticas": ["dietética", "naturista", "herboristería"],
            "Bebidas": ["vinoteca", "bebidas", "cervecería"],
        },
        "Cultura y ocio": {
            "Librerías": ["librería", "libros", "libro"],
            "Papelerías": ["papelería", "útiles escolares", "artículos de oficina"],
            "Jugueterías": ["juguetería", "juguetes"],
        },
        "Hogar": {
            "Ferreterías": ["ferretería", "pinturería", "corralón"],
            "Bazar y regalos": ["bazar", "regalería"],
            "Muebles y colchones": ["mueblería", "colchonería"],
        },
        "Salud y cuidado personal": {
            "Farmacias": ["farmacia"],
            "Perfumerías": ["perfumería"],
            "Ópticas": ["óptica"],
        },
        "Moda": {
            "Indumentaria": ["indumentaria", "ropa", "boutique"],
            "Calzado": ["zapatería", "calzado"],
        },
        "Mascotas": {
            "Veterinarias y pet shops": ["veterinaria", "pet shop", "forrajería"],
        },
        "Otros": {
            "Otros comercios": [],
        },
    }
)


class Comercios(Dominio):
    nombre = "comercios"
    tema = "comercio minorista (supermercados, librerías y locales de barrio)"
    version_prompt = "1"
    ttl_dias = 30  # horarios, servicios y precios cambian: se reanaliza cada mes
    taxonomia = TAXONOMIA
    facetas = ("ciudad", "barrio", "rango_precios", "servicios", "formato")
    # Un relevamiento propio en el local pesa más que un dato scrapeado de la web.
    prioridad_fuentes = {"relevamiento": 3, "web": 1}
    campos_busqueda = ("rubro", "nombre", "descripcion")
    # Datos locales y cambiantes: el modelo no los sabe; siempre con web, acotada.
    politica_web = "siempre"
    max_busquedas = 3
    campos_volatiles = ("servicios", "rango_precios")
    reglas_web = """
- Incluye la ciudad y el barrio del registro en cada búsqueda ("Librería Páginas Recoleta Buenos Aires").
- Primero confirma que el comercio existe y sigue abierto en esa dirección. Si no hay rastro, deja la ficha mínima con confianza "baja".
- Si el registro trae "sitio_web", lee esa página con la herramienta de lectura web antes de buscar: es la fuente más confiable para horario y servicios."""
    reglas = """
- "nombre": nombre comercial tal como lo conoce la gente (sin "S.A.", "S.R.L.").
- "rubros": rubros concretos que vende ("lácteos", "útiles escolares"...).
- "productos_destacados": hasta 5 productos o líneas por los que se lo conoce.
- "servicios": solo los que figuran en el registro o son evidentes por el formato (p. ej., una cadena grande acepta tarjeta).
- "rango_precios": relativo a otros comercios del mismo rubro.
- "formato": "cadena" o "franquicia" solo si reconoces la marca; si no, "independiente" o "desconocido".
"""

    def normalizar(self, fila: dict) -> dict:
        nombre = primero(fila, "nombre", "razon_social", "comercio", "local", "name")
        if not nombre:
            return {}
        datos: dict = {"nombre": nombre}
        for campo, alias in {
            "direccion": ("direccion", "dirección", "domicilio", "address"),
            "barrio": ("barrio",),
            "ciudad": ("ciudad", "localidad", "city"),
            "rubro": ("rubro", "categoria", "categoría", "tipo"),
            "descripcion": ("descripcion", "descripción", "notas"),
            "horario": ("horario", "horarios"),
            "sitio_web": ("sitio_web", "web", "url"),
        }.items():
            valor = primero(fila, *alias)
            if valor:
                datos[campo] = valor
        telefono = primero(fila, "telefono", "teléfono", "tel")
        if telefono:
            datos["telefono"] = _NO_DIGITOS.sub("", telefono)
        imagen = primero(fila, "imagen_url", "imagen", "foto")
        if imagen:
            datos["imagen_url" if imagen.startswith(("http://", "https://")) else "imagen_archivo"] = imagen
        return datos

    def clave(self, datos: dict) -> str:
        # Un mismo nombre puede tener varias sucursales: la dirección es parte de la identidad.
        partes = [clave_texto(datos["nombre"]), _direccion_canonica(datos.get("direccion"))]
        return "--".join(p for p in partes if p)

    def propiedades(self) -> dict[str, dict]:
        return {
            "nombre": texto("Nombre comercial."),
            "descripcion": texto("1 o 2 oraciones."),
            "rubros": lista(),
            "productos_destacados": lista(),
            "rango_precios": opciones(RANGOS),
            "servicios": lista(opciones(SERVICIOS)),
            "formato": opciones(FORMATOS),
        }

    def clave_orden(self, registro: Registro) -> tuple:
        datos = registro.item.datos
        return (clave_texto(datos.get("ciudad")), clave_texto(datos.get("barrio")), clave_texto(self.titulo(registro)))
