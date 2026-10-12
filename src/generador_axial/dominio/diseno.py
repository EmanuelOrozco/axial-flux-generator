"""Raíz de agregado: el diseño completo y sus invariantes cruzadas."""

from __future__ import annotations

from dataclasses import dataclass

from generador_axial.dominio.componentes import (
    Bateria,
    ControladorCarga,
    Estator,
    IndicadorLed,
    InversorAc,
    Rectificador,
    Rotor,
)
from generador_axial.dominio.errores import ErrorDeDiseno, exigir_positivo
from generador_axial.dominio.mecanica import GeometriaMecanica


@dataclass(frozen=True)
class DisenoGenerador:
    """Generador monofásico de flujo axial sin núcleo (coreless) de un solo rotor."""

    rotor: Rotor
    estator: Estator
    entrehierro_m: float
    factor_acoplamiento: float
    rectificador: Rectificador
    indicador: IndicadorLed
    mecanica: GeometriaMecanica
    bateria: Bateria | None = None
    controlador_carga: ControladorCarga | None = None
    inversor: InversorAc | None = None

    def __post_init__(self) -> None:
        exigir_positivo("El entrehierro", self.entrehierro_m)
        if not 0 < self.factor_acoplamiento <= 1:
            raise ErrorDeDiseno("El factor de acoplamiento k debe cumplir 0 < k <= 1.")
        if self.estator.numero_bobinas != self.rotor.numero_polos:
            raise ErrorDeDiseno(
                "El modelo monofásico exige una bobina por polo para que todas las fem estén en fase."
            )
        if self.estator.radio_montaje_m != self.rotor.radio_montaje_m:
            raise ErrorDeDiseno("Imanes y bobinas deben montarse sobre el mismo radio medio.")
        self._validar_ajuste_mecanico()

    def _validar_ajuste_mecanico(self) -> None:
        m = self.mecanica
        radio_montaje = self.rotor.radio_montaje_m

        borde_imanes = radio_montaje + m.con_holgura(self.rotor.iman.diametro_m) / 2
        if borde_imanes + m.pared_minima_m > m.diametro_disco_rotor_m / 2:
            raise ErrorDeDiseno("Los alojamientos de los imanes sobresalen del disco rotor.")
        if self.rotor.iman.espesor_m < m.profundidad_alojamiento_iman_m:
            raise ErrorDeDiseno("El imán quedaría hundido en su alojamiento y aumentaría el entrehierro.")

        radio_bobina = m.con_holgura(self.estator.bobina.diametro_exterior_m) / 2
        if radio_montaje + radio_bobina + m.pared_minima_m > m.diametro_disco_estator_m / 2:
            raise ErrorDeDiseno("Los alojamientos de las bobinas sobresalen del disco estator.")
        if radio_montaje - radio_bobina - m.pared_minima_m < m.diametro_alojamiento_rodamiento_m / 2:
            raise ErrorDeDiseno("Las bobinas invaden el alojamiento central del rodamiento.")
