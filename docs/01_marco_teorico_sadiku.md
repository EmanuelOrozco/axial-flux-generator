# Fundamentación Teórica y Conceptual del Generador Electromagnético
### Basado en *Elementos de Electromagnetismo* (3.ª Edición) de Matthew N. O. Sadiku

> **Versión PDF ampliada**: [`01_marco_teorico.pdf`](01_marco_teorico.pdf) (incluye todas las deducciones paso a paso).
> La numeración de secciones corresponde a la 3.ª edición; puede variar ligeramente en otras ediciones.

---

## 1. Introducción y Contexto

El generador con imanes permanentes de neodimio ($NdFeB$) recorre el camino que Sadiku plantea desde la **Magnetostática** (Capítulos 7 y 8) hasta los **Campos Variables en el Tiempo y las Ecuaciones de Maxwell** (Capítulo 9). Este documento deduce y justifica cada aspecto del generador con esa notación.

---

## 2. Ecuaciones Fundamentales

### 2.1 Magnetostática y Materiales Magnéticos (Sadiku Cap. 7 y 8)

#### A. Ley de Gauss para el campo magnético (Sec. 7.5)
$$\nabla \cdot \mathbf{B} = 0 \quad \Longleftrightarrow \quad \oint_S \mathbf{B} \cdot d\mathbf{S} = 0$$

*Interpretación física*: no existen monopolos magnéticos. Las líneas de flujo de los imanes son cerradas: salen del polo Norte y regresan al polo Sur (por fuera del imán) y se cierran por dentro de él.

#### B. Imanación y materiales ferromagnéticos duros (Sec. 8.5 y 8.6)
En un medio material:
$$\mathbf{B} = \mu_0 (\mathbf{H} + \mathbf{M})$$

El **Neodimio-Hierro-Boro ($Nd_2Fe_{14}B$)** es un **ferromagnético duro** con un ciclo de histéresis muy ancho:
1. **Remanencia ($B_r$)**: entre $1.17\,\text{T}$ (N35) y $1.45\,\text{T}$ (N52). El prototipo usa $B_r = 1.25\,\text{T}$ (grado N38).
2. **Coercitividad ($H_c$)**: $> 850\,\text{kA/m}$; el imán no se desmagnetiza ante los campos de las corrientes inducidas.

#### C. Campo axial de un imán cilíndrico
Una imanación uniforme $\mathbf{M} = M\,\mathbf{a}_z$ equivale a una **corriente superficial ligada** $\mathbf{K}_b = \mathbf{M} \times \mathbf{a}_n = M\,\mathbf{a}_\phi$ sobre la cara lateral (Sec. 8.5), con $\nabla \times \mathbf{M} = 0$ en el interior. Es decir, el imán se comporta como un **solenoide finito** de longitud $L$ con $nI = M = B_r/\mu_0$. Aplicando la expresión del campo en el eje de un solenoide finito (Cap. 7, Biot-Savart), a una distancia $z$ de la cara:
$$B_z(z) = \frac{B_r}{2} \left[ \frac{z + L}{\sqrt{(z + L)^2 + R^2}} - \frac{z}{\sqrt{z^2 + R^2}} \right]$$

#### D. Campo medio en el espesor de la bobina (corrección del modelo)
Las espiras no están en un solo plano: ocupan desde la cara de la bobina ($z = g$, el entrehierro) hasta $z = g + h$ ($h$ = altura de la bobina). Por eso se usa el **promedio exacto** de $B_z$ en ese tramo. Como
$\int \frac{z+L}{\sqrt{(z+L)^2+R^2}}dz = \sqrt{(z+L)^2+R^2}$ y $\int \frac{z}{\sqrt{z^2+R^2}}dz = \sqrt{z^2+R^2}$:
$$\bar{B}_z = \frac{B_r}{2h}\Big[F(g+h) - F(g)\Big], \qquad F(z) = \sqrt{(z+L)^2+R^2} - \sqrt{z^2+R^2}$$

Con los datos del prototipo, $B_z(g) = 0.223\,\text{T}$ pero $\bar{B}_z = 0.155\,\text{T}$: promediar en el espesor reduce el campo (y la tensión) un 31 % respecto de evaluarlo solo en la cara.

