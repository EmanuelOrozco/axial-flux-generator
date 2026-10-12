#!/usr/bin/env python3
"""Simulación analítica del generador: resumen en consola y gráficas en ``simulacion/graficas``.

Equivale a ``uv run generador-axial simular``. Toda la lógica vive en el paquete
``generador_axial`` (carpeta ``src``); este script solo lo invoca.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from generador_axial.presentacion.cli import main  # noqa: E402

if __name__ == "__main__":
    main(["simular", *sys.argv[1:]])
