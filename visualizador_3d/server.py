#!/usr/bin/env python3
"""Servidor local del visualizador 3D.

Abre el simulador en una ventana propia (modo aplicación de un navegador Chromium: Edge, Chrome,
Chromium o Brave) con un tamaño fijo, en lugar de una pestaña más del navegador.

Uso:
    python3 visualizador_3d/server.py [--puerto 8000] [--ventana 1360x860] [--en-pestana] [--sin-navegador]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DIRECTORIO = Path(__file__).resolve().parent
HOST = "127.0.0.1"
LINEA = "=" * 65
NAVEGADORES_CHROMIUM = (
    "microsoft-edge-stable",
    "microsoft-edge",
    "msedge",
    "google-chrome-stable",
    "google-chrome",
    "chrome",
    "chromium",
    "chromium-browser",
    "brave-browser",
    "brave",
)
# Un perfil propio hace que el navegador abra un proceso nuevo y respete --window-size.
PERFIL_VENTANA = Path.home() / ".cache" / "generador_axial" / "ventana"


class ServidorReutilizable(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def tamano_ventana(texto: str) -> tuple[int, int]:
    try:
        ancho, alto = (int(valor) for valor in texto.lower().split("x"))
    except ValueError:
        raise argparse.ArgumentTypeError("Use el formato ANCHOxALTO, por ejemplo 1360x860.") from None
    if ancho < 640 or alto < 480:
        raise argparse.ArgumentTypeError("La ventana debe medir al menos 640x480.")
    return ancho, alto


def leer_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sirve el visualizador 3D en http://localhost.")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--ventana", type=tamano_ventana, default=(1360, 860), metavar="ANCHOxALTO",
                        help="Tamaño de la ventana del simulador (por defecto 1360x860).")
    parser.add_argument("--navegador", help="Ruta o nombre de un navegador Chromium para la ventana.")
    parser.add_argument("--en-pestana", action="store_true", help="Abrir en una pestaña del navegador predeterminado.")
    parser.add_argument("--sin-navegador", action="store_true", help="No abrir el navegador automáticamente.")
    return parser.parse_args()


def buscar_navegador_chromium(preferido: str | None) -> str | None:
    candidatos = (preferido,) if preferido else NAVEGADORES_CHROMIUM
    return next((ruta for nombre in candidatos if (ruta := shutil.which(nombre))), None)


def abrir_ventana_aplicacion(url: str, tamano: tuple[int, int], preferido: str | None) -> bool:
    """Lanza el simulador como ventana de aplicación independiente; False si no hay navegador compatible."""
    navegador = buscar_navegador_chromium(preferido)
    if navegador is None:
        return False
    PERFIL_VENTANA.mkdir(parents=True, exist_ok=True)
    ancho, alto = tamano
    subprocess.Popen(
        [
            navegador,
            f"--app={url}",
            f"--window-size={ancho},{alto}",
            f"--user-data-dir={PERFIL_VENTANA}",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    return True


def main() -> None:
    argumentos = leer_argumentos()
    manejador = partial(SimpleHTTPRequestHandler, directory=str(DIRECTORIO))
    try:
        servidor = ServidorReutilizable((HOST, argumentos.puerto), manejador)
    except OSError as error:
        raise SystemExit(f"No se pudo abrir el puerto {argumentos.puerto}: {error}. Pruebe con --puerto 8080.")

    url = f"http://localhost:{argumentos.puerto}"
    print(f"{LINEA}\nSERVIDOR DEL VISUALIZADOR 3D ACTIVO\n{LINEA}")
    print(f"Dirección local: {url}\nPara detener el servidor presione Ctrl + C.\n{LINEA}")
    if argumentos.en_pestana:
        webbrowser.open(url)
    elif not argumentos.sin_navegador:
        if not abrir_ventana_aplicacion(f"{url}/?ventana=1", argumentos.ventana, argumentos.navegador):
            print("No se encontró Edge, Chrome, Chromium ni Brave: se abre una ventana del navegador predeterminado.")
            webbrowser.open_new(url)

    with servidor:
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")


if __name__ == "__main__":
    main()
