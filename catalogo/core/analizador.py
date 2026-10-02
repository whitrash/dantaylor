"""Backends de análisis.

- `AnalizadorSimulado`: sin red ni costo. Prueba la logística de punta a punta.
- `AnalizadorClaude`: una llamada por item, muchas en paralelo. Para volúmenes
  chicos/medianos o cuando el resultado hace falta ya.
- `ProcesadorPorLotes`: Message Batches API. Hasta 100.000 items por lote, 50 %
  más barato, resultados en menos de 24 h (en general menos de 1 h). Para cargas
  grandes que no son urgentes (catalogar miles de animales de una vez).

Todos devuelven `(ficha, modelo)`; la ficha ya validada contra el esquema del dominio.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import TYPE_CHECKING, Iterable, Iterator

import anthropic

from .almacen import Almacen
from .modelos import Item

if TYPE_CHECKING:
    from ..dominios.base import Dominio

MODELO_POR_DEFECTO = "claude-opus-5-5"
# Si el modelo rechaza un item, la API lo reintenta en otro modelo dentro de la
# misma llamada. No existe en la Batches API: ahí el rechazo queda como error y
# se puede reintentar luego en tiempo real (`--reintentar-errores`).
BETA_FALLBACK = "server-side-fallback-2026-07-01"


class ErrorDeAnalisis(Exception):
    """Falla propia del item (no de la red): reintentarlo igual no sirve."""


class Rechazo(ErrorDeAnalisis):
    pass


class RespuestaIncompleta(ErrorDeAnalisis):
    pass


class RespuestaInvalida(ErrorDeAnalisis):
    pass


def interpretar(dominio: Dominio, mensaje) -> dict:
    if mensaje.stop_reason == "refusal":
        detalle = getattr(mensaje, "stop_details", None)
        raise Rechazo(f"el modelo rechazó el item (categoría: {getattr(detalle, 'category', None)})")
    if mensaje.stop_reason == "max_tokens":
        raise RespuestaIncompleta("la respuesta se cortó por max_tokens")
    texto = next((b.text for b in mensaje.content if b.type == "text"), None)
    if texto is None:
        raise RespuestaInvalida("la respuesta no trae texto")
    try:
        return dominio.validar(json.loads(texto))
    except ValueError as error:  # incluye json.JSONDecodeError
        raise RespuestaInvalida(str(error)) from error


class AnalizadorSimulado:
    modelo = "simulado"

    def __init__(self, latencia: float = 0.0):
        self.latencia = latencia

    async def analizar(self, dominio: Dominio, item: Item) -> tuple[dict, str]:
        if self.latencia:
            await asyncio.sleep(self.latencia)
        return dominio.validar(dominio.simular(item)), self.modelo

    @staticmethod
    def es_reintentable(error: BaseException) -> bool:
        return False

    @staticmethod
    def es_fatal(error: BaseException) -> bool:
        return False

    @staticmethod
    def pausa_global(error: BaseException) -> float | None:
        return None


class AnalizadorClaude:
    def __init__(
        self,
        modelo: str = MODELO_POR_DEFECTO,
        esfuerzo: str = "medium",
        max_tokens: int = 16000,
        cliente: anthropic.AsyncAnthropic | None = None,
    ):
        self.modelo = modelo
        self.esfuerzo = esfuerzo
        self.max_tokens = max_tokens
        self.cliente = cliente or anthropic.AsyncAnthropic()

    def parametros(self, dominio: Dominio, item: Item) -> dict:
        """Pedido para un item. Lo comparten el modo en tiempo real y el de lotes."""
        return {
            "model": self.modelo,
            "max_tokens": self.max_tokens,
            # El system es idéntico para todo el dominio: se cachea y los items
            # siguientes pagan ~10 % por esa parte del prompt.
            "system": [{"type": "text", "text": dominio.instrucciones(), "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": dominio.contenido(item)}],
            # Salida estructurada: el JSON siempre respeta el esquema y "ruta"
            # siempre es una hoja válida de la taxonomía (es un enum).
            "output_config": {
                "effort": self.esfuerzo,
                "format": {"type": "json_schema", "schema": dominio.esquema()},
            },
        }

    async def analizar(self, dominio: Dominio, item: Item) -> tuple[dict, str]:
        mensaje = await self.cliente.beta.messages.create(
            **self.parametros(dominio, item),
            betas=[BETA_FALLBACK],
            fallbacks="default",
        )
        return interpretar(dominio, mensaje), mensaje.model

    @staticmethod
    def es_reintentable(error: BaseException) -> bool:
        if isinstance(error, (anthropic.RateLimitError, anthropic.APIConnectionError)):
            return True
        return isinstance(error, anthropic.APIStatusError) and error.status_code >= 500

    @staticmethod
    def es_fatal(error: BaseException) -> bool:
        """Errores que se repetirían en todos los items: credenciales, permisos,
        modelo inexistente. El SDK señala la falta de credenciales con TypeError."""
        return isinstance(
            error, (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError, TypeError)
        )

    @staticmethod
    def pausa_global(error: BaseException) -> float | None:
        """Ante un 429, todos los trabajadores esperan lo que pide la API."""
        if not isinstance(error, anthropic.RateLimitError):
            return None
        try:
            return float(error.response.headers.get("retry-after", "30"))
        except ValueError:
            return 30.0


def id_de_pedido(clave: str) -> str:
    """`custom_id` de la Batches API (máx. 64 caracteres [a-zA-Z0-9_-])."""
    return hashlib.sha256(clave.encode()).hexdigest()[:40]


class ProcesadorPorLotes:
    MAX_BYTES = 200 * 1024 * 1024  # margen bajo el límite de 256 MB por lote

    def __init__(self, analizador: AnalizadorClaude, almacen: Almacen, tam_lote: int = 10_000, intervalo: float = 60.0):
        if not 1 <= tam_lote <= 100_000:
            raise ValueError("tam_lote debe estar entre 1 y 100.000")
        self.analizador = analizador
        self.almacen = almacen
        self.tam_lote = tam_lote
        self.intervalo = intervalo

    @property
    def cliente(self) -> anthropic.AsyncAnthropic:
        return self.analizador.cliente

    def _tandas(self, dominio: Dominio, items: Iterable[Item]) -> Iterator[tuple[list[dict], list[str]]]:
        pedidos: list[dict] = []
        claves: list[str] = []
        bytes_tanda = 0
        for item in items:
            try:
                params = self.analizador.parametros(dominio, item)
            except OSError as error:  # p. ej. una imagen local que no existe: falla ese item, no el lote
                self.almacen.guardar_error(dominio.nombre, item.clave, f"{type(error).__name__}: {error}")
                continue
            pedido = {"custom_id": id_de_pedido(item.clave), "params": params}
            peso = len(json.dumps(pedido, ensure_ascii=False).encode())
            if pedidos and (len(pedidos) >= self.tam_lote or bytes_tanda + peso > self.MAX_BYTES):
                yield pedidos, claves
                pedidos, claves, bytes_tanda = [], [], 0
            pedidos.append(pedido)
            claves.append(item.clave)
            bytes_tanda += peso
        if pedidos:
            yield pedidos, claves

    async def enviar(self, dominio: Dominio, items: Iterable[Item]) -> list[str]:
        ids = []
        for pedidos, claves in self._tandas(dominio, items):
            lote = await self.cliente.messages.batches.create(requests=pedidos)
            # Se registra enseguida: si el proceso se corta, `recoger` lo retoma
            # en la próxima corrida en vez de volver a enviar (y pagar) lo mismo.
            self.almacen.registrar_lote(lote.id, dominio.nombre, len(pedidos))
            self.almacen.marcar(dominio.nombre, claves, "en_lote", lote_id=lote.id)
            ids.append(lote.id)
        return ids

    async def recoger(self, dominio: Dominio) -> dict[str, int]:
        """Espera todos los lotes abiertos del dominio (en paralelo) y guarda los resultados."""
        cuenta = {"listos": 0, "errores": 0, "reencolados": 0}
        lotes = self.almacen.lotes_abiertos(dominio.nombre)
        await asyncio.gather(*(self._recoger_lote(dominio, lote_id, cuenta) for lote_id in lotes))
        return cuenta

    async def _recoger_lote(self, dominio: Dominio, lote_id: str, cuenta: dict[str, int]) -> None:
        while (await self.cliente.messages.batches.retrieve(lote_id)).processing_status != "ended":
            await asyncio.sleep(self.intervalo)
        # Los resultados llegan en cualquier orden: se emparejan por custom_id.
        por_id = {id_de_pedido(it.clave): it for it in self.almacen.items_del_lote(dominio.nombre, lote_id)}
        async for respuesta in await self.cliente.messages.batches.results(lote_id):
            item = por_id.pop(respuesta.custom_id, None)
            if item is None:
                continue  # el item cambió y se reencoló mientras el lote corría
            resultado = respuesta.result
            if resultado.type == "succeeded":
                try:
                    ficha = interpretar(dominio, resultado.message)
                except ErrorDeAnalisis as error:
                    self.almacen.guardar_error(dominio.nombre, item.clave, f"{type(error).__name__}: {error}")
                    cuenta["errores"] += 1
                else:
                    self.almacen.guardar_analisis(dominio.nombre, item.clave, ficha, resultado.message.model)
                    cuenta["listos"] += 1
            elif resultado.type == "errored" and resultado.error.error.type == "invalid_request_error":
                self.almacen.guardar_error(
                    dominio.nombre, item.clave, f"pedido inválido: {resultado.error.error.message}"
                )
                cuenta["errores"] += 1
            else:
                # Error del servidor, cancelado o vencido: vuelve a la cola.
                self.almacen.marcar(dominio.nombre, [item.clave], "pendiente")
                cuenta["reencolados"] += 1
        if por_id:  # sin resultado: también vuelven a la cola
            self.almacen.marcar(dominio.nombre, [it.clave for it in por_id.values()], "pendiente")
            cuenta["reencolados"] += len(por_id)
        self.almacen.cerrar_lote(lote_id)
