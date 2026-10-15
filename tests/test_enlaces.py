"""Ofertas: ninguna se señala sin enlace vivo, a la página del producto, con stock y al precio anunciado."""

import asyncio
import json
import subprocess
import sys
import time

from catalogo.core import enlaces, pipeline
from catalogo.core.enlaces import Pagina, verificar_enlace
from catalogo.core.texto import leer_numero
from catalogo.dominios import DOMINIOS
from conftest import EJEMPLOS, RAIZ
from test_pipeline import analizar, ingerir_ejemplos

OFERTAS = DOMINIOS["ofertas"]


def pagina_producto(nombre, precio="1.250,00", disponibilidad="InStock", extra=""):
    ld = {
        "@type": "Product",
        "name": nombre,
        "offers": {
            "price": precio.replace(".", "").replace(",", "."),
            "availability": f"https://schema.org/{disponibilidad}",
        },
    }
    return f"""<html><head><title>{nombre} | Tienda</title>
<script type="application/ld+json">{json.dumps(ld)}</script></head>
<body><h1>{nombre}</h1><span class="precio">$ {precio}</span>{extra}<button>Agregar al carrito</button></body></html>"""


LECHE = "Leche entera La Serenísima 1 L"
WEB = {
    "https://t.example/p/leche": Pagina(200, "https://t.example/p/leche", pagina_producto(LECHE)),
    "https://t.example/p/agotada": Pagina(
        200, "https://t.example/p/agotada", pagina_producto(LECHE, disponibilidad="OutOfStock")
    ),
    "https://t.example/p/sin-ld": Pagina(
        200,
        "https://t.example/p/sin-ld",
        f"<title>{LECHE}</title><h1>{LECHE}</h1><p>$ 1.250</p><p>Producto agotado. Avisame cuando haya stock</p>",
    ),
    "https://t.example/p/404": Pagina(404, "https://t.example/p/404", "<h1>Not found</h1>"),
    "https://t.example/p/soft404": Pagina(
        200, "https://t.example/p/soft404", "<title>Tienda</title><h1>Página no encontrada</h1>"
    ),
    "https://t.example/p/vieja": Pagina(
        200, "https://t.example/", "<title>Tienda: ofertas de la semana</title><h1>Bienvenido</h1>"
    ),
    "https://t.example/p/otra-cosa": Pagina(
        200, "https://t.example/p/otra-cosa", pagina_producto("Yerba mate Playadito 1 kg", "4.890")
    ),
    "https://t.example/p/cara": Pagina(200, "https://t.example/p/cara", pagina_producto(LECHE, "1.590,00")),
    "https://t.example/p/bloqueada": Pagina(403, "https://t.example/p/bloqueada", "Access denied"),
    "https://t.example/p/redirige-buscar": Pagina(
        200, "https://t.example/buscar?q=leche", "<h1>Resultados para leche</h1>"
    ),
}


def obtener(url):
    if url == "https://caido.example/p/x":
        raise ConnectionError("conexión rechazada")
    return WEB[url]


def test_cada_motivo_para_no_senalar_una_oferta():
    casos = {
        "https://t.example/p/leche": "ok",
        "https://t.example/p/agotada": "sin_stock",
        "https://t.example/p/sin-ld": "sin_stock",
        "https://t.example/p/404": "muerto",
        "https://t.example/p/soft404": "muerto",
        "https://caido.example/p/x": "no_verificado",
        "https://t.example/p/bloqueada": "no_verificado",
        "https://t.example/p/vieja": "portada",
        "https://t.example/p/redirige-buscar": "portada",
        "https://t.example/p/otra-cosa": "no_aparece",
        "https://t.example/p/cara": "precio_distinto",
    }
    for url, esperado in casos.items():
        v = verificar_enlace(url, LECHE, 1250.0, obtener=obtener)
        assert v.estado == esperado, (url, v.estado, v.motivos)
        assert v.senalizable is (esperado == "ok") and v.motivos
    assert verificar_enlace(None, LECHE, 1250.0, obtener=obtener).estado == "sin_enlace"
    assert verificar_enlace("www.t.example/p/leche", LECHE, obtener=obtener).estado == "invalido"
    assert (
        verificar_enlace("https://t.example/", LECHE, obtener=lambda u: Pagina(200, u, "<h1>Hola</h1>")).estado
        == "portada"
    )


def test_ok_explica_por_que_y_lee_el_precio():
    v = verificar_enlace("https://t.example/p/leche", LECHE, 1250.0, obtener=obtener)
    assert v.disponibilidad == "en_stock" and v.precio_pagina == 1250.0 and v.http == 200
    assert "con stock según datos estructurados" in v.motivos
    assert any("precio confirmado" in m for m in v.motivos)
    cara = verificar_enlace("https://t.example/p/cara", LECHE, 1250.0, obtener=obtener)
    assert cara.precio_pagina == 1590.0 and "$1.590,00" in cara.motivos[-1]


