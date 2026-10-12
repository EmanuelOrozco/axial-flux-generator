"""Caso de uso: simulación temporal realista del sistema completo.

Eje → rotor (inercia, rozamiento) → fem con la forma de onda real → bobinas (R(T), L) → puente de
diodos y condensador → controlador MPPT con sus límites → batería de plomo-ácido → inversor con
pérdidas y desconexión por baja tensión. Las bobinas se calientan con las pérdidas.

Las dinámicas lentas (estado de carga, polarización de la batería y temperatura) avanzan
``factor_tiempo`` veces más rápido que la mecánica, para poder observarlas en pantalla.

``visualizador_3d/js/modelo/dinamica.js`` replica esta clase operación por operación.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from generador_axial.dominio import DisenoGenerador
from generador_axial.dominio import dinamica as dn
from generador_axial.dominio.realista import ParametrosRealistas

SEGUNDOS_POR_MES = 30 * 86400


@dataclass(frozen=True)
class EntradasDinamicas:
    """Lo que el usuario puede cambiar mientras la simulación corre."""

    par_motriz_nm: float
    potencia_carga_ac_w: float
    inversor_encendido: bool
    temperatura_ambiente_c: float
    factor_tiempo: float
    entrehierro_m: float
    espiras_por_bobina: int
    remanencia_t: float
    capacitancia_filtro_f: float


@dataclass(frozen=True)
class InstanteDinamico:
    """Magnitudes del sistema en un instante (las potencias son valores medios en un ciclo eléctrico)."""

    tiempo_s: float
    rpm: float
    angulo_rad: float
    frecuencia_hz: float
    campo_medio_t: float
    remanencia_efectiva_t: float
    resistencia_ohm: float
    reactancia_ohm: float
    fem_rms_v: float
    fem_pico_v: float
    tension_bornes_rms_v: float
    tension_dc_v: float
    rizado_v: float
    corriente_generador_a: float
    par_motriz_nm: float
    par_electromagnetico_nm: float
    par_rozamiento_nm: float
    potencia_eje_w: float
    potencia_electromagnetica_w: float
    perdidas_cobre_w: float
    perdidas_diodos_w: float
    perdidas_foucault_w: float
    perdidas_rozamiento_w: float
    potencia_dc_w: float
    potencia_hacia_bateria_w: float
    etapa_carga: str
    soc: float
    tension_bateria_v: float
    corriente_carga_a: float
    corriente_descarga_a: float
    corriente_neta_a: float
    inversor_activo: bool
    corte_baja_tension: bool
    potencia_ac_w: float
    potencia_entrada_inversor_w: float
    temperatura_bobinas_c: float
    corriente_led_a: float
    salida_dc_segura: bool
    sobretemperatura: bool


class SimulacionDinamica:
    def __init__(self, diseno: DisenoGenerador, parametros: ParametrosRealistas | None = None) -> None:
        if diseno.bateria is None or diseno.controlador_carga is None or diseno.inversor is None:
            raise ValueError("La simulación realista necesita batería, controlador de carga e inversor en el diseño.")
        self.diseno = diseno
        self.p = parametros or ParametrosRealistas()
        integracion = self.p.integracion
        self.perfil = dn.perfil_de_flujo(diseno, integracion.puntos_radiales, integracion.muestras_perfil)
        self.momento_inercia = dn.momento_de_inercia_rotor(diseno, self.p.materiales)

        bobina = diseno.estator.bobina
        self._radio_medio_bobina = (bobina.diametro_interior_m + bobina.diametro_exterior_m) / 4
        self._profundidad_bobina = (bobina.diametro_exterior_m - bobina.diametro_interior_m) / 2
        radio_estator = diseno.mecanica.diametro_disco_estator_m / 2
        self._area_disipacion = 2 * math.pi * radio_estator**2
        self._area_iman = diseno.rotor.iman.area_cara_m2
        self._fraccion_expuesta = self._area_iman / (math.pi * (bobina.diametro_exterior_m / 2) ** 2)

        self.tiempo_s = 0.0
        self.omega = 0.0
        self.angulo = 0.0
        self.soc = diseno.bateria.soc_inicial
        self.tension_polarizacion = 0.0
        self.temperatura_bobinas = self.p.termico.temperatura_ambiente_c
        self.inversor_habilitado = True

    def entradas_por_defecto(self) -> EntradasDinamicas:
        d = self.diseno
        return EntradasDinamicas(
            par_motriz_nm=self.p.motriz.par_inicial_nm,
            potencia_carga_ac_w=15.0,
            inversor_encendido=True,
            temperatura_ambiente_c=self.p.termico.temperatura_ambiente_c,
            factor_tiempo=50.0,
            entrehierro_m=d.entrehierro_m,
            espiras_por_bobina=d.estator.bobina.espiras,
            remanencia_t=d.rotor.iman.remanencia_t,
            capacitancia_filtro_f=d.rectificador.capacitancia_filtro_f,
        )

    # ------------------------------------------------------------ evaluación instantánea
    def _evaluar(self, e: EntradasDinamicas, omega: float, h_lento: float = 0.0) -> dict:
        """Magnitudes con el estado actual; ``h_lento`` > 0 anticipa la polarización al final del paso (implícito)."""
        d, p = self.diseno, self.p
        termico, bat, ctrl, inv = p.termico, p.bateria, d.controlador_carga, d.inversor
        iman, bobina, alambre = d.rotor.iman, d.estator.bobina, d.estator.bobina.alambre
        perfil, iteraciones = self.perfil, p.integracion.iteraciones_biseccion

        remanencia = e.remanencia_t * (1 + termico.coeficiente_remanencia_1_k
                                       * (e.temperatura_ambiente_c - termico.temperatura_referencia_c))
        primitiva = lambda z: math.hypot(z + iman.espesor_m, iman.radio_m) - math.hypot(z, iman.radio_m)  # noqa: E731
        campo = 0.5 * remanencia * (primitiva(e.entrehierro_m + bobina.altura_m) - primitiva(e.entrehierro_m)) / bobina.altura_m
        espiras_totales = d.estator.numero_bobinas * e.espiras_por_bobina
        longitud_hilo = espiras_totales * bobina.longitud_media_espira_m
        factor_termico = 1 + termico.coeficiente_cobre_1_k * (self.temperatura_bobinas - termico.temperatura_referencia_c)
        resistividad = alambre.resistividad_ohm_m * factor_termico
        resistencia = resistividad * longitud_hilo / alambre.area_cobre_m2
        inductancia = d.estator.numero_bobinas * dn.inductancia_bobina_h(
            e.espiras_por_bobina, self._radio_medio_bobina, bobina.altura_m, self._profundidad_bobina
        )

        omega_e = d.rotor.pares_de_polos * omega
        frecuencia = omega_e / (2 * math.pi)
        fem_rms = espiras_totales * campo * self._area_iman * omega_e * perfil.rms_derivada
        fem_pico = fem_rms * perfil.factor_cresta
        reactancia = omega_e * inductancia
        caida = d.rectificador.caida_total_v
        capacitancia = e.capacitancia_filtro_f

        retencion = math.exp(-h_lento / bat.constante_tiempo_polarizacion_s)
        fem_bateria = dn.tension_reposo(bat, self.soc) + self.tension_polarizacion * retencion
        resistencia_carga = bat.resistencia_ohmica_ohm + dn.resistencia_polarizacion(bat, self.soc, 1.0) * (1 - retencion)
        resistencia_descarga = bat.resistencia_ohmica_ohm + bat.resistencia_polarizacion_ohm * (1 - retencion)
        inversor_activo = e.inversor_encendido and self.inversor_habilitado
        potencia_inversor = (
            dn.potencia_entrada_inversor(e.potencia_carga_ac_w, inv.potencia_nominal_w, inv.eficiencia,
                                         p.inversor.potencia_vacio_w)
            if inversor_activo else 0.0
        )
        potencia_autoconsumo = p.controlador.consumo_propio_a * fem_bateria

        def tension_dc(corriente: float) -> float:
            bornes = dn.tension_bornes_rms(fem_rms, resistencia, reactancia, corriente)
            rizado = dn.rizado_pico_a_pico(corriente, frecuencia, capacitancia)
            return dn.tension_dc_media(bornes, perfil.factor_cresta, perfil.factor_media, caida, rizado)

        def potencia(corriente: float) -> float:
            return dn.potencia_dc(fem_rms, resistencia, reactancia, caida, corriente)

        corriente_operacion = 0.0
        if fem_pico - caida >= ctrl.tension_minima_arranque_v and fem_rms > 0:
            corriente_maxima = fem_rms / math.hypot(resistencia, reactancia)
            pendiente = lambda i: dn.derivada_potencia_dc(fem_rms, resistencia, reactancia, caida, i)  # noqa: E731
            if pendiente(0.0) > 0:
                corriente_operacion = dn.biseccion(pendiente, 0.0, corriente_maxima, iteraciones)
                if tension_dc(corriente_operacion) < ctrl.tension_minima_arranque_v:
                    corriente_operacion = dn.biseccion(
                        lambda i: tension_dc(i) - ctrl.tension_minima_arranque_v, 0.0, corriente_operacion, iteraciones
                    )
        potencia_salida_disponible = ctrl.eficiencia * max(0.0, potencia(corriente_operacion))

        flotando = self.soc >= bat.soc_flotacion
        tension_consigna = ctrl.tension_flotacion_v if flotando else ctrl.tension_corte_absorcion_v
        corriente_neta_limite = (tension_consigna - fem_bateria) / (
            resistencia_carga if tension_consigna >= fem_bateria else resistencia_descarga
        )
        resistencia_limite = resistencia_carga if corriente_neta_limite >= 0 else resistencia_descarga
        potencia_neta_limite = corriente_neta_limite * (fem_bateria + resistencia_limite * corriente_neta_limite)
        limite_tension = max(0.0, potencia_neta_limite + potencia_inversor + potencia_autoconsumo)
        limite_corriente = ctrl.corriente_maxima_salida_a * fem_bateria
        potencia_salida = min(potencia_salida_disponible, limite_tension, limite_corriente)

        if potencia_salida_disponible <= 0:
            etapa = "sin generación"
        elif potencia_salida < potencia_salida_disponible:
            if potencia_salida == limite_corriente:
                etapa = "corriente máxima"
            else:
                etapa = "flotación" if flotando else "absorción"
        else:
            etapa = "mppt"

        corriente_generador = corriente_operacion
        if potencia_salida < potencia_salida_disponible:
            potencia_requerida = potencia_salida / ctrl.eficiencia
            corriente_generador = dn.biseccion(
                lambda i: potencia_requerida - potencia(i), 0.0, corriente_operacion, iteraciones
            )

        bornes = dn.tension_bornes_rms(fem_rms, resistencia, reactancia, corriente_generador)
        rizado = dn.rizado_pico_a_pico(corriente_generador, frecuencia, capacitancia)
        tension_bus = dn.tension_dc_media(bornes, perfil.factor_cresta, perfil.factor_media, caida, rizado)
        tension_interna = math.sqrt(max(0.0, fem_rms**2 - (reactancia * corriente_generador) ** 2))
        potencia_em = corriente_generador * tension_interna
        perdidas_cobre = resistencia * corriente_generador**2
        perdidas_diodos = caida * dn.FACTOR_CORRIENTE_MEDIA * corriente_generador
        potencia_bus = potencia_em - perdidas_cobre - perdidas_diodos
        potencia_bateria = ctrl.eficiencia * potencia_bus if potencia_salida_disponible > 0 else 0.0
        volumen_cobre = longitud_hilo * alambre.area_cobre_m2
        perdidas_foucault = dn.perdidas_foucault_w(
            volumen_cobre, self._fraccion_expuesta, omega_e, campo, alambre.diametro_cobre_m, resistividad
        )

        motriz, roz = p.motriz, p.perdidas
        omega_vacio = 2 * math.pi * motriz.velocidad_vacio_rpm / 60
        par_motriz = e.par_motriz_nm * max(0.0, 1 - omega / omega_vacio)
        par_em = (potencia_em + perdidas_foucault) / omega if omega > 0 else 0.0
        par_rozamiento = (
            roz.par_coulomb_nm + roz.coeficiente_viscoso_nm_s * omega + roz.coeficiente_ventilacion_nm_s2 * omega**2
            if omega > 0 else 0.0
        )

        potencia_neta = potencia_bateria - potencia_inversor - potencia_autoconsumo
        resistencia_bateria = resistencia_carga if potencia_neta >= 0 else resistencia_descarga
        corriente_neta = dn.corriente_para_potencia(fem_bateria, resistencia_bateria, potencia_neta)
        tension_bateria = fem_bateria + resistencia_bateria * corriente_neta

        led = d.indicador
        corriente_led = max(0.0, tension_bus - led.caida_led_v) / led.resistencia_ohm
        salida_dc_segura = (
            tension_bus < 0.8 * d.rectificador.tension_nominal_condensador_v
            and corriente_led < led.corriente_maxima_led_a
            and corriente_led**2 * led.resistencia_ohm < led.potencia_nominal_resistencia_w
        )

        return {
            "campo": campo, "remanencia": remanencia, "resistencia": resistencia, "reactancia": reactancia,
            "frecuencia": frecuencia, "fem_rms": fem_rms, "fem_pico": fem_pico, "bornes": bornes,
            "tension_bus": tension_bus, "rizado": rizado, "corriente_generador": corriente_generador,
            "par_motriz": par_motriz, "par_em": par_em, "par_rozamiento": par_rozamiento,
            "potencia_em": potencia_em, "perdidas_cobre": perdidas_cobre, "perdidas_diodos": perdidas_diodos,
            "perdidas_foucault": perdidas_foucault, "potencia_bus": potencia_bus, "potencia_bateria": potencia_bateria,
            "etapa": etapa, "tension_bateria": tension_bateria, "corriente_neta": corriente_neta,
            "corriente_carga": potencia_bateria / tension_bateria,
            "corriente_descarga": (potencia_inversor + potencia_autoconsumo) / tension_bateria,
            "inversor_activo": inversor_activo, "potencia_inversor": potencia_inversor,
            "corriente_led": corriente_led, "salida_dc_segura": salida_dc_segura,
        }

    # ------------------------------------------------------------ integración temporal
    def avanzar(self, dt_s: float, e: EntradasDinamicas) -> InstanteDinamico:
        """Avanza ``dt_s`` segundos en subpasos de como máximo ``paso_maximo_s``."""
        if dt_s > 0:
            subpasos = math.ceil(dt_s / self.p.integracion.paso_maximo_s - 1e-9)
            h = dt_s / subpasos
            for _ in range(subpasos):
                self._subpaso(h, e)
        return self.instantanea(e)

    def _subpaso(self, h: float, e: EntradasDinamicas) -> None:
        p, bat = self.p, self.p.bateria
        h_lento = h * e.factor_tiempo
        r = self._evaluar(e, self.omega, h_lento)

        par_neto = r["par_motriz"] - r["par_em"]
        if self.omega <= 0:
            omega = h * (par_neto - p.perdidas.par_coulomb_nm) / self.momento_inercia if par_neto > p.perdidas.par_coulomb_nm else 0.0
        else:
            omega = max(0.0, self.omega + h * (par_neto - r["par_rozamiento"]) / self.momento_inercia)
        self.omega = omega
        self.angulo = (self.angulo + omega * h) % (2 * math.pi)

        corriente = r["corriente_neta"]
        vp_final = dn.resistencia_polarizacion(bat, self.soc, corriente) * corriente
        self.tension_polarizacion = vp_final + (self.tension_polarizacion - vp_final) * math.exp(
            -h_lento / bat.constante_tiempo_polarizacion_s
        )

        capacidad_c = self.diseno.bateria.capacidad_ah * 3600
        if corriente >= 0:
            self.soc += dn.eficiencia_coulomb(bat, self.soc) * corriente * h_lento / capacidad_c
        else:
            self.soc -= dn.corriente_efectiva_peukert(bat, self.diseno.bateria.capacidad_ah, -corriente) * h_lento / capacidad_c
        self.soc -= bat.autodescarga_mensual * h_lento / SEGUNDOS_POR_MES
        self.soc = min(1.0, max(0.0, self.soc))

        termico = p.termico
        conductancia = (termico.conveccion_natural_w_m2k + termico.conveccion_forzada_w_m2k_por_rad_s * omega) * self._area_disipacion
        temperatura_final = e.temperatura_ambiente_c + (r["perdidas_cobre"] + r["perdidas_foucault"]) / conductancia
        self.temperatura_bobinas = temperatura_final + (self.temperatura_bobinas - temperatura_final) * math.exp(
            -h_lento * conductancia / termico.capacidad_termica_j_k
        )

        if self.inversor_habilitado and r["tension_bateria"] < p.inversor.tension_corte_v:
            self.inversor_habilitado = False
        elif not self.inversor_habilitado and r["tension_bateria"] >= p.inversor.tension_reconexion_v:
            self.inversor_habilitado = True
        self.tiempo_s += h

    def instantanea(self, e: EntradasDinamicas) -> InstanteDinamico:
        r = self._evaluar(e, self.omega)
        return InstanteDinamico(
            tiempo_s=self.tiempo_s,
            rpm=self.omega * 60 / (2 * math.pi),
            angulo_rad=self.angulo,
            frecuencia_hz=r["frecuencia"],
            campo_medio_t=r["campo"],
            remanencia_efectiva_t=r["remanencia"],
            resistencia_ohm=r["resistencia"],
            reactancia_ohm=r["reactancia"],
            fem_rms_v=r["fem_rms"],
            fem_pico_v=r["fem_pico"],
            tension_bornes_rms_v=r["bornes"],
            tension_dc_v=r["tension_bus"],
            rizado_v=r["rizado"],
            corriente_generador_a=r["corriente_generador"],
            par_motriz_nm=r["par_motriz"],
            par_electromagnetico_nm=r["par_em"],
            par_rozamiento_nm=r["par_rozamiento"],
            potencia_eje_w=r["par_motriz"] * self.omega,
            potencia_electromagnetica_w=r["potencia_em"],
            perdidas_cobre_w=r["perdidas_cobre"],
            perdidas_diodos_w=r["perdidas_diodos"],
            perdidas_foucault_w=r["perdidas_foucault"],
            perdidas_rozamiento_w=r["par_rozamiento"] * self.omega,
            potencia_dc_w=r["potencia_bus"],
            potencia_hacia_bateria_w=r["potencia_bateria"],
            etapa_carga=r["etapa"],
            soc=self.soc,
            tension_bateria_v=r["tension_bateria"],
            corriente_carga_a=r["corriente_carga"],
            corriente_descarga_a=r["corriente_descarga"],
            corriente_neta_a=r["corriente_neta"],
            inversor_activo=r["inversor_activo"],
            corte_baja_tension=not self.inversor_habilitado,
            potencia_ac_w=e.potencia_carga_ac_w if r["inversor_activo"] else 0.0,
            potencia_entrada_inversor_w=r["potencia_inversor"],
            temperatura_bobinas_c=self.temperatura_bobinas,
            corriente_led_a=r["corriente_led"],
            salida_dc_segura=r["salida_dc_segura"],
            sobretemperatura=self.temperatura_bobinas > self.p.termico.temperatura_maxima_pla_c,
        )

    def simular(self, e: EntradasDinamicas, duracion_s: float, paso_s: float = 0.05) -> list[InstanteDinamico]:
        """Serie temporal con entradas constantes (incluye el instante inicial)."""
        serie = [self.instantanea(e)]
        for _ in range(int(round(duracion_s / paso_s))):
            serie.append(self.avanzar(paso_s, e))
        return serie

    def con_entradas(self, **cambios) -> EntradasDinamicas:
        return replace(self.entradas_por_defecto(), **cambios)
