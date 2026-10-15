"""Verifica archivos entregados por un recolector antes de ingerirlos.

    python herramientas/verificar_recoleccion.py animales/ comercios/relevamiento.csv

Cada ruta es una carpeta llamada como el dominio (con un archivo por fuente) o
un archivo dentro de una carpeta así. Informa filas, descartes, duplicados,
columnas desconocidas y valores que debían quedar vacíos. En `ofertas`, además,
cada fila tiene que traer precio y un enlace http(s) a la página del producto
(no a la portada ni a un buscador): sin eso la oferta no se publica. No abre los
enlaces (eso lo hace `python -m catalogo enlaces ofertas`). No toca la base.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from catalogo.core.enlaces import es_portada  # noqa: E402
from catalogo.core.pipeline import leer_filas  # noqa: E402
from catalogo.dominios import DOMINIOS  # noqa: E402

COLUMNAS = {
    "animales": {"nombre", "nombre_cientifico", "imagen_url", "peso", "largo", "notas", "fuente"},
    "curiosidades": {"titulo", "categoria", "anio", "pais", "descripcion", "imagen_url", "fuente"},
    "comercios": {
        "nombre",
        "direccion",
        "barrio",
        "ciudad",
        "rubro",
        "telefono",
        "horario",
        "sitio_web",
        "descripcion",
        "imagen_url",
        "fuente",
    },
    "ofertas": {
        "producto",
        "comercio",
        "precio",
        "precio_anterior",
        "enlace",
        "marca",
        "presentacion",
        "ean",
        "vigencia_hasta",
        "sucursal",
        "imagen_url",
        "fuente",
    },
}
SOSPECHOSOS = {"n/a", "na", "desconocido", "desconocida", "?", "-", "null", "none", "sin datos", "s/d"}


def verificar(archivo: Path, dominio_nombre: str) -> bool:
    dominio = DOMINIOS[dominio_nombre]
    filas = list(leer_filas(archivo))
    columnas = set().union(*(f.keys() for f in filas)) if filas else set()
    desconocidas = sorted(columnas - COLUMNAS[dominio_nombre])
    claves: Counter = Counter()
    descartadas = []
    sospechosos = []
    sin_enlace = []
    for i, fila in enumerate(filas, 2):
        for columna, valor in fila.items():
            if str(valor or "").strip().lower() in SOSPECHOSOS:
                sospechosos.append(f"fila {i}: {columna}={valor!r}")
        item = dominio.a_item(fila, archivo.stem)
        if item is None:
            descartadas.append(f"fila {i}: sin identidad ({dict(fila)})")
        else:
            claves[item.clave] += 1
            if dominio.exige_enlace:
                sin_enlace += [
                    f"fila {i} ({item.datos.get(dominio.campo_producto)}): {p}" for p in problemas_enlace(dominio, item)
                ]
    duplicados = [c for c, n in claves.items() if n > 1]
    ok = not (desconocidas or descartadas or duplicados or sospechosos or sin_enlace)
    print(f"{'OK ' if ok else 'REVISAR'} {archivo}  ({dominio_nombre}, fuente '{archivo.stem}'): {len(filas)} filas")
    for etiqueta, lista in (
        ("columnas desconocidas", desconocidas),
        ("filas descartadas", descartadas),
        ("duplicados en el archivo", duplicados),
        ("valores que debían quedar vacíos", sospechosos),
        ("ofertas que NO se van a publicar (sin precio o sin enlace al producto)", sin_enlace),
    ):
        if lista:
            print(f"  - {etiqueta} ({len(lista)}):")
            for linea in lista[:10]:
                print(f"      {linea}")
            if len(lista) > 10:
                print(f"      … y {len(lista) - 10} más")
    return ok


def problemas_enlace(dominio, item) -> list[str]:
    """Lo que se puede saber sin abrir el enlace: que exista, que sea http(s) y que
    no sea la portada ni un buscador."""
    problemas = []
    url, _, precio = dominio.pedido_enlace(item)
    if precio is None:
        problemas.append("sin precio")
    if not url:
        return problemas + ["sin enlace"]
    if not url.startswith(("http://", "https://")):
        return problemas + [f"el enlace no es una URL http(s): {url!r}"]
    motivo = es_portada(url, url)
    return problemas + ([motivo] if motivo else [])


def main(rutas: list[str]) -> int:
    todo_ok = True
    for ruta in map(Path, rutas):
        archivos = (
            sorted(p for p in ruta.iterdir() if p.suffix in (".csv", ".jsonl", ".json")) if ruta.is_dir() else [ruta]
        )
        for archivo in archivos:
            dominio = archivo.parent.name if archivo.parent.name in DOMINIOS else None
            if dominio is None:
                print(f"REVISAR {archivo}: la carpeta debe llamarse como el dominio ({', '.join(DOMINIOS)})")
                todo_ok = False
                continue
            todo_ok &= verificar(archivo, dominio)
    return 0 if todo_ok else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    raise SystemExit(main(sys.argv[1:]))
