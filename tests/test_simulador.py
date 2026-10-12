import numpy as np
import pytest

from generador_axial.dominio import ErrorDeDiseno


def test_fem_es_menos_n_por_la_derivada_del_flujo(simulador, diseno):
    onda = simulador.forma_de_onda(300, ciclos=2, muestras=20001)
    derivada = np.gradient(onda.flujo_por_espira_wb, onda.tiempo_s)
    fem_numerica = -diseno.estator.espiras_totales * derivada
    np.testing.assert_allclose(fem_numerica[1:-1], onda.fem_v[1:-1], atol=1e-3)


def test_tension_es_proporcional_a_la_velocidad(simulador):
    punto = simulador.punto_de_operacion([100, 200, 400])
    np.testing.assert_allclose(punto.tension_pico_v / punto.rpm, punto.tension_pico_v[0] / 100)
    np.testing.assert_allclose(punto.tension_rms_v, punto.tension_pico_v / np.sqrt(2))


def test_maxima_potencia_ocurre_con_carga_igual_a_resistencia_interna(simulador):
    cargas = np.linspace(0.5, 60, 20001)
    operacion = simulador.operar_con_carga(400, cargas)
    carga_optima = cargas[np.argmax(operacion.potencia_carga_w)]
    assert carga_optima == pytest.approx(simulador.resistencia_interna_ohm, abs=0.01)


def test_balance_de_energia_y_par_de_lenz(simulador):
    operacion = simulador.operar_con_carga_adaptada(400)
    omega_m = float(simulador.punto_de_operacion(400).velocidad_angular_mecanica)
    total = operacion.potencia_carga_w + operacion.potencia_perdidas_cobre_w
    assert operacion.potencia_mecanica_w == pytest.approx(total)
    assert operacion.par_resistente_nm * omega_m == pytest.approx(operacion.potencia_mecanica_w)
    assert operacion.eficiencia == pytest.approx(0.5)


def test_sin_giro_no_hay_par_ni_tension(simulador):
    operacion = simulador.operar_con_carga(0, 10)
    assert operacion.par_resistente_nm == 0
    assert operacion.potencia_carga_w == 0


def test_velocidades_invalidas(simulador):
    with pytest.raises(ErrorDeDiseno):
        simulador.punto_de_operacion(-10)
    with pytest.raises(ErrorDeDiseno):
        simulador.forma_de_onda(0)
