"""Dobles de prueba: un cliente de Claude falso (tiempo real + Batches) sin red."""

from __future__ import annotations

import json
from types import SimpleNamespace

from catalogo.core.modelos import Item

PREFIJO = "Registro a catalogar:\n"


def datos_del_pedido(params: dict) -> dict:
    texto = params["messages"][0]["content"][-1]["text"]
    assert texto.startswith(PREFIJO)
    return json.loads(texto[len(PREFIJO) :])


def mensaje(ficha: dict | None = None, stop_reason: str = "end_turn", model: str = "claude-opus-5-5"):
    contenido = [] if ficha is None else [SimpleNamespace(type="text", text=json.dumps(ficha, ensure_ascii=False))]
    return SimpleNamespace(stop_reason=stop_reason, content=contenido, model=model, stop_details=None)


def responder_simulando(dominio, ajustes=None):
    """Responde como Claude, con la ficha simulada del dominio; `ajustes(datos, ficha)` la modifica."""

    def responder(params: dict):
        datos = datos_del_pedido(params)
        ficha = dominio.simular(Item(dominio.nombre, "x", datos))
        if ajustes:
            resultado = ajustes(datos, ficha)
            if resultado is not None:
                return resultado
        return mensaje(ficha)

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
