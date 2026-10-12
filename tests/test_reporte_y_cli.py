import re

import pytest

from generador_axial.aplicacion import Magnitud, generar_reporte
from generador_axial.infraestructura.latex import ExportadorLatex
from generador_axial.presentacion.cli import main


def test_reporte_es_coherente_con_el_simulador(simulador, escenario):
    reporte = generar_reporte(simulador, escenario)
    punto = simulador.punto_de_operacion(escenario.rpm_forma_de_onda)
    assert reporte.valor("TensionPicoRef") == pytest.approx(float(punto.tension_pico_v))
    assert reporte.valor("Eficiencia") == pytest.approx(50)
    assert len(reporte.ensayos.rpm) == len(escenario.rpm_ensayos)


def test_claves_del_reporte_son_macros_latex_validas():
    with pytest.raises(ValueError):
        Magnitud("Valor2", 1.0)


def test_exportador_latex(simulador, escenario, tmp_path):
    valores, tabla = ExportadorLatex(tmp_path).exportar(generar_reporte(simulador, escenario))
    macros = re.findall(r"\\newcommand\{\\Val([A-Za-z]+)\}", valores.read_text(encoding="utf-8"))
    assert len(macros) == len(set(macros))
    assert "ResistenciaInterna" in macros
    assert tabla.read_text(encoding="utf-8").count(r"\\") == len(escenario.rpm_ensayos)


@pytest.mark.parametrize("comando", ["simular", "cad", "reporte"])
def test_cli_genera_archivos(comando, tmp_path, capsys):
    main([comando, "--salida", str(tmp_path)])
    assert any(tmp_path.iterdir())
    assert "->" in capsys.readouterr().out