def test_numeros_de_cualquier_pais():
    assert leer_numero("1.234,56") == 1234.56 and leer_numero("1,234.56") == 1234.56
    assert leer_numero("$ 1.250") == 1250 and leer_numero("12,5") == 12.5 and leer_numero("899") == 899
    assert leer_numero("") is None and leer_numero("gratis") is None


def test_ofertas_normaliza_clave_y_precio_por_kilo():
    datos = OFERTAS.normalizar(
        {
            "producto": LECHE,
            "comercio": "La Estrella",
            "precio": "$ 1.250,00",
            "link": "https://t.example/p/leche",
            "presentacion": "1 L",
        }
    )
    assert datos["precio"] == 1250.0 and datos["enlace"] == "https://t.example/p/leche"
    assert OFERTAS.clave(datos) == "la-estrella--leche-entera-la-serenisima-1-l"
    assert OFERTAS.clave({**datos, "ean": "7790742000019"}) == "la-estrella--7790742000019"


def preparar(almacen):
    ingerir_ejemplos(almacen, "ofertas")
    analizar(almacen, ["ofertas"])


def web_de_ejemplo(url):
    """Simula los sitios de los ejemplos: casi todo bien, con fallas puntuales."""
    filas = [f for a in sorted((EJEMPLOS / "ofertas").iterdir()) for f in pipeline.leer_filas(a)]
    por_url = {f["enlace"]: f for f in filas if f.get("enlace")}
    fila = por_url.get(url)
    if fila is None:
        return Pagina(200, url, "<title>Tienda</title><h1>Bienvenido</h1>")
    if "papel-higienico" in url:
        return Pagina(404, url, "")
    if "havanna" in url:
        return Pagina(200, url, pagina_producto(fila["producto"], fila["precio"], "OutOfStock"))
    if "aceite" in url:
        return Pagina(200, "https://www.laestrella.example/", "<title>La Estrella</title>")
    return Pagina(200, url, pagina_producto(fila["producto"], fila["precio"]))


def test_el_catalogo_solo_publica_ofertas_con_enlace_verificado(almacen, tmp_path):
    preparar(almacen)
    # Sin verificar: nada se publica.
    armado, _ = pipeline.catalogar(almacen, OFERTAS, tmp_path)
    assert armado["total"] == 0 and armado["no_publicadas"] == 14

    cuenta = asyncio.run(pipeline.verificar_enlaces(almacen, OFERTAS, obtener=web_de_ejemplo, avisar=lambda m: None))
    assert cuenta["verificados"] == 14
    assert {e: cuenta[e] for e in enlaces.ESTADOS if cuenta[e]} == {
        "ok": 8,
        "sin_enlace": 1,  # shampoo
        "portada": 3,  # jabón (portada), aceite (redirige), lapiceras (buscador)
        "muerto": 1,  # papel higiénico
        "sin_stock": 1,  # alfajores
    }
    armado, rutas = pipeline.catalogar(almacen, OFERTAS, tmp_path)
    publicadas = [f for f in _fichas(armado)]
    # El perro no tiene precio: enlace ok pero no se publica.
    assert armado["total"] == 7 and armado["no_publicadas"] == 7
    assert all(f["verificacion"]["senalizable"] and f["enlace"] and f["precio"] for f in publicadas)
    motivos = {r["titulo"].split(" · ")[0]: r["motivos"] for r in armado["revisar"] if r.get("no_publicada")}
    assert motivos["Alfajor Havanna x 6"][0].startswith("enlace sin_stock")
    assert motivos["Alimento para perro Pedigree 15 kg"] == ["sin precio"]
    leche = next(f for f in publicadas if f["datos"]["producto"].startswith("Leche"))
    assert leche["descuento_pct"] == 16 and leche["precio_unitario"] == 1250.0 and leche["unidad_precio"] == "L"
    md = rutas[1].read_text()
    assert "## No publicadas (sin enlace verificado)" in md and "[ver](https://www.laestrella.example/p/leche" in md
    assert "Havanna" not in md.split("## No publicadas")[0]


