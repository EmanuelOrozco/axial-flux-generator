"""Capa de dominio: entidades del generador y leyes físicas (Sadiku, Cap. 7 a 9)."""

from generador_axial.dominio.componentes import (
    AlambreMagneto,
    Bateria,
    Bobina,
    ControladorCarga,
    Estator,
    ImanPermanente,
    IndicadorLed,
    InversorAc,
    Rectificador,
    Rotor,
)
from generador_axial.dominio.diseno import DisenoGenerador
from generador_axial.dominio.errores import ErrorDeDiseno
from generador_axial.dominio.mecanica import GeometriaMecanica
from generador_axial.dominio.realista import ParametrosRealistas

__all__ = [
    "AlambreMagneto",
    "Bateria",
    "Bobina",
    "ControladorCarga",
    "DisenoGenerador",
    "ErrorDeDiseno",
    "Estator",
    "GeometriaMecanica",
    "ImanPermanente",
    "IndicadorLed",
    "InversorAc",
    "ParametrosRealistas",
    "Rectificador",
    "Rotor",
]
