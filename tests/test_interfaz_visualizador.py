"""Pruebas de extremo a extremo del visualizador 3D en un navegador real (Chromium + Playwright).

Cada control de la interfaz se acciona como lo haría un usuario y se comprueba que lo que muestra la
pantalla coincide con el modelo dinámico de referencia en Python (``SimulacionDinamica``) evaluado en
el mismo estado que tiene el navegador.

Están excluidas de ``uv run pytest`` por su duración. Ejecución (requiere el grupo ``e2e`` y Chromium):
    uv run --group e2e playwright install chromium
    uv run --group e2e pytest -m interfaz
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from generador_axial import diseno_por_defecto, rutas
from generador_axial.aplicacion import EntradasDinamicas, InstanteDinamico, SimulacionDinamica

sync_api = pytest.importorskip("playwright.sync_api")
pytestmark = pytest.mark.interfaz

INDEX = (rutas.RAIZ_PROYECTO / "visualizador_3d" / "index.html").as_uri()
ARGUMENTOS_WEBGL = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
TIEMPO_MAXIMO_MS = 20_000

ETAPAS = {
    "sin generación": "Sin generación",
    "mppt": "MPPT",
    "absorción": "Absorción 14.4 V",
    "flotación": "Flotación 13.8 V",
    "corriente máxima": "Límite 3 A",
}


# ---------------------------------------------------------------- infraestructura
@pytest.fixture(scope="module")
def navegador():
    with sync_api.sync_playwright() as playwright:
        try:
            navegador = playwright.chromium.launch(args=ARGUMENTOS_WEBGL)
        except sync_api.Error as error:
            pytest.skip(f"Chromium no está disponible para Playwright: {error}")
        yield navegador
        navegador.close()


class Interfaz:
    """Envoltorio de la página con las acciones de un usuario y lecturas del estado interno."""

    def __init__(self, pagina):
        self.pagina = pagina
        self.errores: list[str] = []
        pagina.on("pageerror", lambda e: self.errores.append(str(e)))
        pagina.on("console", lambda m: self.errores.append(m.text) if m.type == "error" else None)

    def abrir(self, consulta: str = "") -> "Interfaz":
        self.pagina.goto(INDEX + consulta)
        self.pagina.wait_for_function("window.GeneradorAxial && window.GeneradorAxial.aplicacion")
        self.pagina.wait_for_timeout(300)
        return self

    def js(self, expresion: str, argumento=None):
        return self.pagina.evaluate(expresion, argumento)

    def app(self, ruta: str):
        return self.js(f"() => window.GeneradorAxial.aplicacion.{ruta}")

    def texto(self, id_: str) -> str:
        return self.pagina.inner_text(f"#{id_}")

    def numero(self, id_: str) -> float:
        return float(self.texto(id_))

    def refrescar(self) -> None:
        """Fuerza un paso para que las vistas reflejen el último cambio (en pausa no avanza el tiempo)."""
        self.avanzar(0.05)

    def clic(self, selector: str) -> None:
        self.pagina.click(selector)
        self.refrescar()

    def mover_deslizador(self, id_: str, valor: float) -> None:
        self.js(
            """([id, valor]) => {
                const e = document.getElementById(id);
                e.value = valor;
                e.dispatchEvent(new Event('input', { bubbles: true }));
            }""",
            [id_, valor],
        )
        self.refrescar()

    def tiene_clase(self, id_: str, clase: str) -> bool:
        return self.js("([id, c]) => document.getElementById(id).classList.contains(c)", [id_, clase])

    def avanzar(self, segundos: float) -> None:
        """Avanza la simulación en tiempo simulado, sin depender de los cuadros por segundo del navegador."""
        self.js("s => { window.GeneradorAxial.aplicacion.avanzar(s); }", segundos)

    def fijar_estado(self, **valores) -> None:
        """Asigna variables de estado de la simulación (p. ej. ``soc``) para preparar un escenario."""
        self.js(
            "v => { const s = window.GeneradorAxial.aplicacion.simulacion; Object.assign(s, v); }",
            valores,
        )

    def en_marcha(self, valor: bool) -> None:
        if self.app("estado.get('enMarcha')") != valor:
            if self.tiene_clase("cajon-ajustes", "abierto"):
                self.pagina.keyboard.press("Escape")
            self.clic("#btn-toggle-run")

    def regimen_y_pausa(self, segundos: float = 12) -> None:
        self.en_marcha(True)
        self.avanzar(segundos)
        self.en_marcha(False)

    def abrir_ajustes(self) -> None:
        if not self.tiene_clase("cajon-ajustes", "abierto"):
            self.clic(".barra-superior [data-accion='abrir-ajustes']")
        self.pagina.wait_for_timeout(400)

    def instante(self) -> dict:
        return self.app("ultimoInstante()")

    def referencia(self) -> InstanteDinamico:
        """El modelo de Python evaluado con el estado y las entradas que tiene ahora el navegador."""
        datos = self.js(
            """() => { const a = window.GeneradorAxial.aplicacion, s = a.simulacion;
                return { omega: s.omega, angulo: s.angulo, soc: s.soc, vp: s.tensionPolarizacion,
                         temp: s.temperaturaBobinas, habilitado: s.inversorHabilitado, t: s.tiempoS,
                         e: a.estado.instantanea() }; }"""
        )
        e = datos["e"]
        simulacion = SimulacionDinamica(diseno_por_defecto())
        simulacion.omega = datos["omega"]
        simulacion.angulo = datos["angulo"]
        simulacion.soc = datos["soc"]
        simulacion.tension_polarizacion = datos["vp"]
        simulacion.temperatura_bobinas = datos["temp"]
        simulacion.inversor_habilitado = datos["habilitado"]
        simulacion.tiempo_s = datos["t"]
        return simulacion.instantanea(
            EntradasDinamicas(
                par_motriz_nm=e["parMotrizNm"],
                potencia_carga_ac_w=e["cargaAcWatts"],
                inversor_encendido=e["inversorEncendido"],
                temperatura_ambiente_c=e["temperaturaAmbienteC"],
                factor_tiempo=e["factorTiempo"],
                entrehierro_m=e["entrehierroMm"] * 1e-3,
                espiras_por_bobina=e["espirasPorBobina"],
                remanencia_t=e["remanenciaT"],
                capacitancia_filtro_f=e["capacitanciaFiltroUf"] * 1e-6,
            )
        )


@pytest.fixture
def ui(navegador):
    contexto = navegador.new_context(viewport={"width": 1360, "height": 860})
    interfaz = Interfaz(contexto.new_page()).abrir()
    yield interfaz
    assert interfaz.errores == [], f"Errores en la consola del navegador: {interfaz.errores}"
    contexto.close()


def cruces_por_cero(t: np.ndarray, v: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Índices e instantes (interpolados) en que la señal cruza cero subiendo."""
    indices = np.where((v[:-1] < 0) & (v[1:] >= 0))[0]
    return indices, t[indices] - v[indices] * (t[indices + 1] - t[indices]) / (v[indices + 1] - v[indices])


