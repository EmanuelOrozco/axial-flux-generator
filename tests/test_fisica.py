import math

import numpy as np
import pytest

from generador_axial.dominio import ImanPermanente, Rectificador
from generador_axial.dominio import fisica

IMAN = ImanPermanente(grado="N38", remanencia_t=1.25, diametro_m=0.020, espesor_m=0.005)


def test_campo_en_la_cara_del_iman():
    esperado = IMAN.remanencia_t / 2 * IMAN.espesor_m / math.hypot(IMAN.espesor_m, IMAN.radio_m)
    assert fisica.campo_axial(IMAN, 0.0) == pytest.approx(esperado)


def test_campo_lejano_tiende_al_de_un_dipolo():
    z = 1.0
    distancia_al_centro = z + IMAN.espesor_m / 2
    dipolo = IMAN.remanencia_t * IMAN.radio_m**2 * IMAN.espesor_m / (2 * distancia_al_centro**3)
    assert fisica.campo_axial(IMAN, z) == pytest.approx(dipolo, rel=1e-3)


def test_campo_decrece_monotonamente():
    campo = fisica.campo_axial(IMAN, np.linspace(0, 0.05, 200))
    assert np.all(np.diff(campo) < 0)


def test_campo_medio_coincide_con_integral_numerica():
    z0, h = 0.0025, 0.006
    z = np.linspace(z0, z0 + h, 20001)
    numerico = np.trapezoid(fisica.campo_axial(IMAN, z), z) / h
    assert fisica.campo_medio_en_tramo(IMAN, z0, h) == pytest.approx(numerico, rel=1e-8)


def test_campo_medio_con_tramo_muy_corto_tiende_al_valor_puntual():
    assert fisica.campo_medio_en_tramo(IMAN, 0.003, 1e-7) == pytest.approx(fisica.campo_axial(IMAN, 0.003), rel=1e-5)


def test_frecuencia_electrica_y_velocidades():
    assert fisica.frecuencia_electrica(300, 8) == pytest.approx(20.0)
    assert fisica.velocidad_angular_mecanica(60) == pytest.approx(2 * math.pi)
    assert fisica.velocidad_angular_electrica(60, 8) == pytest.approx(4 * 2 * math.pi)


def test_rectificador_no_entrega_tension_negativa():
    puente = Rectificador(caida_por_diodo_v=0.3, capacitancia_filtro_f=220e-6, tension_nominal_condensador_v=50)
    assert puente.caida_total_v == pytest.approx(0.6)
    np.testing.assert_allclose(fisica.tension_rectificada([0.2, 5.0], puente), [0.0, 4.4])


def test_rizado_de_onda_completa():
    assert fisica.rizado_pico_a_pico(0.01, 50, 100e-6) == pytest.approx(1.0)
