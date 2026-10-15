# Instrucciones para el bot recolector de datos

Pegá este documento completo al bot que recolecta datos (Grok u otro). Define
**qué archivos tiene que producir y con qué forma** para que el motor de
catálogos los cargue directamente con `python -m catalogo ingerir`.

---

## Tu tarea

Recolectás **datos crudos** de dos catálogos y los entregás en archivos. No
redactás fichas, no clasificás, no inventás: eso lo hace otro paso. Tu trabajo
es juntar registros con la mayor cantidad de campos verificables posible, y
decir de dónde salió cada uno.

Catálogos:

1. **animales** (enciclopedia de fauna)
2. **curiosidades** (arte, deporte, ciencia, historia)
3. **comercios** (supermercados, librerías, locales de barrio de una ciudad)
4. **ofertas** (un producto, en un comercio, a un precio, **con su enlace**)

## Formato de entrega

- Un archivo por catálogo **y por fuente**: `<catalogo>/<fuente>.csv` o
  `<catalogo>/<fuente>.jsonl`. Ejemplos: `animales/wikipedia.csv`,
  `animales/gbif.jsonl`, `comercios/openstreetmap.csv`,
  `comercios/relevamiento.csv`. El nombre del archivo **es** la fuente; se usa
  para resolver conflictos (una fuente más confiable gana).
- CSV: UTF-8, con fila de encabezados, separador coma, valores con comas o
  saltos de línea entre comillas dobles.
- JSONL: un objeto JSON por línea, mismas claves que las columnas.
- Un registro por fila. Si la misma cosa aparece en dos fuentes, va en los dos
  archivos (el motor las combina). No dupliques dentro de un mismo archivo.
- Campos desconocidos: dejalos **vacíos**. Nunca pongas "N/A", "desconocido",
  "?" ni un valor inventado.
- Texto en español. Nombres propios y científicos con su grafía original.
- No incluyas columnas que no estén en las tablas de abajo (se ignoran, pero
  ensucian).

## Catálogo `animales`

| Columna | Obligatoria | Qué es | Ejemplo |
|---|---|---|---|
| `nombre` | sí (si no hay científico) | nombre común en español | `Aguará guazú` |
| `nombre_cientifico` | muy recomendable | binomial `Género especie` | `Chrysocyon brachyurus` |
| `imagen_url` | no | URL pública de una foto (preferir Wikimedia Commons) | `https://upload.wikimedia.org/...jpg` |
| `peso` | no | peso adulto típico, con unidad | `23 kg`, `150 t`, `800 g` |
| `largo` | no | longitud adulta típica, con unidad | `1.2 m`, `35 cm` |
| `notas` | no | texto libre corto con lo que sepas (hábitat, dieta, región) | `Cánido de los pastizales del centro de Sudamérica` |

Identidad: el nombre científico. Si dos filas tienen el mismo científico, son
el mismo animal aunque el nombre común cambie. Si solo tenés el nombre común,
ponelo igual; el motor lo resuelve después.

Fuentes preferidas, en este orden: GBIF (`gbif`), UICN (`uicn`), Wikidata
(`wikidata`), Wikipedia (`wikipedia`). Usá ese nombre de archivo para que la
prioridad funcione.

```csv
nombre,nombre_cientifico,imagen_url,peso,largo,notas
Aguará guazú,Chrysocyon brachyurus,https://upload.wikimedia.org/wikipedia/commons/1/10/Chrysocyon_brachyurus.jpg,23 kg,1 m,Cánido de pastizales; piernas largas; Sudamérica central
Yacaré overo,Caiman latirostris,,60 kg,2 m,Cocodrilo de ríos y esteros del norte argentino
```

## Catálogo `curiosidades`

| Columna | Obligatoria | Qué es | Ejemplo |
|---|---|---|---|
| `titulo` | sí | nombre corto y reconocible de la obra, hecho o récord | `La noche estrellada` |
| `categoria` | recomendable | una o dos palabras: pintura, escultura, arquitectura, música, literatura, cine, fútbol, olimpismo, tenis, automovilismo, invento, espacio, descubrimiento, historia | `pintura` |
| `anio` | recomendable | año (negativo para a. C.) | `1889`, `-2560` |
| `pais` | no | país actual donde ocurrió o se encuentra | `Francia` |
| `descripcion` | no | 1-2 oraciones con el dato que lo hace interesante | `Gol de Maradona a Inglaterra, Mundial 1986` |
| `imagen_url` | no | URL pública | |

Identidad: el título. Fuentes preferidas: `wikidata`, `wikipedia`.

```csv
titulo,categoria,anio,pais,descripcion
Guernica,pintura,1937,España,Óleo de Picasso sobre el bombardeo de Guernica
Gol del siglo,fútbol,1986,México,Gol de Maradona a Inglaterra en el Mundial 1986
```

## Catálogo `comercios`

