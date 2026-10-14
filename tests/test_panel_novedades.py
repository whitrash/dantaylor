import json
import threading
import urllib.request

from catalogo.core import panel
from catalogo.core.almacen import Almacen
from catalogo.core.novedades import Senal, puntuar


def test_el_panel_marca_novedades_por_http(tmp_path):
    ruta = tmp_path / "panel.db"
    almacen = Almacen(str(ruta))
    v = puntuar(
        [
            Senal("oficial", "https://buenosaires.gob.ar/x", 1.8e9, campo="situacion", valor="cerrado"),
            Senal("medio", "https://www.clarin.com/y", 1.8e9, campo="situacion", valor="cerrado"),
        ],
        {"situacion": "abierto"},
        ahora=1.8e9,
    )
    novedad_id = almacen.registrar_novedad(
        "comercios", "kiosco-24", "Kiosco 24", "Kiosco 24 cerró", v.como_dict(), "abierto"
    )
    almacen.cerrar()

    servidor = panel.crear_servidor(str(ruta), "127.0.0.1", 0)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{servidor.server_address[1]}"
    try:
        estado = json.loads(urllib.request.urlopen(base + "/api/estado").read())
        assert estado["novedades_total"] == 1 and estado["novedades"][0]["id"] == novedad_id
        pagina = urllib.request.urlopen(base + "/").read().decode()
        assert 'aria-live="polite"' in pagina and "prefers-reduced-motion" in pagina and 'class="salto"' in pagina

        r = urllib.request.urlopen(urllib.request.Request(base + f"/api/novedades/{novedad_id}/vista", method="POST"))
        assert r.status == 204
        estado = json.loads(urllib.request.urlopen(base + "/api/estado").read())
        assert estado["novedades_total"] == 0

        try:
            urllib.request.urlopen(urllib.request.Request(base + "/api/novedades/999/vista", method="POST"))
        except urllib.error.HTTPError as e:
            assert e.code == 404
        else:
            raise AssertionError("debía dar 404")
        try:
            urllib.request.urlopen(urllib.request.Request(base + f"/api/novedades/{novedad_id}/borrar", method="POST"))
        except urllib.error.HTTPError as e:
            assert e.code == 404
        else:
            raise AssertionError("estado inválido debía dar 404")
    finally:
        servidor.shutdown()
        servidor.server_close()
