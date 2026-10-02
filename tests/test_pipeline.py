import asyncio
import time

from catalogo.core import pipeline
from catalogo.core.analizador import AnalizadorSimulado
from catalogo.dominios import DOMINIOS
from conftest import EJEMPLOS


def ingerir_ejemplos(almacen, *nombres):
    for nombre in nombres:
        for archivo in sorted((EJEMPLOS / nombre).iterdir()):
            pipeline.ingerir(almacen, DOMINIOS[nombre], pipeline.leer_filas(archivo), archivo.stem)


def analizar(almacen, nombres, analizador=None, **opciones):
    return asyncio.run(
        pipeline.analizar(
            almacen,
            [DOMINIOS[n] for n in nombres],
            analizador or AnalizadorSimulado(),
            avisar=lambda m: None,
            **opciones,
        )
    )


def hojas(catalogo):
    def bajar(secciones, camino):
        for s in secciones:
            ruta = camino + [s["nombre"]]
            if s.get("items"):
                yield " > ".join(ruta), [f["titulo"] for f in s["items"]]
            yield from bajar(s.get("secciones", []), ruta)

    return dict(bajar(catalogo["secciones"], []))


def test_ingreso_multifuente_con_prioridad(almacen):
    gbif = EJEMPLOS / "animales" / "gbif.jsonl"
    wiki = EJEMPLOS / "animales" / "wikipedia.csv"
    cuenta = pipeline.ingerir(almacen, DOMINIOS["animales"], pipeline.leer_filas(wiki), "wikipedia")
    assert cuenta["filas"] == 23 and cuenta["repetidas_en_archivo"] == 1 and cuenta["nuevos"] == 22
    cuenta = pipeline.ingerir(almacen, DOMINIOS["animales"], pipeline.leer_filas(gbif), "gbif")
    assert cuenta["nuevos"] == 1 and cuenta["actualizados"] == 3

    por_clave = {i.clave: i for i in almacen.pendientes("animales")}
    leon = por_clave["panthera-leo"]
    assert leon.datos["tamano_cm"] == 210.0  # gbif (prioridad 3) gana sobre wikipedia (2)
    assert leon.fuentes == ["gbif", "wikipedia"]
    assert por_clave["vultur-gryphus"].datos["nombre"] == "Cóndor de los Andes"

    # Volver a cargar la misma fuente no cambia nada ni reencola.
    cuenta = pipeline.ingerir(almacen, DOMINIOS["animales"], pipeline.leer_filas(gbif), "gbif")
    assert cuenta["sin_cambios"] == 4


def test_tres_dominios_en_una_corrida_y_catalogo_ordenado(almacen, tmp_path):
    ingerir_ejemplos(almacen, "animales", "curiosidades", "comercios")
    resultado = analizar(almacen, ["animales", "curiosidades", "comercios"], concurrencia=8)
    assert resultado["modo"] == "tiempo-real"
    assert resultado["dominios"] == {
        "animales": {"listos": 23, "errores": 0},
        "curiosidades": {"listos": 13, "errores": 0},
        "comercios": {"listos": 13, "errores": 0},
    }

    animales, rutas = pipeline.catalogar(almacen, DOMINIOS["animales"], tmp_path)
    assert all(r.exists() for r in rutas)
    secciones = hojas(animales)
    assert list(secciones)[0] == "Mamíferos > Felinos"
    assert secciones["Mamíferos > Cánidos"] == [
        "Aguará guazú (Chrysocyon brachyurus)",
        "Lobo gris (Canis lupus)",
        "Zorro colorado (Lycalopex culpaeus)",
    ]
    assert set(animales["facetas"]) == {"continentes", "dieta", "estado_conservacion"}

    curiosidades, _ = pipeline.catalogar(almacen, DOMINIOS["curiosidades"], tmp_path)
    assert hojas(curiosidades)["Arte > Arquitectura"] == ["Grandes pirámides de Guiza", "Torre Eiffel"]

    comercios, _ = pipeline.catalogar(almacen, DOMINIOS["comercios"], tmp_path)
    # Mismo local por web y por relevamiento = una sola ficha; otra sucursal = otra ficha.
    assert hojas(comercios)["Alimentos y bebidas > Supermercados"] == [
        "Supermercado La Estrella",  # Balvanera
        "Supermercado La Estrella",  # Belgrano
        "Hiper Ahorro",  # Caballito
    ]
    assert comercios["facetas"]["ciudad"]["Buenos Aires"] == 9


def test_segunda_corrida_no_vuelve_a_pagar(almacen):
    ingerir_ejemplos(almacen, "animales")
    analizar(almacen, ["animales"])
    ingerir_ejemplos(almacen, "animales")
    assert analizar(almacen, ["animales"])["dominios"]["animales"] == {"listos": 0, "errores": 0}


def test_solo_vence_el_dominio_con_ttl(almacen):
    ingerir_ejemplos(almacen, "animales", "comercios")
    analizar(almacen, ["animales", "comercios"])
    almacen.db.execute("UPDATE items SET analizado_en=?", (time.time() - 40 * 86400,))
    resultado = analizar(almacen, ["animales", "comercios"])
    assert resultado["dominios"]["animales"]["listos"] == 0  # sin TTL
    assert resultado["dominios"]["comercios"]["listos"] == 13  # TTL 30 días


def test_intercala_dominios_para_que_ninguno_espere_al_otro(almacen):
    ingerir_ejemplos(almacen, "animales", "comercios")
    orden = []

    class Registrador(AnalizadorSimulado):
        async def analizar(self, dominio, item):
            orden.append(dominio.nombre)
            return await super().analizar(dominio, item)

    analizar(almacen, ["animales", "comercios"], Registrador(), concurrencia=1)
    assert orden[:4] == ["animales", "comercios", "animales", "comercios"]


def test_limite_por_corrida(almacen):
    ingerir_ejemplos(almacen, "animales")
    assert analizar(almacen, ["animales"], limite=5)["dominios"]["animales"]["listos"] == 5
    assert almacen.estado("animales")["pendiente"] == 18


def test_paralelo_es_mas_rapido_que_secuencial(almacen):
    ingerir_ejemplos(almacen, "curiosidades")
    inicio = time.monotonic()
    analizar(almacen, ["curiosidades"], AnalizadorSimulado(latencia=0.05), concurrencia=13)
    # 13 items x 50 ms = 0,65 s en secuencia
    assert time.monotonic() - inicio < 0.4
