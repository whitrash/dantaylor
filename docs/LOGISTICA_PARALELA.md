# Logística de análisis en paralelo para los catálogos de comercios y enciclopedias

Análisis de cómo aplicar el motor de `catalogo/` a los dos catálogos reales,
con los datos que cambian el diseño respecto de `ARQUITECTURA.md`:

- hoy el análisis se hace con **Claude Code en la computadora**, de a un item,
  y **busca en internet** en los dos catálogos;
- no está definido si Claude entra con **cuenta** (suscripción) o con **clave
  de API**.

"Enciclopedias" agrupa los dominios `animales` y `curiosidades`; "comercios"
es el dominio `comercios`.

Los precios y límites citados se verificaron el 2026-10-06 en la documentación
oficial. Los costos por item son **estimaciones**: hay que medirlos sobre una
muestra de 20 antes de procesar volumen (sección 8).

---

## 0. Resumen

1. **El cuello de botella es la búsqueda web, no el modelo.** Una ficha sin web
   cuesta centavos y tarda segundos; con web cuesta 3 a 5 veces más y tarda
   un minuto. Paralelizar baja el tiempo, no el costo. Lo que baja el costo es
   **decidir por dominio y por campo cuándo hace falta la web**.
2. **Enciclopedias: dos pasadas.** Primera pasada sin web, en lote (mitad de
   precio), para todo. Segunda pasada con web solo para lo dudoso o volátil
   (20-30 % de los items). Antes de ambas, traer gratis y en paralelo los datos
   estructurados de Wikidata, Wikipedia y GBIF.
3. **Comercios: fuentes estructuradas primero, web acotada después.**
   OpenStreetMap y datos abiertos municipales dan dirección, rubro y horario sin
   costo; la búsqueda web de Claude queda para completar y confirmar, limitada
   a 2-3 búsquedas por comercio y localizada a la ciudad.
4. **Dos vías de ejecución, un solo motor.** Con cuenta: lanzar varias copias
   de `claude -p` en paralelo (sin costo extra, pero limitado por el plan y sin
   modo lote). Con clave de API: el motor actual, con lotes y caché. La cola,
   el estado, la deduplicación y el catálogo son los mismos en las dos vías.
5. **Nada se paga dos veces.** Las fichas que ya existen se importan como
   analizadas; los comercios vencidos se reverifican solo en los campos que
   cambian; las enciclopedias no vencen.

---

## 1. Punto de partida

Lo que se asume del flujo actual (no vi el código; corregir lo que no aplique):

| | Enciclopedias | Comercios |
|---|---|---|
| Cómo se analiza hoy | Claude Code interactivo, un animal/obra por vez, con búsqueda web | Igual, un comercio por vez, con búsqueda web |
| Qué aporta la web | Confirmar datos, imagen, estado de conservación, récords | Casi todo: existencia, dirección, horario, servicios, rubro |
| Resultado | Archivos locales (markdown/JSON) por ficha | Igual |
| Volumen probable | Miles de items, una vez; después goteo | Cientos a miles por ciudad; se renuevan |
| Credenciales | Cuenta de Claude o clave de API (sin definir) | Igual |

Tiempo por item hoy: el de una conversación interactiva con 2-5 búsquedas,
~1-3 minutos, uno a la vez. Mil items son días de trabajo atendido.

---

## 2. Dónde está el cuello de botella

Cada ficha consume tres recursos. Los números son para Claude Opus 5.5
(US$ 4 / 20 por millón de tokens de entrada / salida; lote: 2 / 10; búsqueda
web: US$ 10 por cada 1.000 búsquedas, sin descuento por lote; `web_fetch` sin
costo extra, solo tokens).

| Recurso | Ficha sin web | Ficha con web (2-3 búsquedas) |
|---|---|---|
| Tokens de entrada (sin contar el prompt cacheado) | ~1.500 | ~8.000-12.000 (resultados filtrados) |
| Tokens de salida (ficha + razonamiento) | ~1.500-2.500 | ~2.500-3.500 |
| Búsquedas | 0 | 2-3 (US$ 0,02-0,03) |
| **Costo estimado, tiempo real** | **US$ 0,04-0,06** | **US$ 0,10-0,14** |
| **Costo estimado, lote** | **US$ 0,02-0,03** | **US$ 0,06-0,09** |
| Latencia por item | 10-30 s | 40-120 s |