# ---------------------------------------------------------------- estado inicial
def test_carga_con_los_valores_de_diseno(ui):
    diseno = diseno_por_defecto()
    assert ui.texto("val-gap") == "2.5 mm"
    assert ui.texto("val-turns") == "180"
    assert ui.texto("val-br") == "1.25 T (≈N38)"
    assert ui.texto("val-par") == "0.050 N·m"
    assert ui.texto("val-temp") == "25 °C"
    assert float(ui.js("() => document.getElementById('slider-par').max")) == pytest.approx(0.3)
    # El deslizador de espiras no permite más vueltas de las que caben en la ventana de la bobina.
    bobina = diseno.estator.bobina
    ventana = (bobina.diametro_exterior_m - bobina.diametro_interior_m) / 2
    espiras_maximas = math.floor(ventana * bobina.altura_m / bobina.alambre.diametro_esmaltado_m**2)
    assert int(ui.js("() => document.getElementById('slider-turns').max")) == espiras_maximas
    assert ui.texto("txt-pac") == "15"
    for boton in ("btn-volt-110", "btn-load-15", "btn-tiempo-50", "btn-cap-220"):
        assert ui.tiene_clase(boton, "active"), boton


# ---------------------------------------------------------------- panel contra el modelo de Python
@pytest.mark.parametrize(
    ("par", "entrehierro", "espiras", "remanencia", "temperatura", "condensador"),
    [
        (0.05, 2.5, 180, 1.25, 25, 220),
        (0.20, 1.0, 230, 1.45, 40, 4700),
        (0.12, 5.0, 120, 1.15, -10, 1000),
        (0.30, 10.0, 50, 1.25, 25, 2200),
    ],
)
def test_panel_coincide_con_el_modelo_python(ui, par, entrehierro, espiras, remanencia, temperatura, condensador):
    ui.abrir_ajustes()
    ui.mover_deslizador("slider-gap", entrehierro)
    ui.mover_deslizador("slider-turns", espiras)
    ui.mover_deslizador("slider-br", remanencia)
    ui.mover_deslizador("slider-temp", temperatura)
    ui.clic(f"#btn-cap-{condensador}")
    ui.mover_deslizador("slider-par", par)
    ui.regimen_y_pausa()
    m = ui.referencia()

    assert ui.texto("val-gap") == f"{entrehierro:.1f} mm"
    assert ui.texto("val-turns") == str(espiras)
    assert ui.texto("val-br").startswith(f"{remanencia:.2f} T")
    assert ui.texto("val-temp") == f"{temperatura} °C"
    assert ui.texto("val-par") == f"{par:.3f} N·m"
    assert ui.texto("val-rpm") == f"{round(m.rpm)} RPM"
    assert ui.numero("txt-fe") == pytest.approx(m.frecuencia_hz, abs=0.051)
    pico_bornes = m.tension_bornes_rms_v * (m.fem_pico_v / m.fem_rms_v if m.fem_rms_v else 0)
    assert ui.numero("txt-vp") == pytest.approx(pico_bornes, abs=0.006)
    assert ui.numero("txt-vdc") == pytest.approx(m.tension_dc_v, abs=0.006)
    assert ui.numero("txt-par") == pytest.approx(m.par_motriz_nm, abs=6e-4)
    assert ui.numero("txt-peje") == pytest.approx(m.potencia_eje_w, abs=0.006)
    assert ui.numero("txt-temp") == pytest.approx(m.temperatura_bobinas_c, abs=0.051)
    assert ui.numero("txt-soc") == pytest.approx(100 * m.soc, abs=0.051)
    assert ui.numero("txt-vbat") == pytest.approx(m.tension_bateria_v, abs=0.006)
    assert ui.numero("txt-ichg") == pytest.approx(1e3 * m.corriente_neta_a, abs=0.6)
    assert ui.texto("txt-etapa") == ETAPAS[m.etapa_carga]
    assert ui.texto("val-rizado") == f"rizado {m.rizado_v:.2f} V"


