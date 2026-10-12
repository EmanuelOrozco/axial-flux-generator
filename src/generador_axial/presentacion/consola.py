"""Formateo de resultados para la terminal."""

from __future__ import annotations

from generador_axial.aplicacion import SimuladorGenerador
from generador_axial.configuracion import ESCENARIO_POR_DEFECTO

LINEA = "=" * 65


def resumen_del_diseno(simulador: SimuladorGenerador) -> str:
    d = simulador.diseno
    bobina = d.estator.bobina
    rpm = ESCENARIO_POR_DEFECTO.rpm_forma_de_onda
    punto = simulador.punto_de_operacion(rpm)
    gap_mm = d.entrehierro_m * 1e3
    return "\n".join(
        [
            LINEA,
            "SIMULACIÓN DE GENERADOR DE FLUJO AXIAL CON IMANES DE NEODIMIO",
            "Fundamentado en M. N. O. Sadiku, Elementos de Electromagnetismo",
            LINEA,
            f"Polos magnéticos (P): {d.rotor.numero_polos} ({d.rotor.pares_de_polos} pares de polos)",
            f"Bobinas: {d.estator.numero_bobinas} | Espiras por bobina: {bobina.espiras} "
            f"| Espiras totales en serie: {d.estator.espiras_totales}",
            f"Resistencia interna del estator: {d.estator.resistencia_interna_ohm:.2f} Ω "
            f"(ocupación de la ventana {bobina.factor_ocupacion:.0%})",
            f"Campo en la cara del imán (z = 0): {simulador.campo_en_cara_iman_t:.3f} T",
            f"Campo en la cara de la bobina (z = {gap_mm:.1f} mm): {simulador.campo_en_cara_bobina_t:.3f} T",
            f"Campo medio en el espesor de la bobina: {simulador.campo_medio_bobina_t:.3f} T",
            f"Flujo máximo por espira: {simulador.flujo_maximo_por_espira_wb * 1e6:.2f} µWb",
            f"A {rpm:.0f} RPM: f_e = {float(punto.frecuencia_electrica_hz):.1f} Hz, "
            f"V_pico = {float(punto.tension_pico_v):.2f} V, V_RMS = {float(punto.tension_rms_v):.2f} V, "
            f"V_DC = {float(punto.tension_dc_v):.2f} V",
            LINEA,
            *_resumen_microred(simulador),
        ]
    )


def _resumen_microred(simulador: SimuladorGenerador) -> list[str]:
    escenario = ESCENARIO_POR_DEFECTO
    rpm, potencia = escenario.rpm_microred, escenario.potencia_carga_ac_w
    balance = simulador.balance_microred(rpm, potencia)
    equilibrio = simulador.rpm_de_equilibrio(potencia)
    bateria, inversor = simulador.bateria, simulador.inversor
    return [
        f"MICRORRED: batería {bateria.tension_nominal_v:.0f} V / {bateria.capacidad_ah:.0f} Ah, "
        f"inversor {inversor.tension_salida_rms_v:.0f} V / {inversor.frecuencia_hz:.0f} Hz",
        f"A {rpm:.0f} RPM el generador entrega {balance.potencia_hacia_bateria_w:.2f} W a la batería; "
        f"una carga AC de {potencia:.0f} W consume {balance.potencia_entrada_inversor_w:.2f} W",
        f"Balance neto: {balance.potencia_neta_bateria_w:+.2f} W "
        f"(autonomía hasta el corte: {balance.autonomia_h:.2f} h)",
        f"Velocidad necesaria para sostener {potencia:.0f} W sin descargar la batería: {equilibrio:.0f} RPM",
        LINEA,
    ]
