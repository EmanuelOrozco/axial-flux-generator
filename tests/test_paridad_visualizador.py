"""El visualizador web debe usar los mismos parámetros y ecuaciones que el paquete Python."""

import json
import math
import re
import shutil
import subprocess
from dataclasses import asdict, fields

import pytest

from generador_axial import rutas
from generador_axial.aplicacion.simulacion_dinamica import EntradasDinamicas, InstanteDinamico, SimulacionDinamica
from generador_axial.dominio.realista import ParametrosRealistas

JS = rutas.RAIZ_PROYECTO / "visualizador_3d" / "js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js no está instalado")


def ejecutar_node(codigo: str) -> dict:
    salida = subprocess.run(["node", "-e", codigo], check=True, capture_output=True, text=True, cwd=JS)
    return json.loads(salida.stdout)


def test_configuracion_identica(diseno):
    config = ejecutar_node("console.log(JSON.stringify(require('./config.js')))")
    bobina, iman = diseno.estator.bobina, diseno.rotor.iman
    assert config["iman"]["remanenciaT"] == iman.remanencia_t
    assert config["iman"]["diametroMm"] == pytest.approx(iman.diametro_m * 1e3)
    assert config["iman"]["espesorMm"] == pytest.approx(iman.espesor_m * 1e3)
    assert config["rotor"]["numeroPolos"] == diseno.rotor.numero_polos
    assert config["rotor"]["radioMontajeMm"] == pytest.approx(diseno.rotor.radio_montaje_m * 1e3)
    assert config["rotor"]["diametroDiscoMm"] == pytest.approx(diseno.mecanica.diametro_disco_rotor_m * 1e3)
    assert config["estator"]["espirasPorBobina"] == bobina.espiras
    assert config["estator"]["alturaBobinaMm"] == pytest.approx(bobina.altura_m * 1e3)
    assert config["estator"]["diametroExteriorMm"] == pytest.approx(bobina.diametro_exterior_m * 1e3)
    assert config["entrehierroMm"] == pytest.approx(diseno.entrehierro_m * 1e3)
    assert config["factorAcoplamiento"] == diseno.factor_acoplamiento
    assert config["caidaPuenteV"] == pytest.approx(diseno.rectificador.caida_total_v)
    assert config["rectificador"]["tensionNominalCondensadorV"] == diseno.rectificador.tension_nominal_condensador_v
    led = diseno.indicador
    assert config["indicador"] == {
        "resistenciaOhm": led.resistencia_ohm,
        "potenciaNominalResistenciaW": led.potencia_nominal_resistencia_w,
        "caidaLedV": led.caida_led_v,
        "corrienteMaximaLedA": led.corriente_maxima_led_a,
    }


def test_configuracion_microred_identica(diseno):
    config = ejecutar_node("console.log(JSON.stringify(require('./config.js')))")
    bateria, controlador, inversor = diseno.bateria, diseno.controlador_carga, diseno.inversor
    assert config["bateria"] == {
        "tensionNominalV": bateria.tension_nominal_v,
        "capacidadAh": bateria.capacidad_ah,
        "resistenciaInternaOhm": bateria.resistencia_interna_ohm,
        "tensionMinimaV": bateria.tension_minima_v,
        "tensionMaximaV": bateria.tension_maxima_v,
        "socInicial": bateria.soc_inicial,
        "socMinimoDescarga": bateria.soc_minimo_descarga,
        "histeresisReconexionSoc": bateria.histeresis_reconexion_soc,
    }
    assert config["controladorCarga"] == {
        "tensionMinimaArranqueV": controlador.tension_minima_arranque_v,
        "tensionAbsorcionV": controlador.tension_corte_absorcion_v,
        "tensionFlotacionV": controlador.tension_flotacion_v,
        "corrienteMaximaA": controlador.corriente_maxima_salida_a,
        "eficiencia": controlador.eficiencia,
    }
    assert config["inversor"] == {
        "tensionRmsV": inversor.tension_salida_rms_v,
        "frecuenciaHz": inversor.frecuencia_hz,
        "potenciaNominalW": inversor.potencia_nominal_w,
        "eficiencia": inversor.eficiencia,
    }


