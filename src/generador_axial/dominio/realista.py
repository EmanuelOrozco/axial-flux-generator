"""Parámetros del modelo realista (dinámico) del prototipo. Unidades SI.

El modelo ideal (``fisica.py``) describe el régimen permanente con hipótesis de libro de texto.
Estas entidades agregan lo que el prototipo real no puede evitar: inercia y rozamiento del rotor,
una fuente motriz con característica par-velocidad, el calentamiento de las bobinas, una batería
de plomo-ácido con polarización y efecto Peukert, el consumo en vacío del inversor y el autoconsumo
del controlador de carga.
"""

from __future__ import annotations

from dataclasses import dataclass

from generador_axial.dominio.errores import ErrorDeDiseno, exigir_positivo


@dataclass(frozen=True)
class MaterialesRotor:
    """Densidades de las piezas giratorias, para calcular el momento de inercia."""

    densidad_disco_kg_m3: float = 1240.0  # PLA macizo
    densidad_iman_kg_m3: float = 7500.0  # NdFeB sinterizado
    densidad_eje_kg_m3: float = 7850.0  # acero
    longitud_eje_m: float = 0.150

    def __post_init__(self) -> None:
        exigir_positivo("La densidad del disco", self.densidad_disco_kg_m3)
        exigir_positivo("La densidad del imán", self.densidad_iman_kg_m3)
        exigir_positivo("La densidad del eje", self.densidad_eje_kg_m3)
        exigir_positivo("La longitud del eje", self.longitud_eje_m)


@dataclass(frozen=True)
class PerdidasMecanicas:
    """Par resistente no eléctrico: T = T_c + b·ω + k_v·ω² (rodamientos 608-2RS y ventilación del disco).

    Un generador sin núcleo (coreless) no tiene hierro en el estator, por lo que no hay par de
    retención (cogging) ni pérdidas por histéresis.
    """

    par_coulomb_nm: float = 0.003
    coeficiente_viscoso_nm_s: float = 1.5e-5
    coeficiente_ventilacion_nm_s2: float = 1.5e-8

    def __post_init__(self) -> None:
        if min(self.par_coulomb_nm, self.coeficiente_viscoso_nm_s, self.coeficiente_ventilacion_nm_s2) < 0:
            raise ErrorDeDiseno("Los coeficientes de rozamiento no pueden ser negativos.")


@dataclass(frozen=True)
class FuenteMotriz:
    """Impulsor con característica lineal T(ω) = T_ajuste·(1 − ω/ω_0), como un motor DC o una manivela."""

    par_maximo_nm: float = 0.30
    par_inicial_nm: float = 0.05
    velocidad_vacio_rpm: float = 1500.0
    par_impulso_nm: float = 0.08
    duracion_impulso_s: float = 0.5

    def __post_init__(self) -> None:
        exigir_positivo("El par máximo de la fuente motriz", self.par_maximo_nm)
        exigir_positivo("La velocidad en vacío de la fuente motriz", self.velocidad_vacio_rpm)
        exigir_positivo("El par del impulso", self.par_impulso_nm)
        exigir_positivo("La duración del impulso", self.duracion_impulso_s)
        if not 0 <= self.par_inicial_nm <= self.par_maximo_nm:
            raise ErrorDeDiseno("El par inicial debe estar entre 0 y el par máximo.")


@dataclass(frozen=True)
class ModeloTermico:
    """Nodo térmico único: bobinas de cobre embebidas en el disco estator de PLA.

    C·dT/dt = P_cobre + P_Foucault − (T − T_amb)/R_th, con R_th = 1 / (h(ω)·A) y
    h(ω) = h_natural + h_forzada·ω (el rotor ventila el estator al girar).
    """

    capacidad_termica_j_k: float = 100.0
    conveccion_natural_w_m2k: float = 8.0
    conveccion_forzada_w_m2k_por_rad_s: float = 0.15
    temperatura_ambiente_c: float = 25.0
    temperatura_referencia_c: float = 20.0
    coeficiente_cobre_1_k: float = 0.00393
    coeficiente_remanencia_1_k: float = -0.0012
    temperatura_maxima_pla_c: float = 55.0

    def __post_init__(self) -> None:
        exigir_positivo("La capacidad térmica", self.capacidad_termica_j_k)
        exigir_positivo("La convección natural", self.conveccion_natural_w_m2k)
        if self.conveccion_forzada_w_m2k_por_rad_s < 0:
            raise ErrorDeDiseno("La convección forzada no puede ser negativa.")


