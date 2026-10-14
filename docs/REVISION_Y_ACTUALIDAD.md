# Revisión general y actualidad sin anzuelo

Tres partes: (1) una revisión crítica de lo construido para comercios y
enciclopedias, con lo que está firme y lo que es frágil; (2) el diseño del
mecanismo de **actualidad**, que decide qué es noticia por lógica y no por el
titular; (3) lo que se agregó al panel por cuenta propia (visual, funcional y de
accesibilidad).

---

## 1. Revisión crítica de lo hecho

### 1.1 Comercios ("detectores de supermercados")

| Pieza | Estado | Juicio |
|---|---|---|
| Identidad nombre + dirección canónica | Firme | Resuelve sucursales y "Av./Avenida". Falla con mudanzas (misma tienda, nueva dirección = item nuevo). Ahora el campo `situacion: mudado` lo marca y la descripción trae la nueva dirección; la fusión automática de ambos registros sigue pendiente. |
| Política web "siempre", 3 búsquedas, ciudad en la consulta | Firme | Probado con un local real: 4 fuentes, sitio propio, confianza alta, 10 s, US$ 0,056. |
| Vencimiento a 30 días con prioridad | Firme | Es el único mecanismo de actualidad que existía. Limitación: reanaliza la ficha completa; un refresco parcial (solo horario/situación) costaría la mitad. Pendiente. |
| `situacion` (abierto/cerrado/mudado/desconocido) | **Nuevo** | Es lo que faltaba para que un refresco diga algo útil. Regla en el prompt: nunca "cerrado" por falta de datos. |
| Fuentes estructuradas (OSM, municipio) | **No hecho** | Sigue siendo la mayor mejora de costo pendiente. Sin esto, cada comercio paga 1-3 búsquedas. |
| Riesgo principal | — | **Falsos cierres.** Un comercio sin presencia web parece cerrado. Mitigación: el prompt lo prohíbe, y la novedad "cerrado" exige corroboración (ver §2) antes de mostrarse como novedad; si no, queda "a confirmar". |

### 1.2 Enciclopedias (animales, curiosidades)

| Pieza | Estado | Juicio |
|---|---|---|
| Dos pasadas (sin web → con web solo lo dudoso) | Firme | Probado: León salió "alta" sin web; Tarántula fue a la segunda pasada y volvió con tres fuentes de referencia. |
| Campos volátiles (estado UICN) | Firme | Fuerza la web aunque la confianza sea alta. Es la razón por la que, en un test, el lobo con "NE" fue a verificar. Correcto. |
| Identidad por nombre científico, alias por nombre común | Firme | "Puma" y "León de montaña" se unifican después del análisis. |
| Vigilancia de Wikipedia | **Nuevo** | Ver §2. Sin red en el entorno de desarrollo: probado con dobles que reproducen las respuestas reales de la API (`formatversion=2`, etiquetas `mw-reverted`). Verificar en la PC con un artículo real. |
| Riesgo principal | — | **Confiar en la memoria del modelo para datos que cambian.** Mitigado por los campos volátiles y ahora por la vigilancia. Lo que no cambia (taxonomía, dieta) no necesita web. |

### 1.3 Motor y panel

- **Firme:** reanudación, no pagar dos veces, tope de gasto (ahora no arranca
  items nuevos tras el tope), pausa global ante límites, dos vías (`claude -p`
  y API), lotes recuperables, panel en solo lectura sobre la misma base.
- **Frágil:** la clasificación de errores de `claude -p` es por texto
  ("rate limit", "usage limit"…); si el mensaje cambia, un límite se contaría
  como error del item. El contador de búsquedas en esa vía es aproximado
  (fuentes citadas). Windows sin probar.
- **Deuda:** el refresco mensual de comercios reanaliza todo el item; un modo
  "solo campos volátiles" bajaría el costo a la mitad.

---

## 2. Actualidad sin anzuelo

### 2.1 El problema

"Estar al tanto" leyendo titulares es la forma más cara y menos confiable de
mantener un catálogo: los medios (incluso los buenos) titulan para el clic, las
agencias se copian entre sí (diez notas = una fuente) y lo viejo se recicla
como nuevo. Un catálogo no necesita saber *qué se dice*: necesita saber *si
cambió algo que él afirma*.

### 2.2 Principio

**Es noticia lo que cambia una ficha con motivo.** Todo lo demás es, como
mucho, un motivo para verificar. Y el motivo se escribe: cada novedad lleva su
puntaje y la lista de razones, para que una persona pueda discrepar.

### 2.3 Las reglas (`catalogo/core/novedades.py`)

| # | Regla | Efecto | Por qué |
|---|---|---|---|
| 1 | **Cambio concreto**: alguna señal propone un valor nuevo para un campo de la ficha | +30. Sin esto, el tope es "a confirmar" | Separa "pasa algo" de "cambió algo". |
| 2 | **Corroboración**: fuentes independientes, contadas por dominio registrable (clarin.com y m.clarin.com son una) | 2 → +20; 3 o más → +30; 1 → 0 | Las copias no suman. |
| 3 | **Jerarquía**: oficial/referencia (UICN, Wikidata, Wikipedia, `.gob.ar`, DOI…) > medio establecido o sitio propio > resto > granja de contenido | +20 / +12 / 0 / −15 | Una fuente de referencia pesa; una granja resta aunque acierte. |
| 4 | **Persistencia**: edición de Wikipedia sin revertir ≥2 días (+10) o ≥7 (+15); visitas muy altas ≥3 días seguidos (+10). Edición de hace una hora o pico de un día: 0 | Premia lo que se sostiene | Lo que se revierte o se apaga en un día era ruido. |
| 5 | **Titular**: rasgos de anzuelo ("no vas a creer", pregunta, "revelan", superlativo absoluto, mayúsculas, "N razones"…) | −8 por rasgo, máx. −30 | Juzga la forma, no la verdad; una fuente seria con titular de anzuelo también paga. |
| 6 | **Recencia**: la señal más nueva tiene más de 90 días | −15 | Lo reciclado no es actualidad. |
| 7 | **Redundancia**: la ficha ya dice eso | Descartada (10) | No es novedad. |
| 8 | **Contradicción**: las fuentes proponen valores distintos | −20 y nunca "novedad" | Hay que confirmar cuál. |

