"""Gráficas concretas del generador."""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from generador_axial.aplicacion import SimuladorGenerador
from generador_axial.configuracion import EscenarioDeAnalisis
from generador_axial.infraestructura.graficas.base import ESTILO_REJILLA, Grafica

MM_POR_M = 1e3


class GraficaCampoVsDistancia(Grafica):
    nombre_archivo = "01_campo_magnetico_vs_distancia.png"

    def dibujar(self, figura: Figure) -> None:
        sim, diseno = self.simulador, self.diseno
        z_mm = np.linspace(0.0, self.escenario.distancia_maxima_campo_m * MM_POR_M, 500)
        campo = sim.campo_axial(z_mm / MM_POR_M)
        gap_mm = diseno.entrehierro_m * MM_POR_M
        altura_mm = diseno.estator.bobina.altura_m * MM_POR_M

        ejes = figura.add_subplot()
        ejes.plot(z_mm, campo, color="#d32f2f", linewidth=2.5, label=r"$B_z(z)$ en el eje del imán")
        ejes.axvspan(gap_mm, gap_mm + altura_mm, color="#bbdefb", alpha=0.5,
                     label=f"Espesor de la bobina ({gap_mm:.1f} a {gap_mm + altura_mm:.1f} mm)")
        ejes.hlines(sim.campo_medio_bobina_t, gap_mm, gap_mm + altura_mm, color="#0d47a1", linewidth=2.2,
                    label=rf"$\bar{{B}}_z$ en la bobina = {sim.campo_medio_bobina_t:.3f} T")
        ejes.scatter([gap_mm], [sim.campo_en_cara_bobina_t], color="#1976d2", s=60, zorder=5,
                     label=f"Cara de la bobina (g = {gap_mm:.1f} mm): {sim.campo_en_cara_bobina_t:.3f} T")

        ejes.set_title(r"Decaimiento de $B_z$ con la distancia al imán", fontsize=13, fontweight="bold")
        ejes.set_xlabel("Distancia axial desde la cara del imán [mm]", fontsize=11)
        ejes.set_ylabel(r"Densidad de flujo $B_z$ [T]", fontsize=11)
        ejes.grid(True, **ESTILO_REJILLA)
        ejes.legend(fontsize=9, loc="upper right")


class GraficaFlujoYFem(Grafica):
    nombre_archivo = "02_flujo_y_voltaje_inducido_faraday.png"
    tamano_pulgadas = (9, 6)

    def dibujar(self, figura: Figure) -> None:
        rpm = self.escenario.rpm_forma_de_onda
        onda = self.simulador.forma_de_onda(rpm)
        punto = self.simulador.punto_de_operacion(rpm)
        v_pico, v_rms = float(punto.tension_pico_v), float(punto.tension_rms_v)
        t_ms = onda.tiempo_s * 1e3

        eje_flujo, eje_fem = figura.subplots(2, 1, sharex=True)
        eje_flujo.plot(t_ms, onda.flujo_por_espira_wb * 1e6, color="#0288d1", linewidth=2,
                       label=r"$\Phi(t) = \Phi_{max}\cos(\omega_e t)$ por espira")
        eje_flujo.set_ylabel(r"Flujo $\Phi$ [$\mu$Wb]", fontsize=11)
        eje_flujo.set_title(
            f"Ley de Faraday a {rpm:.0f} RPM ($f_e$ = {float(punto.frecuencia_electrica_hz):.1f} Hz)",
            fontsize=13, fontweight="bold",
        )

        eje_fem.plot(t_ms, onda.fem_v, color="#e65100", linewidth=2.2,
                     label=r"$e(t) = -N_{total}\,d\Phi/dt$")
        eje_fem.axhline(v_rms, color="#4caf50", linestyle="--",
                        label=f"$\\pm V_{{RMS}}$ = {v_rms:.2f} V ($V_{{pico}}$ = {v_pico:.2f} V)")
        eje_fem.axhline(-v_rms, color="#4caf50", linestyle="--")
        eje_fem.set_xlabel("Tiempo [ms]", fontsize=11)
        eje_fem.set_ylabel("Tensión inducida [V]", fontsize=11)

        for ejes in (eje_flujo, eje_fem):
            ejes.grid(True, **ESTILO_REJILLA)
            ejes.legend(loc="upper right", fontsize=9)


