import math
import struct

import pytest

from generador_axial.aplicacion import catalogo_de_piezas
from generador_axial.aplicacion.piezas import PlacaConAlojamientos, SolidoDeRevolucion
from generador_axial.infraestructura.cad import ExportadorStl, construir_malla


def volumen_analitico_mm3(geometria) -> float:
    if isinstance(geometria, SolidoDeRevolucion):
        perfil = [(r * 1e3, z * 1e3) for r, z in geometria.perfil_rz_m]
        aristas = zip(perfil, perfil[1:] + perfil[:1])
        return math.pi * sum((z2 - z1) * (r1**2 + r1 * r2 + r2**2) / 3 for (r1, z1), (r2, z2) in aristas)
    placa: PlacaConAlojamientos = geometria
    radio_ext, radio_int = placa.diametro_exterior_m / 2 * 1e3, placa.diametro_agujero_central_m / 2 * 1e3
    volumen = math.pi * (radio_ext**2 - radio_int**2) * placa.espesor_m * 1e3
    for a in placa.alojamientos:
        volumen -= math.pi * (a.diametro_m / 2 * 1e3) ** 2 * a.profundidad_m * 1e3
    return volumen


@pytest.mark.parametrize("indice", range(4))
def test_piezas_son_solidos_cerrados_con_el_volumen_correcto(diseno, indice):
    pieza = catalogo_de_piezas(diseno)[indice]
    malla = construir_malla(pieza.geometria, longitud_arista_mm=1.0)
    assert malla.es_hermetica(), pieza.nombre_archivo
    assert malla.volumen_con_signo() == pytest.approx(volumen_analitico_mm3(pieza.geometria), rel=5e-3)


def test_archivo_stl_binario_bien_formado(diseno, tmp_path):
    resultados = ExportadorStl(tmp_path, longitud_arista_mm=2.0).exportar(catalogo_de_piezas(diseno))
    for resultado in resultados:
        contenido = resultado.ruta.read_bytes()
        (facetas,) = struct.unpack("<I", contenido[80:84])
        assert facetas == resultado.facetas
        assert len(contenido) == 84 + 50 * facetas


def test_alojamientos_siguen_al_diseno(diseno):
    piezas = {p.nombre_archivo: p for p in catalogo_de_piezas(diseno)}
    rotor = piezas["disco_rotor_8_polos.stl"].geometria
    assert len(rotor.alojamientos) == diseno.rotor.numero_polos
    assert rotor.alojamientos[0].diametro_m > diseno.rotor.iman.diametro_m
    radios = {round(math.hypot(a.centro_x_m, a.centro_y_m), 9) for a in rotor.alojamientos}
    assert radios == {diseno.rotor.radio_montaje_m}
