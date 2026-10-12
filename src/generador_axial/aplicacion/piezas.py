"""Fábrica de piezas fabricables derivadas del diseño (patrón Factory).

Cada pieza se describe con una especificación geométrica independiente del formato
de archivo; la capa de infraestructura la convierte en malla STL.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from generador_axial.dominio import DisenoGenerador


@dataclass(frozen=True)
class Alojamiento:
    """Cavidad cilíndrica ciega abierta hacia la cara superior (z = espesor) de una placa."""

    centro_x_m: float
    centro_y_m: float
    diametro_m: float
    profundidad_m: float


@dataclass(frozen=True)
class PlacaConAlojamientos:
    diametro_exterior_m: float
    diametro_agujero_central_m: float
    espesor_m: float
    alojamientos: tuple[Alojamiento, ...] = ()


@dataclass(frozen=True)
class SolidoDeRevolucion:
    """Perfil cerrado (r, z) en sentido antihorario que gira 360° alrededor del eje z."""

    perfil_rz_m: tuple[tuple[float, float], ...]


Geometria = PlacaConAlojamientos | SolidoDeRevolucion


@dataclass(frozen=True)
class Pieza:
    nombre_archivo: str
    descripcion: str
    geometria: Geometria


def catalogo_de_piezas(diseno: DisenoGenerador) -> tuple[Pieza, ...]:
    return (
        _base_carrete(diseno),
        _tapa_carrete(diseno),
        _disco_rotor(diseno),
        _disco_estator(diseno),
    )


def _alojamientos_en_corona(cantidad: int, radio_m: float, diametro_m: float, profundidad_m: float) -> tuple[Alojamiento, ...]:
    return tuple(
        Alojamiento(
            centro_x_m=radio_m * math.cos(2 * math.pi * i / cantidad),
            centro_y_m=radio_m * math.sin(2 * math.pi * i / cantidad),
            diametro_m=diametro_m,
            profundidad_m=profundidad_m,
        )
        for i in range(cantidad)
    )


def _radios_carrete(diseno: DisenoGenerador) -> tuple[float, float]:
    bobina, mecanica = diseno.estator.bobina, diseno.mecanica
    radio_perno = mecanica.con_holgura(mecanica.diametro_eje_m) / 2
    radio_ala = bobina.diametro_exterior_m / 2 + mecanica.sobremedida_ala_carrete_m
    return radio_perno, radio_ala


def _base_carrete(diseno: DisenoGenerador) -> Pieza:
    bobina, mecanica = diseno.estator.bobina, diseno.mecanica
    radio_perno, radio_ala = _radios_carrete(diseno)
    radio_nucleo = bobina.diametro_interior_m / 2
    ala = mecanica.espesor_ala_carrete_m
    tope = ala + bobina.altura_m
    perfil = (
        (radio_perno, 0.0),
        (radio_ala, 0.0),
        (radio_ala, ala),
        (radio_nucleo, ala),
        (radio_nucleo, tope),
        (radio_perno, tope),
    )
    return Pieza(
        nombre_archivo="carrete_base.stl",
        descripcion=(
            f"Base del carrete: núcleo Ø{bobina.diametro_interior_m * 1e3:.0f} mm x "
            f"{bobina.altura_m * 1e3:.0f} mm con ala Ø{2 * radio_ala * 1e3:.0f} mm"
        ),
        geometria=SolidoDeRevolucion(perfil),
    )


def _tapa_carrete(diseno: DisenoGenerador) -> Pieza:
    radio_perno, radio_ala = _radios_carrete(diseno)
    ala = diseno.mecanica.espesor_ala_carrete_m
    perfil = ((radio_perno, 0.0), (radio_ala, 0.0), (radio_ala, ala), (radio_perno, ala))
    return Pieza(
        nombre_archivo="carrete_tapa.stl",
        descripcion=f"Tapa desmontable del carrete Ø{2 * radio_ala * 1e3:.0f} mm (permite extraer la bobina)",
        geometria=SolidoDeRevolucion(perfil),
    )


def _disco_rotor(diseno: DisenoGenerador) -> Pieza:
    rotor, mecanica = diseno.rotor, diseno.mecanica
    alojamientos = _alojamientos_en_corona(
        rotor.numero_polos,
        rotor.radio_montaje_m,
        mecanica.con_holgura(rotor.iman.diametro_m),
        mecanica.profundidad_alojamiento_iman_m,
    )
    return Pieza(
        nombre_archivo=f"disco_rotor_{rotor.numero_polos}_polos.stl",
        descripcion=f"Disco rotor Ø{mecanica.diametro_disco_rotor_m * 1e3:.0f} mm con {rotor.numero_polos} alojamientos para imanes",
        geometria=PlacaConAlojamientos(
            diametro_exterior_m=mecanica.diametro_disco_rotor_m,
            diametro_agujero_central_m=mecanica.con_holgura(mecanica.diametro_eje_m),
            espesor_m=mecanica.espesor_disco_rotor_m,
            alojamientos=alojamientos,
        ),
    )


def _disco_estator(diseno: DisenoGenerador) -> Pieza:
    estator, mecanica = diseno.estator, diseno.mecanica
    alojamientos = _alojamientos_en_corona(
        estator.numero_bobinas,
        estator.radio_montaje_m,
        mecanica.con_holgura(estator.bobina.diametro_exterior_m),
        mecanica.profundidad_alojamiento_bobina_m,
    )
    return Pieza(
        nombre_archivo="disco_estator_soporte.stl",
        descripcion=f"Disco estator Ø{mecanica.diametro_disco_estator_m * 1e3:.0f} mm con {estator.numero_bobinas} alojamientos para bobinas",
        geometria=PlacaConAlojamientos(
            diametro_exterior_m=mecanica.diametro_disco_estator_m,
            diametro_agujero_central_m=mecanica.con_holgura(mecanica.diametro_alojamiento_rodamiento_m),
            espesor_m=mecanica.espesor_disco_estator_m,
            alojamientos=alojamientos,
        ),
    )
