# Guion de la presentación (10 minutos con demo en vivo)

Diapositivas: `docs/06_presentacion.pdf` (10 diapositivas, 16:9).
Tiempo planificado: **9:00**, con **1:00 de margen** para transiciones o una pregunta rápida.

## Antes de empezar

1. Abrir el simulador **antes** de la presentación y dejarlo en pausa en una ventana aparte:
   ```bash
   uv run python visualizador_3d/server.py
   ```
2. Recargar la página justo antes de presentar para partir del estado inicial (batería al 50 %, carga AC 15 W, inversor encendido, tiempo 50×).
3. Tener el PDF en pantalla completa y el simulador a un `Alt+Tab` de distancia.
4. Si la demo falla, usar la captura de la diapositiva 8 y las gráficas de las diapositivas 6 y 9: contienen los mismos resultados.

## Cronograma

| # | Diapositiva | Duración | Acumulado |
|---|-------------|----------|-----------|
| 1 | Portada | 0:15 | 0:15 |
| 2 | ¿Qué construimos? | 0:45 | 1:00 |
| 3 | La física | 0:50 | 1:50 |
| 4 | El diseño | 0:40 | 2:30 |
| 5 | Modelo realista | 0:50 | 3:20 |
| 6 | Dinámica y carga | 0:40 | 4:00 |
| 7 | Arquitectura del software | 0:30 | 4:30 |
| 8 | **Demo en vivo** | 3:30 | 8:00 |
| 9 | Resultados | 0:40 | 8:40 |
| 10 | Conclusiones | 0:20 | 9:00 |

## Qué decir en cada diapositiva

**1. Portada (0:15).** Presentar el proyecto: un generador de flujo axial con imanes de neodimio, diseñado a partir de la teoría de Sadiku y simulado de extremo a extremo.

**2. ¿Qué construimos? (0:45).** Recorrer el diagrama de izquierda a derecha: el par mueve el rotor, el flujo variable induce tensión en las bobinas, el puente la rectifica, el MPPT carga la batería y el inversor alimenta un bombillo a 110/220 V. Señalar la flecha roja: la corriente produce un par de Lenz que frena el rotor.

**3. La física (0:50).** Tres ideas: el campo del imán decae con la distancia (por eso importa el entrehierro), Faraday da la tensión a partir de la variación del flujo y Lenz explica por qué el generador “cuesta” más de girar cuando entrega corriente. Mencionar el campo medio en la bobina (0.15 T) y el flujo máximo (41 µWb).

**4. El diseño (0:40).** Leer solo tres datos: 8 imanes, 1440 espiras en total y 2.5 mm de entrehierro. La gráfica muestra que la tensión crece linealmente con las RPM; a 300 RPM se obtienen unos 5.3 V rms.

**5. Modelo realista (0:50).** El modelo ideal supone una onda senoidal; el real no lo es porque el imán y la bobina se solapan como dos círculos. Enumerar rápido lo que añade el modelo: inercia del rotor, límites del MPPT, batería de plomo-ácido, inversor con consumo en vacío y temperatura.

**6. Dinámica y carga (0:40).** Izquierda: un impulso con la mano lleva el rotor a ~505 RPM y se detiene en 2.7 s por fricción y Lenz. Derecha: un ciclo de carga completo pasa por MPPT, absorción y flotación.

**7. Arquitectura (0:30).** El código está en capas; el mismo modelo dinámico existe en Python y en JavaScript, y las pruebas exigen que coincidan con un error relativo de 10⁻⁹. Lo que se verá en la demo es el modelo verificado, no una animación.

**8. Demo en vivo (3:30).** Cambiar al simulador y seguir los pasos de la siguiente sección.

**9. Resultados (0:40).** Con 0.07 N·m el rotor se estabiliza en ~483 RPM y entrega 0.96 W a la batería, con un 40 % de eficiencia global. Al par máximo (0.30 N·m) llega a ~1000 RPM y 4.35 W.

**10. Conclusiones (0:20).** Faraday y Lenz explican todo el comportamiento; sin hierro el generador da pocos vatios, suficientes para cargar despacio una batería pero no para sostener una carga AC. Abrir a preguntas.

## Guion de la demo (3:30)

| Tiempo | Acción en el simulador | Qué señalar |
|--------|------------------------|-------------|
| 0:00–0:30 | Reanudar con el par en 0.050 N·m. Mostrar el osciloscopio en **CH1**. | El rotor acelera; la onda del generador no es senoidal (forma trapezoidal). |
| 0:30–1:00 | Poner el par en **0** y pulsar **Impulso**. | Sube a unos 500 RPM y frena solo en ~3 s: eso es Lenz más fricción. |
| 1:00–1:30 | Par en **0.070 N·m**. Osciloscopio en **Dual**. | ~483 RPM, ~32 Hz, 2.40 W en el eje. Se encienden el LED de DC y el LED del cargador. |
| 1:30–2:00 | Mostrar el panel de batería con carga AC **15 W** e inversor encendido. Cambiar **110 V → 220 V**. | Corriente neta ≈ −1.47 A: el generador no alcanza para la carga y la batería se descarga. CH2 muestra la salida del inversor. |
| 2:00–2:40 | **Ajustes** → apagar el inversor. Par en **0.30 N·m** y tiempo **500×**. | La corriente neta se vuelve positiva y el SoC sube visiblemente; la temperatura de las bobinas aumenta. |
| 2:40–3:10 | **Ajustes** → entrehierro de 2.5 a **6 mm**; condensador de 220 a **4700 µF**. | Menor tensión con más entrehierro (el campo decae); el rizado baja con un condensador mayor. |
| 3:10–3:30 | Cerrar ajustes, pulsar **Despiece** y cambiar de cámara (**Entrehierro**). | Los imanes N/S alternados frente a las bobinas: la geometría que produce la onda vista. |

Volver al PDF en la diapositiva 9.
