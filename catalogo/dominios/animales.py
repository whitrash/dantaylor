from __future__ import annotations

from ..core.modelos import Registro
from ..core.taxonomia import Taxonomia
from ..core.texto import clave_texto, normalizar_medida, primero
from .base import Dominio, lista, nullable, opciones, texto

CONTINENTES = ["África", "América del Norte", "América del Sur", "Asia", "Europa", "Oceanía", "Antártida", "Océanos"]
DIETAS = ["carnívoro", "herbívoro", "omnívoro", "insectívoro", "piscívoro", "filtrador", "otro"]
# Lista Roja UICN; NE (no evaluado) va última a propósito (ver convención en base.py).
UICN = ["LC", "NT", "VU", "EN", "CR", "EW", "EX", "DD", "NE"]

TAXONOMIA = Taxonomia(
    {
        "Mamíferos": {
            "Felinos": ["león", "tigre", "jaguar", "puma", "leopardo", "guepardo", "gato", "ocelote", "lince"],
            "Cánidos": ["lobo", "aguará", "zorro", "perro", "chacal", "coyote", "dingo"],
            "Osos": ["oso", "panda"],
            "Primates": ["gorila", "chimpancé", "orangután", "mono", "lémur", "tití", "bonobo"],
            "Cetáceos": ["ballena", "delfín", "orca", "cachalote", "marsopa", "beluga"],
            "Roedores": ["ratón", "rata", "ardilla", "castor", "carpincho", "capibara", "chinchilla", "hámster"],
            "Marsupiales": ["canguro", "koala", "zarigüeya", "wombat", "demonio de tasmania"],
            "Ungulados": [
                "caballo",
                "cebra",
                "jirafa",
                "ciervo",
                "rinoceronte",
                "hipopótamo",
                "guanaco",
                "llama",
                "vicuña",
                "elefante",
            ],
            "Otros mamíferos": ["murciélago", "armadillo", "ornitorrinco", "perezoso", "foca", "morsa"],
        },
        "Aves": {
            "Rapaces": ["águila", "halcón", "cóndor", "búho", "lechuza", "gavilán", "carancho"],
            "Aves marinas": ["pingüino", "albatros", "gaviota", "pelícano", "petrel", "frailecillo"],
            "Aves corredoras": ["ñandú", "avestruz", "emú", "kiwi", "casuario"],
            "Loros y afines": ["loro", "guacamayo", "cotorra", "cacatúa", "periquito"],
            "Paseriformes": ["hornero", "gorrión", "zorzal", "cardenal", "calandria", "benteveo"],
            "Otras aves": ["colibrí", "flamenco", "tucán", "pavo real", "cisne", "pato"],
        },
        "Reptiles": {
            "Serpientes": ["serpiente", "víbora", "boa", "pitón", "cobra", "yarará", "anaconda"],
            "Lagartos": ["lagarto", "iguana", "camaleón", "gecko", "varano", "dragón de komodo"],
            "Tortugas": ["tortuga"],
            "Cocodrilos": ["cocodrilo", "caimán", "yacaré", "aligátor"],
        },
        "Anfibios": {
            "Ranas y sapos": ["rana", "sapo"],
            "Salamandras": ["salamandra", "ajolote", "tritón"],
        },
        "Peces": {
            "Tiburones y rayas": ["tiburón", "raya", "manta"],
            "Peces óseos": ["pez", "salmón", "trucha", "atún", "dorado", "caballito de mar", "piraña"],
        },
        "Invertebrados": {
            "Insectos": ["mariposa", "abeja", "hormiga", "escarabajo", "libélula", "mantis", "luciérnaga"],
            "Arácnidos": ["araña", "escorpión", "tarántula", "alacrán"],
            "Moluscos": ["pulpo", "calamar", "caracol", "almeja", "sepia", "nautilo"],
            "Crustáceos": ["cangrejo", "langosta", "camarón", "krill"],
            "Otros invertebrados": ["medusa", "estrella de mar", "coral", "lombriz", "erizo de mar"],
        },
    }
)


class Animales(Dominio):
    nombre = "animales"
    tema = "zoología y divulgación sobre fauna"
    version_prompt = "1"
    ttl_dias = None  # una especie no cambia: se analiza una vez
    taxonomia = TAXONOMIA
    facetas = ("continentes", "dieta", "estado_conservacion")
    prioridad_fuentes = {"gbif": 3, "uicn": 3, "wikipedia": 2}
    campos_busqueda = ("nombre", "notas")
    reglas = """
- "nombre_cientifico": nomenclatura binomial (Género especie). Si el registro es un grupo ("pingüino"), elige la especie más representativa y usa confianza "media".
- "descripcion": 2 o 3 oraciones para público general.
- "estado_conservacion": categoría de la Lista Roja de la UICN; "NE" si no está evaluada o no lo sabes.
- "tamano_cm" y "peso_kg": valores típicos de un adulto (en aves, longitud del cuerpo); null si no lo sabes.
- "curiosidades": de 2 a 4 datos sorprendentes y verificables, una oración cada uno.
"""

    def normalizar(self, fila: dict) -> dict:
        nombre = primero(fila, "nombre", "nombre_comun", "animal", "especie", "name")
        cientifico = primero(fila, "nombre_cientifico", "cientifico", "scientific_name")
        if not (nombre or cientifico):
            return {}
        datos: dict = {"nombre": nombre or cientifico}
        if cientifico:
            datos["nombre_cientifico"] = cientifico
        imagen = primero(fila, "imagen_url", "imagen", "foto", "image_url")
        if imagen:
            datos["imagen_url" if imagen.startswith(("http://", "https://")) else "imagen_archivo"] = imagen
        peso = normalizar_medida(primero(fila, "peso"))
        if peso and peso[1] == "g":
            datos["peso_kg"] = round(peso[0] / 1000, 3)
        largo = normalizar_medida(primero(fila, "largo", "tamano", "tamaño", "longitud"))
        if largo and largo[1] == "cm":
            datos["tamano_cm"] = largo[0]
        notas = primero(fila, "notas", "descripcion", "descripción")
        if notas:
            datos["notas"] = notas
        return datos

    def clave(self, datos: dict) -> str:
        return clave_texto(datos.get("nombre_cientifico") or datos["nombre"])

    def propiedades(self) -> dict[str, dict]:
        return {
            "nombre_comun": texto("Nombre común más usado en español."),
            "nombre_cientifico": texto("Nombre científico binomial."),
            "descripcion": texto("2 o 3 oraciones."),
            "habitat": lista(),
            "continentes": lista(opciones(CONTINENTES)),
            "dieta": opciones(DIETAS),
            "estado_conservacion": opciones(UICN),
            "tamano_cm": nullable({"type": "number"}),
            "peso_kg": nullable({"type": "number"}),
            "curiosidades": lista(),
        }

    def titulo(self, registro: Registro) -> str:
        comun = registro.analisis.get("nombre_comun") or registro.item.datos.get("nombre")
        cientifico = registro.analisis.get("nombre_cientifico") or registro.item.datos.get("nombre_cientifico")
        return f"{comun} ({cientifico})" if cientifico and cientifico != comun else str(comun)

    def clave_catalogo(self, registro: Registro) -> str:
        # "Puma" y "León de montaña" entran como dos filas distintas, pero el
        # análisis devuelve el mismo nombre científico: en el catálogo son uno.
        return clave_texto(registro.analisis.get("nombre_cientifico")) or registro.item.clave
