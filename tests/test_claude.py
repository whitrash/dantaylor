import asyncio

import anthropic
import httpx2
import pytest

from catalogo.core import pipeline
from catalogo.core.analizador import (
    BETA_FALLBACK,
    MODELO_POR_DEFECTO,
    AnalizadorClaude,
    Rechazo,
    RespuestaIncompleta,
    RespuestaInvalida,
)
from catalogo.core.modelos import Item
from catalogo.core.paralelo import ErrorFatal
from catalogo.dominios import DOMINIOS
from falsos import ClienteFalso, mensaje, responder_simulando
from test_pipeline import hojas, ingerir_ejemplos

ANIMALES = DOMINIOS["animales"]
LEON = Item("animales", "panthera-leo", {"nombre": "León", "nombre_cientifico": "Panthera leo"}, ["wikipedia"])


def error_http(clase, status, headers=None):
    respuesta = httpx2.Response(
        status, headers=headers or {}, request=httpx2.Request("POST", "https://api.anthropic.com")
    )
    return clase(message="x", response=respuesta, body=None)


def test_pedido_con_salida_estructurada_cache_y_fallback():
    cliente = ClienteFalso(responder_simulando(ANIMALES))
    ficha, modelo = asyncio.run(AnalizadorClaude(cliente=cliente).analizar(ANIMALES, LEON))
    assert ficha["ruta"] == "Mamíferos > Felinos" and modelo == MODELO_POR_DEFECTO

    [pedido] = cliente.llamadas
    assert pedido["model"] == "claude-opus-5-5"
    assert pedido["betas"] == [BETA_FALLBACK] and pedido["fallbacks"] == "default"
    assert pedido["output_config"] == {
        "effort": "medium",
        "format": {"type": "json_schema", "schema": ANIMALES.esquema()},
    }
    assert pedido["system"] == [
        {"type": "text", "text": ANIMALES.instrucciones(), "cache_control": {"type": "ephemeral"}}
    ]


@pytest.mark.parametrize(
    "respuesta, error",
    [
        (mensaje(None, stop_reason="refusal"), Rechazo),
        (mensaje({"ruta": "x"}, stop_reason="max_tokens"), RespuestaIncompleta),
        (mensaje(None), RespuestaInvalida),
    ],
)
def test_respuestas_que_no_sirven(respuesta, error):
    cliente = ClienteFalso(lambda params: respuesta)
    with pytest.raises(error):
        asyncio.run(AnalizadorClaude(cliente=cliente).analizar(ANIMALES, LEON))


def test_ruta_fuera_de_taxonomia_es_respuesta_invalida():
    def responder(params):
        ficha = ANIMALES.simular(LEON)
        ficha["ruta"] = "Mamíferos > Dragones"
        return mensaje(ficha)

    with pytest.raises(RespuestaInvalida):
        asyncio.run(AnalizadorClaude(cliente=ClienteFalso(responder)).analizar(ANIMALES, LEON))


def test_que_errores_se_reintentan():
    limite = error_http(anthropic.RateLimitError, 429, {"retry-after": "7"})
    assert AnalizadorClaude.es_reintentable(limite)
    assert AnalizadorClaude.pausa_global(limite) == 7.0
    assert AnalizadorClaude.es_reintentable(error_http(anthropic.InternalServerError, 500))
    assert AnalizadorClaude.es_reintentable(error_http(anthropic.OverloadedError, 529))
    assert not AnalizadorClaude.es_reintentable(error_http(anthropic.BadRequestError, 400))
    assert not AnalizadorClaude.es_reintentable(Rechazo("x"))
    assert AnalizadorClaude.pausa_global(error_http(anthropic.InternalServerError, 500)) is None
    assert AnalizadorClaude.es_fatal(error_http(anthropic.AuthenticationError, 401))
    assert AnalizadorClaude.es_fatal(error_http(anthropic.NotFoundError, 404))  # p. ej. modelo mal escrito
    assert not AnalizadorClaude.es_fatal(error_http(anthropic.BadRequestError, 400))  # puede ser solo ese item
    assert not AnalizadorClaude.es_fatal(Rechazo("x"))


def test_sin_credenciales_corta_la_corrida_y_no_marca_errores(almacen):
    ingerir_ejemplos(almacen, "animales")
    cliente = ClienteFalso(lambda params: error_http(anthropic.AuthenticationError, 401))
    with pytest.raises(ErrorFatal):
        asyncio.run(pipeline.analizar(almacen, [ANIMALES], AnalizadorClaude(cliente=cliente), avisar=lambda m: None))
    assert almacen.errores("animales") == []
    pipeline.preparar(almacen, [ANIMALES])  # lo que estaba en curso vuelve a la cola
    assert almacen.estado("animales")["pendiente"] == 23


def test_tiempo_real_con_reintentos_rechazos_y_misma_especie_con_dos_nombres(almacen, tmp_path):
    ingerir_ejemplos(almacen, "animales")
    llamadas_orca = {"n": 0}

    def ajustes(datos, ficha):
        if datos["nombre"] == "León de montaña":
            ficha["nombre_cientifico"] = "Puma concolor"  # lo que "sabe" el modelo
            ficha["confianza"] = "baja"
        if datos["nombre"] == "Orca":
            llamadas_orca["n"] += 1
            if llamadas_orca["n"] == 1:
                return error_http(anthropic.RateLimitError, 429, {"retry-after": "0"})
        if datos["nombre"] == "Tarántula":
            return mensaje(None, stop_reason="refusal")
        return None

    analizador = AnalizadorClaude(cliente=ClienteFalso(responder_simulando(ANIMALES, ajustes)))
    resultado = asyncio.run(
        pipeline.analizar(almacen, [ANIMALES], analizador, modo="tiempo-real", avisar=lambda m: None)
    )
    assert resultado["reintentos"] == 1
    assert resultado["dominios"]["animales"] == {"listos": 22, "errores": 1}
    assert almacen.errores("animales")[0][1].startswith("Rechazo")

    # "Puma" y "León de montaña" entraron como dos filas, pero son la misma especie:
    # en el catálogo queda una sola ficha (la de mejor confianza) con el otro como alias.
    catalogo, _ = pipeline.catalogar(almacen, ANIMALES, tmp_path)
    assert hojas(catalogo)["Mamíferos > Felinos"] == [
        "Jaguar (Panthera onca)",
        "León (Panthera leo)",
        "Puma (Puma concolor)",
    ]
    felinos = catalogo["secciones"][0]["secciones"][0]
    [puma] = [f for f in felinos["items"] if f["clave"] == "puma-concolor"]
    assert puma["alias"] == ["leon-de-montana"]
    assert puma["fuentes"] == ["wikipedia"]
