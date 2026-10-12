"""Malla de triángulos inmutable con utilidades de verificación geométrica."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

DECIMALES_SOLDADURA = 6


@dataclass(frozen=True)
class Malla:
    """Triángulos con forma (n, 3, 3): n caras, 3 vértices, 3 coordenadas (mm)."""

    triangulos: NDArray[np.float64]

    @classmethod
    def unir(cls, partes: list[NDArray[np.float64]]) -> Malla:
        no_vacias = [p for p in partes if len(p)]
        return cls(np.concatenate(no_vacias) if no_vacias else np.empty((0, 3, 3)))

    def __len__(self) -> int:
        return len(self.triangulos)

    def normales(self) -> NDArray[np.float64]:
        v0, v1, v2 = self.triangulos[:, 0], self.triangulos[:, 1], self.triangulos[:, 2]
        normales = np.cross(v1 - v0, v2 - v0)
        modulo = np.linalg.norm(normales, axis=1, keepdims=True)
        return np.divide(normales, modulo, out=np.zeros_like(normales), where=modulo > 0)

    def volumen_con_signo(self) -> float:
        """Teorema de la divergencia: positivo si las normales apuntan hacia afuera."""
        v0, v1, v2 = self.triangulos[:, 0], self.triangulos[:, 1], self.triangulos[:, 2]
        return float(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6)

    def orientada_hacia_afuera(self) -> Malla:
        if self.volumen_con_signo() >= 0:
            return self
        return Malla(self.triangulos[:, ::-1].copy())

    def es_hermetica(self) -> bool:
        """Cada arista dirigida debe aparecer exactamente una vez y su opuesta también (2-variedad cerrada)."""
        vertices = np.round(self.triangulos, DECIMALES_SOLDADURA)
        aristas: Counter[tuple] = Counter()
        for a, b, c in vertices:
            for inicio, fin in ((a, b), (b, c), (c, a)):
                aristas[(tuple(inicio), tuple(fin))] += 1
        return all(n == 1 and aristas.get((fin, inicio)) == 1 for (inicio, fin), n in aristas.items())
