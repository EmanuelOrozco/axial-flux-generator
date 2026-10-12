# Proyecto de Teoría Electromagnética: Generador con Imanes de Neodimio
Basado en los fundamentos de **Matthew N. O. Sadiku**, *Elementos de Electromagnetismo*, 3.ª Edición (Oxford University Press).

Generador de flujo axial sin núcleo (*coreless AFPMG*) con 8 imanes NdFeB y 8 bobinas en serie, integrado en una **micro-red autónoma completa**:
$$\text{Generador AC} \longrightarrow \text{Puente Rectificador} \longrightarrow \text{Controlador DC-DC} \longrightarrow \text{Batería 12V} \longrightarrow \text{Inversor AC (110V / 220V)} \longrightarrow \text{Carga Residencial}$$

El repositorio reúne el modelo analítico riguroso, un **modelo dinámico realista** del sistema completo, las piezas imprimibles 3D (STL), un simulador computacional y visualizador 3D interactivo en Three.js con osciloscopio de doble traza, y la documentación técnica completa, todo gobernado por **una única fuente de verdad** definida en `src/generador_axial/configuracion.py`.

---

## Estructura del proyecto

```
teoria_electromagnetica/
├── pyproject.toml                  # Proyecto uv: dependencias, comando `generador-axial`, pytest
├── src/generador_axial/            # Paquete Python (arquitectura limpia en capas)
│   ├── configuracion.py            # Diseño por defecto: fuente única de verdad
│   ├── dominio/                    # Componentes validados, física ideal y física realista (dinamica.py, realista.py)
│   ├── aplicacion/                 # Simulador ideal, SimulacionDinamica, catálogo de piezas, reporte
│   ├── infraestructura/            # STL, 12 gráficas matplotlib y macros LaTeX
│   └── presentacion/               # Interfaz CLI (`generador-axial`)
├── tests/                          # 109 pruebas automáticas + 29 de interfaz en Chromium
├── simulacion/
│   ├── modelo_analitico.py         # Envoltorio de `generador-axial simular`
│   └── graficas/                   # 12 curvas: 8 del modelo ideal + onda real, arranque/impulso, régimen vs par, ciclo de carga
├── cad_3d/
│   ├── generar_modelos_stl.py      # Envoltorio de `generador-axial cad`
│   └── stl/                        # Carrete (base + tapa), disco rotor, disco estator
├── visualizador_3d/
│   ├── index.html, server.py, css/
│   └── js/                         # Three.js (PBR) + modelo dinámico (dinamica.js, espejo exacto de Python) + osciloscopio
└── docs/
    ├── 01_marco_teorico_sadiku.md  # Fundamentación completa deducida desde Sadiku
    ├── 02_guia_fabricacion_paso_a_paso.md # Manual paso a paso con lista de compras y seguridad 110V/220V
    ├── 01_marco_teorico.pdf        # Versiones PDF compilables
    ├── 02_memoria_de_calculo.pdf
    ├── 03_guia_fabricacion.pdf
    ├── 04_arquitectura_software.pdf
    ├── 05_modelo_realista.pdf      # Dinámica, onda real, batería de plomo-ácido, inversor, temperatura
    ├── 06_presentacion.pdf         # Presentación de 10 minutos con demo en vivo
    ├── 06_guion_presentacion.md    # Guion cronometrado de la presentación y la demo
    ├── compilar_pdf.sh             # Script de compilación LaTeX
    └── latex/                      # Fuentes y macros LaTeX generadas automáticamente
```

---

## Inicio rápido