def test_regimen_permanente_equilibra_los_pares(ui):
    """En régimen: τ_motriz = τ_em + τ_roz (el frenado de Lenz limita la velocidad)."""
    ui.mover_deslizador("slider-par", 0.07)
    ui.regimen_y_pausa(15)
    m = ui.instante()
    assert m["rpm"] == pytest.approx(483, abs=5)
    assert m["parMotrizNm"] == pytest.approx(m["parElectromagneticoNm"] + m["parRozamientoNm"], abs=2e-4)
    assert m["parElectromagneticoNm"] > m["parRozamientoNm"]
    assert ui.texto("txt-etapa") == "MPPT"


def test_tendencias_teoricas_de_la_fem(ui):
    """A ω fija: E ∝ N y ∝ Br (Faraday), y decrece al abrir el entrehierro (B_z decrece con z)."""
    ui.en_marcha(False)
    ui.mover_deslizador("slider-temp", 20)  # Br efectiva = Br nominal

    def fem(**ajustes):
        for id_, valor in ajustes.items():
            ui.mover_deslizador(id_.replace("_", "-"), valor)
        ui.fijar_estado(omega=2 * math.pi * 1000 / 60)
        return ui.instante()["femPicoV"]

    base = fem(slider_turns=100, slider_br=1.20, slider_gap=2.5)
    assert fem(slider_turns=200) / base == pytest.approx(2.0, rel=1e-9)
    assert fem(slider_turns=100, slider_br=1.44) / base == pytest.approx(1.2, rel=1e-9)
    tensiones = [fem(slider_br=1.20, slider_gap=g) for g in (1.0, 2.5, 5.0, 10.0)]
    assert tensiones == sorted(tensiones, reverse=True)


