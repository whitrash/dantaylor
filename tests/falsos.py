"""Dobles de prueba: un cliente de Claude falso (tiempo real + Batches) y un
ejecutor falso de `claude -p`, sin red."""

from __future__ import annotations

import json
from types import SimpleNamespace

from catalogo.core.modelos import Item

PREFIJO = "Registro a catalogar:\n"


def datos_del_pedido(params: dict) -> dict:
    texto = params["messages"][0]["content"][-1]["text"]
    assert texto.startswith(PREFIJO)
    return json.loads(texto[len(PREFIJO) :])


def uso(busquedas: int = 0):
    return SimpleNamespace(
        input_tokens=1200,
        output_tokens=800,
        cache_read_input_tokens=3000,
        cache_creation_input_tokens=0,
        server_tool_use=SimpleNamespace(web_search_requests=busquedas),
    )


def mensaje(
    ficha: dict | None = None,
    stop_reason: str = "end_turn",
    model: str = "claude-opus-5-5",
    herramienta: bool = False,
    busquedas: int | None = None,
):
    """Respuesta de la API. Con `herramienta=True` la ficha viene como llamada a
    `entregar_ficha` (así responde el modelo cuando tiene búsqueda web)."""
    if ficha is None:
        contenido = []
    elif herramienta:
        contenido = [SimpleNamespace(type="tool_use", id="toolu_1", name="entregar_ficha", input=ficha)]
        stop_reason = "tool_use" if stop_reason == "end_turn" else stop_reason
    else:
        contenido = [SimpleNamespace(type="text", text=json.dumps(ficha, ensure_ascii=False))]
    if busquedas is None:
        busquedas = 2 if herramienta else 0
    return SimpleNamespace(
        stop_reason=stop_reason, content=contenido, model=model, stop_details=None, usage=uso(busquedas)
    )


def responder_simulando(dominio, ajustes=None):
    """Responde como Claude, con la ficha simulada del dominio; `ajustes(datos, ficha)`
    la modifica o devuelve otra respuesta. Si el pedido trae herramientas (web),
    la ficha vuelve por `entregar_ficha`."""

    def responder(params: dict):
        datos = datos_del_pedido(params)
        ficha = dominio.simular(Item(dominio.nombre, "x", datos))
        if ajustes:
            resultado = ajustes(datos, ficha)
            if resultado is not None:
                return resultado
        return mensaje(ficha, herramienta="tools" in params)

    return responder


class LotesFalsos:
    def __init__(self, responder, resultado_lote=None, consultas_hasta_terminar: int = 2):
        self.responder = responder
        self.resultado_lote = resultado_lote
        self.lotes: dict[str, list[dict]] = {}
        self.consultas: dict[str, int] = {}
        self.consultas_hasta_terminar = consultas_hasta_terminar

    async def create(self, requests):
        lote_id = f"msgbatch_{len(self.lotes) + 1}"
        self.lotes[lote_id] = list(requests)
        return SimpleNamespace(id=lote_id, processing_status="in_progress")

    async def retrieve(self, lote_id):
        self.consultas[lote_id] = self.consultas.get(lote_id, 0) + 1
        terminado = self.consultas[lote_id] >= self.consultas_hasta_terminar
        return SimpleNamespace(id=lote_id, processing_status="ended" if terminado else "in_progress")

    async def results(self, lote_id):
        pedidos = self.lotes[lote_id]

        async def generar():
            for pedido in reversed(pedidos):  # en otro orden, como la API real
                if self.resultado_lote:
                    resultado = self.resultado_lote(pedido)
                else:
                    resultado = SimpleNamespace(type="succeeded", message=self.responder(pedido["params"]))
                yield SimpleNamespace(custom_id=pedido["custom_id"], result=resultado)

        return generar()


class ClienteFalso:
    def __init__(self, responder, **opciones_lotes):
        self.responder = responder
        self.llamadas: list[dict] = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(create=self._crear))
        self.messages = SimpleNamespace(batches=LotesFalsos(responder, **opciones_lotes))

    async def _crear(self, **kwargs):
        self.llamadas.append(kwargs)
        respuesta = self.responder(kwargs)
        if isinstance(respuesta, BaseException):
            raise respuesta
        return respuesta


# --- claude -p ----------------------------------------------------------------


def resultado_cli(ficha: dict | None, costo: float = 0.03, busquedas: int = 0, **extra) -> dict:
    """Lo que imprime `claude -p --output-format json` (campos reales, recortados)."""
    base = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "duration_ms": 12000,
        "num_turns": 3,
        "result": "",
        "session_id": "sesion-falsa",
        "total_cost_usd": costo,
        "usage": {
            "input_tokens": 100,
            "output_tokens": 500,
            "cache_read_input_tokens": 2000,
            "cache_creation_input_tokens": 0,
            "server_tool_use": {"web_search_requests": busquedas, "web_fetch_requests": 0},
        },
        "modelUsage": {"claude-opus-5-5": {"costUSD": costo}},
        "permission_denials": [],
    }
    if ficha is not None:
        base["structured_output"] = ficha
    base.update(extra)
    return base


def prompt_del_comando(comando: list[str]) -> dict:
    texto = comando[comando.index("-p") + 1]
    return json.loads(texto[len(PREFIJO) :].split("\n\nImagen")[0])


def opcion(comando: list[str], nombre: str) -> str | None:
    return comando[comando.index(nombre) + 1] if nombre in comando else None


class EjecutorFalso:
    """Reemplaza al subproceso: `responder(comando)` devuelve un dict (resultado
    JSON), una tupla (codigo, stdout, stderr) o una excepción."""

    def __init__(self, responder):
        self.responder = responder
        self.comandos: list[list[str]] = []

    async def __call__(self, comando: list[str], carpeta: str | None, timeout: float):
        self.comandos.append(comando)
        respuesta = self.responder(comando)
        if isinstance(respuesta, BaseException):
            raise respuesta
        if isinstance(respuesta, dict):
            return (1 if respuesta.get("is_error") else 0), json.dumps(respuesta), ""
        return respuesta


def responder_cli_simulando(dominio, ajustes=None):
    def responder(comando):
        datos = prompt_del_comando(comando)
        ficha = dominio.simular(Item(dominio.nombre, "x", datos))
        con_web = bool(opcion(comando, "--tools"))
        if ajustes:
            resultado = ajustes(datos, ficha, con_web)
            if resultado is not None:
                return resultado
        return resultado_cli(ficha, busquedas=2 if con_web else 0)

    return responder
