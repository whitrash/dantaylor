"""Las cuatro etapas, iguales para todos los dominios:

    ingerir  ->  analizar (en paralelo)  ->  catalogar  ->  exportar

`analizar` corre todos los dominios pedidos en UN solo grupo de trabajadores,
intercalando items de cada dominio y compartiendo el límite de ritmo: animales
y comercios no compiten entre sí por el cupo de la API.
"""

from __future__ import annotations

import asyncio
import csv
import functools
import itertools
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, Iterator

from . import catalogo
from .almacen import Almacen
from .analizador import AnalizadorClaude, ProcesadorPorLotes
from .modelos import Item
from .paralelo import ErrorFatal, LimitadorDeTasa, ejecutar_en_paralelo

if TYPE_CHECKING:
    from ..dominios.base import Dominio

MODOS = ("auto", "tiempo-real", "lotes")


def leer_filas(ruta: Path) -> Iterator[dict]:
    sufijo = ruta.suffix.lower()
    if sufijo == ".csv":
        with ruta.open(encoding="utf-8-sig", newline="") as archivo:
            yield from csv.DictReader(archivo)
    elif sufijo == ".jsonl":
        with ruta.open(encoding="utf-8") as archivo:
            yield from (json.loads(linea) for linea in archivo if linea.strip())
    elif sufijo == ".json":
        yield from json.loads(ruta.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"Formato no soportado: {ruta} (usar .csv, .jsonl o .json)")


def ingerir(almacen: Almacen, dominio: Dominio, filas: Iterable[dict], fuente: str) -> dict[str, int]:
    """Normaliza, identifica y combina. Una columna `fuente` en la fila tiene
    prioridad sobre el nombre de fuente del archivo."""
    por_aporte: dict[tuple[str, str], Item] = {}
    cuenta = {"filas": 0, "descartadas": 0, "repetidas_en_archivo": 0}
    for fila in filas:
        cuenta["filas"] += 1
        item = dominio.a_item(fila, str(fila.get("fuente") or fuente))
        if item is None:
            cuenta["descartadas"] += 1
            continue
        clave = (item.clave, item.fuentes[0])
        if clave in por_aporte:
            cuenta["repetidas_en_archivo"] += 1
            por_aporte[clave] = dominio.fusionar(por_aporte[clave], item)
        else:
            por_aporte[clave] = item

    almacen.guardar_aportes(por_aporte.values())
    canonicos = [
        functools.reduce(dominio.fusionar, almacen.aportes(dominio.nombre, clave))
        for clave in dict.fromkeys(c for c, _ in por_aporte)
    ]
    return {**cuenta, **almacen.ingerir(canonicos, dominio.version_prompt)}


def _intercalar(listas: list[list]) -> Iterator:
    vacio = object()
    for grupo in itertools.zip_longest(*listas, fillvalue=vacio):
        yield from (x for x in grupo if x is not vacio)


def preparar(almacen: Almacen, dominios: list[Dominio], *, reintentar_errores: bool = False) -> None:
    for dominio in dominios:
        almacen.recuperar_interrumpidos(dominio.nombre)
        almacen.vencer(dominio.nombre, dominio.ttl_dias)
        if reintentar_errores:
            almacen.reintentar_errores(dominio.nombre)


