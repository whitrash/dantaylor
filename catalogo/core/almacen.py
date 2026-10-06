"""Estado persistente del motor (SQLite).

Cada item tiene un estado:

    pendiente -> en_curso -> listo
                          -> verificar -> en_curso -> listo   (segunda pasada, con web)
                          -> error
    pendiente -> en_lote  -> listo / verificar / error / pendiente (si el lote expiró)

Esto da tres cosas que hacen falta para trabajar con volumen:
  * reanudar: si el proceso se corta, lo `en_curso` vuelve a `pendiente`
    y lo `listo` no se toca;
  * no pagar dos veces: un item cuya huella (datos + versión del prompt) no
    cambió no se vuelve a analizar;
  * vencimiento (TTL): los comercios cambian, los animales no; cada dominio
    decide cada cuánto se reanaliza.

Además guarda:
  * el aporte de cada fuente por separado (`aportes`); la ficha que se analiza
    es la combinación de todas, según la prioridad de fuentes del dominio;
  * métricas por item (segundos, tokens, búsquedas, costo) y un registro de
    corridas y eventos, que es lo que lee el panel visual.

La base se abre en modo WAL: el panel puede leerla mientras el motor escribe.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from typing import Iterable

from .modelos import Item, Registro

ESTADOS = ("pendiente", "en_curso", "en_lote", "verificar", "listo", "error")
METRICAS = ("segundos", "costo_usd", "tokens_entrada", "tokens_salida", "busquedas")

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS items (
    dominio        TEXT NOT NULL,
    clave          TEXT NOT NULL,
    datos          TEXT NOT NULL,
    fuentes        TEXT NOT NULL,
    huella         TEXT NOT NULL,
    estado         TEXT NOT NULL,
    intentos       INTEGER NOT NULL DEFAULT 0,
    analisis       TEXT,
    modelo         TEXT,
    error          TEXT,
    lote_id        TEXT,
    analizado_en   REAL,
    actualizado_en REAL NOT NULL,
    PRIMARY KEY (dominio, clave)
);
CREATE INDEX IF NOT EXISTS items_por_estado ON items (dominio, estado);
CREATE TABLE IF NOT EXISTS aportes (
    dominio TEXT NOT NULL,
    clave   TEXT NOT NULL,
    fuente  TEXT NOT NULL,
    datos   TEXT NOT NULL,
    PRIMARY KEY (dominio, clave, fuente)
);
CREATE TABLE IF NOT EXISTS lotes (
    id        TEXT PRIMARY KEY,
    dominio   TEXT NOT NULL,
    estado    TEXT NOT NULL,
    cantidad  INTEGER NOT NULL,
    creado_en REAL NOT NULL,
    con_web   INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS corridas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    inicio       REAL NOT NULL,
    fin          REAL,
    estado       TEXT NOT NULL,
    modo         TEXT NOT NULL,
    dominios     TEXT NOT NULL,
    concurrencia INTEGER NOT NULL,
    analizador   TEXT NOT NULL,
    total        INTEGER NOT NULL DEFAULT 0,
    listos       INTEGER NOT NULL DEFAULT 0,
    errores      INTEGER NOT NULL DEFAULT 0,
    reintentos   INTEGER NOT NULL DEFAULT 0,
    costo_usd    REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS eventos (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         REAL NOT NULL,
    corrida_id INTEGER,
    dominio    TEXT,
    clave      TEXT,
    tipo       TEXT NOT NULL,
    detalle    TEXT
);
CREATE INDEX IF NOT EXISTS eventos_por_ts ON eventos (ts);
"""

# Columnas agregadas después de la primera versión: se suman a bases existentes.
_COLUMNAS_ITEMS = {
    "prioridad": "INTEGER NOT NULL DEFAULT 0",
    "con_web": "INTEGER",
    "segundos": "REAL",
    "costo_usd": "REAL",
    "tokens_entrada": "INTEGER",
    "tokens_salida": "INTEGER",
    "busquedas": "INTEGER",
}


