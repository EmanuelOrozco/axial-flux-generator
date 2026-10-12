# Guía Práctica de Fabricación Paso a Paso del Generador con Imanes de Neodimio
### Generador de Flujo Axial Sin Núcleo (Coreless AFPMG)

> **Versión PDF ampliada**: [`03_guia_fabricacion.pdf`](03_guia_fabricacion.pdf).
> Todas las cotas coinciden con las piezas de `cad_3d/stl/` y con el modelo de `src/generador_axial/configuracion.py`.

---

## 1. Especificación del Prototipo

- **Rotor**: disco de Ø110 mm con **8 imanes NdFeB Ø20 × 5 mm** a radio 40 mm, polaridad alternada **N-S-N-S-N-S-N-S**.
- **Estator**: disco de Ø120 mm con **8 bobinas** (Ø interior 12 mm, Ø exterior 28 mm, altura 6 mm, 180 espiras AWG 26) en serie con polaridad alternada.
- **Entrehierro**: 2.5 mm entre la cara de los imanes y la cara de las bobinas.
- **Ventajas**: cero *cogging*, comportamiento lineal (Faraday puro), materiales baratos.

---

## 2. ⚠️ Protocolo de Seguridad con Imanes de Neodimio

> [!WARNING]
> 1. **Pellizcos**: a menos de 10 cm los imanes se atraen violentamente. Mantenga los dedos fuera de la línea de impacto.
> 2. **Fragilidad**: son cerámicos sinterizados; si chocan se astillan. Use gafas de protección.
> 3. **Separación**: deslícelos lateralmente; nunca tire de frente.
> 4. **Electrónica y marcapasos**: mantenga tarjetas, teléfonos y marcapasos a más de 30 cm.

### ⚠️ Protocolo Crítico de Seguridad Eléctrica (Batería y Alta Tensión 110 V / 220 V AC)

> [!CAUTION]
> **PELIGRO DE ELECTROCUCIÓN - TENSIÓN RESIDENCIAL LETAL (110 V / 220 V AC):**
> 1. **Aislamiento absoluto**: la salida del inversor entrega 110 V o 220 V eficaces ($V_{pico} \approx 155.6\,\text{V}$ o $311.1\,\text{V}$). A estas tensiones, el contacto directo con la piel puede causar fibrilación ventricular o quemaduras severas. Todo empalme o borne de 110V/220V DEBE estar protegido con cinta aislante de alta calidad o tubo termorretráctil, preferiblemente dentro de una caja plástica cerrada.
> 2. **Regla de oro de manipulación**: NUNCA toque conexiones AC mientras el inversor esté encendido. Apague el interruptor del inversor antes de conectar el bombillo o mover los cables del tomacorriente.
> 3. **Cortocircuito en batería**: una batería de 12 V (plomo o litio) puede suministrar más de 50 A a 100 A en cortocircuito instantáneo, derritiendo cables y provocando incendios. Instale SIEMPRE un fusible de 10 A – 15 A en el borne positivo inmediatamente a la salida de la batería.
> 4. **Puesta a tierra**: conecte la borna de tierra del chasis del inversor a una referencia de tierra si va a conectar equipos de carcasa metálica.

---

## 3. Lista de Materiales

### A. Componentes del Generador y Rectificador (Baja Tensión)

| Ítem | Descripción técnica | Cantidad | Propósito | Costo aprox. (USD) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Imanes NdFeB disco **Ø20 × 5 mm**, grado N38 o superior | 8 (+1 de reserva) | Polos del rotor | 8 – 12 |
| 2 | Alambre de cobre esmaltado **AWG 26** (Ø 0.404 mm) | Carrete de **150 g** (se usan ~91 m ≈ 104 g) | 8 bobinas | 5 – 8 |
| 3 | Rodamientos **608-ZZ / 608-2RS** (Ø8 × Ø22 × 7 mm) | 2 (+1 para el estator, opcional) | Eje de baja fricción | 2 – 4 |
| 4 | Varilla roscada o eje liso **Ø8 mm × 150 mm**, 6 tuercas y 6 arandelas M8 | 1 | Eje | 2 |
| 5 | Discos impresos en PLA/PETG (STL incluidos) o acrílico de 5–6 mm | Rotor Ø110 + estator Ø120 | Soportes | 3 – 6 |
| 6 | Resina epóxica bicomponente | 1 tubo | Fijar imanes y bobinas | 3 |
| 7 | Diodos **1N5819** (Schottky) o **1N4007** | 4 | Puente rectificador | 1 |
| 8 | Condensador electrolítico **220 µF × 50 V** | 1 | Filtro | 0.5 |
| 9 | LED de alto brillo + resistencia **2.2 kΩ, ½ W** | 1 + 1 | Indicador de generación DC | 0.5 |
| 10 | Bornes banana o clema de 2 polos | 1 juego | Medición generador | 1 |

