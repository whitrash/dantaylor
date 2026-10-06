"""Las cuatro etapas, iguales para todos los dominios:

    ingerir  ->  analizar (en paralelo)  ->  catalogar  ->  exportar

`analizar` corre todos los dominios pedidos en UN solo grupo de trabajadores,
intercalando items de cada dominio y compartiendo el límite de ritmo: animales
y comercios no compiten entre sí por el cupo de la API.

Pasadas: los dominios con `politica_web == "si_dudoso"` se analizan primero sin
web (barato) y lo que queda dudoso va a una segunda pasada con web. Los de
`"siempre"` van con web de una. Los de `"nunca"`, sin web.

Cada corrida deja rastro en `corridas` y `eventos`: es lo que muestra el panel
(`python -m catalogo panel`) y lo que se vuelca a `--estado-json` para que otro
programa (p. ej. un indicador de escritorio) lo lea.
"""

from __future__ import annotations

import asyncio
import csv
import functools
import itertools
import json
import os
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable, Iterator

from . import catalogo, panel
from .almacen import Almacen
from .analizador import AnalizadorClaude, ProcesadorPorLotes
from .modelos import Item
from .paralelo import ErrorFatal, LimitadorDeTasa, ejecutar_en_paralelo

if TYPE_CHECKING:
    from ..dominios.base import Dominio

MODOS = ("auto", "tiempo-real", "lotes")
Entrada = tuple["Dominio", Item, bool]  # (dominio, item, con_web)


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
    canonicos = [_canonico(almacen, dominio, clave) for clave in dict.fromkeys(c for c, _ in por_aporte)]
    return {**cuenta, **almacen.ingerir(canonicos, dominio.version_prompt)}


def importar(almacen: Almacen, dominio: Dominio, filas: Iterable[dict], fuente: str, modelo: str = "importado") -> dict:
    """Carga fichas ya analizadas (de un catálogo anterior) como `listo`, para no
    pagarlas de nuevo. Cada fila es `{"registro": {...}, "ficha": {...}}` o una
    fila plana con los campos del registro y de la ficha mezclados. Lo que falte
    de la ficha se completa con valores neutros."""
    cuenta = {"filas": 0, "importadas": 0, "descartadas": 0}
    for fila in filas:
        cuenta["filas"] += 1
        registro = fila["registro"] if isinstance(fila.get("registro"), dict) else fila
        ficha = dict(fila["ficha"]) if isinstance(fila.get("ficha"), dict) else dict(fila)
        item = dominio.a_item(registro, str(fila.get("fuente") or fuente))
        if item is None:
            cuenta["descartadas"] += 1
            continue
        try:
            ficha = dominio.validar(dominio.completar(ficha, item))
        except ValueError:
            cuenta["descartadas"] += 1
            continue
        almacen.guardar_aportes([item])
        almacen.ingerir([_canonico(almacen, dominio, item.clave)], dominio.version_prompt)
        almacen.guardar_analisis(dominio.nombre, item.clave, ficha, modelo, {"costo_usd": 0.0}, estado="listo")
        cuenta["importadas"] += 1
    return cuenta


def _canonico(almacen: Almacen, dominio: Dominio, clave: str) -> Item:
    return functools.reduce(dominio.fusionar, almacen.aportes(dominio.nombre, clave))


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