def test_una_oferta_que_se_cae_es_novedad_comprobada(almacen):
    preparar(almacen)
    asyncio.run(pipeline.verificar_enlaces(almacen, OFERTAS, obtener=web_de_ejemplo, avisar=lambda m: None))
    assert almacen.novedades("ofertas") == []  # la primera verificación no es "cambio"

    def ahora_sin_stock(url):
        pagina = web_de_ejemplo(url)
        return (
            Pagina(pagina.estado, pagina.url_final, pagina.html.replace("InStock", "OutOfStock"))
            if "yerba" in url
            else pagina
        )

    # Recién verificado: no se vuelve a abrir.
    assert (
        asyncio.run(pipeline.verificar_enlaces(almacen, OFERTAS, obtener=ahora_sin_stock, avisar=lambda m: None))[
            "verificados"
        ]
        == 0
    )
    cuenta = asyncio.run(
        pipeline.verificar_enlaces(almacen, OFERTAS, obtener=ahora_sin_stock, max_edad_horas=0, avisar=lambda m: None)
    )
    assert cuenta["sin_stock"] == 2 and cuenta["novedades"] == 1
    [novedad] = almacen.novedades("ofertas")
    assert "Yerba" in novedad["resumen"] and "ya no sirve" in novedad["resumen"]
    assert "comprobado directamente en la página del comercio" in novedad["motivos"]
    assert novedad["categoria"] in ("novedad", "a_confirmar")
    tipos = [e["tipo"] for e in almacen.eventos_recientes(100)]
    assert "enlace" in tipos and "novedad" in tipos


def test_verificacion_vieja_o_enlace_cambiado_no_se_publica(almacen, tmp_path):
    preparar(almacen)
    asyncio.run(pipeline.verificar_enlaces(almacen, OFERTAS, obtener=web_de_ejemplo, avisar=lambda m: None))
    almacen.db.execute("UPDATE enlaces SET verificado_en=?", (time.time() - 30 * 3600,))
    almacen.db.commit()
    armado, _ = pipeline.catalogar(almacen, OFERTAS, tmp_path)
    assert armado["total"] == 0
    assert any("verificado hace 30 h" in m for r in armado["revisar"] for m in r["motivos"])

    # Enlace nuevo para la yerba: se reverifica aunque la verificación sea reciente.
    asyncio.run(
        pipeline.verificar_enlaces(almacen, OFERTAS, obtener=web_de_ejemplo, max_edad_horas=0, avisar=lambda m: None)
    )
    pipeline.ingerir(
        almacen,
        OFERTAS,
        [
            {
                "producto": "Yerba mate Playadito 1 kg",
                "comercio": "Supermercado La Estrella",
                "precio": "4890",
                "enlace": "https://www.laestrella.example/p/yerba-nueva",
            }
        ],
        "supermercado",
    )
    pendientes = almacen.para_verificar_enlaces("ofertas", 24 * 3600)
    assert [i.datos["enlace"] for i in pendientes] == ["https://www.laestrella.example/p/yerba-nueva"]


def test_verificador_de_entregas_avisa_ofertas_sin_enlace():
    salida = subprocess.run(
        [sys.executable, str(RAIZ / "herramientas" / "verificar_recoleccion.py"), str(EJEMPLOS / "ofertas")],
        capture_output=True,
        text=True,
    )
    assert salida.returncode == 1
    assert "Shampoo Sedal 650 ml): sin enlace" in salida.stdout
    assert "Jabón en polvo Ala 3 kg): el enlace es la página principal" in salida.stdout
    assert "Alimento para perro Pedigree 15 kg): sin precio" in salida.stdout
    assert "buscador" in salida.stdout


def test_estado_del_panel_cuenta_enlaces(almacen):
    from catalogo.core import panel

    preparar(almacen)
    asyncio.run(pipeline.verificar_enlaces(almacen, OFERTAS, obtener=web_de_ejemplo, avisar=lambda m: None))
    r = panel.resumen(almacen)
    assert r["dominios"]["ofertas"]["enlaces"]["ok"] == 8 and r["dominios"]["ofertas"]["enlaces_sin_verificar"] == 0
    assert any(e["tipo"] == "enlace" for e in r["eventos"])


def _fichas(catalogo):
    def bajar(secciones):
        for s in secciones:
            yield from s.get("items", [])
            yield from bajar(s.get("secciones", []))

    return list(bajar(catalogo["secciones"]))


def test_una_caida_de_red_no_es_novedad_ni_se_publica(almacen, tmp_path):
    preparar(almacen)
    asyncio.run(pipeline.verificar_enlaces(almacen, OFERTAS, obtener=web_de_ejemplo, avisar=lambda m: None))

    def sin_red(url):
        raise OSError("Tunnel connection failed: 403 Forbidden")

    cuenta = asyncio.run(
        pipeline.verificar_enlaces(almacen, OFERTAS, obtener=sin_red, max_edad_horas=0, avisar=lambda m: None)
    )
    assert cuenta["no_verificado"] == 13 and cuenta["novedades"] == 0  # el shampoo sigue "sin_enlace"
    assert almacen.novedades("ofertas") == []
    armado, _ = pipeline.catalogar(almacen, OFERTAS, tmp_path)
    assert armado["total"] == 0  # sin comprobar hoy, no se señala

    def dns(url):
        raise OSError("[Errno -2] Name or service not known")

    assert verificar_enlace("https://no-existe.example/p", LECHE, obtener=dns).estado == "muerto"
