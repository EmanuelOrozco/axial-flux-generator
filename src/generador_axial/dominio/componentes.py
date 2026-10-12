"""Entidades físicas del generador. Todas las magnitudes están en unidades SI."""

from __future__ import annotations

import math
from dataclasses import dataclass

from generador_axial.dominio.errores import ErrorDeDiseno, exigir_positivo

RESISTIVIDAD_COBRE_20C_OHM_M = 1.72e-8


@dataclass(frozen=True)
class ImanPermanente:
    """Imán cilíndrico de NdFeB con imanación axial uniforme."""

    grado: str
    remanencia_t: float
    diametro_m: float
    espesor_m: float

    def __post_init__(self) -> None:
        exigir_positivo("La remanencia Br", self.remanencia_t)
        exigir_positivo("El diámetro del imán", self.diametro_m)
        exigir_positivo("El espesor del imán", self.espesor_m)

    @property
    def radio_m(self) -> float:
        return self.diametro_m / 2

    @property
    def area_cara_m2(self) -> float:
        return math.pi * self.radio_m**2


@dataclass(frozen=True)
class AlambreMagneto:
    """Alambre de cobre esmaltado usado para devanar las bobinas."""

    calibre_awg: int
    diametro_cobre_m: float
    diametro_esmaltado_m: float
    resistividad_ohm_m: float = RESISTIVIDAD_COBRE_20C_OHM_M

    def __post_init__(self) -> None:
        exigir_positivo("El diámetro del cobre", self.diametro_cobre_m)
        exigir_positivo("La resistividad", self.resistividad_ohm_m)
        if self.diametro_esmaltado_m < self.diametro_cobre_m:
            raise ErrorDeDiseno("El diámetro con esmalte no puede ser menor que el del cobre desnudo.")

    @property
    def area_cobre_m2(self) -> float:
        return math.pi * (self.diametro_cobre_m / 2) ** 2


@dataclass(frozen=True)
class Bobina:
    """Bobina plana con núcleo de aire (sección rectangular en el plano r-z)."""

    espiras: int
    diametro_interior_m: float
    diametro_exterior_m: float
    altura_m: float
    alambre: AlambreMagneto

    def __post_init__(self) -> None:
        exigir_positivo("El número de espiras", self.espiras)
        exigir_positivo("El diámetro interior de la bobina", self.diametro_interior_m)
        exigir_positivo("La altura de la bobina", self.altura_m)
        if self.diametro_exterior_m <= self.diametro_interior_m:
            raise ErrorDeDiseno("El diámetro exterior de la bobina debe superar al interior.")
        if self.factor_ocupacion > 1:
            raise ErrorDeDiseno(
                f"Las {self.espiras} espiras no caben en la ventana de la bobina "
                f"(ocupación {self.factor_ocupacion:.2f} > 1)."
            )

    @property
    def longitud_media_espira_m(self) -> float:
        return math.pi * (self.diametro_interior_m + self.diametro_exterior_m) / 2

    @property
    def longitud_alambre_m(self) -> float:
        return self.espiras * self.longitud_media_espira_m

    @property
    def resistencia_ohm(self) -> float:
        return self.alambre.resistividad_ohm_m * self.longitud_alambre_m / self.alambre.area_cobre_m2

    @property
    def area_ventana_m2(self) -> float:
        return (self.diametro_exterior_m - self.diametro_interior_m) / 2 * self.altura_m

    @property
    def factor_ocupacion(self) -> float:
        """Fracción de la ventana ocupada si cada espira requiere un cuadrado de lado d_esmaltado."""
        return self.espiras * self.alambre.diametro_esmaltado_m**2 / self.area_ventana_m2


@dataclass(frozen=True)
class Rotor:
    """Disco giratorio con imanes de polaridad alternada N-S-N-S."""

    numero_polos: int
    radio_montaje_m: float
    iman: ImanPermanente

    def __post_init__(self) -> None:
        if self.numero_polos < 2 or self.numero_polos % 2:
            raise ErrorDeDiseno("El número de polos debe ser par y mayor o igual a 2.")
        exigir_positivo("El radio de montaje de los imanes", self.radio_montaje_m)
        if distancia_entre_centros(self.radio_montaje_m, self.numero_polos) <= self.iman.diametro_m:
            raise ErrorDeDiseno("Los imanes se solapan: aumente el radio de montaje o reduzca los polos.")

    @property
    def pares_de_polos(self) -> int:
        return self.numero_polos // 2

    @property
    def paso_polar_rad(self) -> float:
        return 2 * math.pi / self.numero_polos


