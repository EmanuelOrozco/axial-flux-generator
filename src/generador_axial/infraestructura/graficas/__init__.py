"""Gráficas del modelo analítico (matplotlib, sin estado global de pyplot)."""

from generador_axial.infraestructura.graficas.base import Grafica
from generador_axial.infraestructura.graficas.catalogo import (
    GraficaCampoVsDistancia,
    GraficaFlujoYFem,
    GraficaPotenciaVsCarga,
    GraficaPotenciaYParVsRpm,
    GraficaTensionVsRpm,
    graficas_estandar,
)
from generador_axial.infraestructura.graficas.realista import graficas_realistas

__all__ = [
    "Grafica",
    "GraficaCampoVsDistancia",
    "GraficaFlujoYFem",
    "GraficaPotenciaVsCarga",
    "GraficaPotenciaYParVsRpm",
    "GraficaTensionVsRpm",
    "graficas_estandar",
    "graficas_realistas",
]
