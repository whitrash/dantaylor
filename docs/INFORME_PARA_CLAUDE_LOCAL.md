# Informe para el Claude local: aplicar el motor de catálogos en Otsutsuki y Pinkra

Este documento está escrito para una sesión de Claude Code que corre **en la
computadora del usuario**, donde viven los proyectos reales. Lo escribió una
sesión de Claude en la nube que no tuvo acceso a esa computadora: todo lo que
dice sobre los proyectos locales ("Detector", las carpetas Otsutsuki y Pinkra)
es lo que el usuario contó, no algo verificado. **Lo primero es mirar.**

## 0. Contexto en cuatro líneas

- El usuario tiene dos catálogos: **enciclopedias** (animales; curiosidades de
  arte, deporte, ciencia e historia) y **comercios** (supermercados, librerías,
  locales de barrio). Hoy los analiza con Claude Code local, **un item por vez,
  con búsqueda web**, desde un software propio llamado **Detector**, que está en
  **Otsutsuki** y en **Pinkra** (carpetas o equipos; averiguarlo).
- Quiere: (1) acortar tiempos analizando en paralelo; (2) que el proceso sea
  **visual, estético e informativo**. Hoy la única señal es un ícono junto al
  reloj que se pone naranja mientras trabaja.
- En el repo `whitrash/dantaylor` (rama
  `claude/parallel-catalog-analysis-logistics-f1y1id`) está hecho un motor que
  resuelve las dos cosas: paralelismo con dos vías (Claude Code local o API) y un
  panel web local con progreso, ritmo, costo, tiempo restante y actividad.
- Tu trabajo es **conectar ese motor con los proyectos reales**, sin romper lo
  que ya funciona, y dejar el panel integrado al flujo del usuario.

## 1. Traer el motor

```bash
git clone -b claude/parallel-catalog-analysis-logistics-f1y1id https://github.com/whitrash/dantaylor.git catalogos-motor
cd catalogos-motor
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest                                                  # 94 tests, sin red, ~5 s
```

Lee en este orden: `README.md`, `docs/ARQUITECTURA.md` (qué se comparte entre
catálogos y por qué), `docs/LOGISTICA_PARALELA.md` (costos, límites, dos vías,
dos pasadas) y después el código: `catalogo/core/` es el motor,
`catalogo/dominios/` tiene una clase por catálogo.

## 2. Qué hace el motor (lo justo para operarlo)

```
ingerir   CSV/JSONL por fuente  ->  SQLite (catalogo.db)
importar  fichas ya hechas      ->  quedan "listas", no se pagan de nuevo
analizar  en paralelo, dos vías:
            --claude-code   lanza `claude -p` N veces a la vez (cuenta del usuario)
            (sin flag)      API de Claude; con clave; modo lotes a mitad de precio
          políticas web por dominio:
            animales, curiosidades: "si_dudoso"  -> pasada 1 sin web; pasada 2 con web
                                                    solo para confianza media/baja o
                                                    campos volátiles vacíos
            comercios:              "siempre"    -> una pasada con web (máx. 3 búsquedas)
catalogar árbol ordenado + facetas + cola de revisión -> salida/<dominio>/{catalogo.md,json,fichas.jsonl}
panel     http://127.0.0.1:8765  (lee la misma base; se puede dejar abierto siempre)
estado    conteos y costos por dominio
```

Garantías ya probadas con tests: reanuda si se corta, no reanaliza lo que no
cambió (huella de datos + versión del prompt), vence comercios a los 30 días y
los pone primero en la cola, frena a todos ante un límite de uso, corta la
corrida ante un error de credenciales, tope de gasto por corrida
(`--max-costo`), lotes recuperables.

**Lo que se probó de verdad (no simulado), en la nube, el 2026-10-06:**
`analizar animales --claude-code` sobre 2 items: "León / Panthera leo" y
"Tarántula" sin especie. León salió con confianza alta en la primera pasada;
Tarántula quedó "baja", fue a la segunda pasada con web y terminó lista.
3 análisis en 20 s, US$ 0,09 en total (modelo de la sesión: Sonnet 5.5). El
panel mostró la corrida en vivo.