def test_sin_par_motriz_el_rotor_se_detiene(ui):
    ui.mover_deslizador("slider-par", 0)
    ui.regimen_y_pausa(15)
    assert ui.app("simulacion.omega") == 0
    assert ui.texto("val-rpm") == "0 RPM"
    assert ui.texto("txt-etapa") == "Sin generación"
    assert ui.numero("txt-vdc") == 0
    assert ui.app("escena.luzLed.intensity") == 0
    assert ui.app("escena.ledCargador.material.emissiveIntensity") == pytest.approx(0.1)


# ---------------------------------------------------------------- impulso manual
def test_impulso_manual_y_frenado(ui):
    ui.mover_deslizador("slider-par", 0)
    ui.regimen_y_pausa(15)

    # El impulso cuenta tiempo simulado: en pausa no se consume.
    resultado = ui.js(
        """() => { const a = window.GeneradorAxial.aplicacion;
            document.getElementById('btn-hand-spin').click();
            a.estado.actualizar({ enMarcha: false });
            a.avanzar(2);
            return [a.estado.get('impulsoManual'), a.simulacion.omega]; }"""
    )
    assert resultado[0] > 0 and resultado[1] == 0
    assert ui.texto("val-par") == "0.000 N·m"
    assert ui.tiene_clase("btn-hand-spin", "active")

    rpm, impulso = ui.js(
        """() => { const a = window.GeneradorAxial.aplicacion;
            a.estado.actualizar({ enMarcha: true });
            const rpm = [], impulso = [];
            for (let k = 0; k < 40; k++) { rpm.push(a.avanzar(0.05).rpm); impulso.push(a.estado.get('impulsoManual')); }
            return [rpm, impulso]; }"""
    )
    # 0.08 N·m durante 0.5 s (10 pasos de 50 ms) y luego solo rozamiento y frenado de Lenz.
    assert impulso[8] > 0 and impulso[10] == 0
    assert max(rpm) == pytest.approx(505, abs=10)
    assert int(np.argmax(rpm)) in (9, 10)
    assert rpm[-1] < max(rpm)
    ui.avanzar(5)
    assert ui.app("simulacion.omega") == 0
    assert not ui.tiene_clase("btn-hand-spin", "active")


# ---------------------------------------------------------------- tiempo, condensador y temperatura
def test_selector_de_tiempo_acelera_la_bateria_y_no_la_mecanica(ui):
    ui.mover_deslizador("slider-par", 0)
    ui.regimen_y_pausa(15)
    ui.en_marcha(True)

    def descarga(factor: int) -> float:
        ui.clic(f"#btn-tiempo-{factor}")
        assert ui.tiene_clase(f"btn-tiempo-{factor}", "active")
        return ui.js(
            """() => { const a = window.GeneradorAxial.aplicacion, s = a.simulacion;
                Object.assign(s, { soc: 0.8, tensionPolarizacion: 0 });
                a.avanzar(2);
                return 0.8 - s.soc; }"""
        )

    lenta, rapida = descarga(1), descarga(500)
    assert lenta > 0
    assert rapida / lenta == pytest.approx(500, rel=0.02)
    # La mecánica corre siempre en tiempo real: la velocidad de régimen no depende del factor.
    ui.mover_deslizador("slider-par", 0.1)
    rpm = []
    for factor in (1, 500):
        ui.clic(f"#btn-tiempo-{factor}")
        ui.fijar_estado(omega=0.0)
        ui.avanzar(1)
        rpm.append(ui.app("simulacion.omega"))
    assert rpm[0] == pytest.approx(rpm[1], rel=0.02)