### B. Componentes del Sistema de Almacenamiento e Inversión (Micro-red 110 V / 220 V)

| Ítem | Descripción técnica | Cantidad | Propósito | Costo aprox. (USD) |
| :--- | :--- | :--- | :--- | :--- |
| 11 | **Batería recargable 12 V** (Plomo-ácido AGM/VRLA 12V 7Ah o LiFePO4 12V 6–10Ah) | 1 | Almacenamiento y buffer de energía | 12 – 22 |
| 12 | **Controlador de carga DC-DC buck-boost con limitación de corriente (CC/CV)**, idealmente con MPPT (e.g., módulo LTC3780 CC/CV o mini-controlador MPPT de 12 V), arranque ≤ 3.5 V, corte a 14.4 V y diodo antirretorno. *Un XL6009 sin límite de corriente no es un cargador válido.* | 1 | Adaptación de tensión y carga segura de batería | 4 – 8 |
| 13 | **Inversor DC-AC 12 V a 110 V o 220 V AC** (150 W – 300 W, onda senoidal pura o modificada) con tomacorriente | 1 | Conversión a tensión de red residencial (60 Hz / 50 Hz) | 15 – 25 |
| 14 | **Portafusible aéreo + Fusible automotriz 10 A – 15 A** | 1 | Protección contra cortocircuito en línea de 12 V | 1.5 |
| 15 | **Fusible rápido AC 1 A – 2 A** con portafusible de chasis | 1 | Protección sobrecorriente en salida 110V/220V | 1 |
| 16 | **Tomacorriente hembra empotrable / aéreo** (NEMA 5-15 para 110V o Schuko/Euro para 220V) | 1 | Enchufe de conexión de cargas | 1.5 |
| 17 | **Bombillo LED o incandescente de prueba** (5 W – 15 W a 110V/220V) con roseta E27 | 1 | Carga visual demostrativa | 2 – 3 |
| 18 | Cable de cobre flexible: **AWG 14** (rojo/negro, 1.5 m para batería/inversor) y **AWG 18** (para 110V/220V) | 1 juego | Conexionado de potencia | 3 |

> **Por qué 50 V y 2.2 kΩ ½ W en el rectificador**: a 1200 RPM el modelo predice $V_{DC} \approx 29.3\,\text{V}$, por encima de los 25 V de un condensador común. Con 1 kΩ la resistencia del LED disiparía ~0.74 W (el triple de lo que soporta una de ¼ W) y el LED recibiría 27 mA; con 2.2 kΩ disipa ~0.34 W (seguro para ½ W) y el LED recibe ~12 mA.

**Costo total estimado**:
- Solo generador y rectificación básica: ~22 – 35 USD.
- Micro-red completa (generador + batería + cargador DC-DC + inversor 110V/220V + protecciones): ~55 – 95 USD.

---

## 4. Herramientas

- Multímetro digital (AC/DC, escala de 200 Ω).
- Cautín, estaño y pasta fundente.
- Lija fina (grano 400–600) o cúter para retirar el esmalte.
- Brújula o imán de referencia marcado (polaridad).
- Calibrador (pie de rey) y galgas o láminas de 2.5 mm para el entrehierro.
- Impresora 3D (o taladro con broca de 8 mm y sierra de copa si usa acrílico/MDF).

---

