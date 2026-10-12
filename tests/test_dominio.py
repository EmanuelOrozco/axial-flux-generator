import math
from dataclasses import replace

import pytest

from generador_axial.dominio import ErrorDeDiseno, GeometriaMecanica, Rotor


def test_resistencia_interna_calculada_a_mano(diseno):
    bobina = diseno.estator.bobina
    longitud_media = math.pi * (0.012 + 0.028) / 2
    area = math.pi * (0.000404 / 2) ** 2
    esperado = 8 * 1.72e-8 * 180 * longitud_media / area
    assert diseno.estator.resistencia_interna_ohm == pytest.approx(esperado)
    assert bobina.longitud_media_espira_m == pytest.approx(0.0628, abs=1e-4)


def test_ocupacion_de_la_ventana_es_fabricable(diseno):
    assert 0 < diseno.estator.bobina.factor_ocupacion < 0.85


def test_polos_impares_son_invalidos(diseno):
    with pytest.raises(ErrorDeDiseno):
        Rotor(numero_polos=7, radio_montaje_m=0.04, iman=diseno.rotor.iman)


def test_imanes_solapados_son_invalidos(diseno):
    with pytest.raises(ErrorDeDiseno):
        Rotor(numero_polos=16, radio_montaje_m=0.04, iman=diseno.rotor.iman)


def test_bobina_con_demasiadas_espiras_es_invalida(diseno):
    with pytest.raises(ErrorDeDiseno):
        replace(diseno.estator.bobina, espiras=2000)


@pytest.mark.parametrize("cambio", [{"entrehierro_m": 0}, {"factor_acoplamiento": 1.2}])
def test_parametros_globales_invalidos(diseno, cambio):
    with pytest.raises(ErrorDeDiseno):
        replace(diseno, **cambio)


def test_bobinas_distintas_a_polos_rompe_el_modelo_monofasico(diseno):
    with pytest.raises(ErrorDeDiseno):
        replace(diseno, estator=replace(diseno.estator, numero_bobinas=6))


def test_salida_dc_es_segura_en_todo_el_rango(diseno, simulador, escenario):
    tension_maxima = float(simulador.punto_de_operacion(escenario.rpm_maxima).tension_dc_v)
    led = diseno.indicador
    assert tension_maxima < 0.8 * diseno.rectificador.tension_nominal_condensador_v
    assert led.potencia_resistencia_w(tension_maxima) < led.potencia_nominal_resistencia_w
    assert led.corriente_a(tension_maxima) < led.corriente_maxima_led_a


def test_disco_rotor_demasiado_pequeno_es_invalido(diseno):
    with pytest.raises(ErrorDeDiseno):
        replace(diseno, mecanica=GeometriaMecanica(diametro_disco_rotor_m=0.09))
