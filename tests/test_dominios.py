import pytest

from catalogo.core.modelos import Item
from catalogo.core.pipeline import leer_filas
from catalogo.dominios import DOMINIOS
from catalogo.dominios.animales import Animales
from catalogo.dominios.comercios import Comercios
from catalogo.dominios.curiosidades import Curiosidades
from conftest import EJEMPLOS

# Palabras de JSON Schema que la salida estructurada no admite.
NO_SOPORTADAS = {"minimum", "maximum", "minLength", "maxLength", "pattern", "minItems", "maxItems", "format"}


def recorrer(esquema):
    yield esquema
    for valor in esquema.get("properties", {}).values():
        yield from recorrer(valor)
    if "items" in esquema:
        yield from recorrer(esquema["items"])
    for variante in esquema.get("anyOf", []):
        yield from recorrer(variante)


@pytest.mark.parametrize("dominio", DOMINIOS.values(), ids=list(DOMINIOS))
def test_esquema_compatible_con_salida_estructurada(dominio):
    for nodo in recorrer(dominio.esquema()):
        assert not NO_SOPORTADAS & set(nodo), nodo
        if nodo.get("type") == "object":
            assert nodo["additionalProperties"] is False
            assert set(nodo["required"]) == set(nodo["properties"])
    assert dominio.esquema()["properties"]["ruta"]["enum"] == dominio.taxonomia.hojas()


@pytest.mark.parametrize("dominio", DOMINIOS.values(), ids=list(DOMINIOS))
def test_instrucciones_estables_para_la_cache(dominio):
    assert dominio.instrucciones() == dominio.instrucciones()
    assert dominio.taxonomia.describir() in dominio.instrucciones()


@pytest.mark.parametrize("dominio", DOMINIOS.values(), ids=list(DOMINIOS))
def test_simular_produce_fichas_validas_para_los_ejemplos(dominio):
    for archivo in sorted((EJEMPLOS / dominio.nombre).iterdir()):
        for fila in leer_filas(archivo):
            item = dominio.a_item(fila, archivo.stem)
            ficha = dominio.validar(dominio.simular(item))
            assert ficha["confianza"] in ("media", "baja")


def test_animales_normaliza_medidas_e_imagenes():
    dominio = Animales()
    datos = dominio.normalizar({"animal": "León", "peso": "190 kg", "largo": "2.5 m", "foto": "https://x/l.jpg"})
    assert datos == {"nombre": "León", "peso_kg": 190.0, "tamano_cm": 250.0, "imagen_url": "https://x/l.jpg"}
    assert dominio.normalizar({"nombre": "León", "imagen": "fotos/leon.jpg"})["imagen_archivo"] == "fotos/leon.jpg"
    assert dominio.normalizar({"otra_cosa": "x"}) == {}
    assert dominio.clave({"nombre": "León", "nombre_cientifico": "Panthera leo"}) == "panthera-leo"


def test_comercios_misma_sucursal_aunque_cambie_la_forma_de_escribir():
    dominio = Comercios()
    a = dominio.a_item({"nombre": "La Estrella", "direccion": "Av. Corrientes 1234"}, "web")
    b = dominio.a_item({"nombre": "LA ESTRELLA", "domicilio": "Avenida Corrientes 1234"}, "relevamiento")
    c = dominio.a_item({"nombre": "La Estrella", "direccion": "Av. Cabildo 2000"}, "web")
    assert a.clave == b.clave != c.clave
    assert dominio.normalizar({"nombre": "x", "tel": "(011) 4555-1234"})["telefono"] == "01145551234"


def test_curiosidades_extrae_el_anio():
    dominio = Curiosidades()
    assert dominio.normalizar({"titulo": "Pirámides", "año": "-2560"})["anio"] == -2560
    assert dominio.normalizar({"titulo": "Imprenta", "fecha": "c. 1440"})["anio"] == 1440


def test_fusionar_respeta_prioridad_de_fuentes():
    dominio = Animales()
    wiki = Item("animales", "panthera-leo", {"nombre": "León", "tamano_cm": 250.0, "notas": "rey"}, ["wikipedia"])
    gbif = Item("animales", "panthera-leo", {"nombre": "León", "tamano_cm": 210.0, "notas": ""}, ["gbif"])
    for fusion in (dominio.fusionar(wiki, gbif), dominio.fusionar(gbif, wiki)):
        assert fusion.datos == {"nombre": "León", "tamano_cm": 210.0, "notas": "rey"}
        assert set(fusion.fuentes) == {"wikipedia", "gbif"}


def test_contenido_pone_la_imagen_antes_del_texto():
    dominio = Animales()
    item = Item("animales", "leon", {"nombre": "León", "imagen_url": "https://x/l.jpg"}, ["w"])
    imagen, texto = dominio.contenido(item)
    assert imagen == {"type": "image", "source": {"type": "url", "url": "https://x/l.jpg"}}
    assert "imagen_url" not in texto["text"] and '"nombre": "León"' in texto["text"]


def test_validar_rechaza_rutas_inventadas():
    dominio = Animales()
    ficha = dominio.simular(Item("animales", "leon", {"nombre": "León"}))
    ficha["ruta"] = "Mamíferos > Dragones"
    with pytest.raises(ValueError, match="ruta"):
        dominio.validar(ficha)
