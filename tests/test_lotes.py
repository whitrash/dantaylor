import asyncio
from types import SimpleNamespace

import pytest

from catalogo.core import pipeline
from catalogo.core.analizador import AnalizadorClaude, ProcesadorPorLotes, id_de_pedido
from catalogo.core.paralelo import ErrorFatal
from catalogo.dominios import DOMINIOS
from falsos import ClienteFalso, datos_del_pedido, mensaje, responder_simulando
from test_pipeline import ingerir_ejemplos

ANIMALES = DOMINIOS["animales"]


def procesador(almacen, cliente, tam_lote=10):
    return ProcesadorPorLotes(AnalizadorClaude(cliente=cliente), almacen, tam_lote=tam_lote, intervalo=0)


def test_id_de_pedido_cumple_el_formato_de_la_api():
    custom_id = id_de_pedido("León de montaña / ñandú ¿?")
    assert len(custom_id) <= 64 and custom_id.isalnum()
    assert id_de_pedido("a") == id_de_pedido("a") != id_de_pedido("b")


def test_envia_en_tandas_y_recoge_resultados_desordenados(almacen):
    ingerir_ejemplos(almacen, "animales")
    cliente = ClienteFalso(responder_simulando(ANIMALES))
    lotes = procesador(almacen, cliente)

    ids = asyncio.run(lotes.enviar(ANIMALES, almacen.pendientes("animales")))
    assert len(ids) == 3  # 23 items en tandas de 10
    assert [len(cliente.messages.batches.lotes[i]) for i in ids] == [10, 10, 3]
    assert almacen.estado("animales")["en_lote"] == 23
    pedido = cliente.messages.batches.lotes[ids[0]][0]
    assert "fallbacks" not in pedido["params"]  # la Batches API no lo acepta

    cuenta = asyncio.run(lotes.recoger(ANIMALES))
    assert cuenta == {"listos": 23, "errores": 0, "reencolados": 0}
    assert almacen.estado("animales")["listo"] == 23
    assert almacen.lotes_abiertos("animales") == []


def test_retoma_lotes_de_una_corrida_anterior_sin_reenviar(almacen):
    ingerir_ejemplos(almacen, "animales")
    cliente = ClienteFalso(responder_simulando(ANIMALES))
    asyncio.run(procesador(almacen, cliente).enviar(ANIMALES, almacen.pendientes("animales")))
    enviados = len(cliente.messages.batches.lotes)

    # "Otra corrida": un procesador nuevo que solo sabe lo que dice el almacén.
    cuenta = asyncio.run(procesador(almacen, cliente).recoger(ANIMALES))
    assert cuenta["listos"] == 23
    assert len(cliente.messages.batches.lotes) == enviados


def test_cada_tipo_de_resultado_va_a_su_estado(almacen):
    ingerir_ejemplos(almacen, "animales")
    responder = responder_simulando(ANIMALES)

    def resultado_lote(pedido):
        nombre = datos_del_pedido(pedido["params"])["nombre"]
        if nombre == "Tarántula":
            return SimpleNamespace(type="succeeded", message=mensaje(None, stop_reason="refusal"))
        if nombre == "Orca":
            error = SimpleNamespace(type="invalid_request_error", message="imagen inaccesible")
            return SimpleNamespace(type="errored", error=SimpleNamespace(type="error", error=error))
        if nombre == "Ajolote":
            error = SimpleNamespace(type="overloaded_error", message="ocupado")
            return SimpleNamespace(type="errored", error=SimpleNamespace(type="error", error=error))
        if nombre == "Hornero":
            return SimpleNamespace(type="expired")
        return SimpleNamespace(type="succeeded", message=responder(pedido["params"]))

    cliente = ClienteFalso(responder, resultado_lote=resultado_lote)
    lotes = procesador(almacen, cliente, tam_lote=100)
    asyncio.run(lotes.enviar(ANIMALES, almacen.pendientes("animales")))
    cuenta = asyncio.run(lotes.recoger(ANIMALES))

    assert cuenta == {"listos": 19, "errores": 2, "reencolados": 2}
    errores = dict(almacen.errores("animales"))
    assert errores["orcinus-orca"] == "pedido inválido: imagen inaccesible"
    assert errores["tarantula"].startswith("Rechazo")
    assert {i.clave for i in almacen.pendientes("animales")} == {"ambystoma-mexicanum", "furnarius-rufus"}