@dataclass(frozen=True)
class Estator:
    """Placa fija con bobinas conectadas en serie con polaridad alternada."""

    numero_bobinas: int
    radio_montaje_m: float
    bobina: Bobina

    def __post_init__(self) -> None:
        exigir_positivo("El número de bobinas", self.numero_bobinas)
        exigir_positivo("El radio de montaje de las bobinas", self.radio_montaje_m)
        if distancia_entre_centros(self.radio_montaje_m, self.numero_bobinas) <= self.bobina.diametro_exterior_m:
            raise ErrorDeDiseno("Las bobinas se solapan: aumente el radio de montaje o reduzca su diámetro.")

    @property
    def espiras_totales(self) -> int:
        return self.numero_bobinas * self.bobina.espiras

    @property
    def resistencia_interna_ohm(self) -> float:
        return self.numero_bobinas * self.bobina.resistencia_ohm


@dataclass(frozen=True)
class Rectificador:
    """Puente de Graetz con condensador de filtro: en cada semiciclo conducen dos diodos en serie."""

    caida_por_diodo_v: float
    capacitancia_filtro_f: float
    tension_nominal_condensador_v: float
    diodos_en_conduccion: int = 2

    def __post_init__(self) -> None:
        if self.caida_por_diodo_v < 0:
            raise ErrorDeDiseno("La caída de tensión del diodo no puede ser negativa.")
        exigir_positivo("La capacitancia del filtro", self.capacitancia_filtro_f)
        exigir_positivo("La tensión nominal del condensador", self.tension_nominal_condensador_v)

    @property
    def caida_total_v(self) -> float:
        return self.caida_por_diodo_v * self.diodos_en_conduccion


@dataclass(frozen=True)
class IndicadorLed:
    """LED con resistencia limitadora conectado a la salida DC."""

    resistencia_ohm: float
    potencia_nominal_resistencia_w: float
    caida_led_v: float
    corriente_maxima_led_a: float

    def __post_init__(self) -> None:
        exigir_positivo("La resistencia del LED", self.resistencia_ohm)
        exigir_positivo("La potencia nominal de la resistencia", self.potencia_nominal_resistencia_w)
        exigir_positivo("La corriente máxima del LED", self.corriente_maxima_led_a)

    def corriente_a(self, tension_dc_v: float) -> float:
        return max(0.0, tension_dc_v - self.caida_led_v) / self.resistencia_ohm

    def potencia_resistencia_w(self, tension_dc_v: float) -> float:
        return self.corriente_a(tension_dc_v) ** 2 * self.resistencia_ohm


@dataclass(frozen=True)
class Bateria:
    """Batería de plomo-ácido AGM de 12 V: fem E_oc(SoC) en serie con R_bat.

    ``tension_minima_v`` y ``tension_maxima_v`` son las tensiones en reposo (circuito abierto)
    con SoC = 0 y SoC = 1; entre ellas la curva se aproxima por una recta.
    """

    tension_nominal_v: float = 12.0
    capacidad_ah: float = 7.0
    resistencia_interna_ohm: float = 0.05
    tension_minima_v: float = 11.8
    tension_maxima_v: float = 12.8
    soc_inicial: float = 0.50
    soc_minimo_descarga: float = 0.20
    histeresis_reconexion_soc: float = 0.05

    def __post_init__(self) -> None:
        exigir_positivo("La tensión nominal de la batería", self.tension_nominal_v)
        exigir_positivo("La capacidad de la batería", self.capacidad_ah)
        exigir_positivo("La resistencia interna de la batería", self.resistencia_interna_ohm)
        exigir_positivo("La histéresis de reconexión", self.histeresis_reconexion_soc)
        if self.tension_maxima_v <= self.tension_minima_v:
            raise ErrorDeDiseno("La tensión máxima de la batería debe superar a la mínima.")
        if not 0.0 <= self.soc_inicial <= 1.0:
            raise ErrorDeDiseno("El estado de carga (SoC) inicial debe estar entre 0.0 y 1.0.")
        if not 0.0 <= self.soc_minimo_descarga < 1.0:
            raise ErrorDeDiseno("El SoC mínimo de descarga debe estar en [0, 1).")

    @property
    def capacidad_coulomb(self) -> float:
        return self.capacidad_ah * 3600.0

    @property
    def energia_almacenada_wh(self) -> float:
        return self.tension_nominal_v * self.capacidad_ah

    def energia_utilizable_wh(self, soc: float) -> float:
        """Energía disponible hasta el corte por baja tensión (SoC mínimo de descarga)."""
        return max(0.0, float(soc) - self.soc_minimo_descarga) * self.energia_almacenada_wh

    def tension_circuito_abierto_v(self, soc: float) -> float:
        """E_oc(SoC) = V_min + (V_max − V_min)·SoC, con SoC recortado a [0, 1]."""
        soc_recortado = min(max(float(soc), 0.0), 1.0)
        return self.tension_minima_v + (self.tension_maxima_v - self.tension_minima_v) * soc_recortado


