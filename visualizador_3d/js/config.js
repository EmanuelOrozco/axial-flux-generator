/**
 * Parámetros del prototipo. Replica `src/generador_axial/configuracion.py`;
 * la prueba `tests/test_paridad_visualizador.py` verifica que ambos coincidan.
 */
(function (raiz, fabrica) {
  const modulo = fabrica();
  if (typeof module === 'object' && module.exports) module.exports = modulo;
  else (raiz.GeneradorAxial = raiz.GeneradorAxial || {}).CONFIG = modulo;
})(this, function () {
  'use strict';

  return Object.freeze({
    iman: Object.freeze({ grado: 'N38', remanenciaT: 1.25, diametroMm: 20, espesorMm: 5 }),
    rotor: Object.freeze({
      numeroPolos: 8,
      radioMontajeMm: 40,
      diametroDiscoMm: 110,
      espesorDiscoMm: 6,
      profundidadAlojamientoMm: 4,
    }),
    estator: Object.freeze({
      numeroBobinas: 8,
      espirasPorBobina: 180,
      diametroInteriorMm: 12,
      diametroExteriorMm: 28,
      alturaBobinaMm: 6,
      diametroDiscoMm: 120,
      espesorDiscoMm: 5,
      profundidadAlojamientoMm: 3,
    }),
    alambre: Object.freeze({ diametroCobreMm: 0.404, diametroEsmaltadoMm: 0.455, resistividadOhmM: 1.72e-8 }),
    mecanica: Object.freeze({ diametroEjeMm: 8, holguraAjusteMm: 0.2 }),
    entrehierroMm: 2.5,
    factorAcoplamiento: 0.85,
    caidaPuenteV: 0.6,
    rectificador: Object.freeze({ tensionNominalCondensadorV: 50, fraccionSeguraCondensador: 0.8, capacitanciaFiltroUf: 220 }),
    indicador: Object.freeze({
      resistenciaOhm: 2200,
      potenciaNominalResistenciaW: 0.5,
      caidaLedV: 2.0,
      corrienteMaximaLedA: 0.02,
    }),
    bateria: Object.freeze({
      tensionNominalV: 12.0,
      capacidadAh: 7.0,
      resistenciaInternaOhm: 0.05,
      tensionMinimaV: 11.8,
      tensionMaximaV: 12.8,
      socInicial: 0.5,
      socMinimoDescarga: 0.2,
      histeresisReconexionSoc: 0.05,
    }),
    controladorCarga: Object.freeze({
      tensionMinimaArranqueV: 3.5,
      tensionAbsorcionV: 14.4,
      tensionFlotacionV: 13.8,
      corrienteMaximaA: 3.0,
      eficiencia: 0.9,
    }),
    inversor: Object.freeze({
      tensionRmsV: 110.0,
      frecuenciaHz: 60.0,
      potenciaNominalW: 150.0,
      eficiencia: 0.9,
    }),
    /** Modelo realista: replica `generador_axial.dominio.realista.ParametrosRealistas`. */
    realista: Object.freeze({
      materiales: Object.freeze({ densidadDiscoKgM3: 1240.0, densidadImanKgM3: 7500.0, densidadEjeKgM3: 7850.0, longitudEjeM: 0.15 }),
      perdidas: Object.freeze({ parCoulombNm: 0.003, coeficienteViscosoNmS: 1.5e-5, coeficienteVentilacionNmS2: 1.5e-8 }),
      motriz: Object.freeze({
        parMaximoNm: 0.3, parInicialNm: 0.05, velocidadVacioRpm: 1500.0, parImpulsoNm: 0.08, duracionImpulsoS: 0.5,
      }),
      termico: Object.freeze({
        capacidadTermicaJK: 100.0,
        conveccionNaturalWM2k: 8.0,
        conveccionForzadaWM2kPorRadS: 0.15,
        temperaturaAmbienteC: 25.0,
        temperaturaReferenciaC: 20.0,
        coeficienteCobre1K: 0.00393,
        coeficienteRemanencia1K: -0.0012,
        temperaturaMaximaPlaC: 55.0,
      }),
      bateria: Object.freeze({
        curvaOcv: Object.freeze([
          [0.0, 10.5], [0.05, 11.3], [0.1, 11.6], [0.2, 11.85], [0.4, 12.1], [0.6, 12.35], [0.8, 12.58], [1.0, 12.85],
        ]),
        resistenciaOhmicaOhm: 0.025,
        resistenciaPolarizacionOhm: 0.03,
        constanteTiempoPolarizacionS: 30.0,
        factorSobrepotencialCarga: 1500.0,
        pendienteSobrepotencialCarga: 50.0,
        exponentePeukert: 1.12,
        horasRegimenNominal: 20.0,
        eficienciaCoulomb: 0.95,
        socInicioGasificacion: 0.85,
        eficienciaCoulombLlena: 0.6,
        autodescargaMensual: 0.03,
        socFlotacion: 0.995,
      }),
      inversor: Object.freeze({ potenciaVacioW: 3.6, tensionCorteV: 10.8, tensionReconexionV: 12.3 }),
      controlador: Object.freeze({ consumoPropioA: 0.008 }),
      integracion: Object.freeze({ pasoMaximoS: 0.005, puntosRadiales: 32, muestrasPerfil: 256, iteracionesBiseccion: 60 }),
    }),
    /** Opciones de la interfaz (no forman parte del diseño). */
    interfaz: Object.freeze({
      factoresTiempo: Object.freeze([1, 10, 50, 500]),
      factorTiempoInicial: 50,
      capacitanciasUf: Object.freeze([220, 1000, 2200, 4700]),
    }),
  });
});
