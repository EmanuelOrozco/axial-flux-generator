"""Pruebas de la microrred: carga de batería, inversor de 110/220 V y balance de potencias."""

import math

import numpy as np
import pytest

from generador_axial.dominio import Bateria, ControladorCarga, ErrorDeDiseno, InversorAc
from generador_axial.dominio import fisica


def test_bateria_curva_de_tension_en_vacio_y_energia():
    bateria = Bateria(tension_nominal_v=12.0, capacidad_ah=7.0, tension_minima_v=11.8, tension_maxima_v=12.8)
    assert bateria.energia_almacenada_wh == pytest.approx(84.0)
    assert bateria.tension_circuito_abierto_v(0.0) == pytest.approx(11.8)
    assert bateria.tension_circuito_abierto_v(1.0) == pytest.approx(12.8)
    assert bateria.tension_circuito_abierto_v(0.5) == pytest.approx(12.3)
    assert bateria.energia_utilizable_wh(0.5) == pytest.approx((0.5 - bateria.soc_minimo_descarga) * 84.0)


@pytest.mark.parametrize(
    "cambios",
    [{"soc_inicial": 1.5}, {"tension_maxima_v": 10.0, "tension_minima_v": 11.0}, {"soc_minimo_descarga": 1.0}],
)
def test_bateria_validaciones(cambios):
    with pytest.raises(ErrorDeDiseno):
        Bateria(**cambios)


def test_controlador_flotacion_no_supera_absorcion():
    with pytest.raises(ErrorDeDiseno):
        ControladorCarga(tension_corte_absorcion_v=13.8, tension_flotacion_v=14.4)


def test_potencia_extraible_usa_la_fem_eficaz():
    assert fisica.potencia_maxima_extraible(10.0, 12.5) == pytest.approx(10.0**2 / (4 * 12.5))


def test_corriente_de_carga_mppt_y_limites():
    bateria, controlador = Bateria(), ControladorCarga(tension_minima_arranque_v=3.5)
    v_oc = bateria.tension_circuito_abierto_v(0.5)

    assert fisica.corriente_carga_bateria(2.0, 1.4, 12.0, bateria, 0.5, controlador) == pytest.approx(0.0)
    esperado = controlador.eficiencia * 10.0**2 / (4 * 12.0) / v_oc
    assert fisica.corriente_carga_bateria(14.0, 10.0, 12.0, bateria, 0.5, controlador) == pytest.approx(esperado)
    assert fisica.corriente_carga_bateria(500.0, 300.0, 12.0, bateria, 0.5, controlador) == pytest.approx(
        controlador.corriente_maxima_salida_a
    )
    assert fisica.corriente_carga_bateria(14.0, 10.0, 12.0, bateria, 1.0, controlador) == pytest.approx(0.0)


def test_inversor_110v_y_220v():
    inversor = InversorAc(tension_salida_rms_v=110.0, eficiencia=0.90)
    assert inversor.tension_pico_v == pytest.approx(110.0 * math.sqrt(2))
    assert InversorAc(tension_salida_rms_v=220.0).tension_pico_v == pytest.approx(220.0 * math.sqrt(2))
    assert inversor.corriente_primario_bateria_a(15.0, 12.0) == pytest.approx(15.0 / 0.90 / 12.0)
    assert fisica.corriente_salida_inversor(110.0, 110.0) == pytest.approx(1.0)


def test_inversor_rechaza_cargas_fuera_de_rango():
    inversor = InversorAc(potencia_nominal_w=150.0)
    with pytest.raises(ErrorDeDiseno):
        inversor.potencia_entrada_w(200.0)
    with pytest.raises(ErrorDeDiseno):
        inversor.potencia_entrada_w(-1.0)


def test_forma_de_onda_inversor(simulador):
    por_defecto = simulador.forma_de_onda_inversor(potencia_carga_w=15.0)
    assert por_defecto.tension_rms_v == simulador.inversor.tension_salida_rms_v
    assert np.max(por_defecto.tension_ac_v) == pytest.approx(simulador.inversor.tension_pico_v, rel=1e-3)
    assert por_defecto.corriente_rms_a == pytest.approx(15.0 / por_defecto.tension_rms_v)

    salida220 = simulador.forma_de_onda_inversor(tension_rms_v=220.0, frecuencia_hz=50.0)
    assert np.max(salida220.tension_ac_v) == pytest.approx(220.0 * math.sqrt(2), rel=1e-3)


def test_balance_conserva_la_energia(simulador):
    balance = simulador.balance_microred(rpm=600, potencia_carga_ac_w=15.0, soc=0.5)
    eficiencia = simulador.controlador_carga.eficiencia
    assert balance.potencia_hacia_bateria_w == pytest.approx(eficiencia * balance.potencia_generador_w)
    assert balance.potencia_mecanica_w == pytest.approx(balance.potencia_generador_w + balance.potencia_perdidas_cobre_w)
    assert balance.potencia_neta_bateria_w == pytest.approx(
        balance.potencia_hacia_bateria_w - balance.potencia_entrada_inversor_w
    )
    assert balance.potencia_neta_bateria_w < 0
    assert balance.autonomia_h == pytest.approx(
        simulador.bateria.energia_utilizable_wh(0.5) / -balance.potencia_neta_bateria_w
    )


def test_balance_con_carga_adaptada_coincide_con_maxima_transferencia(simulador):
    balance = simulador.balance_microred(rpm=600)
    adaptada = simulador.operar_con_carga_adaptada(600)
    assert balance.potencia_generador_w == pytest.approx(float(adaptada.potencia_carga_w))
    assert balance.potencia_perdidas_cobre_w == pytest.approx(float(adaptada.potencia_perdidas_cobre_w))


def test_generador_detenido_solo_descarga(simulador):
    balance = simulador.balance_microred(rpm=0, potencia_carga_ac_w=15.0)
    assert balance.potencia_generador_w == 0.0
    assert balance.par_resistente_nm == 0.0
    assert balance.potencia_neta_bateria_w == pytest.approx(-simulador.inversor.potencia_entrada_w(15.0))


def test_rpm_de_equilibrio_anula_el_balance(simulador):
    rpm = simulador.rpm_de_equilibrio(5.0)
    assert simulador.balance_microred(rpm, 5.0).potencia_neta_bateria_w == pytest.approx(0.0, abs=1e-9)
    assert simulador.rpm_de_equilibrio(0.0) == 0.0
    assert math.isinf(simulador.rpm_de_equilibrio(40.0))


def test_solo_carga_aumenta_el_soc(simulador):
    evolucion = simulador.simular_bateria(rpm=600, duracion_h=0.5, soc_inicial=0.2)
    assert np.all(np.diff(evolucion.soc) > 0)
    assert np.all(evolucion.corriente_descarga_a == 0.0)


def test_corte_por_baja_carga_con_histeresis(simulador):
    bateria = simulador.bateria
    evolucion = simulador.simular_bateria(rpm=600, potencia_carga_ac_w=15.0, duracion_h=6, paso_s=60, soc_inicial=0.5)
    assert evolucion.soc.min() >= bateria.soc_minimo_descarga - 0.01
    assert not evolucion.inversor_activo.all()
    reconexiones = np.flatnonzero(np.diff(evolucion.inversor_activo.astype(int)) == 1)
    for indice in reconexiones:
        assert evolucion.soc[indice + 1] >= bateria.soc_minimo_descarga + bateria.histeresis_reconexion_soc
