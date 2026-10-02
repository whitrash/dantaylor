"""Línea de comandos.

python -m catalogo ingerir animales ejemplos/animales.csv --fuente wikipedia
python -m catalogo analizar animales curiosidades comercios --concurrencia 16
python -m catalogo catalogar animales --salida salida
python -m catalogo estado
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from .core import pipeline
from .core.almacen import Almacen
from .core.analizador import MODELO_POR_DEFECTO, AnalizadorClaude, AnalizadorSimulado
from .core.paralelo import ErrorFatal
from .dominios import DOMINIOS, obtener


def _analizador(args: argparse.Namespace):
    if args.simulado:
        return AnalizadorSimulado(latencia=args.latencia_simulada)
    return AnalizadorClaude(modelo=args.modelo, esfuerzo=args.esfuerzo, max_tokens=args.max_tokens)


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

    def opciones_analisis(p: argparse.ArgumentParser) -> None:
        p.add_argument("--simulado", action="store_true", help="sin red ni costo: prueba la logística")
        p.add_argument("--latencia-simulada", type=float, default=0.0, help="segundos por item en modo simulado")
        p.add_argument("--modelo", default=MODELO_POR_DEFECTO)
        p.add_argument("--esfuerzo", default="medium", choices=["low", "medium", "high", "xhigh", "max"])
        p.add_argument("--max-tokens", type=int, default=16000)

    p = sub.add_parser("analizar", help="analizar en paralelo los items pendientes")
    p.add_argument("dominios", nargs="+", choices=DOMINIOS)
    p.add_argument("--modo", default="auto", choices=pipeline.MODOS)
    p.add_argument("--concurrencia", type=int, default=8, help="pedidos simultáneos (modo tiempo real)")
    p.add_argument("--por-minuto", type=float, help="tope de pedidos por minuto, compartido entre dominios")
    p.add_argument("--limite", type=int, help="máximo de items por dominio en esta corrida")
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

    p = sub.add_parser("estado", help="cuántos items hay en cada estado")
    # Sin `choices`: con nargs="*" argparse falla en Python 3.11; se valida con `obtener`.
    p.add_argument("dominios", nargs="*", help=f"default: todos ({', '.join(DOMINIOS)})")
    p.add_argument("--errores", action="store_true", help="listar los errores")

    args = parser.parse_args(argv)
    almacen = Almacen(args.db)
    try:
        if args.comando == "ingerir":
            dominio = obtener(args.dominio)
            for archivo in args.archivos:
                cuenta = pipeline.ingerir(almacen, dominio, pipeline.leer_filas(archivo), args.fuente or archivo.stem)
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
                )
            )
            _imprimir(resultado)
        elif args.comando == "recoger":
            if args.simulado:
                raise SystemExit("`recoger` trabaja con lotes de Claude; no aplica a --simulado")
            _imprimir(
                _correr(
                    pipeline.recoger_lotes(
                        almacen, [obtener(d) for d in args.dominios], _analizador(args), args.intervalo_lotes
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
                    "lotes_abiertos": almacen.lotes_abiertos(nombre),
                }
                if args.errores:
                    datos["detalle_errores"] = dict(almacen.errores(nombre))
                _imprimir(datos)
    finally:
        almacen.cerrar()


if __name__ == "__main__":
    main()
