# Guía de redacción del informe WINT

Lo que sigue es obligatorio. El informe final es un PDF A4, elegante, en **español rioplatense formal-técnico**, con cuadros sinópticos, diagramas, tablas y comandos reales.

## 1. Archivos que entregás
Directorio de trabajo: `/tmp/claude-0/-home-user-dantaylor/6e5bb834-7e4c-5ebb-a4b4-ccfe5aba7c58/scratchpad/build/`

- `capitulos/<id>.html` — el capítulo (fragmento HTML, sin `<html>` ni `<body>`).
- `capitulos/<id>.fuentes.json` — fuentes citadas: `{"clave": {"t": "título legible", "u": "URL", "f": "fecha de la fuente o 'consultado 7 oct 2026'"}}`.
- `capitulos/<id>.resumen.md` — 4 a 6 viñetas con las conclusiones clave del capítulo, en frases completas (las usa el resumen ejecutivo).

`<id>` es el que te asignan (por ejemplo `cap05`, `apA`). **No toques** ningún otro archivo: ni `lib.py`, ni `estilo.css`, ni `diagramas.py`, ni los capítulos de otros.

El ejemplo vivo está en `capitulos/cap00_ejemplo.html`: **leelo primero**; usa todos los macros.

## 2. Estructura del fragmento
1. Primera línea: `<!--CAP {"num":"05","titulo":"…","entrada":"…","corto":"05","resumen":"…"}-->`
   - `titulo`: una o dos líneas, sin punto final. `entrada`: **una** frase en cursiva (qué se lleva el lector). `corto`: lo que aparece en el índice (`"05"`; apéndices `"A"`). `resumen`: una línea para el índice. Para un apéndice agregá `"etiqueta":"Apéndice A"`.
2. Luego `<p class="lead">…</p>`: el primer párrafo empieza con **una letra** (no con ¿, ¡, comillas ni número) porque la primera letra se muestra como capital. Dice la tesis del capítulo.
3. Después secciones con `<h2>` y subsecciones con `<h3>` (etiqueta en mayúsculas pequeñas). No uses `<h1>`.

## 3. Elementos disponibles (clases y macros)
- Párrafos `<p>`, listas `<ul>`/`<ol>` (viñetas doradas, numeración dorada), `<strong>`, `<em>`. Código en línea: `<code>powercfg /a</code>`. Bloques de comandos: `<pre>…</pre>` (escapá `<`, `>` y `&` como `&lt;`, `&gt;`, `&amp;`; sin resaltado salvo `<span class="k">`, `<span class="s">`, `<span class="c">`).
- **Avisos**: `<div class="aviso"><span class="t">Lo esencial</span><p>…</p></div>`. Variantes: `class="aviso decision"` (índigo: decisiones tuyas), `class="aviso riesgo"` (rojo), `class="aviso ok"` (verde: "Qué hacer"/confirmado). Usalos con medida (uno o dos por sección, no más).
- **Tablas**: `<table><caption>Título</caption><colgroup><col style="width:24%">…</colgroup><thead>…</thead><tbody>…</tbody></table>`. El ensamblador antepone "Tabla N · " al `caption`: no lo escribas. Texto de celdas corto (≤ 25 palabras). Máximo 5 columnas; la primera es el nombre. Para valoraciones usá puntos: `<span class="dots"><i></i><i></i><i></i><i class="o"></i><i class="o"></i></span>` (3 de 5). Etiquetas: `<span class="etq sol">…</span>`, `luna`, `osi`, `rojo`, `gris`.
- **Cuadro sinóptico** (con llaves, el formato clásico): una sola línea de comentario con JSON válido:
  `<!--SIN {"titulo":"…","tono":"luna","arbol":["Raíz",[["Rama",["hoja","hoja"],"sol"],["Rama 2",[["Subrama",["hoja","hoja"]],"hoja"],"osi"]]],"pie":"Frase corta."}-->`
  Formato de nodo: `"texto"` (hoja) o `["texto", [hijos], "tono"]`. Tonos: `sol` (dorado), `luna` (índigo), `osi` (verde), `rojo`, `gris`. **Etiquetas de 1 a 6 palabras**, máximo 3 niveles bajo la raíz, máximo ~16 hojas por cuadro (si no entra, hacé dos cuadros). Un JSON roto hace desaparecer el cuadro: validalo. Caracteres: usá `\"` para comillas dentro del JSON y no uses saltos de línea dentro de un string.