## 5. Procedimiento de Construcción

```
 FASE 0: Imprimir piezas  →  FASE 1: Estator  ─┐
                              FASE 2: Rotor    ─┼→ FASE 3: Ensamble → FASE 4: Rectificación ─┐
                                                                                              ├─► FASE 5: Batería & Inversor 110V/220V ──► FASE 6: Pruebas
```

### Fase 0: Impresión de las piezas (opcional pero recomendada)

Genere o use los STL de `cad_3d/stl/` (unidades en mm):

| Archivo | Pieza | Detalle |
| :--- | :--- | :--- |
| `carrete_base.stl` | Base del carrete | Núcleo Ø12 × 6 mm, ala Ø32 mm, agujero Ø8.4 mm |
| `carrete_tapa.stl` | Tapa del carrete | Ala Ø32 mm desmontable (para extraer la bobina) |
| `disco_rotor_8_polos.stl` | Rotor | Ø110 × 6 mm, 8 alojamientos Ø20.4 × 4 mm, eje Ø8.4 mm |
| `disco_estator_soporte.stl` | Estator | Ø120 × 5 mm, 8 alojamientos Ø28.4 × 3 mm, centro Ø22.4 mm |

Parámetros sugeridos: PLA o PETG, 0.2 mm de capa, 4 perímetros, 40 % de relleno, sin soportes (todas las piezas tienen la cara plana hacia la cama).

### Fase 1: Bobinas y estator

1. **Montar el carrete**: atornille `carrete_base` y `carrete_tapa` con un perno M8 y tuerca. Cubra el núcleo con una vuelta de cinta de teflón o papel encerado para que la bobina no se pegue.
2. **Bobinar**: deje 6 cm de alambre libre (inicio). Enrolle **180 espiras** ordenadas y apretadas (puede usar un taladro a baja velocidad contando vueltas). La ventana del carrete admite ~230 espiras de AWG 26 como límite físico y unas 197 en la práctica (ocupación 0.85); con 180 la ocupación es del 78 %. Deje 6 cm al final.
3. **Fijar y extraer**: impregne con unas gotas de cianoacrilato o barniz, espere a que seque, retire la tapa y saque la bobina.
4. **Marcar**: marque el **inicio (I)** y el **final (F)** de cada bobina. Repita hasta tener 8 bobinas idénticas. Mida cada una: ≈ 1.5 Ω.
5. **Colocar en el estator**: pegue cada bobina con epoxi en su alojamiento del disco estator, **todas con la misma cara hacia arriba** (así todas quedan enrolladas en el mismo sentido).
6. **Raspar el esmalte**: lije 1.5 cm de cada extremo hasta ver el cobre brillante.
7. **Conexión en serie con polaridad alternada**:
   - F1 → F2, I2 → I3, F3 → F4, I4 → I5, F5 → F6, I6 → I7, F7 → F8.
   - Quedan libres **I1** e **I8**: son los terminales de salida AC.
   - Suelde y aísle cada unión con termorretráctil.
   - *Por qué*: bobinas vecinas ven polos opuestos en el mismo instante; invertir cada segunda bobina hace que todas las fem se sumen.
8. **Verificar**: la resistencia entre I1 e I8 debe ser ≈ **12 Ω** (modelo: 12.14 Ω a 20 °C).

### Fase 2: Rotor magnético

1. **Identificar polaridades**: con la brújula, marque 4 imanes con la cara visible **N** y 4 con la cara visible **S**.
2. **Insertar los imanes** en los alojamientos del disco rotor en secuencia **N-S-N-S-N-S-N-S**, de uno en uno y lejos de los demás imanes. Cada imán sobresale 1 mm del disco.
3. **Fijar** con epoxi y dejar curar **12 a 24 h** antes de girar el rotor.

### Fase 3: Ensamble mecánico y entrehierro

