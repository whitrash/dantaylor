# -*- coding: utf-8 -*-
"""Diagramas propios del informe WINT (SVG en línea). Cada función devuelve un <svg> sin figcaption."""
import math

INK, NAVY, INDIGO, GOLD, AMBER = "#1B2033", "#121935", "#2F3E75", "#A87A22", "#E2A83A"
VERDE, ROJO, MUTED, SILVER = "#2F6F66", "#8E3B32", "#656A7C", "#8D96B3"
RULE = "#D9D1BE"
F_SANS, F_DISP, F_SERIF, F_MONO = "Jost", "Cormorant", "Garamond", "Plex"


def T(x, y, s, size=10, w=400, fill=INK, anchor="start", fam=F_SANS, ls=0, it=False, extra=""):
    st = ' font-style="italic"' if it else ""
    return (f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{size}" font-weight="{w}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}"{st} {extra}>{s}</text>')


def R(x, y, w, h, fill="#fff", stroke=RULE, sw=0.8, rx=4, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def L(x1, y1, x2, y2, stroke=RULE, sw=0.8, dash=None, marker=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}{m}/>'


def marker(id_, color):
    return (f'<marker id="{id_}" viewBox="0 0 10 10" refX="8.2" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            f'<path d="M0 1 L9 5 L0 9 z" fill="{color}"/></marker>')


def svg(w, h, body, defs=""):
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img">'
            f'<defs>{defs}</defs>{body}</svg>')


# ============================================================ 1. Estados de energía
def estados_energia():
    W, H = 560, 596
    d = marker("eL", INDIGO) + marker("eS", GOLD) + marker("eV", VERDE)
    b = []
    # contenedor S0
    b.append(R(8, 14, 164, 524, "#E8F1EE", VERDE, 1.1, 8))
    b.append(T(90, 36, "S0 · EQUIPO ENCENDIDO", 9.4, 600, VERDE, "middle", ls=1.6))
    b.append(T(90, 50, "G0 · trabajando", 9, 400, MUTED, "middle", it=True, fam=F_SERIF))
    # N1
    b.append(R(24, 154, 132, 82, "#fff", VERDE, 1.2, 7))
    b.append(T(90, 186, "Activo", 17, 600, NAVY, "middle", fam=F_DISP))
    b.append(T(90, 203, "pantalla encendida", 9.2, 400, MUTED, "middle"))
    b.append(T(90, 220, "WINT trabaja aquí", 9.2, 500, VERDE, "middle"))
    # N2
    b.append(R(24, 338, 132, 66, "#fff", VERDE, 1.0, 7))
    b.append(T(90, 366, "Pantalla apagada", 13.5, 600, NAVY, "middle", fam=F_DISP))
    b.append(T(90, 383, "sigue en S0", 9.2, 400, MUTED, "middle"))
    b.append(L(76, 236, 76, 336, VERDE, 1.1, marker="eV"))
    b.append(L(104, 336, 104, 238, VERDE, 1.1, marker="eV"))
    b.append(T(70, 276, "temporizador", 8.4, 400, MUTED, "end"))
    b.append(T(70, 288, "de pantalla", 8.4, 400, MUTED, "end"))
    b.append(T(110, 306, "entrada del", 8.4, 400, MUTED))
    b.append(T(110, 318, "usuario", 8.4, 400, MUTED))

    # filas de destinos
    rows = [64, 172, 280, 388, 496]
    nx, nw = 318, 234
    # nodos
    # R1 Reposo (dos alternativas)
    b.append(R(nx, 22, nw, 90, "#EEF0F8", INDIGO, 1.1, 7))
    b.append(T(nx + nw / 2, 42, "Reposo", 17, 600, NAVY, "middle", fam=F_DISP))
    b.append(R(nx + 10, 48, 105, 40, "#fff", INDIGO, 0.8, 5))
    b.append(T(nx + 62.5, 65, "Modern Standby", 10.4, 600, INDIGO, "middle"))
    b.append(T(nx + 62.5, 79, "S0 de bajo consumo", 8.6, 400, MUTED, "middle"))
    b.append(R(nx + 119, 48, 105, 40, "#fff", INDIGO, 0.8, 5))
    b.append(T(nx + 171.5, 65, "Suspensión", 10.4, 600, INDIGO, "middle"))
    b.append(T(nx + 171.5, 79, "S3 (equipos con S3)", 8.6, 400, MUTED, "middle"))
    b.append(T(nx + nw / 2, 100, "uno u otro, según el equipo · powercfg /a", 8.6, 400, MUTED, "middle", it=True, fam=F_SERIF))
    # R2 Hibernación
    b.append(R(nx, 142, nw, 60, "#E3E7F3", INDIGO, 1.1, 7))
    b.append(T(nx + nw / 2, 168, "Hibernación", 17, 600, NAVY, "middle", fam=F_DISP))
    b.append(T(nx + nw / 2, 188, "S4 · guarda la memoria en hiberfil.sys", 9.2, 400, MUTED, "middle"))
    # R3 Híbrido
    b.append(R(nx, 250, nw, 60, "#EEF0F6", SILVER, 1.1, 7))
    b.append(T(nx + nw / 2, 276, "Apagado híbrido", 17, 600, NAVY, "middle", fam=F_DISP))
    b.append(T(nx + nw / 2, 296, "Inicio rápido · no es un arranque en frío", 9.2, 400, MUTED, "middle"))
    # R4 Apagado total
    b.append(R(nx, 358, nw, 60, "#EEF0F6", SILVER, 1.1, 7))
    b.append(T(nx + nw / 2, 384, "Apagado total", 17, 600, NAVY, "middle", fam=F_DISP))
    b.append(T(nx + nw / 2, 404, "S5 · G2 (G3 si se corta la corriente)", 9.2, 400, MUTED, "middle"))
    # R5 Reinicio
    b.append(R(nx, 466, nw, 60, "#F8F1DF", GOLD, 1.1, 7))
    b.append(T(nx + nw / 2, 492, "Reinicio", 17, 600, NAVY, "middle", fam=F_DISP))
    b.append(T(nx + nw / 2, 512, "ciclo de arranque completo", 9.2, 400, MUTED, "middle"))

    # flechas ida (Luna, índigo) y vuelta (Sol, dorado)
    ex0, ex1 = 172, nx
    spec = [
        (64, ("Suspender · tapa", "inactividad"), "psshutdown -d", ("tecla · botón · WoL", "temporizador (solo S3)")),
        (172, ("Hibernar", ""), "shutdown /h", ("botón de encendido", "")),
        (280, ("Apagar con Inicio rápido", ""), "shutdown /s /hybrid", ("botón de encendido", "reanuda la sesión del kernel")),
        (388, ("Apagar sin Inicio rápido", ""), "shutdown /s /t 0", ("botón · alarma RTC", "WoL · vuelta de la luz")),
        (496, ("Reiniciar", ""), "shutdown /r /t 0", ("fin del arranque", "completo")),
    ]
    for cy, (o1, o2), cmd, (v1, v2) in spec:
        b.append(L(ex0, cy - 6, ex1 - 2, cy - 6, INDIGO, 1.3, marker="eL"))
        b.append(T(ex0 + 5, cy - 36, o1, 8.8, 500, INDIGO))
        if o2:
            b.append(T(ex0 + 5, cy - 25, o2, 8.8, 500, INDIGO))
            b.append(T(ex0 + 5, cy - 13, cmd, 7.9, 500, NAVY, fam=F_MONO))
        else:
            b.append(T(ex0 + 5, cy - 24, cmd, 7.9, 500, NAVY, fam=F_MONO))
        b.append(L(ex1 - 2, cy + 10, ex0 + 1, cy + 10, GOLD, 1.3, marker="eS"))
        b.append(T(ex0 + 5, cy + 24, v1, 8.8, 500, GOLD))
        if v2:
            b.append(T(ex0 + 5, cy + 35, v2, 8.8, 500, GOLD))
    # flecha reposo -> hibernación
    b.append(L(nx + nw - 22, 113, nx + nw - 22, 141, INDIGO, 1.1, dash="3 2", marker="eL"))
    b.append(T(nx + nw - 28, 130, "«Hibernar tras…»", 8.4, 400, MUTED, "end", it=True, fam=F_SERIF))
    # leyenda
    ly = 560
    b.append(L(14, ly - 8, 546, ly - 8, RULE, 0.6))
    b.append(L(18, ly + 6, 44, ly + 6, INDIGO, 1.4, marker="eL"))
    b.append(T(50, ly + 9.5, "Luna · bajar (WINT lo dispara)", 9.2, 600, INDIGO))
    b.append(L(210, ly + 6, 236, ly + 6, GOLD, 1.4, marker="eS"))
    b.append(T(242, ly + 9.5, "Sol · subir (evento de despertar)", 9.2, 600, GOLD))
    b.append(T(14, ly + 28, "Hibernación, apagado híbrido y apagado total se ven iguales desde afuera; se distinguen por lo que ocurre en el próximo arranque.", 8.8, 400, MUTED, it=True, fam=F_SERIF))
    return svg(W, H, "".join(b), d)


# ============================================================ 2. El día de WINT (anillo de 24 h)
def anillo_dia():
    W, H = 560, 400
    cx, cy, Rr = 160, 200, 104
    d = marker("aL", INDIGO)
    b = []

    def pt(h, r):
        a = math.radians(h * 15 - 90)
        return cx + r * math.cos(a), cy + r * math.sin(a)

    def arco(h0, h1, r, color, w, op=1):
        x0, y0 = pt(h0, r)
        x1, y1 = pt(h1, r)
        span = (h1 - h0) % 24
        grande = 1 if span > 12 else 0
        return (f'<path d="M{x0:.1f} {y0:.1f} A{r} {r} 0 {grande} 1 {x1:.1f} {y1:.1f}" fill="none" '
                f'stroke="{color}" stroke-width="{w}" opacity="{op}" stroke-linecap="butt"/>')

    b.append(f'<circle cx="{cx}" cy="{cy}" r="{Rr+24}" fill="none" stroke="{RULE}" stroke-width="0.6"/>')
    b.append(f'<circle cx="{cx}" cy="{cy}" r="{Rr-24}" fill="none" stroke="{RULE}" stroke-width="0.6"/>')
    b.append(arco(7.5, 23.5, Rr, "#E9C777", 18))
    b.append(arco(23.5, 7.5, Rr, "#B7BEE0", 18))
    for h in range(24):
        x0, y0 = pt(h, Rr + 11)
        x1, y1 = pt(h, Rr + (19 if h % 6 == 0 else 15))
        b.append(L(f"{x0:.1f}", f"{y0:.1f}", f"{x1:.1f}", f"{y1:.1f}", INDIGO if h % 6 == 0 else SILVER, 1.0 if h % 6 == 0 else 0.6))
    for h, s_ in [(0, "00"), (6, "06"), (12, "12"), (18, "18")]:
        x, y = pt(h, Rr + 30)
        b.append(T(f"{x:.1f}", f"{y+3.5:.1f}", s_, 10, 600, INDIGO, "middle"))
    # ventanas solares (solo tema y luz)
    b.append(arco(5 + 37 / 60, 8, Rr + 38, AMBER, 3.0, 0.95))
    b.append(arco(17 + 50 / 60, 20 + 5 / 60, Rr + 38, INDIGO, 3.0, 0.95))
    b.append(T(cx, cy - 4, "Un día", 20, 600, NAVY, "middle", fam=F_DISP))
    b.append(T(cx, cy + 14, "de WINT", 20, 600, NAVY, "middle", fam=F_DISP))
    # hitos
    for h, col, lab, dx, dy, anc in [(7.5, GOLD, "07:30 · Sol", 12, 6, "start"), (23.5, INDIGO, "23:30 · Luna", -12, -6, "end")]:
        x, y = pt(h, Rr)
        b.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5.2" fill="#fff" stroke="{col}" stroke-width="1.7"/>')
    x, y = pt(15, Rr)
    b.append(T(f"{x:.1f}", f"{y+4:.1f}", "SOL", 11.5, 600, "#6B4C0F", "middle", ls=3))
    x, y = pt(3.5, Rr)
    b.append(T(f"{x:.1f}", f"{y+4:.1f}", "LUNA", 11.5, 600, "#27346A", "middle", ls=3))
    x, y = pt(7.5, Rr - 40)
    b.append(T(f"{x:.1f}", f"{y+3:.1f}", "07:30", 9.4, 600, GOLD, "middle"))
    x, y = pt(23.5, Rr - 40)
    b.append(T(f"{x:.1f}", f"{y+3:.1f}", "23:30", 9.4, 600, INDIGO, "middle"))

    ex = 322

    def bloque(y0, titulo, color, puntos, punto_col):
        out = [T(ex, y0, titulo, 9.6, 600, color, ls=1.6)]
        y = y0 + 19
        for p in puntos:
            out.append(f'<circle cx="{ex+4}" cy="{y-3}" r="2.3" fill="{punto_col}"/>')
            out.append(T(ex + 14, y, p, 9.6, 400, INK))
            y += 16.5
        return "".join(out), y

    o, y = bloque(26, "SOL · 07:30", GOLD, ["Despierta, o ya está despierto", "Comprueba la red, con tiempo máximo", "Pasada diaria del Detector", "Resumen de ofertas verificadas", "Libera el pedido de energía"], AMBER)
    b.append(o)
    b.append(L(ex, y - 6, 548, y - 6, RULE, 0.6))
    o, y = bloque(y + 12, "DURANTE EL DÍA", MUTED, ["Reglas con avisos con presupuesto", "Sin preguntas ni conversación", "Digest, no ráfagas"], SILVER)
    b.append(o)
    b.append(L(ex, y - 6, 548, y - 6, RULE, 0.6))
    o, y = bloque(y + 12, "LUNA · 22:45 A 23:30", INDIGO, ["Pausa el Detector", "Pasada de cierre: SEPA, IPC, dólar", "Copia de la base y verificación", "Cuenta atrás con aborto posible", "Suspender · Hibernar · Apagar"], "#7783BD")
    b.append(o)
    b.append(L(ex, y - 6, 548, y - 6, RULE, 0.6))
    b.append(f'<rect x="{ex}" y="{y+6}" width="14" height="3.4" fill="{AMBER}"/>')
    b.append(T(ex + 20, y + 11, "Amanecer en Buenos Aires: 05:37 a 08:00", 8.8, 400, MUTED))
    b.append(f'<rect x="{ex}" y="{y+20}" width="14" height="3.4" fill="{INDIGO}"/>')
    b.append(T(ex + 20, y + 25, "Atardecer: 17:50 a 20:05 (solo tema y luz)", 8.8, 400, MUTED))
    b.append(T(14, H - 8, "Horas de ejemplo: son configurables. La hora solar sirve para el tema y la luz, no para suspender la PC.", 8.8, 400, MUTED, it=True, fam=F_SERIF))
    return svg(W, H, "".join(b), d)

# ============================================================ 3. Capas de WINT
def capas_wint():
    W, H = 560, 560
    d = marker("cA", INDIGO) + marker("cG", GOLD)
    b = []

    def banda(y, h, titulo, fill, stroke, items, tcol=NAVY, item_fill="#fff"):
        out = [R(10, y, 540, h, fill, stroke, 1.0, 8)]
        out.append(T(22, y + 17, titulo, 9, 600, tcol, ls=1.8))
        n = len(items)
        gap = 8
        iw = (540 - 24 - gap * (n - 1)) / n
        for i, (a, c, col) in enumerate(items):
            x = 22 + i * (iw + gap)
            out.append(R(round(x, 1), y + 28, round(iw, 1), h - 38, item_fill, col, 1.0, 5))
            out.append(T(round(x + iw / 2, 1), y + 28 + (h - 38) / 2 - (2 if c else -3), a, 12.5, 600, NAVY, "middle", fam=F_DISP))
            if c:
                out.append(T(round(x + iw / 2, 1), y + 28 + (h - 38) / 2 + 11, c, 8.6, 400, MUTED, "middle"))
        return "".join(out)

    b.append(banda(8, 84, "CLIENTES · SOLO MUESTRAN Y AVISAN", "#F4F1E8", RULE, [
        ("Bandeja", "Windows · estado por color", SILVER), ("Panel web", "PWA instalable", SILVER),
        ("Android", "PWA, luego app nativa", SILVER), ("Avisos", "ntfy · toast", SILVER)]))
    b.append(L(280, 94, 280, 110, INDIGO, 1.2, marker="cA"))
    b.append(T(290, 105, "HTTP local + eventos (SSE) · Tailscale para el teléfono", 8.8, 400, MUTED, it=True, fam=F_SERIF))
    b.append(banda(112, 124, "NÚCLEO WINT · SIN VENTANA, SIN IA EN EL BUCLE", "#E9ECF6", INDIGO, [
        ("Planificador", "Task Scheduler + APScheduler", INDIGO), ("Reglas", "YAML declarativas", INDIGO),
        ("Almacén", "SQLite · eventos con motivo", INDIGO), ("Notificador", "presupuesto · digest", INDIGO)], tcol=INDIGO))
    b.append(L(280, 238, 280, 254, INDIGO, 1.2, marker="cA"))
    b.append(T(290, 249, "manifiesto por módulo · cada módulo es un proceso", 8.8, 400, MUTED, it=True, fam=F_SERIF))
    b.append(banda(256, 96, "MÓDULOS · CADA UNO CON SU MANIFIESTO", "#F8F1DF", GOLD, [
        ("Sol", "despertar", GOLD), ("Luna", "cierre", INDIGO), ("Osi", "por definir", VERDE),
        ("Detector", "precios y ofertas", GOLD), ("Catálogos", "países · animales…", GOLD)], tcol=GOLD))
    b.append(L(280, 354, 280, 370, INDIGO, 1.2, marker="cA"))
    b.append(banda(372, 96, "BORDES · LO QUE WINT NO CONTROLA", "#F1EDE0", RULE, [
        ("Windows", "powercfg · shutdown", SILVER), ("Comercios", "VTEX · JSON-LD · SEPA", SILVER),
        ("Series", "IPC · dólar", SILVER), ("IA opcional", "claude -p, solo extrae", SILVER)]))
    # pie
    b.append(R(10, 480, 540, 70, "none", RULE, 0.8, 8, 'stroke-dasharray="4 3"'))
    b.append(T(22, 500, "REGLA DE ORO", 9, 600, GOLD, ls=1.8))
    b.append(T(22, 518, "La IA, si existe, vive en el borde (extraer y clasificar con esquema validado).", 11, 400, INK, fam=F_SERIF))
    b.append(T(22, 534, "Todo lo que decide qué hacer y cuándo avisar es código y reglas que se pueden leer y probar.", 11, 400, INK, fam=F_SERIF))
    return svg(W, H, "".join(b), d)


# ============================================================ 4. Escalera Android
def escalera_android():
    W, H = 560, 338
    d = marker("sA", GOLD)
    b = []
    pasos = [
        ("1", "PWA + ntfy + Tailscale", "Días", "El panel de WINT se instala desde el navegador; los avisos llegan por ntfy; el acceso remoto es privado.",
         "Paso al siguiente si: la PWA no puede mostrar un widget, o los avisos no llegan de forma confiable.", GOLD, "#F8F1DF"),
        ("2", "App nativa Kotlin + Compose", "Semanas", "Widgets (Glance), canales de notificación, WorkManager, acceso directo a la red del hogar.",
         "Paso al siguiente si: hace falta el catálogo estilo Netflix en un televisor.", INDIGO, "#E9ECF6"),
        ("3", "Android TV · Compose for TV", "Meses", "Filas desplazables con foco por control remoto; el catálogo como pantalla de sala.",
         "Solo si el uso real lo justifica.", VERDE, "#E1EEEA"),
    ]
    for i, (n, t, dur, desc, paso, col, fill) in enumerate(pasos):
        x = 10 + i * 18
        y = 14 + i * 100
        w = 540 - i * 36
        b.append(R(x, y, w, 88, fill, col, 1.2, 8))
        b.append(f'<circle cx="{x+30}" cy="{y+44}" r="19" fill="{col}"/>')
        b.append(T(x + 30, y + 52, n, 22, 600, "#fff", "middle", fam=F_DISP))
        b.append(T(x + 62, y + 24, t, 17, 600, NAVY, fam=F_DISP))
        b.append(T(x + w - 14, y + 22, dur.upper(), 8.8, 600, col, "end", ls=1.6))
        # descripción en dos líneas
        words = desc.split()
        l1, l2 = [], []
        for wd in words:
            (l1 if len(" ".join(l1 + [wd])) < 84 else l2).append(wd)
        b.append(T(x + 62, y + 42, " ".join(l1), 9.8, 400, INK))
        if l2:
            b.append(T(x + 62, y + 55, " ".join(l2), 9.8, 400, INK))
        b.append(T(x + 62, y + 76, paso, 9, 500, col, it=False))
    b.append(T(14, 316, "Windows Subsystem for Android terminó el 5 de marzo de 2025: no hay una ruta oficial para correr apps Android en Windows.", 8.8, 400, MUTED, it=True, fam=F_SERIF))
    b.append(T(14, 328, "Para probar en una PC con Windows conviene el emulador de Android Studio o un teléfono real conectado.", 8.8, 400, MUTED, it=True, fam=F_SERIF))
    return svg(W, H, "".join(b), d)


# ============================================================ 5. Pipeline del Detector
def pipeline_detector():
    W, H = 560, 300
    d = marker("pA", INDIGO)
    b = []
    etapas = [
        ("1", "Descubrir", ["sitemap.xml", "API de catálogo", "JSON-LD Product"], GOLD),
        ("2", "Extraer", ["precio, tachado", "stock, cuotas", "fecha y hora"], GOLD),
        ("3", "Normalizar", ["precio por kg/l/u", "GTIN / EAN", "marca y tamaño"], INDIGO),
        ("4", "Guardar", ["historial en escalón", "captura del HTML", "SQLite → Parquet"], INDIGO),
        ("5", "Analizar", ["mediana por tiempo", "deflactado por IPC", "puntaje 0 a 100"], VERDE),
        ("6", "Avisar", ["umbral y tope diario", "motivo explícito", "digest diario"], VERDE),
    ]
    w = 82
    gap = 9.6
    for i, (n, t, items, col) in enumerate(etapas):
        x = 10 + i * (w + gap)
        b.append(f'<path d="M{x} 14 H{x+w-12} L{x+w} 40 L{x+w-12} 66 H{x} L{x+12} 40 Z" fill="{col}"/>')
        b.append(T(x + w / 2 + 2, 36, n, 11, 600, "#FFE9A6", "middle", fam=F_DISP))
        b.append(T(x + w / 2 + 2, 53, t, 11.8, 600, "#fff", "middle", fam=F_DISP))
        for j, it in enumerate(items):
            b.append(R(x + 4, 78 + j * 30, w - 8, 24, "#fff", RULE, 0.8, 4))
            b.append(T(x + w / 2, 94 + j * 30, it, 8.4, 500, INK, "middle"))
    b.append(L(10, 180, 550, 180, RULE, 0.6))
    # franjas de control
    b.append(R(10, 192, 262, 96, "#F8F1DF", GOLD, 1.0, 8))
    b.append(T(22, 212, "RASTREO CORTÉS", 9, 600, GOLD, ls=1.8))
    for j, s in enumerate(["Respetar robots.txt y límites de ritmo", "Identificarse con un User-Agent propio", "Sin evadir bloqueos ni falsificar un navegador", "Una pasada diaria alcanza: el precio es un escalón"]):
        b.append(f'<circle cx="28" cy="{229+j*15-3}" r="2.2" fill="{AMBER}"/>')
        b.append(T(36, 229 + j * 15, s, 9.2, 400, INK))
    b.append(R(288, 192, 262, 96, "#E9ECF6", INDIGO, 1.0, 8))
    b.append(T(300, 212, "SOLO REGLAS POR DEFECTO", 9, 600, INDIGO, ls=1.8))
    for j, s in enumerate(["Extracción por capas: API, JSON-LD, estado, HTML", "La IA solo propone emparejamientos dudosos", "Una persona los aprueba; el resto es código", "Cada veredicto guarda su motivo y su versión"]):
        b.append(f'<circle cx="306" cy="{229+j*15-3}" r="2.2" fill="#7783BD"/>')
        b.append(T(314, 229 + j * 15, s, 9.2, 400, INK))
    return svg(W, H, "".join(b), d)


# ============================================================ 6. Gráfico de escalón (datos sintéticos)
def escalon_precio():
    W, H = 560, 336
    ox, oy, pw, ph = 56, 30, 484, 222
    dias = 150
    serie = []
    precio = 1000.0
    for dia in range(dias):
        if dia > 0 and dia % 14 == 0 and dia not in (100, 114):
            precio *= 1.0185
        serie.append(round(precio, 1))
    base_pre = serie[99]
    suba = round(base_pre * 1.30, 1)
    for dia in range(100, 114):
        serie[dia] = suba
    tachado = suba
    oferta = round(suba * 0.80, 1)
    for dia in range(114, 121):
        serie[dia] = oferta
    despues = round(base_pre * 1.0185 * 1.04, 1)
    for dia in range(121, dias):
        serie[dia] = despues
    ventana = sorted(serie[24:114])
    mediana = ventana[len(ventana) // 2]
    mas_que_antes = (oferta / base_pre - 1) * 100
    sobre_mediana = (oferta / mediana - 1) * 100

    ymin, ymax = 950, 1560

    def X(d):
        return ox + pw * d / (dias - 1)

    def Y(v):
        return oy + ph * (1 - (v - ymin) / (ymax - ymin))

    b = []
    b.append(T(ox, 16, "PRECIO EN PESOS (NOMINAL) · DATOS SINTÉTICOS, SOLO PARA ILUSTRAR EL MÉTODO", 8.6, 600, INDIGO, ls=1.2))
    b.append(R(ox, oy, pw, ph, "#fff", RULE, 0.8, 2))
    for v in range(1000, 1600, 100):
        b.append(L(ox, f"{Y(v):.1f}", ox + pw, f"{Y(v):.1f}", "#EFE9D9", 0.6))
        b.append(T(ox - 6, f"{Y(v)+3:.1f}", f"{v:,}".replace(",", "."), 9, 400, MUTED, "end"))
    b.append(f'<rect x="{X(114):.1f}" y="{oy}" width="{X(121)-X(114):.1f}" height="{ph}" fill="#F4EAD0" opacity="0.95"/>')
    b.append(T(f"{(X(114)+X(121))/2:.1f}", oy + ph - 7, "OFERTA", 8.2, 600, GOLD, "middle", ls=1.6))
    b.append(L(ox, f"{Y(mediana):.1f}", ox + pw, f"{Y(mediana):.1f}", SILVER, 0.9, dash="5 3"))
    b.append(T(ox + pw - 6, f"{Y(mediana)+12:.1f}", f"mediana de los 90 días previos ≈ {mediana:,.0f}".replace(",", "."), 8.6, 500, MUTED, "end"))
    b.append(L(f"{X(100):.1f}", f"{Y(tachado):.1f}", f"{X(121):.1f}", f"{Y(tachado):.1f}", ROJO, 1.3, dash="3 2"))
    path = [f"M{X(0):.1f} {Y(serie[0]):.1f}"]
    for d_ in range(1, dias):
        if serie[d_] != serie[d_ - 1]:
            path.append(f"H{X(d_):.1f} V{Y(serie[d_]):.1f}")
    path.append(f"H{X(dias-1):.1f}")
    b.append(f'<path d="{" ".join(path)}" fill="none" stroke="{INDIGO}" stroke-width="2" stroke-linejoin="miter"/>')
    def num(x, y, n, col):
        return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{col}"/>'
                + T(f"{x:.1f}", f"{y+3.6:.1f}", str(n), 9.6, 600, "#fff", "middle"))
    b.append(num(X(100) - 12, Y(suba), 1, ROJO))
    b.append(num(X(121) + 12, Y(tachado), 2, ROJO))
    b.append(num(X(121) + 12, Y(oferta) + 14, 3, GOLD))
    b.append(f'<circle cx="{X(100):.1f}" cy="{Y(suba):.1f}" r="3" fill="{ROJO}"/>')
    b.append(f'<circle cx="{X(114):.1f}" cy="{Y(oferta):.1f}" r="3" fill="{GOLD}"/>')
    for dd, lab in [(0, "día 1"), (30, "30"), (60, "60"), (90, "90"), (120, "120"), (149, "150")]:
        b.append(T(f"{X(dd):.1f}", oy + ph + 15, lab, 9, 400, MUTED, "middle"))
    b.append(T(ox + pw / 2, oy + ph + 29, "días de observación", 8.8, 400, MUTED, "middle", it=True, fam=F_SERIF))
    # leyenda numerada debajo
    ly = oy + ph + 46
    cols = [
        (1, ROJO, ["Sube 30 % catorce días", "antes de la oferta."]),
        (2, ROJO, ["Muestra un precio «tachado»", "igual al nuevo precio inflado."]),
        (3, GOLD, [f"«20 % de descuento»: cuesta {mas_que_antes:.0f} % más que", f"antes de la suba y {sobre_mediana:.0f} % sobre la mediana."]),
    ]
    xs = [ox, ox + 128, ox + 290]
    for (n, c, lines), x0 in zip(cols, xs):
        b.append(num(x0 + 7, ly, n, c))
        for k, ln in enumerate(lines):
            b.append(T(x0 + 20, ly + 3.4 + k * 11.5, ln, 9, 400, INK))
    return svg(W, H, "".join(b))

# ============================================================ 7. Hoja de ruta (Gantt)
def hoja_ruta(fases=None):
    fases = fases or [
        ("0 · Perfilar y decidir", 0, 1, "gris", "powercfg /a · prueba real"),
        ("1 · Núcleo y rutinas Sol y Luna", 1, 3, "sol", "primer ciclo completo"),
        ("2 · Detector integrado y reglas", 3, 4, "luna", "avisos en modo sombra"),
        ("3 · Panel y teléfono", 6, 3, "osi", "PWA + ntfy + Tailscale"),
        ("4 · Catálogo estilo Netflix", 8, 4, "sol", "filas y gráficos de escalón"),
        ("5 · Calibrar y publicar", 11, 4, "luna", "muestra humana · umbrales"),
    ]
    W, H = 560, 66 + 36 * len(fases)
    ox = 176
    sem = 15
    pw = 560 - ox - 10
    paso = pw / sem
    col = {"sol": (AMBER, "#8A5E0C"), "luna": ("#7783BD", INDIGO), "osi": ("#5E9C90", VERDE), "gris": ("#B5BACB", MUTED)}
    b = []
    for s_ in range(sem + 1):
        x = ox + s_ * paso
        b.append(L(f"{x:.1f}", 36, f"{x:.1f}", H - 10, "#ECE6D6" if s_ % 5 else RULE, 0.6))
        if s_ < sem:
            b.append(T(f"{x+paso/2:.1f}", 30, str(s_ + 1), 9, 500, MUTED, "middle"))
    b.append(T(ox, 14, "SEMANAS · ORIENTATIVO", 8.8, 600, INDIGO, ls=1.4))
    for i, (nombre, ini, dur, tono, hito) in enumerate(fases):
        y = 46 + i * 36
        c1, c2 = col[tono]
        b.append(T(8, y + 15, nombre, 13, 600, NAVY, fam=F_DISP))
        x = ox + ini * paso
        wbar = dur * paso - 2
        b.append(R(f"{x+1:.1f}", y, f"{wbar:.1f}", 22, c1, c2, 1.0, 5))
        ancho_txt = len(hito) * 4.5
        if x + wbar + 10 + ancho_txt < W - 6:
            b.append(T(f"{x+wbar+8:.1f}", y + 15, hito, 8.8, 500, INK))
        else:
            b.append(T(f"{x-7:.1f}", y + 15, hito, 8.8, 500, INK, "end"))
    return svg(W, H, "".join(b))

DIAGRAMAS = {
    "estados": (estados_energia, "Máquina de estados de energía de Windows 11 con los comandos que disparan cada transición"),
    "anillo": (anillo_dia, "Un día de WINT: Sol, Luna y las ventanas solares"),
    "capas": (capas_wint, "Capas de WINT: clientes, núcleo, módulos y bordes"),
    "escalera": (escalera_android, "Escalera de WINT en Android"),
    "pipeline": (pipeline_detector, "Pipeline del Detector"),
    "escalon": (escalon_precio, "Una oferta que no lo es, vista como escalón"),
    "ruta": (hoja_ruta, "Hoja de ruta por fases"),
}
