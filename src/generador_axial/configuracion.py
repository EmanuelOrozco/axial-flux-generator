"""Única fuente de verdad de los parámetros del prototipo.

``visualizador_3d/js/config.js`` replica estos valores; la prueba
``tests/test_paridad_visualizador.py`` verifica que ambos coincidan.
"""

from __future__ import annotations

from dataclasses import dataclass

from generador_axial.dominio import (
    AlambreMagneto,
    Bateria,
    Bobina,
    ControladorCarga,
    DisenoGenerador,
    Estator,
    GeometriaMecanica,
    ImanPermanente,
    IndicadorLed,
    InversorAc,
    Rectificador,
    Rotor,
)


def diseno_por_defecto() -> DisenoGenerador:
    iman = ImanPermanente(grado="N38", remanencia_t=1.25, diametro_m=0.020, espesor_m=0.005)
    alambre = AlambreMagneto(calibre_awg=26, diametro_cobre_m=0.000404, diametro_esmaltado_m=0.000455)
    bobina = Bobina(
        espiras=180,
        diametro_interior_m=0.012,
        diametro_exterior_m=0.028,
        altura_m=0.006,
        alambre=alambre,
    )
    return DisenoGenerador(
        rotor=Rotor(numero_polos=8, radio_montaje_m=0.040, iman=iman),
        estator=Estator(numero_bobinas=8, radio_montaje_m=0.040, bobina=bobina),
        entrehierro_m=0.0025,
        factor_acoplamiento=0.85,
        rectificador=Rectificador(
            caida_por_diodo_v=0.3,
            capacitancia_filtro_f=220e-6,
            tension_nominal_condensador_v=50,
        ),
        indicador=IndicadorLed(
            resistencia_ohm=2200,
            potencia_nominal_resistencia_w=0.5,
            caida_led_v=2.0,
            corriente_maxima_led_a=0.020,
        ),
        mecanica=GeometriaMecanica(),
        bateria=Bateria(
            tension_nominal_v=12.0,
            capacidad_ah=7.0,
            resistencia_interna_ohm=0.05,
            tension_minima_v=11.8,
            tension_maxima_v=12.8,
            soc_inicial=0.50,
            soc_minimo_descarga=0.20,
            histeresis_reconexion_soc=0.05,
        ),
        controlador_carga=ControladorCarga(
            tension_corte_absorcion_v=14.4,
            tension_flotacion_v=13.8,
            tension_minima_arranque_v=3.5,
            corriente_maxima_salida_a=3.0,
            eficiencia=0.90,
        ),
        inversor=InversorAc(tension_salida_rms_v=110.0, frecuencia_hz=60.0, potencia_nominal_w=150.0, eficiencia=0.90),
    )


@dataclass(frozen=True)
class EscenarioDeAnalisis:
    """Condiciones de operación usadas en gráficas, reportes y tabla de ensayos."""

    rpm_forma_de_onda: float = 300
    rpm_analisis_carga: float = 400
    rpm_ensayos: tuple[float, ...] = (150, 300, 600, 1000)
    rpm_minima: float = 50
    rpm_maxima: float = 1200
    rpm_giro_manual: tuple[float, float] = (100, 400)
    carga_minima_ohm: float = 0.5
    carga_maxima_ohm: float = 60
    distancia_maxima_campo_m: float = 0.020
    rpm_microred: float = 600
    potencia_carga_ac_w: float = 15
    potencias_carga_ac_w: tuple[float, ...] = (0, 5, 15)
    duracion_balance_bateria_h: float = 6
    tensiones_inversor_v: tuple[float, ...] = (110, 220)


ESCENARIO_POR_DEFECTO = EscenarioDeAnalisis()
