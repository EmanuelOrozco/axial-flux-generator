"""Pruebas del modelo realista: geometría del flujo, circuito, batería, inversor y dinámica temporal."""

import math

import pytest

from generador_axial.aplicacion.simulacion_dinamica import SimulacionDinamica
from generador_axial.dominio import ErrorDeDiseno
from generador_axial.dominio import dinamica as dn
from generador_axial.dominio.realista import BateriaPlomoAcido, FuenteMotriz, InversorReal, ParametrosRealistas


@pytest.fixture
def sim(diseno):
    return SimulacionDinamica(diseno)


# ---------------------------------------------------------------- geometría del flujo
def test_area_de_la_lente_en_los_casos_limite():
    assert dn.area_lente(1.0, 2.0, 0.5) == pytest.approx(math.pi)
    assert dn.area_lente(1.0, 2.0, 3.0) == 0.0
    assert dn.area_lente(1.0, 1.0, 1.0) == pytest.approx(2 * math.pi / 3 - math.sqrt(3) / 2)


@pytest.mark.parametrize("d", [0.6, 1.2, 2.1, 2.8])
def test_la_cuerda_es_menos_la_derivada_del_area(d):
    h = 1e-6
    derivada = (dn.area_lente(1.0, 2.0, d + h) - dn.area_lente(1.0, 2.0, d - h)) / (2 * h)
    assert dn.cuerda_lente(1.0, 2.0, d) == pytest.approx(-derivada, rel=1e-6)


def test_flujo_maximo_es_la_fraccion_de_espiras_que_abarcan_el_iman(sim, diseno):
    """Con el imán centrado, una espira de radio ρ enlaza B·π·min(ρ, r_m)²."""
    bobina, r_m = diseno.estator.bobina, diseno.rotor.iman.radio_m
    r_i, r_e = bobina.diametro_interior_m / 2, bobina.diametro_exterior_m / 2
    exacto = ((r_m**3 - r_i**3) / 3 / r_m**2 + (r_e - r_m)) / (r_e - r_i)
    assert sim.perfil.flujo[0] == pytest.approx(exacto, rel=2e-3)
    # El factor de acoplamiento k = 0.85 del modelo ideal era una estimación de esta fracción.
    assert sim.perfil.flujo_maximo == pytest.approx(diseno.factor_acoplamiento, abs=0.03)


def test_la_derivada_del_perfil_integra_al_flujo(sim):
    perfil = sim.perfil
    paso = 2 * math.pi / len(perfil.flujo)
    acumulado = perfil.flujo[0]
    for j in range(1, len(perfil.flujo)):
        acumulado += 0.5 * (perfil.derivada[j - 1] + perfil.derivada[j]) * paso
        assert acumulado == pytest.approx(perfil.flujo[j], abs=0.01)


