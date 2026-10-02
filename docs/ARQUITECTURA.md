# Logística compartida para catálogos

Dos proyectos:

- **Catálogo visual**: animales y curiosidades (arte, deporte, ciencia, historia).
- **Catálogo de comercios**: supermercados, librerías, almacenes, farmacias...

Este documento responde dos preguntas (¿se comparte la logística? ¿qué del
catálogo de comercios sirve para el visual?) y explica cómo funciona el motor
que está en este repositorio.

---

## 1. ¿Logística compartida o separada?

**Compartida en el motor, separada en el dominio.** Los dos proyectos hacen
exactamente el mismo recorrido, solo que con distintos datos:

```
recolectar  →  normalizar  →  identificar  →  analizar  →  clasificar  →  ordenar  →  publicar
```

| Etapa | Catálogo visual | Catálogo de comercios | ¿Se comparte? |
|---|---|---|---|
| Recolección | Wikipedia, GBIF, fotos propias | webs, relevamiento en el local, planillas | **El mecanismo sí** (CSV/JSONL por fuente, prioridad entre fuentes). Las fuentes no. |
| Identidad | nombre científico / título de la obra | nombre + dirección (cada sucursal es una) | **El mecanismo sí.** La regla no. |
| Análisis con IA | ficha de especie u obra | ficha de comercio | **Sí**: mismo motor, distinto esquema y prompt. |
| Paralelismo, reintentos, cupo de la API | igual | igual | **Sí, 100 %.** |
| Clasificación | árbol zoológico / temático | árbol de rubros | **Sí**: misma estructura de árbol, distinto contenido. |
| Vigencia | una especie no cambia | horarios y servicios cambian | **Sí**: un TTL por dominio (nunca vs. 30 días). |
| Orden | alfabético / cronológico | ciudad › barrio › nombre | **El mecanismo sí**, el criterio no. |

Por qué conviene compartir:

1. **Comparten el cupo de la API.** Los límites de pedidos por minuto son de la
   cuenta, no del proyecto. Dos sistemas separados se pisan y se llenan de
   errores 429; un solo motor con un solo limitador reparte el cupo y, si la API
   pide esperar, frena a todos juntos.
2. **Lo difícil se resuelve una sola vez**: retomar después de un corte, no
   pagar dos veces el mismo análisis, enviar lotes de miles, reintentar solo lo
   que tiene sentido reintentar.
3. **Sumar un catálogo nuevo** (plantas, farmacias, museos) es escribir una
   clase de ~100 líneas; la logística ya está.

Lo que **no** hay que compartir es la ficha. Forzar un mismo esquema para un
yaguareté y un supermercado es el error típico: cada dominio define sus campos,
su árbol y su orden.

En el código, `catalogo/core/` es el motor (no sabe nada de animales ni de
comercios) y `catalogo/dominios/` tiene una clase por catálogo.

---

## 2. Qué del catálogo de comercios sirve para el catálogo visual

Los catálogos de supermercados resolvieron hace tiempo problemas que el
catálogo visual también tiene. Todo esto ya está aplicado en el motor:

| Práctica de comercios | Cómo se aplica al catálogo visual | Dónde está |
|---|---|---|
| **Árbol de góndolas** (Almacén › Lácteos › Leches): vocabulario controlado | El modelo elige una hoja de un árbol fijo (Mamíferos › Felinos). El esquema de salida lo fuerza con un `enum`: **no puede inventar categorías**, y el orden del catálogo sale del orden del árbol. | `core/taxonomia.py`, `Dominio.esquema()` |
| **Código de barras (EAN)**: una identidad por producto | El "EAN" de un animal es su **nombre científico** (o un ID de Wikidata/GBIF). Hay dos niveles: antes del análisis (lo que dice la fuente) y después (lo que determina el modelo). Así, "Puma" y "León de montaña" terminan siendo **una ficha con un alias**. | `Dominio.clave()`, `Animales.clave_catalogo()` |
| **Registro maestro con varias fuentes** (ficha del fabricante + del distribuidor) | Cada fuente (Wikipedia, GBIF, UICN, fotos propias) guarda su aporte por separado; la ficha se arma combinándolos y, en conflicto, gana la fuente de más prioridad. Recargar una fuente no pisa a las otras. | tabla `aportes`, `Dominio.fusionar()` |
| **Normalización** ("1 L" = "1000 ml"; "Av." = "Avenida") | "190 kg", "2.5 m", "León"/"leon", "Ñandú"/"nandu" quedan iguales. | `core/texto.py` |
| **Ficha con atributos por rubro** + **completitud** | Cada dominio define sus campos; cada ficha tiene un puntaje de completitud (incluye si tiene imagen). | `Dominio.propiedades()`, `catalogo.completitud()` |
| **Filtros facetados** (marca, precio, tamaño) | Continente, dieta, estado de conservación; época y país para curiosidades. | `Dominio.facetas` |
| **Cola de revisión** de fichas dudosas | Lo de confianza baja, incompleto o vencido va a una lista "Para revisar". | `catalogo.construir()` |
| **Reglas antes que IA** (clasificar por palabras clave) | Cada hoja del árbol tiene palabras clave; sirve como clasificador gratuito y para probar sin costo. | `Taxonomia.sugerir()` |

