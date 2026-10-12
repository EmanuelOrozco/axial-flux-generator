"""Exporta el reporte de cálculo como macros LaTeX que consumen los documentos PDF."""

from __future__ import annotations

from pathlib import Path

from generador_axial.aplicacion.reporte import ReporteDeCalculo

ENCABEZADO = "% Archivo generado automáticamente por `generador-axial reporte`. No editar a mano.\n"


class ExportadorLatex:
    def __init__(self, directorio: Path) -> None:
        self.directorio = directorio

    def exportar(self, reporte: ReporteDeCalculo) -> list[Path]:
        self.directorio.mkdir(parents=True, exist_ok=True)
        return [self._escribir_valores(reporte), self._escribir_tabla_ensayos(reporte)]

    def _escribir_valores(self, reporte: ReporteDeCalculo) -> Path:
        lineas = [ENCABEZADO]
        for magnitud in reporte.magnitudes:
            comentario = f"  % {magnitud.descripcion}" if magnitud.descripcion else ""
            lineas.append(f"\\newcommand{{\\Val{magnitud.clave}}}{{{magnitud.como_texto()}}}{comentario}\n")
        ruta = self.directorio / "valores.tex"
        ruta.write_text("".join(lineas), encoding="utf-8")
        return ruta

    def _escribir_tabla_ensayos(self, reporte: ReporteDeCalculo) -> Path:
        e = reporte.ensayos
        filas = [ENCABEZADO]
        for i, (rpm, fe, vp, vrms, vdc) in enumerate(
            zip(e.rpm, e.frecuencia_electrica_hz, e.tension_pico_v, e.tension_rms_v, e.tension_dc_v), start=1
        ):
            filas.append(
                f"{i} & {rpm:.0f} & {fe:.1f} & {vp:.2f} & {vrms:.2f} & {vdc:.2f} & & & \\\\\n"
            )
        ruta = self.directorio / "tabla_ensayos.tex"
        ruta.write_text("".join(filas), encoding="utf-8")
        return ruta
