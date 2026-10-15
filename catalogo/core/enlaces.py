"""Verificación de enlaces de productos y ofertas.

Una oferta no sirve si el enlace está muerto, lleva a la portada del sitio, a
otro producto, o el producto está sin stock. Antes de señalizar una oferta se
abre su enlace y se comprueba, en este orden:

1. que haya enlace y sea una URL http(s) válida;
2. que responda (sin 4xx/5xx, sin "página no encontrada" disfrazada de 200);
3. que no termine en la portada ni en un buscador del sitio (redirección
   silenciosa = el producto ya no existe);
4. que el producto aparezca en la página (las palabras importantes del nombre);
5. que haya stock (datos estructurados schema.org primero; si no, el texto);
6. que el precio de la página sea el anunciado (si la página lo muestra).

El resultado es una `Verificacion` con un estado único y los motivos en
palabras, para que el panel y el catálogo digan por qué una oferta no se
publica. Todo es determinista y sin modelo: cuesta una petición HTTP.

`obtener(url) -> Pagina` es inyectable, así se prueba sin red.
"""

from __future__ import annotations

import asyncio
import html
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Iterable

from .paralelo import LimitadorDeTasa, ejecutar_en_paralelo
from .texto import leer_numero, sin_acentos

USER_AGENT = "catalogos-motor/0.1 (+https://github.com/whitrash/dantaylor; verificacion de ofertas)"
MAX_BYTES = 2_000_000
TOLERANCIA_PRECIO = 0.02  # 2 %: redondeos y centavos
MINIMO_PALABRAS = 0.6  # fracción de palabras del producto que tienen que estar en la página

ESTADOS = (
    "ok",
    "sin_enlace",
    "invalido",
    "muerto",
    "portada",
    "no_aparece",
    "sin_stock",
    "precio_distinto",
    "no_verificado",
)
# Códigos que no prueban que el enlace esté muerto: el sitio bloquea robots, limita o está caído un rato.
HTTP_TRANSITORIOS = {401, 403, 405, 408, 425, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524}
DESCRIPCION = {
    "ok": "enlace vivo, producto en la página y con stock",
    "sin_enlace": "la oferta no trae enlace",
    "invalido": "el enlace no es una URL http(s)",
    "muerto": "el enlace no responde o la página no existe",
    "portada": "el enlace lleva a la portada o a un buscador, no al producto",
    "no_aparece": "el producto no aparece en la página",
    "sin_stock": "el producto está sin stock",
    "precio_distinto": "el precio de la página no es el anunciado",
    "no_verificado": "no se pudo comprobar ahora (red, bloqueo del sitio o caída momentánea)",
}

_RUTAS_PORTADA = {"", "/", "/index.html", "/index.php", "/home", "/inicio", "/es", "/ar", "/es-ar", "/tienda", "/shop"}
_RUTAS_BUSCADOR = re.compile(r"/(search|buscar|busqueda|catalogsearch|s)(/|$)|[?&](q|s|search|query|busqueda)=", re.I)
_NO_ENCONTRADA = re.compile(
    r"p[áa]gina no encontrada|no encontramos (la p[áa]gina|lo que buscas)|producto no encontrado"
    r"|este producto no existe|el producto (que buscas )?no existe|ya no est[áa] disponible|page not found"
    r"|error 404|\b404\b.{0,40}not found|producto no disponible en (este|el) momento",
    re.I,
)
_SIN_STOCK = re.compile(
    r"sin stock|agotado|no disponible|out of stock|sold out|sin existencias|no hay stock"
    r"|temporalmente sin|avis(a|á)me cuando (est[ée] disponible|haya stock)|producto no disponible",
    re.I,
)
_CON_STOCK = re.compile(
    r"agregar al carrito|a[ñn]adir al carrito|agregar al changuito|comprar ahora|add to cart|en stock|hay stock"
    r"|disponible para (env[íi]o|retiro)|\bcomprar\b",
    re.I,
)
_DISPONIBILIDAD_LD = re.compile(
    r'"availability"\s*:\s*"[^"]*?(InStock|OutOfStock|SoldOut|Discontinued|PreOrder|BackOrder|LimitedAvailability|OnlineOnly|InStoreOnly)"'
)
_DISPONIBILIDAD_MICRO = re.compile(
    r'itemprop="availability"[^>]*?(?:href|content)="[^"]*?(InStock|OutOfStock|SoldOut|Discontinued|PreOrder|BackOrder|LimitedAvailability|OnlineOnly|InStoreOnly)"'
)
_EN_STOCK_LD = {"InStock", "LimitedAvailability", "OnlineOnly", "InStoreOnly", "PreOrder", "BackOrder"}
_PRECIO_LD = re.compile(r'"(?:price|lowPrice|highPrice)"\s*:\s*"?(\d[\d.,]*)')
_PRECIO_TEXTO = re.compile(r"(?:\$|ARS|USD|US\$|€)\s?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)")
_ETIQUETAS = re.compile(r"<(script|style|noscript)\b.*?</\1>", re.I | re.S)
_TAG = re.compile(r"<[^>]+>")
_ESPACIOS = re.compile(r"\s+")
_TITULO = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_STOPWORDS = {
    "de", "del", "la", "el", "los", "las", "con", "sin", "por", "para", "en", "un", "una", "unos", "unas", "y", "o",
    "al", "a", "x", "pack", "oferta", "promo", "the", "of", "and",
}  # fmt: skip


