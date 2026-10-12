"""Ubicaciones por defecto de los artefactos dentro del repositorio."""

from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
DIRECTORIO_GRAFICAS = RAIZ_PROYECTO / "simulacion" / "graficas"
DIRECTORIO_STL = RAIZ_PROYECTO / "cad_3d" / "stl"
DIRECTORIO_LATEX_GENERADO = RAIZ_PROYECTO / "docs" / "latex" / "generado"
