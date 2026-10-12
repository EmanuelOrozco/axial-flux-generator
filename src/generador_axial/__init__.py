"""Generador de flujo axial con imanes de neodimio.

Paquete organizado por capas (arquitectura limpia):

- ``dominio``: entidades del diseño y leyes físicas puras (sin E/S).
- ``aplicacion``: casos de uso que orquestan el dominio (simulación, piezas CAD).
- ``infraestructura``: adaptadores hacia el exterior (gráficas, STL, LaTeX).
- ``presentacion``: interfaz de línea de comandos.

Las dependencias apuntan siempre hacia el dominio, nunca al revés.
"""

from generador_axial.configuracion import ESCENARIO_POR_DEFECTO, diseno_por_defecto

__all__ = ["ESCENARIO_POR_DEFECTO", "diseno_por_defecto"]
__version__ = "2.0.0"