1. Monte los dos rodamientos 608 en soportes rígidos (torres en "U" de madera, aluminio o impresas).
2. Pase el eje de 8 mm y fije el rotor con tuerca y arandela a cada lado (sin cabeceo).
3. Monte el estator fijo frente al rotor, con las bobinas mirando a los imanes.
4. **Ajuste del entrehierro**: separe la cara de los imanes y la cara de las bobinas **2.0 – 3.0 mm** (diseño: 2.5 mm) usando galgas.
   - *Por qué*: el campo cae rápido con la distancia,
     $$B_z(z) = \frac{B_r}{2} \left[ \frac{z + L}{\sqrt{(z + L)^2 + R^2}} - \frac{z}{\sqrt{z^2 + R^2}} \right]$$
     y, por ejemplo, pasar de 2.5 a 5 mm reduce el campo en la cara de la bobina de 0.223 T a 0.162 T.
5. Gire a mano: debe girar suave, **sin tirones** (cero *cogging*) y sin rozar.

### Fase 4: Rectificación y salida

```
                 ┌────────►|────────┬──────────── (+) V_DC
                 │   D1             │         │
  Terminal I1 ───┤                  │        ═╪═ C 220 µF / 50 V
                 │   D3             │         │        │
                 └────|◄────────┐   │         │     [2.2 kΩ ½ W]
                                │   │         │        │
                 ┌────────►|────┼───┘         │      [LED]
                 │   D2         │             │        │
  Terminal I8 ───┤              │             │        │
                 │   D4         │             │        │
                 └────|◄────────┴─────────────┴────────┴── (−) GND
```

(El cruce `┼` no es una conexión.) Lista de conexiones equivalente:
- D1: ánodo en I1, cátodo en (+). D2: ánodo en I8, cátodo en (+).
- D3: ánodo en (−), cátodo en I1. D4: ánodo en (−), cátodo en I8.

1. **Puente**: los terminales I1 e I8 van a las entradas AC (~) de un puente de 4 diodos. En cada semiciclo conducen dos diodos en serie.
2. **Filtro**: condensador de 220 µF × 50 V entre (+) y (−), respetando su polaridad.
3. **Indicador**: resistencia de 2.2 kΩ en serie con el LED entre (+) y (−).
4. **Bornes**: deje dos bornes en la salida DC y dos en la salida AC para medir.

### Fase 5: Conexión de la Micro-red (Controlador DC-DC, Batería, Inversor 110 V / 220 V y Carga)

```
                    ┌───────────────────────── SISTEMA DE POTENCIA Y ALTA TENSIÓN ──────────────────────────┐
                    │                                                                                       │
                    │   ┌──────────────┐     ┌──────────────┐    Fusible 15A   ┌──────────────┐             │
                    │   │              │ (+) │              │(+)    ──[===]──  │(+)           │(+)          │
    (+) V_DC ───────┼──►│ Controlador  ├────►│ Diodo Bloqueo├─────────────────►│              ├───────┐     │
 (del puente)       │   │  Buck-Boost  │     │ o Relé Corte │                  │ Batería 12V  │       │     │
                    │   │ (CC/CV-MPPT) │ (−) │              │(−)               │ (SLA/LiFePO4)│       │     │
    (−) GND ────────┼──►│              ├─────┴──────────────┴─────────────────►│(−)           │       │     │
                    │   └──────────────┘                                       └──────────────┘       │     │
                    │                                                                                 ▼     │
                    │                                                                 ┌───────────────────┐ │
                    │                                                                 │ Inversor DC-AC    │ │
                    │                                                    Línea 12V DC │ 12V -> 110V/220V  │ │
                    │                                                   (Cable AWG 14)│ (P_max: 150-300W) │ │
                    │                                                                 └──┬─────────────┬──┘ │
                    │                                                                    │(+) 110/220V │(−) │
                    │                                                               Fusible 2A         │    │
                    │                                                                 ──[===]──        │    │
                    │                                                                    │             │    │
                    │                                                             ┌──────┴─────────────┴──┐ │
                    │                                                             │ Tomacorriente Hembra  │ │
                    │                                                             │ (Salida Residencial)  │ │
                    │                                                             └───────────┬───────────┘ │
                    │                                                                         ▼             │
                    │                                                                 [Bombillo de Prueba]  │
                    │                                                                   110V/220V 5W-15W    │
                    └───────────────────────────────────────────────────────────────────────────────────────┘
```