Dos consecuencias:

- **La web multiplica el costo por 3-5 y la latencia por 4.** En un catálogo
  de 10.000 animales, la diferencia entre "siempre web" y "web solo cuando hace
  falta" es de cientos de dólares.
- **El paralelismo no cambia el costo; cambia el tiempo.** 2.000 comercios a
  60 s cada uno son 33 horas en secuencia y ~2 horas con 16 trabajadores.

Los límites de la API en el nivel inicial (Start) para Opus 5.5 son 1.000
pedidos/min, 2 M tokens de entrada/min (**los tokens leídos de caché no
cuentan**) y 400 K tokens de salida/min. Con fichas de ~2.000 tokens de salida,
el tope teórico es ~200 fichas/min: muy por encima de lo que la latencia de la
búsqueda web permite. Es decir: con clave de API, **el límite práctico es la
latencia, no el cupo**, y conviene subir la concurrencia (16-32) en vez de
preocuparse por el ritmo. Dos salvedades: las organizaciones nuevas pueden
empezar en un nivel de evaluación con límites menores, y hay límites de
aceleración que penalizan los saltos bruscos de tráfico: subir la concurrencia
de a poco (`--por-minuto`). El nivel Start tiene un tope de gasto mensual de
US$ 500.

### Qué necesita web, por campo

| Dominio | Campo | ¿Necesita web? | Fuente mejor que la búsqueda |
|---|---|---|---|
| animales | nombre científico, taxonomía, dieta, hábitat, descripción | No (conocimiento estable) | Wikidata / GBIF (gratis, estructurado) |
| animales | imagen | No hace falta buscar | Wikimedia Commons vía Wikidata (P18) |
| animales | estado de conservación (UICN) | Cambia cada pocos años | Wikidata (P141) o lista roja; web solo si falta |
| animales | tamaño, peso | No | Wikidata / Wikipedia |
| curiosidades | año, país, personas, resumen | No, salvo items oscuros | Wikidata / Wikipedia |
| curiosidades | récords deportivos, "el más grande/rápido" | Sí (se superan) | web, 1-2 búsquedas |
| comercios | existencia, dirección, rubro | Sí o fuente estructurada | OpenStreetMap (Overpass), datos abiertos municipales, Google Places si hay clave |
| comercios | horario, teléfono, servicios | Sí | sitio propio / redes vía `web_fetch` (sin costo extra); OSM si está cargado |
| comercios | descripción, productos destacados | Sí | web, 1-2 búsquedas localizadas |
| comercios | formato (cadena/independiente), rango de precios | No (lo infiere el modelo) | — |

Regla práctica: **todo lo que se pueda traer de una API estructurada se trae
antes y se le da al modelo como contexto**. El modelo queda para lo que las
fuentes no resuelven: clasificar, redactar, unificar y detectar contradicciones.

---

## 3. Dos vías para correr en paralelo

### Vía A: API directa (el motor actual, `AnalizadorClaude`)

Requiere una clave de API (console de Anthropic, pago por uso).

- Salida estructurada con esquema, prompt de sistema en caché, `fallbacks`
  ante rechazos.
- Búsqueda web del lado del servidor: `web_search_20260209` (filtra los
  resultados con código antes de meterlos en el contexto; eso baja los tokens)
  con `max_uses`, `user_location` (ciudad) y `allowed_domains` /
  `blocked_domains`. `web_fetch_20260209` para leer una URL concreta, con
  `max_content_tokens`.
- **Modo lote** (Message Batches): hasta 100.000 pedidos por lote, mitad de
  precio en tokens, resultados en menos de 24 h. **Acepta búsqueda web** (al
  mismo precio por búsqueda; las búsquedas en lote se regulan por organización,
  así que un lote con muchas búsquedas puede tardar más).
- Límites verificados (nivel Start): 1.000 pedidos/min; lotes: hasta 200.000
  pedidos en cola.

### Vía B: Claude Code local sin interfaz (`claude -p`), varias copias a la vez

Usa lo que ya está instalado y la cuenta con la que se entra hoy. Verificar
con `claude auth status`: `authMethod` dice `claude.ai` (cuenta) o `api_key`.

Comando por item (lo lanza el motor como subproceso, N a la vez):