@dataclass
class Pagina:
    estado: int
    url_final: str
    html: str


@dataclass
class Verificacion:
    url: str | None
    estado: str
    url_final: str | None = None
    http: int | None = None
    disponibilidad: str = "desconocida"  # en_stock | sin_stock | desconocida
    precio_pagina: float | None = None
    motivos: list[str] = field(default_factory=list)
    verificado_en: float = 0.0

    @property
    def senalizable(self) -> bool:
        return self.estado == "ok"

    @property
    def descripcion(self) -> str:
        return DESCRIPCION.get(self.estado, self.estado)

    def como_dict(self) -> dict:
        return {
            "url": self.url,
            "estado": self.estado,
            "url_final": self.url_final,
            "http": self.http,
            "disponibilidad": self.disponibilidad,
            "precio_pagina": self.precio_pagina,
            "motivos": self.motivos,
            "verificado_en": self.verificado_en,
            "senalizable": self.senalizable,
        }


# --- red ---------------------------------------------------------------------


def obtener_pagina(url: str, timeout: float = 20.0, reintentos: int = 1) -> Pagina:
    """GET con redirecciones; un 4xx/5xx vuelve como Pagina (no como excepción).
    Un corte de red se reintenta una vez antes de darse por vencido."""
    pedido = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "es-AR,es;q=0.9,en;q=0.5",
        },
    )
    for intento in range(reintentos + 1):
        try:
            with urllib.request.urlopen(pedido, timeout=timeout) as respuesta:
                return Pagina(
                    respuesta.status, respuesta.geturl(), _decodificar(respuesta.read(MAX_BYTES), respuesta.headers)
                )
        except urllib.error.HTTPError as error:
            cuerpo = b""
            try:
                cuerpo = error.read(MAX_BYTES)
            except Exception:  # noqa: BLE001 - el cuerpo del error es opcional
                pass
            return Pagina(error.code, error.geturl() or url, _decodificar(cuerpo, error.headers))
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            if intento >= reintentos:
                raise
            time.sleep(1.0)
    raise AssertionError("inalcanzable")


def _decodificar(cuerpo: bytes, cabeceras) -> str:
    charset = None
    try:
        charset = cabeceras.get_content_charset()
    except Exception:  # noqa: BLE001
        pass
    if not charset:
        coincidencia = re.search(rb'charset=["\']?([\w-]+)', cuerpo[:4000], re.I)
        charset = coincidencia.group(1).decode("ascii", "ignore") if coincidencia else "utf-8"
    try:
        return cuerpo.decode(charset, errors="replace")
    except LookupError:
        return cuerpo.decode("utf-8", errors="replace")


# --- análisis de la página --------------------------------------------------


