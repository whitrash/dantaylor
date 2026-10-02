from __future__ import annotations

import re

from ..core.modelos import Registro
from ..core.taxonomia import Taxonomia
from ..core.texto import clave_texto, primero
from .base import Dominio, lista, nullable, opciones, texto

EPOCAS = ["Antigüedad", "Edad Media", "Edad Moderna", "Siglo XIX", "Siglo XX", "Siglo XXI", "Desconocida"]
_ANIO = re.compile(r"-?\d{1,4}")

TAXONOMIA = Taxonomia(
    {
        "Arte": {
            "Pintura": ["pintura", "cuadro", "óleo", "pintor", "pintora", "mural", "fresco", "acuarela"],
            "Escultura": ["escultura", "estatua", "busto", "escultor"],
            "Arquitectura": [
                "arquitectura",
                "edificio",
                "catedral",
                "torre",
                "puente",
                "templo",
                "pirámide",
                "palacio",
                "arquitecto",
            ],
            "Música": ["música", "canción", "sinfonía", "ópera", "álbum", "disco", "tango", "compositor", "banda"],
            "Literatura": ["literatura", "libro", "novela", "poema", "cuento", "poeta", "escritor", "escritora"],
            "Cine": ["película", "film", "cine", "director", "directora"],
        },
        "Deporte": {
            "Fútbol": ["fútbol", "futbol", "mundial", "gol", "copa libertadores"],
            "Olimpismo": ["olímpico", "olímpicos", "olimpiada", "juegos olímpicos", "medalla"],
            "Tenis": ["tenis", "wimbledon", "roland garros", "raqueta"],
            "Automovilismo": ["fórmula 1", "automovilismo", "rally", "piloto"],
            "Otros deportes": ["básquet", "rugby", "boxeo", "ajedrez", "natación", "hockey"],
        },
        "Ciencia y tecnología": {
            "Inventos": ["invento", "inventor", "inventora", "patente"],
            "Espacio": ["luna", "planeta", "cohete", "astronauta", "satélite", "telescopio", "cometa"],
            "Descubrimientos": ["descubrimiento", "científico", "científica", "vacuna", "fósil"],
        },
        "Historia": {
            "Antigüedad": ["imperio romano", "egipto", "faraón", "grecia antigua"],
            "Edad Media": ["medieval", "castillo", "cruzada", "vikingo"],
            "Edad Moderna": ["renacimiento", "conquista", "virreinato"],
            "Edad Contemporánea": ["revolución", "independencia", "guerra mundial"],
            "Otras curiosidades": [],
        },
    }
)


class Curiosidades(Dominio):
    nombre = "curiosidades"
    tema = "cultura general: arte, deporte, ciencia e historia"
    version_prompt = "1"
    ttl_dias = None
    taxonomia = TAXONOMIA
    facetas = ("epoca", "pais")
    prioridad_fuentes = {"wikidata": 3, "wikipedia": 2}
    campos_busqueda = ("categoria", "titulo", "descripcion")
    reglas = """
- "titulo": nombre corto y reconocible de la obra, hecho o récord.
- "resumen": 2 o 3 oraciones; "dato_curioso": un único dato sorprendente y verificable.
- "anio": año de la obra o del hecho (negativo para a. C.); null si no aplica o no lo sabes.
- "pais": país actual donde ocurrió o se encuentra; cadena vacía si no aplica.
- "personas": personas clave involucradas (autores, deportistas, inventores).
"""

    def normalizar(self, fila: dict) -> dict:
        titulo = primero(fila, "titulo", "título", "nombre", "tema", "title")
        if not titulo:
            return {}
        datos: dict = {"titulo": titulo}
        categoria = primero(fila, "categoria", "categoría", "tipo", "area")
        if categoria:
            datos["categoria"] = categoria
        descripcion = primero(fila, "descripcion", "descripción", "texto", "notas")
        if descripcion:
            datos["descripcion"] = descripcion
        anio = primero(fila, "anio", "año", "fecha", "year")
        if anio and (coincidencia := _ANIO.search(anio)):
            datos["anio"] = int(coincidencia.group())
        pais = primero(fila, "pais", "país", "lugar")
        if pais:
            datos["pais"] = pais
        imagen = primero(fila, "imagen_url", "imagen", "foto", "image_url")
        if imagen:
            datos["imagen_url" if imagen.startswith(("http://", "https://")) else "imagen_archivo"] = imagen
        return datos

    def clave(self, datos: dict) -> str:
        return clave_texto(datos["titulo"])

    def propiedades(self) -> dict[str, dict]:
        return {
            "titulo": texto("Nombre corto y reconocible."),
            "resumen": texto("2 o 3 oraciones."),
            "dato_curioso": texto("Un dato sorprendente y verificable."),
            "anio": nullable({"type": "integer"}),
            "epoca": opciones(EPOCAS),
            "pais": texto("País actual; vacío si no aplica."),
            "personas": lista(),
        }

    def titulo(self, registro: Registro) -> str:
        return str(registro.analisis.get("titulo") or registro.item.datos.get("titulo"))

    def clave_orden(self, registro: Registro) -> tuple:
        # Dentro de cada categoría, orden cronológico (lo que no tiene año, al final).
        anio = registro.analisis.get("anio")
        return (anio if isinstance(anio, int) else 10**6, clave_texto(self.titulo(registro)))