def test_el_condensador_reduce_el_rizado(ui):
    ui.abrir_ajustes()
    ui.mover_deslizador("slider-par", 0.2)
    ui.regimen_y_pausa(12)
    rizados = []
    for capacidad in (220, 1000, 2200, 4700):
        ui.clic(f"#btn-cap-{capacidad}")
        m = ui.instante()
        rizados.append(m["rizadoV"])
        excesivo = m["rizadoV"] > 0.25 * m["tensionDcV"]
        assert ui.tiene_clase("tarjeta-dc", "alerta") == (excesivo or not m["salidaDcSegura"])
        # ΔV = Ī/(2 f C): a igual corriente el rizado es inversamente proporcional a C.
        i_media = 2 * math.sqrt(2) / math.pi * m["corrienteGeneradorA"]
        assert m["rizadoV"] == pytest.approx(i_media / (2 * m["frecuenciaHz"] * capacidad * 1e-6), rel=1e-9)
    assert rizados == sorted(rizados, reverse=True)
    assert ui.tiene_clase("tarjeta-dc", "alerta") is False


def test_temperatura_ambiente_calienta_las_bobinas_y_debilita_el_iman(ui):
    ui.abrir_ajustes()
    ui.clic("#btn-tiempo-500")
    ui.mover_deslizador("slider-par", 0.2)
    resultados = {}
    for temperatura in (-10, 45):
        ui.mover_deslizador("slider-temp", temperatura)
        ui.regimen_y_pausa(6)
        m = ui.instante()
        resultados[temperatura] = m
        assert m["temperaturaBobinasC"] > temperatura
        assert ui.numero("txt-temp") == pytest.approx(m["temperaturaBobinasC"], abs=0.051)
    # Br baja −0.12 %/K y R del cobre sube 0.393 %/K.
    assert resultados[45]["remanenciaEfectivaT"] / resultados[-10]["remanenciaEfectivaT"] == pytest.approx(
        (1 - 0.0012 * 25) / (1 + 0.0012 * 30), rel=1e-9
    )
    assert resultados[45]["resistenciaOhm"] > resultados[-10]["resistenciaOhm"]


def test_alarma_de_sobretemperatura(ui):
    ui.abrir_ajustes()
    ui.mover_deslizador("slider-temp", 45)
    ui.fijar_estado(temperaturaBobinas=60.0)
    ui.en_marcha(False)
    ui.refrescar()
    assert ui.tiene_clase("tarjeta-temp", "alerta")
    assert "PLA" in ui.js("() => document.getElementById('tarjeta-temp').title")


# ---------------------------------------------------------------- controlador de carga y batería
def test_absorcion_y_flotacion(ui):
    ui.abrir_ajustes()
    ui.clic("#btn-toggle-inverter")
    ui.clic("#btn-tiempo-500")
    ui.mover_deslizador("slider-par", 0.3)
    ui.fijar_estado(soc=0.97)
    ui.regimen_y_pausa(20)
    assert ui.texto("txt-etapa") == "Absorción 14.4 V"
    assert ui.numero("txt-vbat") == pytest.approx(14.4, abs=0.006)
    assert ui.numero("txt-ichg") > 0

    ui.fijar_estado(soc=0.996)
    ui.regimen_y_pausa(20)
    assert ui.texto("txt-etapa") == "Flotación 13.8 V"
    assert ui.numero("txt-vbat") == pytest.approx(13.8, abs=0.006)


def test_corte_por_baja_tension_con_histeresis(ui):
    ui.abrir_ajustes()
    ui.clic("#btn-load-40")
    ui.clic("#btn-tiempo-500")
    ui.mover_deslizador("slider-par", 0)
    ui.fijar_estado(soc=0.05)
    ui.regimen_y_pausa(3)
    assert ui.app("simulacion.inversorHabilitado") is False
    assert ui.texto("txt-vac") == "0" and ui.texto("txt-pac") == "0"
    assert ui.tiene_clase("tarjeta-bateria", "alerta") and ui.tiene_clase("tarjeta-inversor", "alerta")
    assert "apagado" in ui.texto("osc-scale")
    assert ui.app("escena.luzBombillo.intensity") == 0

    # Por debajo de 12.3 V en reposo sigue desconectado (histéresis): OCV(0.35) ≈ 12.04 V.
    ui.fijar_estado(soc=0.35)
    ui.regimen_y_pausa(2)
    assert ui.app("simulacion.inversorHabilitado") is False

    # OCV(0.8) = 12.58 V ≥ 12.3 V: se reconecta.
    ui.fijar_estado(soc=0.8)
    ui.regimen_y_pausa(2)
    assert ui.app("simulacion.inversorHabilitado") is True
    assert ui.texto("txt-vac") == "110"
    assert not ui.tiene_clase("tarjeta-bateria", "alerta")


