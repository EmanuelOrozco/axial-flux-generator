/**
 * Raíz de composición del visualizador: crea el modelo dinámico, las vistas y el controlador, y ejecuta el bucle.
 * Basado en Sadiku, Elementos de Electromagnetismo (Cap. 7 a 9).
 */
(function (GA) {
  'use strict';

  const DT_MAXIMO_S = 0.05;

  function iniciar() {
    const config = GA.CONFIG;
    const modelo = GA.Fisica.crearModelo(config);
    const simulacion = new GA.Dinamica.SimulacionDinamica(config);
    const motriz = config.realista.motriz;
    const porDefecto = simulacion.entradasPorDefecto();

    const estado = new GA.EstadoSimulacion({
      parMotrizNm: porDefecto.parMotrizNm,
      factorTiempo: config.interfaz.factorTiempoInicial,
      temperaturaAmbienteC: porDefecto.temperaturaAmbienteC,
      capacitanciaFiltroUf: porDefecto.capacitanciaFiltroUf,
      entrehierroMm: porDefecto.entrehierroMm,
      espirasPorBobina: porDefecto.espirasPorBobina,
      remanenciaT: porDefecto.remanenciaT,
      enMarcha: true,
      mostrarLineasCampo: true,
      mostrarCorrientes: true,
      vistaExplosionada: false,
      tensionAcRmsV: config.inversor.tensionRmsV,
      cargaAcWatts: porDefecto.potenciaCargaAcW,
      inversorEncendido: true,
      canalOsciloscopio: 'dual',
      impulsoManual: 0,
    });

    const escena = new GA.EscenaGenerador(document.getElementById('canvas-container'), config);
    const osciloscopio = new GA.Osciloscopio(
      document.getElementById('oscilloscope-canvas'),
      document.getElementById('osc-scale'),
      simulacion.perfil,
    );
    const panel = new GA.PanelMetricas(document, config);

    new GA.ControladorInterfaz(document, estado, escena, {
      espirasMaximas: modelo.espirasMaximas,
      parMaximoNm: motriz.parMaximoNm,
    });
    estado.suscribir((s, cambiadas) => escena.aplicarEstado(s, cambiadas));

    const ajustar = () => {
      escena.ajustarTamano();
      osciloscopio.ajustarTamano();
    };
    if ('ResizeObserver' in window) {
      const observador = new ResizeObserver(ajustar);
      observador.observe(document.getElementById('canvas-container'));
      observador.observe(document.getElementById('oscilloscope-canvas'));
    } else {
      window.addEventListener('resize', ajustar);
    }

    // El impulso dura tiempo simulado: se congela con la pausa y no depende de los FPS.
    let impulsoRestanteS = 0;
    estado.suscribir((s, cambiadas) => {
      if (cambiadas.has('impulsoManual') && s.impulsoManual) impulsoRestanteS = motriz.duracionImpulsoS;
    });

    function entradas(s) {
      return {
        parMotrizNm: impulsoRestanteS > 0 ? motriz.parImpulsoNm : s.parMotrizNm,
        potenciaCargaAcW: s.cargaAcWatts,
        inversorEncendido: s.inversorEncendido,
        temperaturaAmbienteC: s.temperaturaAmbienteC,
        factorTiempo: s.factorTiempo,
        entrehierroMm: s.entrehierroMm,
        espirasPorBobina: s.espirasPorBobina,
        remanenciaT: s.remanenciaT,
        capacitanciaFiltroUf: s.capacitanciaFiltroUf,
      };
    }

    const paresDePolos = config.rotor.numeroPolos / 2;

    /** Avanza `dtS` segundos de tiempo real simulado y actualiza las vistas (sin renderizar la escena 3D). */
    function paso(dtS) {
      const s = estado.instantanea();
      const dtSimulado = s.enMarcha ? dtS : 0;
      const anguloInicial = simulacion.angulo;
      const omegaInicial = simulacion.omega;
      const instante = simulacion.avanzar(dtSimulado, entradas(s));
      if (impulsoRestanteS > 0) {
        impulsoRestanteS -= dtSimulado;
        if (impulsoRestanteS <= 1e-9) {
          impulsoRestanteS = 0;
          estado.actualizar({ impulsoManual: 0 });
        }
      }

      // El ángulo se guarda módulo 2π: se recuperan las vueltas completas a partir de la velocidad media.
      const diferencia = instante.anguloRad - anguloInicial;
      const giroEstimado = 0.5 * (omegaInicial + simulacion.omega) * dtSimulado;
      const giro = diferencia + 2 * Math.PI * Math.round((giroEstimado - diferencia) / (2 * Math.PI));
      const anguloElectrico = paresDePolos * instante.anguloRad;
      const tensionAcRmsV = instante.inversorActivo ? s.tensionAcRmsV : 0;

      if (dtSimulado > 0) {
        osciloscopio.registrarTramo(
          dtSimulado,
          instante.amplitudBornesV,
          anguloElectrico,
          paresDePolos * giro,
          Math.SQRT2 * tensionAcRmsV,
          config.inversor.frecuenciaHz,
        );
      }
      osciloscopio.dibujar(instante.amplitudBornesV, s.canalOsciloscopio, tensionAcRmsV);
      panel.mostrar(instante, s, impulsoRestanteS > 0);
      escena.actualizar(dtS, instante, anguloElectrico, simulacion.perfil);
      return instante;
    }

    let instanteAnterior = performance.now();
    function cuadro(marca) {
      requestAnimationFrame(cuadro);
      paso(Math.min(Math.max((marca - instanteAnterior) / 1000, 0), DT_MAXIMO_S));
      instanteAnterior = marca;
      escena.renderizar();
    }
    requestAnimationFrame(cuadro);

    /** Avanza `segundos` de tiempo simulado en pasos fijos, sin esperar a los cuadros del navegador. */
    function avanzar(segundos, pasoS = DT_MAXIMO_S) {
      let ultimo = null;
      for (let t = 0; t < segundos - 1e-9; t += pasoS) ultimo = paso(Math.min(pasoS, segundos - t));
      return ultimo;
    }

    // Acceso para inspeccionar la simulación desde la consola y para las pruebas de interfaz.
    GA.aplicacion = Object.freeze({
      config,
      modelo,
      simulacion,
      estado,
      escena,
      osciloscopio,
      avanzar,
      ultimoInstante: () => simulacion.instantanea(entradas(estado.instantanea())),
    });
  }

  window.addEventListener('DOMContentLoaded', iniciar);
})((window.GeneradorAxial = window.GeneradorAxial || {}));