Segunda prueba real, con el prompt corregido ("haz al menos una búsqueda"):
"Tarántula" sin especie (animales) y "Librería Hernández, Av. Corrientes 1436"
(comercios, un local real). Tarántula: pasada 1 sin web en 7,9 s (US$ 0,017),
quedó "baja"; pasada 2 con web en 15 s (US$ 0,057) citando EOL, CONICET y
Springer, estado UICN "VU" correcto. Librería Hernández: una pasada con web en
10 s (US$ 0,056), confianza alta, cuatro fuentes incluido el sitio propio,
"venta online" detectado. Total 31 s, US$ 0,13. Los costos coinciden con lo
estimado en `LOGISTICA_PARALELA.md` (la web multiplica por 3-4).

## 3. Tu plan de trabajo, en orden

### Paso 1. Reconocimiento (no cambies nada todavía)

Busca "Detector" en Otsutsuki y Pinkra y responde, con rutas concretas:

1. ¿Qué es Detector? (lenguaje, cómo se lanza, qué hace el ícono junto al reloj:
   dónde está el código que lo pone naranja).
2. ¿Cómo dispara hoy los análisis? (¿llama a `claude` por línea de comandos?
   ¿con qué prompt? ¿uno por vez? ¿dónde guarda la respuesta?).
3. ¿Dónde están las **fichas ya hechas** y en qué formato (markdown, JSON,
   carpetas por animal, una tabla)? ¿Cuántas hay por catálogo?
4. ¿Dónde está la **lista de pendientes** (lo que falta analizar)?
5. ¿Qué categorías y campos usan las fichas reales? (compáralas con
   `catalogo/dominios/animales.py`, `curiosidades.py`, `comercios.py`).
6. `claude auth status` → `authMethod`: `claude.ai` (cuenta) o `api_key`.
   `claude --version` (se necesita ≥ 2.1.259 por `--permission-prompts`).
7. Sistema operativo. En Windows, `claude` puede ser un `.cmd`: si
   `--claude-code` no lo encuentra, pasar `--ejecutable-claude` con la ruta
   completa.

Escribe las respuestas en `docs/RECONOCIMIENTO.md` del motor antes de seguir.

### Paso 2. Importar lo que ya existe

Escribe un conversor (`herramientas/exportar_fichas.py` o lo que corresponda al
lenguaje de Detector) que lea las fichas existentes y genere un JSONL con una
línea por ficha:

```json
{"registro": {"nombre": "León", "nombre_cientifico": "Panthera leo"},
 "ficha": {"ruta": "Mamíferos > Felinos", "nombre_comun": "León", "descripcion": "...", "confianza": "alta"}}
```

- `registro`: los datos de entrada tal como los acepta `normalizar()` del dominio
  (alias de columnas en cada clase; `nombre`/`nombre_cientifico` para animales,
  `titulo` para curiosidades, `nombre`+`direccion` para comercios).
- `ficha`: lo que tengas. Lo que falte se completa con valores neutros; si no
  trae `ruta` válida, se infiere de `categoria`/`rubro`/título por palabras
  clave y, si no, cae en "Otros".

```bash
python -m catalogo importar animales fichas_animales.jsonl --fuente catalogo-viejo
python -m catalogo estado
```

Verifica con `catalogar` que el catálogo exportado tenga sentido (orden,
categorías). Si muchas fichas caen en "Otros", ajusta la taxonomía (paso 4)
**antes** de importar en serio.

### Paso 3. Muestra de 20 (medir antes de decidir)

```bash
python -m catalogo ingerir animales pendientes_animales.csv --fuente detector
python -m catalogo panel --abrir            # en otra terminal; déjalo abierto
python -m catalogo analizar animales --claude-code --limite 20 --concurrencia 3 --estado-json estado.json
```

