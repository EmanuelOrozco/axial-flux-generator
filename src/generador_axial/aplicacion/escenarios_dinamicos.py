"""Casos de uso del modelo dinámico que comparten las gráficas y el reporte del Documento 5."""

from __future__ import annotations

from dataclasses import dataclass

from generador_axial.aplicacion.simulacion_dinamica import InstanteDinamico, SimulacionDinamica
from generador_axial.dominio.diseno import DisenoGenerador

SEGUNDOS_POR_HORA = 3600.0


def regimen_permanente(diseno: DisenoGenerador, par_nm: float, duracion_s: float = 15.0, **entradas) -> InstanteDinamico:
    """Instante tras ``duracion_s`` desde reposo con par constante (por defecto, inversor apagado)."""
    simulacion = SimulacionDinamica(diseno)
    e = simulacion.con_entradas(par_motriz_nm=par_nm, **{"inversor_encendido": False, **entradas})
    return simulacion.avanzar(duracion_s, e)


@dataclass(frozen=True)
class RespuestaImpulso:
    tiempo_s: tuple[float, ...]
    rpm: tuple[float, ...]

    @property
    def rpm_pico(self) -> float:
        return max(self.rpm)

    @property
    def tiempo_parada_s(self) -> float:
        """Primer instante, después del pico, en que el rotor queda detenido."""
        pico = self.rpm.index(self.rpm_pico)
        return next(t for t, r in zip(self.tiempo_s[pico:], self.rpm[pico:]) if r == 0.0)


def impulso_y_frenado(
    diseno: DisenoGenerador, inversor_encendido: bool = True, soc: float | None = None,
    duracion_s: float = 4.0, paso_s: float = 0.05,
) -> RespuestaImpulso:
    """Empujón con la mano desde reposo (par de impulso durante su duración) y giro libre posterior."""
    simulacion = SimulacionDinamica(diseno)
    if soc is not None:
        simulacion.soc = soc
    motriz = simulacion.p.motriz
    impulso = simulacion.con_entradas(par_motriz_nm=motriz.par_impulso_nm, inversor_encendido=inversor_encendido)
    libre = simulacion.con_entradas(par_motriz_nm=0.0, inversor_encendido=inversor_encendido)
    tiempos, rpm = [0.0], [0.0]
    for k in range(int(round(duracion_s / paso_s))):
        m = simulacion.avanzar(paso_s, impulso if (k + 0.5) * paso_s < motriz.duracion_impulso_s else libre)
        tiempos.append(m.tiempo_s)
        rpm.append(m.rpm)
    return RespuestaImpulso(tuple(tiempos), tuple(rpm))


@dataclass(frozen=True)
class CicloDeCarga:
    serie: tuple[InstanteDinamico, ...]
    factor_tiempo: float

    def horas(self, instante: InstanteDinamico) -> float:
        return instante.tiempo_s * self.factor_tiempo / SEGUNDOS_POR_HORA

    def inicio_de_etapa_h(self, etapa: str) -> float:
        return self.horas(next(m for m in self.serie if m.etapa_carga == etapa))


def ciclo_de_carga(
    diseno: DisenoGenerador, soc_inicial: float = 0.8, par_nm: float = 0.3, factor_tiempo: float = 500.0,
    duracion_s: float = 240.0, paso_s: float = 1.0,
) -> CicloDeCarga:
    """Carga completa con el inversor apagado: MPPT → absorción → flotación."""
    simulacion = SimulacionDinamica(diseno)
    simulacion.soc = soc_inicial
    e = simulacion.con_entradas(par_motriz_nm=par_nm, inversor_encendido=False, factor_tiempo=factor_tiempo)
    return CicloDeCarga(tuple(simulacion.simular(e, duracion_s, paso_s)), factor_tiempo)