def test_selectores_de_tension_carga_e_inversor(ui):
    ui.clic("#btn-volt-220")
    assert ui.texto("txt-vac") == "220"
    assert ui.tiene_clase("btn-volt-220", "active") and not ui.tiene_clase("btn-volt-110", "active")

    ui.abrir_ajustes()
    for carga in (0, 15, 40):
        ui.clic(f"#btn-load-{carga}")
        assert ui.texto("txt-pac") == str(carga)
        assert [ui.tiene_clase(f"btn-load-{c}", "active") for c in (0, 15, 40)] == [c == carga for c in (0, 15, 40)]
        # El inversor consume aunque no haya carga (3.6 W en vacío).
        assert ui.instante()["potenciaEntradaInversorW"] == pytest.approx(
            3.6 + carga + (150 / 0.9 - 150 - 3.6) / 150**2 * carga**2, rel=1e-9
        )

    ui.clic("#btn-toggle-inverter")
    assert ui.texto("txt-inversor") == "Inversor apagado"
    assert ui.texto("txt-vac") == "0" and ui.texto("txt-pac") == "0"
    assert ui.app("escena.ledInversor.material.emissiveIntensity") == pytest.approx(0.05)
    assert ui.app("escena.luzBombillo.intensity") == 0

    ui.clic("#btn-toggle-inverter")
    assert ui.texto("txt-inversor") == "Inversor encendido"
    assert ui.texto("txt-vac") == "220" and ui.texto("txt-pac") == "40"
    assert ui.app("escena.luzBombillo.intensity") > 0


# ---------------------------------------------------------------- osciloscopio
def test_osciloscopio_muestra_la_onda_real_y_la_salida_ac(ui):
    ui.mover_deslizador("slider-par", 0.1)
    ui.regimen_y_pausa(12)
    m = ui.instante()
    muestras = ui.app("osciloscopio.muestras")
    t = np.array([s["t"] for s in muestras])
    v = np.array([s["v"] for s in muestras])
    v_inv = np.array([s["vInv"] for s in muestras])
    cresta = m["femPicoV"] / m["femRmsV"]
    pico = m["tensionBornesRmsV"] * cresta

    indices, cruces = cruces_por_cero(t, v)
    assert (len(cruces) - 1) / (cruces[-1] - cruces[0]) == pytest.approx(8 * m["rpm"] / 120, rel=0.01)
    assert np.max(np.abs(v)) == pytest.approx(pico, rel=0.01)
    # La fem no es senoidal: el factor de cresta del solape imán-bobina es ≈ 1.34 (√2 ≈ 1.41 en una senoide).
    periodo_entero = v[indices[0] + 1 : indices[-1] + 1]
    assert np.max(np.abs(periodo_entero)) / np.sqrt(np.mean(periodo_entero**2)) == pytest.approx(cresta, rel=0.02)
    assert cresta == pytest.approx(1.336, abs=0.01)

    _, cruces_ac = cruces_por_cero(t, v_inv)
    assert (len(cruces_ac) - 1) / (cruces_ac[-1] - cruces_ac[0]) == pytest.approx(60, rel=0.01)
    assert np.max(np.abs(v_inv)) == pytest.approx(110 * math.sqrt(2), rel=0.01)

    escala_ch1 = next(e for e in (0.5, 1, 2, 5, 10, 20) if 3 * e >= 1.1 * pico)
    assert ui.texto("osc-scale").startswith(f"{escala_ch1} / 100 V/div")
    ui.clic("#btn-osc-ch1")
    assert ui.texto("osc-scale").startswith(f"{escala_ch1} V/div")
    ui.clic("#btn-osc-ch2")
    ui.clic("#btn-volt-220")
    assert ui.texto("osc-scale") == "200 V/div"
    assert [ui.tiene_clase(i, "active") for i in ("btn-osc-dual", "btn-osc-ch1", "btn-osc-ch2")] == [False, False, True]


