"""Armado del catálogo: identidad final, orden, árbol, facetas y cola de revisión.

Todo esto es lo que hace un catálogo de supermercado con sus fichas, aplicado a
cualquier dominio:
  * árbol de secciones (góndolas) en el orden en que se declaró la taxonomía;
  * facetas para filtrar (marca/precio allá; continente/dieta/época acá);
  * completitud de cada ficha y una cola de "revisar" para lo dudoso.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

from .modelos import Registro
from .taxonomia import SEPARADOR

if TYPE_CHECKING:
    from ..dominios.base import Dominio

_RANGO_CONFIANZA = {"alta": 2, "media": 1, "baja": 0}
_CAMPOS_COMUNES = {"ruta", "confianza", "etiquetas"}


def completitud(dominio: Dominio, registro: Registro) -> float:
    """Fracción de campos propios de la ficha con contenido (+ tener imagen)."""
    campos = [c for c in dominio.propiedades() if c not in _CAMPOS_COMUNES]
    llenos = sum(1 for c in campos if registro.analisis.get(c) not in (None, "", []))
    tiene_imagen = bool(registro.item.datos.get("imagen_url") or registro.item.datos.get("imagen_archivo"))
    return round((llenos + tiene_imagen) / (len(campos) + 1), 2)


def _mejor(dominio: Dominio, a: Registro, b: Registro) -> Registro:
    def puntaje(r: Registro) -> tuple:
        return (r.vigente, _RANGO_CONFIANZA.get(r.analisis.get("confianza"), 0), completitud(dominio, r))

    ganador, perdedor = (a, b) if puntaje(a) >= puntaje(b) else (b, a)
    fuentes = list(dict.fromkeys(ganador.item.fuentes + perdedor.item.fuentes))
    return replace(ganador, item=replace(ganador.item, fuentes=fuentes))


def construir(dominio: Dominio, registros: list[Registro]) -> dict:
    # 1. Identidad después del análisis (p. ej. dos nombres comunes, una especie).
    unicos: dict[str, Registro] = {}
    alias: dict[str, list[str]] = {}
    for registro in registros:
        clave = dominio.clave_catalogo(registro)
        alias.setdefault(clave, []).append(registro.item.clave)
        unicos[clave] = _mejor(dominio, unicos[clave], registro) if clave in unicos else registro

    # 2. Orden: primero la posición en la taxonomía, después el criterio del dominio.
    ordenados = sorted(
        unicos.items(),
        key=lambda par: (dominio.taxonomia.posicion(par[1].analisis["ruta"]), dominio.clave_orden(par[1])),
    )

    # 3. Árbol de secciones. Como la lista ya está ordenada por taxonomía, las
    #    hojas de una misma sección quedan contiguas.
    raiz: dict = {"secciones": []}
    facetas: dict[str, Counter] = {f: Counter() for f in dominio.facetas}
    revisar = []
    for clave, registro in ordenados:
        ficha = {
            "clave": clave,
            "titulo": dominio.titulo(registro),
            **registro.analisis,
            "datos": registro.item.datos,
            "fuentes": registro.item.fuentes,
            "alias": sorted(set(alias[clave]) - {clave}),
            "modelo": registro.modelo,
            "vigente": registro.vigente,
            "completitud": completitud(dominio, registro),
        }
        nodo = raiz
        for parte in registro.analisis["ruta"].split(SEPARADOR):
            secciones = nodo.setdefault("secciones", [])
            if not secciones or secciones[-1]["nombre"] != parte:
                secciones.append({"nombre": parte})
            nodo = secciones[-1]
        nodo.setdefault("items", []).append(ficha)

        for faceta in dominio.facetas:
            facetas[faceta].update(dominio.valores_faceta(registro, faceta))

        motivos = []
        if registro.analisis.get("confianza") == "baja":
            motivos.append("confianza baja")
        if ficha["completitud"] < 0.5:
            motivos.append(f"ficha incompleta ({ficha['completitud']:.0%})")
        if not registro.vigente:
            motivos.append("análisis vencido o datos nuevos sin analizar")
        if motivos:
            revisar.append({"clave": clave, "titulo": ficha["titulo"], "motivos": motivos})

    return {
        "dominio": dominio.nombre,
        "generado_en": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(ordenados),
        "secciones": raiz["secciones"],
        "facetas": {f: dict(c.most_common()) for f, c in facetas.items()},
        "revisar": revisar,
    }


def a_markdown(catalogo: dict) -> str:
    lineas = [f"# Catálogo: {catalogo['dominio']}", "", f"_{catalogo['total']} fichas · {catalogo['generado_en']}_", ""]

    def bajar(secciones: list[dict], nivel: int) -> None:
        for seccion in secciones:
            lineas.append(f"{'#' * min(nivel, 6)} {seccion['nombre']}")
            lineas.append("")
            for ficha in seccion.get("items", []):
                resumen = ficha.get("descripcion") or ficha.get("resumen") or ""
                marca = "" if ficha.get("confianza") != "baja" else " ⚠️"
                lineas.append(f"- **{ficha['titulo']}**{marca}" + (f": {resumen}" if resumen else ""))
            if seccion.get("items"):
                lineas.append("")
            bajar(seccion.get("secciones", []), nivel + 1)

    bajar(catalogo["secciones"], 2)
    if catalogo["facetas"]:
        lineas += ["## Filtros (facetas)", ""]
        for faceta, valores in catalogo["facetas"].items():
            lista = ", ".join(f"{v} ({n})" for v, n in list(valores.items())[:15]) or "—"
            lineas.append(f"- **{faceta}**: {lista}")
        lineas.append("")
    if catalogo["revisar"]:
        lineas += ["## Para revisar", ""]
        lineas += [f"- {r['titulo']}: {', '.join(r['motivos'])}" for r in catalogo["revisar"]]
        lineas.append("")
    return "\n".join(lineas)


def exportar(catalogo: dict, carpeta: Path) -> list[Path]:
    carpeta.mkdir(parents=True, exist_ok=True)
    json_ruta = carpeta / "catalogo.json"
    md_ruta = carpeta / "catalogo.md"
    jsonl_ruta = carpeta / "fichas.jsonl"
    json_ruta.write_text(json.dumps(catalogo, ensure_ascii=False, indent=2), encoding="utf-8")
    md_ruta.write_text(a_markdown(catalogo), encoding="utf-8")

    def fichas(secciones: list[dict]):
        for seccion in secciones:
            yield from seccion.get("items", [])
            yield from fichas(seccion.get("secciones", []))

    with jsonl_ruta.open("w", encoding="utf-8") as archivo:
        for ficha in fichas(catalogo["secciones"]):
            archivo.write(json.dumps(ficha, ensure_ascii=False) + "\n")
    return [json_ruta, md_ruta, jsonl_ruta]
