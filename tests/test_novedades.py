"""Actualidad sin anzuelo: reglas explicables y verificables sin red."""

import json
import time

import pytest

from catalogo.core import novedades, pipeline
from catalogo.core.novedades import (
    Senal,
    cambios_entre_fichas,
    dominio_registrable,
    es_clickbait,
    nivel_fuente,
    puntuar,
)
from catalogo.dominios import DOMINIOS
from catalogo.recolectores import wikipedia
from test_pipeline import Registrador, analizar, ingerir_ejemplos

AHORA = 1_800_000_000.0
DIA = 86400


def senal(fuente, campo="estado_conservacion", valor="EN", dias=1, **kw):
    return Senal(kw.pop("tipo", "medio"), fuente, AHORA - dias * DIA, campo=campo, valor=valor, **kw)


def test_dominio_registrable_y_niveles():
    assert dominio_registrable("https://www.lanacion.com.ar/sociedad/x") == "lanacion.com.ar"
    assert dominio_registrable("m.es.wikipedia.org") == "wikipedia.org"
    assert dominio_registrable("https://amp.theguardian.com/x") == "theguardian.com"
    assert dominio_registrable("buenosaires.gob.ar/habilitaciones") == "buenosaires.gob.ar"
    assert nivel_fuente("https://www.iucnredlist.org/species/15951") == 3
    assert nivel_fuente("https://es.wikipedia.org/wiki/Panthera_leo") == 3
    assert nivel_fuente("https://buenosaires.gob.ar/x") == 3  # sufijo oficial
    assert nivel_fuente("https://www.clarin.com/x") == 2
    assert nivel_fuente("https://blogdeanimales.example/x") == 1
    assert nivel_fuente("https://www.taringa.net/x") == 0


@pytest.mark.parametrize(
    "titular, esperado",
    [
        ("La UICN reclasifica al león como vulnerable", []),
        ("No vas a creer lo que pasó después con este león", ["apela a la incredulidad", "promesa de desenlace"]),
        ("¿Está el león en peligro de extinción?", ["titular en pregunta"]),
        (
            "INCREÍBLE: el ANIMAL MÁS RÁPIDO de la historia!!!",
            ["adjetivo de impacto", "puntuación enfática", "superlativo absoluto", "gritos en mayúsculas"],
        ),
        ("7 razones por las que los pumas son únicos", ["lista numérica"]),
    ],
)
def test_es_clickbait_detecta_rasgos(titular, esperado):
    penalizacion, motivos = es_clickbait(titular)
    assert motivos == esperado
    assert penalizacion == min(30, 8 * len(esperado))


def test_sin_senales_se_descarta():
    assert puntuar([], ahora=AHORA).categoria == "descartada"


def test_cambio_corroborado_por_fuentes_de_referencia_es_novedad():
    senales = [
        senal("https://www.iucnredlist.org/species/15951", dias=3),
        senal("https://es.wikipedia.org/wiki/Panthera_leo", dias=2),
        senal("https://www.lanacion.com.ar/x", dias=1, titular="La UICN reclasifica al león"),
    ]
    v = puntuar(senales, {"estado_conservacion": "VU"}, ahora=AHORA)
    assert v.categoria == "novedad" and v.puntaje >= 60
    assert v.campo == "estado_conservacion" and v.valor == "EN"
    assert v.fuentes == ["iucnredlist.org", "lanacion.com.ar", "wikipedia.org"]
    assert "3 fuentes independientes" in v.motivos and "fuente oficial o de referencia" in v.motivos


def test_una_sola_fuente_floja_no_alcanza():
    v = puntuar([senal("https://blogdeanimales.example/x")], {"estado_conservacion": "VU"}, ahora=AHORA)
    assert v.categoria == "descartada" and "una sola fuente" in v.motivos


def test_mismo_dato_desde_dos_dominios_copiados_cuenta_como_una_fuente():
    senales = [senal("https://www.clarin.com/a"), senal("https://m.clarin.com/b"), senal("https://clarin.com/amp/c")]
    v = puntuar(senales, {"estado_conservacion": "VU"}, ahora=AHORA)
    assert "una sola fuente" in v.motivos and v.fuentes == ["clarin.com"]


