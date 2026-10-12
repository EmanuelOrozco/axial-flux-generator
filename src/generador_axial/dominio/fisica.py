"""Leyes físicas del generador como funciones puras y vectorizables con NumPy.

Referencias (Sadiku, *Elementos de Electromagnetismo*, 3.ª ed.):
- Campo de un imán: modelo de corriente superficial ligada K_b = M x a_n (Sec. 8.5)
  aplicado a la expresión del campo en el eje de un solenoide finito (Cap. 7).
- Ley de Faraday y fem de movimiento/transformador (Sec. 9.2 y 9.3).
"""

from __future__ import annotations

import math

import numpy as np
from numpy.typing import ArrayLike, NDArray

from generador_axial.dominio.componentes import (
    Bateria,
    ControladorCarga,
    ImanPermanente,
    Rectificador,
)
from generador_axial.dominio.errores import exigir_positivo

Vector = NDArray[np.float64]


def campo_axial(iman: ImanPermanente, z_m: ArrayLike) -> Vector:
    """B_z sobre el eje del imán a una distancia z de su cara.

    B_z(z) = (Br/2) [ (z+L)/sqrt((z+L)^2+R^2) - z/sqrt(z^2+R^2) ]
    """
    z = np.asarray(z_m, dtype=float)
    radio, espesor = iman.radio_m, iman.espesor_m
    return 0.5 * iman.remanencia_t * ((z + espesor) / np.hypot(z + espesor, radio) - z / np.hypot(z, radio))


def _primitiva_campo_axial(iman: ImanPermanente, z: Vector) -> Vector:
    """Primitiva de B_z respecto a z (sin el factor Br/2)."""
    return np.hypot(z + iman.espesor_m, iman.radio_m) - np.hypot(z, iman.radio_m)


def campo_medio_en_tramo(iman: ImanPermanente, z_inicial_m: ArrayLike, longitud_m: float) -> Vector:
    """Promedio exacto de B_z en el tramo [z0, z0 + h], donde se reparten las espiras de la bobina."""
    exigir_positivo("La longitud del tramo de promediado", longitud_m)
    z0 = np.asarray(z_inicial_m, dtype=float)
    integral = _primitiva_campo_axial(iman, z0 + longitud_m) - _primitiva_campo_axial(iman, z0)
    return 0.5 * iman.remanencia_t * integral / longitud_m


def velocidad_angular_mecanica(rpm: ArrayLike) -> Vector:
    """omega_m = 2*pi*RPM/60 [rad/s]."""
    return 2 * math.pi * np.asarray(rpm, dtype=float) / 60


def frecuencia_electrica(rpm: ArrayLike, numero_polos: int) -> Vector:
    """f_e = P*RPM/120 [Hz]: cada par de polos completa un ciclo eléctrico por vuelta."""
    return numero_polos * np.asarray(rpm, dtype=float) / 120


def velocidad_angular_electrica(rpm: ArrayLike, numero_polos: int) -> Vector:
    """omega_e = 2*pi*f_e = (P/2)*omega_m [rad/s]."""
    return 2 * math.pi * frecuencia_electrica(rpm, numero_polos)


def fem_pico(espiras_totales: int, omega_electrica: ArrayLike, flujo_maximo_wb: float) -> Vector:
    """Amplitud de e(t) = -N dPhi/dt con Phi(t) = Phi_max cos(omega_e t)."""
    return espiras_totales * np.asarray(omega_electrica, dtype=float) * flujo_maximo_wb


def tension_rectificada(tension_pico_v: ArrayLike, rectificador: Rectificador) -> Vector:
    """Tensión DC en vacío tras el puente de diodos y el condensador de filtro."""
    return np.maximum(0.0, np.asarray(tension_pico_v, dtype=float) - rectificador.caida_total_v)


def rizado_pico_a_pico(corriente_a: float, frecuencia_electrica_hz: float, capacitancia_f: float) -> float:
    """Rectificación de onda completa: el condensador se recarga a 2 f_e, por lo que dV = I / (2 f_e C)."""
    return corriente_a / (2 * frecuencia_electrica_hz * capacitancia_f)


def corriente_en_carga(fem_rms_v: ArrayLike, resistencia_interna_ohm: float, resistencia_carga_ohm: ArrayLike) -> Vector:
    """Circuito de Thévenin: I = E / (R_int + R_L)."""
    return np.asarray(fem_rms_v, dtype=float) / (resistencia_interna_ohm + np.asarray(resistencia_carga_ohm, dtype=float))


def potencia_maxima_extraible(fem_rms_v: ArrayLike, resistencia_interna_ohm: float) -> Vector:
    """Máxima transferencia sobre el equivalente de Thévenin del generador: P = E_rms² / (4 R_int).

    Se usa la fem eficaz (no la de pico): con R_L = R_int la mitad de E_rms cae en la carga.
    """
    exigir_positivo("La resistencia interna del generador", resistencia_interna_ohm)
    return np.asarray(fem_rms_v, dtype=float) ** 2 / (4 * resistencia_interna_ohm)


def corriente_carga_bateria(
    tension_dc_v: ArrayLike,
    fem_rms_v: ArrayLike,
    resistencia_interna_ohm: float,
    bateria: Bateria,
    soc: float,
    controlador: ControladorCarga,
) -> Vector:
    """Corriente que el controlador MPPT inyecta en la batería (despreciando la caída del puente).

    - Arranca solo si la tensión rectificada en vacío alcanza su umbral mínimo.
    - Entrega I = eta·P_max / E_oc(SoC), limitada por su corriente máxima y porque la tensión
      en bornes no puede superar la de absorción: E_oc + I·R_bat <= V_abs.
    - Con la batería llena (SoC = 1) deja de cargar.
    """
    v_dc = np.asarray(tension_dc_v, dtype=float)
    if soc >= 1.0:
        return np.zeros_like(v_dc)
    v_oc = bateria.tension_circuito_abierto_v(soc)
    potencia = controlador.eficiencia * potencia_maxima_extraible(fem_rms_v, resistencia_interna_ohm)
    corriente = np.where(v_dc >= controlador.tension_minima_arranque_v, potencia / v_oc, 0.0)
    limite_absorcion = max(0.0, (controlador.tension_corte_absorcion_v - v_oc) / bateria.resistencia_interna_ohm)
    return np.clip(corriente, 0.0, min(controlador.corriente_maxima_salida_a, limite_absorcion))


def forma_de_onda_inversor(tension_rms_v: float, frecuencia_hz: float, tiempo_s: ArrayLike) -> Vector:
    """Tensión senoidal de salida del inversor: v(t) = sqrt(2) * V_RMS * sin(2*pi*f*t)."""
    t = np.asarray(tiempo_s, dtype=float)
    v_pico = math.sqrt(2) * float(tension_rms_v)
    return v_pico * np.sin(2 * math.pi * float(frecuencia_hz) * t)


def corriente_salida_inversor(potencia_carga_w: float, tension_rms_v: float) -> float:
    """Corriente eficaz entregada a la carga en bornes de 110V o 220V: I = P / V_RMS."""
    if tension_rms_v <= 0 or potencia_carga_w <= 0:
        return 0.0
    return float(potencia_carga_w) / float(tension_rms_v)

