/**
 * Apariencia realista de la escena: mapa de entorno de estudio (PMREM) y texturas procedurales
 * dibujadas en canvas (madera contrachapada, PLA impreso por capas, bobinado esmaltado, etiquetas).
 * No depende de archivos externos: todo se genera al iniciar.
 */
(function (GA) {
  'use strict';

  /** Generador pseudoaleatorio determinista (mulberry32): las texturas salen iguales en cada carga. */
  function aleatorio(semilla) {
    let a = semilla >>> 0;
    return () => {
      a = (a + 0x6d2b79f5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function lienzo(ancho, alto) {
    const canvas = document.createElement('canvas');
    canvas.width = ancho;
    canvas.height = alto;
    return { canvas, ctx: canvas.getContext('2d') };
  }

  function textura(canvas, { color = true, repetir = [1, 1] } = {}) {
    const t = new THREE.CanvasTexture(canvas);
    if (color) t.encoding = THREE.sRGBEncoding;
    t.wrapS = THREE.RepeatWrapping;
    t.wrapT = THREE.RepeatWrapping;
    t.repeat.set(...repetir);
    t.anisotropy = 4;
    return t;
  }

  /**
   * Estudio fotográfico: caja clara con dos softboxes y un aro cenital. Se pre-filtra con PMREM
   * para que los metales y el vidrio tengan reflejos creíbles sin cargar un HDR.
   */
  function crearEntorno(renderer) {
    const estudio = new THREE.Scene();
    const sala = new THREE.Mesh(
      new THREE.BoxGeometry(100, 60, 100),
      new THREE.MeshBasicMaterial({ color: 0x8c9a88, side: THREE.BackSide }),
    );
    sala.position.y = 20;
    estudio.add(sala);
    const suelo = new THREE.Mesh(new THREE.PlaneGeometry(100, 100), new THREE.MeshBasicMaterial({ color: 0x4d5a49 }));
    suelo.rotation.x = -Math.PI / 2;
    suelo.position.y = -9.9;
    estudio.add(suelo);

    const panel = (ancho, alto, intensidad, x, y, z, ry) => {
      const malla = new THREE.Mesh(
        new THREE.PlaneGeometry(ancho, alto),
        new THREE.MeshBasicMaterial({ color: new THREE.Color(intensidad, intensidad, intensidad * 0.97), side: THREE.DoubleSide }),
      );
      malla.position.set(x, y, z);
      malla.rotation.y = ry;
      estudio.add(malla);
    };
    panel(30, 24, 6, -45, 22, 10, Math.PI / 2);
    panel(24, 18, 3, 45, 18, -15, -Math.PI / 2);
    panel(40, 8, 2.5, 0, 26, -49, 0);
    const cenital = new THREE.Mesh(new THREE.CircleGeometry(16, 32), new THREE.MeshBasicMaterial({ color: new THREE.Color(5, 5, 4.8) }));
    cenital.rotation.x = Math.PI / 2;
    cenital.position.y = 49;
    estudio.add(cenital);

    const pmrem = new THREE.PMREMGenerator(renderer);
    const entorno = pmrem.fromScene(estudio, 0.04).texture;
    pmrem.dispose();
    estudio.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) o.material.dispose();
    });
    return entorno;
  }

  /** Tablero de contrachapado de abedul: vetas onduladas, nudos tenues y poro fino. */
  function madera() {
    const { canvas, ctx } = lienzo(1024, 512);
    const azar = aleatorio(7);
    ctx.fillStyle = '#b98f5e';
    ctx.fillRect(0, 0, 1024, 512);
    for (let i = 0; i < 160; i++) {
      const y0 = azar() * 512;
      const amplitud = 2 + azar() * 6;
      const fase = azar() * Math.PI * 2;
      const oscuro = 0.04 + azar() * 0.1;
      ctx.strokeStyle = `rgba(110, 72, 38, ${oscuro})`;
      ctx.lineWidth = 0.6 + azar() * 2.4;
      ctx.beginPath();
      for (let x = 0; x <= 1024; x += 16) {
        const y = y0 + amplitud * Math.sin((x / 1024) * Math.PI * 4 + fase) + 3 * Math.sin((x / 1024) * Math.PI * 2 + fase * 2);
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
    for (let i = 0; i < 4; i++) {
      const x = azar() * 1024;
      const y = azar() * 512;
      const g = ctx.createRadialGradient(x, y, 1, x, y, 10 + azar() * 12);
      g.addColorStop(0, 'rgba(96, 58, 28, 0.35)');
      g.addColorStop(1, 'rgba(96, 58, 28, 0)');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.ellipse(x, y, 30, 12, 0, 0, Math.PI * 2);
      ctx.fill();
    }
    const imagen = ctx.getImageData(0, 0, 1024, 512);
    for (let i = 0; i < imagen.data.length; i += 4) {
      const ruido = (azar() - 0.5) * 14;
      imagen.data[i] += ruido;
      imagen.data[i + 1] += ruido;
      imagen.data[i + 2] += ruido;
    }
    ctx.putImageData(imagen, 0, 0);
    return textura(canvas, { repetir: [1, 1] });
  }

  /** Relieve de capas de impresión FDM (0.2 mm): rayado fino para `bumpMap`. */
  function capasImpresion(periodoPx = 4) {
    const { canvas, ctx } = lienzo(64, 256);
    ctx.fillStyle = '#808080';
    ctx.fillRect(0, 0, 64, 256);
    for (let y = 0; y < 256; y += periodoPx) {
      ctx.fillStyle = '#a0a0a0';
      ctx.fillRect(0, y, 64, periodoPx / 2);
    }
    return textura(canvas, { color: false, repetir: [1, 8] });
  }

  /** Espiras de alambre esmaltado vistas de canto: franjas cobrizas con brillo especular alterno. */
  function bobinado() {
    const { canvas, ctx } = lienzo(256, 256);
    const azar = aleatorio(11);
    const paso = 4;
    for (let y = 0; y < 256; y += paso) {
      const tono = 0.85 + azar() * 0.25;
      const g = ctx.createLinearGradient(0, y, 0, y + paso);
      g.addColorStop(0, `rgb(${110 * tono}, ${52 * tono}, ${22 * tono})`);
      g.addColorStop(0.45, `rgb(${235 * tono}, ${150 * tono}, ${88 * tono})`);
      g.addColorStop(1, `rgb(${100 * tono}, ${46 * tono}, ${20 * tono})`);
      ctx.fillStyle = g;
      ctx.fillRect(0, y, 256, paso);
    }
    return textura(canvas, { repetir: [1, 1] });
  }

  /** Relieve del bobinado: crestas de alambre. */
  function relieveBobinado() {
    const { canvas, ctx } = lienzo(16, 256);
    for (let y = 0; y < 256; y += 4) {
      const g = ctx.createLinearGradient(0, y, 0, y + 4);
      g.addColorStop(0, '#202020');
      g.addColorStop(0.5, '#ffffff');
      g.addColorStop(1, '#202020');
      ctx.fillStyle = g;
      ctx.fillRect(0, y, 16, 4);
    }
    return textura(canvas, { color: false });
  }

  /**
   * Etiqueta impresa: fondo, franja de color y líneas de texto.
   * @param {object} d  { fondo, franja, tinta, titulo, lineas: string[], ancho, alto }
   */
  function etiqueta(d) {
    const ancho = d.ancho ?? 512;
    const alto = d.alto ?? 256;
    const { canvas, ctx } = lienzo(ancho, alto);
    ctx.fillStyle = d.fondo;
    ctx.fillRect(0, 0, ancho, alto);
    if (d.franja) {
      ctx.fillStyle = d.franja;
      ctx.fillRect(0, alto * 0.72, ancho, alto * 0.1);
    }
    ctx.fillStyle = d.tinta;
    ctx.textBaseline = 'top';
    const margen = ancho * 0.06;
    const escribir = (texto, peso, alturaRelativa, y) => {
      let tamano = Math.round(alto * alturaRelativa);
      ctx.font = `${peso} ${tamano}px Helvetica, Arial, sans-serif`;
      const disponible = ancho - 2 * margen;
      const medido = ctx.measureText(texto).width;
      if (medido > disponible) {
        tamano = Math.floor((tamano * disponible) / medido);
        ctx.font = `${peso} ${tamano}px Helvetica, Arial, sans-serif`;
      }
      ctx.fillText(texto, margen, y);
    };
    escribir(d.titulo, 600, 0.2, alto * 0.1);
    (d.lineas ?? []).forEach((linea, i) => escribir(linea, 400, 0.1, alto * (0.36 + i * 0.13)));
    return textura(canvas);
  }

  /** Convierte a lineal los colores sRGB de todos los materiales y luces (Three r128 trabaja en lineal). */
  function linealizarColores(raiz) {
    const vistos = new Set();
    raiz.traverse((objeto) => {
      if (objeto.isLight && objeto.color && !vistos.has(objeto)) {
        vistos.add(objeto);
        objeto.color.convertSRGBToLinear();
        if (objeto.groundColor) objeto.groundColor.convertSRGBToLinear();
      }
      const materiales = Array.isArray(objeto.material) ? objeto.material : [objeto.material];
      materiales.forEach((m) => {
        if (!m || vistos.has(m)) return;
        vistos.add(m);
        if (m.color) m.color.convertSRGBToLinear();
        if (m.emissive) m.emissive.convertSRGBToLinear();
      });
    });
  }

  GA.Materiales = Object.freeze({
    crearEntorno,
    madera,
    capasImpresion,
    bobinado,
    relieveBobinado,
    etiqueta,
    linealizarColores,
  });
})((window.GeneradorAxial = window.GeneradorAxial || {}));
