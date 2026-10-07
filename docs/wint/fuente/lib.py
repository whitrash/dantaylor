# -*- coding: utf-8 -*-
"""Ayudas para armar el informe WINT: citas, cuadros sinópticos con llaves, tablas, avisos, portada."""
import html, math, random

def esc(s):
    return html.escape(str(s), quote=False)

# ----------------------------------------------------------------- citas
class Citas:
    """Numera las fuentes por orden de primera aparición y arma el apéndice."""
    def __init__(self):
        self.datos = {}   # clave -> (titulo, url, fecha)
        self.orden = []
    def reg(self, clave, titulo, url, fecha=""):
        self.datos[clave] = (titulo, url, fecha)
    def c(self, *claves):
        nums = []
        for k in claves:
            if k not in self.datos:
                raise KeyError("fuente no registrada: " + k)
            if k not in self.orden:
                self.orden.append(k)
            nums.append(self.orden.index(k) + 1)
        nums.sort()
        return '<sup class="c">' + ",".join(str(n) for n in nums) + "</sup>"
    def apendice(self):
        filas = []
        for i, k in enumerate(self.orden, 1):
            t, u, f = self.datos[k]
            fecha = f' <span style="color:#656A7C">· {esc(f)}</span>' if f else ""
            filas.append(f'<div class="f"><span class="k">{i}</span><span>{esc(t)}{fecha}<span class="u">{esc(u)}</span></span></div>')
        return '<div class="fuentes">' + "".join(filas) + "</div>"

# ----------------------------------------------------------------- piezas
def dots(n, de=5, tono=""):
    return f'<span class="dots {tono}">' + "".join('<i></i>' if i < n else '<i class="o"></i>' for i in range(de)) + "</span>"

def etq(txt, tono="gris"):
    return f'<span class="etq {tono}">{txt}</span>'

def aviso(titulo, cuerpo, tono=""):
    return f'<div class="aviso {tono}"><span class="t">{titulo}</span>{cuerpo}</div>'

def pre(texto):
    return "<pre>" + texto + "</pre>"

def tabla(cabeceras, filas, anchos=None, caption=None, clase=""):
    cg = ""
    if anchos:
        cg = "<colgroup>" + "".join(f'<col style="width:{a}">' for a in anchos) + "</colgroup>"
    cap = f"<caption>{caption}</caption>" if caption else ""
    th = "".join(f"<th>{c}</th>" for c in cabeceras)
    tb = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in f) + "</tr>" for f in filas)
    return f'<table class="{clase}">{cap}{cg}<thead><tr>{th}</tr></thead><tbody>{tb}</tbody></table>'

def figura(svg, pie, num=None):
    n = f"<b>Figura {num}</b>" if num else ""
    return f"<figure>{svg}<figcaption>{n}{pie}</figcaption></figure>"

# ----------------------------------------------------------------- cuadro sinóptico
_TOP = '<svg viewBox="0 0 20 10" preserveAspectRatio="none"><path d="M20 .5 Q10 .5 10 10" fill="none" stroke="var(--brace)" stroke-width="1.1" vector-effect="non-scaling-stroke"/></svg>'
_MID = '<svg viewBox="0 0 20 20" preserveAspectRatio="none"><path d="M10 0 C10 7 8 10 .6 10 C8 10 10 13 10 20" fill="none" stroke="var(--brace)" stroke-width="1.1" vector-effect="non-scaling-stroke"/></svg>'
_BOT = '<svg viewBox="0 0 20 10" preserveAspectRatio="none"><path d="M10 0 Q10 9.5 20 9.5" fill="none" stroke="var(--brace)" stroke-width="1.1" vector-effect="non-scaling-stroke"/></svg>'
_LLAVE = f'<div class="ll">{_TOP}<div class="tallo"></div>{_MID}<div class="tallo"></div>{_BOT}</div>'