def test_onda_alterna_simetrica_y_no_senoidal(sim):
    perfil = sim.perfil
    n = len(perfil.flujo)
    for j in range(n // 2):
        assert perfil.flujo[j + n // 2] == pytest.approx(-perfil.flujo[j], abs=1e-12)
    assert perfil.factor_cresta < math.sqrt(2)  # onda más aplanada (trapezoidal) que una senoide
    assert perfil.derivada_en(0.0) == pytest.approx(perfil.derivada[0])
    assert perfil.derivada_en(2 * math.pi) == pytest.approx(perfil.derivada[0])


# ---------------------------------------------------------------- parámetros derivados
def test_inductancia_de_wheeler(diseno):
    b = diseno.estator.bobina
    radio, profundidad = (b.diametro_interior_m + b.diametro_exterior_m) / 4, (b.diametro_exterior_m - b.diametro_interior_m) / 2
    pulgadas = 39.37
    clasica_uh = 0.8 * (radio * pulgadas) ** 2 * b.espiras**2 / (
        6 * radio * pulgadas + 9 * b.altura_m * pulgadas + 10 * profundidad * pulgadas
    )
    assert dn.inductancia_bobina_h(b.espiras, radio, b.altura_m, profundidad) == pytest.approx(clasica_uh * 1e-6, rel=5e-3)


def test_momento_de_inercia_dominado_por_los_imanes(sim, diseno):
    iman = diseno.rotor.iman
    masa_iman = 7500 * iman.area_cara_m2 * iman.espesor_m
    j_imanes = diseno.rotor.numero_polos * masa_iman * (iman.radio_m**2 / 2 + diseno.rotor.radio_montaje_m**2)
    assert 2e-4 < sim.momento_inercia < 3e-4
    assert j_imanes / sim.momento_inercia > 0.5


# ---------------------------------------------------------------- rectificador y MPPT
def test_potencia_dc_sin_reactancia_es_el_thevenin_menos_los_diodos():
    e, r, caida, i = 8.0, 12.0, 0.6, 0.25
    esperado = e * i - r * i**2 - caida * dn.FACTOR_CORRIENTE_MEDIA * i
    assert dn.potencia_dc(e, r, 0.0, caida, i) == pytest.approx(esperado)


def test_la_biseccion_encuentra_el_punto_de_maxima_potencia():
    e, r, x, caida = 9.0, 12.4, 1.1, 0.6
    i_max = e / math.hypot(r, x)
    optimo = dn.biseccion(lambda i: dn.derivada_potencia_dc(e, r, x, caida, i), 0.0, i_max, 60)
    p_opt = dn.potencia_dc(e, r, x, caida, optimo)
    assert all(dn.potencia_dc(e, r, x, caida, i_max * k / 200) <= p_opt + 1e-12 for k in range(201))
    # Sin reactancia el óptimo es I = (E − k_d)/(2R).
    sin_x = dn.biseccion(lambda i: dn.derivada_potencia_dc(e, r, 0.0, caida, i), 0.0, e / r, 60)
    assert sin_x == pytest.approx((e - caida * dn.FACTOR_CORRIENTE_MEDIA) / (2 * r), rel=1e-9)


def test_tension_dc_con_rizado():
    assert dn.rizado_pico_a_pico(0.3, 30.0, 2200e-6) == pytest.approx(dn.FACTOR_CORRIENTE_MEDIA * 0.3 / (60 * 2200e-6))
    # Condensador grande: pico − diodos − rizado/2; condensador insuficiente: valor medio rectificado.
    assert dn.tension_dc_media(5.0, 1.4, 0.64, 0.6, 1.0) == pytest.approx(7.0 - 0.6 - 0.5)
    assert dn.tension_dc_media(5.0, 1.4, 0.64, 0.6, 20.0) == pytest.approx(7.0 * 0.64 - 0.6)


# ---------------------------------------------------------------- batería e inversor
def test_curva_de_reposo_y_eficiencia_coulombica():
    bat = BateriaPlomoAcido()
    assert dn.tension_reposo(bat, 0.0) == 10.5 and dn.tension_reposo(bat, 1.0) == 12.85
    assert dn.tension_reposo(bat, 0.5) == pytest.approx((12.10 + 12.35) / 2)
    assert dn.tension_reposo(bat, -1) == 10.5 and dn.tension_reposo(bat, 2) == 12.85
    assert dn.eficiencia_coulomb(bat, 0.5) == bat.eficiencia_coulomb
    assert dn.eficiencia_coulomb(bat, 1.0) == pytest.approx(bat.eficiencia_coulomb_llena)


def test_efecto_peukert():
    bat = BateriaPlomoAcido()
    nominal = 7.0 / bat.horas_regimen_nominal
    assert dn.corriente_efectiva_peukert(bat, 7.0, nominal) == pytest.approx(nominal)
    assert dn.corriente_efectiva_peukert(bat, 7.0, 4 * nominal) > 4 * nominal
    assert dn.corriente_efectiva_peukert(bat, 7.0, 0.0) == 0.0


@pytest.mark.parametrize("potencia", [-40.0, -1.0, 0.0, 2.5])
def test_corriente_para_una_potencia_en_bornes(potencia):
    i = dn.corriente_para_potencia(12.2, 0.025, potencia)
    assert i * (12.2 + 0.025 * i) == pytest.approx(potencia, abs=1e-9)


def test_inversor_con_consumo_en_vacio(diseno):
    inv = diseno.inversor
    assert dn.potencia_entrada_inversor(0.0, inv.potencia_nominal_w, inv.eficiencia, 3.6) == pytest.approx(3.6)
    nominal = dn.potencia_entrada_inversor(inv.potencia_nominal_w, inv.potencia_nominal_w, inv.eficiencia, 3.6)
    assert inv.potencia_nominal_w / nominal == pytest.approx(inv.eficiencia)
    assert 15 / dn.potencia_entrada_inversor(15, inv.potencia_nominal_w, inv.eficiencia, 3.6) < 0.82


@pytest.mark.parametrize(
    ("clase", "cambios"),
    [
        (BateriaPlomoAcido, {"curva_ocv": ((0.0, 12.0), (1.0, 11.0))}),
        (BateriaPlomoAcido, {"exponente_peukert": 0.9}),
        (InversorReal, {"tension_corte_v": 12.5}),
        (FuenteMotriz, {"par_inicial_nm": 1.0}),
    ],
)
def test_validaciones(clase, cambios):
    with pytest.raises(ErrorDeDiseno):
        clase(**cambios)


# ---------------------------------------------------------------- dinámica
def test_sin_par_suficiente_el_rotor_no_arranca(sim):
    sim.simular(sim.con_entradas(par_motriz_nm=0.002), 2.0)
    assert sim.omega == 0.0


def test_regimen_permanente_equilibra_los_pares(sim):
    x = sim.simular(sim.con_entradas(par_motriz_nm=0.07), 6.0)[-1]
    assert x.par_motriz_nm == pytest.approx(x.par_electromagnetico_nm + x.par_rozamiento_nm, rel=1e-4)
    assert x.frecuencia_hz == pytest.approx(sim.diseno.rotor.numero_polos * x.rpm / 120)
    assert 300 < x.rpm < 700


def test_conservacion_de_la_energia(sim):
    x = sim.simular(sim.con_entradas(par_motriz_nm=0.12), 4.0)[-1]
    assert x.potencia_electromagnetica_w == pytest.approx(x.perdidas_cobre_w + x.perdidas_diodos_w + x.potencia_dc_w)
    assert x.potencia_hacia_bateria_w == pytest.approx(sim.diseno.controlador_carga.eficiencia * x.potencia_dc_w)
    entrada = x.potencia_eje_w
    salidas = x.potencia_electromagnetica_w + x.perdidas_foucault_w + x.perdidas_rozamiento_w
    assert entrada == pytest.approx(salidas, rel=1e-3)
    assert x.potencia_hacia_bateria_w < x.potencia_eje_w


def test_sin_par_motriz_el_rotor_se_detiene(sim):
    sim.simular(sim.con_entradas(par_motriz_nm=0.1), 3.0)
    serie = sim.simular(sim.con_entradas(par_motriz_nm=0.0), 6.0)
    rpm = [x.rpm for x in serie]
    assert all(b <= a for a, b in zip(rpm, rpm[1:]))
    assert rpm[-1] == 0.0


def test_mas_carga_electrica_frena_mas(sim, diseno):
    """Ley de Lenz: con el controlador cargando, el mismo par mueve el rotor más despacio."""
    a = SimulacionDinamica(diseno)
    cargando = a.simular(a.con_entradas(par_motriz_nm=0.08), 5.0)[-1]
    b = SimulacionDinamica(diseno)
    b.soc = 1.0  # batería llena: el controlador solo mantiene la flotación
    b.inversor_habilitado = False
    llena = b.simular(b.con_entradas(par_motriz_nm=0.08, inversor_encendido=False), 5.0)[-1]
    assert cargando.par_electromagnetico_nm > llena.par_electromagnetico_nm
    assert llena.rpm > cargando.rpm


def test_condensador_pequeno_limita_la_tension_del_bus(sim):
    pequeno = sim.simular(sim.con_entradas(par_motriz_nm=0.1), 3.0)[-1]
    grande = sim.instantanea(sim.con_entradas(par_motriz_nm=0.1, capacitancia_filtro_f=4700e-6))
    assert pequeno.rizado_v > 5 * grande.rizado_v
    assert grande.tension_dc_v > pequeno.tension_dc_v


def test_corte_por_baja_tension_con_histeresis(sim):
    sim.soc = 0.02
    sim.avanzar(0.05, sim.con_entradas(par_motriz_nm=0.0, potencia_carga_ac_w=40.0))
    assert sim.inversor_habilitado is False
    x = sim.instantanea(sim.con_entradas(par_motriz_nm=0.0, potencia_carga_ac_w=40.0))
    assert x.corte_baja_tension and not x.inversor_activo and x.potencia_ac_w == 0
    sim.soc = 0.45  # por encima del corte pero bajo la reconexión (12.3 V): sigue desconectado
    sim.avanzar(0.05, sim.con_entradas(par_motriz_nm=0.0, potencia_carga_ac_w=40.0))
    assert sim.inversor_habilitado is False
    sim.soc = 0.7
    sim.avanzar(0.05, sim.con_entradas(par_motriz_nm=0.0, potencia_carga_ac_w=40.0))
    assert sim.inversor_habilitado is True


def test_la_absorcion_limita_la_tension_de_carga(sim):
    """Cerca de la carga completa el sobrepotencial de gasificación lleva los bornes a 14.4 V."""
    sim.soc = 0.97
    serie = sim.simular(sim.con_entradas(par_motriz_nm=0.3, inversor_encendido=False), 4.0)
    x = serie[-1]
    assert x.etapa_carga == "absorción"
    assert x.tension_bateria_v == pytest.approx(sim.diseno.controlador_carga.tension_corte_absorcion_v, abs=1e-6)
    assert x.corriente_carga_a < serie[20].corriente_carga_a  # la corriente decae durante la absorción


def test_flotacion_con_bateria_llena(sim):
    sim.soc = 1.0
    x = sim.simular(sim.con_entradas(par_motriz_nm=0.3, inversor_encendido=False), 6.0)[-1]
    assert x.etapa_carga == "flotación"
    assert x.tension_bateria_v == pytest.approx(sim.diseno.controlador_carga.tension_flotacion_v, abs=1e-6)
    assert 0 < x.corriente_neta_a < 0.05


def test_calentamiento_de_las_bobinas(sim):
    termico = sim.p.termico
    serie = sim.simular(sim.con_entradas(par_motriz_nm=0.2, factor_tiempo=500.0), 15.0)
    x = serie[-1]
    conductancia = (termico.conveccion_natural_w_m2k + termico.conveccion_forzada_w_m2k_por_rad_s * x.rpm * math.pi / 30) * (
        2 * math.pi * (sim.diseno.mecanica.diametro_disco_estator_m / 2) ** 2
    )
    estacionaria = termico.temperatura_ambiente_c + (x.perdidas_cobre_w + x.perdidas_foucault_w) / conductancia
    assert x.temperatura_bobinas_c == pytest.approx(estacionaria, abs=0.05)
    assert x.resistencia_ohm > serie[0].resistencia_ohm  # R(T) = R20·(1 + α·ΔT)


def test_la_temperatura_ambiente_debilita_los_imanes(sim):
    frio = sim.instantanea(sim.con_entradas(temperatura_ambiente_c=0.0))
    calor = sim.instantanea(sim.con_entradas(temperatura_ambiente_c=45.0))
    assert calor.remanencia_efectiva_t / frio.remanencia_efectiva_t == pytest.approx((1 - 0.0012 * 25) / (1 + 0.0012 * 20))


def test_la_fem_real_frente_al_modelo_ideal(sim, simulador):
    # A la temperatura de referencia (20 °C) la remanencia es la de catálogo, como en el modelo ideal.
    x = sim.simular(sim.con_entradas(par_motriz_nm=0.07, temperatura_ambiente_c=20.0), 3.0)[-1]
    ideal = simulador.punto_de_operacion(x.rpm)
    k = sim.diseno.factor_acoplamiento
    assert x.fem_pico_v / float(ideal.tension_pico_v) == pytest.approx(sim.perfil.pico_derivada / k, rel=1e-9)
    assert x.fem_rms_v / float(ideal.tension_rms_v) == pytest.approx(sim.perfil.rms_derivada * math.sqrt(2) / k, rel=1e-9)


def test_sobrepotencial_de_gasificacion():
    bat = ParametrosRealistas().bateria
    assert dn.resistencia_polarizacion(bat, 0.5, -1.0) == bat.resistencia_polarizacion_ohm
    assert dn.resistencia_polarizacion(bat, 0.5, 0.2) == pytest.approx(bat.resistencia_polarizacion_ohm, rel=0.01)
    assert dn.resistencia_polarizacion(bat, 1.0, 0.2) == pytest.approx(
        bat.resistencia_polarizacion_ohm * (1 + bat.factor_sobrepotencial_carga)
    )