---

### 2.2 Ley de Faraday (Sadiku Sec. 9.2)

$$\text{Forma integral: } \quad \mathcal{E}_{fem} = \oint_L \mathbf{E} \cdot d\mathbf{l} = -\frac{d\Psi}{dt}, \qquad \Psi = N\int_S \mathbf{B} \cdot d\mathbf{S}$$
$$\text{Forma diferencial: } \quad \nabla \times \mathbf{E} = -\frac{\partial \mathbf{B}}{\partial t}$$

---

## 3. FEM de Transformador vs. FEM de Movimiento (Sadiku Sec. 9.3)

### Caso 1: Espira estacionaria en campo variable
$$\mathcal{E}_{tr} = -\int_S \frac{\partial \mathbf{B}}{\partial t} \cdot d\mathbf{S}$$

### Caso 2: Espira móvil en campo estático
La fuerza de Lorentz $\mathbf{F} = q(\mathbf{v} \times \mathbf{B})$ equivale a un campo $\mathbf{E}_m = \mathbf{v} \times \mathbf{B}$:
$$\mathcal{E}_m = \oint_L (\mathbf{v} \times \mathbf{B}) \cdot d\mathbf{l}$$

### Caso 3: Caso general
$$\mathcal{E} = -\int_S \frac{\partial \mathbf{B}}{\partial t} \cdot d\mathbf{S} + \oint_L (\mathbf{v} \times \mathbf{B}) \cdot d\mathbf{l}$$

### Aplicación al generador de flujo axial
- **Marco del estator**: las bobinas están quietas y el campo en su posición varía al pasar polos N y S alternados → **fem de transformador**.
- **Marco del rotor**: el campo es estático y los conductores se mueven con $\mathbf{v} = -\boldsymbol{\omega}_m \times \mathbf{r}$ → **fem de movimiento**.

Ambos marcos dan la misma tensión: para $v \ll c$ las transformaciones de los campos se reducen a $\mathbf{E}' = \mathbf{E} + \mathbf{v}\times\mathbf{B}$, de modo que lo que en un marco es $\partial\mathbf{B}/\partial t$ en el otro es $\mathbf{v}\times\mathbf{B}$.

---

## 4. Ley de Lenz y Conservación de la Energía

El signo negativo de la ley de Faraday es la **Ley de Lenz**:
> *La corriente inducida circula en el sentido que crea un flujo que se opone a la variación del flujo que la produjo.*

### Par resistente
1. Con una carga $R_L$: $I(t) = \dfrac{\mathcal{E}(t)}{R_{int} + R_L}$.
2. Fuerza sobre cada elemento de corriente (Sec. 8.2): $d\mathbf{F} = I\, d\mathbf{l} \times \mathbf{B}$.
3. Par sobre el rotor: $\boldsymbol{\tau} = \mathbf{r} \times \mathbf{F}$, opuesto a $\boldsymbol{\omega}_m$.

**No hay energía gratuita**: $P_{mec} = \tau\,\omega_m = P_{carga} + P_{Cu}$. Con carga adaptada a 400 RPM el modelo da $P_{mec} = 2.04\,\text{W}$ y $\tau = 48.7\,\text{mN·m}$.

---

## 5. Modelo Analítico del Generador de Flujo Axial

### 5.1 Parámetros
- $P$: número de polos (imanes N-S alternados). Prototipo: $P = 8$.
- $N_b$: número de bobinas (monofásico: $N_b = P$).
- $N$: espiras por bobina (prototipo: 180).
- $\omega_m = 2\pi\,\text{RPM}/60$.
- $k$: factor de acoplamiento (flujo útil / flujo ideal), $0.70 \le k \le 0.85$.

### 5.2 Frecuencia eléctrica y flujo
$$\theta_p = \frac{2\pi}{P}, \qquad f_e = \frac{P}{2}\cdot\frac{\text{RPM}}{60} = \frac{P \cdot \text{RPM}}{120}, \qquad \omega_e = \frac{P}{2}\,\omega_m$$
$$\Phi(t) = \Phi_{max} \cos(\omega_e t), \qquad \Phi_{max} = k\,\bar{B}_z\,\pi R^2$$