#### Paso a paso del cableado de la micro-red:

1. **Ajuste del Controlador DC-DC (buck-boost CC/CV)**:
   - Conecte una fuente de laboratorio de 12 V a la entrada (sin batería en la salida). Con el multímetro en la salida, ajuste el potenciómetro de tensión (CV) a **14.4 V** (absorción, plomo-ácido) o **14.6 V** (LiFePO4).
   - Cortocircuite la salida a través del amperímetro y ajuste el potenciómetro de corriente (CC) a **3 A** como máximo (≈ 0.4 C para 7 Ah).
   - *Por qué*: el generador tiene $R_{int} \approx 12\,\Omega$. Un elevador de tensión fija (sin MPPT ni límite) intenta sacar más corriente de la que el generador puede dar, su entrada colapsa y deja de cargar. El modelo supone que el controlador trabaja cerca del punto de máxima potencia, $P_{max} = E_{RMS}^2/(4R_{int})$.
   - Verifique que el módulo posea diodo antirretorno integrado; si no lo tiene, coloque un diodo Schottky (1N5822 o similar de 3A) en serie en la salida (+) para evitar que la batería se descargue hacia el generador cuando este se detenga.

2. **Conexión de la Batería y Protección DC**:
   - Conecte el cable negro (AWG 14) directamente del polo negativo (−) de la batería al negativo común del sistema.
   - En el polo positivo (+), conecte inmediatamente el **portafusible aéreo con fusible automotriz de 10 A o 15 A**.
   - Conecte la salida positiva del controlador de carga después del fusible.
   - *Comprobación*: mida con el multímetro entre bornes de la batería; debe registrar entre 12.4 V y 12.8 V en reposo.

3. **Conexión del Inversor DC-AC (110 V o 220 V)**:
   - Asegúrese de que el interruptor de encendido del inversor esté en posición **OFF (Apagado)**.
   - Conecte los cables gruesos de entrada del inversor a los bornes de la batería respetando estrictamente la polaridad:
     - Cable Rojo (+) al borne positivo con fusible.
     - Cable Negro (−) al borne negativo de la batería.
   - *(Precaución: al hacer el primer contacto puede saltar una pequeña chispa inocua debida a la carga inicial de los condensadores internos del inversor; esto es normal)*.

4. **Conexión de Salida de Alta Tensión y Carga**:
   - Conecte el cable de salida AC del inversor a un tomacorriente hembra debidamente aislado en caja plástica, intercalando un fusible rápido de 1 A o 2 A en la línea viva (*Fase*).
   - Enchufe la roseta E27 con el bombillo de prueba (LED de 5W a 15W o incandescente de baja potencia).
   - Mantenga todos los cables y terminales de 110V/220V completamente cubiertos y aislados antes de encender.

---

## 6. Protocolo de Pruebas y Ensayos del Sistema Completo

### A. Ensayos en Vacío y Rectificación del Generador
Valores teóricos calculados por el modelo (`uv run generador-axial reporte`) con puente Schottky ($2V_D = 0.6\,\text{V}$). Complete las columnas medidas:

| Ensayo | Método de giro | RPM | $f_e$ (Hz) | $V_{pico}$ teórico (V) | $V_{RMS}$ teórico (V) | $V_{DC}$ teórico (V) | $V_{RMS}$ medido | $V_{DC}$ medido | LED Gen |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | Giro lento a mano | 150 | 10.0 | 3.73 | 2.64 | 3.13 | | | |
| 2 | Giro rápido a mano | 300 | 20.0 | 7.47 | 5.28 | 6.87 | | | |
| 3 | Taladro, baja velocidad | 600 | 40.0 | 14.94 | 10.56 | 14.34 | | | |
| 4 | Taladro, media velocidad | 1000 | 66.7 | 24.89 | 17.60 | 24.29 | | | |

