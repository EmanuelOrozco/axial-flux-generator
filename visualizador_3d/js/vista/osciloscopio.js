/**
 * Osciloscopio digital en un canvas 2D. El eje horizontal es tiempo simulado real
 * (ventana fija), de modo que la frecuencia visible no depende de los FPS.
 */
(function (GA) {
  'use strict';

  const DIVISIONES_X = 8;
  const DIVISIONES_Y = 6;
  const VENTANA_S = 0.1;
  const PERIODO_MUESTREO_S = 0.0002;
  const ESCALAS_V_POR_DIV = [0.5, 1, 2, 5, 10, 20];
  const ESCALAS_INVERSOR_V_POR_DIV = [50, 100, 200];
  const COLORES = Object.freeze({
    pantalla: 'rgba(255, 255, 255, 0.03)',
    reticula: 'rgba(255, 255, 255, 0.07)',
    eje: 'rgba(255, 255, 255, 0.22)',
    generador: '#f3c47c',
    inversor: '#cfe8c7',
  });

  /** Menor escala en la que el pico (+10 % de margen) cabe en media pantalla. */
  function escalaPara(tensionPicoV, escalas) {
    return escalas.find((e) => e * (DIVISIONES_Y / 2) >= tensionPicoV * 1.1) ?? escalas[escalas.length - 1];
  }

  class Osciloscopio {
    /** @param {object} perfil  Perfil de flujo del modelo dinámico (forma de onda real, no senoidal). */
    constructor(canvas, etiquetaEscala, perfil) {
      this.canvas = canvas;
      this.perfil = perfil;
      this.ctx = canvas.getContext('2d');
      this.etiquetaEscala = etiquetaEscala;
      this.muestras = [];
      this.tiempoS = 0;
      this.ajustarTamano();
    }

    ajustarTamano() {
      const ppp = window.devicePixelRatio || 1;
      const rect = this.canvas.getBoundingClientRect();
      this.canvas.width = rect.width * ppp;
      this.canvas.height = rect.height * ppp;
      this.ctx.setTransform(ppp, 0, 0, ppp, 0, 0);
    }

    /**
     * Registra el tramo recorrido en un fotograma con submuestras de la onda real
     * v(θe) = −A·dφ/dθe(θe), evitando el aliasing cuando f_e supera la tasa de refresco.
     */
    registrarTramo(dtS, amplitudV, anguloElectricoFinal, incrementoElectrico, tensionInversorPicoV, frecuenciaInversorHz) {
      const submuestras = Math.max(1, Math.ceil(dtS / PERIODO_MUESTREO_S));
      const anguloInicial = anguloElectricoFinal - incrementoElectrico;
      for (let k = 1; k <= submuestras; k++) {
        const fraccion = k / submuestras;
        const t = this.tiempoS + fraccion * dtS;
        this.muestras.push({
          t,
          v: -amplitudV * this.perfil.derivadaEn(anguloInicial + fraccion * incrementoElectrico),
          vInv: tensionInversorPicoV * Math.sin(2 * Math.PI * frecuenciaInversorHz * t),
        });
      }
      this.tiempoS += dtS;
      const limite = this.tiempoS - VENTANA_S;
      const primeraVigente = this.muestras.findIndex((m) => m.t >= limite);
      if (primeraVigente > 0) this.muestras.splice(0, primeraVigente);
    }

    /** @param {number} tensionInversorRmsV  0 cuando el inversor no entrega tensión. */
    dibujar(amplitudV, canal, tensionInversorRmsV) {
      const tensionPicoV = amplitudV * this.perfil.picoDerivada;
      const ancho = this.canvas.clientWidth;
      const alto = this.canvas.clientHeight;
      const voltsPorDiv = escalaPara(tensionPicoV, ESCALAS_V_POR_DIV);
      const voltsInvPorDiv = escalaPara(Math.SQRT2 * tensionInversorRmsV, ESCALAS_INVERSOR_V_POR_DIV);
      const msPorDiv = ((VENTANA_S * 1000) / DIVISIONES_X).toFixed(1);
      const apagado = tensionInversorRmsV > 0 ? '' : ' · apagado';

      if (canal === 'ch1') {
        this.etiquetaEscala.textContent = `${voltsPorDiv} V/div · ${msPorDiv} ms/div`;
      } else if (canal === 'ch2') {
        this.etiquetaEscala.textContent = `${voltsInvPorDiv} V/div${apagado}`;
      } else {
        this.etiquetaEscala.textContent = `${voltsPorDiv} / ${voltsInvPorDiv} V/div${apagado}`;
      }

      this._dibujarReticula(ancho, alto);
      this._dibujarTraza(ancho, alto, voltsPorDiv, voltsInvPorDiv, canal);
    }

    _dibujarReticula(ancho, alto) {
      const ctx = this.ctx;
      ctx.clearRect(0, 0, ancho, alto);
      ctx.fillStyle = COLORES.pantalla;
      ctx.fillRect(0, 0, ancho, alto);
      ctx.strokeStyle = COLORES.reticula;
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 1; i < DIVISIONES_X; i++) {
        ctx.moveTo((i * ancho) / DIVISIONES_X, 0);
        ctx.lineTo((i * ancho) / DIVISIONES_X, alto);
      }
      for (let j = 1; j < DIVISIONES_Y; j++) {
        ctx.moveTo(0, (j * alto) / DIVISIONES_Y);
        ctx.lineTo(ancho, (j * alto) / DIVISIONES_Y);
      }
      ctx.stroke();
      ctx.strokeStyle = COLORES.eje;
      ctx.beginPath();
      ctx.moveTo(0, alto / 2);
      ctx.lineTo(ancho, alto / 2);
      ctx.stroke();
    }

    _dibujarTraza(ancho, alto, voltsPorDiv, voltsInvPorDiv, canal) {
      if (this.muestras.length < 2) return;
      const ctx = this.ctx;
      const inicio = this.tiempoS - VENTANA_S;

      // CH2: salida del inversor (110 V o 220 V AC)
      if (canal !== 'ch1') {
        const pixelesPorVoltInv = alto / DIVISIONES_Y / voltsInvPorDiv;
        ctx.strokeStyle = COLORES.inversor;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        this.muestras.forEach(({ t, vInv }, i) => {
          const x = ((t - inicio) / VENTANA_S) * ancho;
          const y = alto / 2 - vInv * pixelesPorVoltInv;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.stroke();
      }

      // CH1: tensión del generador
      if (canal !== 'ch2') {
        const pixelesPorVolt = alto / DIVISIONES_Y / voltsPorDiv;
        ctx.strokeStyle = COLORES.generador;
        ctx.lineWidth = 1.6;
        ctx.beginPath();
        this.muestras.forEach(({ t, v }, i) => {
          const x = ((t - inicio) / VENTANA_S) * ancho;
          const y = alto / 2 - v * pixelesPorVolt;
          if (i === 0) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        });
        ctx.stroke();
      }
    }
  }

  GA.Osciloscopio = Osciloscopio;
})((window.GeneradorAxial = window.GeneradorAxial || {}));