Umbrales: **≥60 novedad**, **35-59 a confirmar**, **<35 descartada**.

### 2.4 De dónde salen las señales

1. **Del propio refresco (lo más confiable).** Cuando una ficha se reanaliza
   (vencimiento, datos nuevos, verificación) y cambia un campo de
   `campos_novedad`, cada URL citada en `fuentes_web` es una señal. Un comercio
   que pasa a "cerrado" citando el municipio y un diario: 70 puntos, novedad.
   Citando solo un blog: 30, descartada; queda en la ficha pero no se anuncia.
2. **De Wikipedia (`vigilar`), como disparador.** Para enciclopedias, se mira
   si el artículo *se mueve*: ediciones de tamaño apreciable que siguen sin
   revertir (MediaWiki marca las revertidas con `mw-reverted`; se ignoran
   bots y cambios menores a 50 bytes) y visitas sostenidas muy por encima de
   la mediana del mes. Si hay movimiento firme, el item pasa a `verificar`: la
   próxima corrida lo reanaliza **con web** y, si algún campo cambió, recién
   ahí hay novedad. Wikipedia no dice qué cambió; dice dónde mirar. Esto es
   exactamente "fijarse en Wikipedia para considerar algo digno de noticia",
   pero con la verificación después, no antes.
3. **Lo que no se hace a propósito:** leer titulares de medios para
   decidir. Los medios entran solo como fuentes citadas por la verificación,
   y pasan por las reglas 2, 3, 5 y 6 como cualquier otra.

### 2.5 Cómo se usa

```bash
python -m catalogo vigilar animales curiosidades        # semanal; marca a verificar lo que se mueve
python -m catalogo analizar animales curiosidades comercios --claude-code   # verifica y refresca
python -m catalogo novedades                            # lista con puntaje y motivos
python -m catalogo novedades --vista 12                 # o desde el panel, con los botones
```

Las novedades aparecen en el panel con su categoría, puntaje, motivos (los
que restan, en naranja) y fuentes; se marcan vistas o descartadas desde ahí.

### 2.6 Límites honestos

- Las listas de fuentes por nivel son cortas y están pensadas para Argentina y
  España; hay que ampliarlas según lo que aparezca. Una fuente desconocida es
  nivel 1, no 0: la duda no castiga.
- El detector de anzuelo es por patrones en español; no entiende ironía ni
  idiomas. Está para restar, no para decidir solo.
- La vigilancia de Wikipedia cuesta una o dos llamadas por ficha (gratis, con
  `User-Agent` identificado). Para miles de fichas, correrla semanal y con
  `--limite`, o repartirla por días.
- No probado con red real desde este entorno (proxy cerrado a Wikimedia).

---

## 3. Lo que se agregó al panel por cuenta propia

**Visual y funcional**

- Sección **Novedades** con contador, categoría con icono, puntaje en barra,
  motivos como etiquetas (en naranja los que restan), fuentes enlazadas, y
  botones "vista"/"descartar" que escriben en la base.
- **Favicon dinámico**: el punto de color del estado también en la pestaña del
  navegador (verde trabajando, ámbar pausa o lotes, rojo interrumpido, gris
  inactivo). Es el "iconito al lado del reloj", pero con todo el panel a un
  clic.
- **Título de la pestaña** con avance y novedades: "● 64 % · Catálogos · 2
  novedades".
- **Filtro por catálogo** encima de la actividad (chips con el color fijo de
  cada dominio; filtrar no recolorea).
- **Avisar al terminar**: notificación del navegador cuando la corrida pasa
  de "trabajando" a terminada, con fichas listas y costo.

**Accesibilidad**

- Estado y avance con `aria-live="polite"`: un lector de pantalla anuncia los
  cambios sin que la página se vuelva ruidosa.
- **Pausar actualización**: para leer con calma o con lector de pantalla; el
  botón lo dice y reanuda a mano.
- `prefers-reduced-motion`: sin latido ni transiciones.
- Foco visible en todo lo interactivo; enlace de salto a la actividad; botones
  con etiquetas que nombran el item ("Marcar como vista: Kiosco 24").
- Medidores con `role="img"` y descripción numérica; gráfica de ritmo con su
  tabla equivalente; tamaños en `em` y botón **A+** para texto más grande.
- Colores de estado siempre con icono y texto, nunca solos; tema claro y
  oscuro validados contra el mismo sistema de color del resto del panel.

**Lo que no agregué, y por qué**

- Sonidos: molestan más de lo que ayudan en una corrida de horas; la
  notificación del navegador cubre el caso.
- Gráficas de costo por día: hasta tener una semana de datos reales no hay
  nada que mostrar; el dato está en `corridas` para cuando haga falta.