def test_lo_que_la_ficha_ya_dice_no_es_novedad():
    senales = [senal("https://www.iucnredlist.org/x"), senal("https://es.wikipedia.org/x")]
    v = puntuar(senales, {"estado_conservacion": "EN"}, ahora=AHORA)
    assert v.categoria == "descartada" and v.puntaje == 10


def test_fuentes_que_se_contradicen_bajan_a_confirmar():
    senales = [
        senal("https://www.iucnredlist.org/x", valor="EN"),
        senal("https://es.wikipedia.org/x", valor="EN"),
        senal("https://www.lanacion.com.ar/x", valor="CR"),
    ]
    v = puntuar(senales, {"estado_conservacion": "VU"}, ahora=AHORA)
    assert v.categoria == "a_confirmar" and v.valor == "EN"
    assert any("no coinciden" in m for m in v.motivos)


def test_titular_anzuelo_y_granja_restan():
    serias = [senal("https://www.iucnredlist.org/x"), senal("https://es.wikipedia.org/x")]
    limpio = puntuar(serias, {"estado_conservacion": "VU"}, ahora=AHORA)
    con_anzuelo = puntuar(
        serias + [senal("https://www.taringa.net/x", titular="NO VAS A CREER lo que REVELAN sobre el LEÓN!!!")],
        {"estado_conservacion": "VU"},
        ahora=AHORA,
    )
    assert con_anzuelo.puntaje < limpio.puntaje
    assert any("anzuelo" in m for m in con_anzuelo.motivos) and any("granja" in m for m in con_anzuelo.motivos)


def test_lo_viejo_no_es_actualidad():
    senales = [senal("https://www.iucnredlist.org/x", dias=120), senal("https://es.wikipedia.org/x", dias=130)]
    v = puntuar(senales, {"estado_conservacion": "VU"}, ahora=AHORA)
    assert any("no es actualidad" in m for m in v.motivos)
    assert (
        v.puntaje
        == puntuar(
            [s.__class__(**{**s.__dict__, "cuando": AHORA}) for s in senales],
            {"estado_conservacion": "VU"},
            ahora=AHORA,
        ).puntaje
        - 15
    )


def test_solo_actividad_vale_una_verificacion_nunca_una_noticia():
    firme = Senal(
        "wikipedia_edicion", "es.wikipedia.org", AHORA - 8 * DIA, titular="actualizo estado UICN", dias_vigente=8
    )
    sostenido = Senal("wikipedia_visitas", "es.wikipedia.org", AHORA - DIA, dias_vigente=4)
    v = puntuar([firme, sostenido], {"estado_conservacion": "VU"}, ahora=AHORA)
    assert v.categoria == "a_confirmar" and v.campo is None
    assert any("solo hay movimiento" in m for m in v.motivos)

    reciente = Senal("wikipedia_edicion", "es.wikipedia.org", AHORA - 3600, dias_vigente=0.04)
    pico = Senal("wikipedia_visitas", "es.wikipedia.org", AHORA - DIA, dias_vigente=1)
    v = puntuar([reciente, pico], ahora=AHORA)
    assert v.categoria == "descartada"
    assert any("puede revertirse" in m for m in v.motivos) and any("pico de visitas" in m for m in v.motivos)


def test_cambios_entre_fichas():
    vieja = {"estado_conservacion": "VU", "nombre_cientifico": "Panthera leo", "dieta": "carnívoro"}
    nueva = {
        **vieja,
        "estado_conservacion": "EN",
        "dieta": "omnívoro",
        "fuentes_web": ["https://iucnredlist.org/a", "https://iucnredlist.org/a", "https://bbc.com/b"],
    }
    senales = cambios_entre_fichas(("estado_conservacion", "nombre_cientifico"), vieja, nueva, ahora=AHORA)
    assert [(s.campo, s.valor, s.fuente) for s in senales] == [
        ("estado_conservacion", "EN", "https://iucnredlist.org/a"),
        ("estado_conservacion", "EN", "https://bbc.com/b"),
    ]
    assert cambios_entre_fichas(("estado_conservacion",), vieja, {**vieja, "estado_conservacion": "NE"}) == []
    sin_fuentes = cambios_entre_fichas(("estado_conservacion",), vieja, {**vieja, "estado_conservacion": "EN"})
    assert len(sin_fuentes) == 1 and sin_fuentes[0].fuente == "modelo" and sin_fuentes[0].nivel == 1