class GraficaTensionVsRpm(Grafica):
    nombre_archivo = "03_voltaje_rms_vs_rpm.png"

    def dibujar(self, figura: Figure) -> None:
        esc = self.escenario
        rpm = np.linspace(esc.rpm_minima, esc.rpm_maxima, 200)
        punto = self.simulador.punto_de_operacion(rpm)

        polos = self.diseno.rotor.numero_polos

        ejes = figura.add_subplot()
        ejes.axvspan(*esc.rpm_giro_manual, color="#fff9c4", alpha=0.6, label="Zona de giro manual")
        ejes.plot(rpm, punto.tension_pico_v, color="#1565c0", linewidth=1.8, label="$V_{pico}$ (AC en vacío)")
        ejes.plot(rpm, punto.tension_rms_v, color="#2e7d32", linewidth=2.5, label="$V_{RMS}$ (AC en vacío)")
        ejes.plot(rpm, punto.tension_dc_v, color="#f57c00", linestyle="--", linewidth=2,
                  label=f"$V_{{DC}}$ rectificada ($V_{{pico}}$ − {self.diseno.rectificador.caida_total_v:.1f} V)")
        eje_frecuencia = ejes.secondary_xaxis(
            "top", functions=(lambda r: polos * r / 120, lambda f: 120 * f / polos)
        )

        ejes.set_title("Respuesta del generador vs. velocidad de giro", fontsize=13, fontweight="bold")
        ejes.set_xlabel("Velocidad de rotación [RPM]", fontsize=11)
        eje_frecuencia.set_xlabel(f"Frecuencia eléctrica $f_e = P\\cdot RPM/120$ [Hz]  (P = {polos})", fontsize=10)
        ejes.set_ylabel("Tensión [V]", fontsize=11)
        ejes.grid(True, **ESTILO_REJILLA)
        ejes.legend(loc="upper left", fontsize=9)


class GraficaPotenciaVsCarga(Grafica):
    nombre_archivo = "04_potencia_vs_resistencia_carga.png"

    def dibujar(self, figura: Figure) -> None:
        esc, sim = self.escenario, self.simulador
        rpm = esc.rpm_analisis_carga
        cargas = np.linspace(esc.carga_minima_ohm, esc.carga_maxima_ohm, 500)
        operacion = sim.operar_con_carga(rpm, cargas)
        optima = sim.operar_con_carga_adaptada(rpm)
        r_opt, p_max = float(optima.resistencia_carga_ohm), float(optima.potencia_carga_w)
        v_rms = float(sim.punto_de_operacion(rpm).tension_rms_v)

        ejes = figura.add_subplot()
        ejes.plot(cargas, operacion.potencia_carga_w, color="#c2185b", linewidth=2.5, label="Potencia en la carga $P_L(R_L)$")
        ejes.axvline(r_opt, color="#1976d2", linestyle="--", linewidth=1.8,
                     label=f"$R_L = R_{{int}}$ = {r_opt:.1f} Ω  →  $P_{{max}}$ = {p_max:.2f} W")
        ejes.scatter([r_opt], [p_max], color="#1976d2", s=80, zorder=5)

        ejes.set_title(f"Máxima transferencia de potencia a {rpm:.0f} RPM ($V_{{RMS}}$ = {v_rms:.2f} V)",
                       fontsize=13, fontweight="bold")
        ejes.set_xlabel("Resistencia de carga $R_L$ [Ω]", fontsize=11)
        ejes.set_ylabel("Potencia en la carga [W]", fontsize=11)
        ejes.grid(True, **ESTILO_REJILLA)
        ejes.legend(fontsize=10, loc="upper right")


