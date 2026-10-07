# -*- coding: utf-8 -*-
"""Ensambla el informe WINT: capítulos HTML + macros -> HTML único -> PDF (Chromium) con índice paginado.

Uso:
  python3 ensamblar.py                 # informe completo -> salida/WINT_informe.pdf
  python3 ensamblar.py --solo cap05    # solo un capítulo (vista previa rápida)
"""
import glob, html, json, os, re, subprocess, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
from lib import sinoptico, emblema_portada, esc  # noqa: E402
from diagramas import DIAGRAMAS  # noqa: E402

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
CAPS = os.path.join(AQUI, "capitulos")
SALIDA = os.path.join(AQUI, "salida")
FECHA = "7 de octubre de 2026"

# ----------------------------------------------------------------- estado global del ensamblado
class Estado:
    def __init__(self):
        self.fig = 0
        self.cua = 0
        self.tab = 0
        self.url2id = {}      # url -> id global
        self.fuentes = {}     # id -> (titulo, url, fecha)
        self.orden = []       # ids por primera cita
        self.alias = {}       # "cap05:clave" -> id
        self.avisos = []

def registrar_fuentes(est, cap_id, ruta_json):
    if not os.path.exists(ruta_json):
        return
    datos = json.load(open(ruta_json, encoding="utf-8"))
    for k, v in datos.items():
        url = v.get("u", "").strip()
        titulo = v.get("t", url)
        fecha = v.get("f", "")
        if url in est.url2id:
            est.alias[f"{cap_id}:{k}"] = est.url2id[url]
        else:
            nuevo = f"s{len(est.fuentes)+1}"
            est.url2id[url] = nuevo
            est.fuentes[nuevo] = (titulo, url, fecha)
            est.alias[f"{cap_id}:{k}"] = nuevo

def citar(est, cap_id, claves):
    nums = []
    for k in [c.strip() for c in claves.split(",") if c.strip()]:
        sid = est.alias.get(f"{cap_id}:{k}")
        if not sid:
            est.avisos.append(f"[{cap_id}] fuente no registrada: {k}")
            continue
        if sid not in est.orden:
            est.orden.append(sid)
        nums.append(est.orden.index(sid) + 1)
    if not nums:
        return ""
    nums = sorted(set(nums))
    return '<sup class="c">' + ",".join(map(str, nums)) + "</sup>"

# ----------------------------------------------------------------- macros
def expandir(txt, est, cap_id):
    # cuadros sinópticos
    def sin(m):
        try:
            d = json.loads(m.group(1))
        except Exception as e:  # noqa: BLE001
            est.avisos.append(f"[{cap_id}] JSON inválido en SIN: {e}")
            return ""
        est.cua += 1
        return sinoptico(d["arbol"], d.get("titulo"), d.get("tono", "sol"), d.get("pie"), est.cua)
    txt = re.sub(r"<!--SIN\s*(\{.*?\})\s*-->", sin, txt, flags=re.S)

    # diagramas propios: <!--DIAG nombre | pie-->
    def diag(m):
        nombre = m.group(1).strip()
        pie = (m.group(2) or "").strip()
        if nombre not in DIAGRAMAS:
            est.avisos.append(f"[{cap_id}] diagrama inexistente: {nombre}")
            return ""
        est.fig += 1
        fn, desc = DIAGRAMAS[nombre]
        return f'<figure>{fn()}<figcaption><b>Figura {est.fig}</b> {pie or desc}</figcaption></figure>'
    txt = re.sub(r"<!--DIAG\s+([a-z_]+)\s*(?:\|\s*(.*?))?\s*-->", diag, txt, flags=re.S)

    # citas
    txt = re.sub(r"\[\[c:([^\]]+)\]\]", lambda m: citar(est, cap_id, m.group(1)), txt)

    # captions de tablas
    def cap(m):
        est.tab += 1
        return f"<caption>Tabla {est.tab} · "
    txt = re.sub(r"<caption>", cap, txt)
    return txt

# ----------------------------------------------------------------- piezas
def portada():
    return f'''<div class="cover">{emblema_portada()}
<div class="marca"><div class="regla"></div><p class="kicker">Informe técnico y hoja de ruta</p><h1>WINT</h1>
<p class="sub">Una plataforma personal, predecible y silenciosa para ahorrar</p>
<p class="triada">Sol<b>·</b>Luna<b>·</b>Osi</p></div>
<div class="pie"><div class="l">{FECHA}<br>Buenos Aires, Argentina</div><div>Edición 1.0</div></div></div>'''