async def analizar(
    almacen: Almacen,
    dominios: list[Dominio],
    analizador,
    *,
    modo: str = "auto",
    concurrencia: int = 8,
    por_minuto: float | None = None,
    limite: int | None = None,
    reintentar_errores: bool = False,
    umbral_lotes: int = 1000,
    tam_lote: int = 10_000,
    intervalo_lotes: float = 60.0,
    esperar_lotes: bool = True,
    avisar: Callable[[str], None] = lambda m: print(m, file=sys.stderr),
) -> dict:
    if modo not in MODOS:
        raise ValueError(f"modo desconocido: {modo}")
    preparar(almacen, dominios, reintentar_errores=reintentar_errores)
    pendientes = {d.nombre: almacen.pendientes(d.nombre, limite) for d in dominios}
    total = sum(len(v) for v in pendientes.values())
    usa_claude = isinstance(analizador, AnalizadorClaude)
    if modo == "auto":
        modo = "lotes" if usa_claude and total >= umbral_lotes else "tiempo-real"
    if modo == "lotes" and not usa_claude:
        raise ValueError("el modo lotes requiere el analizador de Claude")
    avisar(f"{total} items pendientes en {', '.join(pendientes)} · modo {modo}")

    if modo == "lotes":
        procesador = ProcesadorPorLotes(analizador, almacen, tam_lote=tam_lote, intervalo=intervalo_lotes)
        for dominio in dominios:
            try:
                ids = await procesador.enviar(dominio, pendientes[dominio.nombre])
            except Exception as error:
                if analizador.es_fatal(error):
                    raise ErrorFatal(error) from error
                raise
            if ids:
                avisar(f"{dominio.nombre}: {len(ids)} lote(s) enviados: {', '.join(ids)}")
        if not esperar_lotes:
            return {"modo": modo, "dominios": {d.nombre: {"enviados": len(pendientes[d.nombre])} for d in dominios}}
        return {"modo": modo, "dominios": await recoger_lotes(almacen, dominios, analizador, intervalo_lotes)}

    por_dominio = {d.nombre: {"listos": 0, "errores": 0} for d in dominios}
    hechos = 0
    paso = max(1, total // 10)

    def contar(dominio: Dominio, campo: str) -> None:
        nonlocal hechos
        por_dominio[dominio.nombre][campo] += 1
        hechos += 1
        if hechos % paso == 0 or hechos == total:
            avisar(f"  {hechos}/{total}")

    async def trabajo(entrada: tuple[Dominio, Item]):
        dominio, item = entrada
        almacen.marcar(dominio.nombre, [item.clave], "en_curso")
        return await analizador.analizar(dominio, item)

    def al_terminar(entrada: tuple[Dominio, Item], resultado: tuple[dict, str]) -> None:
        dominio, item = entrada
        ficha, modelo = resultado
        almacen.guardar_analisis(dominio.nombre, item.clave, ficha, modelo)
        contar(dominio, "listos")

    def al_fallar(entrada: tuple[Dominio, Item], error: BaseException) -> None:
        dominio, item = entrada
        almacen.guardar_error(dominio.nombre, item.clave, f"{type(error).__name__}: {error}")
        contar(dominio, "errores")

    resumen = await ejecutar_en_paralelo(
        _intercalar([[(d, it) for it in pendientes[d.nombre]] for d in dominios]),
        trabajo,
        concurrencia=concurrencia,
        limitador=LimitadorDeTasa(por_minuto),
        es_reintentable=analizador.es_reintentable,
        es_fatal=analizador.es_fatal,
        pausa_global=analizador.pausa_global,
        al_terminar=al_terminar,
        al_fallar=al_fallar,
    )
    return {
        "modo": modo,
        "segundos": round(resumen.segundos, 2),
        "reintentos": resumen.reintentos,
        "dominios": por_dominio,
    }


async def recoger_lotes(almacen: Almacen, dominios: list[Dominio], analizador, intervalo: float = 60.0) -> dict:
    """Espera y guarda los lotes abiertos. Sirve para retomar en otra corrida."""
    procesador = ProcesadorPorLotes(analizador, almacen, intervalo=intervalo)
    try:
        cuentas = await asyncio.gather(*(procesador.recoger(d) for d in dominios))
    except Exception as error:
        if analizador.es_fatal(error):
            raise ErrorFatal(error) from error
        raise
    return {d.nombre: c for d, c in zip(dominios, cuentas, strict=True)}


def catalogar(almacen: Almacen, dominio: Dominio, carpeta: Path) -> tuple[dict, list[Path]]:
    armado = catalogo.construir(dominio, almacen.analizados(dominio.nombre))
    return armado, catalogo.exportar(armado, carpeta / dominio.nombre)