@pytest.mark.parametrize("rpm", [100, 300, 1200])
@pytest.mark.parametrize("soc", [0.0, 0.5, 1.0])
def test_corriente_de_carga_identica(simulador, rpm, soc):
    resultado = ejecutar_node(
        "const c = require('./config.js');"
        "const m = require('./modelo/fisica.js').crearModelo(c);"
        f"console.log(JSON.stringify(m.calcular({{rpm: {rpm}, entrehierroMm: c.entrehierroMm,"
        f" espirasPorBobina: c.estator.espirasPorBobina, remanenciaT: c.iman.remanenciaT, socBateria: {soc}}})));"
    )
    esperado = float(simulador.corriente_carga_bateria_a(rpm, soc))
    assert resultado["corrienteCargaA"] == pytest.approx(esperado, rel=1e-12, abs=1e-15)


@pytest.mark.parametrize("rpm", [0, 300, 1000])
def test_resultados_identicos(simulador, diseno, rpm):
    resultado = ejecutar_node(
        "const c = require('./config.js');"
        "const m = require('./modelo/fisica.js').crearModelo(c);"
        f"console.log(JSON.stringify(m.calcular({{rpm: {rpm}, entrehierroMm: c.entrehierroMm,"
        " espirasPorBobina: c.estator.espirasPorBobina, remanenciaT: c.iman.remanenciaT})));"
    )
    punto = simulador.punto_de_operacion(rpm)
    assert resultado["campoMedioT"] == pytest.approx(simulador.campo_medio_bobina_t, rel=1e-12)
    assert resultado["flujoMaximoWb"] == pytest.approx(simulador.flujo_maximo_por_espira_wb, rel=1e-12)
    assert resultado["tensionPicoV"] == pytest.approx(float(punto.tension_pico_v), rel=1e-12, abs=1e-12)
    assert resultado["tensionDcV"] == pytest.approx(float(punto.tension_dc_v), rel=1e-12, abs=1e-12)
    assert resultado["resistenciaInternaOhm"] == pytest.approx(diseno.estator.resistencia_interna_ohm, rel=1e-12)
    assert resultado["ocupacion"] == pytest.approx(diseno.estator.bobina.factor_ocupacion, rel=1e-12)
    vdc = float(punto.tension_dc_v)
    assert resultado["corrienteLedA"] == pytest.approx(diseno.indicador.corriente_a(vdc), rel=1e-12, abs=1e-15)
    assert resultado["potenciaResistenciaLedW"] == pytest.approx(
        diseno.indicador.potencia_resistencia_w(vdc), rel=1e-12, abs=1e-15
    )
    assert resultado["salidaDcSegura"] is True


# ---------------------------------------------------------------- modelo realista
def camel(nombre: str) -> str:
    return re.sub(r"_([a-z0-9])", lambda m: m.group(1).upper(), nombre)


