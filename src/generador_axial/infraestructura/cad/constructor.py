"""Convierte especificaciones geométricas de piezas en mallas cerradas (en milímetros)."""

from __future__ import annotations

import math
from functools import singledispatch

import numpy as np
from matplotlib.path import Path as Trayecto
from matplotlib.tri import Triangulation
from numpy.typing import NDArray

from generador_axial.aplicacion.piezas import PlacaConAlojamientos, SolidoDeRevolucion
from generador_axial.infraestructura.cad.malla import Malla

MM_POR_M = 1000.0
SEGMENTOS_MINIMOS = 24

Puntos2D = NDArray[np.float64]
Triangulos = NDArray[np.float64]


@singledispatch
def construir_malla(geometria, longitud_arista_mm: float = 1.0) -> Malla:
    raise TypeError(f"No hay constructor de malla para {type(geometria).__name__}.")


@construir_malla.register
def _(geometria: SolidoDeRevolucion, longitud_arista_mm: float = 1.0) -> Malla:
    perfil = np.asarray(geometria.perfil_rz_m) * MM_POR_M
    segmentos = _segmentos_para_radio(perfil[:, 0].max(), longitud_arista_mm)
    angulos = 2 * np.pi * np.arange(segmentos) / segmentos
    cosenos, senos = np.cos(angulos), np.sin(angulos)

    def vertice(k: int, j: int) -> NDArray[np.float64]:
        r, z = perfil[k % len(perfil)]
        return np.array([r * cosenos[j % segmentos], r * senos[j % segmentos], z])

    caras = []
    for k in range(len(perfil)):
        for j in range(segmentos):
            a, b = vertice(k, j), vertice(k + 1, j)
            c, d = vertice(k + 1, j + 1), vertice(k, j + 1)
            caras.extend(([a, b, c], [a, c, d]))
    return Malla(np.array(caras)).orientada_hacia_afuera()


@construir_malla.register
def _(geometria: PlacaConAlojamientos, longitud_arista_mm: float = 1.0) -> Malla:
    espesor = geometria.espesor_m * MM_POR_M
    exterior = _circunferencia(0.0, 0.0, geometria.diametro_exterior_m * MM_POR_M / 2, longitud_arista_mm)
    central = _circunferencia(0.0, 0.0, geometria.diametro_agujero_central_m * MM_POR_M / 2, longitud_arista_mm)

    partes = [
        _pared(exterior, 0.0, espesor),
        _pared(central[::-1], 0.0, espesor),
    ]
    huecos_superiores, huecos_inferiores = [central], [central]
    for alojamiento in geometria.alojamientos:
        borde = _circunferencia(
            alojamiento.centro_x_m * MM_POR_M,
            alojamiento.centro_y_m * MM_POR_M,
            alojamiento.diametro_m * MM_POR_M / 2,
            longitud_arista_mm,
        )
        profundidad = min(alojamiento.profundidad_m * MM_POR_M, espesor)
        fondo = espesor - profundidad
        huecos_superiores.append(borde)
        partes.append(_pared(borde[::-1], fondo, espesor))
        if fondo > 0:
            partes.append(_elevar(_abanico_convexo(borde), fondo))
        else:
            huecos_inferiores.append(borde)

    partes.append(_elevar(_triangular_region(exterior, huecos_superiores), espesor))
    partes.append(_elevar(_triangular_region(exterior, huecos_inferiores), 0.0)[:, ::-1])
    return Malla.unir(partes).orientada_hacia_afuera()


def _segmentos_para_radio(radio_mm: float, longitud_arista_mm: float) -> int:
    return max(SEGMENTOS_MINIMOS, math.ceil(2 * math.pi * radio_mm / longitud_arista_mm))


def _circunferencia(cx: float, cy: float, radio: float, longitud_arista_mm: float) -> Puntos2D:
    """Polígono regular en sentido antihorario."""
    n = _segmentos_para_radio(radio, longitud_arista_mm)
    angulos = 2 * np.pi * np.arange(n) / n
    return np.column_stack((cx + radio * np.cos(angulos), cy + radio * np.sin(angulos)))


def _pared(contorno: Puntos2D, z_inferior: float, z_superior: float) -> Triangulos:
    """Pared vertical; la normal apunta a la derecha del sentido de recorrido del contorno."""
    siguiente = np.roll(contorno, -1, axis=0)
    a = np.column_stack((contorno, np.full(len(contorno), z_inferior)))
    b = np.column_stack((siguiente, np.full(len(contorno), z_inferior)))
    c = np.column_stack((siguiente, np.full(len(contorno), z_superior)))
    d = np.column_stack((contorno, np.full(len(contorno), z_superior)))
    return np.concatenate((np.stack((a, b, c), axis=1), np.stack((a, c, d), axis=1)))


def _abanico_convexo(contorno: Puntos2D) -> NDArray[np.float64]:
    """Triangulación en abanico de un polígono convexo antihorario: triángulos 2D (m, 3, 2)."""
    indices = np.arange(1, len(contorno) - 1)
    return np.stack(
        (np.repeat(contorno[:1], len(indices), axis=0), contorno[indices], contorno[indices + 1]),
        axis=1,
    )


def _triangular_region(exterior: Puntos2D, huecos: list[Puntos2D]) -> NDArray[np.float64]:
    """Triangula un polígono con huecos usando Delaunay y descartando lo exterior al material.

    Con contornos densamente muestreados y separados entre sí, cada arista de borde es
    una arista de Gabriel y por tanto pertenece a la triangulación de Delaunay; así
    ningún triángulo cruza un borde y basta clasificar los centroides.
    """
    puntos = np.concatenate([exterior, *huecos])
    triangulacion = Triangulation(puntos[:, 0], puntos[:, 1])
    triangulos = puntos[triangulacion.triangles]
    centroides = triangulos.mean(axis=1)

    dentro = Trayecto(exterior).contains_points(centroides)
    for hueco in huecos:
        dentro &= ~Trayecto(hueco).contains_points(centroides)
    triangulos = triangulos[dentro]

    u = triangulos[:, 1] - triangulos[:, 0]
    w = triangulos[:, 2] - triangulos[:, 0]
    horarios = u[:, 0] * w[:, 1] - u[:, 1] * w[:, 0] < 0
    triangulos[horarios] = triangulos[horarios][:, ::-1]
    return triangulos


def _elevar(triangulos_2d: NDArray[np.float64], z: float) -> Triangulos:
    altura = np.full(triangulos_2d.shape[:2] + (1,), z)
    return np.concatenate((triangulos_2d, altura), axis=2)