class GraficaPotenciaYParVsRpm(Grafica):
    nombre_archivo = "05_potencia_y_par_lenz_vs_rpm.png"

    def dibujar(self, figura: Figure) -> None:
        esc, sim = self.escenario, self.simulador
        rpm = np.linspace(esc.rpm_minima, esc.rpm_maxima, 200)
        operacion = sim.operar_con_carga_adaptada(rpm)

        eje_p = figura.add_subplot()
        eje_t = eje_p.twinx()
        lineas = [
            *eje_p.plot(rpm, operacion.potencia_mecanica_w, color="#6a1b9a", linewidth=2.2,
                        label="Potencia mecánica requerida"),
            *eje_p.plot(rpm, operacion.potencia_carga_w, color="#c2185b", linestyle="--", linewidth=2,
                        label="Potencia útil en la carga"),
            *eje_t.plot(rpm, operacion.par_resistente_nm * 1e3, color="#00838f", linestyle=":", linewidth=2.2,
                        label="Par resistente de Lenz"),
        ]
        eje_p.set_title(f"Balance energético con carga adaptada ($R_L$ = {sim.resistencia_interna_ohm:.1f} Ω)",
                        fontsize=13, fontweight="bold")
        eje_p.set_xlabel("Velocidad de rotación [RPM]", fontsize=11)
        eje_p.set_ylabel("Potencia [W]", fontsize=11)
        eje_t.set_ylabel("Par resistente [mN·m]", fontsize=11, color="#00838f")
        eje_p.grid(True, **ESTILO_REJILLA)
        eje_p.legend(lineas, [l.get_label() for l in lineas], loc="upper left", fontsize=9)


class GraficaBalanceBateria(Grafica):
    nombre_archivo = "06_curva_carga_bateria.png"
    tamano_pulgadas = (9, 6)

    def dibujar(self, figura: Figure) -> None:
        esc, sim = self.escenario, self.simulador
        bateria = sim.bateria
        rpm = esc.rpm_microred

        eje_soc, eje_corriente = figura.subplots(2, 1, sharex=True)
        for potencia, color in zip(esc.potencias_carga_ac_w, ("#2e7d32", "#f9a825", "#c62828")):
            evolucion = sim.simular_bateria(rpm, potencia, esc.duracion_balance_bateria_h, paso_s=60)
            etiqueta = "Solo carga (inversor sin consumo)" if potencia == 0 else f"Carga AC de {potencia:.0f} W"
            eje_soc.plot(evolucion.tiempo_h, evolucion.soc * 100, color=color, linewidth=2.2, label=etiqueta)
            eje_corriente.plot(evolucion.tiempo_h, evolucion.corriente_neta_a, color=color, linewidth=2, label=etiqueta)

        eje_soc.axhline(bateria.soc_minimo_descarga * 100, color="#455a64", linestyle="--", linewidth=1.5,
                        label=f"Corte del inversor (SoC = {bateria.soc_minimo_descarga:.0%})")
        eje_soc.set_ylabel("Estado de carga [%]", fontsize=11)
        eje_soc.set_title(
            f"Batería {bateria.tension_nominal_v:.0f} V / {bateria.capacidad_ah:.0f} Ah con el generador a {rpm:.0f} RPM",
            fontsize=13, fontweight="bold",
        )
        eje_corriente.axhline(0, color="#455a64", linewidth=1)
        eje_corriente.set_ylabel("Corriente neta [A]\n(+ carga, − descarga)", fontsize=10)
        eje_corriente.set_xlabel("Tiempo [h]", fontsize=11)
        for ejes in (eje_soc, eje_corriente):
            ejes.grid(True, **ESTILO_REJILLA)
            ejes.legend(fontsize=8, loc="best")