Compara esas 20 fichas con 20 hechas a mano por el flujo actual. Criterio
para seguir: igual o mejor en 18 de 20. Anota de `estado`: segundos por ficha,
búsquedas por ficha, costo (estimación de Claude Code) y cuántas quedaron
"para revisar". Repite para comercios con 20 locales reales (ahí la web es
obligatoria; mira que `fuentes_web` traiga URLs).

Si la calidad no alcanza, lo que se toca es, en este orden: `reglas` y
`reglas_web` del dominio, `max_busquedas`, `--esfuerzo` (`medium` → `high`),
`--modelo`. Cada cambio de prompt o esquema: **subir `version_prompt`** en la
clase del dominio, o las fichas viejas no se reanalizan.

### Paso 4. Adaptar los dominios a los catálogos reales

En `catalogo/dominios/*.py`:

- `TAXONOMIA`: que las hojas sean las categorías reales del catálogo del
  usuario, en el orden en que quiere verlas. Las hojas son un `enum` del
  esquema: el modelo no puede inventar otras.
- `propiedades()`: los campos reales de la ficha.
- `normalizar()`: los nombres de columna que exporta Detector.
- `prioridad_fuentes`: qué fuente gana en conflicto.
- Si hay un cuarto catálogo, es otra subclase de `Dominio` registrada en
  `catalogo/dominios/__init__.py`.

Mantén los tests verdes (`pytest`); agrega casos con datos reales anonimizados.

### Paso 5. Integrar Detector con el panel (lo "visual")

Dos formas, elegir según cómo esté hecho Detector:

**A. Detector consulta el panel por HTTP** (si Detector puede hacer una
petición cada pocos segundos): `GET http://127.0.0.1:8765/api/estado` devuelve
JSON (campos en §5). Lanzar `python -m catalogo panel` junto con Detector.

**B. Detector lee un archivo** (más simple, sin servidor): correr `analizar`
con `--estado-json ruta/estado.json`; el motor lo reescribe como mucho una vez
por segundo, de forma atómica. Detector lo lee y muestra lo que quiera.

Qué mostrar en lugar del ícono naranja, de menos a más:

1. **Color del ícono por `estado`**: `trabajando` verde (latiendo),
   `pausado` ámbar, `lotes` ámbar, `interrumpido`/`desconectado` rojo,
   `inactivo` gris.
2. **Tooltip o texto al lado**: `totales.listo / totales.total` (p. ej.
   "1.284 / 2.000"), `ritmo_por_min`, `eta_segundos` formateado,
   `totales.costo_usd`.
3. **Clic en el ícono** abre `http://127.0.0.1:8765` (el panel completo:
   progreso por catálogo, qué se está analizando ahora, actividad, errores).

El panel ya sirve como ventana propia; si Detector puede embeber un navegador,
embebe esa URL y listo.

### Paso 6. Dejar la rutina

- Semana: `analizar <dominios> --claude-code --concurrencia 3` para lo nuevo.
  Concurrencia 2-4 con cuenta: más no sirve, se topa con el límite del plan y
  el motor pausa solo.
- Mes: `analizar comercios --claude-code` (los vencidos a 30 días entran
  solos, primero en la cola).
- Si hay clave de API y volumen (miles): `analizar <dominio> --modo lotes
  --no-esperar` y después `recoger <dominio>`. Mitad de precio, < 24 h.
- `estado --errores` y la sección "Para revisar" de `catalogo.md` como tarea
  humana corta.

Si Detector lanza estos comandos él mismo, que pase siempre `--db` con una
ruta fija y `--estado-json` a donde Detector lee.

## 4. Formatos de intercambio

**Entrada (`ingerir`)**: CSV (UTF-8, con encabezado), JSONL o JSON. Una carpeta
por dominio y un archivo por fuente; el nombre del archivo es la fuente (o
columna `fuente` por fila). Columnas aceptadas (alias) por dominio:

