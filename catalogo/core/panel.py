"""Panel visual del motor.

`python -m catalogo panel` levanta un servidor HTTP local (sin dependencias)
que sirve `panel.html` y un resumen JSON en `/api/estado`. La página lo
consulta cada 2 segundos y muestra progreso, ritmo, costo, tiempo restante,
qué se está analizando ahora, la actividad reciente y las novedades.

El mismo resumen es lo que `analizar --estado-json ruta.json` escribe a disco,
así que cualquier otro programa (un indicador de bandeja, un widget) puede
leerlo sin hablar con el servidor.

Única escritura: `POST /api/novedades/<id>/<vista|descartada|nueva>`.
"""

from __future__ import annotations

import json
import re
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .almacen import Almacen

_HTML = Path(__file__).with_name("panel.html")
VENTANA_SERIE = 30 * 60  # segundos de historia para la gráfica de ritmo
VENTANA_RITMO = 5 * 60  # segundos sobre los que se calcula fichas/minuto
INACTIVO_TRAS = 120  # sin eventos durante este tiempo = la corrida se cortó
TIPOS_VISIBLES = (
    "listo",
    "verificar",
    "error",
    "reintento",
    "pausa",
    "tope_costo",
    "lote_enviado",
    "lote_recibido",
    "fase",
    "fin",
    "novedad",
    "enlace",
)
_RUTA_NOVEDAD = re.compile(r"^/api/novedades/(\d+)/(vista|descartada|nueva)$")


