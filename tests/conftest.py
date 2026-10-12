import pytest

from generador_axial import ESCENARIO_POR_DEFECTO, diseno_por_defecto
from generador_axial.aplicacion import SimuladorGenerador


@pytest.fixture
def diseno():
    return diseno_por_defecto()


@pytest.fixture
def simulador(diseno):
    return SimuladorGenerador(diseno)


@pytest.fixture
def escenario():
    return ESCENARIO_POR_DEFECTO
