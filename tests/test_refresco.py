"""Refresco parcial: una ficha vencida reverifica solo lo volátil y copia el resto."""

import asyncio
import json
import time

from catalogo.core import pipeline
from catalogo.core.analizador import AnalizadorClaude, AnalizadorClaudeCode, ProcesadorPorLotes
from catalogo.core.modelos import Item
from catalogo.dominios import DOMINIOS
from falsos import ClienteFalso, EjecutorFalso, mensaje, opcion, prompt_del_comando, resultado_cli, responder_simulando
from test_pipeline import Registrador, analizar, ingerir_ejemplos

COMERCIOS = DOMINIOS["comercios"]
ANIMALES = DOMINIOS["animales"]
DIA = 86400


def vencer_todo(almacen):
    almacen.db.execute("UPDATE items SET analizado_en=?", (time.time() - 40 * DIA,))
    almacen.db.commit()


def test_esquema_y_prompt_reducidos():
    campos = COMERCIOS.campos_de_refresco()
    assert campos == ("situacion", "servicios", "rango_precios", "confianza", "fuentes_web")
    esquema = COMERCIOS.esquema(refresco=True)
    assert set(esquema["properties"]) == set(campos) == set(esquema["required"])  # mismo orden que la ficha completa
    assert "ruta" not in esquema["properties"]
    assert "Refresco de una ficha existente" in COMERCIOS.instrucciones(True, refresco=True)
    assert "Refresco" not in COMERCIOS.instrucciones(True)
    previa = {"ruta": "x", "etiquetas": ["a"], "situacion": "abierto"}
    texto = COMERCIOS.contenido_texto(Item("comercios", "k", {"nombre": "Kiosco"}), previa)
    assert "Ficha anterior" in texto and '"situacion": "abierto"' in texto and "etiquetas" not in texto
    # Animales también refresca (estado_conservacion); sin volátiles no se refresca.
    assert ANIMALES.puede_refrescar() and DOMINIOS["curiosidades"].puede_refrescar() is False


def test_refresco_aplicable_solo_con_ficha_previa_valida():
    item = Item("comercios", "k", {"nombre": "Kiosco", "rubro": "kiosco"})
    completa = COMERCIOS.validar(COMERCIOS.simular(item))
    assert COMERCIOS.refresco_aplicable(completa)
    assert not COMERCIOS.refresco_aplicable(None)
    assert not COMERCIOS.refresco_aplicable({"ruta": completa["ruta"]})  # esquema viejo: faltan campos
    assert not DOMINIOS["curiosidades"].refresco_aplicable(
        DOMINIOS["curiosidades"].simular(Item("curiosidades", "g", {"titulo": "Guernica"}))
    )

    parcial = {
        "situacion": "cerrado",
        "servicios": [],
        "rango_precios": "$$",
        "confianza": "alta",
        "fuentes_web": ["https://a"],
    }
    fusion = COMERCIOS.fusionar_refresco(completa, {**parcial, "descripcion": "no debería entrar"})
    assert fusion["situacion"] == "cerrado" and fusion["descripcion"] == completa["descripcion"]
    assert fusion["ruta"] == completa["ruta"] and fusion["fuentes_web"] == ["https://a"]


def test_vencidos_se_refrescan_y_el_resto_se_copia(almacen):
    ingerir_ejemplos(almacen, "comercios")
    primera = Registrador(
        ajustar=lambda item, ficha: ficha.update(descripcion="Descripción original", situacion="abierto")
    )
    analizar(almacen, ["comercios"], primera)
    vencer_todo(almacen)
    assert {i.motivo for i in almacen.pendientes("comercios")} == set()  # todavía listos
    pipeline.preparar(almacen, [COMERCIOS])
    assert {i.motivo for i in almacen.pendientes("comercios")} == {"vencido"}

    segunda = Registrador(ajustar=lambda item, ficha: ficha.update(descripcion="NO debería pisar", situacion="cerrado"))
    resultado = analizar(almacen, ["comercios"], segunda)
    assert resultado["dominios"]["comercios"]["listos"] == 13
    fichas = {r.item.clave: r.analisis for r in almacen.analizados("comercios")}
    assert all(f["descripcion"] == "Descripción original" and f["situacion"] == "cerrado" for f in fichas.values())
    assert all(i.motivo is None for i in [r.item for r in almacen.analizados("comercios")])
    inicios = [e for e in almacen.eventos_recientes(200) if e["tipo"] == "inicio"]
    assert sum(1 for e in inicios if e["detalle"].get("refresco")) == 13
    listos = [e for e in almacen.eventos_recientes(200) if e["tipo"] == "listo"]
    assert listos[0]["detalle"]["refresco"] is True
    # Un cierre detectado por el refresco es novedad solo si lo respaldan fuentes: acá no las hay.
    assert almacen.novedades("comercios") == []


