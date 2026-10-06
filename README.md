# Catálogos: motor compartido de análisis en paralelo

Un solo motor para recolectar, analizar con Claude **en paralelo** y ordenar
dos proyectos de catálogo:

- **visual**: `animales` y `curiosidades` (arte, deporte, ciencia, historia);
- **comercios**: supermercados, librerías, almacenes, farmacias...

El diseño (qué se comparte, qué no y qué se tomó del catálogo de comercios)
está en [docs/ARQUITECTURA.md](docs/ARQUITECTURA.md). Cómo aplicarlo a los
catálogos reales, con búsqueda web y las dos vías de ejecución (cuenta o clave
de API), en [docs/LOGISTICA_PARALELA.md](docs/LOGISTICA_PARALELA.md).

## Instalación

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Probar sin costo (modo simulado)

```bash
python -m catalogo ingerir animales ejemplos/animales/wikipedia.csv ejemplos/animales/gbif.jsonl
python -m catalogo ingerir curiosidades ejemplos/curiosidades/wikipedia.csv
python -m catalogo ingerir comercios ejemplos/comercios/web.csv ejemplos/comercios/relevamiento.csv

# los tres dominios a la vez, 16 trabajadores, 0,2 s simulados por item
python -m catalogo analizar animales curiosidades comercios --simulado --latencia-simulada 0.2 --concurrencia 16

python -m catalogo catalogar animales curiosidades comercios --salida salida
python -m catalogo estado
```

Resultado en `salida/<dominio>/catalogo.md` (legible), `catalogo.json` (árbol
con facetas y cola de revisión) y `fichas.jsonl` (una ficha por línea).

## Con Claude

```bash
export ANTHROPIC_API_KEY=...

# empezar con una muestra chica para revisar la calidad
python -m catalogo analizar animales --limite 5 --modo tiempo-real

# volumen chico/mediano: en paralelo y en tiempo real
python -m catalogo analizar animales curiosidades comercios --concurrencia 16 --por-minuto 300

# volumen grande: Message Batches (50 % más barato, resultados en < 24 h)
python -m catalogo analizar animales --modo lotes --no-esperar
python -m catalogo recoger animales          # más tarde, o en otra máquina con la misma base

# lo que falló o fue rechazado, otra vez en tiempo real (con fallback de modelo)
python -m catalogo estado animales --errores
python -m catalogo analizar animales --reintentar-errores --modo tiempo-real
```

Opciones útiles: `--modelo` (por defecto `claude-opus-5-5`), `--esfuerzo`
(`low`…`max`, por defecto `medium`), `--modo auto` con `--umbral-lotes`,
`--db` para usar otra base de estado.

## Estructura

```
catalogo/
  core/            motor compartido (no sabe de animales ni de comercios)
    paralelo.py      trabajadores asyncio, límite de ritmo, reintentos, pausa ante 429
    almacen.py       estado en SQLite: reanudar, no pagar dos veces, TTL, lotes, fuentes
    analizador.py    simulado · Claude en tiempo real · Message Batches
    taxonomia.py     árbol de categorías (vocabulario controlado + orden)
    catalogo.py      identidad final, orden, árbol, facetas, cola de revisión, exportación
    pipeline.py      ingerir → analizar → catalogar
    texto.py         normalización de texto y medidas
  dominios/        una clase por catálogo: animales, curiosidades, comercios
ejemplos/          datos de muestra, una carpeta por dominio y un archivo por fuente
tests/             pytest, sin red (cliente de Claude falso)
```

## Tests

```bash
pytest
```