@dataclass(frozen=True)
class ControladorCarga:
    """Convertidor DC-DC con seguimiento del punto de máxima potencia (MPPT) y corte por absorción."""

    tension_corte_absorcion_v: float = 14.4
    tension_flotacion_v: float = 13.8
    tension_minima_arranque_v: float = 3.5
    corriente_maxima_salida_a: float = 3.0
    eficiencia: float = 0.90

    def __post_init__(self) -> None:
        exigir_positivo("La tensión de absorción", self.tension_corte_absorcion_v)
        exigir_positivo("La tensión de flotación", self.tension_flotacion_v)
        exigir_positivo("La tensión mínima de arranque", self.tension_minima_arranque_v)
        exigir_positivo("La corriente máxima de carga", self.corriente_maxima_salida_a)
        if not 0.0 < self.eficiencia <= 1.0:
            raise ErrorDeDiseno("La eficiencia del controlador debe cumplir 0 < eta <= 1.")
        if self.tension_flotacion_v > self.tension_corte_absorcion_v:
            raise ErrorDeDiseno("La tensión de flotación no puede superar a la de absorción.")


@dataclass(frozen=True)
class InversorAc:
    """Inversor DC/AC senoidal con transformador elevador (fem de transformador, Sadiku Sec. 9.3)."""

    tension_salida_rms_v: float = 110.0
    frecuencia_hz: float = 60.0
    potencia_nominal_w: float = 150.0
    eficiencia: float = 0.90

    def __post_init__(self) -> None:
        exigir_positivo("La tensión nominal de salida del inversor", self.tension_salida_rms_v)
        exigir_positivo("La frecuencia del inversor", self.frecuencia_hz)
        exigir_positivo("La potencia nominal del inversor", self.potencia_nominal_w)
        if not 0.0 < self.eficiencia <= 1.0:
            raise ErrorDeDiseno("La eficiencia del inversor debe cumplir 0 < eta <= 1.")

    @property
    def tension_pico_v(self) -> float:
        return math.sqrt(2) * self.tension_salida_rms_v

    def exigir_capacidad(self, potencia_carga_w: float) -> None:
        if potencia_carga_w < 0:
            raise ErrorDeDiseno("La potencia de la carga AC no puede ser negativa.")
        if potencia_carga_w > self.potencia_nominal_w:
            raise ErrorDeDiseno(
                f"La carga de {potencia_carga_w:.0f} W supera la potencia nominal del inversor "
                f"({self.potencia_nominal_w:.0f} W)."
            )

    def potencia_entrada_w(self, potencia_carga_w: float) -> float:
        """P_entrada = P_AC / eta_inv."""
        self.exigir_capacidad(potencia_carga_w)
        return potencia_carga_w / self.eficiencia

    def corriente_primario_bateria_a(self, potencia_carga_w: float, tension_bateria_v: float) -> float:
        """Corriente demandada a la batería para entregar la potencia AC demandada."""
        if tension_bateria_v <= 0 or potencia_carga_w <= 0:
            return 0.0
        return self.potencia_entrada_w(potencia_carga_w) / tension_bateria_v


def distancia_entre_centros(radio_montaje_m: float, cantidad: int) -> float:
    """Cuerda entre dos elementos consecutivos repartidos uniformemente en una circunferencia."""
    if cantidad < 2:
        return math.inf
    return 2 * radio_montaje_m * math.sin(math.pi / cantidad)