# --- Wikipedia (sin red) -------------------------------------------------------


def respuestas_wikipedia(ahora=AHORA):
    def iso(dias):
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ahora - dias * DIA))

    revisiones = {
        "query": {
            "pages": [
                {
                    "title": "Panthera leo",
                    "revisions": [
                        {
                            "revid": 10,
                            "timestamp": iso(0.02),
                            "user": "Alguien",
                            "comment": "amplío",
                            "size": 50600,
                            "tags": [],
                        },
                        {
                            "revid": 9,
                            "timestamp": iso(1),
                            "user": "Vándalo",
                            "comment": "jaja",
                            "size": 50400,
                            "tags": ["mw-reverted"],
                        },
                        {
                            "revid": 8,
                            "timestamp": iso(1),
                            "user": "Patrullero",
                            "comment": "revierto",
                            "size": 50300,
                            "tags": ["mw-undo"],
                        },
                        {
                            "revid": 7,
                            "timestamp": iso(5),
                            "user": "Bibliotecario",
                            "comment": "estado UICN 2026",
                            "size": 50300,
                            "tags": [],
                        },
                        {
                            "revid": 6,
                            "timestamp": iso(6),
                            "user": "CorrectorBot",
                            "comment": "typo",
                            "size": 49900,
                            "tags": [],
                        },
                        {
                            "revid": 5,
                            "timestamp": iso(9),
                            "user": "Otro",
                            "comment": "enlace",
                            "size": 49880,
                            "tags": [],
                        },
                        {
                            "revid": 4,
                            "timestamp": iso(60),
                            "user": "Viejo",
                            "comment": "muy viejo",
                            "size": 49850,
                            "tags": [],
                        },
                    ],
                }
            ]
        }
    }
    visitas = {
        "items": [{"timestamp": f"202609{d:02d}00", "views": 300} for d in range(1, 28)]
        + [
            {"timestamp": "2026092800", "views": 2500},
            {"timestamp": "2026092900", "views": 3100},
            {"timestamp": "2026093000", "views": 2800},
        ]
    }

    def obtener(url):
        if "api.php" in url:
            return revisiones
        if "pageviews" in url:
            assert "Panthera_leo" in url
            return visitas
        raise AssertionError(url)

    return obtener


def test_senales_de_wikipedia_firmes_y_sostenidas():
    senales = wikipedia.senales("Panthera leo", obtener=respuestas_wikipedia(), ahora=AHORA)
    ediciones = [s for s in senales if s.tipo == "wikipedia_edicion"]
    # La de hace una hora cuenta pero no es firme; la revertida, la que revierte, el bot,
    # la chica (<50 bytes) y la vieja (60 días) quedan afuera.
    assert [(s.titular, round(s.dias_vigente)) for s in ediciones] == [("amplío", 0), ("estado UICN 2026", 5)]
    assert ediciones[1].url.endswith("diff=7")
    [visitas] = [s for s in senales if s.tipo == "wikipedia_visitas"]
    assert visitas.dias_vigente == 3 and "3100 visitas" in visitas.titular
    v = puntuar(senales, ahora=AHORA)
    assert v.categoria == "a_confirmar"


def test_articulo_inexistente_no_da_senales():
    obtener = lambda url: {"query": {"pages": [{"missing": True}]}} if "api.php" in url else {"items": []}  # noqa: E731
    assert wikipedia.senales("Nada", obtener=obtener, ahora=AHORA) == []


