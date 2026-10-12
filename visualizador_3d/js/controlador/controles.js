/**
 * Controlador: traduce eventos del DOM en cambios de estado y refleja el estado en los controles.
 * No conoce Three.js ni las ecuaciones; solo habla con `EstadoSimulacion` y la escena por su API pública.
 */
(function (GA) {
  'use strict';

  const NOMBRE_VENTANA = 'simulador-axial';
  const TAMANO_VENTANA = { ancho: 1360, alto: 860 };

  /** Botones de opción única: id del botón → valor que asignan a la clave del estado. */
  const SELECTORES = {
    tensionAcRmsV: { 'btn-volt-110': 110, 'btn-volt-220': 220 },
    cargaAcWatts: { 'btn-load-0': 0, 'btn-load-15': 15, 'btn-load-40': 40 },
    canalOsciloscopio: { 'btn-osc-dual': 'dual', 'btn-osc-ch1': 'ch1', 'btn-osc-ch2': 'ch2' },
    factorTiempo: { 'btn-tiempo-1': 1, 'btn-tiempo-10': 10, 'btn-tiempo-50': 50, 'btn-tiempo-500': 500 },
    capacitanciaFiltroUf: { 'btn-cap-220': 220, 'btn-cap-1000': 1000, 'btn-cap-2200': 2200, 'btn-cap-4700': 4700 },
  };

  const INTERRUPTORES = {
    'check-field-lines': 'mostrarLineasCampo',
    'check-current-arrows': 'mostrarCorrientes',
    'check-exploded': 'vistaExplosionada',
    'btn-toggle-inverter': 'inversorEncendido',
  };

  /** True si la página ya está en su propia ventana (ventana emergente o modo aplicación del servidor). */
  function enVentanaPropia() {
    return window.name === NOMBRE_VENTANA || new URLSearchParams(window.location.search).has('ventana');
  }

  class ControladorInterfaz {
    constructor(documento, estado, escena, limites) {
      this.doc = documento;
      this.estado = estado;
      this.escena = escena;
      this.contadorImpulsos = 0;
      this.$ = (id) => documento.getElementById(id);

      this.$('slider-turns').max = limites.espirasMaximas;
      this.$('slider-par').max = limites.parMaximoNm;
      this._vincularDeslizadores();
      this._vincularBotones();
      this._vincularSelectores();
      this._vincularInterruptores();
      this._vincularCajonDeAjustes();
      this._vincularVentanaAparte();
      estado.suscribir((s, cambiadas) => this._reflejar(s, cambiadas));
    }

    _vincularDeslizadores() {
      const deslizadores = {
        'slider-par': ['parMotrizNm', parseFloat],
        'slider-temp': ['temperaturaAmbienteC', parseFloat],
        'slider-gap': ['entrehierroMm', parseFloat],
        'slider-turns': ['espirasPorBobina', (v) => parseInt(v, 10)],
        'slider-br': ['remanenciaT', parseFloat],
      };
      Object.entries(deslizadores).forEach(([id, [clave, convertir]]) => {
        this.$(id).addEventListener('input', (e) => {
          this.estado.actualizar({ [clave]: convertir(e.target.value) });
        });
      });
    }

    _vincularBotones() {
      this.$('btn-toggle-run').addEventListener('click', () => {
        this.estado.actualizar({ enMarcha: !this.estado.get('enMarcha') });
      });
      this.$('btn-hand-spin').addEventListener('click', () => this._impulsoManual());
      this.$('btn-despiece').addEventListener('click', () => {
        this.estado.actualizar({ vistaExplosionada: !this.estado.get('vistaExplosionada') });
      });

      const camaras = { 'cam-iso': 'isometrica', 'cam-front': 'frontal', 'cam-side': 'entrehierro' };
      Object.entries(camaras).forEach(([id, nombre]) => {
        this.$(id).addEventListener('click', () => this.escena.posicionarCamara(nombre));
      });

      const modal = this.$('help-modal');
      this.$('btn-open-help').addEventListener('click', () => modal.showModal());
      this.$('btn-close-help').addEventListener('click', () => modal.close());
    }

    _vincularSelectores() {
      Object.entries(SELECTORES).forEach(([clave, opciones]) => {
        Object.entries(opciones).forEach(([id, valor]) => {
          this.$(id).addEventListener('click', () => this.estado.actualizar({ [clave]: valor }));
        });
      });
    }

    _vincularInterruptores() {
      Object.entries(INTERRUPTORES).forEach(([id, clave]) => {
        this.$(id).addEventListener('change', (e) => this.estado.actualizar({ [clave]: e.target.checked }));
      });
    }

    _vincularCajonDeAjustes() {
      const cajon = this.$('cajon-ajustes');
      const abrir = (abierto) => {
        cajon.classList.toggle('abierto', abierto);
        cajon.setAttribute('aria-hidden', String(!abierto));
      };
      this.doc.querySelectorAll('[data-accion="abrir-ajustes"]').forEach((boton) => {
        boton.addEventListener('click', () => abrir(!cajon.classList.contains('abierto')));
      });
      this.$('btn-cerrar-ajustes').addEventListener('click', () => abrir(false));
      this.doc.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') abrir(false);
      });
    }

    _vincularVentanaAparte() {
      const boton = this.$('btn-ventana');
      if (enVentanaPropia()) {
        boton.hidden = true;
        return;
      }
      boton.addEventListener('click', () => {
        const { ancho, alto } = TAMANO_VENTANA;
        const izquierda = Math.max(0, (window.screen.availWidth - ancho) / 2);
        const arriba = Math.max(0, (window.screen.availHeight - alto) / 2);
        const ventana = window.open(
          window.location.href,
          NOMBRE_VENTANA,
          `popup=yes,width=${ancho},height=${alto},left=${izquierda},top=${arriba}`,
        );
        if (ventana) ventana.focus();
      });
    }

    /**
     * Un empujón con la mano: se retira la fuente motriz y se aplica un par breve (lo cuenta el bucle de
     * simulación); después el rotor frena solo por rozamiento y por el frenado de Lenz.
     */
    _impulsoManual() {
      this.contadorImpulsos += 1;
      this.estado.actualizar({ parMotrizNm: 0, enMarcha: true, impulsoManual: this.contadorImpulsos });
    }

    _reflejar(s, cambiadas) {
      const $ = this.$;
      if (cambiadas.has('parMotrizNm')) {
        $('slider-par').value = s.parMotrizNm;
        $('val-par').textContent = `${s.parMotrizNm.toFixed(3)} N·m`;
      }
      if (cambiadas.has('temperaturaAmbienteC')) {
        $('slider-temp').value = s.temperaturaAmbienteC;
        $('val-temp').textContent = `${Math.round(s.temperaturaAmbienteC)} °C`;
      }
      if (cambiadas.has('impulsoManual')) $('btn-hand-spin').classList.toggle('active', Boolean(s.impulsoManual));
      if (cambiadas.has('entrehierroMm')) $('val-gap').textContent = `${s.entrehierroMm.toFixed(1)} mm`;
      if (cambiadas.has('espirasPorBobina')) $('val-turns').textContent = `${s.espirasPorBobina}`;
      if (cambiadas.has('remanenciaT')) {
        $('val-br').textContent = `${s.remanenciaT.toFixed(2)} T (≈${GA.Fisica.gradoAproximado(s.remanenciaT)})`;
      }
      if (cambiadas.has('enMarcha')) {
        $('btn-toggle-run').classList.toggle('active', s.enMarcha);
        $('txt-marcha').textContent = s.enMarcha ? 'Pausar' : 'Reanudar';
      }
      Object.entries(SELECTORES).forEach(([clave, opciones]) => {
        if (!cambiadas.has(clave)) return;
        Object.entries(opciones).forEach(([id, valor]) => $(id).classList.toggle('active', s[clave] === valor));
      });
      Object.entries(INTERRUPTORES).forEach(([id, clave]) => {
        if (cambiadas.has(clave)) $(id).checked = s[clave];
      });
      if (cambiadas.has('inversorEncendido')) {
        $('txt-inversor').textContent = s.inversorEncendido ? 'Inversor encendido' : 'Inversor apagado';
      }
      if (cambiadas.has('vistaExplosionada')) $('btn-despiece').classList.toggle('active', s.vistaExplosionada);
    }
  }

  GA.ControladorInterfaz = ControladorInterfaz;
})((window.GeneradorAxial = window.GeneradorAxial || {}));