```bash
claude -p "$(cat item.json)" \
  --append-system-prompt-file instrucciones_animales.txt \
  --json-schema "$(cat esquema_animales.json)" \
  --output-format json \
  --tools "WebSearch,WebFetch" \
  --allowedTools "WebSearch,WebFetch" \
  --permission-prompts none \
  --max-turns 8 \
  --max-budget-usd 0.50 \
  --no-session-persistence \
  --effort medium
```

- `--json-schema` devuelve la ficha validada en `structured_output` (el mismo
  `esquema()` del dominio sirve tal cual: la ruta sigue siendo un `enum`).
- `--output-format json` trae `total_cost_usd` (estimación del cliente) y
  `session_id`.
- `--tools` restringe a las dos herramientas de web (sin Bash ni edición de
  archivos); `--allowedTools` las pre-aprueba; `--permission-prompts none`
  niega cualquier otra cosa en vez de quedarse esperando.
- `--max-turns` y `--max-budget-usd` acotan un item que se va por las ramas.
- `--no-session-persistence` evita guardar miles de transcripciones en
  `~/.claude`.
- **No usar `--bare`**: arranca más rápido pero no usa la cuenta, exige clave
  de API.

Limitaciones:

- **Sin modo lote ni control de caché**: todo es tiempo real a precio pleno
  (si es clave de API) o contra los límites del plan (si es cuenta).
- **Límites del plan**: con cuenta, las copias en paralelo consumen la misma
  ventana de uso. En la práctica, 2-4 copias a la vez; una carga de miles de
  items va a toparse con el límite y tendrá que esperar a que se renueve. El
  motor lo trata como una pausa global, igual que un 429.
- **Arranque por item**: cada `claude -p` levanta un proceso completo (carga
  CLAUDE.md, hooks, MCP del directorio). Conviene correrlo desde una carpeta
  vacía dedicada, para que no cargue nada ajeno.
- Detección de errores: el resultado JSON trae `is_error` y `subtype`; un
  límite de uso llega como resultado con error (no como excepción). El motor
  tiene que leer ese texto para distinguir "pausar a todos" de "este item falló".

### Comparación

| | Vía A: API | Vía B: `claude -p` |
|---|---|---|
| Costo | Pago por uso; lote a mitad de precio | Incluido en el plan hasta su límite |
| Concurrencia práctica | 16-32 (más, pidiendo límites) | 2-4 |
| Volumen por día | Decenas de miles (lote) | Decenas a pocos cientos |
| Búsqueda web | Sí, con filtrado y localización | Sí (las herramientas de siempre) |
| Salida estructurada | Sí | Sí (`--json-schema`) |
| Caché del prompt | Sí (lectura a 5 % del precio) | No controlable |
| Reanudar, deduplicar, catálogo | Motor | Motor (igual) |
| Qué hace falta | Clave de API y crédito | Nada nuevo |

**Recomendación: las dos, con el mismo motor.** Se agrega un tercer analizador
(`AnalizadorClaudeCode`) que lanza `claude -p`. Regla de uso:

- **Goteo** (lo nuevo de la semana, reintentos, lo que vuelve de revisión):
  vía B, 3 copias, sin costo extra.
- **Volumen** (carga inicial de enciclopedias, refresco mensual de comercios):
  vía A en lote. Si no hay clave, la vía B lo hace igual, solo que en días en
  vez de horas.

Vías consideradas y descartadas: Managed Agents (sesiones con sandbox; no hace
falta un sandbox para esto y suma costo por hora) y meter varios items en un
mismo pedido (ahorra poco con el prompt ya en caché, y un error arrastra a
todos los items del pedido; solo tendría sentido para una preclasificación
barata, que las reglas por palabras clave ya resuelven).

---

## 4. Enciclopedias (animales, curiosidades)

Propiedad clave: **el conocimiento es estable**. Un animal se analiza una vez
(`ttl_dias = None`) y el modelo ya sabe casi todo; la web sirve para confirmar,
no para descubrir.

### Pipeline