| Dominio | Identidad | Columnas reconocidas |
|---|---|---|
| animales | `nombre_cientifico`, si no `nombre` | nombre/nombre_comun/animal/especie, nombre_cientifico/cientifico/scientific_name, imagen_url/imagen/foto, peso ("190 kg"), largo/tamano/longitud ("2.5 m"), notas/descripcion |
| curiosidades | `titulo` | titulo/título/nombre/tema, categoria/tipo/area, descripcion/texto/notas, anio/año/fecha, pais/lugar, imagen |
| comercios | `nombre` + `direccion` canónica (una sucursal = un item) | nombre/razon_social/comercio/local, direccion/domicilio, barrio, ciudad/localidad, rubro/categoria/tipo, descripcion/notas, horario, sitio_web/web/url, telefono/tel, imagen |

**Importación (`importar`)**: JSONL `{"registro": {...}, "ficha": {...}}` o
filas planas con todo mezclado (ver paso 2).

**Salida (`catalogar`)**: `salida/<dominio>/fichas.jsonl` (una ficha por línea
con `clave`, `titulo`, todos los campos del esquema, `datos` de entrada,
`fuentes`, `alias`, `modelo`, `vigente`, `completitud`), `catalogo.json` (árbol
de secciones + facetas + `revisar`) y `catalogo.md` legible.

## 5. API del panel (`/api/estado` y `--estado-json`)

```jsonc
{
  "hora": 1791308149.9,            // epoch
  "db": "catalogo.db",
  "estado": "trabajando",          // trabajando | pausado | lotes | interrumpido | inactivo
  "corrida": {"id": 7, "modo": "tiempo-real", "analizador": "claude-code", "concurrencia": 3,
              "inicio": 1791308000.0, "fin": null, "estado": "activa",
              "total": 120, "listos": 41, "errores": 1, "reintentos": 2, "costo_usd": 1.23},
  "totales": {"pendiente": 60, "en_curso": 3, "en_lote": 0, "verificar": 15, "listo": 41, "error": 1,
              "total": 120, "avance": 0.34, "costo_usd": 1.23, "busquedas": 30, "confianza_baja": 4},
  "dominios": {"animales": { /* mismos campos que totales + segundos_prom, tokens_* */ }},
  "ritmo_por_min": 6.2,
  "eta_segundos": 760,             // null si no hay ritmo
  "restantes": 78,
  "serie": [{"minuto": 1791308100, "listos": 5, "errores": 0}, ...],   // últimos 30 minutos
  "en_curso": [{"dominio": "animales", "clave": "panthera-leo", "titulo": "León", "segundos": 12}],
  "eventos": [{"ts": ..., "tipo": "listo", "dominio": "animales", "clave": "...", "detalle": {"titulo": "...", "segundos": 4.5, "costo_usd": 0.03, "busquedas": 1}}],
  "lotes": [], "errores_recientes": []
}
```

Tipos de evento: `fase`, `inicio`, `listo`, `verificar`, `error`, `reintento`,
`pausa`, `tope_costo`, `lote_enviado`, `lote_recibido`, `fin`.

## 6. Lo que NO está hecho (y cómo hacerlo si hace falta)

1. **Recolectores de fuentes estructuradas** (gratis, antes del modelo): Wikidata
   (QID, nombre científico, imagen P18, estado UICN P141), Wikipedia (extracto),
   GBIF (taxonomía) para enciclopedias; OpenStreetMap/Overpass (nombre,
   dirección, horario, web) y datos abiertos municipales para comercios. Bajan
   búsquedas y suben precisión. Diseño: un módulo por fuente en
   `catalogo/recolectores/`, que usa `ejecutar_en_paralelo` con 5-10
   simultáneos, `User-Agent` identificado, y guarda aportes con prioridad alta
   (`guardar_aportes`). Hazlo después de la muestra de 20, si las búsquedas
   por ficha son el costo dominante.
