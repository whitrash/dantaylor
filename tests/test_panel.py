import json
import threading
import time
import urllib.request

from catalogo.core import panel, pipeline
from catalogo.core.almacen import Almacen
from catalogo.dominios import DOMINIOS
from test_pipeline import Registrador, analizar, ingerir_ejemplos


def test_resumen_vacio():
    almacen = Almacen(":memory:")
    r = panel.resumen(almacen)
    assert r["estado"] == "inactivo" and r["dominios"] == {} and r["corrida"] is None
    assert r["totales"]["total"] == 0 and r["eta_segundos"] is None and r["ritmo_por_min"] == 0
    assert len(r["serie"]) == 30 and r["eventos"] == [] and r["en_curso"] == []


def test_resumen_despues_de_una_corrida(almacen):
    ingerir_ejemplos(almacen, "animales", "comercios")
    analizar(almacen, ["animales", "comercios"], Registrador(costo=0.01))
    r = panel.resumen(almacen)
    assert r["estado"] == "inactivo"  # la corrida terminó
    assert r["totales"]["total"] == 36 and r["totales"]["listo"] == 36 and r["totales"]["avance"] == 1.0
    assert r["dominios"]["animales"]["listo"] == 23 and r["dominios"]["comercios"]["avance"] == 1.0
    assert r["totales"]["costo_usd"] == 0.36 and r["restantes"] == 0
    assert r["corrida"]["estado"] == "terminada" and json.loads(r["corrida"]["dominios"]) == ["animales", "comercios"]
    assert r["eventos"][0]["tipo"] == "fin" and any(e["tipo"] == "listo" for e in r["eventos"])
    assert sum(p["listos"] for p in r["serie"]) == 36  # todo cayó en el último minuto o el anterior
    assert r["lotes"] == [] and r["errores_recientes"] == []


def test_estado_general_mientras_trabaja_pausa_o_se_corta(almacen):
    ingerir_ejemplos(almacen, "curiosidades")
    corrida = almacen.iniciar_corrida("tiempo-real", ["curiosidades"], 4, "api", 13)
    item = almacen.pendientes("curiosidades")[0]
    almacen.marcar("curiosidades", [item.clave], "en_curso")
    almacen.registrar_evento(corrida, "inicio", "curiosidades", item.clave, titulo="Guernica")
    almacen.registrar_evento(corrida, "listo", "curiosidades", "otro", titulo="Otro", costo_usd=0.02)
    r = panel.resumen(almacen)
    assert r["estado"] == "trabajando"
    assert r["ritmo_por_min"] > 0 and r["eta_segundos"] is not None
    assert r["en_curso"] == [
        {"dominio": "curiosidades", "clave": item.clave, "titulo": item.datos["titulo"], "segundos": 0}
    ]

    almacen.registrar_evento(corrida, "pausa", segundos=120)
    assert panel.resumen(almacen)["estado"] == "pausado"

    almacen.db.execute("UPDATE eventos SET ts = ts - 600")
    almacen.db.commit()
    assert panel.resumen(almacen)["estado"] == "interrumpido"

    almacen.terminar_corrida(corrida, estado="pendiente_lotes")
    almacen.marcar("curiosidades", [item.clave], "en_lote", lote_id="msgbatch_x")
    almacen.registrar_lote("msgbatch_x", "curiosidades", 1)
    r = panel.resumen(almacen)
    assert r["estado"] == "lotes" and r["lotes"][0]["id"] == "msgbatch_x"


def test_servidor_http_sirve_pagina_y_estado(tmp_path):
    ruta = tmp_path / "panel.db"
    almacen = Almacen(str(ruta))
    ingerir_ejemplos(almacen, "comercios")
    analizar(almacen, ["comercios"])

    servidor = panel.crear_servidor(str(ruta), "127.0.0.1", 0)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    base = f"http://127.0.0.1:{servidor.server_address[1]}"
    try:
        pagina = urllib.request.urlopen(base + "/").read().decode()
        assert "<title>Catálogos · panel</title>" in pagina and "/api/estado" in pagina
        with urllib.request.urlopen(base + "/api/estado") as r:
            assert r.headers["Content-Type"].startswith("application/json")
            estado = json.loads(r.read())
        assert estado["dominios"]["comercios"]["listo"] == 13 and estado["db"] == str(ruta)
        try:
            urllib.request.urlopen(base + "/otra")
        except urllib.error.HTTPError as e:
            assert e.code == 404
        else:
            raise AssertionError("debía dar 404")
        # El panel lee mientras el motor escribe (WAL): la lectura no bloquea ni falla.
        almacen.registrar_evento(None, "listo", "comercios", "x", titulo="x")
        assert json.loads(urllib.request.urlopen(base + "/api/estado").read())["eventos"][0]["clave"] == "x"
    finally:
        servidor.shutdown()
        servidor.server_close()
        almacen.cerrar()
    assert time.time() > 0  # sanity


def test_instantanea_escribe_como_mucho_una_vez_por_segundo(almacen, tmp_path):
    ingerir_ejemplos(almacen, "comercios")
    ruta = tmp_path / "estado.json"
    inst = pipeline.Instantanea(almacen, ruta, cada=10)
    inst.tal_vez()
    primera = ruta.stat().st_mtime_ns
    almacen.marcar("comercios", [almacen.pendientes("comercios")[0].clave], "en_curso")
    inst.tal_vez()  # demasiado pronto: no reescribe
    assert ruta.stat().st_mtime_ns == primera
    inst.tal_vez(forzar=True)
    assert json.loads(ruta.read_text())["totales"]["en_curso"] == 1
    assert DOMINIOS["comercios"].nombre in json.loads(ruta.read_text())["dominios"]