def test_vigilar_manda_a_verificar_lo_que_se_mueve(almacen):
    ingerir_ejemplos(almacen, "animales")
    analizar(almacen, ["animales"])
    assert almacen.estado("animales")["listo"] == 23
    activo = respuestas_wikipedia()
    quieto = lambda url: {"query": {"pages": [{"missing": True}]}} if "api.php" in url else {"items": []}  # noqa: E731

    def obtener(url):
        return activo(url) if "Panthera+leo" in url or "Panthera_leo" in url else quieto(url)

    cuenta = pipeline.vigilar(almacen, DOMINIOS["animales"], obtener=obtener, ahora=AHORA, avisar=lambda m: None)
    assert cuenta == {"revisados": 23, "a_verificar": 1, "sin_movimiento": 22, "errores": 0}
    assert [i.clave for i in almacen.para_verificar("animales")] == ["panthera-leo"]
    [novedad] = almacen.novedades("animales")
    assert novedad["categoria"] == "a_confirmar" and novedad["campo"] is None
    assert "León" in novedad["resumen"]
    # La próxima corrida reanaliza solo ese item, con web.
    registrador = Registrador()
    analizar(almacen, ["animales"], registrador)
    assert registrador.llamadas == [("animales", "panthera-leo", True)]


def test_vigilar_sigue_si_una_consulta_falla(almacen):
    ingerir_ejemplos(almacen, "curiosidades")
    analizar(almacen, ["curiosidades"])

    def obtener(url):
        if "Guernica" in url:
            raise OSError("sin red")
        return {"query": {"pages": [{"missing": True}]}} if "api.php" in url else {"items": []}

    cuenta = pipeline.vigilar(almacen, DOMINIOS["curiosidades"], obtener=obtener, ahora=AHORA, avisar=lambda m: None)
    assert cuenta["errores"] == 1 and cuenta["revisados"] == 13


def test_un_comercio_que_cierra_es_novedad_al_refrescar(almacen):
    ingerir_ejemplos(almacen, "comercios")
    analizar(almacen, ["comercios"])
    assert almacen.novedades() == []
    almacen.db.execute("UPDATE items SET analizado_en=?", (time.time() - 40 * DIA,))
    almacen.db.commit()

    def ajustar(item, ficha):
        if item.datos["nombre"] == "Kiosco 24":
            ficha["situacion"] = "cerrado"
            ficha["fuentes_web"] = [
                "https://buenosaires.gob.ar/habilitaciones/123",
                "https://www.lanacion.com.ar/kiosco",
            ]
        else:
            ficha["situacion"] = "desconocido"  # igual que antes: no es novedad

    analizar(almacen, ["comercios"], Registrador(ajustar=ajustar))
    [novedad] = almacen.novedades("comercios")
    assert novedad["categoria"] == "novedad" and novedad["puntaje"] == 70
    assert (
        novedad["campo"] == "situacion"
        and novedad["valor_nuevo"] == "cerrado"
        and novedad["valor_anterior"] == "desconocido"
    )
    assert novedad["resumen"] == 'Kiosco 24: "situacion" pasa de desconocido a cerrado'
    assert novedad["fuentes"] == ["buenosaires.gob.ar", "lanacion.com.ar"]
    assert any(e["tipo"] == "novedad" for e in almacen.eventos_recientes(100))
    assert almacen.marcar_novedad(novedad["id"], "vista") and almacen.novedades("comercios") == []
    assert almacen.novedades("comercios", estado=None)[0]["estado"] == "vista"
    assert json.dumps(novedad["motivos"], ensure_ascii=False)  # serializable para el panel


def test_resumen_del_panel_trae_novedades(almacen):
    ingerir_ejemplos(almacen, "comercios")
    v = novedades.puntuar(
        [
            senal("https://buenosaires.gob.ar/x", campo="situacion", valor="cerrado"),
            senal("https://www.clarin.com/y", campo="situacion", valor="cerrado"),
        ],
        {"situacion": "abierto"},
        ahora=AHORA,
    )
    almacen.registrar_novedad("comercios", "kiosco-24", "Kiosco 24", "Kiosco 24 cerró", v.como_dict(), "abierto")
    from catalogo.core import panel

    r = panel.resumen(almacen)
    assert r["novedades_total"] == 1 and r["novedades"][0]["resumen"] == "Kiosco 24 cerró"
    assert r["novedades"][0]["motivos"] and r["novedades"][0]["fuentes"] == ["buenosaires.gob.ar", "clarin.com"]
