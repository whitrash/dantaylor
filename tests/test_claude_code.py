"""`claude -p` como analizador, con el subproceso reemplazado por un doble."""

import asyncio
import json
from pathlib import Path

import pytest

from catalogo.core import pipeline
from catalogo.core.analizador import (
    AnalizadorClaudeCode,
    ErrorCredenciales,
    ErrorDeAnalisis,
    LimiteDeUso,
    RespuestaIncompleta,
    RespuestaInvalida,
)
from catalogo.core.modelos import Item
from catalogo.core.paralelo import ErrorFatal
from catalogo.dominios import DOMINIOS
from falsos import EjecutorFalso, opcion, resultado_cli, responder_cli_simulando
from test_pipeline import ingerir_ejemplos

ANIMALES = DOMINIOS["animales"]
LEON = Item("animales", "panthera-leo", {"nombre": "León", "nombre_cientifico": "Panthera leo"}, ["wikipedia"])


def analizador(responder, tmp_path, **kw):
    return AnalizadorClaudeCode(carpeta=str(tmp_path), ejecutar=EjecutorFalso(responder), **kw)


def test_comando_restringe_herramientas_y_fija_el_esquema(tmp_path):
    a = analizador(responder_cli_simulando(ANIMALES), tmp_path, max_turnos=7, max_costo_item=0.25, esfuerzo="low")
    comando = a.comando(ANIMALES, LEON)
    assert comando[0] == "claude" and comando[1] == "-p" and comando[2].startswith("Registro a catalogar")
    assert json.loads(opcion(comando, "--json-schema")) == ANIMALES.esquema()
    assert opcion(comando, "--output-format") == "json"
    assert opcion(comando, "--tools") == "" and opcion(comando, "--allowedTools") == ""  # sin web: ninguna herramienta
    assert opcion(comando, "--permission-prompts") == "none"
    assert opcion(comando, "--max-turns") == "7" and opcion(comando, "--max-budget-usd") == "0.25"
    assert "--no-session-persistence" in comando and opcion(comando, "--effort") == "low"
    assert "--model" not in comando  # sin --modelo se usa el de la sesión de Claude Code
    assert "--bare" not in comando  # --bare no usa la cuenta
    sistema = Path(opcion(comando, "--system-prompt-file"))
    assert sistema.read_text(encoding="utf-8") == ANIMALES.instrucciones(False)

    con_web = a.comando(ANIMALES, LEON, con_web=True)
    assert opcion(con_web, "--tools") == "WebSearch,WebFetch"
    assert Path(opcion(con_web, "--system-prompt-file")).read_text(encoding="utf-8") == ANIMALES.instrucciones(True)

    con_modelo = analizador(responder_cli_simulando(ANIMALES), tmp_path, modelo="claude-opus-5-5").comando(
        ANIMALES, LEON
    )
    assert opcion(con_modelo, "--model") == "claude-opus-5-5"


def test_imagen_local_habilita_read_y_la_menciona(tmp_path):
    foto = tmp_path / "leon.jpg"
    foto.write_bytes(b"\xff\xd8")
    item = Item("animales", "panthera-leo", {"nombre": "León", "imagen_archivo": str(foto)}, ["fotos"])
    comando = analizador(responder_cli_simulando(ANIMALES), tmp_path).comando(ANIMALES, item, con_web=True)
    assert opcion(comando, "--tools") == "WebSearch,WebFetch,Read"
    assert str(foto) in comando[2] and "imagen_archivo" not in comando[2].split("\n\nImagen")[0]


def test_lee_structured_output_y_metricas(tmp_path):
    a = analizador(responder_cli_simulando(ANIMALES), tmp_path)
    ficha, modelo, metricas = asyncio.run(a.analizar(ANIMALES, LEON, con_web=True))
    assert ficha["ruta"] == "Mamíferos > Felinos" and modelo == "claude-opus-5-5"
    assert metricas == {
        "segundos": 12.0,
        "tokens_entrada": 2100,
        "tokens_salida": 500,
        "busquedas": 2,
        "costo_usd": 0.03,
    }


def test_sin_contador_del_servidor_cuenta_las_fuentes_citadas(tmp_path):
    ficha = {**ANIMALES.simular(LEON), "fuentes_web": ["https://a", "https://b", "https://a"]}
    a = analizador(lambda c: resultado_cli(ficha, busquedas=0), tmp_path)
    assert asyncio.run(a.analizar(ANIMALES, LEON, con_web=True))[2]["busquedas"] == 2


def test_sin_structured_output_toma_el_json_del_texto(tmp_path):
    ficha = ANIMALES.simular(LEON)
    texto = "```json\n" + json.dumps(ficha, ensure_ascii=False) + "\n```"
    a = analizador(lambda c: resultado_cli(None, result=texto), tmp_path)
    assert asyncio.run(a.analizar(ANIMALES, LEON))[0]["ruta"] == "Mamíferos > Felinos"

    a = analizador(lambda c: resultado_cli(None, result="no pude"), tmp_path)
    with pytest.raises(RespuestaInvalida):
        asyncio.run(a.analizar(ANIMALES, LEON))


