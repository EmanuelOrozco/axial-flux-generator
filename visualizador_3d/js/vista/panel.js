/** Panel de telemetría: muestra las magnitudes del generador, de la mecánica y de la microrred. */
(function (GA) {
  'use strict';

  const ETAPAS = Object.freeze({
    'sin generación': 'Sin generación',
    mppt: 'MPPT',
    'absorción': 'Absorción 14.4 V',
    'flotación': 'Flotación 13.8 V',
    'corriente máxima': 'Límite 3 A',
  });

  class PanelMetricas {
    constructor(documento, config) {
      const $ = (id) => documento.getElementById(id);
      this.config = config;
      this.campos = {
        frecuencia: $('txt-fe'),
        pico: $('txt-vp'),
        dc: $('txt-vdc'),
        par: $('txt-par'),
        potenciaEje: $('txt-peje'),
        temperatura: $('txt-temp'),
        etapa: $('txt-etapa'),
        soc: $('txt-soc'),
        tensionBateria: $('txt-vbat'),
        corrienteNeta: $('txt-ichg'),
        tensionAc: $('txt-vac'),
        potenciaAc: $('txt-pac'),
        rizado: $('val-rizado'),
      };
      this.barraSoc = $('barra-soc');
      this.rpmReal = $('val-rpm');
      this.alertas = [$('tarjeta-bateria'), $('tarjeta-inversor')];
      this.tarjetaDc = $('tarjeta-dc');
      this.tarjetaTemperatura = $('tarjeta-temp');
    }

    /**
     * @param {object}  m          Instante de `Dinamica.SimulacionDinamica`.
     * @param {object}  s          Estado de la interfaz.
     * @param {boolean} enImpulso  True mientras dura el empujón manual.
     */
    mostrar(m, s, enImpulso) {
      const c = this.campos;
      this.rpmReal.textContent = `${Math.round(m.rpm)} RPM`;
      c.frecuencia.textContent = m.frecuenciaHz.toFixed(1);
      c.pico.textContent = (m.tensionBornesRmsV * (m.femRmsV > 0 ? m.femPicoV / m.femRmsV : 0)).toFixed(2);
      c.dc.textContent = m.tensionDcV.toFixed(2);
      c.par.textContent = m.parMotrizNm.toFixed(3);
      c.potenciaEje.textContent = m.potenciaEjeW.toFixed(2);
      c.temperatura.textContent = m.temperaturaBobinasC.toFixed(1);
      c.etapa.textContent = enImpulso ? 'Impulso' : ETAPAS[m.etapaCarga] ?? m.etapaCarga;
      c.soc.textContent = (m.soc * 100).toFixed(1);
      this.barraSoc.style.width = `${(m.soc * 100).toFixed(1)}%`;
      c.tensionBateria.textContent = m.tensionBateriaV.toFixed(2);
      c.corrienteNeta.textContent = (m.corrienteNetaA * 1000).toFixed(0);
      c.tensionAc.textContent = (m.inversorActivo ? s.tensionAcRmsV : 0).toFixed(0);
      c.potenciaAc.textContent = m.potenciaAcW.toFixed(0);
      c.rizado.textContent = `rizado ${m.rizadoV.toFixed(2)} V`;

      this.alertas.forEach((elemento) => elemento.classList.toggle('alerta', m.corteBajaTension));
      const rizadoExcesivo = m.tensionDcV > 0 && m.rizadoV > 0.25 * m.tensionDcV;
      this.tarjetaDc.classList.toggle('alerta', !m.salidaDcSegura || rizadoExcesivo);
      if (!m.salidaDcSegura) {
        this.tarjetaDc.title = `Fuera de los límites del condensador o del LED (I_LED = ${(m.corrienteLedA * 1000).toFixed(1)} mA).`;
      } else if (rizadoExcesivo) {
        this.tarjetaDc.title = `Rizado de ${m.rizadoV.toFixed(1)} V: aumente el condensador de filtro.`;
      } else {
        this.tarjetaDc.title = '';
      }
      this.tarjetaTemperatura.classList.toggle('alerta', m.sobretemperatura);
      this.tarjetaTemperatura.title = m.sobretemperatura ? 'Las bobinas superan el límite del PLA (55 °C).' : '';
    }
  }

  GA.PanelMetricas = PanelMetricas;
})((window.GeneradorAxial = window.GeneradorAxial || {}));
