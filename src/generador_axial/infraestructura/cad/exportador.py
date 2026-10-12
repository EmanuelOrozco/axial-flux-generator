"""Escritura de mallas en formato STL binario."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from generador_axial.aplicacion.piezas import Pieza
from generador_axial.infraestructura.cad.constructor import construir_malla
from generador_axial.infraestructura.cad.malla import Malla

CABECERA_STL = b"Generador axial NdFeB - Teoria Electromagnetica (Sadiku) - unidades: mm"

_REGISTRO_STL = np.dtype(
    [("normal", "<f4", (3,)), ("vertices", "<f4", (3, 3)), ("atributo", "<u2")]
)


@dataclass(frozen=True)
class ResultadoExportacion:
    pieza: Pieza
    ruta: Path
    facetas: int
    volumen_mm3: float


def escribir_stl_binario(malla: Malla, ruta: Path) -> None:
    registros = np.zeros(len(malla), dtype=_REGISTRO_STL)
    registros["normal"] = malla.normales()
    registros["vertices"] = malla.triangulos
    with ruta.open("wb") as archivo:
        archivo.write(CABECERA_STL.ljust(80, b"\0"))
        archivo.write(np.uint32(len(malla)).tobytes())
        archivo.write(registros.tobytes())


class ExportadorStl:
    def __init__(self, directorio: Path, longitud_arista_mm: float = 1.0) -> None:
        self.directorio = directorio
        self.longitud_arista_mm = longitud_arista_mm

    def exportar(self, piezas: tuple[Pieza, ...]) -> list[ResultadoExportacion]:
        self.directorio.mkdir(parents=True, exist_ok=True)
        resultados = []
        for pieza in piezas:
            malla = construir_malla(pieza.geometria, self.longitud_arista_mm)
            ruta = self.directorio / pieza.nombre_archivo
            escribir_stl_binario(malla, ruta)
            resultados.append(ResultadoExportacion(pieza, ruta, len(malla), malla.volumen_con_signo()))
        return resultados
