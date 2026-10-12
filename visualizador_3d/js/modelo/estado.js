/**
 * Estado observable de la simulación (patrón Observer).
 * Las vistas y el controlador se suscriben y reaccionan solo a las claves que cambian.
 */
(function (GA) {
  'use strict';

  class EstadoSimulacion {
    constructor(inicial) {
      this._datos = { ...inicial };
      this._oyentes = new Set();
    }

    get(clave) {
      return this._datos[clave];
    }

    instantanea() {
      return Object.freeze({ ...this._datos });
    }

    actualizar(cambios) {
      const cambiadas = Object.keys(cambios).filter((clave) => this._datos[clave] !== cambios[clave]);
      if (cambiadas.length === 0) return;
      Object.assign(this._datos, cambios);
      const instantanea = this.instantanea();
      this._oyentes.forEach((oyente) => oyente(instantanea, new Set(cambiadas)));
    }

    /** Registra un oyente, lo invoca con el estado actual y devuelve la función para darlo de baja. */
    suscribir(oyente) {
      this._oyentes.add(oyente);
      oyente(this.instantanea(), new Set(Object.keys(this._datos)));
      return () => this._oyentes.delete(oyente);
    }
  }

  GA.EstadoSimulacion = EstadoSimulacion;
})((window.GeneradorAxial = window.GeneradorAxial || {}));
