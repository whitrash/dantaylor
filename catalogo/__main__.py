"""Línea de comandos.

python -m catalogo ingerir animales ejemplos/animales/wikipedia.csv --fuente wikipedia
python -m catalogo importar animales fichas_viejas.jsonl        # lo ya analizado, sin pagar de nuevo
python -m catalogo analizar animales comercios --claude-code     # con Claude Code local (tu cuenta)
python -m catalogo analizar animales --modo lotes --no-esperar   # con clave de API, a mitad de precio
python -m catalogo panel --abrir                                 # panel visual en el navegador
python -m catalogo catalogar animales --salida salida
python -m catalogo estado
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .core import panel, pipeline
from .core.almacen import Almacen
from .core.analizador import MODELO_POR_DEFECTO, AnalizadorClaude, AnalizadorClaudeCode, AnalizadorSimulado
from .core.paralelo import ErrorFatal
from .dominios import DOMINIOS, obtener

ESFUERZOS = ["low", "medium", "high", "xhigh", "max"]


def _analizador(args: argparse.Namespace):
    if args.simulado:
        return AnalizadorSimulado(latencia=args.latencia_simulada)
    if args.claude_code:
        if not AnalizadorClaudeCode.disponible(args.ejecutable_claude):
            raise SystemExit(
                f"No encuentro `{args.ejecutable_claude}` en el PATH. Instalá Claude Code o indicá la ruta con --ejecutable-claude."
            )
        return AnalizadorClaudeCode(
            modelo=args.modelo,
            esfuerzo=args.esfuerzo,
            max_turnos=args.max_turnos,
            max_costo_item=args.max_costo_item,
            timeout=args.timeout_item,
            ejecutable=args.ejecutable_claude,
            carpeta=args.carpeta_claude,
        )
    return AnalizadorClaude(
        modelo=args.modelo or MODELO_POR_DEFECTO, esfuerzo=args.esfuerzo, max_tokens=args.max_tokens
    )


def _imprimir(datos: object) -> None:
    print(json.dumps(datos, ensure_ascii=False, indent=2))


def _correr(corrutina):
    try:
        return asyncio.run(corrutina)
    except ErrorFatal as error:
        raise SystemExit(
            f"Corrida detenida: {error}\n"
            "Lo terminado quedó guardado; lo que estaba en curso vuelve a la cola en la próxima corrida."
        ) from None
    except ValueError as error:
        raise SystemExit(str(error)) from None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="catalogo", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--db", default="catalogo.db", help="archivo SQLite con el estado (default: catalogo.db)")
    sub = parser.add_subparsers(dest="comando", required=True)

    p = sub.add_parser("ingerir", help="cargar filas (CSV/JSONL/JSON) de una fuente")
    p.add_argument("dominio", choices=DOMINIOS)
    p.add_argument("archivos", nargs="+", type=Path)
    p.add_argument("--fuente", help="nombre de la fuente (default: nombre del archivo)")

    p = sub.add_parser("importar", help="cargar fichas ya analizadas como listas (no se vuelven a pagar)")
    p.add_argument("dominio", choices=DOMINIOS)
    p.add_argument("archivos", nargs="+", type=Path)
    p.add_argument("--fuente", help="nombre de la fuente (default: nombre del archivo)")
    p.add_argument("--etiqueta-modelo", default="importado", help="qué figura como modelo en esas fichas")

    def opciones_analisis(p: argparse.ArgumentParser) -> None:
        g = p.add_argument_group("con qué analizar")
        g.add_argument("--simulado", action="store_true", help="sin red ni costo: prueba la logística")
        g.add_argument("--latencia-simulada", type=float, default=0.0, help="segundos por item en modo simulado")
        g.add_argument(
            "--claude-code",
            action="store_true",
            help="usar `claude -p` (Claude Code local, tu cuenta) en vez de la API",
        )
        g.add_argument("--ejecutable-claude", default="claude", help="ruta al ejecutable de Claude Code")
        g.add_argument("--carpeta-claude", help="carpeta vacía desde donde correr `claude -p` (default: una temporal)")
        g.add_argument("--max-turnos", type=int, default=12, help="turnos máximos por item en --claude-code")
        g.add_argument("--max-costo-item", type=float, default=0.5, help="tope en USD por item en --claude-code")
        g.add_argument("--timeout-item", type=float, default=600.0, help="segundos máximos por item en --claude-code")
        g.add_argument(
            "--modelo", help=f"id del modelo (API: default {MODELO_POR_DEFECTO}; Claude Code: el de tu sesión)"
        )
        g.add_argument("--esfuerzo", default="medium", choices=ESFUERZOS)
        g.add_argument("--max-tokens", type=int, default=16000, help="tope de tokens de salida por item (API)")
        g.add_argument("--sin-web", action="store_true", help="no buscar en internet en ningún dominio")
        g.add_argument("--estado-json", type=Path, help="escribir el resumen del panel a este archivo cada segundo")

    p = sub.add_parser("analizar", help="analizar en paralelo los items pendientes")
    p.add_argument("dominios", nargs="+", choices=DOMINIOS)
    p.add_argument("--modo", default="auto", choices=pipeline.MODOS)
    p.add_argument("--concurrencia", type=int, default=8, help="pedidos simultáneos (modo tiempo real)")
    p.add_argument("--por-minuto", type=float, help="tope de pedidos por minuto, compartido entre dominios")
    p.add_argument("--limite", type=int, help="máximo de items por dominio en esta corrida")
    p.add_argument("--max-costo", type=float, help="tope de gasto en USD para esta corrida")
    p.add_argument("--reintentar-errores", action="store_true")
    p.add_argument("--umbral-lotes", type=int, default=1000, help="en modo auto, desde cuántos items usar lotes")
    p.add_argument("--tam-lote", type=int, default=10_000)
    p.add_argument("--intervalo-lotes", type=float, default=60.0, help="segundos entre consultas de estado de un lote")
    p.add_argument("--no-esperar", action="store_true", help="en modo lotes: enviar y salir (después usar `recoger`)")
    opciones_analisis(p)

    p = sub.add_parser("recoger", help="esperar y guardar lotes enviados antes")
    p.add_argument("dominios", nargs="+", choices=DOMINIOS)
    p.add_argument("--intervalo-lotes", type=float, default=60.0)
    opciones_analisis(p)

    p = sub.add_parser("catalogar", help="armar y exportar el catálogo ordenado")
    p.add_argument("dominios", nargs="+", choices=DOMINIOS)
    p.add_argument("--salida", type=Path, default=Path("salida"))

    p = sub.add_parser("panel", help="panel visual del motor en el navegador")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--puerto", type=int, default=8765)
    p.add_argument("--abrir", action="store_true", help="abrir el navegador")

    p = sub.add_parser("estado", help="cuántos items hay en cada estado, con costos")
    # Sin `choices`: con nargs="*" argparse falla en Python 3.11; se valida con `obtener`.
    p.add_argument("dominios", nargs="*", help=f"default: todos ({', '.join(DOMINIOS)})")
    p.add_argument("--errores", action="store_true", help="listar los errores")

    args = parser.parse_args(argv)
    if args.comando == "panel":
        Almacen(args.db).cerrar()  # crea la base si no existe; el panel la abre solo para leer
        panel.servir(args.db, args.host, args.puerto, abrir=args.abrir)
        return

    almacen = Almacen(args.db)
    try:
        if args.comando == "ingerir":
            dominio = obtener(args.dominio)
            for archivo in args.archivos:
                cuenta = pipeline.ingerir(almacen, dominio, pipeline.leer_filas(archivo), args.fuente or archivo.stem)
                _imprimir({"archivo": str(archivo), **cuenta})
        elif args.comando == "importar":
            dominio = obtener(args.dominio)
            for archivo in args.archivos:
                cuenta = pipeline.importar(
                    almacen, dominio, pipeline.leer_filas(archivo), args.fuente or archivo.stem, args.etiqueta_modelo
                )
                _imprimir({"archivo": str(archivo), **cuenta})
        elif args.comando == "analizar":
            resultado = _correr(
                pipeline.analizar(
                    almacen,
                    [obtener(d) for d in args.dominios],
                    _analizador(args),
                    modo=args.modo,
                    concurrencia=args.concurrencia,
                    por_minuto=args.por_minuto,
                    limite=args.limite,
                    reintentar_errores=args.reintentar_errores,
                    umbral_lotes=args.umbral_lotes,
                    tam_lote=args.tam_lote,
                    intervalo_lotes=args.intervalo_lotes,
                    esperar_lotes=not args.no_esperar,
                    web=not args.sin_web,
                    max_costo=args.max_costo,
                    estado_json=args.estado_json,
                )
            )
            _imprimir(resultado)
        elif args.comando == "recoger":
            if args.simulado or args.claude_code:
                raise SystemExit(
                    "`recoger` trabaja con lotes de la API de Claude; no aplica a --simulado ni --claude-code"
                )
            _imprimir(
                _correr(
                    pipeline.recoger_lotes(
                        almacen,
                        [obtener(d) for d in args.dominios],
                        _analizador(args),
                        args.intervalo_lotes,
                        web=not args.sin_web,
                        estado_json=args.estado_json,
                    )
                )
            )
        elif args.comando == "catalogar":
            for nombre in args.dominios:
                armado, rutas = pipeline.catalogar(almacen, obtener(nombre), args.salida)
                _imprimir(
                    {
                        "dominio": nombre,
                        "fichas": armado["total"],
                        "para_revisar": len(armado["revisar"]),
                        "archivos": [str(r) for r in rutas],
                    }
                )
        elif args.comando == "estado":
            for nombre in args.dominios or list(DOMINIOS):
                obtener(nombre)
                datos: dict = {
                    "dominio": nombre,
                    **almacen.estado(nombre),
                    **almacen.metricas(nombre),
                    "lotes_abiertos": almacen.lotes_abiertos(nombre),
                }
                if args.errores:
                    datos["detalle_errores"] = dict(almacen.errores(nombre))
                _imprimir(datos)
    finally:
        almacen.cerrar()


if __name__ == "__main__":
    main()