```
1. recolectar (gratis, HTTP en paralelo, sin modelo)
   Wikidata: QID, nombre científico, imagen (P18), estado UICN (P141), masa, longitud
   Wikipedia (REST summary): extracto + miniatura
   GBIF: taxonomía aceptada, sinónimos
        │  10-20 pedidos simultáneos por fuente, User-Agent identificado
        ▼
2. pasada 1: ficha completa SIN web, en lote (vía A) o tiempo real (vía B)
   Entrada: datos recolectados + registro propio. El prompt dice:
   "no busques; si no estás seguro, confianza media/baja".
        │
        ▼
3. pasada 2: verificación CON web, solo para:
   - confianza "baja" o "media",
   - campos marcados volátiles (estado UICN sin dato en Wikidata; récords),
   - items que las fuentes estructuradas no encontraron.
   max_uses = 2, prompt: "verificá solo estos campos: ...".
        │
        ▼
4. catalogar (identidad final por QID/nombre científico; alias; facetas; revisión)
```

### Identidad

El "código de barras" pasa a ser el **QID de Wikidata** cuando existe (resuelve
sinónimos, nombres comunes en varios idiomas y cambios de nomenclatura); el
nombre científico queda como respaldo. Para curiosidades, el QID de la obra o
del hecho cumple el mismo papel.

### Números estimados (10.000 items, Opus 5.5)

| Etapa | Items | Costo unitario | Total | Tiempo |
|---|---|---|---|---|
| Recolección estructurada | 10.000 | 0 | 0 | 20-40 min (limitado por cortesía hacia las APIs) |
| Pasada 1 en lote | 10.000 | US$ 0,02-0,03 | **US$ 200-300** | < 24 h, normalmente ~1 h |
| Pasada 2 con web (25 %) | 2.500 | US$ 0,06-0,09 (lote) | **US$ 150-225** | < 24 h |
| **Total** | | | **~US$ 350-525** | **1-2 días calendario, sin atención** |

Si se hiciera todo con web y en tiempo real: ~US$ 1.000-1.400 y ~10 h con 16
trabajadores. La diferencia es el argumento para las dos pasadas.

Con la vía B (cuenta), el mismo trabajo se reparte en varios días de goteo
automático; no hay costo marginal pero sí espera por los límites del plan.

### Ajustes específicos

- `politica_web = "si_dudoso"` para los dos dominios.
- Campos volátiles: `estado_conservacion` (animales); `dato_curioso` cuando
  menciona un récord (curiosidades).
- Guardar las URLs citadas por la búsqueda web en la ficha (`fuentes_web`): la
  API las devuelve sin costo de tokens y sirven para auditar.
- Imágenes: usar la URL de Commons que da Wikidata en vez de pedirle al modelo
  que la busque; se le puede pasar la imagen al modelo para que confirme que
  corresponde al animal (vía A: bloque `image` por URL; ya soportado).

---

## 5. Comercios

Propiedad clave: **los datos son locales y cambian**. El modelo no sabe nada de
"Almacén Los Primos, Pasaje Roma 45"; todo viene de afuera y caduca.

### Pipeline

```
1. recolectar (gratis o barato, HTTP en paralelo)
   OpenStreetMap / Overpass: comercios por ciudad o barrio con shop=*, nombre,
     dirección, opening_hours, phone, website (cobertura variable; muy buena en
     ciudades grandes)
   Datos abiertos municipales (habilitaciones comerciales) si existen
   Google Places API si hay clave (pago, pero estructurado y actual)
   Sitio propio / redes: web_fetch de la URL conocida (sin costo extra)
        │
        ▼
2. análisis CON web acotada (siempre), vía A o B
   web_search_20260209 con:
     max_uses = 3
     user_location = {city, region, country}  (resultados de ESA ciudad)
     blocked_domains = agregadores de baja calidad (lista corta, ajustable)
   Prompt: "confirmá que existe y está abierto; completá horario y servicios
   solo con fuentes; si no encontrás nada, confianza baja y no inventes".
        │
        ▼
3. catalogar (clave = nombre + dirección canónica; facetas ciudad/barrio/rubro)
        │
        ▼
4. refresco mensual (ttl_dias = 30): reverificación PARCIAL
   Solo campos volátiles: existencia, horario, teléfono, servicios.
   1 búsqueda + fetch del sitio; la descripción y el rubro no se rehacen.
```

### Números estimados (2.000 comercios, Opus 5.5)

