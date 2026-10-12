"""Interfaz de línea de comandos (patrón Command: un objeto por subcomando).

Uso:
    generador-axial simular   [--salida DIR]
    generador-axial cad       [--salida DIR] [--arista MM]
    generador-axial reporte   [--salida DIR]
    generador-axial todo
"""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from pathlib import Path

from generador_axial import rutas
from generador_axial.aplicacion import SimuladorGenerador, catalogo_de_piezas, generar_reporte
from generador_axial.configuracion import ESCENARIO_POR_DEFECTO, diseno_por_defecto
from generador_axial.presentacion import consola

LINEA = "=" * 65


class Comando(ABC):
    nombre: str
    ayuda: str

    def configurar(self, parser: argparse.ArgumentParser) -> None:
        """Agrega argumentos propios del subcomando."""

    @abstractmethod
    def ejecutar(self, argumentos: argparse.Namespace, simulador: SimuladorGenerador) -> None: ...


class ComandoSimular(Comando):
    nombre = "simular"
    ayuda = "Imprime el resumen del diseño y exporta las gráficas del modelo analítico y del realista."

    def configurar(self, parser):
        parser.add_argument("--salida", type=Path, default=rutas.DIRECTORIO_GRAFICAS)

    def ejecutar(self, argumentos, simulador):
        from generador_axial.infraestructura.graficas import graficas_estandar, graficas_realistas

        print(consola.resumen_del_diseno(simulador))
        graficas = [*graficas_estandar(simulador, ESCENARIO_POR_DEFECTO), *graficas_realistas(simulador, ESCENARIO_POR_DEFECTO)]
        for grafica in graficas:
            print(f" -> Gráfica guardada: {grafica.exportar(argumentos.salida)}")


class ComandoCad(Comando):
    nombre = "cad"
    ayuda = "Genera las piezas imprimibles en formato STL (milímetros)."

    def configurar(self, parser):
        parser.add_argument("--salida", type=Path, default=rutas.DIRECTORIO_STL)
        parser.add_argument("--arista", type=float, default=1.0, help="Longitud máxima de arista en los círculos [mm].")

    def ejecutar(self, argumentos, simulador):
        from generador_axial.infraestructura.cad import ExportadorStl

        exportador = ExportadorStl(argumentos.salida, argumentos.arista)
        for resultado in exportador.exportar(catalogo_de_piezas(simulador.diseno)):
            print(
                f" -> {resultado.ruta.name}: {resultado.pieza.descripcion} "
                f"({resultado.facetas} facetas, {resultado.volumen_mm3 / 1e3:.1f} cm³)"
            )


class ComandoReporte(Comando):
    nombre = "reporte"
    ayuda = "Exporta las magnitudes calculadas como macros LaTeX para los documentos PDF."

    def configurar(self, parser):
        parser.add_argument("--salida", type=Path, default=rutas.DIRECTORIO_LATEX_GENERADO)

    def ejecutar(self, argumentos, simulador):
        from generador_axial.infraestructura.latex import ExportadorLatex

        reporte = generar_reporte(simulador, ESCENARIO_POR_DEFECTO)
        for ruta in ExportadorLatex(argumentos.salida).exportar(reporte):
            print(f" -> Archivo LaTeX generado: {ruta}")


class ComandoTodo(Comando):
    nombre = "todo"
    ayuda = "Ejecuta simular, cad y reporte con sus salidas por defecto."

    def __init__(self, comandos: list[Comando]) -> None:
        self.comandos = comandos

    def ejecutar(self, argumentos, simulador):
        for comando in self.comandos:
            parser = argparse.ArgumentParser()
            comando.configurar(parser)
            print(f"\n{LINEA}\n{comando.ayuda}\n{LINEA}")
            comando.ejecutar(parser.parse_args([]), simulador)


def construir_comandos() -> list[Comando]:
    basicos: list[Comando] = [ComandoSimular(), ComandoCad(), ComandoReporte()]
    return [*basicos, ComandoTodo(basicos)]


def main(argv: list[str] | None = None) -> None:
    comandos = construir_comandos()
    parser = argparse.ArgumentParser(prog="generador-axial", description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="comando", required=True)
    por_nombre = {}
    for comando in comandos:
        comando.configurar(subparsers.add_parser(comando.nombre, help=comando.ayuda))
        por_nombre[comando.nombre] = comando

    argumentos = parser.parse_args(argv)
    simulador = SimuladorGenerador(diseno_por_defecto())
    por_nombre[argumentos.comando].ejecutar(argumentos, simulador)


if __name__ == "__main__":
    main()