### 5.3 FEM por bobina
$$\mathcal{E}(t) = -N \frac{d\Phi}{dt} = N \omega_e \Phi_{max} \sin(\omega_e t)$$
$$V_{pico} = N\,\omega_e\,\Phi_{max}, \qquad V_{RMS} = \frac{V_{pico}}{\sqrt{2}}$$

### 5.4 Bobinas en serie
Bobinas vecinas ven polos opuestos; conectadas en serie **con polaridad alternada** sus fem se suman:
$$V_{total}(t) = N_{total}\,\omega_e\,\Phi_{max}\,\sin(\omega_e t), \qquad N_{total} = N_b \cdot N$$

> **Modelo ideal frente al modelo realista.** Las secciones 5 a 10 usan el modelo ideal de régimen permanente (flujo senoidal, batería lineal). El modelo realista del Documento 5, que es el que ejecuta el visualizador, calcula el flujo por el solape imán–espira: la fem resulta no senoidal (factor de cresta 1.335 en lugar de 1.414) y su valor RMS es 0.93 veces el ideal. También añade inercia, rozamiento, inductancia, una batería de plomo-ácido con polarización, un inversor con consumo en vacío y temperatura.

---

## 6. ¿Por qué un estator sin núcleo de hierro (coreless)?

1. **Con hierro laminado**: más flujo ($\mu_r \approx 1000-5000$), pero aparecen pérdidas por histéresis y por corrientes parásitas (Cap. 9) y un fuerte **par de reluctancia (cogging)**.
2. **Sin núcleo**: $\mu_r \approx 1$, **cero cogging**, sin pérdidas en el núcleo, modelo lineal. Ideal para el laboratorio.

---

## 7. Circuito Equivalente y Rectificación

- Fuente: $\mathcal{E}(t) = V_{pico}\sin(\omega_e t)$.
- Resistencia interna, con longitud media de espira $\ell_m = \pi (D_i + D_e)/2$:
  $$R_{int} = \rho_{Cu}\,\frac{N_{total}\,\ell_m}{A_{Cu}} = 12.14\,\Omega \text{ (prototipo)}$$
- Inductancia pequeña (núcleo de aire): $Z_{int} \approx R_{int}$.
- Puente de Graetz (dos diodos conducen en cada semiciclo):
  $$V_{DC} \approx V_{pico} - 2V_D$$
  con $V_D \approx 0.7\,\text{V}$ (1N4007) o $0.3\,\text{V}$ (Schottky 1N5819).

---

## 8. Almacenamiento Electroquímico y Carga de Baterías

Una batería de ciclo profundo (plomo-ácido regulada por válvula VRLA/AGM o fosfato de hierro y litio $\text{LiFePO}_4$) actúa como amortiguador de energía (*energy buffer*), desacoplando la generación mecánica intermitente del consumo de la carga.

### 8.1 Circuito equivalente de la batería
Una celda o batería secundaria se modela como una fuerza contraelectromotriz (fem interna) $E_{oc}$ (tensión de circuito abierto, dependiente del Estado de Carga, $\text{SoC}$) en serie con una resistencia interna $R_{bat}$:
$$V_{terminal} = E_{oc}(\text{SoC}) + I_{chg} R_{bat}$$
donde para plomo-ácido de 12 V nominales:
$$E_{oc}(\text{SoC}) \approx 11.8\,\text{V} + 1.0\,\text{V} \cdot \text{SoC}$$
- $\text{SoC} = 0\,\%$ (descargada): $E_{oc} \approx 11.8\,\text{V}$.
- $\text{SoC} = 100\,\%$ (plena carga): $E_{oc} \approx 12.8\,\text{V}$ (en reposo); durante la carga sube hasta $14.4\,\text{V}$ en absorción y se mantiene en $13.8\,\text{V}$ en flotación.