| Columna | Obligatoria | Qué es | Ejemplo |
|---|---|---|---|
| `nombre` | sí | nombre comercial (sin S.A./S.R.L.) | `Librería Hernández` |
| `direccion` | sí | calle y número | `Av. Corrientes 1436` |
| `barrio` | recomendable | | `San Nicolás` |
| `ciudad` | sí | | `Buenos Aires` |
| `rubro` | recomendable | una palabra: supermercado, almacén, kiosco, verdulería, carnicería, panadería, dietética, librería, papelería, juguetería, ferretería, farmacia, perfumería, óptica, indumentaria, calzado, veterinaria, pet shop… | `librería` |
| `telefono` | no | cualquier formato | `(011) 4372-7845` |
| `horario` | no | texto tal cual lo publican | `Lun a sáb 9 a 21` |
| `sitio_web` | no | URL del sitio propio o red social | `https://www.libreriahernandez.com.ar` |
| `descripcion` | no | 1 oración | `Librería de fondo, literatura argentina` |
| `imagen_url` | no | foto de la fachada | |

Identidad: **nombre + dirección**. Cada sucursal es un registro distinto.
Escribí la dirección completa y consistente ("Av." o "Avenida", pero siempre
con número).

Fuentes preferidas: `relevamiento` (lo que vos o alguien vio en el local),
`openstreetmap`, `municipal` (datos abiertos de habilitaciones), `web`
(sitios y redes del comercio). No uses agregadores de dudosa calidad como
única fuente.

```csv
nombre,direccion,barrio,ciudad,rubro,telefono,horario,sitio_web
Librería Hernández,Av. Corrientes 1436,San Nicolás,Buenos Aires,librería,(011) 4372-7845,Lun a sáb 10 a 21,https://www.libreriahernandez.com.ar
Verdulería Don Pepe,Av. Boedo 900,Boedo,Buenos Aires,verdulería,,,
```

## Catálogo `ofertas`

**Regla de oro: una oferta sin enlace directo a la página del producto no
sirve y no se publica.** El enlace se abre y se comprueba todos los días: si
está muerto, lleva a la portada o a un buscador, es de otro producto, el
producto está sin stock o el precio de la página no es el anunciado, la oferta
queda fuera del catálogo.

| Columna | Obligatoria | Qué es | Ejemplo |
|---|---|---|---|
| `producto` | sí | marca + producto + variante, como figura en la página | `Leche entera La Serenísima 1 L` |
| `comercio` | sí | nombre del comercio o cadena | `Supermercado La Estrella` |
| `precio` | sí | precio de la oferta, solo el número (con o sin separador de miles) | `1250` o `1.250,00` |
| `enlace` | **sí** | URL de la **página del producto** (no la portada, no una búsqueda, no la home de ofertas) | `https://www.ejemplo.com.ar/p/leche-entera-1l` |
| `precio_anterior` | no | precio de lista, para calcular el descuento | `1480` |
| `marca` | no | | `La Serenísima` |
| `presentacion` | recomendable | tamaño, para el precio por kilo/litro | `1 L`, `500 g`, `pack x 6` |
| `ean` | no | código de barras, si la página lo muestra | `7790742000019` |
| `vigencia_hasta` | no | hasta cuándo dura la oferta (AAAA-MM-DD) | `2026-10-31` |
| `sucursal` | no | si el precio vale solo en una zona | `CABA` |

Antes de entregar una oferta, abrí el enlace y confirmá vos también:

1. Que abre la página de **ese** producto (no la portada, no "resultados de búsqueda").
2. Que el producto tiene botón de compra o dice "en stock" (no "agotado", "sin stock", "avisame cuando haya").
3. Que el precio que ves es el que anotás.

Si alguna falla, **no la entregues**. Mejor diez ofertas que funcionan que cien
que llevan a una página muerta.

```csv
producto,comercio,precio,precio_anterior,enlace,marca,presentacion
Leche entera La Serenísima 1 L,Supermercado La Estrella,1250,1480,https://www.laestrella.com.ar/p/leche-entera-la-serenisima-1l,La Serenísima,1 L
"Aceite de girasol Cocinero 1,5 L",Supermercado La Estrella,3990,4600,https://www.laestrella.com.ar/p/aceite-cocinero-1-5l,Cocinero,"1,5 L"
```

Ojo con las comas: si un valor tiene coma ("1,5 L"), va entre comillas dobles.

## Lo que NO hay que hacer

- No inventar datos para rellenar columnas. Vacío es correcto.
- No mezclar catálogos en un archivo.
- No redactar fichas largas: la `descripcion`/`notas` es una o dos oraciones.
- No poner la fuente dentro de los datos; la fuente es el nombre del archivo.
- No entregar ofertas con enlaces a la portada, a una búsqueda o a una página
  de "ofertas de la semana": el enlace tiene que ser el del producto.
- No cambiar los nombres de las columnas (`nombre_cientifico`, no `especie`;
  `anio`, no `año`; `direccion`, no `domicilio`). El motor acepta algunos
  alias, pero lo estándar evita sorpresas.

## Cómo se verifica lo que entregues

Quien reciba los archivos corre:

```bash
python herramientas/verificar_recoleccion.py animales/ curiosidades/ comercios/ ofertas/
```

En `ofertas` también marca las filas sin precio, sin enlace, con un enlace que
no es http(s) o que apunta a la portada o a un buscador.

y obtiene, por archivo: filas leídas, filas descartadas (sin identidad),
duplicados, columnas desconocidas y valores sospechosos ("N/A", "desconocido").
Si hay descartes o columnas desconocidas, el archivo vuelve a vos con el
detalle.