def a_camel(valor):
    if isinstance(valor, dict):
        return {camel(k): a_camel(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [a_camel(v) for v in valor]
    return valor


def test_parametros_realistas_identicos(diseno):
    config = ejecutar_node("console.log(JSON.stringify(require('./config.js')))")
    assert config["realista"] == a_camel(asdict(ParametrosRealistas()))
    assert config["mecanica"]["diametroEjeMm"] == pytest.approx(diseno.mecanica.diametro_eje_m * 1e3)
    assert config["mecanica"]["holguraAjusteMm"] == pytest.approx(diseno.mecanica.holgura_ajuste_m * 1e3)
    assert config["rectificador"]["capacitanciaFiltroUf"] == pytest.approx(diseno.rectificador.capacitancia_filtro_f * 1e6)
    assert config["estator"]["diametroDiscoMm"] == pytest.approx(diseno.mecanica.diametro_disco_estator_m * 1e3)


def test_perfil_de_flujo_e_inercia_identicos(diseno):
    sim = SimulacionDinamica(diseno)
    js = ejecutar_node(
        "const c = require('./config.js'); const D = require('./modelo/dinamica.js');"
        "const s = new D.SimulacionDinamica(c);"
        "console.log(JSON.stringify({flujo: s.perfil.flujo, derivada: s.perfil.derivada, j: s.momentoInercia}));"
    )
    assert js["flujo"] == pytest.approx(list(sim.perfil.flujo), rel=1e-12, abs=1e-15)
    assert js["derivada"] == pytest.approx(list(sim.perfil.derivada), rel=1e-12, abs=1e-15)
    assert js["j"] == pytest.approx(sim.momento_inercia, rel=1e-12)


# Guion de entradas: (paso desde el que rige, cambios). Recorre arranque, carga, frenado,
# calentamiento, cambio de condensador y de geometría.
GUION = {
    "arranque_y_carga": (
        {"soc": 0.5},
        [
            (0, {}),
            (30, {"par_motriz_nm": 0.2}),
            (50, {"potencia_carga_ac_w": 40.0}),
            (60, {"factor_tiempo": 500.0}),
            (70, {"temperatura_ambiente_c": 40.0}),
            (80, {"par_motriz_nm": 0.0}),
            (90, {"capacitancia_filtro_f": 2200e-6, "par_motriz_nm": 0.12}),
            (100, {"espiras_por_bobina": 230, "entrehierro_m": 0.0015, "remanencia_t": 1.4}),
            (110, {"inversor_encendido": False}),
        ],
    ),
    "absorcion": (
        {"soc": 0.97},
        [(0, {"par_motriz_nm": 0.3, "inversor_encendido": False, "factor_tiempo": 500.0})],
    ),
    "flotacion": (
        {"soc": 0.996},
        [(0, {"par_motriz_nm": 0.3, "inversor_encendido": False}), (60, {"inversor_encendido": True})],
    ),
    "corte_por_baja_tension": (
        {"soc": 0.03},
        [(0, {"par_motriz_nm": 0.0, "potencia_carga_ac_w": 40.0}), (40, {"par_motriz_nm": 0.3, "factor_tiempo": 500.0})],
    ),
}
PASOS, DT = 120, 0.05
CAMPOS_JS = {f.name: camel(f.name) for f in fields(InstanteDinamico)}


def entradas_del_guion(sim: SimulacionDinamica, guion, paso: int) -> EntradasDinamicas:
    cambios = {}
    for desde, valores in guion:
        if paso >= desde:
            cambios.update(valores)
    return sim.con_entradas(**cambios)


def a_entradas_js(e: EntradasDinamicas) -> dict:
    return {
        "parMotrizNm": e.par_motriz_nm, "potenciaCargaAcW": e.potencia_carga_ac_w,
        "inversorEncendido": e.inversor_encendido, "temperaturaAmbienteC": e.temperatura_ambiente_c,
        "factorTiempo": e.factor_tiempo, "entrehierroMm": e.entrehierro_m * 1e3,
        "espirasPorBobina": e.espiras_por_bobina, "remanenciaT": e.remanencia_t,
        "capacitanciaFiltroUf": e.capacitancia_filtro_f * 1e6,
    }


@pytest.mark.parametrize("nombre", list(GUION))
def test_simulacion_dinamica_identica_paso_a_paso(diseno, nombre):
    inicial, guion = GUION[nombre]
    sim = SimulacionDinamica(diseno)
    sim.soc = inicial["soc"]
    entradas = [entradas_del_guion(sim, guion, k) for k in range(PASOS)]
    esperado = [sim.avanzar(DT, e) for e in entradas]

    js = ejecutar_node(
        "const c = require('./config.js'); const D = require('./modelo/dinamica.js');"
        f"const s = new D.SimulacionDinamica(c); s.soc = {inicial['soc']};"
        f"const entradas = {json.dumps([a_entradas_js(e) for e in entradas])};"
        f"console.log(JSON.stringify(entradas.map(e => s.avanzar({DT}, e))));"
    )
    for k, (python, node) in enumerate(zip(esperado, js)):
        for campo, clave in CAMPOS_JS.items():
            valor = getattr(python, campo)
            if isinstance(valor, (bool, str)):
                assert node[clave] == valor, f"paso {k}, {campo}"
            else:
                assert node[clave] == pytest.approx(valor, rel=1e-9, abs=1e-12), f"paso {k}, {campo}"
    assert not math.isnan(esperado[-1].soc)