Y al revés: lo del catálogo visual que sirve a comercios es el **análisis de
imágenes** (foto de la fachada o de la góndola). El mismo campo `imagen_url`
funciona en los tres dominios.

---

## 3. Cómo se analiza en paralelo

```
 ejemplos/<dominio>/<fuente>.csv|jsonl
          │  ingerir: normalizar → clave → combinar fuentes
          ▼
 SQLite ── items (pendiente) + aportes por fuente
          │  analizar
          ├── tiempo real: N trabajadores asyncio, UN limitador compartido
          │     por todos los dominios, reintentos con backoff, pausa
          │     global ante 429; cada resultado se guarda al instante
          │
          └── lotes: Message Batches API (hasta 100.000 por lote,
                50 % más barato, < 24 h). El id del lote se guarda:
                si el proceso se corta, se retoma sin reenviar
          ▼
 items (listo | error)
          │  catalogar: identidad final → orden → árbol → facetas → revisión
          ▼
 salida/<dominio>/catalogo.json · catalogo.md · fichas.jsonl
```

En tiempo real, los items de distintos dominios se **intercalan** (animal,
comercio, curiosidad, animal...) en un único grupo de trabajadores, así que
ningún proyecto espera a que termine el otro.

### Qué modo usar

| Situación | Modo |
|---|---|
| Menos de ~1000 items, o el resultado hace falta ya | `--modo tiempo-real` |
| Miles de animales u obras de una sola vez | `--modo lotes` |
| Refresco mensual de comercios | `--modo lotes --no-esperar`, y después `recoger` |
| Sin un criterio claro | `--modo auto` (lotes desde `--umbral-lotes`, 1000 por defecto) |
| Items rechazados en un lote | `--reintentar-errores --modo tiempo-real` (en tiempo real hay *fallback* a otro modelo; en lotes no existe) |

`--concurrencia` (pedidos simultáneos) y `--por-minuto` (tope de ritmo) se
ajustan a los límites de la cuenta de la API. Si igual llega un 429, el motor
lee el `retry-after` y frena a todos los trabajadores.

### Costos

1. **Lotes**: 50 % menos por token.
2. **No pagar dos veces**: cada item tiene una huella (datos + `version_prompt`).
   Si no cambió, no se reanaliza. Para forzar un reanálisis general después de
   cambiar el prompt o el esquema, se sube `version_prompt` del dominio.
3. **Caché de prompts**: el prompt de sistema (reglas + árbol) es idéntico para
   todos los items de un dominio y va marcado para caché. Solo se activa por
   encima de un tamaño mínimo de prefijo, que depende del modelo; con árboles
   grandes se aprovecha más.
4. **Esfuerzo**: por defecto `medium`. Antes de bajarlo a `low` en todo un
   dominio, conviene comparar la calidad sobre una muestra (`--limite 20`).

---

## 4. Garantías

- **Reanudable**: si se corta (Ctrl+C, caída), la próxima corrida retoma; lo
  terminado no se repite y los lotes enviados se recogen sin reenviar.
- **Idempotente**: volver a cargar las mismas fuentes no genera trabajo nuevo.
- **Errores clasificados**: red, 429 y 5xx se reintentan; un rechazo del modelo,
  una respuesta cortada o una ficha inválida van a `error` con el motivo
  (`python -m catalogo estado --errores`).
- **Fichas válidas**: salida estructurada con esquema JSON + validación propia
  (la ruta tiene que existir en el árbol).

---

## 5. Cómo conectar los proyectos existentes

1. Exportar los datos de cada fuente a CSV o JSONL, en
   `<carpeta>/<dominio>/<fuente>.csv` (el nombre del archivo es la fuente, que
   define la prioridad). Los nombres de columna son flexibles: cada dominio
   acepta alias (`nombre`, `nombre_comun`, `especie`, `animal`...).
   También se puede llamar a `pipeline.ingerir()` desde Python con diccionarios.
2. Ajustar a cada catálogo real: el árbol (`TAXONOMIA`), los campos de la ficha
   (`propiedades()`), las reglas del prompt (`reglas`) y la prioridad de fuentes.
3. Para sumar un catálogo: crear `catalogo/dominios/<nuevo>.py` con una
   subclase de `Dominio` y registrarla en `catalogo/dominios/__init__.py`.

## 6. Límites y próximos pasos

- **Una máquina**: SQLite alcanza para cientos de miles de items en una
  máquina. Para repartir el trabajo entre varias máquinas habría que cambiar
  `Almacen` por Postgres (con `SELECT ... FOR UPDATE SKIP LOCKED` como cola);
  los dominios no cambian.
- **Imágenes locales** viajan en base64 y engordan los lotes (máx. 256 MB): con
  muchas fotos, mejor URLs públicas o la Files API.
- **Pre-clasificación**: hoy las palabras clave solo se usan en modo simulado;
  podrían usarse para mandar al modelo solo lo que las reglas no resuelven.