2. **Vía API con web, probada de verdad**: la combinación web_search +
   herramienta estricta `entregar_ficha` está escrita según la documentación
   pero solo probada con dobles. Si el usuario tiene clave de API, la primera
   corrida real debe ser `--limite 3` mirando `estado --errores`.
3. **Windows**: el subproceso `claude -p` y el servidor del panel no se probaron
   en Windows. Puntos a vigilar: ruta del ejecutable, `asyncio` con subprocesos
   (funciona con el loop por defecto de Python ≥ 3.8), codificación de la
   consola (`PYTHONUTF8=1` si aparecen acentos rotos).
4. **Imágenes locales en lotes**: viajan en base64 y engordan el lote (máx.
   256 MB). Con muchas fotos, usar URLs o la Files API.

## 7. Criterios de aceptación

- `pytest` verde después de tus cambios, con al menos un test por dominio
  usando datos reales (anonimizados si hace falta).
- Las fichas existentes importadas no se reanalizan (`analizar` reporta 0
  pendientes tras importar).
- Muestra de 20 por catálogo: calidad ≥ 18/20 contra el flujo actual, con los
  números (segundos, búsquedas, costo) anotados en `docs/RECONOCIMIENTO.md`.
- Panel abierto durante una corrida real muestra en curso, ritmo y ETA; Detector
  cambia de color según `estado` y muestra al menos listo/total.
- Un corte a mitad de corrida (Ctrl+C) y volver a lanzar: retoma sin repetir.

## 8. Decisiones del usuario que tienes que pedirle

1. Cuenta o clave de API (define si hay modo lotes y cuánta concurrencia).
2. Ciudades del catálogo de comercios (para las reglas de búsqueda).
3. Si el catálogo se publica (hay que mostrar las fuentes citadas).
4. Modelo: el de la sesión (hoy Sonnet 5.5 en la nube) u Opus 5.5 con
   `--modelo claude-opus-5-5`; comparar en la muestra de 20.
5. Qué categorías reales quiere ver y en qué orden (taxonomía).

## 9. Notas de lo verificado y lo dudoso

- Verificado con `claude -p` real: `--json-schema` devuelve la ficha en
  `structured_output`; `--output-format json` trae `total_cost_usd`,
  `usage.server_tool_use.web_search_requests`, `modelUsage` (de ahí sale el
  nombre del modelo). El motor lee exactamente esos campos.
- Resuelto: con el prompt "puedes buscar", el modelo no buscaba en la segunda
  pasada; con "haz al menos una búsqueda" buscó y citó fuentes (ver §2). Si en
  la PC vuelve a no buscar en algún dominio, el lugar para insistir es
  `reglas_web` de ese dominio.
- Contador de búsquedas con `--claude-code`: `claude -p` devuelve
  `web_search_requests: 0` aunque haya buscado (verificado con fichas que
  citan 3-4 URLs). El motor usa entonces la cantidad de fuentes citadas en
  `fuentes_web` como aproximación; en el panel, "Búsquedas web" es eso para
  esta vía. Con la API el contador es exacto.
- El límite de uso del plan llega como resultado con error de `claude -p`; el
  motor lo detecta por texto ("rate limit", "usage limit", "overloaded"…) y
  pausa 60 s a todos. Si en la PC el mensaje es distinto, ajustar
  `_SENAL_LIMITE` en `catalogo/core/analizador.py`.

## Mensaje de arranque sugerido (para pegar en la sesión local)

> Clona `https://github.com/whitrash/dantaylor.git` (rama
> `claude/parallel-catalog-analysis-logistics-f1y1id`) en `catalogos-motor/` y
> lee `docs/INFORME_PARA_CLAUDE_LOCAL.md`. Mis proyectos reales están en
> Otsutsuki y Pinkra, en el software "Detector". Sigue el plan del informe en
> orden: primero reconocimiento (sin cambiar nada), después importar las fichas
> existentes, muestra de 20 con el panel abierto, y recién ahí adaptar los
> dominios e integrar Detector con el panel. Pregúntame lo de la sección 8
> antes de la muestra.
