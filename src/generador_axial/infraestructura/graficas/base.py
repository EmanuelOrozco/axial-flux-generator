"""Clase base de las gráficas (patrón Template Method)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from matplotlib.figure import Figure

from generador_axial.aplicacion import SimuladorGenerador
from generador_axial.configuracion import EscenarioDeAnalisis

ESTILO_REJILLA = {"linestyle": ":", "alpha": 0.6}


class Grafica(ABC):
    """Define el flujo crear figura -> dibujar -> guardar; cada subclase solo implementa ``dibujar``."""

    nombre_archivo: str
    tamano_pulgadas: tuple[float, float] = (8, 5)
    resolucion_dpi: int = 150

    def __init__(self, simulador: SimuladorGenerador, escenario: EscenarioDeAnalisis) -> None:
        self.simulador = simulador
        self.escenario = escenario

    @property
    def diseno(self):
        return self.simulador.diseno

    def exportar(self, directorio: Path) -> Path:
        directorio.mkdir(parents=True, exist_ok=True)
        figura = Figure(figsize=self.tamano_pulgadas, dpi=self.resolucion_dpi, layout="tight")
        self.dibujar(figura)
        ruta = directorio / self.nombre_archivo
        figura.savefig(ruta)
        return ruta

    @abstractmethod
    def dibujar(self, figura: Figure) -> None: ...
