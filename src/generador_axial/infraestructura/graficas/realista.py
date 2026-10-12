"""Gráficas del modelo dinámico realista (Documento 5)."""

from __future__ import annotations

import math

import numpy as np
from matplotlib.figure import Figure

from generador_axial.aplicacion import SimulacionDinamica
from generador_axial.aplicacion.escenarios_dinamicos import ciclo_de_carga, impulso_y_frenado, regimen_permanente
from generador_axial.infraestructura.graficas.base import ESTILO_REJILLA, Grafica
COLORES_ETAPA = {
    "mppt": "#e3f2fd",
    "absorción": "#fff3e0",
    "flotación": "#e8f5e9",
    "corriente máxima": "#fce4ec",
}


class GraficaOndaReal(Grafica):
    nombre_archivo = "09_onda_real_vs_senoidal.png"
    tamano_pulgadas = (9, 6)

    def dibujar(self, figura: Figure) -> None:
        perfil = SimulacionDinamica(self.diseno).perfil
        muestras = len(perfil.flujo)
        theta = np.arange(muestras) * 360.0 / muestras
        k = self.diseno.factor_acoplamiento
        seno_equivalente = -math.sqrt(2) * perfil.rms_derivada * np.sin(np.radians(theta))

        eje_flujo, eje_fem = figura.subplots(2, 1, sharex=True)
        eje_flujo.plot(theta, perfil.flujo, color="#0288d1", linewidth=2.2,
                       label=rf"Solape imán–espira: $\phi_{{max}}$ = {perfil.flujo_maximo:.3f}")
        eje_flujo.plot(theta, k * np.cos(np.radians(theta)), color="#90a4ae", linestyle="--", linewidth=1.6,
                       label=rf"Modelo ideal $k\cos\theta_e$ ($k$ = {k:.2f})")
        eje_flujo.set_ylabel(r"$\phi = \Phi/(\bar B_z A_{imán})$", fontsize=11)
        eje_flujo.set_title("Forma de onda real del flujo y de la fem (una vuelta eléctrica)",
                            fontsize=13, fontweight="bold")

        eje_fem.plot(theta, -np.asarray(perfil.derivada), color="#e65100", linewidth=2.2,
                     label=rf"$-d\phi/d\theta_e$ real (factor de cresta {perfil.factor_cresta:.3f})")
        eje_fem.plot(theta, -seno_equivalente, color="#90a4ae", linestyle="--", linewidth=1.6,
                     label=r"Senoide de igual RMS (factor de cresta $\sqrt{2}$ = 1.414)")
        eje_fem.set_ylabel(r"fem normalizada $-d\phi/d\theta_e$", fontsize=11)
        eje_fem.set_xlabel(r"Ángulo eléctrico $\theta_e$ [°]", fontsize=11)
        for ejes in (eje_flujo, eje_fem):
            ejes.set_xlim(0, 360)
            ejes.grid(True, **ESTILO_REJILLA)
            ejes.legend(loc="upper right", fontsize=8)


class GraficaArranqueYFrenado(Grafica):
    nombre_archivo = "10_arranque_impulso_y_frenado.png"
    tamano_pulgadas = (9, 6.5)
    par_regimen_nm = 0.07
    duracion_arranque_s = 15.0
    duracion_frenado_s = 4.0
    paso_s = 0.05

    def dibujar(self, figura: Figure) -> None:
        eje_arranque, eje_impulso = figura.subplots(2, 1)

        simulacion = SimulacionDinamica(self.diseno)
        serie = simulacion.simular(simulacion.con_entradas(par_motriz_nm=self.par_regimen_nm), self.duracion_arranque_s)
        t = np.array([m.tiempo_s for m in serie])
        eje_potencia = eje_arranque.twinx()
        lineas = [
            *eje_arranque.plot(t, [m.rpm for m in serie], color="#1565c0", linewidth=2.2, label="Velocidad [RPM]"),
            *eje_potencia.plot(t, [m.potencia_eje_w for m in serie], color="#6a1b9a", linestyle=":", linewidth=1.8,
                               label="Potencia en el eje [W]"),
            *eje_potencia.plot(t, [m.potencia_hacia_bateria_w for m in serie], color="#2e7d32", linewidth=2,
                               label="Potencia hacia la batería [W]"),
        ]
        eje_arranque.set_title(
            f"Arranque desde reposo con {self.par_regimen_nm:.2f} N·m (régimen: {serie[-1].rpm:.0f} RPM)",
            fontsize=12, fontweight="bold",
        )
        eje_arranque.set_ylabel("RPM", fontsize=10)
        eje_potencia.set_ylabel("Potencia [W]", fontsize=10)
        eje_arranque.legend(lineas, [l.get_label() for l in lineas], loc="center right", fontsize=8)

        motriz = SimulacionDinamica(self.diseno).p.motriz
        casos = (
            (dict(inversor_encendido=False, soc=1.0), "#90a4ae", "Batería llena e inversor apagado (poca corriente)"),
            (dict(inversor_encendido=True), "#c62828", "Batería al 50 % con 15 W de carga (frenado de Lenz)"),
        )
        for opciones, color, etiqueta in casos:
            respuesta = impulso_y_frenado(self.diseno, duracion_s=self.duracion_frenado_s, paso_s=self.paso_s, **opciones)
            eje_impulso.plot(respuesta.tiempo_s, respuesta.rpm, color=color, linewidth=2.2,
                             label=f"{etiqueta}: pico {respuesta.rpm_pico:.0f} RPM")
        eje_impulso.axvspan(0, motriz.duracion_impulso_s, color="#fff9c4", alpha=0.7,
                            label=f"Impulso de {motriz.par_impulso_nm:.2f} N·m durante {motriz.duracion_impulso_s:.1f} s")
        eje_impulso.set_title("Impulso con la mano y frenado por rozamiento y por ley de Lenz", fontsize=12, fontweight="bold")
        eje_impulso.set_xlabel("Tiempo [s]", fontsize=10)
        eje_impulso.set_ylabel("RPM", fontsize=10)
        eje_impulso.legend(fontsize=8, loc="upper right")
        for ejes in (eje_arranque, eje_impulso):
            ejes.grid(True, **ESTILO_REJILLA)


