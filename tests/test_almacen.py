import time

from catalogo.core.modelos import Item


def item(clave="leon", **datos):
    return Item("animales", clave, datos or {"nombre": "León"}, ["wikipedia"])


def test_reingresar_lo_mismo_no_reencola(almacen):
    assert almacen.ingerir([item()], "1")["nuevos"] == 1
    almacen.guardar_analisis("animales", "leon", {"ruta": "x"}, "m")
    assert almacen.ingerir([item()], "1") == {"nuevos": 0, "actualizados": 0, "sin_cambios": 1}
    assert almacen.estado("animales")["listo"] == 1


def test_datos_nuevos_o_prompt_nuevo_reencolan_y_conservan_el_analisis_viejo(almacen):
    almacen.ingerir([item()], "1")
    almacen.guardar_analisis("animales", "leon", {"ruta": "x"}, "m")

    assert almacen.ingerir([item(nombre="León africano")], "1")["actualizados"] == 1
    [registro] = almacen.analizados("animales")
    assert registro.vigente is False and registro.analisis == {"ruta": "x"}

    almacen.guardar_analisis("animales", "leon", {"ruta": "y"}, "m")
    assert almacen.ingerir([item(nombre="León africano")], "2")["actualizados"] == 1
    assert [i.clave for i in almacen.pendientes("animales")] == ["leon"]


def test_vencimiento_por_ttl(almacen):
    almacen.ingerir([item()], "1")
    almacen.guardar_analisis("animales", "leon", {"ruta": "x"}, "m")
    assert almacen.vencer("animales", None) == 0
    assert almacen.vencer("animales", 30) == 0
    almacen.db.execute("UPDATE items SET analizado_en=?", (time.time() - 31 * 86400,))
    assert almacen.vencer("animales", 30) == 1
    assert almacen.estado("animales")["pendiente"] == 1


def test_recupera_lo_interrumpido(almacen):
    almacen.ingerir([item("a"), item("b")], "1")
    almacen.marcar("animales", ["a", "b"], "en_curso")
    assert almacen.pendientes("animales") == []
    assert almacen.recuperar_interrumpidos("animales") == 2
    assert len(almacen.pendientes("animales")) == 2


def test_errores_y_reintento(almacen):
    almacen.ingerir([item()], "1")
    almacen.guardar_error("animales", "leon", "Rechazo: x")
    assert almacen.errores("animales") == [("leon", "Rechazo: x")]
    assert almacen.reintentar_errores("animales") == 1
    assert almacen.estado("animales")["pendiente"] == 1


def test_aportes_por_fuente_se_reemplazan_sin_pisar_otras(almacen):
    almacen.guardar_aportes([Item("animales", "leon", {"peso_kg": 1}, ["wikipedia"])])
    almacen.guardar_aportes([Item("animales", "leon", {"peso_kg": 2}, ["gbif"])])
    almacen.guardar_aportes([Item("animales", "leon", {"peso_kg": 3}, ["wikipedia"])])
    aportes = almacen.aportes("animales", "leon")
    assert [(a.fuentes, a.datos) for a in aportes] == [(["gbif"], {"peso_kg": 2}), (["wikipedia"], {"peso_kg": 3})]


def test_lotes(almacen):
    almacen.ingerir([item("a"), item("b")], "1")
    almacen.registrar_lote("msgbatch_1", "animales", 2)
    almacen.marcar("animales", ["a", "b"], "en_lote", lote_id="msgbatch_1")
    assert almacen.lotes_abiertos("animales") == ["msgbatch_1"]
    assert {i.clave for i in almacen.items_del_lote("animales", "msgbatch_1")} == {"a", "b"}
    almacen.cerrar_lote("msgbatch_1")
    assert almacen.lotes_abiertos("animales") == []