- **Diagramas propios** (ya dibujados, vos solo los ubicás): `<!--DIAG nombre | texto del pie-->` con `nombre` ∈
  - `estados` — máquina de estados de energía de Windows (Reposo, Hibernación, híbrido, total, Reinicio; flechas de Luna y de Sol con sus comandos). Cap. 5.
  - `anillo` — un día de WINT en 24 horas: Sol 07:30, Luna 23:30, ventanas solares de Buenos Aires. Cap. 5 o 4.
  - `capas` — capas de WINT: clientes, núcleo, módulos, bordes. Cap. 4.
  - `escalera` — escalera de WINT en Android: PWA → nativa → TV. Cap. 7.
  - `pipeline` — pipeline del Detector, seis etapas. Cap. 6.
  - `escalon` — gráfico sintético de una oferta que no lo es. Cap. 6.
  - `ruta` — hoja de ruta por fases (Gantt). Cap. 10.
  Cada diagrama se coloca una sola vez en el informe. El pie debe explicar **cómo leerlo** en una o dos frases. Los diagramas ya incluyen sus propios textos: no los repitas, **comentalos** y remití a ellos ("la figura anterior").
- **Citas**: `[[c:clave]]` o `[[c:clave1,clave2]]` justo después de la frase. Cada clave debe existir en tu `fuentes.json`. Se numeran solas por orden de aparición en todo el informe. **Usá solo URLs que aparezcan en los archivos de investigación**; nunca inventes una. Si el dato viene de una copia o espejo, el título de la fuente lo dice ("copia de Microsoft Learn en GitHub", "extracto de búsqueda").
- No numeres figuras, cuadros ni tablas a mano y no cites números ("figura 3"): remití por posición ("el cuadro siguiente") o por capítulo ("capítulo 5").

## 4. Estilo
- Español rioplatense **formal-técnico, impersonal**: "WINT calcula…", "conviene…", "hay que…". **Sin voseo ni tuteo** (el voseo queda para el capítulo 11, que escribe otra persona). Sin emojis. Sin muletillas ("cabe destacar", "en el mundo actual"). Frases de longitud media; un párrafo, una idea.
- Fechas "7 de octubre de 2026"; porcentajes "30 %" (con espacio fino normal); decimales con coma y miles con punto en el texto ("1.284 fichas", "US$ 0,012"); en comandos y código, la sintaxis original. Los nombres de producto y los términos técnicos van en su forma original (Task Scheduler = "Programador de tareas" la primera vez, con el nombre original entre paréntesis si ayuda).
- Densidad: el lector quiere **información técnica precisa y qué hacer**, no divulgación. Prefiero una tabla o un cuadro antes que tres párrafos. Cada capítulo cierra con una caja `aviso ok` titulada **Qué hacer** con 3 a 6 pasos concretos y ordenados.
- Todo lo **propuesto** (recetas, umbrales, matrices, orden de pasos) se presenta como propuesta de diseño; todo lo **verificado** lleva cita; lo **no verificado** se marca con `<span class="etq rojo">sin verificar</span>` o con "según prensa" / "según un espejo no oficial". No conviertas una duda en una afirmación.
- **Orden de prioridad de las fuentes internas** cuando se contradicen: `research/complementos/*.md` > `research/<frente>.verificado.md` > `research/<frente>.md`. Y **no repitas** las afirmaciones que la auditoría (`research/AUDITORIA.md`, sección 2.1) marca como erróneas. `DECISIONES.md` resuelve las posiciones del informe: **si lo que leés en un frente contradice `DECISIONES.md`, gana `DECISIONES.md`.**
- Si falta un dato, **decilo** ("no se pudo verificar") en lugar de rellenar. Si hace falta una decisión de la persona, usá `aviso decision`.

## 5. Maquetación y revisión visual (obligatoria)
- Largo: respetá el presupuesto de páginas de tu encargo (±15 %). Una página A4 admite ~550 palabras de texto corrido, o ~1/2 página de tabla de 8 filas.
- Para ver tu capítulo: `cd` al directorio de trabajo y corré `python3 ensamblar.py --solo <id>`; genera `salida/previa_<id>.pdf`. Convertilo con `pdftoppm -r 70 -png salida/previa_<id>.pdf salida/p_<id>` y **mirá las imágenes** (herramienta Read). Corregí: desbordes de tablas o de texto, títulos huérfanos al final de página, páginas casi vacías por un bloque que no entra, cuadros sinópticos con etiquetas largas, cajas demasiado grandes. `figure`, `.aviso`, `.sinoptico`, `pre` y las filas de tabla no se cortan entre páginas: un bloque grande puede dejar un hueco; reordená para evitarlo.
- La numeración "Figura N", "Cuadro N", "Tabla N" y de fuentes en la previa es parcial (solo tu capítulo); es normal.
- Revisá que `python3 ensamblar.py --solo <id>` no imprima `AVISO:` (JSON inválido, fuente no registrada, diagrama inexistente).

## 6. Honestidad
La investigación se hizo con búsqueda web limitada y con muchos sitios oficiales bloqueados; por eso muchas versiones y fechas salen de GitHub, de registros de paquetes y de extractos de búsqueda. **Es preferible un informe que diga "no se pudo verificar" a uno que afirme con seguridad algo que nadie abrió.** Si un dato es decisivo y está débil, decilo en una caja `aviso riesgo` y proponé cómo verificarlo (qué comando, qué página, qué prueba).