class GraficaInversor(Grafica):
    nombre_archivo = "07_onda_inversor_110v_220v.png"
    tamano_pulgadas = (9, 6)

    def dibujar(self, figura: Figure) -> None:
        esc, sim = self.escenario, self.simulador
        eje_inv, eje_gen = figura.subplots(2, 1, sharex=True)

        for tension, color in zip(esc.tensiones_inversor_v, ("#0288d1", "#d81b60")):
            salida = sim.forma_de_onda_inversor(tension_rms_v=tension)
            eje_inv.plot(salida.tiempo_s * 1e3, salida.tension_ac_v, color=color, linewidth=2,
                         label=f"{tension:.0f} V RMS ($V_{{pico}}$ = {np.sqrt(2) * tension:.1f} V) a {salida.frecuencia_hz:.0f} Hz")
        eje_inv.set_ylabel("Salida del inversor [V]", fontsize=11)
        eje_inv.set_title("Salida del inversor (frecuencia fija) frente al generador (frecuencia variable)",
                          fontsize=12, fontweight="bold")

        punto = sim.punto_de_operacion(esc.rpm_microred)
        tiempo_s = salida.tiempo_s
        v_gen = float(punto.tension_pico_v) * np.sin(float(punto.velocidad_angular_electrica) * tiempo_s)
        eje_gen.plot(tiempo_s * 1e3, v_gen, color="#e65100", linewidth=2,
                     label=f"Generador a {esc.rpm_microred:.0f} RPM ($V_{{pico}}$ = {float(punto.tension_pico_v):.1f} V, "
                           f"$f_e$ = {float(punto.frecuencia_electrica_hz):.0f} Hz)")
        eje_gen.set_ylabel("Generador [V]", fontsize=11)
        eje_gen.set_xlabel("Tiempo [ms]", fontsize=11)
        for ejes in (eje_inv, eje_gen):
            ejes.grid(True, **ESTILO_REJILLA)
            ejes.legend(loc="upper right", fontsize=8)


class GraficaBalancePotenciaVsRpm(Grafica):
    nombre_archivo = "08_balance_potencia_vs_rpm.png"

    def dibujar(self, figura: Figure) -> None:
        esc, sim = self.escenario, self.simulador
        rpm = np.linspace(0, esc.rpm_maxima, 241)
        hacia_bateria = [sim.balance_microred(r).potencia_hacia_bateria_w for r in rpm]

        ejes = figura.add_subplot()
        ejes.plot(rpm, hacia_bateria, color="#2e7d32", linewidth=2.5, label="Potencia que el generador entrega a la batería")
        for potencia, color in zip(esc.potencias_carga_ac_w, ("#90a4ae", "#f9a825", "#c62828")):
            if potencia == 0:
                continue
            consumo = sim.inversor.potencia_entrada_w(potencia)
            equilibrio = sim.rpm_de_equilibrio(potencia)
            texto = f"{equilibrio:.0f} RPM" if equilibrio <= esc.rpm_maxima else f"{equilibrio:.0f} RPM, fuera de rango"
            ejes.axhline(consumo, color=color, linestyle="--", linewidth=1.8,
                         label=f"Consumo del inversor con {potencia:.0f} W AC ({consumo:.1f} W) → equilibrio a {texto}")
            if equilibrio <= esc.rpm_maxima:
                ejes.scatter([equilibrio], [consumo], color=color, s=60, zorder=5)

        ejes.set_title("¿Puede el generador sostener la carga AC?", fontsize=13, fontweight="bold")
        ejes.set_xlabel("Velocidad de rotación [RPM]", fontsize=11)
        ejes.set_ylabel("Potencia en el nodo de la batería [W]", fontsize=11)
        ejes.set_ylim(0, None)
        ejes.grid(True, **ESTILO_REJILLA)
        ejes.legend(fontsize=8, loc="center left")


def graficas_estandar(simulador: SimuladorGenerador, escenario: EscenarioDeAnalisis) -> list[Grafica]:
    clases = (
        GraficaCampoVsDistancia,
        GraficaFlujoYFem,
        GraficaTensionVsRpm,
        GraficaPotenciaVsCarga,
        GraficaPotenciaYParVsRpm,
        GraficaBalanceBateria,
        GraficaInversor,
        GraficaBalancePotenciaVsRpm,
    )
    return [clase(simulador, escenario) for clase in clases]
