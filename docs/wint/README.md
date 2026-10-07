# WINT · Informe técnico y hoja de ruta

**[WINT_informe.pdf](WINT_informe.pdf)** (67 páginas, 7 de octubre de 2026): qué es WINT, cómo construir
Sol y Luna sobre el modelo real de energía de Windows (más allá de Suspender, Apagar y Reiniciar), la
arquitectura de un "bot que no piensa", el Detector y la detección de ofertas falsas con pesos de hoy,
WINT en Android, visualización estilo Netflix, el mapa del software que ya existe y una hoja de ruta por etapas.

Para leer rápido: capítulo 1 (resumen), 5 (Sol y Luna en Windows) y 10 (hoja de ruta). El capítulo 11
tiene las preguntas que faltan responder.

## Qué hay en esta carpeta

| Ruta | Contenido |
|---|---|
| `WINT_informe.pdf` | El informe. |
| `investigacion/` | Notas de los 11 frentes de investigación, la verificación independiente de cada uno (`*.verificado.md`), la auditoría de completitud (`AUDITORIA.md`) y la segunda ronda (`complementos/`). Sirven para auditar cualquier dato del informe. |
| `fuente/` | El generador del PDF: capítulos en HTML con macros (`capitulos/`), diagramas en SVG (`diagramas.py`), estilos (`estilo.css`), ensamblador (`ensamblar.py`), y los documentos de criterio usados para redactar (`DECISIONES.md`, `GUIA_REDACCION.md`). |

## Regenerar el PDF

```bash
cd docs/wint/fuente
./bajar_fuentes.sh                 # tipografías OFL en ../fonts/static (requiere fonttools)
pip install pypdf
WINT_CHROME=/ruta/a/chrome python3 ensamblar.py      # salida/WINT_informe.pdf
python3 ensamblar.py --solo cap05  # vista previa de un capítulo
```

Límite conocido: durante la investigación varios sitios oficiales estuvieron bloqueados; el informe marca
lo no verificado y explica en el capítulo 2 qué tan firme es cada área.
