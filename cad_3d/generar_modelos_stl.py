#!/usr/bin/env python3
"""Genera las piezas imprimibles (STL en milímetros) en ``cad_3d/stl``.

Equivale a ``uv run generador-axial cad``. Toda la lógica vive en el paquete
``generador_axial`` (carpeta ``src``); este script solo lo invoca.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from generador_axial.presentacion.cli import main  # noqa: E402

if __name__ == "__main__":
    main(["cad", *sys.argv[1:]])