def test_datos_nuevos_o_esquema_viejo_reanalizan_completo(almacen):
    ingerir_ejemplos(almacen, "comercios")
    analizar(almacen, ["comercios"], Registrador(ajustar=lambda i, f: f.update(descripcion="Original")))
    # 1) datos nuevos: motivo "cambio" -> análisis completo
    pipeline.ingerir(
        almacen, COMERCIOS, [{"nombre": "Kiosco 24", "direccion": "Av. Corrientes 1500", "horario": "24 h"}], "web"
    )
    [kiosco] = almacen.pendientes("comercios")
    assert kiosco.motivo == "cambio"
    # 2) vencido pero con ficha del esquema viejo -> análisis completo
    almacen.db.execute(
        "UPDATE items SET analisis=? WHERE clave='hiper-ahorro--av-rivadavia-5000'", (json.dumps({"ruta": "x"}),)
    )
    almacen.db.execute(
        "UPDATE items SET analizado_en=? WHERE clave='hiper-ahorro--av-rivadavia-5000'", (time.time() - 40 * DIA,)
    )
    almacen.db.commit()
    registrador = Registrador(ajustar=lambda i, f: f.update(descripcion="Nueva"))
    analizar(almacen, ["comercios"], registrador)
    fichas = {r.item.clave: r.analisis for r in almacen.analizados("comercios")}
    assert fichas["kiosco-24--av-corrientes-1500"]["descripcion"] == "Nueva"
    assert fichas["hiper-ahorro--av-rivadavia-5000"]["descripcion"] == "Nueva"
    inicios = [e for e in almacen.eventos_recientes(50) if e["tipo"] == "inicio"]
    assert all(not e["detalle"].get("refresco") for e in inicios)


def test_api_pide_esquema_reducido_esfuerzo_bajo_y_una_busqueda():
    item = Item("comercios", "k", {"nombre": "Kiosco 24", "rubro": "kiosco"}, ["web"], motivo="vencido")
    previa = COMERCIOS.validar(COMERCIOS.simular(item))

    def responder(params):
        return mensaje(
            {
                "situacion": "cerrado",
                "servicios": [],
                "rango_precios": "$",
                "confianza": "alta",
                "fuentes_web": ["https://x"],
            },
            herramienta=True,
        )

    cliente = ClienteFalso(responder)
    analizador = AnalizadorClaude(cliente=cliente, esfuerzo="high")
    parcial, _, _ = asyncio.run(analizador.analizar(COMERCIOS, item, con_web=True, previa=previa))
    assert parcial == {
        "situacion": "cerrado",
        "servicios": [],
        "rango_precios": "$",
        "confianza": "alta",
        "fuentes_web": ["https://x"],
    }
    [pedido] = cliente.llamadas
    assert pedido["output_config"]["effort"] == "low"
    assert pedido["tools"][0]["max_uses"] == 1
    assert set(pedido["tools"][2]["input_schema"]["properties"]) == set(COMERCIOS.campos_de_refresco())
    assert (
        "Refresco" in pedido["system"][0]["text"] and "Ficha anterior" in pedido["messages"][0]["content"][-1]["text"]
    )
    sin_web = analizador.parametros(COMERCIOS, item, con_web=False, previa=previa)
    assert set(sin_web["output_config"]["format"]["schema"]["properties"]) == set(COMERCIOS.campos_de_refresco())


def test_claude_code_pide_esquema_reducido(tmp_path):
    item = Item("comercios", "k", {"nombre": "Kiosco 24", "rubro": "kiosco"}, ["web"], motivo="vencido")
    previa = COMERCIOS.validar(COMERCIOS.simular(item))
    ejecutor = EjecutorFalso(
        lambda c: resultado_cli(
            {
                "situacion": "abierto",
                "servicios": ["pago con QR"],
                "rango_precios": "$",
                "confianza": "alta",
                "fuentes_web": [],
            }
        )
    )
    a = AnalizadorClaudeCode(carpeta=str(tmp_path), ejecutar=ejecutor, esfuerzo="high")
    parcial, _, _ = asyncio.run(a.analizar(COMERCIOS, item, con_web=True, previa=previa))
    assert parcial["servicios"] == ["pago con QR"]
    [comando] = ejecutor.comandos
    assert set(json.loads(opcion(comando, "--json-schema"))["properties"]) == set(COMERCIOS.campos_de_refresco())
    assert opcion(comando, "--effort") == "low" and opcion(comando, "--system-prompt-file").endswith("-refresco.txt")
    assert prompt_del_comando(comando)["nombre"] == "Kiosco 24"


def test_lotes_refrescan_y_fusionan(almacen):
    ingerir_ejemplos(almacen, "comercios")
    analizar(
        almacen, ["comercios"], Registrador(ajustar=lambda i, f: f.update(descripcion="Original", situacion="abierto"))
    )
    vencer_todo(almacen)
    pipeline.preparar(almacen, [COMERCIOS])

    def ajustes(datos, ficha):
        ficha["situacion"] = "cerrado"
        ficha["descripcion"] = "NO debería pisar"
        if "Ficha anterior" in json.dumps(datos):  # nunca: datos es el registro, no el prompt
            raise AssertionError
        return None

    cliente = ClienteFalso(responder_simulando(COMERCIOS, ajustes))
    lotes = ProcesadorPorLotes(AnalizadorClaude(cliente=cliente), almacen, tam_lote=100, intervalo=0)
    ids = asyncio.run(lotes.enviar(COMERCIOS, almacen.pendientes("comercios"), con_web=True))
    pedido = cliente.messages.batches.lotes[ids[0]][0]["params"]
    assert set(pedido["tools"][2]["input_schema"]["properties"]) == set(COMERCIOS.campos_de_refresco())
    cuenta = asyncio.run(lotes.recoger(COMERCIOS))
    assert cuenta["listos"] == 13
    fichas = {r.item.clave: r.analisis for r in almacen.analizados("comercios")}
    assert all(f["descripcion"] == "Original" and f["situacion"] == "cerrado" for f in fichas.values())
