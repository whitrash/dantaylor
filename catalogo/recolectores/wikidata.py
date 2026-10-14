"""Datos estructurados de Wikidata, gratis, antes de pagar búsquedas.

Para un animal: QID, nombre científico (P225), imagen de Commons (P18), estado
UICN (P141), masa (P2067) y longitud (P2043), y el título del artículo en la
Wikipedia del idioma. Para una curiosidad: QID, año (P571) e imagen.

Dos llamadas por item: `wbsearchentities` (texto -> QID) y `wbgetentities`
(QID -> claims). Ambas aceptan una función `obtener(url) -> dict` inyectable,
así el recolector se prueba sin red.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "catalogos-motor/0.1 (https://github.com/whitrash/dantaylor)"

# Categorías de la Lista Roja de la UICN en Wikidata.
UICN = {
    "Q211005": "LC",
    "Q719675": "NT",
    "Q278113": "VU",
    "Q11394": "EN",
    "Q219127": "CR",
    "Q239509": "EW",
    "Q237350": "EX",
    "Q3245245": "DD",
    "Q3350324": "NE",
}
UNIDADES = {
    "Q11570": "kg",
    "Q41803": "g",
    "Q191118": "t",
    "Q11573": "m",
    "Q174728": "cm",
    "Q174789": "mm",
}
PROPIEDADES = {
    "nombre_cientifico": "P225",
    "imagen": "P18",
    "uicn": "P141",
    "masa": "P2067",
    "longitud": "P2043",
    "inicio": "P571",
}


def obtener_json(url: str, timeout: float = 20.0) -> dict:
    pedido = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(pedido, timeout=timeout) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def buscar(texto: str, idioma: str = "es", obtener=obtener_json) -> str | None:
    """Primer QID que coincide con el texto (en el idioma dado, con respaldo en inglés)."""
    for lengua in dict.fromkeys((idioma, "en")):
        consulta = urllib.parse.urlencode(
            {
                "action": "wbsearchentities",
                "search": texto,
                "language": lengua,
                "type": "item",
                "limit": 1,
                "format": "json",
            }
        )
        resultados = (obtener(f"{API}?{consulta}") or {}).get("search") or []
        if resultados:
            return str(resultados[0]["id"])
    return None


def entidad(qid: str, idioma: str = "es", obtener=obtener_json) -> dict | None:
    consulta = urllib.parse.urlencode(
        {
            "action": "wbgetentities",
            "ids": qid,
            "props": "claims|sitelinks|labels",
            "languages": idioma,
            "format": "json",
        }
    )
    datos = (obtener(f"{API}?{consulta}") or {}).get("entities") or {}
    ent = datos.get(qid)
    return None if not ent or "missing" in ent else ent


def _valores(ent: dict, propiedad: str) -> list:
    salida = []
    for afirmacion in (ent.get("claims") or {}).get(propiedad, []):
        snak = afirmacion.get("mainsnak") or {}
        if snak.get("snaktype") == "value" and "datavalue" in snak:
            salida.append(snak["datavalue"]["value"])
    return salida


def _cantidad(valor: dict) -> str | None:
    """{'amount': '+190', 'unit': '.../Q11570'} -> '190 kg' (lo que `normalizar_medida` entiende)."""
    unidad = UNIDADES.get(str(valor.get("unit", "")).rsplit("/", 1)[-1])
    if not unidad:
        return None
    cantidad = str(valor.get("amount", "")).lstrip("+")
    return f"{cantidad} {unidad}" if cantidad else None


def url_imagen(nombre_archivo: str, ancho: int = 1200) -> str:
    return f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(nombre_archivo.replace(' ', '_'))}?width={ancho}"


def _anio(valor: dict) -> int | None:
    """'+1889-06-00T00:00:00Z' -> 1889; '-2560-00-00T00:00:00Z' -> -2560."""
    tiempo = str(valor.get("time", ""))
    if not tiempo or len(tiempo) < 5:
        return None
    signo = -1 if tiempo[0] == "-" else 1
    try:
        return signo * int(tiempo[1:5])
    except ValueError:
        return None


def fila_animal(qid: str, ent: dict, idioma: str = "es") -> dict:
    fila: dict = {"qid": qid}
    cientificos = _valores(ent, PROPIEDADES["nombre_cientifico"])
    if cientificos:
        fila["nombre_cientifico"] = cientificos[0]
    imagenes = _valores(ent, PROPIEDADES["imagen"])
    if imagenes:
        fila["imagen_url"] = url_imagen(imagenes[0])
    estados = [UICN.get(v.get("id")) for v in _valores(ent, PROPIEDADES["uicn"]) if isinstance(v, dict)]
    if any(estados):
        fila["estado_conservacion"] = next(e for e in estados if e)
    for campo, prop in (("peso", "masa"), ("largo", "longitud")):
        for valor in _valores(ent, PROPIEDADES[prop]):
            texto = _cantidad(valor) if isinstance(valor, dict) else None
            if texto:
                fila[campo] = texto
                break
    titulo = ((ent.get("sitelinks") or {}).get(f"{idioma}wiki") or {}).get("title")
    if titulo:
        fila["titulo_wikipedia"] = titulo
    return fila


def fila_curiosidad(qid: str, ent: dict, idioma: str = "es") -> dict:
    fila: dict = {"qid": qid}
    for valor in _valores(ent, PROPIEDADES["inicio"]):
        anio = _anio(valor) if isinstance(valor, dict) else None
        if anio is not None:
            fila["anio"] = str(anio)
            break
    imagenes = _valores(ent, PROPIEDADES["imagen"])
    if imagenes:
        fila["imagen_url"] = url_imagen(imagenes[0])
    titulo = ((ent.get("sitelinks") or {}).get(f"{idioma}wiki") or {}).get("title")
    if titulo:
        fila["titulo_wikipedia"] = titulo
    return fila


CONSTRUCTORES = {"animales": fila_animal, "curiosidades": fila_curiosidad}


def consultar(dominio: str, texto: str, idioma: str = "es", obtener=obtener_json) -> dict | None:
    """Fila de entrada (en el formato que acepta `normalizar()`) para un texto, o None."""
    constructor = CONSTRUCTORES.get(dominio)
    if constructor is None:
        return None
    qid = buscar(texto, idioma, obtener)
    if not qid:
        return None
    ent = entidad(qid, idioma, obtener)
    return constructor(qid, ent, idioma) if ent else None