def huella(datos: dict, version_prompt: str) -> str:
    contenido = json.dumps(datos, sort_keys=True, ensure_ascii=False) + "\x00" + version_prompt
    return hashlib.sha256(contenido.encode()).hexdigest()


class Almacen:
    def __init__(self, ruta: str = ":memory:", solo_lectura: bool = False):
        """`solo_lectura` es para el panel: abre sin tocar el esquema ni escribir,
        así nunca compite con el motor por el bloqueo de escritura."""
        self.ruta = ruta
        if solo_lectura:
            self.db = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True, timeout=5)
            self.db.row_factory = sqlite3.Row
            return
        self.db = sqlite3.connect(ruta, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.executescript(_ESQUEMA)
        self._migrar()

    def _migrar(self) -> None:
        existentes = {f["name"] for f in self.db.execute("PRAGMA table_info(items)")}
        with self.db:
            for columna, tipo in _COLUMNAS_ITEMS.items():
                if columna not in existentes:
                    self.db.execute(f"ALTER TABLE items ADD COLUMN {columna} {tipo}")
            if "con_web" not in {f["name"] for f in self.db.execute("PRAGMA table_info(lotes)")}:
                self.db.execute("ALTER TABLE lotes ADD COLUMN con_web INTEGER NOT NULL DEFAULT 0")

    def cerrar(self) -> None:
        self.db.close()

    # --- ingreso ---------------------------------------------------------

    def guardar_aportes(self, items: Iterable[Item]) -> None:
        """Lo que dice cada fuente sobre cada item, por separado. Volver a cargar
        una fuente reemplaza su aporte sin pisar lo que dijeron las demás."""
        with self.db:
            self.db.executemany(
                "INSERT INTO aportes (dominio, clave, fuente, datos) VALUES (?, ?, ?, ?)"
                " ON CONFLICT (dominio, clave, fuente) DO UPDATE SET datos=excluded.datos",
                [(it.dominio, it.clave, it.fuentes[0], _json(it.datos)) for it in items],
            )

    def aportes(self, dominio: str, clave: str) -> list[Item]:
        filas = self.db.execute(
            "SELECT fuente, datos FROM aportes WHERE dominio=? AND clave=? ORDER BY fuente", (dominio, clave)
        )
        return [Item(dominio, clave, json.loads(f["datos"]), [f["fuente"]]) for f in filas]

    def ingerir(self, items: Iterable[Item], version_prompt: str) -> dict[str, int]:
        cuenta = {"nuevos": 0, "actualizados": 0, "sin_cambios": 0}
        ahora = time.time()
        with self.db:
            for item in items:
                nueva = huella(item.datos, version_prompt)
                fila = self.db.execute(
                    "SELECT huella, fuentes FROM items WHERE dominio=? AND clave=?",
                    (item.dominio, item.clave),
                ).fetchone()
                fuentes = json.dumps(item.fuentes, ensure_ascii=False)
                if fila is None:
                    self.db.execute(
                        "INSERT INTO items (dominio, clave, datos, fuentes, huella, estado, actualizado_en)"
                        " VALUES (?, ?, ?, ?, ?, 'pendiente', ?)",
                        (item.dominio, item.clave, _json(item.datos), fuentes, nueva, ahora),
                    )
                    cuenta["nuevos"] += 1
                elif fila["huella"] != nueva:
                    # Cambiaron los datos o la versión del prompt: hay que reanalizar.
                    # El análisis anterior se conserva (se muestra como no vigente).
                    self.db.execute(
                        "UPDATE items SET datos=?, fuentes=?, huella=?, estado='pendiente',"
                        " intentos=0, error=NULL, lote_id=NULL, actualizado_en=? WHERE dominio=? AND clave=?",
                        (_json(item.datos), fuentes, nueva, ahora, item.dominio, item.clave),
                    )
                    cuenta["actualizados"] += 1
                else:
                    if fila["fuentes"] != fuentes:
                        self.db.execute(
                            "UPDATE items SET fuentes=? WHERE dominio=? AND clave=?",
                            (fuentes, item.dominio, item.clave),
                        )
                    cuenta["sin_cambios"] += 1
        return cuenta

    # --- preparación de una corrida -------------------------------------

    def recuperar_interrumpidos(self, dominio: str) -> int:
        """Lo que quedó `en_curso` de una corrida cortada vuelve a la cola
        (a `verificar` si ya tenía una primera pasada guardada)."""
        with self.db:
            return self.db.execute(
                "UPDATE items SET estado=CASE WHEN analisis IS NOT NULL AND con_web=0 THEN 'verificar'"
                " ELSE 'pendiente' END WHERE dominio=? AND estado='en_curso'",
                (dominio,),
            ).rowcount

    def vencer(self, dominio: str, ttl_dias: float | None) -> int:
        """Lo vencido vuelve a la cola con prioridad: caduca, así que va antes
        que la carga masiva de items nuevos."""
        if ttl_dias is None:
            return 0
        limite = time.time() - ttl_dias * 86400
        with self.db:
            return self.db.execute(
                "UPDATE items SET estado='pendiente', prioridad=1 WHERE dominio=? AND estado='listo' AND analizado_en < ?",
                (dominio, limite),
            ).rowcount

    def reintentar_errores(self, dominio: str) -> int:
        with self.db:
            return self.db.execute(
                "UPDATE items SET estado='pendiente', error=NULL WHERE dominio=? AND estado='error'", (dominio,)
            ).rowcount

    def pendientes(self, dominio: str, limite: int | None = None, estado: str = "pendiente") -> list[Item]:
        consulta = "SELECT * FROM items WHERE dominio=? AND estado=? ORDER BY prioridad DESC, clave"
        parametros: tuple = (dominio, estado)
        if limite is not None:
            consulta += " LIMIT ?"
            parametros += (limite,)
        return [_a_item(f) for f in self.db.execute(consulta, parametros)]

    def para_verificar(self, dominio: str) -> list[Item]:
        return self.pendientes(dominio, estado="verificar")

    # --- transiciones ----------------------------------------------------

    def marcar(self, dominio: str, claves: Iterable[str], estado: str, lote_id: str | None = None) -> None:
        assert estado in ESTADOS
        with self.db:
            self.db.executemany(
                "UPDATE items SET estado=?, lote_id=?, actualizado_en=? WHERE dominio=? AND clave=?",
                [(estado, lote_id, time.time(), dominio, c) for c in claves],
            )

    def guardar_analisis(
        self,
        dominio: str,
        clave: str,
        analisis: dict,
        modelo: str,
        metricas: dict | None = None,
        estado: str = "listo",
        con_web: bool = False,
    ) -> None:
        assert estado in ("listo", "verificar")
        m = metricas or {}
        ahora = time.time()
        with self.db:
            self.db.execute(
                "UPDATE items SET estado=?, analisis=?, modelo=?, error=NULL, lote_id=NULL, prioridad=0,"
                " intentos=intentos+1, analizado_en=?, actualizado_en=?, con_web=?,"
                " segundos=?, costo_usd=?, tokens_entrada=?, tokens_salida=?, busquedas=?"
                " WHERE dominio=? AND clave=?",
                (
                    estado,
                    _json(analisis),
                    modelo,
                    ahora,
                    ahora,
                    int(con_web),
                    *(m.get(k) for k in METRICAS),
                    dominio,
                    clave,
                ),
            )

    def guardar_error(self, dominio: str, clave: str, error: str, segundos: float | None = None) -> None:
        with self.db:
            self.db.execute(
                "UPDATE items SET estado='error', error=?, lote_id=NULL, intentos=intentos+1,"
                " segundos=COALESCE(?, segundos), actualizado_en=? WHERE dominio=? AND clave=?",
                (error[:2000], segundos, time.time(), dominio, clave),
            )

    # --- lotes (Message Batches) ----------------------------------------

    def registrar_lote(self, lote_id: str, dominio: str, cantidad: int, con_web: bool = False) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO lotes (id, dominio, estado, cantidad, creado_en, con_web) VALUES (?, ?, 'abierto', ?, ?, ?)",
                (lote_id, dominio, cantidad, time.time(), int(con_web)),
            )

    def cerrar_lote(self, lote_id: str) -> None:
        with self.db:
            self.db.execute("UPDATE lotes SET estado='cerrado' WHERE id=?", (lote_id,))

    def lotes_abiertos(self, dominio: str) -> list[str]:
        filas = self.db.execute(
            "SELECT id FROM lotes WHERE dominio=? AND estado='abierto' ORDER BY creado_en", (dominio,)
        )
        return [f["id"] for f in filas]

    def lote(self, lote_id: str) -> dict:
        return dict(self.db.execute("SELECT * FROM lotes WHERE id=?", (lote_id,)).fetchone())

    def todos_los_lotes_abiertos(self) -> list[dict]:
        return [dict(f) for f in self.db.execute("SELECT * FROM lotes WHERE estado='abierto' ORDER BY creado_en")]

    def items_del_lote(self, dominio: str, lote_id: str) -> list[Item]:
        filas = self.db.execute(
            "SELECT * FROM items WHERE dominio=? AND lote_id=? AND estado='en_lote'", (dominio, lote_id)
        )
        return [_a_item(f) for f in filas]

    # --- corridas y eventos (lo que mira el panel) -----------------------

    def iniciar_corrida(self, modo: str, dominios: list[str], concurrencia: int, analizador: str, total: int) -> int:
        with self.db:
            cursor = self.db.execute(
                "INSERT INTO corridas (inicio, estado, modo, dominios, concurrencia, analizador, total)"
                " VALUES (?, 'activa', ?, ?, ?, ?, ?)",
                (time.time(), modo, json.dumps(dominios), concurrencia, analizador, total),
            )
            return int(cursor.lastrowid)

    def actualizar_corrida(self, corrida_id: int, **campos) -> None:
        if not campos:
            return
        asignaciones = ", ".join(f"{k}=?" for k in campos)
        with self.db:
            self.db.execute(f"UPDATE corridas SET {asignaciones} WHERE id=?", (*campos.values(), corrida_id))

    def terminar_corrida(self, corrida_id: int, estado: str = "terminada", **campos) -> None:
        self.actualizar_corrida(corrida_id, fin=time.time(), estado=estado, **campos)

    def corrida_activa(self) -> dict | None:
        fila = self.db.execute("SELECT * FROM corridas WHERE fin IS NULL ORDER BY id DESC LIMIT 1").fetchone()
        return dict(fila) if fila else None

    def ultima_corrida(self) -> dict | None:
        fila = self.db.execute("SELECT * FROM corridas ORDER BY id DESC LIMIT 1").fetchone()
        return dict(fila) if fila else None

    def registrar_evento(
        self, corrida_id: int | None, tipo: str, dominio: str | None = None, clave: str | None = None, **detalle
    ) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO eventos (ts, corrida_id, dominio, clave, tipo, detalle) VALUES (?, ?, ?, ?, ?, ?)",
                (time.time(), corrida_id, dominio, clave, tipo, _json(detalle) if detalle else None),
            )

    def eventos_recientes(self, cantidad: int = 25, tipos: tuple[str, ...] | None = None) -> list[dict]:
        consulta = "SELECT * FROM eventos"
        parametros: tuple = ()
        if tipos:
            consulta += f" WHERE tipo IN ({','.join('?' * len(tipos))})"
            parametros = tipos
        consulta += " ORDER BY id DESC LIMIT ?"
        return [_evento(f) for f in self.db.execute(consulta, (*parametros, cantidad))]

    def ultimo_evento(self) -> dict | None:
        fila = self.db.execute("SELECT * FROM eventos ORDER BY id DESC LIMIT 1").fetchone()
        return _evento(fila) if fila else None

    def eventos_por_minuto(self, desde: float) -> dict[int, dict[str, int]]:
        filas = self.db.execute(
            "SELECT CAST(ts / 60 AS INTEGER) * 60 AS minuto,"
            " SUM(tipo='listo') AS listos, SUM(tipo='error') AS errores"
            " FROM eventos WHERE ts >= ? AND tipo IN ('listo', 'error') GROUP BY minuto",
            (desde,),
        )
        return {int(f["minuto"]): {"listos": f["listos"], "errores": f["errores"]} for f in filas}

    def en_curso(self) -> list[dict]:
        """Items que se están analizando ahora, con la hora en que arrancaron."""
        filas = self.db.execute(
            "SELECT i.dominio, i.clave, i.datos, MAX(e.ts) AS desde FROM items i"
            " LEFT JOIN eventos e ON e.dominio=i.dominio AND e.clave=i.clave AND e.tipo='inicio'"
            " WHERE i.estado='en_curso' GROUP BY i.dominio, i.clave ORDER BY desde"
        )
        return [
            {"dominio": f["dominio"], "clave": f["clave"], "datos": json.loads(f["datos"]), "desde": f["desde"]}
            for f in filas
        ]

    # --- lectura ---------------------------------------------------------

    def analizados(self, dominio: str) -> list[Registro]:
        filas = self.db.execute(
            "SELECT * FROM items WHERE dominio=? AND analisis IS NOT NULL ORDER BY clave", (dominio,)
        )
        return [
            Registro(
                item=_a_item(f),
                analisis=json.loads(f["analisis"]),
                modelo=f["modelo"],
                vigente=f["estado"] == "listo",
            )
            for f in filas
        ]

    def errores(self, dominio: str) -> list[tuple[str, str]]:
        filas = self.db.execute(
            "SELECT clave, error FROM items WHERE dominio=? AND estado='error' ORDER BY clave", (dominio,)
        )
        return [(f["clave"], f["error"]) for f in filas]

    def estado(self, dominio: str) -> dict[str, int]:
        cuenta = {e: 0 for e in ESTADOS}
        for fila in self.db.execute(
            "SELECT estado, COUNT(*) AS n FROM items WHERE dominio=? GROUP BY estado", (dominio,)
        ):
            cuenta[fila["estado"]] = fila["n"]
        return cuenta

    def metricas(self, dominio: str) -> dict:
        fila = self.db.execute(
            "SELECT COUNT(*) AS n, SUM(costo_usd) AS costo, AVG(segundos) AS segundos,"
            " SUM(busquedas) AS busquedas, SUM(tokens_entrada) AS tokens_entrada, SUM(tokens_salida) AS tokens_salida,"
            " SUM(json_extract(analisis, '$.confianza') = 'baja') AS confianza_baja"
            " FROM items WHERE dominio=? AND analisis IS NOT NULL",
            (dominio,),
        ).fetchone()
        return {
            "analizados": fila["n"] or 0,
            "costo_usd": round(fila["costo"] or 0.0, 4),
            "segundos_prom": round(fila["segundos"], 1) if fila["segundos"] is not None else None,
            "busquedas": fila["busquedas"] or 0,
            "tokens_entrada": fila["tokens_entrada"] or 0,
            "tokens_salida": fila["tokens_salida"] or 0,
            "confianza_baja": fila["confianza_baja"] or 0,
        }

    def dominios_presentes(self) -> list[str]:
        return [f["dominio"] for f in self.db.execute("SELECT DISTINCT dominio FROM items ORDER BY dominio")]


def _json(valor: object) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True)


def _a_item(fila: sqlite3.Row) -> Item:
    return Item(
        dominio=fila["dominio"],
        clave=fila["clave"],
        datos=json.loads(fila["datos"]),
        fuentes=json.loads(fila["fuentes"]),
    )


def _evento(fila: sqlite3.Row) -> dict:
    evento = dict(fila)
    evento["detalle"] = json.loads(evento["detalle"]) if evento["detalle"] else {}
    return evento