| Escenario | Costo unitario | Total | Tiempo (16 trabajadores) |
|---|---|---|---|
| Sin recolección previa, 3 búsquedas, tiempo real | US$ 0,10-0,14 | **US$ 200-280** | 1,5-4 h |
| Con OSM previo, 1-2 búsquedas, tiempo real | US$ 0,06-0,09 | **US$ 120-180** | 1-2,5 h |
| Igual, en lote | US$ 0,04-0,06 | **US$ 80-120** | < 24 h |
| Refresco mensual parcial (1 búsqueda, salida corta), lote | US$ 0,02-0,04 | **US$ 40-80 / mes** | < 24 h |

### Ajustes específicos

- `politica_web = "siempre"`, pero con `max_uses = 3` y localización.
- Identidad: ya es nombre + dirección canónica (una sucursal = un item).
  Sumar el `osm_id` / `place_id` cuando la recolección lo trae.
- Un comercio sin ninguna presencia en la web va a "Para revisar" con confianza
  baja; es mejor una ficha vacía que una inventada.
- Si el catálogo se publica, mostrar las fuentes citadas (la API lo exige para
  resultados de búsqueda mostrados a usuarios finales).

---

## 6. Lo que se comparte entre los dos catálogos

- **Una cola, un cupo.** Animales, curiosidades y comercios entran intercalados
  en el mismo grupo de trabajadores y comparten el limitador de ritmo. Lo que
  falta: **prioridades**. Los comercios vencidos van primero (caducan); la carga
  masiva de enciclopedias va de fondo, en lote.
- **Un limitador por fuente externa.** Wikimedia, OSM y la API de Claude tienen
  límites distintos; `LimitadorDeTasa` ya admite instancias separadas.
- **Checkpoints y reanudación** (ya hechos): cada ficha se guarda apenas llega;
  un corte no pierde lo hecho; los lotes se recogen en otra corrida.
- **No pagar dos veces** (ya hecho): huella por item + versión del prompt; TTL
  por dominio.
- **Cola de revisión única**, con el motivo (confianza baja, incompleto,
  vencido, sin fuentes).
- **Tope de gasto** por corrida (nuevo): sumar `usage` (vía A) o
  `total_cost_usd` (vía B) y detenerse al llegar al tope.

---

## 7. Cambios concretos en el motor

En orden de valor sobre esfuerzo. Tamaños aproximados.

| # | Cambio | Para qué | Estado |
|---|---|---|---|
| 1 | `importar <dominio> <archivos>`: cargar las fichas ya hechas como `listo` | No volver a pagar lo que ya está analizado | **Hecho** (`pipeline.importar`) |
| 2 | `AnalizadorClaudeCode`: subproceso `claude -p` con `--json-schema`; lee `structured_output`, `total_cost_usd`, `usage`; distingue límite de uso (pausa global) de error del item | Vía B con el mismo motor | **Hecho y probado con `claude -p` real** (`--claude-code`) |
| 3 | `politica_web` por dominio + herramientas `web_search_20260209` / `web_fetch_20260209` + ficha por herramienta estricta `entregar_ficha`; `pause_turn` se continúa en tiempo real y se reencola en lotes | Vía A con web | **Hecho** (probado con dobles; falta corrida real con clave) |
| 4 | Etapa `recolectar`: un módulo por fuente (`wikidata`, `wikipedia`, `gbif`, `overpass`) | Menos búsquedas, más precisión | Pendiente (diseño en el informe para el Claude local, §6) |
| 5 | Estado `verificar` (segunda pasada) + `campos_volatiles` por dominio + `fuentes_web` en la ficha | Dos pasadas en enciclopedias; una con web en comercios | **Hecho** (`estado_tras_analisis`) |
| 6 | Columna `prioridad` en la cola | Comercios vencidos antes que carga masiva | **Hecho** (`vencer` pone prioridad 1) |
| 7 | `--max-costo` por corrida | Tope de gasto | **Hecho** (no arranca items nuevos al llegar al tope) |
| 8 | Campo `qid` / `osm_id` en la identidad | Deduplicación más robusta | Pendiente (va con el cambio 4) |
| 9 | Métricas por item (segundos, tokens, búsquedas, costo), `corridas` y `eventos` en la base | Saber qué cuesta y qué pasa | **Hecho** |
| 10 | Panel visual (`python -m catalogo panel`) + `--estado-json` para otros programas | Reemplazar el ícono naranja por progreso, ritmo, ETA, costo, actividad | **Hecho** (`core/panel.py`, `core/panel.html`) |