Requiere [uv](https://docs.astral.sh/uv/) y Python 3.11+.

```bash
uv sync                           # Instala dependencias en .venv
uv run generador-axial simular    # Resumen del diseño + 12 gráficas en simulacion/graficas/
uv run generador-axial cad        # Genera piezas STL en cad_3d/stl/
uv run generador-axial reporte    # Genera macros LaTeX en docs/latex/generado/
uv run generador-axial todo       # Ejecuta simulación, CAD y reporte en un solo comando
uv run pytest                     # Ejecuta las 109 pruebas automáticas (física ideal y realista, CAD, paridad JS)
uv run --group e2e playwright install chromium   # Una sola vez: navegador para las pruebas de interfaz
uv run --group e2e pytest -m interfaz            # 29 pruebas de la interfaz en Chromium (≈11 min con WebGL por software)
```

### Visualizador 3D Computacional

El visualizador ejecuta el **modelo dinámico realista** (Documento 5), idéntico paso a paso al de Python:

- **Par motriz, no velocidad**: se fija el par de la fuente (0–0.30 N·m); la velocidad resulta del equilibrio con la inercia, el rozamiento de los rodamientos y el **frenado de Lenz**. El botón *Impulso* simula un empujón con la mano (0.08 N·m durante 0.5 s).
- **Forma de onda real**: la fem sale del solape imán–espira (factor de cresta 1.34, no senoidal) y así la dibuja el osciloscopio (CH1), junto a la salida del inversor (CH2).
- **Electrónica con límites**: inductancia y R(T) de las bobinas, puente con rizado según el condensador (220–4700 µF), MPPT con tensión mínima de bus, absorción 14.4 V, flotación 13.8 V y límite de 3 A.
- **Batería de plomo-ácido** (Thévenin con polarización, Peukert, gasificación, autodescarga) e **inversor real** (3.6 W en vacío, corte bajo 10.8 V y reconexión sobre 12.3 V).
- **Temperatura**: calentamiento de las bobinas, pérdida de remanencia del imán y alarma por encima de 55 °C (PLA).
- **Tiempo**: selector 1×, 10×, 50× o 500× para la batería y la temperatura; la mecánica corre siempre en tiempo real.
- **Render físicamente basado**: mapa de entorno, tono ACES, sombras suaves y texturas procedurales (contrachapado, capas de impresión, bobinado esmaltado, etiquetas).

Abra `visualizador_3d/index.html` en el navegador, o inicie el servidor local:
```bash
uv run python visualizador_3d/server.py                          # Abre el simulador en su propia ventana (1360x860)
uv run python visualizador_3d/server.py --ventana 1600x1000      # Otro tamaño de ventana
uv run python visualizador_3d/server.py --en-pestana             # En una pestaña del navegador
uv run python visualizador_3d/server.py --puerto 9000 --sin-navegador
uv run python visualizador_3d/server.py --navegador chromium     # Usar un navegador Chromium concreto
```

### Documentos PDF

```bash
./docs/compilar_pdf.sh                        # Compila los cinco documentos y la presentación
./docs/compilar_pdf.sh 06_presentacion        # Compila solo uno
```
*(Requiere `pdflatex` con paquetes `circuitikz`, `tcolorbox` y `siunitx`)*.

---

## Resultados del Sistema y Diseño por Defecto

| Parámetro | Valor del Modelo | Fundamento / Nota |
| :--- | :--- | :--- |
| Polos magnéticos ($P$) | 8 imanes NdFeB N38 | $\varnothing 20 \times 5\,\text{mm}$, polaridad alternada N-S |
| Bobinas del estator ($N_b \times N$) | 8 bobinas de 180 espiras | AWG 26, sin núcleo de hierro (*coreless*) |
| Campo magnético medio ($\bar{B}_z$) | **0.1545 T** | Integral exacta en el espesor de la bobina (Sadiku Cap. 7-8) |
| Flujo magnético máximo ($\Phi_{max}$) | **41.27 µWb** | Por espira ($k = 0.85$) |
| Resistencia interna ($R_{int}$) | **12.14 Ω** | Longitud media de espira calculada a 20 °C |
| Frecuencia a 300 RPM ($f_e$) | **20.0 Hz** | $f_e = P \cdot \text{RPM}/120$ |
| Tensión inducida a 300 RPM | **7.47 V pico / 5.28 V RMS** | Ley de Faraday (Sadiku Sec. 9.2) |
| Tensión continua rectificada ($V_{DC}$) | **6.87 V** (Schottky) / **24.29 V** a 1000 RPM | Puente de Graetz $V_{pico} - 2V_D$ |
| Batería de almacenamiento | **12.0 V nominal / 7.0 Ah** | Modelo electroquímico con curva SoC y umbral de corte |
| Salida del inversor residencial | **110 V / 220 V AC** (60 Hz), 150 W, η = 0.90 | SPWM senoidal pura con acoplamiento por transformador elevador |
| Carga residencial conectada | **Bombillo 15 W** | Exige 16.67 W a la batería (1.36 A) |
| Carga MPPT a 600 RPM | **2.07 W / 168 mA** | $P_{max} = E_{RMS}^2/(4R_{int})$, $\eta_c = 0.90$ |
| Balance neto con 15 W a 600 RPM | **−14.60 W** (autonomía 1.73 h) | La batería se descarga |
| RPM de equilibrio para 15 W / 5 W | **1704 RPM / 984 RPM** | 15 W no es sostenible dentro de 1200 RPM: el generador **recarga**, la batería **alimenta** |

### Modelo dinámico realista (Documento 5)

| Resultado | Valor | Nota |
| :--- | :--- | :--- |
| Inercia del rotor | **2.415 × 10⁻⁴ kg·m²** | Disco PLA + imanes + eje de acero |
| Inductancia de las 8 bobinas | **4.22 mH** | Wheeler; sin hierro, sin *cogging* |
| Factor de cresta de la fem | **1.335** | Senoide: 1.414; E_RMS real = 0.93 × ideal |
| Régimen con 0.07 N·m | **483 RPM, 0.96 W a la batería** | Eficiencia eje → batería ≈ 40 % |
| Impulso con la mano | **pico de 505 RPM**, parada 2.7 s después | Frenado por rozamiento y por Lenz |
| Rizado con 0.2 N·m | **18.8 V (220 µF) / 0.88 V (4700 µF)** | El condensador original es insuficiente |
| Ciclo de carga desde 80 % (0.30 N·m) | **absorción a las 4.0 h, flotación a las 8.2 h** | Corriente de flotación ≈ 21 mA |

