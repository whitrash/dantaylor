"""Estado persistente del motor (SQLite).

Cada item tiene un estado:

    pendiente -> en_curso -> listo
                          -> error
    pendiente -> en_lote  -> listo / error / pendiente (si el lote expiró)

Esto da tres cosas que hacen falta para trabajar con volumen:
  * reanudar: si el proceso se corta, lo `en_curso` vuelve a `pendiente`
    y lo `listo` no se toca;
  * no pagar dos veces: un item cuya huella (datos + versión del prompt) no
    cambió no se vuelve a analizar;
  * vencimiento (TTL): los comercios cambian, los animales no; cada dominio
    decide cada cuánto se reanaliza.

Además guarda el aporte de cada fuente por separado (`aportes`); la ficha que se
analiza es la combinación de todas, según la prioridad de fuentes del dominio.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from typing import Iterable

from .modelos import Item, Registro

ESTADOS = ("pendiente", "en_curso", "en_lote", "listo", "error")

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
    creado_en REAL NOT NULL
);
"""


def huella(datos: dict, version_prompt: str) -> str:
    contenido = json.dumps(datos, sort_keys=True, ensure_ascii=False) + "\x00" + version_prompt
    return hashlib.sha256(contenido.encode()).hexdigest()


class Almacen:
    def __init__(self, ruta: str = ":memory:"):
        self.db = sqlite3.connect(ruta)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=NORMAL")
        self.db.executescript(_ESQUEMA)

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
        """Lo que quedó `en_curso` de una corrida cortada vuelve a la cola."""
        with self.db:
            return self.db.execute(
                "UPDATE items SET estado='pendiente' WHERE dominio=? AND estado='en_curso'", (dominio,)
            ).rowcount

    def vencer(self, dominio: str, ttl_dias: float | None) -> int:
        if ttl_dias is None:
            return 0
        limite = time.time() - ttl_dias * 86400
        with self.db:
            return self.db.execute(
                "UPDATE items SET estado='pendiente' WHERE dominio=? AND estado='listo' AND analizado_en < ?",
                (dominio, limite),
            ).rowcount

    def reintentar_errores(self, dominio: str) -> int:
        with self.db:
            return self.db.execute(
                "UPDATE items SET estado='pendiente', error=NULL WHERE dominio=? AND estado='error'", (dominio,)
            ).rowcount

    def pendientes(self, dominio: str, limite: int | None = None) -> list[Item]:
        consulta = "SELECT * FROM items WHERE dominio=? AND estado='pendiente' ORDER BY clave"
        parametros: tuple = (dominio,)
        if limite is not None:
            consulta += " LIMIT ?"
            parametros += (limite,)
        return [_a_item(f) for f in self.db.execute(consulta, parametros)]

    # --- transiciones ----------------------------------------------------

    def marcar(self, dominio: str, claves: Iterable[str], estado: str, lote_id: str | None = None) -> None:
        assert estado in ESTADOS
        with self.db:
            self.db.executemany(
                "UPDATE items SET estado=?, lote_id=?, actualizado_en=? WHERE dominio=? AND clave=?",
                [(estado, lote_id, time.time(), dominio, c) for c in claves],
            )

    def guardar_analisis(self, dominio: str, clave: str, analisis: dict, modelo: str) -> None:
        ahora = time.time()
        with self.db:
            self.db.execute(
                "UPDATE items SET estado='listo', analisis=?, modelo=?, error=NULL, lote_id=NULL,"
                " intentos=intentos+1, analizado_en=?, actualizado_en=? WHERE dominio=? AND clave=?",
                (_json(analisis), modelo, ahora, ahora, dominio, clave),
            )

    def guardar_error(self, dominio: str, clave: str, error: str) -> None:
        with self.db:
            self.db.execute(
                "UPDATE items SET estado='error', error=?, lote_id=NULL, intentos=intentos+1,"
                " actualizado_en=? WHERE dominio=? AND clave=?",
                (error[:2000], time.time(), dominio, clave),
            )

    # --- lotes (Message Batches) ----------------------------------------

    def registrar_lote(self, lote_id: str, dominio: str, cantidad: int) -> None:
        with self.db:
            self.db.execute(
                "INSERT INTO lotes (id, dominio, estado, cantidad, creado_en) VALUES (?, ?, 'abierto', ?, ?)",
                (lote_id, dominio, cantidad, time.time()),
            )

    def cerrar_lote(self, lote_id: str) -> None:
        with self.db:
            self.db.execute("UPDATE lotes SET estado='cerrado' WHERE id=?", (lote_id,))

    def lotes_abiertos(self, dominio: str) -> list[str]:
        filas = self.db.execute(
            "SELECT id FROM lotes WHERE dominio=? AND estado='abierto' ORDER BY creado_en", (dominio,)
        )
        return [f["id"] for f in filas]

    def items_del_lote(self, dominio: str, lote_id: str) -> list[Item]:
        filas = self.db.execute(
            "SELECT * FROM items WHERE dominio=? AND lote_id=? AND estado='en_lote'", (dominio, lote_id)
        )
        return [_a_item(f) for f in filas]

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


def _json(valor: object) -> str:
    return json.dumps(valor, ensure_ascii=False, sort_keys=True)


def _a_item(fila: sqlite3.Row) -> Item:
    return Item(
        dominio=fila["dominio"],
        clave=fila["clave"],
        datos=json.loads(fila["datos"]),
        fuentes=json.loads(fila["fuentes"]),
    )