Lo que no cambió en esta ronda: `taxonomia.py` (salvo que el nombre de la hoja
también cuenta como palabra clave), `catalogo.py`, `texto.py`.

---

## 8. Plan por etapas

**Etapa 0 (un día): medir antes de decidir.**

1. `claude auth status` → saber si hay cuenta o clave.
2. Exportar las fichas existentes de los dos proyectos a CSV/JSONL e importarlas
   (`importar-fichas`), para que no se reanalicen.
3. Exportar los items pendientes como `<dominio>/<fuente>.csv`.
4. Muestra de 20 items por catálogo, `--limite 20`, con la vía disponible.
   Comparar contra 20 fichas hechas a mano hoy: ¿misma calidad? ¿qué campos
   fallan? Anotar costo real (`usage` o `total_cost_usd`) y tiempo por item.

Criterio para seguir: calidad igual o mejor en 18 de 20, y costo por item
dentro del rango estimado. Si no, ajustar prompt/política y repetir.

**Etapa 1 (dos o tres días): ajustar.**

- Política web por dominio; `max_uses`; `esfuerzo` (`medium` por defecto;
  probar `low` en comercios, que es más clasificación que razonamiento).
- Decidir modelo por pasada. Opus 5.5 por defecto; Sonnet 5.5 (mitad de precio)
  es candidato para la pasada 1 de enciclopedias y para el refresco de
  comercios, **solo si la muestra muestra igual calidad**.
- Recolectores estructurados (Wikidata/GBIF; Overpass) y medir cuánto bajan las
  búsquedas.

**Etapa 2: volumen.**

- Enciclopedias: pasada 1 en lote (noche), pasada 2 en lote al día siguiente.
- Comercios: por ciudad, en lote si no urge; tiempo real para una ciudad chica.
- Subir la concurrencia de a poco (8 → 16 → 32) mirando los 429.

**Etapa 3: rutina.**

- Semanal: `analizar` de lo nuevo por vía B (goteo, sin costo extra).
- Mensual: `vencer` + reverificación parcial de comercios en lote.
- `estado --errores` y la cola "Para revisar" como tarea humana corta.

---

## 9. Riesgos y cómo se cubren

| Riesgo | Señal | Cobertura |
|---|---|---|
| Búsqueda web deshabilitada en la organización (Console) | 400 "web search is not enabled" | Revisar Settings → Capabilities antes de la muestra |
| Nivel de evaluación / límites de aceleración en una cuenta de API nueva | 429 frecuentes al subir concurrencia | `--por-minuto` bajo al principio; subir en escalones |
| Tope de gasto mensual (US$ 500 en Start) | 429 sin `retry-after`, `enforced_spend_limit_reached` | `--max-costo`; el motor lo detecta como fatal, no como reintentable |
| Límite del plan en vía B | `claude -p` devuelve resultado con error de límite | Pausa global y reanudación automática; concurrencia 2-4 |
| Lote con búsqueda web lento (regulado por organización) | Lote tarda horas | Normal; no reenviar; `recoger` cuando termine |
| `pause_turn` en un resultado de lote | `stop_reason == "pause_turn"` | Reencolar ese item a tiempo real |
| Cortesía con Wikimedia / OSM | 429 o bloqueo de IP | User-Agent identificado, 5-10 simultáneos, limitador propio |
| Comercio sin presencia web | Ficha vacía, confianza baja | Cola de revisión; el prompt prohíbe inventar |
| Tokenizador nuevo (4.7+) usa ~30 % más tokens | Estimaciones cortas | Medir con la muestra de 20; las cifras de este documento son rangos |
| Publicar resultados con citas | Obligación de mostrar fuentes | `fuentes_web` guardado en cada ficha |

---

## 10. Decisiones pendientes del dueño del proyecto

1. **Cuenta o clave de API** (sección 3). Define si hay modo lote.
2. **Volumen real** por catálogo y cuántos items nuevos por semana.
3. **Ciudades** del catálogo de comercios (para `user_location` y Overpass).
4. **Si el catálogo se publica** (por las citas de fuentes).
5. **Modelo**: Opus 5.5 en todo, o Sonnet 5.5 en las pasadas más mecánicas si
   la muestra lo justifica.
