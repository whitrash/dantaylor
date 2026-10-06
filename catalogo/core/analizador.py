"""Backends de análisis.

- `AnalizadorSimulado`: sin red ni costo. Prueba la logística de punta a punta.
- `AnalizadorClaude`: API de Claude, una llamada por item, muchas en paralelo.
  Con `con_web=True` el modelo puede buscar en la web (herramientas del servidor).
- `ProcesadorPorLotes`: Message Batches API. Hasta 100.000 items por lote, 50 %
  más barato en tokens, resultados en menos de 24 h. Para volumen no urgente.
- `AnalizadorClaudeCode`: lanza `claude -p` (Claude Code instalado en la
  computadora) como subproceso, varios a la vez. Usa la cuenta con la que ya
  se entra; no hace falta clave de API. Sin lotes ni control de caché.

Todos devuelven `(ficha, modelo, metricas)`; la ficha ya validada contra el
esquema del dominio; `metricas` trae segundos, tokens, búsquedas y costo.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Awaitable, Callable, Iterable, Iterator

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
HERRAMIENTA_FICHA = "entregar_ficha"
MAX_PAUSAS = 6  # veces que se continúa un turno pausado por búsquedas largas

# USD por millón de tokens: entrada, salida, lectura de caché, escritura de caché (5 min).
# Prefijos: gana el más largo que coincida con el id del modelo.
PRECIOS = {
    "claude-opus-5-5": (4.0, 20.0, 0.20, 5.0),
    "claude-opus-5": (5.0, 25.0, 0.50, 6.25),
    "claude-opus-4": (5.0, 25.0, 0.50, 6.25),
    "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5),
    "claude-sonnet-5": (2.0, 10.0, 0.20, 2.5),
    "claude-sonnet-4": (3.0, 15.0, 0.30, 3.75),
    "claude-haiku-4-5": (1.0, 5.0, 0.10, 1.25),
    "claude-fable-5-1": (10.0, 50.0, 0.25, 12.5),
    "claude-fable-5": (10.0, 50.0, 1.0, 12.5),
}
PRECIO_BUSQUEDA = 0.01  # USD por búsqueda web


class ErrorDeAnalisis(Exception):
    """Falla propia del item (no de la red): reintentarlo igual no sirve."""


class Rechazo(ErrorDeAnalisis):
    pass


class RespuestaIncompleta(ErrorDeAnalisis):
    pass


class RespuestaInvalida(ErrorDeAnalisis):
    pass


class LimiteDeUso(Exception):
    """La cuenta o la API piden esperar: se reintenta y se frena a todos."""


class ErrorCredenciales(Exception):
    """Sin sesión ni clave: se repetiría en todos los items."""


def costo_estimado(modelo: str | None, uso: dict, lote: bool = False) -> float | None:
    """Costo en USD según la tabla de precios; None si el modelo no está en la tabla."""
    precios = None
    for prefijo in sorted(PRECIOS, key=len, reverse=True):
        if modelo and modelo.startswith(prefijo):
            precios = PRECIOS[prefijo]
            break
    if precios is None:
        return None
    entrada, salida, lectura, escritura = precios
    factor = 0.5 if lote else 1.0
    tokens = (
        (uso.get("input_tokens") or 0) * entrada
        + (uso.get("output_tokens") or 0) * salida
        + (uso.get("cache_read_input_tokens") or 0) * lectura
        + (uso.get("cache_creation_input_tokens") or 0) * escritura
    ) / 1_000_000
    return round(tokens * factor + (uso.get("web_search_requests") or 0) * PRECIO_BUSQUEDA, 6)


def _uso(mensaje) -> dict:
    uso = getattr(mensaje, "usage", None)
    if uso is None:
        return {}
    servidor = getattr(uso, "server_tool_use", None)
    return {
        "input_tokens": getattr(uso, "input_tokens", 0) or 0,
        "output_tokens": getattr(uso, "output_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(uso, "cache_read_input_tokens", 0) or 0,
        "cache_creation_input_tokens": getattr(uso, "cache_creation_input_tokens", 0) or 0,
        "web_search_requests": getattr(servidor, "web_search_requests", 0) or 0,
    }


def metricas_de(mensaje, segundos: float, lote: bool = False) -> dict:
    uso = _uso(mensaje)
    return {
        "segundos": round(segundos, 2),
        "tokens_entrada": uso.get("input_tokens", 0) + uso.get("cache_read_input_tokens", 0),
        "tokens_salida": uso.get("output_tokens", 0),
        "busquedas": uso.get("web_search_requests", 0),
        "costo_usd": costo_estimado(getattr(mensaje, "model", None), uso, lote),
    }


def interpretar(dominio: Dominio, mensaje) -> dict:
    if mensaje.stop_reason == "refusal":
        detalle = getattr(mensaje, "stop_details", None)
        raise Rechazo(f"el modelo rechazó el item (categoría: {getattr(detalle, 'category', None)})")
    if mensaje.stop_reason == "max_tokens":
        raise RespuestaIncompleta("la respuesta se cortó por max_tokens")
    if mensaje.stop_reason == "pause_turn":
        raise RespuestaIncompleta("el turno quedó pausado (búsquedas largas); reintentar en tiempo real")
    # Con web, la ficha llega como llamada a la herramienta `entregar_ficha`
    # (esquema estricto); sin web, como texto JSON con salida estructurada.
    for bloque in mensaje.content:
        if bloque.type == "tool_use" and bloque.name == HERRAMIENTA_FICHA:
            try:
                return dominio.validar(dict(bloque.input))
            except ValueError as error:
                raise RespuestaInvalida(str(error)) from error
    texto = next((b.text for b in reversed(mensaje.content) if b.type == "text"), None)
    if texto is None:
        raise RespuestaInvalida("la respuesta no trae ficha ni texto")
    try:
        return dominio.validar(json.loads(_sin_cerco(texto)))
    except ValueError as error:  # incluye json.JSONDecodeError
        raise RespuestaInvalida(str(error)) from error


def _sin_cerco(texto: str) -> str:
    """Quita un cerco ```json ... ``` si el modelo lo puso."""
    texto = texto.strip()
    if texto.startswith("```"):
        texto = re.sub(r"^```[a-zA-Z]*\s*", "", texto)
        texto = re.sub(r"\s*```$", "", texto)
    return texto


class AnalizadorSimulado:
    nombre = "simulado"
    modelo = "simulado"

    def __init__(self, latencia: float = 0.0):
        self.latencia = latencia

    async def analizar(self, dominio: Dominio, item: Item, con_web: bool = False) -> tuple[dict, str, dict]:
        inicio = time.monotonic()
        if self.latencia:
            await asyncio.sleep(self.latencia)
        metricas = {
            "segundos": round(time.monotonic() - inicio, 3),
            "tokens_entrada": 0,
            "tokens_salida": 0,
            "busquedas": 1 if con_web else 0,
            "costo_usd": 0.0,
        }
        return dominio.validar(dominio.simular(item)), self.modelo, metricas

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
    nombre = "api"

    def __init__(
        self,
        modelo: str | None = None,
        esfuerzo: str = "medium",
        max_tokens: int = 16000,
        cliente: anthropic.AsyncAnthropic | None = None,
    ):
        self.modelo = modelo or MODELO_POR_DEFECTO
        self.esfuerzo = esfuerzo
        self.max_tokens = max_tokens
        self.cliente = cliente or anthropic.AsyncAnthropic()

    def parametros(self, dominio: Dominio, item: Item, con_web: bool = False) -> dict:
        """Pedido para un item. Lo comparten el modo en tiempo real y el de lotes.

        Todo lo que va antes del registro (system, tools) es idéntico para todo
        el dominio: así la caché de prompts sirve para cada item siguiente."""
        pedido = {
            "model": self.modelo,
            "max_tokens": self.max_tokens,
            "system": [
                {"type": "text", "text": dominio.instrucciones(con_web), "cache_control": {"type": "ephemeral"}}
            ],
            "messages": [{"role": "user", "content": dominio.contenido(item)}],
            "output_config": {"effort": self.esfuerzo},
        }
        if con_web:
            # Herramientas fijas por dominio (nada por item, o se pierde la caché).
            # La ficha vuelve por `entregar_ficha` con esquema estricto.
            pedido["tools"] = [
                {"type": "web_search_20260209", "name": "web_search", "max_uses": dominio.max_busquedas},
                {
                    "type": "web_fetch_20260209",
                    "name": "web_fetch",
                    "max_uses": dominio.max_busquedas,
                    "max_content_tokens": 20000,
                },
                dominio.herramienta_ficha(),
            ]
        else:
            # Salida estructurada: el JSON siempre respeta el esquema y "ruta"
            # siempre es una hoja válida de la taxonomía (es un enum).
            pedido["output_config"]["format"] = {"type": "json_schema", "schema": dominio.esquema()}
        return pedido

    async def analizar(self, dominio: Dominio, item: Item, con_web: bool = False) -> tuple[dict, str, dict]:
        inicio = time.monotonic()
        pedido = self.parametros(dominio, item, con_web)
        uso_total: dict[str, int] = {}
        for _ in range(MAX_PAUSAS + 1):
            mensaje = await self.cliente.beta.messages.create(**pedido, betas=[BETA_FALLBACK], fallbacks="default")
            for clave, valor in _uso(mensaje).items():
                uso_total[clave] = uso_total.get(clave, 0) + valor
            if mensaje.stop_reason != "pause_turn":
                break
            # La API pausó un turno largo de búsquedas: se reenvía tal cual para que siga.
            pedido["messages"] = pedido["messages"] + [{"role": "assistant", "content": mensaje.content}]
        ficha = interpretar(dominio, mensaje)
        segundos = time.monotonic() - inicio
        metricas = {
            "segundos": round(segundos, 2),
            "tokens_entrada": uso_total.get("input_tokens", 0) + uso_total.get("cache_read_input_tokens", 0),
            "tokens_salida": uso_total.get("output_tokens", 0),
            "busquedas": uso_total.get("web_search_requests", 0),
            "costo_usd": costo_estimado(mensaje.model, uso_total),
        }
        return ficha, mensaje.model, metricas

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

    def __init__(
        self,
        analizador: AnalizadorClaude,
        almacen: Almacen,
        tam_lote: int = 10_000,
        intervalo: float = 60.0,
        web: bool = True,
    ):
        if not 1 <= tam_lote <= 100_000:
            raise ValueError("tam_lote debe estar entre 1 y 100.000")
        self.analizador = analizador
        self.almacen = almacen
        self.tam_lote = tam_lote
        self.intervalo = intervalo
        self.web = web  # False = las fichas son finales aunque el dominio pida segunda pasada

    @property
    def cliente(self) -> anthropic.AsyncAnthropic:
        return self.analizador.cliente

    def _tandas(self, dominio: Dominio, items: Iterable[Item], con_web: bool) -> Iterator[tuple[list[dict], list[str]]]:
        pedidos: list[dict] = []
        claves: list[str] = []
        bytes_tanda = 0
        for item in items:
            try:
                params = self.analizador.parametros(dominio, item, con_web)
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

    async def enviar(self, dominio: Dominio, items: Iterable[Item], con_web: bool = False) -> list[str]:
        ids = []
        for pedidos, claves in self._tandas(dominio, items, con_web):
            lote = await self.cliente.messages.batches.create(requests=pedidos)
            # Se registra enseguida: si el proceso se corta, `recoger` lo retoma
            # en la próxima corrida en vez de volver a enviar (y pagar) lo mismo.
            self.almacen.registrar_lote(lote.id, dominio.nombre, len(pedidos), con_web)
            self.almacen.marcar(dominio.nombre, claves, "en_lote", lote_id=lote.id)
            ids.append(lote.id)
        return ids

    async def recoger(
        self, dominio: Dominio, al_guardar: Callable[[str, str, str, dict | None], None] | None = None
    ) -> dict[str, int]:
        """Espera todos los lotes abiertos del dominio (en paralelo) y guarda los resultados."""
        cuenta = {"listos": 0, "verificar": 0, "errores": 0, "reencolados": 0}
        lotes = self.almacen.lotes_abiertos(dominio.nombre)
        await asyncio.gather(*(self._recoger_lote(dominio, lote_id, cuenta, al_guardar) for lote_id in lotes))
        return cuenta

    async def _recoger_lote(self, dominio: Dominio, lote_id: str, cuenta: dict[str, int], al_guardar) -> None:
        while (await self.cliente.messages.batches.retrieve(lote_id)).processing_status != "ended":
            await asyncio.sleep(self.intervalo)
        con_web = bool(self.almacen.lote(lote_id)["con_web"])
        # Los resultados llegan en cualquier orden: se emparejan por custom_id.
        por_id = {id_de_pedido(it.clave): it for it in self.almacen.items_del_lote(dominio.nombre, lote_id)}
        async for respuesta in await self.cliente.messages.batches.results(lote_id):
            item = por_id.pop(respuesta.custom_id, None)
            if item is None:
                continue  # el item cambió y se reencoló mientras el lote corría
            resultado = respuesta.result
            if resultado.type == "succeeded":
                mensaje = resultado.message
                if mensaje.stop_reason == "pause_turn":
                    # Un turno pausado no se puede continuar dentro del lote: vuelve a la cola.
                    self.almacen.marcar(dominio.nombre, [item.clave], "pendiente")
                    cuenta["reencolados"] += 1
                    continue
                try:
                    ficha = interpretar(dominio, mensaje)
                except ErrorDeAnalisis as error:
                    self.almacen.guardar_error(dominio.nombre, item.clave, f"{type(error).__name__}: {error}")
                    cuenta["errores"] += 1
                    if al_guardar:
                        al_guardar(dominio.nombre, item.clave, "error", None)
                else:
                    estado = dominio.estado_tras_analisis(ficha, con_web) if self.web else "listo"
                    metricas = metricas_de(mensaje, 0.0, lote=True)
                    self.almacen.guardar_analisis(
                        dominio.nombre, item.clave, ficha, mensaje.model, metricas, estado=estado, con_web=con_web
                    )
                    cuenta["listos" if estado == "listo" else "verificar"] += 1
                    if al_guardar:
                        al_guardar(dominio.nombre, item.clave, estado, metricas)
            elif resultado.type == "errored" and resultado.error.error.type == "invalid_request_error":
                self.almacen.guardar_error(
                    dominio.nombre, item.clave, f"pedido inválido: {resultado.error.error.message}"
                )
                cuenta["errores"] += 1
                if al_guardar:
                    al_guardar(dominio.nombre, item.clave, "error", None)
            else:
                # Error del servidor, cancelado o vencido: vuelve a la cola.
                self.almacen.marcar(dominio.nombre, [item.clave], "pendiente")
                cuenta["reencolados"] += 1
        if por_id:  # sin resultado: también vuelven a la cola
            self.almacen.marcar(dominio.nombre, [it.clave for it in por_id.values()], "pendiente")
            cuenta["reencolados"] += len(por_id)
        self.almacen.cerrar_lote(lote_id)


# --- Claude Code (claude -p) -------------------------------------------------

Ejecutor = Callable[[list[str], str | None, float], Awaitable[tuple[int, str, str]]]

_SENAL_LIMITE = re.compile(r"rate.?limit|usage limit|limit reached|too many requests|overloaded|capacity|\b429\b", re.I)
_SENAL_CREDENCIALES = re.compile(
    r"not logged in|log ?in|authentication|invalid api key|credential|unauthorized|\b401\b", re.I
)


async def _ejecutar_subproceso(comando: list[str], carpeta: str | None, timeout: float) -> tuple[int, str, str]:
    proceso = await asyncio.create_subprocess_exec(
        *comando,
        cwd=carpeta,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.DEVNULL,
    )
    try:
        salida, errores = await asyncio.wait_for(proceso.communicate(), timeout)
    except asyncio.TimeoutError:
        proceso.kill()
        await proceso.wait()
        raise
    return proceso.returncode or 0, salida.decode(errors="replace"), errores.decode(errors="replace")


class AnalizadorClaudeCode:
    """Un `claude -p` por item, con salida validada contra el esquema del dominio.

    Usa la sesión de Claude Code de la computadora (cuenta o clave, lo que haya).
    Las herramientas se limitan a WebSearch/WebFetch (y Read si hay imagen local):
    nada de Bash ni edición de archivos. Corre desde una carpeta vacía dedicada
    para no cargar CLAUDE.md, hooks ni MCP de ningún proyecto.
    """

    nombre = "claude-code"

    def __init__(
        self,
        modelo: str | None = None,
        esfuerzo: str = "medium",
        max_turnos: int = 12,
        max_costo_item: float = 0.5,
        timeout: float = 600.0,
        ejecutable: str = "claude",
        carpeta: str | None = None,
        ejecutar: Ejecutor | None = None,
    ):
        self.modelo = modelo
        self.esfuerzo = esfuerzo
        self.max_turnos = max_turnos
        self.max_costo_item = max_costo_item
        self.timeout = timeout
        self.ejecutable = ejecutable
        self.carpeta = carpeta or tempfile.mkdtemp(prefix="catalogo-claude-")
        self.ejecutar = ejecutar or _ejecutar_subproceso
        self._archivos_sistema: dict[tuple[str, bool], str] = {}

    def _archivo_sistema(self, dominio: Dominio, con_web: bool) -> str:
        clave = (dominio.nombre, con_web)
        if clave not in self._archivos_sistema:
            ruta = Path(self.carpeta) / f"sistema-{dominio.nombre}-{'web' if con_web else 'sin-web'}.txt"
            ruta.write_text(dominio.instrucciones(con_web), encoding="utf-8")
            self._archivos_sistema[clave] = str(ruta)
        return self._archivos_sistema[clave]

    def comando(self, dominio: Dominio, item: Item, con_web: bool = False) -> list[str]:
        herramientas = ["WebSearch", "WebFetch"] if con_web else []
        prompt = dominio.contenido_texto(item)
        if item.datos.get("imagen_archivo"):
            herramientas.append("Read")
            prompt += f"\n\nImagen del registro (leela con Read): {os.path.abspath(item.datos['imagen_archivo'])}"
        lista = ",".join(herramientas)
        comando = [
            self.ejecutable,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--json-schema",
            json.dumps(dominio.esquema(), ensure_ascii=False),
            "--system-prompt-file",
            self._archivo_sistema(dominio, con_web),
            "--tools",
            lista,
            "--allowedTools",
            lista,
            "--permission-prompts",
            "none",
            "--max-turns",
            str(self.max_turnos),
            "--max-budget-usd",
            f"{self.max_costo_item:.2f}",
            "--no-session-persistence",
            "--effort",
            self.esfuerzo,
        ]
        if self.modelo:
            comando += ["--model", self.modelo]
        return comando

    async def analizar(self, dominio: Dominio, item: Item, con_web: bool = False) -> tuple[dict, str, dict]:
        inicio = time.monotonic()
        codigo, salida, errores = await self.ejecutar(self.comando(dominio, item, con_web), self.carpeta, self.timeout)
        resultado = _ultimo_json(salida)
        texto = " ".join(str(x) for x in (resultado.get("result", ""), errores) if x)
        if codigo != 0 or resultado.get("is_error"):
            if _SENAL_CREDENCIALES.search(texto):
                raise ErrorCredenciales(texto.strip()[:300])
            if _SENAL_LIMITE.search(texto):
                raise LimiteDeUso(texto.strip()[:300])
            subtipo = resultado.get("subtype", "")
            if subtipo in ("error_max_turns", "error_max_budget_usd"):
                raise RespuestaIncompleta(f"{subtipo}: el item no terminó dentro del tope")
            raise ErrorDeAnalisis(
                f"claude -p falló (código {codigo}, {subtipo or 'sin detalle'}): {texto.strip()[:300]}"
            )
        ficha = resultado.get("structured_output")
        if ficha is None:
            try:
                ficha = json.loads(_sin_cerco(str(resultado.get("result", ""))))
            except ValueError as error:
                raise RespuestaInvalida("la respuesta no trae structured_output ni JSON") from error
        try:
            ficha = dominio.validar(ficha)
        except ValueError as error:
            raise RespuestaInvalida(str(error)) from error
        uso = resultado.get("usage") or {}
        servidor = uso.get("server_tool_use") or {}
        modelos = list((resultado.get("modelUsage") or {}).keys())
        metricas = {
            "segundos": round((resultado.get("duration_ms") or (time.monotonic() - inicio) * 1000) / 1000, 2),
            "tokens_entrada": (uso.get("input_tokens") or 0) + (uso.get("cache_read_input_tokens") or 0),
            "tokens_salida": uso.get("output_tokens") or 0,
            # Claude Code no refleja sus búsquedas en server_tool_use (verificado: 0 con
            # fuentes citadas); se toman las fuentes de la ficha como aproximación.
            "busquedas": servidor.get("web_search_requests") or len(set(ficha.get("fuentes_web") or [])),
            "costo_usd": resultado.get("total_cost_usd"),
        }
        return ficha, modelos[0] if modelos else (self.modelo or "claude-code"), metricas

    @staticmethod
    def es_reintentable(error: BaseException) -> bool:
        return isinstance(error, (LimiteDeUso, asyncio.TimeoutError))

    @staticmethod
    def es_fatal(error: BaseException) -> bool:
        return isinstance(error, (ErrorCredenciales, FileNotFoundError))

    @staticmethod
    def pausa_global(error: BaseException) -> float | None:
        return 60.0 if isinstance(error, LimiteDeUso) else None

    @staticmethod
    def disponible(ejecutable: str = "claude") -> bool:
        return shutil.which(ejecutable) is not None


def _ultimo_json(salida: str) -> dict:
    """`--output-format json` imprime un objeto; si algo más se coló en stdout, se toma el último objeto."""
    for linea in reversed(salida.strip().splitlines()):
        linea = linea.strip()
        if linea.startswith("{"):
            try:
                return json.loads(linea)
            except ValueError:
                continue
    try:
        return json.loads(salida)
    except ValueError:
        return {}