class Instantanea:
    """Vuelca el resumen del panel a un archivo JSON, como mucho una vez por segundo.
    Es la forma más simple de que otro programa muestre el estado del motor."""

    def __init__(self, almacen: Almacen, ruta: Path | None, cada: float = 1.0):
        self.almacen = almacen
        self.ruta = Path(ruta) if ruta else None
        self.cada = cada
        self._ultima = 0.0

    def tal_vez(self, forzar: bool = False) -> None:
        if not self.ruta:
            return
        ahora = time.monotonic()
        if not forzar and ahora - self._ultima < self.cada:
            return
        self._ultima = ahora
        temporal = self.ruta.with_suffix(self.ruta.suffix + ".tmp")
        temporal.write_text(json.dumps(panel.resumen(self.almacen), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(temporal, self.ruta)


class _Corrida:
    """Contadores, eventos y tope de gasto de una corrida en marcha."""

    def __init__(
        self,
        almacen: Almacen,
        corrida_id: int,
        dominios: list[Dominio],
        total: int,
        instantanea: Instantanea,
        avisar: Callable[[str], None],
        max_costo: float | None,
        web: bool,
    ):
        self.almacen = almacen
        self.id = corrida_id
        self.dominios = {d.nombre: d for d in dominios}
        self.total = total
        self.instantanea = instantanea
        self.avisar = avisar
        self.max_costo = max_costo
        self.web = web
        self.por_dominio = {d.nombre: {"listos": 0, "verificar": 0, "errores": 0} for d in dominios}
        self.costo = 0.0
        self.reintentos = 0
        self.hechos = 0
        self.detenido = False
        self._paso = max(1, total // 10)

    def evento(self, tipo: str, dominio: str | None = None, clave: str | None = None, **detalle) -> None:
        self.almacen.registrar_evento(self.id, tipo, dominio, clave, **detalle)
        self.instantanea.tal_vez()

    def inicio(self, dominio: Dominio, item: Item, con_web: bool) -> None:
        self.almacen.marcar(dominio.nombre, [item.clave], "en_curso")
        self.evento("inicio", dominio.nombre, item.clave, titulo=dominio.titulo_item(item), con_web=con_web)

    def resultado(self, dominio: Dominio, item: Item, ficha: dict, modelo: str, metricas: dict, con_web: bool) -> None:
        estado = dominio.estado_tras_analisis(ficha, con_web) if self.web else "listo"
        self.almacen.guardar_analisis(
            dominio.nombre, item.clave, ficha, modelo, metricas, estado=estado, con_web=con_web
        )
        self.contar(dominio.nombre, estado, metricas, titulo=dominio.titulo_item(item), clave=item.clave, modelo=modelo)

    def contar(
        self, dominio: str, estado: str, metricas: dict | None, *, titulo: str | None, clave: str, **extra
    ) -> None:
        m = metricas or {}
        self.por_dominio[dominio]["listos" if estado == "listo" else "verificar"] += 1
        self.costo += m.get("costo_usd") or 0.0
        self.evento(
            estado,
            dominio,
            clave,
            titulo=titulo,
            segundos=m.get("segundos"),
            costo_usd=m.get("costo_usd"),
            busquedas=m.get("busquedas"),
            **extra,
        )
        self._progreso()

    def error(self, dominio: Dominio, item: Item, error: BaseException, segundos: float | None = None) -> None:
        self.almacen.guardar_error(dominio.nombre, item.clave, f"{type(error).__name__}: {error}", segundos)
        self.por_dominio[dominio.nombre]["errores"] += 1
        self.evento("error", dominio.nombre, item.clave, titulo=dominio.titulo_item(item), error=str(error)[:300])
        self._progreso()

    def reintento(self, entrada: Entrada, error: BaseException, espera: float) -> None:
        dominio, item, _ = entrada
        self.reintentos += 1
        self.evento(
            "reintento",
            dominio.nombre,
            item.clave,
            titulo=dominio.titulo_item(item),
            error=str(error)[:200],
            espera=espera,
        )

    def pausa(self, segundos: float) -> None:
        self.evento("pausa", segundos=segundos)
        self.avisar(f"  pausa de {segundos:.0f} s pedida por la API")

    def _progreso(self) -> None:
        self.hechos += 1
        self.almacen.actualizar_corrida(
            self.id,
            listos=sum(c["listos"] for c in self.por_dominio.values()),
            errores=sum(c["errores"] for c in self.por_dominio.values()),
            reintentos=self.reintentos,
            costo_usd=round(self.costo, 6),
        )
        if self.hechos % self._paso == 0 or self.hechos == self.total:
            self.avisar(f"  {self.hechos}/{self.total} · US$ {self.costo:.2f}")
        if self.max_costo is not None and self.costo >= self.max_costo and not self.detenido:
            self.detenido = True
            self.evento("tope_costo", costo_usd=round(self.costo, 4), tope=self.max_costo)
            self.avisar(f"  tope de gasto alcanzado (US$ {self.costo:.2f} >= {self.max_costo}); no se toman más items")

    def entradas(self, listas: list[list[Entrada]]) -> Iterator[Entrada]:
        for entrada in _intercalar(listas):
            if self.detenido:
                return
            yield entrada

    def resumen(self, modo: str, segundos: float) -> dict:
        return {
            "modo": modo,
            "corrida_id": self.id,
            "segundos": round(segundos, 2),
            "reintentos": self.reintentos,
            "costo_usd": round(self.costo, 4),
            "detenido_por_costo": self.detenido,
            "dominios": self.por_dominio,
        }


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
    web: bool = True,
    max_costo: float | None = None,
    estado_json: Path | None = None,
    avisar: Callable[[str], None] = lambda m: print(m, file=sys.stderr),
) -> dict:
    if modo not in MODOS:
        raise ValueError(f"modo desconocido: {modo}")
    preparar(almacen, dominios, reintentar_errores=reintentar_errores)
    pendientes = {d.nombre: almacen.pendientes(d.nombre, limite) for d in dominios}
    # Lo que quedó a medio verificar en una corrida anterior entra directo con web.
    previos = {
        d.nombre: almacen.para_verificar(d.nombre) if web and d.politica_web == "si_dudoso" else [] for d in dominios
    }
    total = sum(len(v) for v in pendientes.values()) + sum(len(v) for v in previos.values())
    usa_api = isinstance(analizador, AnalizadorClaude)
    if modo == "auto":
        modo = "lotes" if usa_api and total >= umbral_lotes else "tiempo-real"
    if modo == "lotes" and not usa_api:
        raise ValueError("el modo lotes requiere el analizador de la API de Claude (sin --claude-code ni --simulado)")

    corrida_id = almacen.iniciar_corrida(modo, [d.nombre for d in dominios], concurrencia, analizador.nombre, total)
    instantanea = Instantanea(almacen, estado_json)
    corrida = _Corrida(almacen, corrida_id, dominios, total, instantanea, avisar, max_costo, web)
    avisar(
        f"{total} items pendientes en {', '.join(pendientes)} · modo {modo} · {analizador.nombre}"
        + ("" if web else " · sin web")
    )
    inicio = time.monotonic()
    try:
        if modo == "lotes":
            resultado = await _analizar_en_lotes(
                almacen, dominios, analizador, corrida, pendientes, previos, tam_lote, intervalo_lotes, esperar_lotes
            )
        else:
            resultado = await _analizar_en_tiempo_real(
                almacen, dominios, analizador, corrida, pendientes, previos, concurrencia, por_minuto
            )
            resultado = {**corrida.resumen(modo, time.monotonic() - inicio), **resultado}
    except BaseException as error:
        almacen.terminar_corrida(corrida_id, estado="interrumpida", costo_usd=round(corrida.costo, 6))
        corrida.evento("fin", estado="interrumpida", error=f"{type(error).__name__}: {error}"[:300])
        instantanea.tal_vez(forzar=True)
        raise
    estado_final = "pendiente_lotes" if modo == "lotes" and not esperar_lotes else "terminada"
    almacen.terminar_corrida(corrida_id, estado=estado_final, costo_usd=round(corrida.costo, 6))
    corrida.evento("fin", estado=estado_final)
    instantanea.tal_vez(forzar=True)
    return resultado


async def _fase(
    corrida: _Corrida, analizador, entradas: Iterable[Entrada], concurrencia: int, limitador: LimitadorDeTasa
):
    async def trabajo(entrada: Entrada):
        dominio, item, con_web = entrada
        corrida.inicio(dominio, item, con_web)
        return await analizador.analizar(dominio, item, con_web)

    def al_terminar(entrada: Entrada, resultado: tuple[dict, str, dict]) -> None:
        dominio, item, con_web = entrada
        ficha, modelo, metricas = resultado
        corrida.resultado(dominio, item, ficha, modelo, metricas, con_web)

    def al_fallar(entrada: Entrada, error: BaseException) -> None:
        dominio, item, _ = entrada
        corrida.error(dominio, item, error)

    return await ejecutar_en_paralelo(
        entradas,
        trabajo,
        concurrencia=concurrencia,
        limitador=limitador,
        es_reintentable=analizador.es_reintentable,
        es_fatal=analizador.es_fatal,
        pausa_global=analizador.pausa_global,
        al_terminar=al_terminar,
        al_fallar=al_fallar,
        al_reintentar=corrida.reintento,
        al_pausar=corrida.pausa,
        detener=lambda: corrida.detenido,
    )


async def _analizar_en_tiempo_real(
    almacen, dominios, analizador, corrida: _Corrida, pendientes, previos, concurrencia, por_minuto
) -> dict:
    limitador = LimitadorDeTasa(por_minuto)
    primera = [[(d, it, d.necesita_web(corrida.web)) for it in pendientes[d.nombre]] for d in dominios]
    primera += [[(d, it, True) for it in previos[d.nombre]] for d in dominios]
    corrida.evento("fase", numero=1, items=sum(len(x) for x in primera))
    await _fase(corrida, analizador, corrida.entradas(primera), concurrencia, limitador)

    fases = 1
    if corrida.web and not corrida.detenido:
        segunda = [
            [(d, it, True) for it in almacen.para_verificar(d.nombre)]
            for d in dominios
            if d.politica_web == "si_dudoso"
        ]
        cantidad = sum(len(x) for x in segunda)
        if cantidad:
            fases = 2
            corrida.evento("fase", numero=2, items=cantidad)
            corrida.avisar(f"  segunda pasada con web: {cantidad} items a verificar")
            corrida.total += cantidad
            await _fase(corrida, analizador, corrida.entradas(segunda), concurrencia, limitador)
    return {"fases": fases}


async def _analizar_en_lotes(
    almacen, dominios, analizador, corrida: _Corrida, pendientes, previos, tam_lote, intervalo, esperar
) -> dict:
    procesador = ProcesadorPorLotes(analizador, almacen, tam_lote=tam_lote, intervalo=intervalo, web=corrida.web)
    enviados = {}
    for dominio in dominios:
        try:
            ids = await procesador.enviar(
                dominio, pendientes[dominio.nombre], con_web=dominio.necesita_web(corrida.web)
            )
            if previos[dominio.nombre]:
                ids += await procesador.enviar(dominio, previos[dominio.nombre], con_web=True)
        except Exception as error:
            if analizador.es_fatal(error):
                raise ErrorFatal(error) from error
            raise
        enviados[dominio.nombre] = len(pendientes[dominio.nombre]) + len(previos[dominio.nombre])
        for lote_id in ids:
            corrida.evento("lote_enviado", dominio.nombre, lote_id=lote_id)
        if ids:
            corrida.avisar(f"{dominio.nombre}: {len(ids)} lote(s) enviados: {', '.join(ids)}")
    if not esperar:
        return {
            "modo": "lotes",
            "corrida_id": corrida.id,
            "dominios": {n: {"enviados": k} for n, k in enviados.items()},
        }
    cuentas = await _recoger(almacen, dominios, procesador, corrida)
    return {"modo": "lotes", "corrida_id": corrida.id, "costo_usd": round(corrida.costo, 4), "dominios": cuentas}


async def _recoger(almacen, dominios, procesador: ProcesadorPorLotes, corrida: _Corrida) -> dict:
    """Recoge los lotes abiertos; lo que quede a verificar se manda en una segunda
    tanda con web y se recoge también."""
    analizador = procesador.analizador
    totales = {d.nombre: {"listos": 0, "verificar": 0, "errores": 0, "reencolados": 0} for d in dominios}

    def al_guardar(dominio: str, clave: str, estado: str, metricas: dict | None) -> None:
        if estado == "error":
            corrida.por_dominio[dominio]["errores"] += 1
            corrida.evento("error", dominio, clave, titulo=clave)
            corrida._progreso()
        else:
            corrida.contar(dominio, estado, metricas, titulo=clave, clave=clave)

    for _ronda in range(2):
        try:
            cuentas = await asyncio.gather(*(procesador.recoger(d, al_guardar) for d in dominios))
        except Exception as error:
            if analizador.es_fatal(error):
                raise ErrorFatal(error) from error
            raise
        for dominio, cuenta in zip(dominios, cuentas, strict=True):
            for clave, valor in cuenta.items():
                totales[dominio.nombre][clave] += valor
            corrida.evento("lote_recibido", dominio.nombre, **cuenta)
        if not corrida.web:
            break
        hubo_segunda = False
        for dominio in dominios:
            if dominio.politica_web != "si_dudoso":
                continue
            items = almacen.para_verificar(dominio.nombre)
            if items:
                hubo_segunda = True
                corrida.total += len(items)
                for lote_id in await procesador.enviar(dominio, items, con_web=True):
                    corrida.evento("lote_enviado", dominio.nombre, lote_id=lote_id, segunda_pasada=True)
        if not hubo_segunda:
            break
    return totales


async def recoger_lotes(
    almacen: Almacen,
    dominios: list[Dominio],
    analizador,
    intervalo: float = 60.0,
    *,
    web: bool = True,
    estado_json: Path | None = None,
    avisar: Callable[[str], None] = lambda m: print(m, file=sys.stderr),
) -> dict:
    """Espera y guarda los lotes abiertos. Sirve para retomar en otra corrida."""
    pendientes = sum(almacen.lote(i)["cantidad"] for d in dominios for i in almacen.lotes_abiertos(d.nombre))
    corrida_id = almacen.iniciar_corrida("recoger", [d.nombre for d in dominios], 0, analizador.nombre, pendientes)
    instantanea = Instantanea(almacen, estado_json)
    corrida = _Corrida(almacen, corrida_id, dominios, pendientes, instantanea, avisar, None, web)
    procesador = ProcesadorPorLotes(analizador, almacen, intervalo=intervalo, web=web)
    try:
        totales = await _recoger(almacen, dominios, procesador, corrida)
    except BaseException as error:
        almacen.terminar_corrida(corrida_id, estado="interrumpida", costo_usd=round(corrida.costo, 6))
        corrida.evento("fin", estado="interrumpida", error=f"{type(error).__name__}: {error}"[:300])
        raise
    almacen.terminar_corrida(corrida_id, estado="terminada", costo_usd=round(corrida.costo, 6))
    corrida.evento("fin", estado="terminada")
    instantanea.tal_vez(forzar=True)
    return totales


def catalogar(almacen: Almacen, dominio: Dominio, carpeta: Path) -> tuple[dict, list[Path]]:
    armado = catalogo.construir(dominio, almacen.analizados(dominio.nombre))
    return armado, catalogo.exportar(armado, carpeta / dominio.nombre)
