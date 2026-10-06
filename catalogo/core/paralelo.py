"""Ejecución en paralelo con límite de concurrencia, ritmo y reintentos.

Es genérico a propósito: lo usa el análisis con Claude, pero sirve igual para
descargar imágenes o consultar una API de precios. Una sola instancia de
`LimitadorDeTasa` puede compartirse entre varios dominios para que los dos
proyectos no se peleen por el mismo cupo de la API.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable


class LimitadorDeTasa:
    """Espacia los arranques para no superar `por_minuto`, y permite pausar a todos
    los trabajadores juntos cuando la API responde 429 (en vez de que cada uno
    insista por su cuenta)."""

    def __init__(self, por_minuto: float | None = None):
        self.intervalo = 60.0 / por_minuto if por_minuto else 0.0
        self._siguiente = 0.0
        self._pausa_hasta = 0.0
        self._candado = asyncio.Lock()

    async def esperar(self) -> None:
        async with self._candado:
            ahora = time.monotonic()
            turno = max(ahora, self._siguiente, self._pausa_hasta)
            self._siguiente = turno + self.intervalo
        if turno > ahora:
            await asyncio.sleep(turno - ahora)

    def pausar(self, segundos: float) -> None:
        self._pausa_hasta = max(self._pausa_hasta, time.monotonic() + segundos)


class ErrorFatal(Exception):
    """Un error que se repetiría en todas las entradas (credenciales, modelo
    inexistente): se corta todo en vez de marcar miles de fallas iguales."""

    def __init__(self, error: BaseException):
        super().__init__(f"{type(error).__name__}: {error}")
        self.error = error


@dataclass
class Resumen:
    ok: int = 0
    fallidos: int = 0
    reintentos: int = 0
    segundos: float = 0.0


def _nunca(_: BaseException) -> bool:
    return False


def _sin_pausa(_: BaseException) -> float | None:
    return None


async def ejecutar_en_paralelo(
    entradas: Iterable[Any],
    trabajo: Callable[[Any], Awaitable[Any]],
    *,
    concurrencia: int = 8,
    limitador: LimitadorDeTasa | None = None,
    reintentos: int = 3,
    espera_base: float = 1.0,
    espera_max: float = 60.0,
    es_reintentable: Callable[[BaseException], bool] = _nunca,
    es_fatal: Callable[[BaseException], bool] = _nunca,
    pausa_global: Callable[[BaseException], float | None] = _sin_pausa,
    al_terminar: Callable[[Any, Any], None] | None = None,
    al_fallar: Callable[[Any, BaseException], None] | None = None,
    al_reintentar: Callable[[Any, BaseException, float], None] | None = None,
    al_pausar: Callable[[float], None] | None = None,
    detener: Callable[[], bool] | None = None,
) -> Resumen:
    """Procesa `entradas` con `concurrencia` trabajadores.

    - Cada resultado se entrega a `al_terminar` apenas está listo (checkpoint:
      si el proceso se corta, lo ya terminado no se pierde).
    - Los errores reintentables esperan con backoff exponencial + jitter.
    - Si `pausa_global` devuelve segundos (p. ej. por un 429), se frena a todos.
    - Si `es_fatal`, se detiene todo y se lanza `ErrorFatal`; las entradas en
      curso no se reportan como fallidas.
    - Si `detener()` devuelve True (p. ej. tope de gasto), no se arranca ninguna
      entrada más; las que ya están en vuelo terminan normalmente.
    - Las entradas se consumen de a poco (cola acotada), así que sirve con
      generadores de cientos de miles de elementos.
    """
    if concurrencia < 1:
        raise ValueError("concurrencia debe ser >= 1")
    limitador = limitador or LimitadorDeTasa()
    resumen = Resumen()
    cola: asyncio.Queue = asyncio.Queue(maxsize=concurrencia * 2)
    fin = object()
    inicio = time.monotonic()

    async def productor() -> None:
        for entrada in entradas:
            if detener and detener():
                break
            await cola.put(entrada)
        for _ in range(concurrencia):
            await cola.put(fin)

    async def trabajador() -> None:
        while True:
            entrada = await cola.get()
            if entrada is fin:
                return
            if detener and detener():
                continue  # se vacía la cola sin arrancar nada nuevo
            intento = 0
            while True:
                await limitador.esperar()
                try:
                    resultado = await trabajo(entrada)
                except Exception as error:  # noqa: BLE001 - se clasifica abajo
                    if es_fatal(error):
                        raise ErrorFatal(error) from error
                    if intento < reintentos and es_reintentable(error):
                        pausa = pausa_global(error)
                        if pausa:
                            limitador.pausar(pausa)
                            if al_pausar:
                                al_pausar(pausa)
                        espera = min(espera_max, espera_base * 2**intento)
                        intento += 1
                        resumen.reintentos += 1
                        if al_reintentar:
                            al_reintentar(entrada, error, espera)
                        await asyncio.sleep(espera * random.uniform(0.5, 1.0))
                        continue
                    resumen.fallidos += 1
                    if al_fallar:
                        al_fallar(entrada, error)
                    break
                resumen.ok += 1
                if al_terminar:
                    al_terminar(entrada, resultado)
                break

    tareas = [asyncio.create_task(productor())] + [asyncio.create_task(trabajador()) for _ in range(concurrencia)]
    try:
        await asyncio.gather(*tareas)
    finally:
        for tarea in tareas:
            tarea.cancel()
        # Recoge lo que quedó (cancelaciones u otros ErrorFatal simultáneos).
        await asyncio.gather(*tareas, return_exceptions=True)
    resumen.segundos = time.monotonic() - inicio
    return resumen
