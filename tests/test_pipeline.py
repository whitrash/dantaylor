import asyncio
import json
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


class Registrador(AnalizadorSimulado):
    """Simulado que anota qué analizó, con o sin web, y deja retocar la ficha."""

    def __init__(self, ajustar=None, costo=0.0, **kw):
        super().__init__(**kw)
        self.llamadas = []  # (dominio, clave, con_web)
        self.ajustar = ajustar  # ajustar(item, ficha) modifica la ficha simulada
        self.costo = costo

    async def analizar(self, dominio, item, con_web=False):
        self.llamadas.append((dominio.nombre, item.clave, con_web))
        ficha, modelo, metricas = await super().analizar(dominio, item, con_web)
        if self.ajustar:
            self.ajustar(item, ficha)
        metricas["costo_usd"] = self.costo
        return ficha, modelo, metricas


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
    assert resultado["modo"] == "tiempo-real" and resultado["fases"] == 2
    # Enciclopedias: pasada sin web (todo queda a verificar porque lo simulado nunca es "alta")
    # y después con web. Comercios: una sola pasada, con web.
    assert resultado["dominios"] == {
        "animales": {"listos": 23, "verificar": 23, "errores": 0},
        "curiosidades": {"listos": 13, "verificar": 13, "errores": 0},
        "comercios": {"listos": 13, "verificar": 0, "errores": 0},
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


def test_dos_pasadas_solo_para_lo_dudoso(almacen):
    ingerir_ejemplos(almacen, "animales")

    # Lo que empieza con L sale con confianza alta y estado UICN conocido en la primera
    # pasada; el resto, media. El lobo queda "alta" pero con el campo volátil vacío
    # (NE): también va a verificar.
    def ajustar(item, ficha):
        if item.datos["nombre"].startswith("L"):
            ficha["confianza"] = "alta"
            ficha["estado_conservacion"] = "NE" if item.datos["nombre"] == "Lobo gris" else "LC"
        else:
            ficha["confianza"] = "media"

    registrador = Registrador(ajustar=ajustar)
    resultado = analizar(almacen, ["animales"], registrador)

    sin_web = {c for d, c, w in registrador.llamadas if not w}
    con_web = {c for d, c, w in registrador.llamadas if w}
    assert len(sin_web) == 23 and con_web == sin_web - {"panthera-leo", "leon-de-montana"}
    assert resultado["dominios"]["animales"] == {"listos": 23, "verificar": 21, "errores": 0}
    assert almacen.estado("animales")["listo"] == 23
    filas = {f["clave"]: f["con_web"] for f in almacen.db.execute("SELECT clave, con_web FROM items")}
    assert filas["panthera-leo"] == 0 and filas["orcinus-orca"] == 1


def test_sin_web_no_hace_segunda_pasada(almacen):
    ingerir_ejemplos(almacen, "animales", "comercios")
    registrador = Registrador()
    resultado = analizar(almacen, ["animales", "comercios"], registrador, web=False)
    assert all(not w for _, _, w in registrador.llamadas)
    assert resultado["fases"] == 1
    assert resultado["dominios"]["animales"] == {"listos": 23, "verificar": 0, "errores": 0}
    assert resultado["dominios"]["comercios"] == {"listos": 13, "verificar": 0, "errores": 0}


def test_segunda_corrida_no_vuelve_a_pagar(almacen):
    ingerir_ejemplos(almacen, "animales")
    analizar(almacen, ["animales"])
    ingerir_ejemplos(almacen, "animales")
    assert analizar(almacen, ["animales"])["dominios"]["animales"] == {"listos": 0, "verificar": 0, "errores": 0}


def test_solo_vence_el_dominio_con_ttl_y_lo_vencido_va_primero(almacen):
    ingerir_ejemplos(almacen, "animales", "comercios")
    analizar(almacen, ["animales", "comercios"])
    almacen.db.execute(
        "UPDATE items SET analizado_en=? WHERE clave IN ('kiosco-24--av-corrientes-1500', 'hiper-ahorro--av-rivadavia-5000')",
        (time.time() - 40 * 86400,),
    )
    pipeline.ingerir(almacen, DOMINIOS["comercios"], [{"nombre": "Almacén Nuevo", "direccion": "Calle 1 100"}], "web")
    registrador = Registrador()
    resultado = analizar(almacen, ["animales", "comercios"], registrador, concurrencia=1)
    assert resultado["dominios"]["animales"]["listos"] == 0  # sin TTL
    assert resultado["dominios"]["comercios"]["listos"] == 3  # 2 vencidos + 1 nuevo
    # Los vencidos (prioridad 1) van antes que el nuevo (prioridad 0).
    assert [c for _, c, _ in registrador.llamadas] == [
        "hiper-ahorro--av-rivadavia-5000",
        "kiosco-24--av-corrientes-1500",
        "almacen-nuevo--1-100",
    ]


def test_intercala_dominios_para_que_ninguno_espere_al_otro(almacen):
    ingerir_ejemplos(almacen, "animales", "comercios")
    registrador = Registrador()
    analizar(almacen, ["animales", "comercios"], registrador, concurrencia=1)
    assert [d for d, _, _ in registrador.llamadas[:4]] == ["animales", "comercios", "animales", "comercios"]


def test_limite_por_corrida(almacen):
    ingerir_ejemplos(almacen, "animales")
    assert analizar(almacen, ["animales"], limite=5)["dominios"]["animales"]["listos"] == 5
    assert almacen.estado("animales")["pendiente"] == 18


def test_tope_de_gasto_detiene_la_corrida_sin_perder_lo_hecho(almacen):
    ingerir_ejemplos(almacen, "animales")
    resultado = analizar(almacen, ["animales"], Registrador(costo=0.10), concurrencia=2, max_costo=0.5)
    assert resultado["detenido_por_costo"] is True
    hechos = resultado["dominios"]["animales"]["listos"] + resultado["dominios"]["animales"]["verificar"]
    assert 5 <= hechos <= 6  # el tope se alcanza con 5; el otro trabajador en vuelo termina el suyo
    assert almacen.estado("animales")["pendiente"] >= 16
    assert almacen.estado("animales")["en_curso"] == 0
    assert any(e["tipo"] == "tope_costo" for e in almacen.eventos_recientes(50))
    assert almacen.ultima_corrida()["costo_usd"] >= 0.5


def test_metricas_corrida_y_eventos_quedan_guardados(almacen):
    ingerir_ejemplos(almacen, "curiosidades")
    resultado = analizar(almacen, ["curiosidades"], Registrador(costo=0.02))
    assert almacen.metricas("curiosidades") == {
        "analizados": 13,
        "costo_usd": 0.26,
        "segundos_prom": 0.0,
        "busquedas": 13,  # la segunda pasada simulada cuenta una búsqueda por ficha
        "tokens_entrada": 0,
        "tokens_salida": 0,
        "confianza_baja": 0,
    }
    corrida = almacen.ultima_corrida()
    assert corrida["id"] == resultado["corrida_id"] and corrida["estado"] == "terminada"
    assert corrida["listos"] == 13 and corrida["costo_usd"] == 0.52 and corrida["fin"] is not None
    tipos = [e["tipo"] for e in almacen.eventos_recientes(200)]
    assert tipos[0] == "fin" and tipos.count("fase") == 2 and tipos.count("inicio") == 26
    assert tipos.count("verificar") == 13 and tipos.count("listo") == 13
    [evento] = [e for e in almacen.eventos_recientes(200) if e["tipo"] == "listo" and e["clave"] == "guernica"]
    assert evento["detalle"]["titulo"] == "Guernica" and evento["detalle"]["costo_usd"] == 0.02


def test_estado_json_se_escribe_para_otros_programas(almacen, tmp_path):
    ingerir_ejemplos(almacen, "comercios")
    ruta = tmp_path / "estado.json"
    analizar(almacen, ["comercios"], estado_json=ruta)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["estado"] == "inactivo" and datos["totales"]["listo"] == 13
    assert datos["dominios"]["comercios"]["avance"] == 1.0
    assert datos["corrida"]["estado"] == "terminada"


def test_importar_fichas_existentes_no_se_vuelven_a_analizar(almacen, tmp_path):
    animales = DOMINIOS["animales"]
    filas = [
        {
            "registro": {"nombre": "León", "nombre_cientifico": "Panthera leo"},
            "ficha": {
                "ruta": "Mamíferos > Felinos",
                "nombre_comun": "León",
                "nombre_cientifico": "Panthera leo",
                "descripcion": "Gran felino social de África.",
                "dieta": "carnívoro",
                "confianza": "alta",
            },
        },
        # Fila plana, como la exportaría un catálogo viejo: sin ruta, con una categoría en texto.
        {"nombre": "Zorro colorado", "categoria": "cánidos", "descripcion": "Zorro andino.", "peso": "7 kg"},
        {"sin_nombre": True},
    ]
    cuenta = pipeline.importar(almacen, animales, filas, fuente="catalogo-viejo")
    assert cuenta == {"filas": 3, "importadas": 2, "descartadas": 1}
    assert almacen.estado("animales")["listo"] == 2

    registrador = Registrador()
    analizar(almacen, ["animales"], registrador)
    assert registrador.llamadas == []  # nada que pagar

    catalogo, _ = pipeline.catalogar(almacen, animales, tmp_path)
    assert hojas(catalogo) == {
        "Mamíferos > Felinos": ["León (Panthera leo)"],
        "Mamíferos > Cánidos": ["Zorro colorado"],
    }
    [zorro] = catalogo["secciones"][0]["secciones"][1]["items"]
    assert zorro["modelo"] == "importado" and zorro["confianza"] == "media" and zorro["datos"]["peso_kg"] == 7.0


def test_paralelo_es_mas_rapido_que_secuencial(almacen):
    ingerir_ejemplos(almacen, "curiosidades")
    inicio = time.monotonic()
    analizar(almacen, ["curiosidades"], AnalizadorSimulado(latencia=0.05), concurrencia=13)
    # 13 items x 2 pasadas x 50 ms = 1,3 s en secuencia
    assert time.monotonic() - inicio < 0.6