def texto_visible(documento: str) -> str:
    sin_scripts = _ETIQUETAS.sub(" ", documento)
    plano = html.unescape(_TAG.sub(" ", sin_scripts))
    return _ESPACIOS.sub(" ", plano).strip()


def titulo_pagina(documento: str) -> str:
    coincidencia = _TITULO.search(documento)
    return _ESPACIOS.sub(" ", html.unescape(coincidencia.group(1))).strip() if coincidencia else ""


def palabras_clave(producto: str) -> list[str]:
    plano = sin_acentos(producto).lower()
    salida = []
    for palabra in re.findall(r"[a-z0-9]+", plano):
        if len(palabra) >= 3 and palabra not in _STOPWORDS and palabra not in salida:
            salida.append(palabra)
    return salida


def producto_aparece(producto: str, texto: str) -> tuple[bool, list[str]]:
    """¿Están en la página las palabras importantes del nombre? Devuelve
    (aparece, palabras que faltan)."""
    claves = palabras_clave(producto)
    if not claves:
        return True, []
    plano = " " + re.sub(r"[^a-z0-9]+", " ", sin_acentos(texto).lower()) + " "
    faltan = [p for p in claves if f" {p} " not in plano and p not in plano]
    presentes = len(claves) - len(faltan)
    return presentes >= max(1, round(len(claves) * MINIMO_PALABRAS)), faltan


def disponibilidad(documento: str, texto: str) -> tuple[str, str]:
    """('en_stock' | 'sin_stock' | 'desconocida', de dónde salió)."""
    for patron, origen in ((_DISPONIBILIDAD_LD, "datos estructurados"), (_DISPONIBILIDAD_MICRO, "microdatos")):
        valores = patron.findall(documento)
        if valores:
            if any(v in _EN_STOCK_LD for v in valores):
                return "en_stock", origen
            return "sin_stock", origen
    if _SIN_STOCK.search(texto):
        return "sin_stock", "texto de la página"
    if _CON_STOCK.search(texto):
        return "en_stock", "texto de la página"
    return "desconocida", ""


def precios_en_pagina(documento: str, texto: str) -> list[float]:
    """Precios estructurados primero (más fiables), después los del texto."""
    vistos: list[float] = []
    for crudo in _PRECIO_LD.findall(documento) + _PRECIO_TEXTO.findall(texto):
        valor = leer_numero(crudo)
        if valor is not None and valor > 0 and valor not in vistos:
            vistos.append(valor)
    return vistos


def es_portada(url_original: str, url_final: str) -> str | None:
    """Motivo si la URL final es una portada o un buscador; None si parece una página propia."""
    original = urllib.parse.urlparse(url_original)
    final = urllib.parse.urlparse(url_final or url_original)
    ruta_final = final.path.rstrip("/").lower() or ""
    if ruta_final in _RUTAS_PORTADA and not final.query:
        if (original.path.rstrip("/").lower() or "") in _RUTAS_PORTADA and not original.query:
            return "el enlace es la página principal del sitio, no la del producto"
        return f"redirige a la portada ({final.netloc})"
    if _RUTAS_BUSCADOR.search(final.path + ("?" + final.query if final.query else "")):
        return "el enlace lleva a un buscador del sitio, no a la página del producto"
    return None


# --- verificación -------------------------------------------------------------