def _nodo(n, nivel, tono):
    if isinstance(n, str):
        label, hijos, t = n, [], tono
    else:
        label = n[0]
        hijos = n[1] if len(n) > 1 and n[1] else []
        t = n[2] if len(n) > 2 and n[2] else tono
    clase = f"sn n{min(nivel,4)} tono-{t}" + ("" if hijos else " hoja")
    h = f'<div class="{clase}"><div class="et"><span class="eti">{label}</span></div>'
    if hijos:
        h += _LLAVE + '<div class="hij">' + "".join(_nodo(c, nivel + 1, t) for c in hijos) + "</div>"
    return h + "</div>"

def sinoptico(arbol, titulo=None, tono="sol", pie=None, num=None):
    """arbol = (etiqueta, [hijos]); hijo = str | (etiqueta, [hijos], tono_opcional)."""
    t = f'<div class="titulo">{titulo}</div>' if titulo else ""
    cuerpo = _nodo(arbol, 0, tono)
    fig = f'<div class="sinoptico"><div class="caja">{t}{cuerpo}</div>'
    if pie:
        n = f"<b>Cuadro {num}</b> " if num else ""
        fig += f'<div class="pie-cuadro">{n}{pie}</div>'
    return fig + "</div>"

# ----------------------------------------------------------------- portada
def _lcg(seed):
    s = seed
    while True:
        s = (s * 1103515245 + 12345) & 0x7FFFFFFF
        yield s / 0x7FFFFFFF

def _creciente(cx, cy, R, dx, dy, r):
    """Trazo de una luna creciente: círculo (cx,cy,R) menos círculo desplazado (cx+dx, cy+dy, r)."""
    d = math.hypot(dx, dy)
    a = (R * R - r * r + d * d) / (2 * d)
    h = math.sqrt(max(R * R - a * a, 0))
    ux, uy = dx / d, dy / d
    px, py = cx + a * ux, cy + a * uy
    p1 = (px + h * -uy, py + h * ux)
    p2 = (px - h * -uy, py - h * ux)
    return (f"M{p1[0]:.2f} {p1[1]:.2f} A{R} {R} 0 1 0 {p2[0]:.2f} {p2[1]:.2f} "
            f"A{r} {r} 0 0 1 {p1[0]:.2f} {p1[1]:.2f} Z")