### 8.2 Dinámica de carga en el tiempo
La corriente de carga $I_{chg}(t)$ incrementa la carga acumulada $Q(t)$:
$$Q(t) = Q(0) + \int_0^t I_{chg}(t')\,dt' \qquad \Longrightarrow \qquad \text{SoC}(t) = \text{SoC}(0) + \frac{1}{C_{Ah} \cdot 3600\,\text{s/h}} \int_0^t I_{chg}(t')\,dt'$$
donde $C_{Ah}$ es la capacidad de la batería en Amperios-hora ($\text{Ah}$).

### 8.3 Inductancia y almacenamiento de energía magnética en el convertidor DC-DC (Sadiku Sec. 8.8, 8.9 y 9.2)
Para cargar eficientemente la batería cuando la tensión rectificada $V_{DC}$ del generador varía con las RPM, se intercala un controlador DC-DC (Buck, Boost o Buck-Boost).

El elemento central es un **inductor de potencia** con núcleo ferromagnético cerrado (toroide de ferrita o polvo de hierro). De acuerdo con Sadiku (Sec. 8.9), la energía magnética almacenada en el campo del inductor es:
$$W_m = \frac{1}{2} \int_v \mathbf{B} \cdot \mathbf{H}\,dv = \frac{1}{2} L I^2$$
Por la ley de Faraday-Lenz aplicada a inductores (Sec. 9.2):
$$\mathcal{E}_L = -L \frac{di}{dt} \quad \Longleftrightarrow \quad v_L(t) = L \frac{di}{dt}$$
1. **Fase de acumulación (conmutador cerrado)**: la corriente del generador magnetiza el inductor, almacenando energía en el campo magnético $\mathbf{H}$ según $\frac{di}{dt} = \frac{V_{in}}{L} > 0$.
2. **Fase de descarga (conmutador abierto)**: la derivada de corriente se vuelve negativa; por la ley de Lenz, la fem autoinducida $\mathcal{E}_L$ invierte su polaridad para forzar el paso de corriente a través de un diodo hacia la batería, entregando la energía almacenada $W_m$ a una tensión regulada $V_{bat}$.
3. **Condición de carga directa**: sin convertidor elevador (diodo de bloqueo simple), la corriente solo fluye si la tensión rectificada supera el umbral de conducción:
   $$V_{DC} > V_{bat} + V_{drop} \qquad (V_{drop} \approx 0.6\,\text{V} - 0.7\,\text{V})$$
   A 300 RPM ($V_{DC} \approx 6.87\,\text{V}$), se requiere un convertidor Step-Up (Boost) o un régimen de giro superior para superar los ~12.5 V de la batería.

---

## 9. Inversión DC a AC (110 V / 220 V) y Acoplamiento Magnético

Para energizar electrodomésticos, lámparas y cargas estándar, la energía almacenada en la batería (DC) se convierte en corriente alterna de frecuencia y tensión industrial estandarizada ($110\,\text{V}_{\text{RMS}}$ a 60 Hz o $220\,\text{V}_{\text{RMS}}$ a 50/60 Hz).

### 9.1 Inducción mutua y transformador elevador (Sadiku Sec. 8.8 y 9.3)
Un inversor elevador típicamente contiene un transformador de alta frecuencia o baja frecuencia. La inductancia mutua se define en Sadiku Sec. 8.8 y la fem de transformador en la Sec. 9.3:
$$\Psi_1 = L_1 I_1 + M_{12} I_2, \qquad \Psi_2 = M_{21} I_1 + L_2 I_2, \qquad M_{12} = M_{21} = k \sqrt{L_1 L_2}$$
Para un núcleo ferromagnético cerrado con acoplamiento estrecho ($k \approx 1$):
$$\oint \mathbf{E} \cdot d\mathbf{l} = -\frac{d\Phi}{dt} \quad \Longrightarrow \quad v_1(t) = N_1 \frac{d\Phi}{dt}, \quad v_2(t) = N_2 \frac{d\Phi}{dt}$$
De donde se deduce la relación de transformación ideal:
$$\frac{V_2}{V_1} = \frac{N_2}{N_1} = a, \qquad \frac{I_2}{I_1} \approx \frac{N_1}{N_2} = \frac{1}{a}$$
- Para elevar de $12\,\text{V}$ a $110\,\text{V}_{\text{RMS}}$ ($V_{pico} = 155.6\,\text{V}$): relación de espiras $a \approx 13:1$.
- Para elevar a $220\,\text{V}_{\text{RMS}}$ ($V_{pico} = 311.1\,\text{V}$): relación de espiras $a \approx 26:1$.

### 9.2 Síntesis de onda senoidal por SPWM (Sinusoidal Pulse Width Modulation)
El puente en H de transistores MOSFET conmuta a alta frecuencia (e.g. 20 kHz – 50 kHz) modulando el ancho de pulso en función del seno de la referencia:
$$d(t) = \frac{1 + M_a \sin(\omega_0 t)}{2}, \qquad \omega_0 = 2\pi f_0 \quad (f_0 = 60\,\text{Hz} \text{ o } 50\,\text{Hz})$$
Por análisis de Fourier (teoría de circuitos; no lo cubre Sadiku), la tensión conmutada contiene la componente fundamental $\omega_0$ y armónicos centrados en múltiplos de la frecuencia portadora. Mediante un filtro pasa-bajos LC:
$$f_c = \frac{1}{2\pi \sqrt{L_f C_f}} \ll f_{portadora}$$
se eliminan los armónicos de alta frecuencia, entregando una tensión senoidal pura a la carga:
$$v_{AC}(t) = \sqrt{2}\,V_{RMS}\,\sin(2\pi f_0 t)$$

### 9.3 Conservación de la potencia a través del sistema
La potencia de la carga $P_{AC} = V_{RMS} I_{RMS} \cos(\phi)$ proviene de la batería a través de la eficiencia del inversor $\eta_{inv}$ ($85\,\% - 92\,\%$):
$$P_{bat\_out} = \frac{P_{AC}}{\eta_{inv}} \qquad \Longrightarrow \qquad I_{bat\_out} = \frac{P_{AC}}{\eta_{inv} V_{bat}}$$
Por ejemplo, el bombillo de 15 W del modelo, a 110 V, consume:
$$I_{AC} = \frac{15\,\text{W}}{110\,\text{V}} \approx 136\,\text{mA}_{\text{RMS}}$$
pero drena de la batería (con $\eta_{inv} = 0.90$ y $E_{oc} = 12.3\,\text{V}$ al 50 % de carga):
$$I_{bat\_descarga} = \frac{15\,\text{W}}{0.90 \times 12.3\,\text{V}} \approx 1.36\,\text{A}_{\text{DC}}$$
Esto ilustra por qué la batería es indispensable: permite suministrar picos de corriente a 110V/220V que el pequeño generador de laboratorio no podría sostener directamente en tiempo real.

---

## 10. Cadena Energética Completa y Balance de la Micro-red

```
[Mecánica]  ──►  [Generador Axial]  ──►  [Rectificador]  ──►  [Controlador DC-DC]  ──►  [Batería 12V]  ──►  [Inversor AC]  ──►  [Carga 110V/220V]
   P_mec             V_AC(fe), I_AC          V_DC, I_DC              I_chg, V_bat             SoC(t)          V_RMS(60Hz)          Bombillo / Carga
 P_in = τ·ωm        Faraday: -dΦ/dt       Graetz 2·VD       Faraday inductor: L·di/dt      Buffer Q(t)     Transformador: N2/N1      P_out = V·I·cosφ
```

Balance de potencia instantánea en el nodo DC de la batería:
$$P_{neto\_bat}(t) = P_{in\_chg}(t) - P_{out\_inv}(t)$$
- Si $P_{neto\_bat} > 0$: la batería se carga ($\frac{d\text{SoC}}{dt} > 0$).
- Si $P_{neto\_bat} < 0$: la batería se descarga para abastecer la carga de 110V/220V ($\frac{d\text{SoC}}{dt} < 0$).
- Si el generador se detiene (RPM = 0), la batería continúa alimentando el inversor hasta alcanzar su umbral de corte de seguridad ($\text{SoC} = 20\,\%$); se reconecta al recuperar el 25 % (histéresis, para que no oscile).

**Resultado del modelo** (`uv run generador-axial simular`, gráficas 06 y 08):
- A 600 RPM el generador entrega $2.07\,\text{W}$ a la batería (168 mA), mientras que un bombillo de 15 W exige $16.67\,\text{W}$ al inversor: la batería pierde $14.6\,\text{W}$ y llega al corte en unas 1.7 h (1.5 h con el generador parado).
- Para sostener 15 W sin descargar la batería haría falta girar a unas **1700 RPM**, por encima del rango del prototipo (1200 RPM). Una carga de 5 W se equilibra a unas 980 RPM.
- Conclusión: este generador de laboratorio **recarga** la batería; la potencia de 110 V / 220 V la aporta la batería, no el generador en tiempo real.

En el modelo realista (Documento 5 y visualizador) el inversor consume 3.6 W en vacío, de modo que el bombillo de 15 W exige unos 18.7 W a la batería; además, el corte se hace por tensión en bornes (10.8 V) y la reconexión a 12.3 V, como en un inversor comercial.

---

## 11. Resumen de Fórmulas y Parámetros del Sistema

| Parámetro / Ecuación | Referencia Sadiku | Significado Físico |
| :--- | :--- | :--- |
| $\nabla \cdot \mathbf{B} = 0$ | Sec. 7.5 | No existen monopolos; líneas de campo cerradas |
| $\mathbf{B} = \mu_0(\mathbf{H} + \mathbf{M})$ | Sec. 8.5 | Magnetización permanente de imanes NdFeB |
| $B_z(z) = \frac{B_r}{2}\left[\frac{z+L}{\sqrt{(z+L)^2+R^2}}-\frac{z}{\sqrt{z^2+R^2}}\right]$ | Sec. 7.3 & 8.5 | Campo magnético axial en el eje de un polo cilíndrico |
| $\bar{B}_z = \frac{B_r}{2h}[F(g+h)-F(g)]$ | Integración analítica | Campo medio efectivo en el volumen de las bobinas |
| $\Phi_{max} = k\,\bar{B}_z\,\pi R^2$ | Sec. 7.5 | Flujo magnético máximo concatenado por espira |
| $f_e = P \cdot \text{RPM}/120$ | Sec. 9.2 | Frecuencia eléctrica inducida en el estator |
| $\mathcal{E}(t) = -N_{total}\frac{d\Phi}{dt} = V_{pico}\sin(\omega_e t)$ | Sec. 9.2 | Ley de Faraday-Lenz en las bobinas conectadas en serie |
| $V_{pico} = N_{total}\,\omega_e\,\Phi_{max}$ | Sec. 9.2 | Tensión inducida de cresta en el generador |
| $V_{DC} = V_{pico} - 2V_D$ | Teoría de diodos | Tensión continua rectificada a la salida del puente |
| $W_m = \frac{1}{2} L I^2$ | Sec. 8.9 | Energía almacenada en el inductor del convertidor DC-DC |
| $\mathcal{E}_L = -L \frac{di}{dt}$ | Sec. 9.2 | Fem autoinducida para transferencia de energía DC-DC |
| $P_{max} = \frac{E_{RMS}^2}{4R_{int}}$, $\;I_{chg} = \frac{\eta_c P_{max}}{E_{oc}(\text{SoC})}$ | Máxima transferencia (Thévenin) | Corriente que el controlador MPPT inyecta a la batería |
| $\text{SoC}(t) = \text{SoC}_0 + \frac{1}{C}\int I_{chg}\,dt$ | Balance electroquímico | Evolución temporal del estado de carga de la batería |
| $\frac{V_{AC}}{V_{bat}} \approx \frac{N_s}{N_p}$ | Sec. 8.8 y 9.3 | Elevación de tensión en el transformador del inversor |
| $v_{AC}(t) = \sqrt{2} V_{RMS}\sin(2\pi f_0 t)$ | Teoría de circuitos (SPWM) | Tensión de salida residencial (110 V o 220 V senoidal pura) |
| $P_{in\_inv} = \frac{V_{RMS} I_{RMS} \cos\phi}{\eta_{inv}}$ | Conservación de energía | Demanda de potencia sobre el banco de baterías |
| $\tau = (P_{carga} + P_{Cu})/\omega_m$ | Sec. 8.2 & Lenz | Par resistente mecánico opuesto al giro del rotor |

