"""Señales de actividad en Wikipedia para un título.

No se lee el artículo: se mira si *se mueve*. Dos señales:

* **Ediciones firmes**: cambios de tamaño apreciable en los últimos días que
  no fueron revertidos (MediaWiki etiqueta las ediciones revertidas con
  `mw-reverted`). Una edición que sigue en pie a los días es un indicio de que
  algo cambió de verdad; una de hace una hora todavía no dice nada.
* **Interés sostenido**: visitas diarias muy por encima de la mediana del mes
  durante varios días seguidos. Un pico de un día suele ser un meme o un
  titular; tres días seguidos, un hecho.

Ninguna de las dos dice *qué* cambió: eso lo decide la segunda pasada con web
sobre la ficha. Acá solo se decide si vale la pena pagarla.
"""

from __future__ import annotations

import json
import statistics
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Callable

from ..core.novedades import Senal

USER_AGENT = "catalogos-motor/0.1 (https://github.com/whitrash/dantaylor)"
BYTES_MINIMOS = 50  # ediciones más chicas (typos, enlaces) no cuentan
FACTOR_VISITAS = 3.0
VISITAS_MINIMAS = 100

Obtener = Callable[[str], dict]


def obtener_json(url: str, timeout: float = 20.0) -> dict:
    pedido = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(pedido, timeout=timeout) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def url_articulo(titulo: str, idioma: str = "es") -> str:
    return f"https://{idioma}.wikipedia.org/wiki/{urllib.parse.quote(titulo.replace(' ', '_'))}"


def revisiones(titulo: str, idioma: str = "es", limite: int = 50, obtener: Obtener = obtener_json) -> list[dict]:
    """Últimas revisiones, de la más nueva a la más vieja."""
    consulta = urllib.parse.urlencode(
        {
            "action": "query",
            "prop": "revisions",
            "titles": titulo,
            "rvlimit": limite,
            "rvprop": "ids|timestamp|user|comment|size|tags",
            "format": "json",
            "formatversion": 2,
        }
    )
    datos = obtener(f"https://{idioma}.wikipedia.org/w/api.php?{consulta}")
    paginas = (datos.get("query") or {}).get("pages") or []
    if not paginas or paginas[0].get("missing"):
        return []
    salida = []
    for r in paginas[0].get("revisions", []):
        etiquetas = r.get("tags") or []
        salida.append(
            {
                "id": r.get("revid"),
                "ts": _epoch(r.get("timestamp", "")),
                "usuario": r.get("user", ""),
                "comentario": r.get("comment", ""),
                "tamano": r.get("size", 0),
                "revertida": "mw-reverted" in etiquetas,
                "revierte": any(t in etiquetas for t in ("mw-undo", "mw-rollback", "mw-manual-revert")),
            }
        )
    return salida


def visitas(
    titulo: str, idioma: str = "es", dias: int = 30, obtener: Obtener = obtener_json, ahora: float | None = None
) -> list[tuple[str, int]]:
    """Visitas diarias [(AAAAMMDD, n)], hasta ayer (la API no tiene el día en curso)."""
    fin = datetime.fromtimestamp(ahora or time.time(), tz=timezone.utc) - timedelta(days=1)
    inicio = fin - timedelta(days=dias - 1)
    articulo = urllib.parse.quote(titulo.replace(" ", "_"), safe="")
    url = (
        f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{idioma}.wikipedia/all-access/user/"
        f"{articulo}/daily/{inicio:%Y%m%d}00/{fin:%Y%m%d}00"
    )
    datos = obtener(url)
    return [(item["timestamp"][:8], int(item["views"])) for item in datos.get("items", [])]


def senales(
    titulo: str,
    idioma: str = "es",
    dias: int = 30,
    obtener: Obtener = obtener_json,
    ahora: float | None = None,
) -> list[Senal]:
    ahora = ahora or time.time()
    fuente = f"{idioma}.wikipedia.org"
    resultado: list[Senal] = []

    revs = revisiones(titulo, idioma, obtener=obtener)
    for actual, anterior in zip(revs, revs[1:] + [None], strict=False):
        if actual["ts"] < ahora - dias * 86400:
            break
        if actual["revertida"] or actual["revierte"]:
            continue
        if "bot" in actual["usuario"].lower():
            continue
        delta = actual["tamano"] - (anterior["tamano"] if anterior else 0)
        if abs(delta) < BYTES_MINIMOS:
            continue
        resultado.append(
            Senal(
                "wikipedia_edicion",
                fuente,
                actual["ts"],
                titular=actual["comentario"],
                url=f"https://{idioma}.wikipedia.org/w/index.php?diff={actual['id']}",
                dias_vigente=(ahora - actual["ts"]) / 86400,
            )
        )

    serie = visitas(titulo, idioma, dias, obtener=obtener, ahora=ahora)
    if len(serie) >= 10:
        base = [n for _, n in serie[:-7]]
        mediana = statistics.median(base) if base else 0
        umbral = max(VISITAS_MINIMAS, mediana * FACTOR_VISITAS)
        ultimos = serie[-7:]
        elevados = [(dia, n) for dia, n in ultimos if n >= umbral]
        if elevados:
            seguidos = 0
            for _, n in reversed(ultimos):
                if n >= umbral:
                    seguidos += 1
                else:
                    break
            dia, maximo = max(elevados, key=lambda x: x[1])
            resultado.append(
                Senal(
                    "wikipedia_visitas",
                    fuente,
                    _epoch_dia(dia),
                    titular=f"{maximo} visitas/día contra una mediana de {mediana:.0f}",
                    url=url_articulo(titulo, idioma),
                    dias_vigente=seguidos,
                )
            )
    return resultado


def _epoch(iso: str) -> float:
    if not iso:
        return 0.0
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _epoch_dia(aaaammdd: str) -> float:
    return datetime.strptime(aaaammdd, "%Y%m%d").replace(tzinfo=timezone.utc).timestamp()