class GraficaRegimenVsPar(Grafica):
    nombre_archivo = "11_regimen_vs_par_motriz.png"
    tamano_pulgadas = (9, 6)

    def dibujar(self, figura: Figure) -> None:
        motriz = SimulacionDinamica(self.diseno).p.motriz
        pares = np.linspace(0.01, motriz.par_maximo_nm, 15)
        regimen = [regimen_permanente(self.diseno, float(par)) for par in pares]
        eje_rpm, eje_potencia = figura.subplots(2, 1, sharex=True)

        eje_rpm.plot(pares, [m.rpm for m in regimen], color="#1565c0", linewidth=2.2, marker="o", markersize=4,
                     label="Velocidad de régimen")
        eje_rpm.axhline(motriz.velocidad_vacio_rpm, color="#90a4ae", linestyle="--",
                        label=f"Velocidad en vacío de la fuente ({motriz.velocidad_vacio_rpm:.0f} RPM)")
        eje_rpm.set_ylabel("RPM", fontsize=10)
        eje_rpm.set_title("Régimen permanente según el par motriz (inversor apagado)", fontsize=12, fontweight="bold")

        eje_eficiencia = eje_potencia.twinx()
        lineas = [
            *eje_potencia.plot(pares, [m.potencia_eje_w for m in regimen], color="#6a1b9a", linewidth=2,
                               label="Potencia en el eje"),
            *eje_potencia.plot(pares, [m.potencia_hacia_bateria_w for m in regimen], color="#2e7d32", linewidth=2.2,
                               label="Potencia hacia la batería"),
            *eje_eficiencia.plot(pares, [100 * m.potencia_hacia_bateria_w / m.potencia_eje_w if m.potencia_eje_w else 0
                                         for m in regimen], color="#ef6c00", linestyle="--", linewidth=1.8,
                                 label="Eficiencia eje → batería [%]"),
        ]
        eje_potencia.set_ylabel("Potencia [W]", fontsize=10)
        eje_eficiencia.set_ylabel("Eficiencia [%]", fontsize=10)
        eje_potencia.set_xlabel("Par de arranque de la fuente motriz [N·m]", fontsize=10)
        eje_potencia.legend(lineas, [l.get_label() for l in lineas], loc="upper left", fontsize=8)
        eje_rpm.legend(fontsize=8, loc="lower right")
        for ejes in (eje_rpm, eje_potencia):
            ejes.grid(True, **ESTILO_REJILLA)


class GraficaCicloDeCarga(Grafica):
    nombre_archivo = "12_ciclo_de_carga_bateria.png"
    tamano_pulgadas = (9, 6.5)

    def dibujar(self, figura: Figure) -> None:
        ciclo = ciclo_de_carga(self.diseno)
        serie, factor = ciclo.serie, ciclo.factor_tiempo
        horas = np.array([ciclo.horas(m) for m in serie])
        eje_tension, eje_corriente = figura.subplots(2, 1, sharex=True)

        eje_soc = eje_tension.twinx()
        lineas = [
            *eje_tension.plot(horas, [m.tension_bateria_v for m in serie], color="#c62828", linewidth=2.2,
                              label="Tensión en bornes [V]"),
            *eje_soc.plot(horas, [100 * m.soc for m in serie], color="#1565c0", linewidth=2, label="Estado de carga [%]"),
        ]
        eje_tension.set_ylabel("Tensión [V]", fontsize=10)
        eje_soc.set_ylabel("SoC [%]", fontsize=10)
        eje_tension.set_title("Ciclo de carga de la batería de plomo-ácido con 0.30 N·m", fontsize=12, fontweight="bold")
        eje_tension.legend(lineas, [l.get_label() for l in lineas], loc="center right", fontsize=8)

        eje_corriente.plot(horas, [1e3 * m.corriente_neta_a for m in serie], color="#2e7d32", linewidth=2.2,
                           label="Corriente hacia la batería [mA]")
        eje_corriente.set_ylabel("Corriente [mA]", fontsize=10)
        eje_corriente.set_xlabel(f"Tiempo [h] (tiempo acelerado ×{factor:.0f})", fontsize=10)

        inicio, etapa = 0, serie[0].etapa_carga
        for i, m in enumerate([*serie[1:], None], start=1):
            if m is None or m.etapa_carga != etapa:
                if etapa in COLORES_ETAPA:
                    for ejes in (eje_tension, eje_corriente):
                        ejes.axvspan(horas[inicio], horas[i - 1], color=COLORES_ETAPA[etapa], zorder=0)
                    eje_corriente.text((horas[inicio] + horas[i - 1]) / 2, 0.92, etapa.upper(), ha="center",
                                       transform=eje_corriente.get_xaxis_transform(), fontsize=8, color="#455a64")
                if m is not None:
                    inicio, etapa = i, m.etapa_carga
        eje_corriente.legend(fontsize=8, loc="center right")
        for ejes in (eje_tension, eje_corriente):
            ejes.grid(True, **ESTILO_REJILLA)


def graficas_realistas(simulador, escenario) -> list[Grafica]:
    clases = (GraficaOndaReal, GraficaArranqueYFrenado, GraficaRegimenVsPar, GraficaCicloDeCarga)
    return [clase(simulador, escenario) for clase in clases]
