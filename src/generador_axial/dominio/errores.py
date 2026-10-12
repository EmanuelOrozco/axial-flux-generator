"""Errores propios del dominio."""


class ErrorDeDiseno(ValueError):
    """Un parámetro de diseño es físicamente inválido o incoherente con el resto."""


def exigir_positivo(nombre: str, valor: float) -> None:
    if not valor > 0:
        raise ErrorDeDiseno(f"{nombre} debe ser positivo (se recibió {valor}).")