def verificar_enlace(
    url: str | None,
    producto: str | None = None,
    precio: float | None = None,
    *,
    obtener: Callable[[str], Pagina] = obtener_pagina,
    ahora: float | None = None,
    tolerancia: float = TOLERANCIA_PRECIO,
) -> Verificacion:
    ahora = ahora or time.time()
    v = Verificacion(url, "ok", verificado_en=ahora)
    if not url or not str(url).strip():
        return _fallar(v, "sin_enlace", "la oferta no trae enlace")
    url = str(url).strip()
    v.url = url
    partes = urllib.parse.urlparse(url)
    if partes.scheme not in ("http", "https") or not partes.netloc:
        return _fallar(v, "invalido", f"no es una URL http(s): {url[:80]}")
    try:
        pagina = obtener(url)
    except Exception as error:  # noqa: BLE001
        if _es_dns(error):
            return _fallar(v, "muerto", f"el dominio no existe: {str(error)[:120]}")
        # Puede ser la red propia (proxy, wifi) o el sitio un rato: no prueba que el enlace esté muerto.
        return _fallar(v, "no_verificado", f"no responde: {type(error).__name__}: {str(error)[:120]}")
    v.http = pagina.estado
    v.url_final = pagina.url_final or url
    if pagina.estado in HTTP_TRANSITORIOS:
        return _fallar(v, "no_verificado", f"HTTP {pagina.estado}: el sitio no deja verificar ahora")
    if pagina.estado >= 400:
        return _fallar(v, "muerto", f"HTTP {pagina.estado}")
    documento = pagina.html or ""
    texto = texto_visible(documento)
    titulo = titulo_pagina(documento)
    if _NO_ENCONTRADA.search(titulo) or _NO_ENCONTRADA.search(texto[:3000]):
        return _fallar(v, "muerto", "la página dice que no existe (404 disfrazado de 200)")
    motivo_portada = es_portada(url, v.url_final)
    if motivo_portada:
        return _fallar(v, "portada", motivo_portada)
    if producto:
        aparece, faltan = producto_aparece(producto, titulo + " " + texto)
        if not aparece:
            return _fallar(v, "no_aparece", f"faltan en la página: {', '.join(faltan[:6])}")
    v.disponibilidad, origen = disponibilidad(documento, texto)
    if v.disponibilidad == "sin_stock":
        return _fallar(v, "sin_stock", f"sin stock según {origen}")
    if v.disponibilidad == "desconocida":
        v.motivos.append("la página no dice si hay stock")
    else:
        v.motivos.append(f"con stock según {origen}")
    precios = precios_en_pagina(documento, texto)
    if precio is not None and precio > 0:
        if not precios:
            v.motivos.append("la página no muestra un precio legible: precio sin verificar")
        else:
            cercano = min(precios, key=lambda p: abs(p - precio))
            v.precio_pagina = cercano
            if abs(cercano - precio) <= precio * tolerancia:
                v.motivos.append(f"precio confirmado en la página ({_dinero(cercano)})")
            else:
                return _fallar(v, "precio_distinto", f"en la página figura {_dinero(cercano)}, no {_dinero(precio)}")
    elif precios:
        v.precio_pagina = precios[0]
    return v


def _es_dns(error: BaseException) -> bool:
    razon = getattr(error, "reason", error)
    texto = f"{razon}".lower()
    return "name or service not known" in texto or "nodename nor servname" in texto or "getaddrinfo failed" in texto


def _fallar(v: Verificacion, estado: str, motivo: str) -> Verificacion:
    v.estado = estado
    v.motivos.append(motivo)
    return v


def _dinero(valor: float) -> str:
    return f"${valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


Pedido = tuple[object, str | None, str | None, float | None]  # (etiqueta, url, producto, precio)


async def verificar_enlaces(
    pedidos: Iterable[Pedido],
    *,
    concurrencia: int = 8,
    por_minuto: float | None = None,
    obtener: Callable[[str], Pagina] = obtener_pagina,
    al_terminar: Callable[[object, Verificacion], None] | None = None,
    ahora: float | None = None,
) -> dict[object, Verificacion]:
    """Verifica muchos enlaces a la vez (hilos para la red, mismo motor de
    paralelismo que el análisis). Devuelve {etiqueta: Verificacion}."""
    resultados: dict[object, Verificacion] = {}

    async def trabajo(pedido: Pedido) -> Verificacion:
        etiqueta, url, producto, precio = pedido
        return await asyncio.to_thread(verificar_enlace, url, producto, precio, obtener=obtener, ahora=ahora)

    def guardar(pedido: Pedido, verificacion: Verificacion) -> None:
        resultados[pedido[0]] = verificacion
        if al_terminar:
            al_terminar(pedido[0], verificacion)

    await ejecutar_en_paralelo(
        list(pedidos),
        trabajo,
        concurrencia=concurrencia,
        limitador=LimitadorDeTasa(por_minuto),
        reintentos=0,
        al_terminar=guardar,
    )
    return resultados
