"""Generación de mallas triangulares y exportación a STL."""

from generador_axial.infraestructura.cad.constructor import construir_malla
from generador_axial.infraestructura.cad.exportador import ExportadorStl, ResultadoExportacion
from generador_axial.infraestructura.cad.malla import Malla

__all__ = ["ExportadorStl", "Malla", "ResultadoExportacion", "construir_malla"]
