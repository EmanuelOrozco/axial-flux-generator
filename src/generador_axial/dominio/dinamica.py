"""Leyes físicas del modelo realista como funciones puras escalares.

Se escriben con ``math`` (no NumPy) y con el mismo orden de operaciones que
``visualizador_3d/js/modelo/dinamica.js``: la prueba de paridad compara ambas implementaciones
paso a paso.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from generador_axial.dominio.diseno import DisenoGenerador
from generador_axial.dominio.realista import BateriaPlomoAcido, MaterialesRotor

FACTOR_CORRIENTE_MEDIA = 2 * math.sqrt(2) / math.pi  # I_media / I_rms de una senoide rectificada
MICROHENRIOS_WHEELER = 31.6e-6  # constante de la fórmula de Wheeler en unidades SI


# ---------------------------------------------------------------- geometría del flujo
def area_lente(r1: float, r2: float, d: float) -> float:
    """Área común de dos círculos de radios r1 y r2 cuyos centros distan d."""
    if d >= r1 + r2:
        return 0.0
    if d <= abs(r1 - r2):
        return math.pi * min(r1, r2) ** 2
    a1 = r1 * r1 * math.acos((d * d + r1 * r1 - r2 * r2) / (2 * d * r1))
    a2 = r2 * r2 * math.acos((d * d + r2 * r2 - r1 * r1) / (2 * d * r2))
    a3 = 0.5 * math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2))
    return a1 + a2 - a3


def cuerda_lente(r1: float, r2: float, d: float) -> float:
    """Longitud de la cuerda común de dos círculos; es −dA/dd del área de la lente."""
    if d >= r1 + r2 or d <= abs(r1 - r2):
        return 0.0
    return math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2)) / d


@dataclass(frozen=True)
class PerfilDeFlujo:
    """Flujo normalizado por espira φ(θe) = Φ/(B̄·A_imán) y su derivada en un periodo eléctrico.

    Supone B uniforme sobre la huella de cada imán y nulo fuera de ella; las espiras se reparten
    uniformemente entre el radio interior y el exterior de la bobina.
    """

    flujo: tuple[float, ...]
    derivada: tuple[float, ...]
    pico_derivada: float
    rms_derivada: float
    media_abs_derivada: float

    @property
    def factor_cresta(self) -> float:
        return self.pico_derivada / self.rms_derivada

    @property
    def factor_media(self) -> float:
        """Valor medio rectificado de la fem relativo a su pico."""
        return self.media_abs_derivada / self.pico_derivada

    @property
    def flujo_maximo(self) -> float:
        return max(self.flujo)

    def derivada_en(self, angulo_electrico_rad: float) -> float:
        """dφ/dθe interpolada linealmente (periódica)."""
        muestras = len(self.derivada)
        posicion = (angulo_electrico_rad / (2 * math.pi)) % 1.0 * muestras
        indice = math.floor(posicion)
        fraccion = posicion - indice
        a = self.derivada[indice % muestras]
        b = self.derivada[(indice + 1) % muestras]
        return a + (b - a) * fraccion


def perfil_de_flujo(diseno: DisenoGenerador, puntos_radiales: int, muestras: int) -> PerfilDeFlujo:
    radio_iman = diseno.rotor.iman.radio_m
    area_iman = math.pi * radio_iman**2
    bobina = diseno.estator.bobina
    radio_interior, radio_exterior = bobina.diametro_interior_m / 2, bobina.diametro_exterior_m / 2
    radio_montaje = diseno.rotor.radio_montaje_m
    polos = diseno.rotor.numero_polos
    pares = polos // 2
    paso_radial = (radio_exterior - radio_interior) / puntos_radiales

    flujo, derivada = [], []
    for j in range(muestras):
        angulo_mecanico = (2 * math.pi * j / muestras) / pares
        suma_flujo = 0.0
        suma_derivada = 0.0
        for i in range(puntos_radiales):
            rho = radio_interior + (i + 0.5) * paso_radial
            for k in range(polos):
                x = angulo_mecanico + 2 * math.pi * k / polos
                delta = math.atan2(math.sin(x), math.cos(x))
                distancia = 2 * radio_montaje * math.sin(abs(delta) / 2)
                signo = 1.0 if k % 2 == 0 else -1.0
                signo_delta = (delta > 0) - (delta < 0)
                suma_flujo += signo * area_lente(rho, radio_iman, distancia)
                suma_derivada -= (
                    signo * cuerda_lente(rho, radio_iman, distancia) * radio_montaje * math.cos(delta / 2) * signo_delta
                )
        flujo.append(suma_flujo / (puntos_radiales * area_iman))
        derivada.append(suma_derivada / (puntos_radiales * area_iman * pares))

    pico = max(abs(v) for v in derivada)
    rms = math.sqrt(sum(v * v for v in derivada) / muestras)
    media = sum(abs(v) for v in derivada) / muestras
    return PerfilDeFlujo(tuple(flujo), tuple(derivada), pico, rms, media)


# ---------------------------------------------------------------- parámetros eléctricos y mecánicos
def inductancia_bobina_h(espiras: int, radio_medio_m: float, altura_m: float, profundidad_radial_m: float) -> float:
    """Fórmula de Wheeler para bobinas multicapa con núcleo de aire: L = 31.6·N²·r²/(6r + 9ℓ + 10c) [µH, m]."""
    return MICROHENRIOS_WHEELER * espiras**2 * radio_medio_m**2 / (
        6 * radio_medio_m + 9 * altura_m + 10 * profundidad_radial_m
    )


def momento_de_inercia_rotor(diseno: DisenoGenerador, materiales: MaterialesRotor) -> float:
    """J = disco − alojamientos + imanes + eje [kg·m²]."""
    m = diseno.mecanica
    radio_disco = m.diametro_disco_rotor_m / 2
    iman = diseno.rotor.iman
    radio_montaje = diseno.rotor.radio_montaje_m
    polos = diseno.rotor.numero_polos

    masa_disco = materiales.densidad_disco_kg_m3 * math.pi * radio_disco**2 * m.espesor_disco_rotor_m
    radio_alojamiento = m.con_holgura(iman.diametro_m) / 2
    masa_alojamiento = materiales.densidad_disco_kg_m3 * math.pi * radio_alojamiento**2 * m.profundidad_alojamiento_iman_m
    masa_iman = materiales.densidad_iman_kg_m3 * math.pi * iman.radio_m**2 * iman.espesor_m
    masa_eje = materiales.densidad_eje_kg_m3 * math.pi * (m.diametro_eje_m / 2) ** 2 * materiales.longitud_eje_m

    j_disco = 0.5 * masa_disco * radio_disco**2
    j_alojamientos = polos * masa_alojamiento * (radio_alojamiento**2 / 2 + radio_montaje**2)
    j_imanes = polos * masa_iman * (iman.radio_m**2 / 2 + radio_montaje**2)
    j_eje = 0.5 * masa_eje * (m.diametro_eje_m / 2) ** 2
    return j_disco - j_alojamientos + j_imanes + j_eje


def perdidas_foucault_w(volumen_cobre_m3: float, fraccion_expuesta: float, omega_electrica: float,
                        campo_t: float, diametro_hilo_m: float, resistividad_ohm_m: float) -> float:
    """Corrientes de Foucault en hilo redondo bajo campo transversal: P/V = ω²·B²·d²/(32ρ)."""
    return volumen_cobre_m3 * fraccion_expuesta * omega_electrica**2 * campo_t**2 * diametro_hilo_m**2 / (
        32 * resistividad_ohm_m
    )


# ---------------------------------------------------------------- rectificador + MPPT
def biseccion(funcion: Callable[[float], float], a: float, b: float, iteraciones: int) -> float:
    """Raíz de una función decreciente con f(a) ≥ 0 ≥ f(b)."""
    for _ in range(iteraciones):
        medio = 0.5 * (a + b)
        if funcion(medio) > 0:
            a = medio
        else:
            b = medio
    return 0.5 * (a + b)


def potencia_dc(fem_rms: float, resistencia: float, reactancia: float, caida_diodos: float, corriente: float) -> float:
    """P_DC(I) = I·√(E² − X²I²) − R·I² − 2V_D·I_media: potencia que el puente entrega al bus DC."""
    tension_interna = math.sqrt(max(0.0, fem_rms**2 - (reactancia * corriente) ** 2))
    return corriente * tension_interna - resistencia * corriente**2 - caida_diodos * FACTOR_CORRIENTE_MEDIA * corriente


def derivada_potencia_dc(fem_rms: float, resistencia: float, reactancia: float, caida_diodos: float,
                         corriente: float) -> float:
    tension_interna = math.sqrt(max(1e-30, fem_rms**2 - (reactancia * corriente) ** 2))
    return ((fem_rms**2 - 2 * (reactancia * corriente) ** 2) / tension_interna
            - 2 * resistencia * corriente - caida_diodos * FACTOR_CORRIENTE_MEDIA)


def tension_bornes_rms(fem_rms: float, resistencia: float, reactancia: float, corriente: float) -> float:
    """Con carga equivalente resistiva: V = I·R_eq = √(E² − X²I²) − R·I."""
    return max(0.0, math.sqrt(max(0.0, fem_rms**2 - (reactancia * corriente) ** 2)) - resistencia * corriente)


def rizado_pico_a_pico(corriente_rms: float, frecuencia_hz: float, capacitancia_f: float) -> float:
    if frecuencia_hz <= 0:
        return 0.0
    return FACTOR_CORRIENTE_MEDIA * corriente_rms / (2 * frecuencia_hz * capacitancia_f)


def tension_dc_media(tension_bornes: float, factor_cresta: float, factor_media: float, caida_diodos: float,
                     rizado: float) -> float:
    """Bus DC: pico menos diodos menos medio rizado, sin bajar del valor medio rectificado sin filtro."""
    pico = factor_cresta * tension_bornes
    return max(0.0, pico - caida_diodos - rizado / 2, pico * factor_media - caida_diodos)


# ---------------------------------------------------------------- batería de plomo-ácido
def interpolar_curva(curva: tuple[tuple[float, float], ...], x: float) -> float:
    if x <= curva[0][0]:
        return curva[0][1]
    for (x0, y0), (x1, y1) in zip(curva, curva[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return curva[-1][1]


def tension_reposo(bateria: BateriaPlomoAcido, soc: float) -> float:
    return interpolar_curva(bateria.curva_ocv, soc)


def resistencia_polarizacion(bateria: BateriaPlomoAcido, soc: float, corriente_a: float) -> float:
    """R_p en descarga; al cargar se suma el sobrepotencial de gasificación A·e^(B·(SoC − 1))."""
    if corriente_a <= 0:
        return bateria.resistencia_polarizacion_ohm
    return bateria.resistencia_polarizacion_ohm * (
        1 + bateria.factor_sobrepotencial_carga * math.exp(bateria.pendiente_sobrepotencial_carga * (soc - 1))
    )


def eficiencia_coulomb(bateria: BateriaPlomoAcido, soc: float) -> float:
    """Constante hasta el inicio de la gasificación y decreciente linealmente hasta SoC = 1."""
    if soc <= bateria.soc_inicio_gasificacion:
        return bateria.eficiencia_coulomb
    fraccion = min(1.0, (soc - bateria.soc_inicio_gasificacion) / (1 - bateria.soc_inicio_gasificacion))
    return bateria.eficiencia_coulomb + (bateria.eficiencia_coulomb_llena - bateria.eficiencia_coulomb) * fraccion


def corriente_efectiva_peukert(bateria: BateriaPlomoAcido, capacidad_ah: float, corriente_descarga_a: float) -> float:
    """I_ef = I·(I/I_n)^(k−1), con I_n = C/h_n: a mayor corriente, menor capacidad aprovechable."""
    if corriente_descarga_a <= 0:
        return 0.0
    corriente_nominal = capacidad_ah / bateria.horas_regimen_nominal
    return corriente_descarga_a * (corriente_descarga_a / corriente_nominal) ** (bateria.exponente_peukert - 1)


def corriente_para_potencia(fem_v: float, resistencia_ohm: float, potencia_w: float) -> float:
    """Corriente neta I (positiva cargando) tal que I·(E + R·I) = P, rama físicamente estable."""
    discriminante = fem_v**2 + 4 * resistencia_ohm * potencia_w
    if discriminante <= 0:
        return -fem_v / (2 * resistencia_ohm)
    return (-fem_v + math.sqrt(discriminante)) / (2 * resistencia_ohm)


# ---------------------------------------------------------------- inversor
def potencia_entrada_inversor(potencia_ac_w: float, potencia_nominal_w: float, eficiencia_nominal: float,
                              potencia_vacio_w: float) -> float:
    """P_entrada = P_0 + P + k·P², con k tal que la eficiencia a potencia nominal sea la de catálogo."""
    k = (potencia_nominal_w / eficiencia_nominal - potencia_nominal_w - potencia_vacio_w) / potencia_nominal_w**2
    return potencia_vacio_w + potencia_ac_w + max(0.0, k) * potencia_ac_w**2