def test_item_que_cambia_mientras_esta_en_un_lote_se_reanaliza(almacen):
    ingerir_ejemplos(almacen, "animales")
    cliente = ClienteFalso(responder_simulando(ANIMALES))
    lotes = procesador(almacen, cliente, tam_lote=100)
    asyncio.run(lotes.enviar(ANIMALES, almacen.pendientes("animales")))

    nuevo = [{"nombre": "León", "nombre_cientifico": "Panthera leo", "notas": "dato corregido"}]
    pipeline.ingerir(almacen, ANIMALES, nuevo, "wikipedia")

    cuenta = asyncio.run(lotes.recoger(ANIMALES))
    assert cuenta["listos"] == 22
    assert [i.clave for i in almacen.pendientes("animales")] == ["panthera-leo"]


def test_modo_auto_elige_lotes_con_mucho_volumen(almacen):
    ingerir_ejemplos(almacen, "animales", "comercios")
    cliente = ClienteFalso(responder_simulando(ANIMALES))
    cliente.messages.batches.responder = lambda params: _responder_por_dominio(params)
    resultado = asyncio.run(
        pipeline.analizar(
            almacen,
            [ANIMALES, DOMINIOS["comercios"]],
            AnalizadorClaude(cliente=cliente),
            modo="auto",
            umbral_lotes=30,
            intervalo_lotes=0,
            avisar=lambda m: None,
        )
    )
    assert resultado["modo"] == "lotes"
    assert resultado["dominios"]["animales"]["listos"] == 23
    assert resultado["dominios"]["comercios"]["listos"] == 13
    assert cliente.llamadas == []  # nada en tiempo real


def test_modo_auto_usa_tiempo_real_con_poco_volumen(almacen):
    ingerir_ejemplos(almacen, "curiosidades")
    cliente = ClienteFalso(responder_simulando(DOMINIOS["curiosidades"]))
    resultado = asyncio.run(
        pipeline.analizar(almacen, [DOMINIOS["curiosidades"]], AnalizadorClaude(cliente=cliente), avisar=lambda m: None)
    )
    assert resultado["modo"] == "tiempo-real" and len(cliente.llamadas) == 13


def test_enviar_sin_esperar_y_recoger_despues(almacen):
    ingerir_ejemplos(almacen, "curiosidades")
    dominio = DOMINIOS["curiosidades"]
    cliente = ClienteFalso(responder_simulando(dominio))
    analizador = AnalizadorClaude(cliente=cliente)
    resultado = asyncio.run(
        pipeline.analizar(almacen, [dominio], analizador, modo="lotes", esperar_lotes=False, avisar=lambda m: None)
    )
    assert resultado["dominios"]["curiosidades"] == {"enviados": 13}
    assert almacen.estado("curiosidades")["en_lote"] == 13

    cuentas = asyncio.run(pipeline.recoger_lotes(almacen, [dominio], analizador, intervalo=0))
    assert cuentas["curiosidades"]["listos"] == 13


def test_imagen_local_inexistente_falla_solo_ese_item(almacen):
    ingerir_ejemplos(almacen, "animales")
    pipeline.ingerir(almacen, ANIMALES, [{"nombre": "Lince ibérico", "imagen": "no/existe.jpg"}], "fotos")
    cliente = ClienteFalso(responder_simulando(ANIMALES))
    lotes = procesador(almacen, cliente, tam_lote=100)
    asyncio.run(lotes.enviar(ANIMALES, almacen.pendientes("animales")))
    assert asyncio.run(lotes.recoger(ANIMALES))["listos"] == 23
    [(clave, error)] = almacen.errores("animales")
    assert clave == "lince-iberico" and error.startswith("FileNotFoundError")


def test_lotes_sin_credenciales_corta_sin_tocar_los_items(almacen):
    ingerir_ejemplos(almacen, "curiosidades")
    cliente = ClienteFalso(responder_simulando(DOMINIOS["curiosidades"]))

    async def sin_credenciales(requests):
        raise TypeError("Could not resolve authentication method")

    cliente.messages.batches.create = sin_credenciales
    with pytest.raises(ErrorFatal):
        asyncio.run(
            pipeline.analizar(
                almacen,
                [DOMINIOS["curiosidades"]],
                AnalizadorClaude(cliente=cliente),
                modo="lotes",
                avisar=lambda m: None,
            )
        )
    assert almacen.estado("curiosidades")["pendiente"] == 13


def _responder_por_dominio(params):
    datos = datos_del_pedido(params)
    dominio = DOMINIOS["comercios"] if "rubro" in datos or "direccion" in datos else ANIMALES
    return responder_simulando(dominio)(params)
