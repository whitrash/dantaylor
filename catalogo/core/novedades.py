"""Actualidad sin morder el anzuelo.

Un catálogo "al día" no es el que repite titulares: es el que cambia una ficha
cuando hay motivo. Acá se decide qué es noticia con reglas explicables, que se
pueden leer en el panel al lado de cada novedad:

1. **Cambio concreto.** Es noticia si cambia un campo de la ficha (el estado de
   conservación, si un comercio cerró, un récord superado). Una señal que no
   cambia nada es, como mucho, un motivo para verificar.
2. **Corroboración.** Dos fuentes independientes valen más que una; tres, más.
   "Independientes" quiere decir dominios distintos: diez notas que copian la
   misma agencia son una fuente.
3. **Jerarquía.** Un organismo oficial, una obra de referencia (Wikidata,
   Wikipedia con citas) o el sitio propio del comercio pesan más que un medio;
   un medio establecido más que un portal cualquiera; una granja de contenido
   resta.
4. **Persistencia.** Una edición en Wikipedia que sigue sin revertir a los
   días vale; una de hace una hora, no todavía. Un interés sostenido vale; un
   pico de visitas de un día es ruido.
5. **Titular.** Los rasgos de anzuelo ("no vas a creer", pregunta, mayúsculas,
   superlativos absolutos) restan, vengan de donde vengan.
6. **Recencia y redundancia.** Lo viejo reciclado no es actualidad; lo que la
   ficha ya dice no es novedad.

El resultado es un puntaje de 0 a 100 con sus motivos, y una categoría:
`novedad` (aplicar/mostrar), `a_confirmar` (reverificar con web) o `descartada`.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

UMBRAL_NOVEDAD = 60
UMBRAL_CONFIRMAR = 35
DIAS_RECIENTE = 90
DIAS_EDICION_FIRME = 2
DIAS_EDICION_MUY_FIRME = 7
DIAS_INTERES_SOSTENIDO = 3
PENALIZACION_POR_RASGO = 8
PENALIZACION_MAXIMA = 30

# Nivel 3: oficial o de referencia. Nivel 2: medios establecidos y sitios propios.
# Nivel 1: el resto. Nivel 0: granjas de contenido conocidas. Son listas cortas a
# propósito: se amplían en cada proyecto según lo que vaya apareciendo.
NIVEL_FUENTES = {
    3: (
        "wikipedia.org",
        "wikidata.org",
        "wikimedia.org",
        "iucnredlist.org",
        "gbif.org",
        "eol.org",
        "conicet.gov.ar",
        "doi.org",
        "springer.com",
        "nature.com",
        "science.org",
        "ncbi.nlm.nih.gov",
        "un.org",
        "who.int",
        "nasa.gov",
        "esa.int",
        "fifa.com",
        "olympics.com",
        "atptour.com",
        "wtatennis.com",
        "fia.com",
        "guinnessworldrecords.com",
        "unesco.org",
        "boe.es",
        "boletinoficial.gob.ar",
    ),
    2: (
        "bbc.com",
        "bbc.co.uk",
        "reuters.com",
        "apnews.com",
        "afp.com",
        "nytimes.com",
        "theguardian.com",
        "elpais.com",
        "dw.com",
        "lanacion.com.ar",
        "clarin.com",
        "infobae.com",
        "pagina12.com.ar",
        "ambito.com",
        "perfil.com",
        "telam.com.ar",
        "elmundo.es",
        "abc.es",
        "lavanguardia.com",
        "emol.com",
        "elcomercio.pe",
        "eluniversal.com.mx",
        "folha.uol.com.br",
    ),
    0: ("taringa.net", "buzzfeed.com", "upsocl.com", "viralnova.com", "clickhole.com"),
}
SUFIJOS_OFICIALES = (
    ".gob.ar",
    ".gov.ar",
    ".gob.mx",
    ".gob.es",
    ".gov",
    ".gob.cl",
    ".gub.uy",
    ".gov.br",
    ".edu",
    ".edu.ar",
)

CLICKBAIT = [
    (r"no (vas|podr[áa]s|van|vais) a creer", "apela a la incredulidad"),
    (r"\b(incre[íi]ble|impactante|sorprendente|escalofriante|brutal|tremend[oa]|alucinante)\b", "adjetivo de impacto"),
    (r"lo que (pas[óo]|hizo|dijo|encontr[óo]) (despu[ée]s|a continuaci[óo]n|luego)", "promesa de desenlace"),
    (r"(te sorprender[áa]|te va a sorprender|nadie esperaba|nadie imagin|no esperaba)", "promesa de sorpresa"),
    (r"\b(revelan|revel[óo]|el secreto|la verdad (detr[áa]s|sobre|oculta))\b", "revelación vaga"),
    (r"\b(viral|furor|pol[ée]mica|esc[áa]ndalo|bomba|estalla|estall[óo])\b", "palabra de alarma"),
    (r"\?\s*$", "titular en pregunta"),
    (r"!{2,}|\.{3,}\s*$", "puntuación enfática"),
    (r"\b\d+\s+(razones|cosas|datos|secretos|motivos|curiosidades)\b", "lista numérica"),
    (
        r"\b(el|la|los|las)\s+(\S+\s+){0,2}m[áa]s\s.{3,40}\sde (la historia|todos los tiempos|todo el mundo)",
        "superlativo absoluto",
    ),
    (r"\b(mir[áa]|mira|ver[áa]s|tienes que ver|hay que ver) (lo que|c[óo]mo|qu[ée]|esto)\b", "orden de mirar"),
    (r"\b(ya no es lo que era|adi[óo]s a|se acab[óo])\b", "dramatización"),
]
_VACIOS = (None, "", [], "NE", "desconocido", "Desconocida", "desconocida")


@dataclass
class Senal:
    """Una pieza de evidencia sobre un item."""

    tipo: str  # wikipedia_edicion | wikipedia_visitas | wikidata | oficial | sitio_propio | medio | ficha_cambio | otra
    fuente: str  # dominio o URL de donde salió
    cuando: float  # epoch
    titular: str = ""
    campo: str | None = None  # campo de la ficha que cambiaría; None = solo "hay movimiento"
    valor: object = None  # valor nuevo propuesto
    url: str = ""
    dias_vigente: float = 0.0  # ediciones: días sin revertir; visitas: días seguidos elevados
    nivel: int | None = None  # fuerza el nivel de la fuente (p. ej. sitio propio del comercio = 2)


@dataclass
class Veredicto:
    puntaje: int
    categoria: str  # novedad | a_confirmar | descartada
    motivos: list[str] = field(default_factory=list)
    campo: str | None = None
    valor: object = None
    fuentes: list[str] = field(default_factory=list)

    def como_dict(self) -> dict:
        return {
            "puntaje": self.puntaje,
            "categoria": self.categoria,
            "motivos": self.motivos,
            "campo": self.campo,
            "valor": self.valor,
            "fuentes": self.fuentes,
        }


def dominio_registrable(fuente: str) -> str:
    """'https://www.lanacion.com.ar/x/y' -> 'lanacion.com.ar'. Sirve para no contar
    dos veces la misma fuente y para clasificarla."""
    host = fuente.strip().lower()
    if "://" in host or host.startswith("www."):
        host = urlparse(host if "://" in host else "http://" + host).hostname or host
    host = host.split("/")[0]
    for prefijo in ("www.", "m.", "amp."):
        if host.startswith(prefijo):
            host = host[len(prefijo) :]
    partes = host.split(".")
    if len(partes) >= 3 and partes[-2] in ("com", "gob", "gov", "org", "net", "edu", "gub", "co"):
        return ".".join(partes[-3:])
    return ".".join(partes[-2:]) if len(partes) >= 2 else host


def nivel_fuente(fuente: str) -> int:
    dominio = dominio_registrable(fuente)
    for nivel, dominios in NIVEL_FUENTES.items():
        if dominio in dominios or any(dominio.endswith("." + d) for d in dominios):
            return nivel
    if dominio.endswith(SUFIJOS_OFICIALES):
        return 3
    return 1


def es_clickbait(titular: str) -> tuple[int, list[str]]:
    """Penalización (0-30) y motivos. No juzga la verdad del titular: juzga su forma."""
    if not titular:
        return 0, []
    texto = titular.strip()
    motivos = [motivo for patron, motivo in CLICKBAIT if re.search(patron, texto, re.I)]
    gritadas = [p for p in re.findall(r"\b[A-ZÁÉÍÓÚÑ]{4,}\b", texto)]
    if len(gritadas) >= 3:
        motivos.append("gritos en mayúsculas")
    return min(PENALIZACION_MAXIMA, PENALIZACION_POR_RASGO * len(motivos)), motivos


def _norm(valor: object) -> str:
    return (
        json.dumps(valor, sort_keys=True, ensure_ascii=False) if not isinstance(valor, str) else valor.strip().lower()
    )


def puntuar(senales: list[Senal], ficha_actual: dict | None = None, ahora: float | None = None) -> Veredicto:
    ahora = ahora or time.time()
    if not senales:
        return Veredicto(0, "descartada", ["sin señales"])
    motivos: list[str] = []
    puntaje = 0

    # 1. Cambio concreto.
    concretas = [s for s in senales if s.campo]
    campo = valor = None
    contradiccion = False
    if concretas:
        por_campo: dict[str, dict[str, int]] = {}
        for s in concretas:
            por_campo.setdefault(s.campo, {}).setdefault(_norm(s.valor), 0)
            por_campo[s.campo][_norm(s.valor)] += 1
        campo = max(por_campo, key=lambda c: sum(por_campo[c].values()))
        valor_norm = max(por_campo[campo], key=por_campo[campo].get)
        valor = next(s.valor for s in concretas if s.campo == campo and _norm(s.valor) == valor_norm)
        contradiccion = len(por_campo[campo]) > 1
        if ficha_actual is not None and _norm(ficha_actual.get(campo)) == valor_norm:
            return Veredicto(10, "descartada", [f'la ficha ya dice eso en "{campo}": no es novedad'], campo, valor)
        puntaje += 30
        motivos.append(f'cambia un campo concreto de la ficha ("{campo}")')
        if contradiccion:
            puntaje -= 20
            motivos.append(f'las fuentes no coinciden en el valor de "{campo}"')
    else:
        motivos.append(
            "ninguna señal cambia un campo de la ficha: solo hay movimiento; vale una verificación, no una noticia"
        )

    # 2. Corroboración.
    fuentes = sorted({dominio_registrable(s.fuente) for s in senales if s.fuente})
    if len(fuentes) >= 3:
        puntaje += 30
        motivos.append(f"{len(fuentes)} fuentes independientes")
    elif len(fuentes) == 2:
        puntaje += 20
        motivos.append("dos fuentes independientes")
    else:
        motivos.append("una sola fuente")

    # 3. Jerarquía.
    niveles = [s.nivel if s.nivel is not None else nivel_fuente(s.fuente) for s in senales if s.fuente]
    mejor = max(niveles) if niveles else 1
    if mejor == 3:
        puntaje += 20
        motivos.append("fuente oficial o de referencia")
    elif mejor == 2:
        puntaje += 12
        motivos.append("medio establecido o sitio propio")
    if niveles and min(niveles) == 0:
        puntaje -= 15
        motivos.append("alguna fuente es una granja de contenido")

    # 4. Persistencia.
    ediciones = [s for s in senales if s.tipo == "wikipedia_edicion"]
    if ediciones:
        firme = max(s.dias_vigente for s in ediciones)
        if firme >= DIAS_EDICION_MUY_FIRME:
            puntaje += 15
            motivos.append(f"edición en Wikipedia sin revertir desde hace {firme:.0f} días")
        elif firme >= DIAS_EDICION_FIRME:
            puntaje += 10
            motivos.append(f"edición en Wikipedia sin revertir desde hace {firme:.0f} días")
        else:
            motivos.append("edición en Wikipedia muy reciente: todavía puede revertirse")
    visitas = [s for s in senales if s.tipo == "wikipedia_visitas"]
    if visitas:
        sostenido = max(s.dias_vigente for s in visitas)
        if sostenido >= DIAS_INTERES_SOSTENIDO:
            puntaje += 10
            motivos.append(f"interés sostenido: {sostenido:.0f} días con visitas muy por encima de lo habitual")
        else:
            motivos.append("pico de visitas de uno o dos días: no cuenta por sí solo")

    # 5. Titular.
    penalizacion = 0
    rasgos: list[str] = []
    for titular in {s.titular for s in senales if s.titular}:
        p, m = es_clickbait(titular)
        penalizacion = min(PENALIZACION_MAXIMA, penalizacion + p)
        rasgos += [x for x in m if x not in rasgos]
    if penalizacion:
        puntaje -= penalizacion
        motivos.append("titular con rasgos de anzuelo: " + ", ".join(rasgos))

    # 6. Recencia.
    edad = (ahora - max(s.cuando for s in senales)) / 86400
    if edad > DIAS_RECIENTE:
        puntaje -= 15
        motivos.append(f"la señal más nueva tiene {edad:.0f} días: no es actualidad")

    puntaje = max(0, min(100, puntaje))
    if not concretas:
        categoria = "a_confirmar" if puntaje >= UMBRAL_CONFIRMAR else "descartada"
    elif puntaje >= UMBRAL_NOVEDAD and not contradiccion:
        categoria = "novedad"
    elif puntaje >= UMBRAL_CONFIRMAR:
        categoria = "a_confirmar"
    else:
        categoria = "descartada"
    return Veredicto(puntaje, categoria, motivos, campo, valor, fuentes)


def cambios_entre_fichas(campos: tuple[str, ...], vieja: dict, nueva: dict, ahora: float | None = None) -> list[Senal]:
    """Señales a partir de una ficha reanalizada: cada campo vigilado que cambió,
    respaldado por cada fuente que la nueva ficha cita."""
    ahora = ahora or time.time()
    fuentes = list(dict.fromkeys(nueva.get("fuentes_web") or []))
    senales: list[Senal] = []
    for campo in campos:
        antes, despues = vieja.get(campo), nueva.get(campo)
        if despues in _VACIOS or _norm(antes) == _norm(despues):
            continue
        if fuentes:
            senales += [Senal("ficha_cambio", f, ahora, campo=campo, valor=despues, url=f) for f in fuentes]
        else:
            senales.append(Senal("ficha_cambio", "modelo", ahora, campo=campo, valor=despues, nivel=1))
    return senales


def resumen_cambio(titulo: str, campo: str | None, antes: object, despues: object) -> str:
    if not campo:
        return f"{titulo}: hay movimiento reciente; conviene verificar"
    return f'{titulo}: "{campo}" pasa de {_mostrar(antes)} a {_mostrar(despues)}'


def _mostrar(valor: object) -> str:
    if valor in (None, "", []):
        return "(vacío)"
    return json.dumps(valor, ensure_ascii=False) if not isinstance(valor, str) else valor