def test_la_traza_maxima_cabe_en_pantalla(ui):
    ui.abrir_ajustes()
    ui.mover_deslizador("slider-gap", 1.0)
    ui.mover_deslizador("slider-turns", 230)
    ui.mover_deslizador("slider-br", 1.45)
    ui.mover_deslizador("slider-temp", -10)
    ui.mover_deslizador("slider-par", 0.3)
    ui.regimen_y_pausa(12)
    assert ui.numero("txt-vp") * 1.1 <= 3 * 20


# ---------------------------------------------------------------- control de la simulación
def test_pausa_congela_rotor_bateria_y_osciloscopio(ui):
    ui.en_marcha(False)
    leer = """() => { const a = window.GeneradorAxial.aplicacion, s = a.simulacion;
        return [s.angulo, s.soc, s.temperaturaBobinas, a.osciloscopio.tiempoS, s.tiempoS]; }"""
    antes = ui.js(leer)
    ui.pagina.wait_for_timeout(1000)
    assert ui.js(leer) == antes
    assert ui.texto("txt-marcha") == "Reanudar" and not ui.tiene_clase("btn-toggle-run", "active")

    ui.en_marcha(True)
    despues = ui.js(
        """() => { const a = window.GeneradorAxial.aplicacion, s = a.simulacion;
            const t0 = s.tiempoS; a.avanzar(0.5); return [s.tiempoS - t0, s.soc]; }"""
    )
    assert despues[0] == pytest.approx(0.5, abs=1e-9)
    assert despues[1] != antes[1]
    assert ui.texto("txt-marcha") == "Pausar"


# ---------------------------------------------------------------- escena 3D
def test_render_fisicamente_basado(ui):
    datos = ui.js(
        """() => { const e = window.GeneradorAxial.aplicacion.escena;
            return [e.renderer.toneMapping === THREE.ACESFilmicToneMapping,
                    e.renderer.outputEncoding === THREE.sRGBEncoding,
                    Boolean(e.escena.environment), e.renderer.shadowMap.enabled,
                    e.bobinas.every(b => b.bobina.material.map && b.bobina.castShadow)]; }"""
    )
    assert datos == [True, True, True, True, True]


def test_conmutadores_de_visualizacion(ui):
    ui.abrir_ajustes()
    ui.clic("#check-field-lines")
    assert ui.app("escena.grupoLineasCampo.visible") is False
    ui.clic("#check-current-arrows")
    assert ui.js("() => window.GeneradorAxial.aplicacion.escena.bobinas.every(b => !b.indicador.visible)")

    ui.clic("#check-field-lines")
    ui.clic("#check-current-arrows")
    assert ui.app("escena.grupoLineasCampo.visible") is True

    # Despiece desde la tarjeta: sincroniza el interruptor del cajón y separa el estator 35 mm.
    ui.pagina.keyboard.press("Escape")
    z_inicial = ui.app("escena.grupoEstator.position.z")
    ui.clic("#btn-despiece")
    assert ui.js("() => document.getElementById('check-exploded').checked") is True
    assert ui.tiene_clase("btn-despiece", "active")
    ui.avanzar(3)
    assert ui.app("escena.grupoEstator.position.z") - z_inicial == pytest.approx(35, abs=0.01)
    ui.clic("#btn-despiece")
    ui.avanzar(3)
    assert ui.app("escena.grupoEstator.position.z") == pytest.approx(z_inicial, abs=0.01)


def test_el_entrehierro_mueve_el_estator(ui):
    z_25 = ui.app("escena.grupoEstator.position.z")
    ui.mover_deslizador("slider-gap", 6.0)
    assert ui.app("escena.grupoEstator.position.z") - z_25 == pytest.approx(3.5, abs=1e-6)


