"""Capa de aplicación: casos de uso sobre el diseño del generador."""

from generador_axial.aplicacion.piezas import Pieza, catalogo_de_piezas
from generador_axial.aplicacion.reporte import Magnitud, ReporteDeCalculo, generar_reporte
from generador_axial.aplicacion.simulador import (
    BalanceMicrored,
    EvolucionBateria,
    FormaDeOnda,
    OperacionConCarga,
    PuntoDeOperacion,
    SalidaInversor,
    SimuladorGenerador,
)
from generador_axial.aplicacion.simulacion_dinamica import EntradasDinamicas, InstanteDinamico, SimulacionDinamica

__all__ = [
    "BalanceMicrored",
    "EntradasDinamicas",
    "EvolucionBateria",
    "FormaDeOnda",
    "InstanteDinamico",
    "Magnitud",
    "OperacionConCarga",
    "Pieza",
    "PuntoDeOperacion",
    "ReporteDeCalculo",
    "SalidaInversor",
    "SimulacionDinamica",
    "SimuladorGenerador",
    "catalogo_de_piezas",
    "generar_reporte",
]
