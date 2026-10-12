"""Casos de uso del modelo analítico: punto de operación, carga, batería e inversor."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property

import numpy as np
from numpy.typing import ArrayLike, NDArray

from generador_axial.dominio import (
    Bateria,
    ControladorCarga,
    DisenoGenerador,
    ErrorDeDiseno,
    InversorAc,
)
from generador_axial.dominio import fisica
from generador_axial.dominio.errores import exigir_positivo
from generador_axial.dominio.fisica import Vector


@dataclass(frozen=True)
class PuntoDeOperacion:
    """Magnitudes en vacío (sin carga) a una velocidad dada. Admite escalares o arreglos."""

    rpm: Vector
    velocidad_angular_mecanica: Vector
    frecuencia_electrica_hz: Vector
    velocidad_angular_electrica: Vector
    tension_pico_v: Vector
    tension_rms_v: Vector
    tension_dc_v: Vector


@dataclass(frozen=True)
class FormaDeOnda:
    tiempo_s: Vector
    flujo_por_espira_wb: Vector
    fem_v: Vector


@dataclass(frozen=True)
class OperacionConCarga:
    """Régimen senoidal con carga resistiva R_L conectada a los bornes AC."""

    resistencia_carga_ohm: Vector
    corriente_rms_a: Vector
    tension_carga_rms_v: Vector
    potencia_carga_w: Vector
    potencia_perdidas_cobre_w: Vector
    potencia_mecanica_w: Vector
    par_resistente_nm: Vector
    eficiencia: Vector


@dataclass(frozen=True)
class EvolucionBateria:
    """Integración temporal del SoC: el generador carga y el inversor descarga."""

    tiempo_h: Vector
    soc: Vector
    tension_bateria_v: Vector
    corriente_carga_a: Vector
    corriente_descarga_a: Vector
    inversor_activo: NDArray[np.bool_]

    @property
    def corriente_neta_a(self) -> Vector:
        return self.corriente_carga_a - self.corriente_descarga_a


@dataclass(frozen=True)
class SalidaInversor:
    """Tensión senoidal de salida del inversor y corrientes asociadas."""

    tiempo_s: Vector
    tension_ac_v: Vector
    tension_rms_v: float
    frecuencia_hz: float
    potencia_carga_w: float
    corriente_rms_a: float
    corriente_bateria_a: float


@dataclass(frozen=True)
class BalanceMicrored:
    """Flujo de potencia en régimen permanente: eje -> generador -> controlador -> batería -> inversor."""

    rpm: float
    soc: float
    tension_bateria_v: float
    potencia_mecanica_w: float
    potencia_generador_w: float
    potencia_perdidas_cobre_w: float
    par_resistente_nm: float
    potencia_hacia_bateria_w: float
    inversor_activo: bool
    potencia_carga_ac_w: float
    potencia_entrada_inversor_w: float
    potencia_neta_bateria_w: float
    autonomia_h: float



class SimuladorGenerador:
    """Fachada sobre las leyes físicas aplicadas a un diseño concreto."""

    def __init__(self, diseno: DisenoGenerador) -> None:
        self.diseno = diseno

    @property
    def iman(self):
        return self.diseno.rotor.iman

    @property
    def resistencia_interna_ohm(self) -> float:
        return self.diseno.estator.resistencia_interna_ohm

    def campo_axial(self, z_m: ArrayLike) -> Vector:
        return fisica.campo_axial(self.iman, z_m)

    @cached_property
    def campo_en_cara_iman_t(self) -> float:
        return float(self.campo_axial(0.0))

    @cached_property
    def campo_en_cara_bobina_t(self) -> float:
        return float(self.campo_axial(self.diseno.entrehierro_m))

    @cached_property
    def campo_medio_bobina_t(self) -> float:
        """B_z promediado sobre el espesor de la bobina, [g, g + h]."""
        altura = self.diseno.estator.bobina.altura_m
        return float(fisica.campo_medio_en_tramo(self.iman, self.diseno.entrehierro_m, altura))

    @cached_property
    def flujo_maximo_por_espira_wb(self) -> float:
        """Phi_max = k * B_medio * A_iman."""
        return self.diseno.factor_acoplamiento * self.campo_medio_bobina_t * self.iman.area_cara_m2

    def punto_de_operacion(self, rpm: ArrayLike) -> PuntoDeOperacion:
        rpm_arr = np.asarray(rpm, dtype=float)
        if np.any(rpm_arr < 0):
            raise ErrorDeDiseno("La velocidad de giro no puede ser negativa.")
        polos = self.diseno.rotor.numero_polos
        omega_e = fisica.velocidad_angular_electrica(rpm_arr, polos)
        tension_pico = fisica.fem_pico(self.diseno.estator.espiras_totales, omega_e, self.flujo_maximo_por_espira_wb)
        return PuntoDeOperacion(
            rpm=rpm_arr,
            velocidad_angular_mecanica=fisica.velocidad_angular_mecanica(rpm_arr),
            frecuencia_electrica_hz=fisica.frecuencia_electrica(rpm_arr, polos),
            velocidad_angular_electrica=omega_e,
            tension_pico_v=tension_pico,
            tension_rms_v=tension_pico / np.sqrt(2),
            tension_dc_v=fisica.tension_rectificada(tension_pico, self.diseno.rectificador),
        )

    def forma_de_onda(self, rpm: float, ciclos: int = 2, muestras: int = 1000) -> FormaDeOnda:
        """Phi(t) = Phi_max cos(omega_e t)  y  e(t) = N_total omega_e Phi_max sin(omega_e t)."""
        if rpm <= 0:
            raise ErrorDeDiseno("Se necesita una velocidad positiva para trazar la forma de onda.")
        punto = self.punto_de_operacion(rpm)
        omega_e = float(punto.velocidad_angular_electrica)
        tiempo = np.linspace(0.0, ciclos / float(punto.frecuencia_electrica_hz), muestras)
        return FormaDeOnda(
            tiempo_s=tiempo,
            flujo_por_espira_wb=self.flujo_maximo_por_espira_wb * np.cos(omega_e * tiempo),
            fem_v=float(punto.tension_pico_v) * np.sin(omega_e * tiempo),
        )

    def operar_con_carga(self, rpm: ArrayLike, resistencia_carga_ohm: ArrayLike) -> OperacionConCarga:
        """Balance de potencias; el par resistente de Lenz es P_mec / omega_m."""
        punto = self.punto_de_operacion(rpm)
        carga = np.asarray(resistencia_carga_ohm, dtype=float)
        if np.any(carga <= 0):
            raise ErrorDeDiseno("La resistencia de carga debe ser positiva.")
        corriente = fisica.corriente_en_carga(punto.tension_rms_v, self.resistencia_interna_ohm, carga)
        potencia_carga = corriente**2 * carga
        perdidas = corriente**2 * self.resistencia_interna_ohm
        potencia_mecanica = potencia_carga + perdidas
        omega_m = punto.velocidad_angular_mecanica
        par = np.divide(potencia_mecanica, omega_m, out=np.zeros_like(potencia_mecanica), where=omega_m > 0)
        return OperacionConCarga(
            resistencia_carga_ohm=carga,
            corriente_rms_a=corriente,
            tension_carga_rms_v=corriente * carga,
            potencia_carga_w=potencia_carga,
            potencia_perdidas_cobre_w=perdidas,
            potencia_mecanica_w=potencia_mecanica,
            par_resistente_nm=par,
            eficiencia=carga / (carga + self.resistencia_interna_ohm),
        )

    def operar_con_carga_adaptada(self, rpm: ArrayLike) -> OperacionConCarga:
        """Teorema de máxima transferencia de potencia: R_L = R_int."""
        return self.operar_con_carga(rpm, self.resistencia_interna_ohm)

    @property
    def bateria(self) -> Bateria:
        return self.diseno.bateria if self.diseno.bateria is not None else Bateria()

    @property
    def controlador_carga(self) -> ControladorCarga:
        return self.diseno.controlador_carga if self.diseno.controlador_carga is not None else ControladorCarga()

    @property
    def inversor(self) -> InversorAc:
        return self.diseno.inversor if self.diseno.inversor is not None else InversorAc()

    def corriente_carga_bateria_a(self, rpm: ArrayLike, soc: float) -> Vector:
        """Corriente que el controlador MPPT entrega a la batería con el generador girando a ``rpm``."""
        punto = self.punto_de_operacion(rpm)
        return fisica.corriente_carga_bateria(
            punto.tension_dc_v, punto.tension_rms_v, self.resistencia_interna_ohm,
            self.bateria, soc, self.controlador_carga,
        )

    def _corriente_generador_a(self, fem_rms_v: float, potencia_w: float) -> float:
        """Corriente eficaz con la que el generador entrega ``potencia_w`` a su carga.

        De P = E·I − I²·R se toma la raíz menor (rama de alta eficiencia, R_L >= R_int).
        """
        if potencia_w <= 0:
            return 0.0
        r = self.resistencia_interna_ohm
        discriminante = max(0.0, fem_rms_v**2 - 4 * r * potencia_w)
        return (fem_rms_v - math.sqrt(discriminante)) / (2 * r)

    def balance_microred(self, rpm: float, potencia_carga_ac_w: float = 0.0, soc: float | None = None) -> BalanceMicrored:
        """Balance de potencias en régimen permanente para un SoC dado (por defecto, el inicial)."""
        if rpm < 0:
            raise ErrorDeDiseno("La velocidad de giro no puede ser negativa.")
        bateria, controlador, inversor = self.bateria, self.controlador_carga, self.inversor
        inversor.exigir_capacidad(potencia_carga_ac_w)
        soc = bateria.soc_inicial if soc is None else float(soc)
        tension_bateria = bateria.tension_circuito_abierto_v(soc)

        potencia_hacia_bateria = float(self.corriente_carga_bateria_a(rpm, soc)) * tension_bateria
        potencia_generador = potencia_hacia_bateria / controlador.eficiencia
        fem_rms = float(self.punto_de_operacion(rpm).tension_rms_v)
        corriente_generador = self._corriente_generador_a(fem_rms, potencia_generador)
        perdidas_cobre = corriente_generador**2 * self.resistencia_interna_ohm
        potencia_mecanica = potencia_generador + perdidas_cobre
        omega_m = float(fisica.velocidad_angular_mecanica(rpm))

        inversor_activo = soc > bateria.soc_minimo_descarga
        potencia_ac = potencia_carga_ac_w if inversor_activo else 0.0
        potencia_entrada_inversor = inversor.potencia_entrada_w(potencia_ac)
        potencia_neta = potencia_hacia_bateria - potencia_entrada_inversor
        autonomia = bateria.energia_utilizable_wh(soc) / -potencia_neta if potencia_neta < 0 else float("inf")

        return BalanceMicrored(
            rpm=float(rpm),
            soc=soc,
            tension_bateria_v=tension_bateria,
            potencia_mecanica_w=potencia_mecanica,
            potencia_generador_w=potencia_generador,
            potencia_perdidas_cobre_w=perdidas_cobre,
            par_resistente_nm=potencia_mecanica / omega_m if omega_m > 0 else 0.0,
            potencia_hacia_bateria_w=potencia_hacia_bateria,
            inversor_activo=inversor_activo,
            potencia_carga_ac_w=potencia_ac,
            potencia_entrada_inversor_w=potencia_entrada_inversor,
            potencia_neta_bateria_w=potencia_neta,
            autonomia_h=autonomia,
        )

    def rpm_de_equilibrio(self, potencia_carga_ac_w: float) -> float:
        """Velocidad a la que el generador repone exactamente lo que consume el inversor.

        eta_c·E_rms²/(4 R_int) = P_AC/eta_inv  y  E_rms ∝ RPM. Devuelve ``inf`` si el
        controlador no puede entregar esa corriente a ninguna velocidad.
        """
        bateria, controlador = self.bateria, self.controlador_carga
        potencia_entrada = self.inversor.potencia_entrada_w(potencia_carga_ac_w)
        if potencia_entrada == 0:
            return 0.0
        tension_minima_bateria = bateria.tension_circuito_abierto_v(0.0)
        if potencia_entrada / tension_minima_bateria > controlador.corriente_maxima_salida_a:
            return float("inf")
        fem_requerida = math.sqrt(4 * self.resistencia_interna_ohm * potencia_entrada / controlador.eficiencia)
        fem_por_rpm = float(self.punto_de_operacion(1.0).tension_rms_v)
        return fem_requerida / fem_por_rpm

    def simular_bateria(
        self,
        rpm: float,
        potencia_carga_ac_w: float = 0.0,
        duracion_h: float = 1.0,
        paso_s: float = 30.0,
        soc_inicial: float | None = None,
    ) -> EvolucionBateria:
        """Integra dSoC/dt = (I_carga − I_inversor) / C con desconexión por baja carga e histéresis."""
        if rpm < 0:
            raise ErrorDeDiseno("La velocidad de giro no puede ser negativa.")
        exigir_positivo("La duración de la simulación", duracion_h)
        exigir_positivo("El paso de integración", paso_s)
        bateria, inversor = self.bateria, self.inversor
        inversor.exigir_capacidad(potencia_carga_ac_w)

        punto = self.punto_de_operacion(rpm)
        pasos = int(round(duracion_h * 3600 / paso_s)) + 1
        tiempo_h = np.arange(pasos) * paso_s / 3600
        soc_hist, tension_hist, carga_hist, descarga_hist = (np.zeros(pasos) for _ in range(4))
        activo_hist = np.zeros(pasos, dtype=bool)

        soc = bateria.soc_inicial if soc_inicial is None else float(soc_inicial)
        habilitado = soc > bateria.soc_minimo_descarga
        for i in range(pasos):
            if soc <= bateria.soc_minimo_descarga:
                habilitado = False
            elif soc >= bateria.soc_minimo_descarga + bateria.histeresis_reconexion_soc:
                habilitado = True
            tension_oc = bateria.tension_circuito_abierto_v(soc)
            corriente_carga = float(fisica.corriente_carga_bateria(
                punto.tension_dc_v, punto.tension_rms_v, self.resistencia_interna_ohm,
                bateria, soc, self.controlador_carga,
            ))
            corriente_descarga = inversor.corriente_primario_bateria_a(potencia_carga_ac_w, tension_oc) if habilitado else 0.0
            corriente_neta = corriente_carga - corriente_descarga

            soc_hist[i], activo_hist[i] = soc, habilitado
            tension_hist[i] = tension_oc + corriente_neta * bateria.resistencia_interna_ohm
            carga_hist[i], descarga_hist[i] = corriente_carga, corriente_descarga
            soc = min(1.0, max(0.0, soc + corriente_neta * paso_s / bateria.capacidad_coulomb))

        return EvolucionBateria(
            tiempo_h=tiempo_h,
            soc=soc_hist,
            tension_bateria_v=tension_hist,
            corriente_carga_a=carga_hist,
            corriente_descarga_a=descarga_hist,
            inversor_activo=activo_hist,
        )

    def forma_de_onda_inversor(
        self,
        tension_rms_v: float | None = None,
        frecuencia_hz: float | None = None,
        potencia_carga_w: float = 0.0,
        ciclos: int = 3,
        muestras: int = 1000,
    ) -> SalidaInversor:
        """v(t) = √2·V_RMS·sin(2πft); por defecto con la tensión y frecuencia del inversor del diseño."""
        inversor = self.inversor
        tension_rms = inversor.tension_salida_rms_v if tension_rms_v is None else float(tension_rms_v)
        frecuencia = inversor.frecuencia_hz if frecuencia_hz is None else float(frecuencia_hz)
        tiempo = np.linspace(0.0, ciclos / frecuencia, muestras)
        tension_bateria = self.bateria.tension_circuito_abierto_v(self.bateria.soc_inicial)
        return SalidaInversor(
            tiempo_s=tiempo,
            tension_ac_v=fisica.forma_de_onda_inversor(tension_rms, frecuencia, tiempo),
            tension_rms_v=tension_rms,
            frecuencia_hz=frecuencia,
            potencia_carga_w=float(potencia_carga_w),
            corriente_rms_a=fisica.corriente_salida_inversor(potencia_carga_w, tension_rms),
            corriente_bateria_a=inversor.corriente_primario_bateria_a(potencia_carga_w, tension_bateria),
        )
