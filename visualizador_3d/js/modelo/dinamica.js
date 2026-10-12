/**
 * Modelo realista (dinámico) del sistema completo. Replica operación por operación
 * `generador_axial.dominio.dinamica` y `generador_axial.aplicacion.simulacion_dinamica`;
 * la prueba `tests/test_paridad_visualizador.py` compara ambas implementaciones paso a paso.
 *
 * Eje → rotor (inercia, rozamiento) → fem con la forma de onda real → bobinas (R(T), L) → puente de
 * diodos y condensador → controlador MPPT con sus límites → batería de plomo-ácido → inversor.
 */
(function (raiz, fabrica) {
  const modulo = fabrica();
  if (typeof module === 'object' && module.exports) module.exports = modulo;
  else (raiz.GeneradorAxial = raiz.GeneradorAxial || {}).Dinamica = modulo;
})(this, function () {
  'use strict';

  const M_POR_MM = 1e-3;
  const FACTOR_CORRIENTE_MEDIA = (2 * Math.SQRT2) / Math.PI;
  const MICROHENRIOS_WHEELER = 31.6e-6;
  const SEGUNDOS_POR_MES = 30 * 86400;

  // ------------------------------------------------------------ geometría del flujo
  function areaLente(r1, r2, d) {
    if (d >= r1 + r2) return 0.0;
    if (d <= Math.abs(r1 - r2)) return Math.PI * Math.min(r1, r2) ** 2;
    const a1 = r1 * r1 * Math.acos((d * d + r1 * r1 - r2 * r2) / (2 * d * r1));
    const a2 = r2 * r2 * Math.acos((d * d + r2 * r2 - r1 * r1) / (2 * d * r2));
    const a3 = 0.5 * Math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2));
    return a1 + a2 - a3;
  }

  function cuerdaLente(r1, r2, d) {
    if (d >= r1 + r2 || d <= Math.abs(r1 - r2)) return 0.0;
    return Math.sqrt((-d + r1 + r2) * (d + r1 - r2) * (d - r1 + r2) * (d + r1 + r2)) / d;
  }

  /** φ(θe) = Φ/(B̄·A_imán) y dφ/dθe en un periodo eléctrico (B uniforme sobre la huella del imán). */
  function perfilDeFlujo(config) {
    const { puntosRadiales, muestrasPerfil: muestras } = config.realista.integracion;
    const radioIman = (config.iman.diametroMm / 2) * M_POR_MM;
    const areaIman = Math.PI * radioIman ** 2;
    const radioInterior = (config.estator.diametroInteriorMm / 2) * M_POR_MM;
    const radioExterior = (config.estator.diametroExteriorMm / 2) * M_POR_MM;
    const radioMontaje = config.rotor.radioMontajeMm * M_POR_MM;
    const polos = config.rotor.numeroPolos;
    const pares = Math.floor(polos / 2);
    const pasoRadial = (radioExterior - radioInterior) / puntosRadiales;

    const flujo = [];
    const derivada = [];
    for (let j = 0; j < muestras; j++) {
      const anguloMecanico = ((2 * Math.PI * j) / muestras) / pares;
      let sumaFlujo = 0.0;
      let sumaDerivada = 0.0;
      for (let i = 0; i < puntosRadiales; i++) {
        const rho = radioInterior + (i + 0.5) * pasoRadial;
        for (let k = 0; k < polos; k++) {
          const x = anguloMecanico + (2 * Math.PI * k) / polos;
          const delta = Math.atan2(Math.sin(x), Math.cos(x));
          const distancia = 2 * radioMontaje * Math.sin(Math.abs(delta) / 2);
          const signo = k % 2 === 0 ? 1.0 : -1.0;
          const signoDelta = (delta > 0) - (delta < 0);
          sumaFlujo += signo * areaLente(rho, radioIman, distancia);
          sumaDerivada -= signo * cuerdaLente(rho, radioIman, distancia) * radioMontaje * Math.cos(delta / 2) * signoDelta;
        }
      }
      flujo.push(sumaFlujo / (puntosRadiales * areaIman));
      derivada.push(sumaDerivada / (puntosRadiales * areaIman * pares));
    }

    const pico = Math.max(...derivada.map(Math.abs));
    const rms = Math.sqrt(derivada.reduce((s, v) => s + v * v, 0) / muestras);
    const media = derivada.reduce((s, v) => s + Math.abs(v), 0) / muestras;
    return Object.freeze({
      flujo,
      derivada,
      picoDerivada: pico,
      rmsDerivada: rms,
      mediaAbsDerivada: media,
      factorCresta: pico / rms,
      factorMedia: media / pico,
      /** dφ/dθe interpolada linealmente (periódica). */
      derivadaEn(anguloElectricoRad) {
        const vuelta = anguloElectricoRad / (2 * Math.PI);
        const posicion = (((vuelta % 1) + 1) % 1) * muestras;
        const indice = Math.floor(posicion);
        const fraccion = posicion - indice;
        const a = derivada[indice % muestras];
        const b = derivada[(indice + 1) % muestras];
        return a + (b - a) * fraccion;
      },
    });
  }

  // ------------------------------------------------------------ parámetros derivados
  function inductanciaBobinaH(espiras, radioMedioM, alturaM, profundidadRadialM) {
    return (MICROHENRIOS_WHEELER * espiras ** 2 * radioMedioM ** 2) / (6 * radioMedioM + 9 * alturaM + 10 * profundidadRadialM);
  }

  function momentoDeInerciaRotor(config) {
    const mat = config.realista.materiales;
    const rot = config.rotor;
    const radioDisco = (rot.diametroDiscoMm / 2) * M_POR_MM;
    const espesorDisco = rot.espesorDiscoMm * M_POR_MM;
    const profundidad = rot.profundidadAlojamientoMm * M_POR_MM;
    const diametroIman = config.iman.diametroMm * M_POR_MM;
    const radioIman = diametroIman / 2;
    const espesorIman = config.iman.espesorMm * M_POR_MM;
    const radioMontaje = rot.radioMontajeMm * M_POR_MM;
    const polos = rot.numeroPolos;
    const diametroEje = config.mecanica.diametroEjeMm * M_POR_MM;

    const masaDisco = mat.densidadDiscoKgM3 * Math.PI * radioDisco ** 2 * espesorDisco;
    const radioAlojamiento = (diametroIman + 2 * config.mecanica.holguraAjusteMm * M_POR_MM) / 2;
    const masaAlojamiento = mat.densidadDiscoKgM3 * Math.PI * radioAlojamiento ** 2 * profundidad;
    const masaIman = mat.densidadImanKgM3 * Math.PI * radioIman ** 2 * espesorIman;
    const masaEje = mat.densidadEjeKgM3 * Math.PI * (diametroEje / 2) ** 2 * mat.longitudEjeM;

    const jDisco = 0.5 * masaDisco * radioDisco ** 2;
    const jAlojamientos = polos * masaAlojamiento * (radioAlojamiento ** 2 / 2 + radioMontaje ** 2);
    const jImanes = polos * masaIman * (radioIman ** 2 / 2 + radioMontaje ** 2);
    const jEje = 0.5 * masaEje * (diametroEje / 2) ** 2;
    return jDisco - jAlojamientos + jImanes + jEje;
  }

  function perdidasFoucaultW(volumenCobreM3, fraccionExpuesta, omegaElectrica, campoT, diametroHiloM, resistividadOhmM) {
    return (volumenCobreM3 * fraccionExpuesta * omegaElectrica ** 2 * campoT ** 2 * diametroHiloM ** 2) / (32 * resistividadOhmM);
  }

  // ------------------------------------------------------------ rectificador + MPPT
  function biseccion(funcion, a, b, iteraciones) {
    for (let n = 0; n < iteraciones; n++) {
      const medio = 0.5 * (a + b);
      if (funcion(medio) > 0) a = medio;
      else b = medio;
    }
    return 0.5 * (a + b);
  }

  function potenciaDc(femRms, resistencia, reactancia, caidaDiodos, corriente) {
    const tensionInterna = Math.sqrt(Math.max(0.0, femRms ** 2 - (reactancia * corriente) ** 2));
    return corriente * tensionInterna - resistencia * corriente ** 2 - caidaDiodos * FACTOR_CORRIENTE_MEDIA * corriente;
  }

  function derivadaPotenciaDc(femRms, resistencia, reactancia, caidaDiodos, corriente) {
    const tensionInterna = Math.sqrt(Math.max(1e-30, femRms ** 2 - (reactancia * corriente) ** 2));
    return (femRms ** 2 - 2 * (reactancia * corriente) ** 2) / tensionInterna
      - 2 * resistencia * corriente - caidaDiodos * FACTOR_CORRIENTE_MEDIA;
  }

  function tensionBornesRms(femRms, resistencia, reactancia, corriente) {
    return Math.max(0.0, Math.sqrt(Math.max(0.0, femRms ** 2 - (reactancia * corriente) ** 2)) - resistencia * corriente);
  }

  function rizadoPicoAPico(corrienteRms, frecuenciaHz, capacitanciaF) {
    if (frecuenciaHz <= 0) return 0.0;
    return (FACTOR_CORRIENTE_MEDIA * corrienteRms) / (2 * frecuenciaHz * capacitanciaF);
  }

  function tensionDcMedia(tensionBornes, factorCresta, factorMedia, caidaDiodos, rizado) {
    const pico = factorCresta * tensionBornes;
    return Math.max(0.0, pico - caidaDiodos - rizado / 2, pico * factorMedia - caidaDiodos);
  }

  // ------------------------------------------------------------ batería de plomo-ácido
  function interpolarCurva(curva, x) {
    if (x <= curva[0][0]) return curva[0][1];
    for (let i = 1; i < curva.length; i++) {
      const [x0, y0] = curva[i - 1];
      const [x1, y1] = curva[i];
      if (x <= x1) return y0 + ((y1 - y0) * (x - x0)) / (x1 - x0);
    }
    return curva[curva.length - 1][1];
  }

  function resistenciaPolarizacion(bat, soc, corrienteA) {
    if (corrienteA <= 0) return bat.resistenciaPolarizacionOhm;
    return bat.resistenciaPolarizacionOhm * (1 + bat.factorSobrepotencialCarga * Math.exp(bat.pendienteSobrepotencialCarga * (soc - 1)));
  }

  function eficienciaCoulomb(bat, soc) {
    if (soc <= bat.socInicioGasificacion) return bat.eficienciaCoulomb;
    const fraccion = Math.min(1.0, (soc - bat.socInicioGasificacion) / (1 - bat.socInicioGasificacion));
    return bat.eficienciaCoulomb + (bat.eficienciaCoulombLlena - bat.eficienciaCoulomb) * fraccion;
  }

  function corrienteEfectivaPeukert(bat, capacidadAh, corrienteDescargaA) {
    if (corrienteDescargaA <= 0) return 0.0;
    const corrienteNominal = capacidadAh / bat.horasRegimenNominal;
    return corrienteDescargaA * (corrienteDescargaA / corrienteNominal) ** (bat.exponentePeukert - 1);
  }

  function corrienteParaPotencia(femV, resistenciaOhm, potenciaW) {
    const discriminante = femV ** 2 + 4 * resistenciaOhm * potenciaW;
    if (discriminante <= 0) return -femV / (2 * resistenciaOhm);
    return (-femV + Math.sqrt(discriminante)) / (2 * resistenciaOhm);
  }

  // ------------------------------------------------------------ inversor
  function potenciaEntradaInversor(potenciaAcW, potenciaNominalW, eficienciaNominal, potenciaVacioW) {
    const k = (potenciaNominalW / eficienciaNominal - potenciaNominalW - potenciaVacioW) / potenciaNominalW ** 2;
    return potenciaVacioW + potenciaAcW + Math.max(0.0, k) * potenciaAcW ** 2;
  }

  // ------------------------------------------------------------ simulación
  class SimulacionDinamica {
    constructor(config) {
      this.config = config;
      this.p = config.realista;
      this.perfil = perfilDeFlujo(config);
      this.momentoInercia = momentoDeInerciaRotor(config);

      const est = config.estator;
      const diametroInterior = est.diametroInteriorMm * M_POR_MM;
      const diametroExterior = est.diametroExteriorMm * M_POR_MM;
      this._radioMedioBobina = (diametroInterior + diametroExterior) / 4;
      this._profundidadBobina = (diametroExterior - diametroInterior) / 2;
      this._alturaBobina = est.alturaBobinaMm * M_POR_MM;
      this._longitudMediaEspira = (Math.PI * (diametroInterior + diametroExterior)) / 2;
      const radioEstator = (est.diametroDiscoMm / 2) * M_POR_MM;
      this._areaDisipacion = 2 * Math.PI * radioEstator ** 2;
      this._radioIman = (config.iman.diametroMm / 2) * M_POR_MM;
      this._espesorIman = config.iman.espesorMm * M_POR_MM;
      this._areaIman = Math.PI * this._radioIman ** 2;
      this._fraccionExpuesta = this._areaIman / (Math.PI * (diametroExterior / 2) ** 2);
      this._diametroCobre = config.alambre.diametroCobreMm * M_POR_MM;
      this._areaCobre = Math.PI * (this._diametroCobre / 2) ** 2;

      this.tiempoS = 0.0;
      this.omega = 0.0;
      this.angulo = 0.0;
      this.soc = config.bateria.socInicial;
      this.tensionPolarizacion = 0.0;
      this.temperaturaBobinas = this.p.termico.temperaturaAmbienteC;
      this.inversorHabilitado = true;
    }

    entradasPorDefecto() {
      const c = this.config;
      return {
        parMotrizNm: this.p.motriz.parInicialNm,
        potenciaCargaAcW: 15.0,
        inversorEncendido: true,
        temperaturaAmbienteC: this.p.termico.temperaturaAmbienteC,
        factorTiempo: 50.0,
        entrehierroMm: c.entrehierroMm,
        espirasPorBobina: c.estator.espirasPorBobina,
        remanenciaT: c.iman.remanenciaT,
        capacitanciaFiltroUf: c.rectificador.capacitanciaFiltroUf,
      };
    }

    /** Magnitudes con el estado actual; `hLento` > 0 anticipa la polarización al final del paso (implícito). */
    _evaluar(e, omega, hLento = 0.0) {
      const c = this.config;
      const p = this.p;
      const termico = p.termico;
      const bat = p.bateria;
      const ctrl = c.controladorCarga;
      const inv = c.inversor;
      const perfil = this.perfil;
      const iteraciones = p.integracion.iteracionesBiseccion;

      const entrehierro = e.entrehierroMm * M_POR_MM;
      const remanencia = e.remanenciaT * (1 + termico.coeficienteRemanencia1K * (e.temperaturaAmbienteC - termico.temperaturaReferenciaC));
      const primitiva = (z) => Math.hypot(z + this._espesorIman, this._radioIman) - Math.hypot(z, this._radioIman);
      const campo = (0.5 * remanencia * (primitiva(entrehierro + this._alturaBobina) - primitiva(entrehierro))) / this._alturaBobina;
      const espirasTotales = c.estator.numeroBobinas * e.espirasPorBobina;
      const longitudHilo = espirasTotales * this._longitudMediaEspira;
      const factorTermico = 1 + termico.coeficienteCobre1K * (this.temperaturaBobinas - termico.temperaturaReferenciaC);
      const resistividad = c.alambre.resistividadOhmM * factorTermico;
      const resistencia = (resistividad * longitudHilo) / this._areaCobre;
      const inductancia = c.estator.numeroBobinas * inductanciaBobinaH(
        e.espirasPorBobina, this._radioMedioBobina, this._alturaBobina, this._profundidadBobina,
      );

      const omegaE = Math.floor(c.rotor.numeroPolos / 2) * omega;
      const frecuencia = omegaE / (2 * Math.PI);
      const femRms = espirasTotales * campo * this._areaIman * omegaE * perfil.rmsDerivada;
      const femPico = femRms * perfil.factorCresta;
      const reactancia = omegaE * inductancia;
      const caida = c.caidaPuenteV;
      const capacitancia = e.capacitanciaFiltroUf * 1e-6;

      const retencion = Math.exp(-hLento / bat.constanteTiempoPolarizacionS);
      const femBateria = interpolarCurva(bat.curvaOcv, this.soc) + this.tensionPolarizacion * retencion;
      const resistenciaCarga = bat.resistenciaOhmicaOhm + resistenciaPolarizacion(bat, this.soc, 1.0) * (1 - retencion);
      const resistenciaDescarga = bat.resistenciaOhmicaOhm + bat.resistenciaPolarizacionOhm * (1 - retencion);
      const inversorActivo = e.inversorEncendido && this.inversorHabilitado;
      const potenciaInversor = inversorActivo
        ? potenciaEntradaInversor(e.potenciaCargaAcW, inv.potenciaNominalW, inv.eficiencia, p.inversor.potenciaVacioW)
        : 0.0;
      const potenciaAutoconsumo = p.controlador.consumoPropioA * femBateria;

      const tensionDc = (corriente) => {
        const bornes = tensionBornesRms(femRms, resistencia, reactancia, corriente);
        const rizado = rizadoPicoAPico(corriente, frecuencia, capacitancia);
        return tensionDcMedia(bornes, perfil.factorCresta, perfil.factorMedia, caida, rizado);
      };
      const potencia = (corriente) => potenciaDc(femRms, resistencia, reactancia, caida, corriente);

      let corrienteOperacion = 0.0;
      if (femPico - caida >= ctrl.tensionMinimaArranqueV && femRms > 0) {
        const corrienteMaxima = femRms / Math.hypot(resistencia, reactancia);
        const pendiente = (i) => derivadaPotenciaDc(femRms, resistencia, reactancia, caida, i);
        if (pendiente(0.0) > 0) {
          corrienteOperacion = biseccion(pendiente, 0.0, corrienteMaxima, iteraciones);
          if (tensionDc(corrienteOperacion) < ctrl.tensionMinimaArranqueV) {
            corrienteOperacion = biseccion((i) => tensionDc(i) - ctrl.tensionMinimaArranqueV, 0.0, corrienteOperacion, iteraciones);
          }
        }
      }
      const potenciaSalidaDisponible = ctrl.eficiencia * Math.max(0.0, potencia(corrienteOperacion));

      const flotando = this.soc >= bat.socFlotacion;
      const tensionConsigna = flotando ? ctrl.tensionFlotacionV : ctrl.tensionAbsorcionV;
      const corrienteNetaLimite = (tensionConsigna - femBateria) / (tensionConsigna >= femBateria ? resistenciaCarga : resistenciaDescarga);
      const resistenciaLimite = corrienteNetaLimite >= 0 ? resistenciaCarga : resistenciaDescarga;
      const potenciaNetaLimite = corrienteNetaLimite * (femBateria + resistenciaLimite * corrienteNetaLimite);
      const limiteTension = Math.max(0.0, potenciaNetaLimite + potenciaInversor + potenciaAutoconsumo);
      const limiteCorriente = ctrl.corrienteMaximaA * femBateria;
      const potenciaSalida = Math.min(potenciaSalidaDisponible, limiteTension, limiteCorriente);

      let etapa;
      if (potenciaSalidaDisponible <= 0) etapa = 'sin generación';
      else if (potenciaSalida < potenciaSalidaDisponible) {
        if (potenciaSalida === limiteCorriente) etapa = 'corriente máxima';
        else etapa = flotando ? 'flotación' : 'absorción';
      } else etapa = 'mppt';

      let corrienteGenerador = corrienteOperacion;
      if (potenciaSalida < potenciaSalidaDisponible) {
        const potenciaRequerida = potenciaSalida / ctrl.eficiencia;
        corrienteGenerador = biseccion((i) => potenciaRequerida - potencia(i), 0.0, corrienteOperacion, iteraciones);
      }

      const bornes = tensionBornesRms(femRms, resistencia, reactancia, corrienteGenerador);
      const rizado = rizadoPicoAPico(corrienteGenerador, frecuencia, capacitancia);
      const tensionBus = tensionDcMedia(bornes, perfil.factorCresta, perfil.factorMedia, caida, rizado);
      const tensionInterna = Math.sqrt(Math.max(0.0, femRms ** 2 - (reactancia * corrienteGenerador) ** 2));
      const potenciaEm = corrienteGenerador * tensionInterna;
      const perdidasCobre = resistencia * corrienteGenerador ** 2;
      const perdidasDiodos = caida * FACTOR_CORRIENTE_MEDIA * corrienteGenerador;
      const potenciaBus = potenciaEm - perdidasCobre - perdidasDiodos;
      const potenciaBateria = potenciaSalidaDisponible > 0 ? ctrl.eficiencia * potenciaBus : 0.0;
      const volumenCobre = longitudHilo * this._areaCobre;
      const perdidasFoucault = perdidasFoucaultW(volumenCobre, this._fraccionExpuesta, omegaE, campo, this._diametroCobre, resistividad);

      const motriz = p.motriz;
      const roz = p.perdidas;
      const omegaVacio = (2 * Math.PI * motriz.velocidadVacioRpm) / 60;
      const parMotriz = e.parMotrizNm * Math.max(0.0, 1 - omega / omegaVacio);
      const parEm = omega > 0 ? (potenciaEm + perdidasFoucault) / omega : 0.0;
      const parRozamiento = omega > 0
        ? roz.parCoulombNm + roz.coeficienteViscosoNmS * omega + roz.coeficienteVentilacionNmS2 * omega ** 2
        : 0.0;

      const potenciaNeta = potenciaBateria - potenciaInversor - potenciaAutoconsumo;
      const resistenciaBateria = potenciaNeta >= 0 ? resistenciaCarga : resistenciaDescarga;
      const corrienteNeta = corrienteParaPotencia(femBateria, resistenciaBateria, potenciaNeta);
      const tensionBateria = femBateria + resistenciaBateria * corrienteNeta;

      const led = c.indicador;
      const corrienteLed = Math.max(0.0, tensionBus - led.caidaLedV) / led.resistenciaOhm;
      const salidaDcSegura = tensionBus < 0.8 * c.rectificador.tensionNominalCondensadorV
        && corrienteLed < led.corrienteMaximaLedA
        && corrienteLed ** 2 * led.resistenciaOhm < led.potenciaNominalResistenciaW;

      return {
        campo, remanencia, resistencia, reactancia, frecuencia, femRms, femPico, bornes, tensionBus, rizado,
        corrienteGenerador, parMotriz, parEm, parRozamiento, potenciaEm, perdidasCobre, perdidasDiodos,
        perdidasFoucault, potenciaBus, potenciaBateria, etapa, tensionBateria, corrienteNeta,
        corrienteCarga: potenciaBateria / tensionBateria,
        corrienteDescarga: (potenciaInversor + potenciaAutoconsumo) / tensionBateria,
        inversorActivo, potenciaInversor, corrienteLed, salidaDcSegura,
        amplitudFem: espirasTotales * campo * this._areaIman * omegaE,
      };
    }

    /** Avanza `dtS` segundos en subpasos de como máximo `pasoMaximoS`. */
    avanzar(dtS, e) {
      if (dtS > 0) {
        const subpasos = Math.ceil(dtS / this.p.integracion.pasoMaximoS - 1e-9);
        const h = dtS / subpasos;
        for (let n = 0; n < subpasos; n++) this._subpaso(h, e);
      }
      return this.instantanea(e);
    }

    _subpaso(h, e) {
      const p = this.p;
      const bat = p.bateria;
      const hLento = h * e.factorTiempo;
      const r = this._evaluar(e, this.omega, hLento);

      const parNeto = r.parMotriz - r.parEm;
      let omega;
      if (this.omega <= 0) {
        omega = parNeto > p.perdidas.parCoulombNm ? (h * (parNeto - p.perdidas.parCoulombNm)) / this.momentoInercia : 0.0;
      } else {
        omega = Math.max(0.0, this.omega + (h * (parNeto - r.parRozamiento)) / this.momentoInercia);
      }
      this.omega = omega;
      this.angulo = (this.angulo + omega * h) % (2 * Math.PI);

      const corriente = r.corrienteNeta;
      const vpFinal = resistenciaPolarizacion(bat, this.soc, corriente) * corriente;
      this.tensionPolarizacion = vpFinal + (this.tensionPolarizacion - vpFinal) * Math.exp(-hLento / bat.constanteTiempoPolarizacionS);

      const capacidadAh = this.config.bateria.capacidadAh;
      const capacidadC = capacidadAh * 3600;
      if (corriente >= 0) this.soc += (eficienciaCoulomb(bat, this.soc) * corriente * hLento) / capacidadC;
      else this.soc -= (corrienteEfectivaPeukert(bat, capacidadAh, -corriente) * hLento) / capacidadC;
      this.soc -= (bat.autodescargaMensual * hLento) / SEGUNDOS_POR_MES;
      this.soc = Math.min(1.0, Math.max(0.0, this.soc));

      const termico = p.termico;
      const conductancia = (termico.conveccionNaturalWM2k + termico.conveccionForzadaWM2kPorRadS * omega) * this._areaDisipacion;
      const temperaturaFinal = e.temperaturaAmbienteC + (r.perdidasCobre + r.perdidasFoucault) / conductancia;
      this.temperaturaBobinas = temperaturaFinal
        + (this.temperaturaBobinas - temperaturaFinal) * Math.exp((-hLento * conductancia) / termico.capacidadTermicaJK);

      if (this.inversorHabilitado && r.tensionBateria < p.inversor.tensionCorteV) this.inversorHabilitado = false;
      else if (!this.inversorHabilitado && r.tensionBateria >= p.inversor.tensionReconexionV) this.inversorHabilitado = true;
      this.tiempoS += h;
    }

    instantanea(e) {
      const r = this._evaluar(e, this.omega);
      return Object.freeze({
        tiempoS: this.tiempoS,
        rpm: (this.omega * 60) / (2 * Math.PI),
        anguloRad: this.angulo,
        frecuenciaHz: r.frecuencia,
        campoMedioT: r.campo,
        remanenciaEfectivaT: r.remanencia,
        resistenciaOhm: r.resistencia,
        reactanciaOhm: r.reactancia,
        femRmsV: r.femRms,
        femPicoV: r.femPico,
        tensionBornesRmsV: r.bornes,
        tensionDcV: r.tensionBus,
        rizadoV: r.rizado,
        corrienteGeneradorA: r.corrienteGenerador,
        parMotrizNm: r.parMotriz,
        parElectromagneticoNm: r.parEm,
        parRozamientoNm: r.parRozamiento,
        potenciaEjeW: r.parMotriz * this.omega,
        potenciaElectromagneticaW: r.potenciaEm,
        perdidasCobreW: r.perdidasCobre,
        perdidasDiodosW: r.perdidasDiodos,
        perdidasFoucaultW: r.perdidasFoucault,
        perdidasRozamientoW: r.parRozamiento * this.omega,
        potenciaDcW: r.potenciaBus,
        potenciaHaciaBateriaW: r.potenciaBateria,
        etapaCarga: r.etapa,
        soc: this.soc,
        tensionBateriaV: r.tensionBateria,
        corrienteCargaA: r.corrienteCarga,
        corrienteDescargaA: r.corrienteDescarga,
        corrienteNetaA: r.corrienteNeta,
        inversorActivo: r.inversorActivo,
        corteBajaTension: !this.inversorHabilitado,
        potenciaAcW: r.inversorActivo ? e.potenciaCargaAcW : 0.0,
        potenciaEntradaInversorW: r.potenciaInversor,
        temperaturaBobinasC: this.temperaturaBobinas,
        corrienteLedA: r.corrienteLed,
        salidaDcSegura: r.salidaDcSegura,
        sobretemperatura: this.temperaturaBobinas > this.p.termico.temperaturaMaximaPlaC,
        // Solo para el visualizador: e(θe) en bornes = −amplitud·dφ/dθe(θe).
        amplitudBornesV: r.femRms > 0 ? (r.amplitudFem * r.bornes) / r.femRms : 0.0,
      });
    }
  }

  return {
    FACTOR_CORRIENTE_MEDIA,
    areaLente,
    cuerdaLente,
    perfilDeFlujo,
    inductanciaBobinaH,
    momentoDeInerciaRotor,
    potenciaDc,
    interpolarCurva,
    potenciaEntradaInversor,
    SimulacionDinamica,
  };
});