### B. Ensayos de Carga de Batería (Nodo DC)
1. Conecte el multímetro en modo amperímetro DC (escala 10 A) en serie entre el controlador de carga y el polo (+) de la batería.
2. Gire el generador a 400, 600, 800 y 1000 RPM.
3. Observe el encendido del LED de carga del controlador y anote:
   - Corriente de inyección ($I_{chg}$): verificar que es positiva y comparar con el modelo (batería al 50 %, $\eta_c = 0.90$):

     | RPM | Potencia a batería (W) | $I_{chg}$ teórica (mA) | $I_{chg}$ medida |
     | :---: | :---: | :---: | :---: |
     | 400 | 0.92 | 75 | |
     | 600 | 2.07 | 168 | |
     | 800 | 3.68 | 299 | |
     | 1000 | 5.74 | 467 | |

   - Tensión en bornes ($V_{bat}$): sube sólo unas décimas de voltio; con corrientes < 0.5 A una batería de 7 Ah tarda más de 10 h en cargarse (≈ 21 h de 50 % a 100 % a 600 RPM).
   - Al detener el generador, verifique que la corriente cae a 0 y no se invierte (diodo antirretorno bloquea retorno).

### C. Ensayos del Inversor y Carga de 110 V / 220 V
1. Con la batería conectada y el generador en reposo, encienda el interruptor del inversor (**ON**).
2. Mida con multímetro en escala AC 600 V los bornes del tomacorriente:
   - Versión 110 V: debe medir entre **110 V y 120 V AC**. Frecuencia: **60 Hz ± 0.5 Hz**.
   - Versión 220 V: debe medir entre **220 V y 230 V AC**. Frecuencia: **50 Hz o 60 Hz**.
3. Enchufe el bombillo de prueba (bombillo LED de 15 W):
   - El bombillo debe encenderse con brillo pleno y estable.
   - Mida la corriente consumida de la batería: $I_{bat} \approx \frac{15\,\text{W}}{0.90 \times 12.3\,\text{V}} \approx 1.36\,\text{A}$.
4. Ponga a girar el generador con el taladro:
   - El generador inyecta potencia al nodo DC reduciendo la descarga neta de la batería (con 15 W: −14.6 W a 600 RPM, −8.4 W a 1200 RPM).
   - **Con 15 W la batería siempre se descarga** dentro del rango del prototipo: el equilibrio exige ≈ 1700 RPM. Con un bombillo de 5 W hay carga neta por encima de ≈ 980 RPM.
   - El inversor debe cortar cuando la batería se agota. En el modelo ideal el corte está al 20 % de carga (≈ 12.0 V en reposo) y la reconexión al 25 %; un inversor comercial, como el del modelo realista, corta por tensión en bornes (≈ 10.8 V) y reconecta por encima de 12.3 V.
   - Observe la respuesta en el osciloscopio: el canal 1 muestra la onda AC variable del generador y el canal 2 muestra la onda limpia y estable de 110 V / 220 V a 60 Hz.

### Análisis de discrepancias
1. **Diodos**: $V_{DC} = V_{pico} - 2V_D$ (−1.4 V con 1N4007, −0.6 V con 1N5819).
2. **Resistencia interna**: con carga directa, $V_{carga} = \mathcal{E}\,R_L/(R_{int} + R_L)$.
3. **Factor de acoplamiento**: si las tensiones medidas son sistemáticamente menores, estime el $k$ real como $k_{real} = 0.85 \cdot V_{medido}/V_{teórico}$.
4. **Eficiencia del inversor**: las pérdidas en el transformador elevador y los MOSFETs implican que $P_{in\_DC} = P_{AC} / \eta_{inv}$ ($\eta_{inv} \approx 85\% - 90\%$).
5. **Temperatura**: la resistencia del cobre aumenta ~0.39 %/°C.
6. **Modelo ideal frente al realista**: las tablas de esta guía salen del modelo ideal. El modelo realista (Documento 5 y visualizador) da valores algo menores, porque la fem real no es senoidal (su valor RMS es 0.93 veces el ideal), el controlador no arranca por debajo de 3.5 V y el inversor consume 3.6 W en vacío. Por ejemplo, con 15 W de carga la batería entrega ≈ 1.48 A en lugar de 1.36 A.

