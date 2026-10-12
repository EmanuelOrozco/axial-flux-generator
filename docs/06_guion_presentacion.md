# Guion de la presentación (10 minutos con demo en vivo)

Diapositivas: `docs/06_presentacion.pdf` (9 diapositivas, 16:9).
Público: **general, no técnico**. Se evitan las fórmulas y se explican las ideas con comparaciones cotidianas.
Tiempo planificado: **8:50**, con **1:10 de margen** para transiciones o una pregunta rápida.

## Antes de empezar

1. Abrir el simulador **antes** de la presentación en una ventana aparte:
   ```bash
   uv run python visualizador_3d/server.py
   ```
2. Justo antes de presentar, recargar la página para partir del estado inicial (batería al 50 %, carga de 15 W, inversor encendido, tiempo 50×) y pulsar **Pausar**: al recargar, el simulador arranca en marcha.
3. Tener el PDF en pantalla completa y el simulador a un `Alt+Tab` de distancia.
4. Si la demo falla, usar la captura de la diapositiva 7 y las cifras de la diapositiva 8.

## Recomendaciones para un público general

- Decir “vueltas por minuto” en lugar de RPM, y “voltaje” o “electricidad” en lugar de fem o flujo.
- Usar siempre la misma comparación: **la dínamo de bicicleta** (genera electricidad y cuesta más pedalear con la luz encendida).
- No leer las diapositivas: tienen pocas palabras para que el público mire la demo.

## Cronograma

| # | Diapositiva | Duración | Acumulado |
|---|-------------|----------|-----------|
| 1 | Portada | 0:15 | 0:15 |
| 2 | ¿Qué construimos? | 0:45 | 1:00 |
| 3 | La idea: un imán en movimiento produce electricidad | 1:00 | 2:00 |
| 4 | El generador por dentro | 0:40 | 2:40 |
| 5 | Una simulación lo más cercana posible a la realidad | 0:50 | 3:30 |
| 6 | ¿Por qué confiar en la simulación? | 0:30 | 4:00 |
| 7 | **Demo en vivo** | 3:30 | 7:30 |
| 8 | ¿Cuánta energía produce? | 0:50 | 8:20 |
| 9 | Conclusiones y mensaje final | 0:30 | 8:50 |

## Qué decir en cada diapositiva

**1. Portada (0:15).** “Les voy a mostrar cómo un disco con imanes que gira puede cargar una batería y encender un bombillo.”

**2. ¿Qué construimos? (0:45).** Recorrer el diagrama: alguien gira el disco, los imanes pasan frente a las bobinas y producen electricidad, un convertidor la prepara, el cargador llena la batería y el inversor la convierte en la electricidad de un enchufe de casa para el bombillo.

**3. La idea (1:00).** Es la diapositiva más importante. Contar los tres pasos del dibujo. Luego, Faraday: “cuanto más rápido gira, más voltaje”. Luego, Lenz, con la dínamo: “cuanta más electricidad pedimos, más cuesta girar”. Esa es la razón por la que la energía nunca sale gratis.

**4. El generador por dentro (0:40).** Señalar en la imagen los imanes de colores (norte y sur alternados) y las bobinas de cobre. Mencionar que están separados solo 2.5 mm, porque el imán pierde fuerza muy rápido con la distancia.

**5. Simulación realista (0:50).** “Un modelo simple diría que todo funciona perfecto. El nuestro tiene en cuenta que el disco pesa, que hay rozamiento, que la batería no es perfecta y que el calor afecta.” Señalar la gráfica: tras un empujón, el disco se frena solo en menos de 3 segundos.

**6. ¿Por qué confiar? (0:30).** Usa la física del curso, el cálculo y la simulación coinciden en sus resultados, y 138 pruebas automáticas lo revisan. “Lo que van a ver no es una animación: son cálculos.”

**7. Demo en vivo (3:30).** Cambiar al simulador y seguir los pasos de la siguiente sección.

**8. ¿Cuánta energía produce? (0:50).** Girando suave (unas 8 vueltas por segundo) llega casi 1 W a la batería, lo que alcanza para un LED. De cada 10 partes de esfuerzo, 4 se convierten en energía guardada. Un bombillo de 15 W gasta más de lo que el generador produce: por eso la batería es clave, porque guarda la energía para usarla después.

**9. Conclusiones (0:30).** Repasar los cuatro puntos y leer en voz alta el mensaje final del recuadro. Abrir a preguntas.

## Guion de la demo (3:30)

| Tiempo | Acción en el simulador | Qué decir |
|--------|------------------------|-----------|
| 0:00–0:30 | Reanudar con el par en 0.050 N·m. Mostrar el osciloscopio. | “El disco empieza a girar y aquí vemos la electricidad que genera: sube y baja cada vez que pasa un imán.” |
| 0:30–1:00 | Poner el par en **0** y pulsar **Impulso**. | “Esto es un empujón con la mano. Miren cómo se frena solo: el rozamiento y la propia electricidad lo detienen.” |
| 1:00–1:30 | Par en **0.070 N·m**. | “Con un giro suave y constante se estabiliza en unas 480 vueltas por minuto.” Señalar los LED encendidos. |
| 1:30–2:00 | Mostrar el panel de batería con la carga de **15 W** encendida. Cambiar **110 V → 220 V**. | “El bombillo gasta más de lo que producimos, así que la batería se va vaciando. El inversor puede dar 110 o 220 voltios, como un enchufe.” |
| 2:00–2:40 | **Ajustes** → apagar el inversor. Par en **0.30 N·m** y tiempo **500×**. | “Ahora apagamos el bombillo, giramos con fuerza y aceleramos el tiempo: la batería se va llenando y las bobinas se calientan un poco.” |
| 2:40–3:10 | **Ajustes** → entrehierro de 2.5 a **6 mm**. | “Si separamos un poco los imanes de las bobinas, el voltaje cae: por eso deben estar tan cerca.” |
| 3:10–3:30 | Cerrar ajustes, pulsar **Despiece** y la cámara **Entrehierro**. | “Así se ve por dentro: imanes norte y sur alternados frente a las bobinas.” |

Volver al PDF en la diapositiva 8.