def test_indicadores_de_la_escena_siguen_a_la_fisica(ui):
    ui.mover_deslizador("slider-par", 0.1)
    ui.regimen_y_pausa(12)
    m = ui.instante()
    assert ui.app("escena.luzLed.intensity") == pytest.approx(2.5 * min(1, m["corrienteLedA"] / 0.02), rel=1e-9)
    assert ui.app("escena.ledCargador.material.emissiveIntensity") == pytest.approx(1.0)
    assert ui.app("escena.barraSoC.scale.x") == pytest.approx(m["soc"], abs=1e-9)
    assert ui.app("escena.grupoRotor.rotation.z") == pytest.approx(m["anguloRad"], abs=1e-9)
    brillo = ui.js("() => window.GeneradorAxial.aplicacion.escena.bobinas[0].bobina.material.emissiveIntensity")
    assert 0.2 <= brillo <= 0.8


@pytest.mark.parametrize(("boton", "posicion"), [("cam-front", [0, 0, 300]), ("cam-side", [230, 15, -5]), ("cam-iso", [255, 140, 300])])
def test_camaras(ui, boton, posicion):
    ui.clic(f"#{boton}")
    camara = ui.js("() => window.GeneradorAxial.aplicacion.escena.camara.position.toArray()")
    assert camara == pytest.approx(posicion, abs=0.5)


# ---------------------------------------------------------------- ventanas y paneles
def test_cajon_de_ajustes_y_modal_de_formulas(ui):
    ui.clic(".barra-superior [data-accion='abrir-ajustes']")
    assert ui.tiene_clase("cajon-ajustes", "abierto")
    ui.clic("#btn-cerrar-ajustes")
    assert not ui.tiene_clase("cajon-ajustes", "abierto")
    ui.clic(".tarjeta-red [data-accion='abrir-ajustes']")
    assert ui.tiene_clase("cajon-ajustes", "abierto")
    ui.pagina.keyboard.press("Escape")
    assert not ui.tiene_clase("cajon-ajustes", "abierto")

    ui.clic("#btn-open-help")
    assert ui.js("() => document.getElementById('help-modal').open") is True
    assert "Lenz" in ui.texto("help-modal") and "Thévenin" in ui.texto("help-modal")
    ui.clic("#btn-close-help")
    assert ui.js("() => document.getElementById('help-modal').open") is False


def test_ventana_aparte(ui, navegador):
    with ui.pagina.expect_popup() as emergente:
        ui.clic("#btn-ventana")
    ventana = emergente.value
    ventana.wait_for_load_state()
    assert ventana.evaluate("window.name") == "simulador-axial"
    assert ventana.is_hidden("#btn-ventana")
    ventana.close()  # tres páginas con WebGL por software saturan la CPU del entorno de pruebas

    contexto = navegador.new_context()
    propia = Interfaz(contexto.new_page()).abrir("?ventana=1")
    assert propia.pagina.is_hidden("#btn-ventana")
    contexto.close()


def test_se_adapta_al_tamano_de_la_ventana(ui):
    for ancho, alto in ((1360, 860), (1024, 680)):
        ui.pagina.set_viewport_size({"width": ancho, "height": alto})
        ui.pagina.wait_for_timeout(400)
        lienzo = ui.js(
            """() => { const c = document.getElementById('canvas-container');
                const r = window.GeneradorAxial.aplicacion.escena.renderer.domElement;
                return [c.clientWidth, c.clientHeight, r.clientWidth, r.clientHeight]; }"""
        )
        assert lienzo[:2] == lienzo[2:]
        assert ui.js("() => [...document.querySelectorAll('.cifras dd')].every(e => e.scrollWidth <= e.clientWidth + 1)")
        superpuestos = ui.js(
            """() => { const r = (s) => document.querySelector(s).getBoundingClientRect();
                const a = r('.tarjeta-titulo'), b = r('.tarjeta-red'), c = r('.barra-inferior');
                const choca = (p, q) => p.left < q.right && q.left < p.right && p.top < q.bottom && q.top < p.bottom;
                return choca(a, b) || choca(a, c) || choca(b, c); }"""
        )
        assert not superpuestos