@dataclass(frozen=True)
class BateriaPlomoAcido:
    """Circuito equivalente de Thévenin de primer orden de una batería AGM de 12 V.

    V_bornes = E_oc(SoC) + V_p + R_0·I   (I > 0 cargando)
    dV_p/dt = (R_p·I − V_p)/τ_p
    La curva E_oc(SoC) es la tensión en reposo; su codo inferior reproduce el colapso de tensión
    al final de la descarga. Al cargar, la resistencia de polarización crece como
    R_p·(1 + A·e^(B·(SoC − 1))): es el sobrepotencial de gasificación que, cerca de la carga
    completa, obliga al controlador a pasar a absorción y deja solo una pequeña corriente de flotación.
    """

    curva_ocv: tuple[tuple[float, float], ...] = (
        (0.00, 10.50),
        (0.05, 11.30),
        (0.10, 11.60),
        (0.20, 11.85),
        (0.40, 12.10),
        (0.60, 12.35),
        (0.80, 12.58),
        (1.00, 12.85),
    )
    resistencia_ohmica_ohm: float = 0.025
    resistencia_polarizacion_ohm: float = 0.030
    constante_tiempo_polarizacion_s: float = 30.0
    factor_sobrepotencial_carga: float = 1500.0
    pendiente_sobrepotencial_carga: float = 50.0
    exponente_peukert: float = 1.12
    horas_regimen_nominal: float = 20.0
    eficiencia_coulomb: float = 0.95
    soc_inicio_gasificacion: float = 0.85
    eficiencia_coulomb_llena: float = 0.60
    autodescarga_mensual: float = 0.03
    soc_flotacion: float = 0.995

    def __post_init__(self) -> None:
        socs = [p[0] for p in self.curva_ocv]
        tensiones = [p[1] for p in self.curva_ocv]
        if socs[0] != 0.0 or socs[-1] != 1.0 or socs != sorted(set(socs)):
            raise ErrorDeDiseno("La curva E_oc(SoC) debe ir de SoC = 0 a SoC = 1 en orden creciente.")
        if tensiones != sorted(tensiones):
            raise ErrorDeDiseno("La tensión en reposo debe crecer con el estado de carga.")
        exigir_positivo("La resistencia óhmica de la batería", self.resistencia_ohmica_ohm)
        exigir_positivo("La resistencia de polarización", self.resistencia_polarizacion_ohm)
        exigir_positivo("La constante de tiempo de polarización", self.constante_tiempo_polarizacion_s)
        if self.exponente_peukert < 1.0:
            raise ErrorDeDiseno("El exponente de Peukert debe ser mayor o igual a 1.")
        if not 0 < self.eficiencia_coulomb_llena <= self.eficiencia_coulomb <= 1:
            raise ErrorDeDiseno("Las eficiencias coulómbicas deben cumplir 0 < η_llena ≤ η ≤ 1.")
        if not 0 < self.soc_inicio_gasificacion < 1:
            raise ErrorDeDiseno("El inicio de la gasificación debe estar entre 0 y 1.")
        if self.factor_sobrepotencial_carga < 0 or self.pendiente_sobrepotencial_carga < 0:
            raise ErrorDeDiseno("Los parámetros del sobrepotencial de carga no pueden ser negativos.")


@dataclass(frozen=True)
class InversorReal:
    """Pérdidas del inversor: P_entrada = P_0 + P_AC + k·P_AC², con k fijado por la eficiencia nominal.

    Desconexión por baja tensión (LVD) en bornes de la batería, con reconexión por histéresis.
    """

    potencia_vacio_w: float = 3.6
    tension_corte_v: float = 10.8
    tension_reconexion_v: float = 12.3

    def __post_init__(self) -> None:
        if self.potencia_vacio_w < 0:
            raise ErrorDeDiseno("El consumo en vacío del inversor no puede ser negativo.")
        if self.tension_reconexion_v <= self.tension_corte_v:
            raise ErrorDeDiseno("La tensión de reconexión debe superar a la de corte.")


@dataclass(frozen=True)
class ControladorMpptReal:
    """Autoconsumo del controlador, tomado siempre de la batería."""

    consumo_propio_a: float = 0.008

    def __post_init__(self) -> None:
        if self.consumo_propio_a < 0:
            raise ErrorDeDiseno("El autoconsumo del controlador no puede ser negativo.")


@dataclass(frozen=True)
class Integracion:
    """Discretización numérica compartida por Python y el visualizador (deben coincidir para la paridad)."""

    paso_maximo_s: float = 0.005
    puntos_radiales: int = 32
    muestras_perfil: int = 256
    iteraciones_biseccion: int = 60

    def __post_init__(self) -> None:
        exigir_positivo("El paso de integración", self.paso_maximo_s)
        exigir_positivo("Los puntos radiales", self.puntos_radiales)
        exigir_positivo("Las muestras del perfil", self.muestras_perfil)
        exigir_positivo("Las iteraciones de bisección", self.iteraciones_biseccion)


@dataclass(frozen=True)
class ParametrosRealistas:
    materiales: MaterialesRotor = MaterialesRotor()
    perdidas: PerdidasMecanicas = PerdidasMecanicas()
    motriz: FuenteMotriz = FuenteMotriz()
    termico: ModeloTermico = ModeloTermico()
    bateria: BateriaPlomoAcido = BateriaPlomoAcido()
    inversor: InversorReal = InversorReal()
    controlador: ControladorMpptReal = ControladorMpptReal()
    integracion: Integracion = Integracion()
