import asyncio
import time

import pytest

from catalogo.core.paralelo import ErrorFatal, LimitadorDeTasa, ejecutar_en_paralelo


class Reintentable(Exception):
    pass


def correr(coro):
    return asyncio.run(coro)


def test_respeta_concurrencia_y_procesa_todo():
    activos = maximo = 0
    terminados = []

    async def trabajo(x):
        nonlocal activos, maximo
        activos += 1
        maximo = max(maximo, activos)
        await asyncio.sleep(0.02)
        activos -= 1
        return x * 2

    inicio = time.monotonic()
    resumen = correr(
        ejecutar_en_paralelo(range(40), trabajo, concurrencia=8, al_terminar=lambda e, r: terminados.append(r))
    )
    assert resumen.ok == 40 and resumen.fallidos == 0
    assert sorted(terminados) == [x * 2 for x in range(40)]
    assert maximo == 8
    # 40 items x 20 ms en secuencia serían 0,8 s; con 8 trabajadores ~0,1 s
    assert time.monotonic() - inicio < 0.5


def test_acepta_generadores_perezosos():
    producidos = []

    def generador():
        for i in range(100):
            producidos.append(i)
            yield i

    async def trabajo(x):
        await asyncio.sleep(0)
        return x

    resumen = correr(ejecutar_en_paralelo(generador(), trabajo, concurrencia=4))
    assert resumen.ok == 100 and producidos == list(range(100))


def test_reintenta_errores_reintentables():
    intentos = {"n": 0}

    async def trabajo(x):
        intentos["n"] += 1
        if intentos["n"] < 3:
            raise Reintentable()
        return x

    resumen = correr(
        ejecutar_en_paralelo([1], trabajo, espera_base=0.001, es_reintentable=lambda e: isinstance(e, Reintentable))
    )
    assert resumen.ok == 1 and resumen.reintentos == 2


def test_no_reintenta_errores_del_item_y_avisa():
    fallas = []
    llamadas = {"n": 0}

    async def trabajo(x):
        llamadas["n"] += 1
        raise ValueError("dato roto")

    resumen = correr(
        ejecutar_en_paralelo(
            ["a"],
            trabajo,
            es_reintentable=lambda e: isinstance(e, Reintentable),
            al_fallar=lambda e, err: fallas.append((e, err)),
        )
    )
    assert resumen.fallidos == 1 and llamadas["n"] == 1
    assert fallas[0][0] == "a" and isinstance(fallas[0][1], ValueError)


def test_agota_reintentos():
    async def trabajo(x):
        raise Reintentable()

    resumen = correr(
        ejecutar_en_paralelo([1], trabajo, reintentos=2, espera_base=0.001, es_reintentable=lambda e: True)
    )
    assert resumen.fallidos == 1 and resumen.reintentos == 2


def test_limitador_espacia_arranques():
    async def trabajo(x):
        return x

    inicio = time.monotonic()
    correr(ejecutar_en_paralelo(range(5), trabajo, concurrencia=5, limitador=LimitadorDeTasa(por_minuto=600)))
    # 600/min = uno cada 0,1 s: el quinto arranca a los 0,4 s
    assert time.monotonic() - inicio >= 0.38


def test_pausa_global_frena_a_todos():
    async def escenario():
        limitador = LimitadorDeTasa()
        limitador.pausar(0.15)
        inicio = time.monotonic()
        await limitador.esperar()
        return time.monotonic() - inicio

    assert correr(escenario()) >= 0.14


def test_pausa_global_se_activa_con_el_error():
    pausas = []
    intentos = {"n": 0}

    async def trabajo(x):
        intentos["n"] += 1
        if intentos["n"] == 1:
            raise Reintentable()
        return x

    correr(
        ejecutar_en_paralelo(
            [1],
            trabajo,
            espera_base=0.001,
            es_reintentable=lambda e: True,
            pausa_global=lambda e: pausas.append(e) or 0.01,
        )
    )
    assert len(pausas) == 1


def test_error_fatal_corta_todo_sin_marcar_fallas():
    fallas = []
    iniciados = []

    async def trabajo(x):
        iniciados.append(x)
        await asyncio.sleep(0.01)
        raise PermissionError("sin credenciales")

    with pytest.raises(ErrorFatal, match="sin credenciales"):
        correr(
            ejecutar_en_paralelo(
                range(1000),
                trabajo,
                concurrencia=4,
                es_fatal=lambda e: isinstance(e, PermissionError),
                al_fallar=lambda e, err: fallas.append(e),
            )
        )
    assert fallas == [] and len(iniciados) == 4


def test_concurrencia_invalida():
    async def trabajo(x):
        return x

    with pytest.raises(ValueError):
        correr(ejecutar_en_paralelo([1], trabajo, concurrencia=0))
