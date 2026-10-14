"""Recolector de Wikidata, con las respuestas de la API reproducidas sin red."""

from catalogo.core import pipeline
from catalogo.dominios import DOMINIOS
from catalogo.recolectores import wikidata
from test_pipeline import Registrador, analizar, hojas, ingerir_ejemplos

LEON = {
    "entities": {
        "Q140": {
            "claims": {
                "P225": [{"mainsnak": {"snaktype": "value", "datavalue": {"value": "Panthera leo"}}}],
                "P18": [{"mainsnak": {"snaktype": "value", "datavalue": {"value": "Lion waiting in Namibia.jpg"}}}],
                "P141": [{"mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q278113"}}}}],
                "P2067": [
                    {"mainsnak": {"snaktype": "somevalue"}},
                    {
                        "mainsnak": {
                            "snaktype": "value",
                            "datavalue": {"value": {"amount": "+190", "unit": "http://www.wikidata.org/entity/Q11570"}},
                        }
                    },
                ],
                "P2043": [
                    {
                        "mainsnak": {
                            "snaktype": "value",
                            "datavalue": {"value": {"amount": "+2.1", "unit": "http://www.wikidata.org/entity/Q11573"}},
                        }
                    }
                ],
            },
            "sitelinks": {"eswiki": {"title": "Panthera leo"}, "enwiki": {"title": "Lion"}},
        }
    }
}
GUERNICA = {
    "entities": {
        "Q175036": {
            "claims": {
                "P571": [
                    {"mainsnak": {"snaktype": "value", "datavalue": {"value": {"time": "+1937-06-04T00:00:00Z"}}}}
                ],
                "P18": [{"mainsnak": {"snaktype": "value", "datavalue": {"value": "Mural del Gernika.jpg"}}}],
            },
            "sitelinks": {"eswiki": {"title": "Guernica (cuadro)"}},
        }
    }
}


def obtener_falso(url):
    if "wbsearchentities" in url:
        if "search=Panthera+leo&" in url or "search=Le%C3%B3n&" in url:
            return {"search": [{"id": "Q140", "label": "león"}]}
        if "search=Guernica" in url:
            return {"search": [{"id": "Q175036"}]}
        return {"search": []}
    if "wbgetentities" in url:
        if "ids=Q140" in url:
            return LEON
        if "ids=Q175036" in url:
            return GUERNICA
        return {"entities": {"Q0": {"missing": ""}}}
    raise AssertionError(url)


def test_fila_de_un_animal_desde_wikidata():
    fila = wikidata.consultar("animales", "Panthera leo", obtener=obtener_falso)
    assert fila == {
        "qid": "Q140",
        "nombre_cientifico": "Panthera leo",
        "imagen_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Lion_waiting_in_Namibia.jpg?width=1200",
        "estado_conservacion": "VU",
        "peso": "190 kg",
        "largo": "2.1 m",
        "titulo_wikipedia": "Panthera leo",
    }
    datos = DOMINIOS["animales"].normalizar({**fila, "nombre": "León"})
    assert datos["peso_kg"] == 190.0 and datos["tamano_cm"] == 210.0 and datos["estado_conservacion"] == "VU"
    assert datos["qid"] == "Q140" and datos["titulo_wikipedia"] == "Panthera leo"


def test_fila_de_una_curiosidad_y_casos_sin_resultado():
    fila = wikidata.consultar("curiosidades", "Guernica", obtener=obtener_falso)
    assert fila["qid"] == "Q175036" and fila["anio"] == "1937" and fila["titulo_wikipedia"] == "Guernica (cuadro)"
    assert DOMINIOS["curiosidades"].normalizar({**fila, "titulo": "Guernica"})["anio"] == 1937
    assert wikidata.consultar("animales", "Bicho inexistente", obtener=obtener_falso) is None
    assert wikidata.consultar("comercios", "Kiosco", obtener=obtener_falso) is None
    assert wikidata._anio({"time": "-2560-00-00T00:00:00Z"}) == -2560
    assert (
        wikidata._cantidad({"amount": "+5", "unit": "http://www.wikidata.org/entity/Q999"}) is None
    )  # unidad desconocida


def test_recolectar_agrega_el_aporte_sin_cambiar_la_clave(almacen):
    ingerir_ejemplos(almacen, "animales")
    cuenta = pipeline.recolectar(almacen, DOMINIOS["animales"], obtener=obtener_falso, avisar=lambda m: None)
    assert cuenta == {"consultados": 23, "con_datos": 1, "sin_resultado": 22, "ya_tenian": 0, "errores": 0}
    por_clave = {i.clave: i for i in almacen.pendientes("animales")}
    leon = por_clave["panthera-leo"]  # misma clave que antes
    assert leon.datos["qid"] == "Q140" and leon.datos["estado_conservacion"] == "VU"
    assert leon.datos["imagen_url"].startswith("https://commons.wikimedia.org/")
    assert leon.datos["tamano_cm"] == 210.0  # Wikidata (prioridad 3) coincide con GBIF; Wikipedia decía 250
    assert set(leon.fuentes) == {"gbif", "wikipedia", "wikidata"}
    # Segunda pasada: ya tiene QID, no se vuelve a consultar.
    cuenta = pipeline.recolectar(almacen, DOMINIOS["animales"], obtener=obtener_falso, avisar=lambda m: None)
    assert cuenta["ya_tenian"] == 1 and cuenta["consultados"] == 22


def test_el_qid_unifica_en_el_catalogo_y_sirve_para_vigilar(almacen, tmp_path):
    ingerir_ejemplos(almacen, "animales")
    pipeline.recolectar(almacen, DOMINIOS["animales"], obtener=obtener_falso, avisar=lambda m: None)
    analizar(almacen, ["animales"], Registrador())
    catalogo, _ = pipeline.catalogar(almacen, DOMINIOS["animales"], tmp_path)
    felinos = catalogo["secciones"][0]["secciones"][0]["items"]
    [leon] = [f for f in felinos if f["clave"] == "q140"]
    assert leon["titulo"] == "León (Panthera leo)"
    [registro] = [r for r in almacen.analizados("animales") if r.item.clave == "panthera-leo"]
    assert DOMINIOS["animales"].titulo_wikipedia(registro) == "Panthera leo"


def test_recolectar_sigue_si_una_consulta_falla(almacen):
    ingerir_ejemplos(almacen, "curiosidades")

    def obtener(url):
        if "Guernica" in url:
            raise OSError("sin red")
        return {"search": []}

    cuenta = pipeline.recolectar(almacen, DOMINIOS["curiosidades"], obtener=obtener, avisar=lambda m: None)
    assert cuenta["errores"] == 1 and cuenta["consultados"] == 13 and cuenta["con_datos"] == 0
    assert hojas  # el import se usa en el otro test; evita el aviso del linter
