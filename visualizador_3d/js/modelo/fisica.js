/**
 * Modelo físico del generador (mismas ecuaciones que `generador_axial.dominio.fisica`).
 * Funciones puras: no tocan el DOM ni Three.js, por eso también se ejecutan en Node.
 */
(function (raiz, fabrica) {
  const modulo = fabrica();
  if (typeof module === 'object' && module.exports) module.exports = modulo;
  else (raiz.GeneradorAxial = raiz.GeneradorAxial || {}).Fisica = modulo;
})(this, function () {
  'use strict';

  const M_POR_MM = 1e-3;

  /** B_z(z) = (Br/2) [ (z+L)/√((z+L)²+R²) − z/√(z²+R²) ] */
  function campoAxial(remanenciaT, radioM, espesorM, zM) {
    const t1 = (zM + espesorM) / Math.hypot(zM + espesorM, radioM);
    const t2 = zM / Math.hypot(zM, radioM);
    return 0.5 * remanenciaT * (t1 - t2);
  }

  /** Promedio exacto de B_z en [z0, z0 + h] usando la primitiva √((z+L)²+R²) − √(z²+R²). */
  function campoMedioEnTramo(remanenciaT, radioM, espesorM, z0M, longitudM) {
    const primitiva = (z) => Math.hypot(z + espesorM, radioM) - Math.hypot(z, radioM);
    return (0.5 * remanenciaT * (primitiva(z0M + longitudM) - primitiva(z0M))) / longitudM;
  }

  /** Grado comercial más cercano a una remanencia dada (valores típicos de catálogo). */
  function gradoAproximado(remanenciaT) {
    const grados = [
      ['N35', 1.19], ['N38', 1.24], ['N42', 1.30], ['N45', 1.34], ['N48', 1.40], ['N52', 1.45],
    ];
    return grados.reduce((mejor, g) => (Math.abs(g[1] - remanenciaT) < Math.abs(mejor[1] - remanenciaT) ? g : mejor))[0];
  }

  /** E_oc(SoC) = V_min + (V_max − V_min)·SoC, con SoC recortado a [0, 1]. */
  function tensionCircuitoAbierto(bateria, soc) {
    const s = Math.min(Math.max(soc, 0), 1);
    return bateria.tensionMinimaV + (bateria.tensionMaximaV - bateria.tensionMinimaV) * s;
  }

  /** Máxima transferencia sobre el equivalente de Thévenin: P = E_rms² / (4 R_int). */
  function potenciaMaximaExtraible(femRmsV, resistenciaInternaOhm) {
    return femRmsV ** 2 / (4 * resistenciaInternaOhm);
  }

  /**
   * Corriente que el controlador MPPT entrega a la batería: I = η·P_max / E_oc(SoC),
   * limitada por su corriente máxima y por la tensión de absorción; nula con la batería llena.
   */
  function corrienteCargaBateria({ tensionDcV, femRmsV, resistenciaInternaOhm, soc }, bateria, controlador) {
    if (soc >= 1 || tensionDcV < controlador.tensionMinimaArranqueV) return 0;
    const vOc = tensionCircuitoAbierto(bateria, soc);
    const corriente = (controlador.eficiencia * potenciaMaximaExtraible(femRmsV, resistenciaInternaOhm)) / vOc;
    const limiteAbsorcion = Math.max(0, (controlador.tensionAbsorcionV - vOc) / bateria.resistenciaInternaOhm);
    return Math.min(Math.max(corriente, 0), controlador.corrienteMaximaA, limiteAbsorcion);
  }

  /**
   * Estado de la salida DC frente a sus límites de diseño: condensador por debajo del 80 % de su tensión
   * nominal, corriente del LED y potencia de su resistencia por debajo de los valores nominales.
   */
  function salidaDc(tensionDcV, rectificador, indicador) {
    const corrienteLedA = Math.max(0, tensionDcV - indicador.caidaLedV) / indicador.resistenciaOhm;
    const potenciaResistenciaW = corrienteLedA ** 2 * indicador.resistenciaOhm;
    const limiteCondensadorV = rectificador.fraccionSeguraCondensador * rectificador.tensionNominalCondensadorV;
    return {
      corrienteLedA,
      potenciaResistenciaW,
      dentroDeLimites:
        tensionDcV < limiteCondensadorV &&
        corrienteLedA < indicador.corrienteMaximaLedA &&
        potenciaResistenciaW < indicador.potenciaNominalResistenciaW,
    };
  }

  /**
   * Crea un modelo ligado a la geometría fija de `config`.
   * `calcular` recibe los parámetros que el usuario puede variar en la interfaz.
   */
  function crearModelo(config) {
    const radioImanM = (config.iman.diametroMm / 2) * M_POR_MM;
    const espesorImanM = config.iman.espesorMm * M_POR_MM;
    const areaImanM2 = Math.PI * radioImanM ** 2;
    const est = config.estator;
    const alturaBobinaM = est.alturaBobinaMm * M_POR_MM;
    const longitudMediaEspiraM = (Math.PI * (est.diametroInteriorMm + est.diametroExteriorMm) / 2) * M_POR_MM;
    const areaCobreM2 = Math.PI * ((config.alambre.diametroCobreMm / 2) * M_POR_MM) ** 2;
    const ventanaM2 = ((est.diametroExteriorMm - est.diametroInteriorMm) / 2) * M_POR_MM * alturaBobinaM;
    const ladoEspiraM = config.alambre.diametroEsmaltadoMm * M_POR_MM;

    function calcular({ rpm, entrehierroMm, espirasPorBobina, remanenciaT, socBateria = config.bateria.socInicial }) {
      const gapM = entrehierroMm * M_POR_MM;
      const campoCaraBobinaT = campoAxial(remanenciaT, radioImanM, espesorImanM, gapM);
      const campoMedioT = campoMedioEnTramo(remanenciaT, radioImanM, espesorImanM, gapM, alturaBobinaM);
      const flujoMaximoWb = config.factorAcoplamiento * campoMedioT * areaImanM2;

      const frecuenciaHz = (config.rotor.numeroPolos * rpm) / 120;
      const omegaE = 2 * Math.PI * frecuenciaHz;
      const espirasTotales = est.numeroBobinas * espirasPorBobina;
      const tensionPicoV = espirasTotales * omegaE * flujoMaximoWb;
      const tensionDcV = Math.max(0, tensionPicoV - config.caidaPuenteV);
      const resistenciaInternaOhm = (config.alambre.resistividadOhmM * espirasTotales * longitudMediaEspiraM) / areaCobreM2;
      const tensionRmsV = tensionPicoV / Math.SQRT2;
      const corrienteCargaA = corrienteCargaBateria(
        { tensionDcV, femRmsV: tensionRmsV, resistenciaInternaOhm, soc: socBateria },
        config.bateria,
        config.controladorCarga,
      );

      const dc = salidaDc(tensionDcV, config.rectificador, config.indicador);

      return {
        campoCaraBobinaT,
        campoMedioT,
        flujoMaximoWb,
        frecuenciaHz,
        omegaE,
        tensionPicoV,
        tensionRmsV,
        tensionDcV,
        resistenciaInternaOhm,
        ocupacion: (espirasPorBobina * ladoEspiraM ** 2) / ventanaM2,
        corrienteCargaA,
        corrienteLedA: dc.corrienteLedA,
        potenciaResistenciaLedW: dc.potenciaResistenciaW,
        salidaDcSegura: dc.dentroDeLimites,
      };
    }

    /** Máximo de espiras por bobina que caben en la ventana (ocupación = 1). */
    const espirasMaximas = Math.floor(ventanaM2 / ladoEspiraM ** 2);

    return { calcular, espirasMaximas };
  }

  return {
    campoAxial,
    campoMedioEnTramo,
    gradoAproximado,
    tensionCircuitoAbierto,
    potenciaMaximaExtraible,
    corrienteCargaBateria,
    salidaDc,
    crearModelo,
  };
});
