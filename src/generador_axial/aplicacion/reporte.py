"""Caso de uso: reunir todas las magnitudes intermedias y finales de la memoria de cálculo."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np

from generador_axial.aplicacion import escenarios_dinamicos as ed
from generador_axial.aplicacion.simulacion_dinamica import SimulacionDinamica
from generador_axial.aplicacion.simulador import PuntoDeOperacion, SimuladorGenerador
from generador_axial.configuracion import EscenarioDeAnalisis
from generador_axial.dominio import dinamica as dn
from generador_axial.dominio import fisica

_CLAVE_VALIDA = re.compile(r"^[A-Za-z]+$")


@dataclass(frozen=True)
class Magnitud:
    """Valor con nombre estable; ``clave`` solo admite letras para poder usarse como macro LaTeX."""

    clave: str
    valor: float | str
    decimales: int = 3
    descripcion: str = ""

    def __post_init__(self) -> None:
        if not _CLAVE_VALIDA.match(self.clave):
            raise ValueError(f"Clave inválida para el reporte: {self.clave!r}")

    def como_texto(self) -> str:
        if isinstance(self.valor, str):
            return self.valor
        return f"{self.valor:.{self.decimales}f}"


@dataclass(frozen=True)
class ReporteDeCalculo:
    magnitudes: tuple[Magnitud, ...]
    ensayos: PuntoDeOperacion

    def valor(self, clave: str) -> float | str:
        return next(m.valor for m in self.magnitudes if m.clave == clave)


def generar_reporte(simulador: SimuladorGenerador, escenario: EscenarioDeAnalisis) -> ReporteDeCalculo:
    d = simulador.diseno
    iman, bobina, alambre = d.rotor.iman, d.estator.bobina, d.estator.bobina.alambre
    mm, mm2 = 1e3, 1e6
    g, h = d.entrehierro_m, bobina.altura_m

    radio, espesor = iman.radio_m, iman.espesor_m

    def raiz(z: float) -> float:
        return math.hypot(z, radio)

    def primitiva(z: float) -> float:
        return raiz(z + espesor) - raiz(z)

    ref = simulador.punto_de_operacion(escenario.rpm_forma_de_onda)
    rpm_carga = escenario.rpm_analisis_carga
    vacio_carga = simulador.punto_de_operacion(rpm_carga)
    carga = simulador.operar_con_carga_adaptada(rpm_carga)

    rect, led = d.rectificador, d.indicador
    vdc_ref = float(ref.tension_dc_v)
    vdc_max = float(simulador.punto_de_operacion(escenario.rpm_maxima).tension_dc_v)
    corriente_led_ref = led.corriente_a(vdc_ref)
    rizado_ref = fisica.rizado_pico_a_pico(corriente_led_ref, float(ref.frecuencia_electrica_hz), rect.capacitancia_filtro_f)

    magnitudes = (
        Magnitud("GradoIman", iman.grado, descripcion="Grado comercial del imán"),
        Magnitud("Br", iman.remanencia_t, 2, "Remanencia [T]"),
        Magnitud("DiametroIman", iman.diametro_m * mm, 0, "[mm]"),
        Magnitud("RadioIman", iman.radio_m * mm, 1, "[mm]"),
        Magnitud("EspesorIman", iman.espesor_m * mm, 1, "[mm]"),
        Magnitud("AreaImanMM", iman.area_cara_m2 * mm2, 2, "[mm^2]"),
        Magnitud("Polos", d.rotor.numero_polos, 0),
        Magnitud("ParesPolos", d.rotor.pares_de_polos, 0),
        Magnitud("PasoPolarGrados", math.degrees(d.rotor.paso_polar_rad), 1, "[grados]"),
        Magnitud("RadioMontaje", d.rotor.radio_montaje_m * mm, 1, "[mm]"),
        Magnitud("Bobinas", d.estator.numero_bobinas, 0),
        Magnitud("Espiras", bobina.espiras, 0),
        Magnitud("EspirasTotales", d.estator.espiras_totales, 0),
        Magnitud("DiametroInteriorBobina", bobina.diametro_interior_m * mm, 1, "[mm]"),
        Magnitud("DiametroExteriorBobina", bobina.diametro_exterior_m * mm, 1, "[mm]"),
        Magnitud("AlturaBobina", h * mm, 1, "[mm]"),
        Magnitud("Entrehierro", g * mm, 1, "[mm]"),
        Magnitud("EntrehierroMasAltura", (g + h) * mm, 1, "[mm]"),
        Magnitud("Acoplamiento", d.factor_acoplamiento, 2),
        Magnitud("CalibreAWG", alambre.calibre_awg, 0),
        Magnitud("DiametroCobre", alambre.diametro_cobre_m * mm, 3, "[mm]"),
        Magnitud("DiametroEsmaltado", alambre.diametro_esmaltado_m * mm, 3, "[mm]"),
        Magnitud("AreaCobreMM", alambre.area_cobre_m2 * mm2, 4, "[mm^2]"),
        Magnitud("ResistividadCobre", alambre.resistividad_ohm_m * 1e8, 2, "[1e-8 ohm m]"),
        Magnitud("LongitudMediaEspira", bobina.longitud_media_espira_m * mm, 2, "[mm]"),
        Magnitud("LongitudAlambreBobina", bobina.longitud_alambre_m, 2, "[m]"),
        Magnitud("LongitudAlambreTotal", bobina.longitud_alambre_m * d.estator.numero_bobinas, 2, "[m]"),
        Magnitud("ResistenciaBobina", bobina.resistencia_ohm, 3, "[ohm]"),
        Magnitud("ResistenciaInterna", d.estator.resistencia_interna_ohm, 2, "[ohm]"),
        Magnitud("VentanaBobinaMM", bobina.area_ventana_m2 * mm2, 1, "[mm^2]"),
        Magnitud("Ocupacion", bobina.factor_ocupacion, 2),
        Magnitud("RaizCaraIman", raiz(espesor) * mm, 4, "sqrt(L^2+R^2) [mm]"),
        Magnitud("TerminoCaraIman", espesor / raiz(espesor), 4, "L/sqrt(L^2+R^2)"),
        Magnitud("CampoCaraIman", simulador.campo_en_cara_iman_t, 4, "[T]"),
        Magnitud("EntrehierroMasEspesor", (g + espesor) * mm, 1, "g+L [mm]"),
        Magnitud("RaizGL", raiz(g + espesor) * mm, 4, "sqrt((g+L)^2+R^2) [mm]"),
        Magnitud("RaizG", raiz(g) * mm, 4, "sqrt(g^2+R^2) [mm]"),
        Magnitud("TerminoUnoG", (g + espesor) / raiz(g + espesor), 4, "(g+L)/sqrt((g+L)^2+R^2)"),
        Magnitud("TerminoDosG", g / raiz(g), 4, "g/sqrt(g^2+R^2)"),
        Magnitud("CampoCaraBobina", simulador.campo_en_cara_bobina_t, 4, "[T]"),
        Magnitud("EntrehierroAlturaEspesor", (g + h + espesor) * mm, 1, "g+h+L [mm]"),
        Magnitud("RaizGHL", raiz(g + h + espesor) * mm, 4, "sqrt((g+h+L)^2+R^2) [mm]"),
        Magnitud("RaizGH", raiz(g + h) * mm, 4, "sqrt((g+h)^2+R^2) [mm]"),
        Magnitud("PrimitivaEnG", primitiva(g) * mm, 4, "F(g) [mm]"),
        Magnitud("PrimitivaEnGH", primitiva(g + h) * mm, 4, "F(g+h) [mm]"),
        Magnitud("DiferenciaPrimitivas", (primitiva(g + h) - primitiva(g)) * mm, 4, "F(g+h)-F(g) [mm]"),
        Magnitud("CampoMedioBobina", simulador.campo_medio_bobina_t, 4, "[T]"),
        Magnitud("ReduccionPorPromedio", 100 * (1 - simulador.campo_medio_bobina_t / simulador.campo_en_cara_bobina_t), 1, "[%]"),
        Magnitud("FlujoMaximoMicro", simulador.flujo_maximo_por_espira_wb * 1e6, 3, "[uWb]"),
        Magnitud("AreaImanM", iman.area_cara_m2 * 1e4, 4, "[1e-4 m^2]"),
        Magnitud("CaidaDiodo", rect.caida_por_diodo_v, 2, "[V]"),
        Magnitud("CaidaPuente", rect.caida_total_v, 2, "[V]"),
        Magnitud("CapacitanciaMicro", rect.capacitancia_filtro_f * 1e6, 0, "[uF]"),
        Magnitud("TensionNominalCondensador", rect.tension_nominal_condensador_v, 0, "[V]"),
        Magnitud("RpmMaxima", escenario.rpm_maxima, 0),
        Magnitud("TensionDcMaxima", vdc_max, 2, "[V]"),
        Magnitud("MargenCondensador", 100 * (1 - vdc_max / rect.tension_nominal_condensador_v), 0, "[%]"),
        Magnitud("ResistenciaLed", led.resistencia_ohm, 0, "[ohm]"),
        Magnitud("PotenciaNominalResistenciaLed", led.potencia_nominal_resistencia_w, 2, "[W]"),
        Magnitud("CaidaLed", led.caida_led_v, 1, "[V]"),
        Magnitud("CorrienteLedRefMili", corriente_led_ref * 1e3, 2, "[mA]"),
        Magnitud("CorrienteLedMaxMili", led.corriente_a(vdc_max) * 1e3, 1, "[mA]"),
        Magnitud("CorrienteLedLimiteMili", led.corriente_maxima_led_a * 1e3, 0, "[mA]"),
        Magnitud("PotenciaResistenciaLedMax", led.potencia_resistencia_w(vdc_max), 3, "[W]"),
        Magnitud("RizadoRef", rizado_ref * 1e3, 1, "[mV]"),
        Magnitud("RpmReferencia", escenario.rpm_forma_de_onda, 0),
        Magnitud("OmegaMecanicaRef", float(ref.velocidad_angular_mecanica), 3, "[rad/s]"),
        Magnitud("FrecuenciaRef", float(ref.frecuencia_electrica_hz), 2, "[Hz]"),
        Magnitud("PeriodoRefMs", 1e3 / float(ref.frecuencia_electrica_hz), 2, "[ms]"),
        Magnitud("OmegaElectricaRef", float(ref.velocidad_angular_electrica), 2, "[rad/s]"),
        Magnitud("TensionPicoRef", float(ref.tension_pico_v), 2, "[V]"),
        Magnitud("TensionRmsRef", float(ref.tension_rms_v), 2, "[V]"),
        Magnitud("TensionDcRef", float(ref.tension_dc_v), 2, "[V]"),
        Magnitud("TensionPicoPorBobinaRef", float(ref.tension_pico_v) / d.estator.numero_bobinas, 3, "[V]"),
        Magnitud("RpmCarga", rpm_carga, 0),
        Magnitud("OmegaMecanicaCarga", float(vacio_carga.velocidad_angular_mecanica), 2, "[rad/s]"),
        Magnitud("TensionPicoCarga", float(vacio_carga.tension_pico_v), 2, "[V]"),
        Magnitud("TensionRmsCarga", float(vacio_carga.tension_rms_v), 2, "[V]"),
        Magnitud("CorrienteCarga", float(carga.corriente_rms_a), 3, "[A]"),
        Magnitud("TensionEnCarga", float(carga.tension_carga_rms_v), 2, "[V]"),
        Magnitud("PotenciaCarga", float(carga.potencia_carga_w), 3, "[W]"),
        Magnitud("PotenciaPerdidas", float(carga.potencia_perdidas_cobre_w), 3, "[W]"),
        Magnitud("PotenciaMecanica", float(carga.potencia_mecanica_w), 3, "[W]"),
        Magnitud("ParResistenteMili", float(carga.par_resistente_nm) * 1e3, 1, "[mN m]"),
        Magnitud("Eficiencia", float(carga.eficiencia) * 100, 0, "[%]"),
        *_magnitudes_microred(simulador, escenario),
        *_magnitudes_realistas(simulador),
    )
    ensayos = simulador.punto_de_operacion(np.asarray(escenario.rpm_ensayos, dtype=float))
    return ReporteDeCalculo(magnitudes=magnitudes, ensayos=ensayos)


def _magnitudes_microred(simulador: SimuladorGenerador, escenario: EscenarioDeAnalisis) -> tuple[Magnitud, ...]:
    bateria, controlador, inversor = simulador.bateria, simulador.controlador_carga, simulador.inversor
    rpm = escenario.rpm_microred
    potencia_ac = escenario.potencia_carga_ac_w
    potencia_reducida = min(p for p in escenario.potencias_carga_ac_w if p > 0)
    soc = bateria.soc_inicial

    punto = simulador.punto_de_operacion(rpm)
    solo_carga = simulador.balance_microred(rpm, 0.0, soc)
    con_carga = simulador.balance_microred(rpm, potencia_ac, soc)
    parado = simulador.balance_microred(0.0, potencia_ac, soc)
    tension_oc = solo_carga.tension_bateria_v
    corriente_carga = solo_carga.potencia_hacia_bateria_w / tension_oc
    corriente_inversor = con_carga.potencia_entrada_inversor_w / tension_oc

    return (
        Magnitud("BateriaTension", bateria.tension_nominal_v, 0, "[V]"),
        Magnitud("BateriaCapacidad", bateria.capacidad_ah, 0, "[Ah]"),
        Magnitud("BateriaEnergia", bateria.energia_almacenada_wh, 0, "[Wh]"),
        Magnitud("BateriaResistencia", bateria.resistencia_interna_ohm, 2, "[ohm]"),
        Magnitud("BateriaVacia", bateria.tension_minima_v, 1, "E_oc con SoC = 0 [V]"),
        Magnitud("BateriaLlena", bateria.tension_maxima_v, 1, "E_oc con SoC = 1 [V]"),
        Magnitud("BateriaPendiente", bateria.tension_maxima_v - bateria.tension_minima_v, 1, "[V]"),
        Magnitud("SocInicial", soc * 100, 0, "[%]"),
        Magnitud("SocCorte", bateria.soc_minimo_descarga * 100, 0, "[%]"),
        Magnitud("SocReconexion", (bateria.soc_minimo_descarga + bateria.histeresis_reconexion_soc) * 100, 0, "[%]"),
        Magnitud("TensionOcRef", tension_oc, 2, "[V]"),
        Magnitud("EnergiaUtilRef", bateria.energia_utilizable_wh(soc), 1, "[Wh]"),
        Magnitud("ControladorEficiencia", controlador.eficiencia * 100, 0, "[%]"),
        Magnitud("ControladorArranque", controlador.tension_minima_arranque_v, 1, "[V]"),
        Magnitud("ControladorCorrienteMax", controlador.corriente_maxima_salida_a, 1, "[A]"),
        Magnitud("ControladorAbsorcion", controlador.tension_corte_absorcion_v, 1, "[V]"),
        Magnitud("RpmMicrored", rpm, 0),
        Magnitud("FemRmsMicrored", float(punto.tension_rms_v), 2, "[V]"),
        Magnitud("TensionDcMicrored", float(punto.tension_dc_v), 2, "[V]"),
        Magnitud("PotenciaExtraibleMicrored", solo_carga.potencia_generador_w, 3, "[W]"),
        Magnitud("PotenciaHaciaBateria", solo_carga.potencia_hacia_bateria_w, 3, "[W]"),
        Magnitud("CorrienteCargaMicroredMili", corriente_carga * 1e3, 0, "[mA]"),
        Magnitud("PotenciaMecanicaMicrored", solo_carga.potencia_mecanica_w, 2, "[W]"),
        Magnitud("ParMicroredMili", solo_carga.par_resistente_nm * 1e3, 1, "[mN m]"),
        Magnitud("HorasRecarga", (1 - soc) * bateria.capacidad_ah / corriente_carga, 1, "[h]"),
        Magnitud("InversorTension", inversor.tension_salida_rms_v, 0, "[V]"),
        Magnitud("InversorPico", inversor.tension_pico_v, 1, "[V]"),
        Magnitud("InversorTensionAlta", max(escenario.tensiones_inversor_v), 0, "[V]"),
        Magnitud("InversorPicoAlto", np.sqrt(2) * max(escenario.tensiones_inversor_v), 1, "[V]"),
        Magnitud("InversorFrecuencia", inversor.frecuencia_hz, 0, "[Hz]"),
        Magnitud("InversorNominal", inversor.potencia_nominal_w, 0, "[W]"),
        Magnitud("InversorEficiencia", inversor.eficiencia * 100, 0, "[%]"),
        Magnitud("RelacionEspiras", inversor.tension_pico_v / bateria.tension_nominal_v, 1, "V_pico,AC / V_bat"),
        Magnitud("PotenciaCargaAc", potencia_ac, 0, "[W]"),
        Magnitud("CorrienteAcMili", fisica.corriente_salida_inversor(potencia_ac, inversor.tension_salida_rms_v) * 1e3, 0, "[mA]"),
        Magnitud("PotenciaEntradaInversor", con_carga.potencia_entrada_inversor_w, 2, "[W]"),
        Magnitud("CorrienteInversorBateria", corriente_inversor, 2, "[A]"),
        Magnitud("PotenciaNetaBateria", con_carga.potencia_neta_bateria_w, 2, "[W]"),
        Magnitud("AutonomiaHoras", con_carga.autonomia_h, 2, "[h]"),
        Magnitud("AutonomiaParadoHoras", parado.autonomia_h, 2, "[h]"),
        Magnitud("RpmEquilibrio", simulador.rpm_de_equilibrio(potencia_ac), 0),
        Magnitud("PotenciaCargaReducida", potencia_reducida, 0, "[W]"),
        Magnitud("RpmEquilibrioReducida", simulador.rpm_de_equilibrio(potencia_reducida), 0),
    )


def _magnitudes_realistas(simulador: SimuladorGenerador) -> tuple[Magnitud, ...]:
    """Parámetros y resultados del modelo dinámico (Documento 5)."""
    d = simulador.diseno
    simulacion = SimulacionDinamica(d)
    p, perfil = simulacion.p, simulacion.perfil
    bobina = d.estator.bobina
    inductancia = dn.inductancia_bobina_h(
        bobina.espiras,
        (bobina.diametro_interior_m + bobina.diametro_exterior_m) / 4,
        bobina.altura_m,
        (bobina.diametro_exterior_m - bobina.diametro_interior_m) / 2,
    )
    bat, inv, termico, motriz, roz = p.bateria, p.inversor, p.termico, p.motriz, p.perdidas
    k_inversor = (simulador.inversor.potencia_nominal_w / simulador.inversor.eficiencia
                  - simulador.inversor.potencia_nominal_w - inv.potencia_vacio_w) / simulador.inversor.potencia_nominal_w**2

    par_ref = 0.07
    regimen = ed.regimen_permanente(d, par_ref)
    termico_ref = ed.regimen_permanente(d, par_ref, factor_tiempo=500.0)
    con_carga = ed.regimen_permanente(d, par_ref, inversor_encendido=True)
    maximo = ed.regimen_permanente(d, motriz.par_maximo_nm)
    rizado_bajo = ed.regimen_permanente(d, 0.2, capacitancia_filtro_f=220e-6)
    rizado_alto = ed.regimen_permanente(d, 0.2, capacitancia_filtro_f=4700e-6)
    impulso = ed.impulso_y_frenado(d)
    ciclo = ed.ciclo_de_carga(d)

    return (
        Magnitud("InerciaRotor", simulacion.momento_inercia * 1e4, 3, "[1e-4 kg m^2]"),
        Magnitud("InductanciaBobinaMili", inductancia * 1e3, 3, "[mH]"),
        Magnitud("InductanciaTotalMili", d.estator.numero_bobinas * inductancia * 1e3, 2, "[mH]"),
        Magnitud("FlujoMaximoReal", perfil.flujo_maximo, 3, "phi_max normalizado"),
        Magnitud("PicoDerivadaFlujo", perfil.pico_derivada, 3),
        Magnitud("RmsDerivadaFlujo", perfil.rms_derivada, 3),
        Magnitud("FactorCresta", perfil.factor_cresta, 3),
        Magnitud("FactorMedia", perfil.factor_media, 3),
        Magnitud("RelacionFemRealIdeal", math.sqrt(2) * perfil.rms_derivada / d.factor_acoplamiento, 3),
        Magnitud("PuntosRadiales", p.integracion.puntos_radiales, 0),
        Magnitud("MuestrasPerfil", p.integracion.muestras_perfil, 0),
        Magnitud("PasoIntegracionMili", p.integracion.paso_maximo_s * 1e3, 0, "[ms]"),
        Magnitud("ParCoulombMili", roz.par_coulomb_nm * 1e3, 1, "[mN m]"),
        Magnitud("CoefViscosoMicro", roz.coeficiente_viscoso_nm_s * 1e6, 1, "[uN m s]"),
        Magnitud("CoefVentilacionNano", roz.coeficiente_ventilacion_nm_s2 * 1e9, 1, "[nN m s^2]"),
        Magnitud("ParMaximoMotriz", motriz.par_maximo_nm, 2, "[N m]"),
        Magnitud("VelocidadVacioMotriz", motriz.velocidad_vacio_rpm, 0, "[RPM]"),
        Magnitud("ParImpulso", motriz.par_impulso_nm, 2, "[N m]"),
        Magnitud("DuracionImpulso", motriz.duracion_impulso_s, 1, "[s]"),
        Magnitud("CapacidadTermica", termico.capacidad_termica_j_k, 0, "[J/K]"),
        Magnitud("ConveccionNatural", termico.conveccion_natural_w_m2k, 0, "[W/m^2K]"),
        Magnitud("ConveccionForzada", termico.conveccion_forzada_w_m2k_por_rad_s, 2, "[W/m^2K por rad/s]"),
        Magnitud("CoefCobre", termico.coeficiente_cobre_1_k * 100, 3, "[%/K]"),
        Magnitud("CoefRemanencia", termico.coeficiente_remanencia_1_k * 100, 2, "[%/K]"),
        Magnitud("TemperaturaMaximaPla", termico.temperatura_maxima_pla_c, 0, "[C]"),
        Magnitud("BateriaRCero", bat.resistencia_ohmica_ohm * 1e3, 0, "[mohm]"),
        Magnitud("BateriaRPolarizacion", bat.resistencia_polarizacion_ohm * 1e3, 0, "[mohm]"),
        Magnitud("BateriaTau", bat.constante_tiempo_polarizacion_s, 0, "[s]"),
        Magnitud("BateriaPeukert", bat.exponente_peukert, 2),
        Magnitud("BateriaEtaCoulomb", bat.eficiencia_coulomb * 100, 0, "[%]"),
        Magnitud("BateriaEtaLlena", bat.eficiencia_coulomb_llena * 100, 0, "[%]"),
        Magnitud("BateriaSocGas", bat.soc_inicio_gasificacion * 100, 0, "[%]"),
        Magnitud("BateriaAutodescarga", bat.autodescarga_mensual * 100, 0, "[%/mes]"),
        Magnitud("BateriaSocFlotacion", bat.soc_flotacion * 100, 1, "[%]"),
        Magnitud("BateriaFactorGas", bat.factor_sobrepotencial_carga, 0),
        Magnitud("BateriaPendienteGas", bat.pendiente_sobrepotencial_carga, 0),
        Magnitud("ControladorFlotacion", simulador.controlador_carga.tension_flotacion_v, 1, "[V]"),
        Magnitud("ConsumoControladorMili", p.controlador.consumo_propio_a * 1e3, 0, "[mA]"),
        Magnitud("InversorVacio", inv.potencia_vacio_w, 1, "[W]"),
        Magnitud("InversorCoefCuadratico", k_inversor * 1e4, 2, "[1e-4 1/W]"),
        Magnitud("InversorCorte", inv.tension_corte_v, 1, "[V]"),
        Magnitud("InversorReconexion", inv.tension_reconexion_v, 1, "[V]"),
        Magnitud("ParReferencia", par_ref, 2, "[N m]"),
        Magnitud("RpmRegimenRef", regimen.rpm, 0),
        Magnitud("PotenciaEjeRef", regimen.potencia_eje_w, 2, "[W]"),
        Magnitud("PotenciaElectromagneticaRef", regimen.potencia_electromagnetica_w, 2, "[W]"),
        Magnitud("PerdidasCobreRef", regimen.perdidas_cobre_w, 3, "[W]"),
        Magnitud("PerdidasRozamientoRef", regimen.perdidas_rozamiento_w, 3, "[W]"),
        Magnitud("PerdidasFoucaultMili", regimen.perdidas_foucault_w * 1e3, 2, "[mW]"),
        Magnitud("PotenciaBateriaRef", regimen.potencia_hacia_bateria_w, 2, "[W]"),
        Magnitud("EficienciaRef", 100 * regimen.potencia_hacia_bateria_w / regimen.potencia_eje_w, 0, "[%]"),
        Magnitud("TensionDcRefReal", regimen.tension_dc_v, 2, "[V]"),
        Magnitud("CorrienteGeneradorRef", regimen.corriente_generador_a, 3, "[A]"),
        Magnitud("TemperaturaRegimenRef", termico_ref.temperatura_bobinas_c, 1, "[C]"),
        Magnitud("RpmConCargaRef", con_carga.rpm, 0),
        Magnitud("PotenciaEntradaInversorRef", con_carga.potencia_entrada_inversor_w, 1, "[W]"),
        Magnitud("CorrienteNetaConCarga", con_carga.corriente_neta_a, 2, "[A]"),
        Magnitud("RpmParMaximo", maximo.rpm, 0),
        Magnitud("PotenciaBateriaParMaximo", maximo.potencia_hacia_bateria_w, 2, "[W]"),
        Magnitud("RizadoBajo", rizado_bajo.rizado_v, 1, "[V] con 220 uF"),
        Magnitud("RizadoAlto", rizado_alto.rizado_v, 2, "[V] con 4700 uF"),
        Magnitud("RpmPicoImpulso", impulso.rpm_pico, 0),
        Magnitud("TiempoParadaImpulso", impulso.tiempo_parada_s, 1, "[s]"),
        Magnitud("HorasHastaAbsorcion", ciclo.inicio_de_etapa_h("absorción"), 1, "[h]"),
        Magnitud("HorasHastaFlotacion", ciclo.inicio_de_etapa_h("flotación"), 1, "[h]"),
        Magnitud("CorrienteFlotacionMili", ciclo.serie[-1].corriente_neta_a * 1e3, 0, "[mA]"),
    )