def emblema_portada():
    g = _lcg(7)
    estrellas = []
    for _ in range(190):
        x, y = next(g) * 210, next(g) ** 1.35 * 175
        r = 0.12 + next(g) * 0.38
        o = 0.25 + next(g) * 0.7
        estrellas.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#F4EAD0" opacity="{o:.2f}"/>')
    cx, cy, R = 105, 82, 56
    ticks = []
    for h in range(24):
        a = math.radians(h * 15 - 90)
        mayor = h % 6 == 0
        r0, r1 = R + 3.0, R + (7.6 if mayor else 5.2)
        ticks.append(f'<line x1="{cx + r0*math.cos(a):.2f}" y1="{cy + r0*math.sin(a):.2f}" x2="{cx + r1*math.cos(a):.2f}" y2="{cy + r1*math.sin(a):.2f}" stroke="#E2A83A" stroke-width="{0.45 if mayor else 0.22}" opacity="{0.95 if mayor else 0.6}"/>')
    # luna a las 22 h (arriba-izquierda) y sol a las 7 h (arriba-derecha)... se ubican en el anillo
    am = math.radians(-120)   # luna a las 22 h
    asol = math.radians(15)   # sol a las 7 h
    mx, my = cx + R * math.cos(am), cy + R * math.sin(am)
    sx, sy = cx + R * math.cos(asol), cy + R * math.sin(asol)
    cre = _creciente(mx, my, 13.5, 5.4, -3.6, 11.4)
    rayos = []
    for i in range(36):
        a = math.radians(i * 10)
        l = 5.2 if i % 2 == 0 else 3.4
        rayos.append(f'<line x1="{sx + 12.6*math.cos(a):.2f}" y1="{sy + 12.6*math.sin(a):.2f}" x2="{sx + (12.6+l)*math.cos(a):.2f}" y2="{sy + (12.6+l)*math.sin(a):.2f}" stroke="#F0BD55" stroke-width="0.32" stroke-linecap="round"/>')
    # arcos día/noche sobre el anillo
    def arco(a0, a1, color, ancho, op):
        x0, y0 = cx + R * math.cos(math.radians(a0)), cy + R * math.sin(math.radians(a0))
        x1, y1 = cx + R * math.cos(math.radians(a1)), cy + R * math.sin(math.radians(a1))
        grande = 1 if (a1 - a0) % 360 > 180 else 0
        return f'<path d="M{x0:.2f} {y0:.2f} A{R} {R} 0 {grande} 1 {x1:.2f} {y1:.2f}" fill="none" stroke="{color}" stroke-width="{ancho}" opacity="{op}" stroke-linecap="round"/>'
    return f'''<svg class="emblema" viewBox="0 0 210 297" xmlns="http://www.w3.org/2000/svg">
<defs>
 <radialGradient id="gs" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#FFE9A6"/><stop offset=".62" stop-color="#F0BD55"/><stop offset="1" stop-color="#D9902B"/></radialGradient>
 <radialGradient id="gm" cx="40%" cy="38%" r="70%"><stop offset="0" stop-color="#FFFFFF"/><stop offset="1" stop-color="#B8C0DC"/></radialGradient>
 <radialGradient id="halo" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#F0BD55" stop-opacity=".42"/><stop offset="1" stop-color="#F0BD55" stop-opacity="0"/></radialGradient>
 <radialGradient id="haloM" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="#B8C0DC" stop-opacity=".30"/><stop offset="1" stop-color="#B8C0DC" stop-opacity="0"/></radialGradient>
</defs>
{''.join(estrellas)}
<circle cx="{cx}" cy="{cy}" r="{R+30}" fill="none" stroke="#E2A83A" stroke-width=".12" opacity=".25"/>
<circle cx="{cx}" cy="{cy}" r="{R+14}" fill="none" stroke="#C9CDE6" stroke-width=".1" opacity=".25"/>
{''.join(ticks)}
<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="#C9CDE6" stroke-width=".28" opacity=".55"/>
{arco(3, 177, "#E2A83A", .9, .95)}
{arco(183, 357, "#8D96D3", .9, .8)}
<circle cx="{sx:.2f}" cy="{sy:.2f}" r="30" fill="url(#halo)"/>
<circle cx="{mx:.2f}" cy="{my:.2f}" r="26" fill="url(#haloM)"/>
{''.join(rayos)}
<circle cx="{sx:.2f}" cy="{sy:.2f}" r="10.6" fill="url(#gs)"/>
<path d="{cre}" fill="url(#gm)"/>
<circle cx="{cx}" cy="{cy}" r="1.4" fill="#E2A83A"/>
<circle cx="{cx}" cy="{cy}" r="3.6" fill="none" stroke="#E2A83A" stroke-width=".25" opacity=".8"/>
<text x="{cx}" y="{cy - R - 10.4}" text-anchor="middle" font-family="Jost" font-weight="500" font-size="2.5" letter-spacing=".5" fill="#E2A83A">00</text>
<text x="{cx + R + 11.2}" y="{cy + 0.9}" text-anchor="middle" font-family="Jost" font-weight="500" font-size="2.5" letter-spacing=".5" fill="#E2A83A">06</text>
<text x="{cx}" y="{cy + R + 13.2}" text-anchor="middle" font-family="Jost" font-weight="500" font-size="2.5" letter-spacing=".5" fill="#E2A83A">12</text>
<text x="{cx - R - 11.2}" y="{cy + 0.9}" text-anchor="middle" font-family="Jost" font-weight="500" font-size="2.5" letter-spacing=".5" fill="#E2A83A">18</text>
</svg>'''
