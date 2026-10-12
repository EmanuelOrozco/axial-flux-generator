"""Cotas mecánicas de las piezas fabricables (discos, carrete). Unidades SI."""

from __future__ import annotations

from dataclasses import dataclass, fields

from generador_axial.dominio.errores import ErrorDeDiseno, exigir_positivo


@dataclass(frozen=True)
class GeometriaMecanica:
    diametro_disco_rotor_m: float = 0.110
    espesor_disco_rotor_m: float = 0.006
    profundidad_alojamiento_iman_m: float = 0.004
    diametro_eje_m: float = 0.008
    diametro_disco_estator_m: float = 0.120
    espesor_disco_estator_m: float = 0.005
    profundidad_alojamiento_bobina_m: float = 0.003
    diametro_alojamiento_rodamiento_m: float = 0.022
    espesor_ala_carrete_m: float = 0.002
    sobremedida_ala_carrete_m: float = 0.002
    holgura_ajuste_m: float = 0.0002
    pared_minima_m: float = 0.0015

    def __post_init__(self) -> None:
        for campo in fields(self):
            exigir_positivo(campo.name.replace("_", " "), getattr(self, campo.name))
        if self.profundidad_alojamiento_iman_m >= self.espesor_disco_rotor_m:
            raise ErrorDeDiseno("El alojamiento del imán atravesaría el disco rotor.")
        if self.profundidad_alojamiento_bobina_m >= self.espesor_disco_estator_m:
            raise ErrorDeDiseno("El alojamiento de la bobina atravesaría el disco estator.")

    def con_holgura(self, diametro_m: float) -> float:
        """Diámetro de un agujero que debe alojar una pieza de ``diametro_m`` con ajuste deslizante."""
        return diametro_m + 2 * self.holgura_ajuste_m