def test_ruta_invalida_es_respuesta_invalida(tmp_path):
    ficha = {**ANIMALES.simular(LEON), "ruta": "Mamíferos > Dragones"}
    with pytest.raises(RespuestaInvalida):
        asyncio.run(analizador(lambda c: resultado_cli(ficha), tmp_path).analizar(ANIMALES, LEON))


@pytest.mark.parametrize(
    "respuesta, error, reintentable, fatal, pausa",
    [
        (
            resultado_cli(
                None, is_error=True, subtype="error_during_execution", result="Rate limit reached, try again later"
            ),
            LimiteDeUso,
            True,
            False,
            60.0,
        ),
        (
            resultado_cli(None, is_error=True, subtype="error", result="You've hit your usage limit"),
            LimiteDeUso,
            True,
            False,
            60.0,
        ),
        ((1, "", "Error: Not logged in. Run `claude auth login`."), ErrorCredenciales, False, True, None),
        (
            resultado_cli(None, is_error=True, subtype="error_max_turns", result=""),
            RespuestaIncompleta,
            False,
            False,
            None,
        ),
        (
            resultado_cli(None, is_error=True, subtype="error_max_budget_usd", result=""),
            RespuestaIncompleta,
            False,
            False,
            None,
        ),
        ((1, "", "algo raro pasó"), ErrorDeAnalisis, False, False, None),
        (asyncio.TimeoutError(), asyncio.TimeoutError, True, False, None),
        (FileNotFoundError("claude"), FileNotFoundError, False, True, None),
    ],
)
def test_clasificacion_de_fallas(tmp_path, respuesta, error, reintentable, fatal, pausa):
    a = analizador(lambda c: respuesta, tmp_path)
    with pytest.raises(error) as info:
        asyncio.run(a.analizar(ANIMALES, LEON))
    assert AnalizadorClaudeCode.es_reintentable(info.value) is reintentable
    assert AnalizadorClaudeCode.es_fatal(info.value) is fatal
    assert AnalizadorClaudeCode.pausa_global(info.value) == pausa


def test_corrida_completa_con_claude_code_hace_las_dos_pasadas(almacen, tmp_path):
    ingerir_ejemplos(almacen, "animales")
    ejecutor = EjecutorFalso(responder_cli_simulando(ANIMALES))
    a = AnalizadorClaudeCode(carpeta=str(tmp_path), ejecutar=ejecutor)
    resultado = asyncio.run(pipeline.analizar(almacen, [ANIMALES], a, concurrencia=4, avisar=lambda m: None))
    assert resultado["modo"] == "tiempo-real" and resultado["fases"] == 2
    assert resultado["dominios"]["animales"] == {"listos": 23, "verificar": 23, "errores": 0}
    herramientas = [opcion(c, "--tools") for c in ejecutor.comandos]
    assert herramientas.count("") == 23 and herramientas.count("WebSearch,WebFetch") == 23
    assert resultado["costo_usd"] == pytest.approx(46 * 0.03)
    assert almacen.metricas("animales")["busquedas"] == 46
    assert almacen.ultima_corrida()["analizador"] == "claude-code"


def test_limite_de_uso_pausa_y_reintenta(almacen, tmp_path):
    ingerir_ejemplos(almacen, "curiosidades")
    fallas = {"n": 0}

    def ajustes(datos, ficha, con_web):
        if datos["titulo"] == "Guernica" and fallas["n"] == 0:
            fallas["n"] += 1
            return resultado_cli(None, is_error=True, subtype="error", result="rate limit exceeded")
        return None

    class SinEspera(AnalizadorClaudeCode):
        @staticmethod
        def pausa_global(error):
            return 0.01

    a = SinEspera(
        carpeta=str(tmp_path), ejecutar=EjecutorFalso(responder_cli_simulando(DOMINIOS["curiosidades"], ajustes))
    )
    resultado = asyncio.run(pipeline.analizar(almacen, [DOMINIOS["curiosidades"]], a, web=False, avisar=lambda m: None))
    assert resultado["reintentos"] == 1 and resultado["dominios"]["curiosidades"]["listos"] == 13
    tipos = [e["tipo"] for e in almacen.eventos_recientes(100)]
    assert "pausa" in tipos and "reintento" in tipos


def test_sin_sesion_corta_la_corrida(almacen, tmp_path):
    ingerir_ejemplos(almacen, "curiosidades")
    a = analizador(lambda c: (1, "", "Not logged in"), tmp_path)
    with pytest.raises(ErrorFatal):
        asyncio.run(pipeline.analizar(almacen, [DOMINIOS["curiosidades"]], a, avisar=lambda m: None))
    assert almacen.errores("curiosidades") == []