def leer_capitulos(solo=None):
    archivos = sorted(glob.glob(os.path.join(CAPS, "cap*.html"))) + sorted(glob.glob(os.path.join(CAPS, "ap*.html")))
    if solo:
        archivos = [a for a in archivos if os.path.basename(a).startswith(solo)]
    caps = []
    for a in archivos:
        txt = open(a, encoding="utf-8").read()
        m = re.search(r"<!--CAP\s*(\{.*?\})\s*-->", txt, re.S)
        if not m:
            print("AVISO: sin cabecera CAP en", a)
            continue
        meta = json.loads(m.group(1))
        cuerpo = txt.replace(m.group(0), "", 1)
        cid = os.path.basename(a)[:-5]
        caps.append({"id": cid, "meta": meta, "cuerpo": cuerpo, "json": a[:-5] + ".fuentes.json"})
    return caps

def cabecera_cap(meta):
    etiqueta = meta.get("etiqueta") or f"Capítulo {meta['num']}"
    return (f'<div class="capitulo" id="{meta.get("anchor","")}"><span class="num">{esc(etiqueta)}</span>'
            f'<h1>{meta["titulo"]}</h1><p class="entrada">{meta.get("entrada","")}</p><div class="filete"></div></div>')

def indice(caps, paginas):
    filas = []
    for c in caps:
        m = c["meta"]
        et = m.get("corto") or m["num"]
        pg = paginas.get(c["id"], "")
        filas.append(f'<div class="fila"><span class="n">{esc(et)}</span><span class="t">{m["titulo"]}'
                     f'<small>{m.get("resumen","")}</small></span><span class="p">{pg}</span></div>')
    return ('<div class="capitulo" style="break-before:page"><span class="num">Contenido</span><h1>Índice</h1>'
            '<p class="entrada">Qué hay en este informe y dónde encontrarlo.</p><div class="filete"></div></div>'
            '<div class="toc">' + "".join(filas) + "</div>")

def doc_html(caps, est, paginas, solo=False):
    partes = []
    if not solo:
        partes.append(portada())
        partes.append(indice(caps, paginas))
    for c in caps:
        registrar_fuentes(est, c["id"], c["json"])
        partes.append(cabecera_cap(c["meta"]))
        partes.append(expandir(c["cuerpo"], est, c["id"]))
    # apéndice automático de fuentes
    if not solo and est.orden:
        filas = []
        for i, sid in enumerate(est.orden, 1):
            t, u, f = est.fuentes[sid]
            fecha = f' <span style="color:#656A7C">· {esc(f)}</span>' if f else ""
            filas.append(f'<div class="f"><span class="k">{i}</span><span>{esc(t)}{fecha}<span class="u">{esc(u)}</span></span></div>')
        partes.append('<div class="capitulo" id="fuentes"><span class="num">Apéndice</span><h1>Fuentes consultadas</h1>'
                      '<p class="entrada">Numeradas por orden de aparición. Cada número remite a una cita en el texto.</p><div class="filete"></div></div>'
                      '<p class="piefuente">Las fechas son las de la fuente o, si no figuran, las de la consulta (7 de octubre de 2026). '
                      'Varias páginas oficiales no pudieron abrirse durante la investigación; cuando una cita remite a un espejo o a un '
                      'extracto de búsqueda, el texto lo aclara.</p><div class="fuentes">' + "".join(filas) + "</div>")
    return ('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>WINT · Informe técnico</title>'
            '<link rel="stylesheet" href="estilo.css"></head><body>' + "\n".join(partes) + "</body></html>")

def imprimir(html_path, pdf_path):
    r = subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf_path}", html_path], capture_output=True, text=True)
    if not os.path.exists(pdf_path):
        print(r.stderr[-800:])
        raise SystemExit("no se generó el PDF")

def paginas_de(pdf, caps):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    res = {}
    textos = []
    for p in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", pdf, "-"], capture_output=True, text=True).stdout
        textos.append(t.lower())
    for c in caps:
        etiqueta = (c["meta"].get("etiqueta") or f"Capítulo {c['meta']['num']}").lower()
        for p, t in enumerate(textos, 1):
            if p > 2 and etiqueta in t:
                res[c["id"]] = p
                break
    return res, n

def main():
    solo = None
    if "--solo" in sys.argv:
        solo = sys.argv[sys.argv.index("--solo") + 1]
    os.makedirs(SALIDA, exist_ok=True)
    caps = leer_capitulos(solo)
    if not caps:
        raise SystemExit("no hay capítulos en " + CAPS)
    paginas = {}
    for pasada in (1, 2):
        est = Estado()
        h = doc_html(caps, est, paginas, solo=bool(solo))
        hp = os.path.join(AQUI, "informe.html" if not solo else f"previa_{solo}.html")
        open(hp, "w", encoding="utf-8").write(h)
        pdf = os.path.join(SALIDA, "WINT_informe.pdf" if not solo else f"previa_{solo}.pdf")
        imprimir(hp, pdf)
        if solo:
            break
        paginas, total = paginas_de(pdf, caps)
        print(f"pasada {pasada}: {total} páginas; capítulos en {paginas}")
    for a in est.avisos:
        print("AVISO:", a)
    print("PDF:", pdf)

if __name__ == "__main__":
    main()