def resumen(almacen: Almacen) -> dict:
    ahora = time.time()
    dominios: dict[str, dict] = {}
    for nombre in almacen.dominios_presentes():
        estados = almacen.estado(nombre)
        total = sum(estados.values())
        dominios[nombre] = {
            **estados,
            "total": total,
            "avance": round(estados["listo"] / total, 4) if total else 0.0,
            **almacen.metricas(nombre),
        }
        enlaces = almacen.resumen_enlaces(nombre)
        if enlaces:
            dominios[nombre]["enlaces"] = {
                "ok": enlaces.get("ok", 0),
                **{k: v for k, v in enlaces.items() if k != "ok"},
            }
            dominios[nombre]["enlaces_sin_verificar"] = max(0, total - sum(enlaces.values()))
    totales = _sumar(dominios.values())
    corrida = almacen.corrida_activa() or almacen.ultima_corrida()
    ultimo = almacen.ultimo_evento()
    estado = _estado_general(corrida, ultimo, totales, ahora)

    por_minuto = almacen.eventos_por_minuto(ahora - VENTANA_SERIE)
    minuto_actual = int(ahora // 60) * 60
    serie = []
    for i in range(VENTANA_SERIE // 60 - 1, -1, -1):
        minuto = minuto_actual - i * 60
        punto = por_minuto.get(minuto, {"listos": 0, "errores": 0})
        serie.append({"minuto": minuto, "listos": punto["listos"], "errores": punto["errores"]})

    listos_recientes = sum(v["listos"] for m, v in por_minuto.items() if m >= ahora - VENTANA_RITMO)
    minutos = VENTANA_RITMO / 60
    if corrida and corrida["fin"] is None:
        minutos = min(minutos, max(0.5, (ahora - corrida["inicio"]) / 60))
    ritmo = listos_recientes / minutos if estado in ("trabajando", "pausado") else 0.0
    restantes = totales["pendiente"] + totales["en_curso"] + totales["en_lote"] + totales["verificar"]
    eta = round(restantes / ritmo * 60) if ritmo > 0 else None

    en_curso = []
    for fila in almacen.en_curso():
        datos = fila["datos"]
        en_curso.append(
            {
                "dominio": fila["dominio"],
                "clave": fila["clave"],
                "titulo": str(datos.get("nombre") or datos.get("titulo") or datos.get("producto") or fila["clave"]),
                "segundos": round(ahora - fila["desde"]) if fila["desde"] else None,
            }
        )

    return {
        "hora": ahora,
        "db": almacen.ruta,
        "estado": estado,
        "corrida": corrida,
        "dominios": dominios,
        "totales": totales,
        "ritmo_por_min": round(ritmo, 2),
        "eta_segundos": eta,
        "restantes": restantes,
        "serie": serie,
        "en_curso": en_curso,
        "eventos": almacen.eventos_recientes(40, TIPOS_VISIBLES),
        "lotes": almacen.todos_los_lotes_abiertos(),
        "errores_recientes": almacen.eventos_recientes(8, ("error",)),
        "novedades": almacen.novedades(estado="nueva", limite=12),
        "novedades_total": almacen.contar_novedades("nueva"),
    }


def _sumar(dominios) -> dict:
    claves = (
        "pendiente",
        "en_curso",
        "en_lote",
        "verificar",
        "listo",
        "error",
        "total",
        "analizados",
        "busquedas",
        "confianza_baja",
    )
    totales = {k: 0 for k in claves}
    costo = 0.0
    for d in dominios:
        for k in claves:
            totales[k] += d.get(k, 0) or 0
        costo += d.get("costo_usd") or 0.0
    totales["costo_usd"] = round(costo, 4)
    totales["avance"] = round(totales["listo"] / totales["total"], 4) if totales["total"] else 0.0
    return totales


def _estado_general(corrida: dict | None, ultimo: dict | None, totales: dict, ahora: float) -> str:
    if not corrida or corrida["fin"] is not None:
        if corrida and corrida["estado"] == "pendiente_lotes" and totales["en_lote"]:
            return "lotes"
        return "inactivo"
    if ultimo and ultimo["tipo"] == "pausa" and ahora - ultimo["ts"] < (ultimo["detalle"].get("segundos") or 60):
        return "pausado"
    if totales["en_lote"] and not totales["en_curso"]:
        return "lotes"
    if ultimo and ahora - ultimo["ts"] > INACTIVO_TRAS:
        return "interrumpido"
    return "trabajando"


class _Manejador(BaseHTTPRequestHandler):
    ruta_db = "catalogo.db"

    def do_GET(self) -> None:  # noqa: N802 - nombre fijado por http.server
        ruta = self.path.split("?", 1)[0]
        if ruta in ("/", "/index.html"):
            self._responder(200, "text/html; charset=utf-8", _HTML.read_bytes())
        elif ruta == "/api/estado":
            almacen = Almacen(self.ruta_db, solo_lectura=True)
            try:
                cuerpo = json.dumps(resumen(almacen), ensure_ascii=False).encode()
            finally:
                almacen.cerrar()
            self._responder(200, "application/json; charset=utf-8", cuerpo)
        else:
            self._responder(404, "text/plain; charset=utf-8", b"no encontrado")

    def do_POST(self) -> None:  # noqa: N802
        coincidencia = _RUTA_NOVEDAD.match(self.path.split("?", 1)[0])
        if not coincidencia:
            self._responder(404, "text/plain; charset=utf-8", b"no encontrado")
            return
        almacen = Almacen(self.ruta_db)
        try:
            ok = almacen.marcar_novedad(int(coincidencia.group(1)), coincidencia.group(2))
        finally:
            almacen.cerrar()
        self._responder(204 if ok else 404, "text/plain; charset=utf-8", b"")

    def _responder(self, codigo: int, tipo: str, cuerpo: bytes) -> None:
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if cuerpo:
            self.wfile.write(cuerpo)

    def log_message(self, *args) -> None:  # silencio: el panel se consulta cada 2 s
        pass


def crear_servidor(ruta_db: str, host: str = "127.0.0.1", puerto: int = 8765) -> ThreadingHTTPServer:
    manejador = type("Manejador", (_Manejador,), {"ruta_db": ruta_db})
    return ThreadingHTTPServer((host, puerto), manejador)


def servir(ruta_db: str, host: str = "127.0.0.1", puerto: int = 8765, abrir: bool = False) -> None:
    servidor = crear_servidor(ruta_db, host, puerto)
    direccion = f"http://{host}:{servidor.server_address[1]}"
    print(f"Panel en {direccion}  (Ctrl+C para cerrar)", file=sys.stderr)
    if abrir:
        webbrowser.open(direccion)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
