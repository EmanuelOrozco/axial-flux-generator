/**
 * Vista 3D del generador con Three.js. Unidades: milímetros; el eje del generador es z.
 *
 * Disposición axial (z creciente): soporte trasero → disco rotor con imanes →
 * entrehierro → bobinas → placa del estator → soporte delantero.
 */
(function (GA) {
  'use strict';

  const COLORES = Object.freeze({
    norte: 0xc8553d,
    sur: 0x3f5f7a,
    cobre: 0xc98a4b,
    campo: 0xffffff,
    corriente: 0xf3c47c,
    led: 0x9be37f,
    base: 0x9db495,
    soporte: 0xdde5d8,
    cielo: 0xf4f8f1,
    suelo: 0x5f7d5b,
  });

  const Z_ROTOR = -10;
  const Z_SOPORTE_TRASERO = -55;
  const Z_SOPORTE_DELANTERO = 60;
  const Y_SUPERFICIE_BASE = -66;
  const LONGITUD_EJE = 150;
  const RADIO_EJE = 4;
  const DESPLAZAMIENTO_DESPIECE = 35;
  const CONSTANTE_TIEMPO_DESPIECE_S = 0.25;

  const CAMARAS = Object.freeze({
    isometrica: { posicion: [255, 140, 300], objetivo: [0, -12, 0] },
    frontal: { posicion: [0, 0, 300], objetivo: [0, -10, 0] },
    entrehierro: { posicion: [230, 15, -5], objetivo: [0, -5, -5] },
  });

  function material(color, opciones = {}) {
    return new THREE.MeshStandardMaterial({ color, roughness: 0.4, metalness: 0.6, ...opciones });
  }

  /** Cilindro con su eje alineado al eje z del mundo. */
  function cilindroAxial(radio, altura, segmentos, mat) {
    const malla = new THREE.Mesh(new THREE.CylinderGeometry(radio, radio, altura, segmentos), mat);
    malla.rotation.x = Math.PI / 2;
    return malla;
  }

  function posicionEnCorona(indice, cantidad, radio) {
    const angulo = (indice * 2 * Math.PI) / cantidad;
    return { x: radio * Math.cos(angulo), y: radio * Math.sin(angulo), angulo };
  }

  class EscenaGenerador {
    constructor(contenedor, config) {
      this.config = config;
      this.contenedor = contenedor;
      this.bobinas = [];
      this.desplazamientoDespiece = 0;
      this.desplazamientoObjetivo = 0;
      this.entrehierroMm = config.entrehierroMm;

      const rot = config.rotor;
      this.zCaraImanLocal = rot.espesorDiscoMm / 2 - rot.profundidadAlojamientoMm + config.iman.espesorMm;

      this._crearNucleo();
      this._crearIluminacion();
      this._crearBase();
      this._crearEje();
      this._crearRotor();
      this._crearEstator();
      this._crearLed();
      this._crearBateria();
      this._crearControladorCarga();
      this._crearInversor();
      this._crearBombilloResidencial();
      this._crearCables();
      this._reconstruirLineasDeCampo();
      this._actualizarPosicionEstator();
      this._prepararSombras();
      GA.Materiales.linealizarColores(this.escena);
    }

    /** Todo proyecta y recibe sombra salvo las ayudas didácticas translúcidas (líneas de B, anillos de corriente). */
    _prepararSombras() {
      this.escena.traverse((objeto) => {
        if (!objeto.isMesh) return;
        const translucido = objeto.material.transparent && objeto.material.opacity < 0.5;
        objeto.castShadow = !translucido;
        objeto.receiveShadow = true;
      });
    }

    _crearNucleo() {
      this.escena = new THREE.Scene();

      const { ancho, alto } = this._tamanoContenedor();
      this.camara = new THREE.PerspectiveCamera(40, ancho / alto, 0.1, 1000);
      // Fondo transparente: el degradado y el título del escenario quedan detrás del modelo.
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setClearColor(0x000000, 0);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.setSize(ancho, alto);
      this.renderer.shadowMap.enabled = true;
      this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      this.renderer.outputEncoding = THREE.sRGBEncoding;
      this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
      this.renderer.toneMappingExposure = 0.95;
      this.contenedor.appendChild(this.renderer.domElement);
      this.escena.environment = GA.Materiales.crearEntorno(this.renderer);

      this.controles = new THREE.OrbitControls(this.camara, this.renderer.domElement);
      this.controles.enableDamping = true;
      this.controles.dampingFactor = 0.06;
      this.controles.minDistance = 30;
      this.controles.maxDistance = 500;
      this.posicionarCamara('isometrica');
    }

    _crearIluminacion() {
      this.escena.add(new THREE.HemisphereLight(COLORES.cielo, COLORES.suelo, 0.3));
      const principal = new THREE.DirectionalLight(0xfff6ea, 1.4);
      principal.position.set(100, 150, 120);
      principal.castShadow = true;
      principal.shadow.mapSize.set(2048, 2048);
      principal.shadow.camera.left = -160;
      principal.shadow.camera.right = 160;
      principal.shadow.camera.top = 160;
      principal.shadow.camera.bottom = -160;
      principal.shadow.camera.near = 10;
      principal.shadow.camera.far = 500;
      principal.shadow.bias = -0.0004;
      principal.shadow.normalBias = 0.4;
      principal.shadow.radius = 4;
      this.escena.add(principal);
      const contraluz = new THREE.DirectionalLight(0xe6f2e0, 0.35);
      contraluz.position.set(-120, 60, -140);
      this.escena.add(contraluz);
    }

    _crearBase() {
      const vetas = GA.Materiales.madera();
      const canto = new THREE.MeshStandardMaterial({ color: 0xd9bf98, roughness: 0.85, metalness: 0 });
      const tablero = new THREE.MeshStandardMaterial({ map: vetas, roughness: 0.62, metalness: 0, bumpMap: vetas, bumpScale: 0.15 });
      const base = new THREE.Mesh(new THREE.BoxGeometry(260, 8, 190), [canto, canto, tablero, canto, canto, canto]);
      base.position.y = Y_SUPERFICIE_BASE - 4;
      this.escena.add(base);

      const matPata = material(0x1d1f1d, { roughness: 0.95, metalness: 0 });
      const matTornillo = material(0xb9bec2, { metalness: 1, roughness: 0.3 });
      [[-118, -83], [118, -83], [-118, 83], [118, 83]].forEach(([x, z]) => {
        const pata = new THREE.Mesh(new THREE.CylinderGeometry(7, 8, 5, 24), matPata);
        pata.position.set(x, Y_SUPERFICIE_BASE - 10.5, z);
        const tornillo = new THREE.Mesh(new THREE.CylinderGeometry(2.6, 2.6, 0.8, 6), matTornillo);
        tornillo.position.set(x, Y_SUPERFICIE_BASE + 0.4, z);
        this.escena.add(pata, tornillo);
      });

      const altura = -Y_SUPERFICIE_BASE + 14;
      const capas = GA.Materiales.capasImpresion();
      capas.repeat.set(1, altura / 2);
      const mat = material(COLORES.soporte, { roughness: 0.55, metalness: 0, bumpMap: capas, bumpScale: 0.25 });
      const geometria = new THREE.BoxGeometry(16, altura, 12);
      const geometriaPie = new THREE.BoxGeometry(40, 5, 22);
      [Z_SOPORTE_TRASERO, Z_SOPORTE_DELANTERO].forEach((z) => {
        const soporte = new THREE.Mesh(geometria, mat);
        soporte.position.set(0, Y_SUPERFICIE_BASE + altura / 2, z);
        const pie = new THREE.Mesh(geometriaPie, mat);
        pie.position.set(0, Y_SUPERFICIE_BASE + 2.5, z);
        this.escena.add(soporte, pie);
        [-14, 14].forEach((x) => {
          const tornillo = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.4, 1.6, 6), matTornillo);
          tornillo.position.set(x, Y_SUPERFICIE_BASE + 5.8, z);
          this.escena.add(tornillo);
        });
      });
    }

    _crearEje() {
      this.eje = cilindroAxial(RADIO_EJE, LONGITUD_EJE, 32, material(0xd5d9dd, { metalness: 1, roughness: 0.22 }));
      this.escena.add(this.eje);

      // Rodamiento 608: aro exterior cromado, sello de goma negro y aro interior.
      const matAro = material(0xcfd3d6, { metalness: 1, roughness: 0.18 });
      const matSello = material(0x161816, { metalness: 0, roughness: 0.7 });
      [Z_SOPORTE_TRASERO, Z_SOPORTE_DELANTERO].forEach((z) => {
        const aro = cilindroAxial(11, 7, 32, matAro);
        const sello = cilindroAxial(9.2, 7.3, 32, matSello);
        const interior = cilindroAxial(5.6, 7.6, 24, matAro);
        [aro, sello, interior].forEach((pieza) => { pieza.position.z = z; });
        this.escena.add(aro, sello, interior);
      });
    }

    _crearRotor() {
      const { rotor, iman } = this.config;
      this.grupoRotor = new THREE.Group();
      this.grupoRotor.position.z = Z_ROTOR;

      const capas = GA.Materiales.capasImpresion(3);
      capas.repeat.set(1, 3);
      const disco = cilindroAxial(rotor.diametroDiscoMm / 2, rotor.espesorDiscoMm, 96, material(0x2f3b30, {
        metalness: 0, roughness: 0.45, bumpMap: capas, bumpScale: 0.2,
      }));
      this.grupoRotor.add(disco);
      const cubo = cilindroAxial(12, 12, 32, material(0xc4c9cc, { metalness: 1, roughness: 0.28 }));
      const prisionero = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.6, 3, 6), material(0x1a1a1a, { metalness: 0.8, roughness: 0.4 }));
      prisionero.position.set(0, 12.6, 0);
      this.grupoRotor.add(cubo, prisionero);

      // Imán niquelado con la cara polar pintada (rojo N, azul S) como en los kits didácticos.
      const matNiquel = material(0xd9dcdf, { metalness: 1, roughness: 0.2 });
      const caraPintada = (color) => material(color, { metalness: 0.1, roughness: 0.35 });
      const matNorte = [matNiquel, caraPintada(COLORES.norte), matNiquel];
      const matSur = [matNiquel, caraPintada(COLORES.sur), matNiquel];
      const zCentroIman = this.zCaraImanLocal - iman.espesorMm / 2;
      for (let i = 0; i < rotor.numeroPolos; i++) {
        const { x, y } = posicionEnCorona(i, rotor.numeroPolos, rotor.radioMontajeMm);
        const esNorte = i % 2 === 0;
        const imanMalla = cilindroAxial(iman.diametroMm / 2, iman.espesorMm, 32, esNorte ? matNorte : matSur);
        imanMalla.position.set(x, y, zCentroIman);
        imanMalla.castShadow = true;
        this.grupoRotor.add(imanMalla);
      }

      this.grupoLineasCampo = new THREE.Group();
      this.materialLineasCampo = new THREE.LineBasicMaterial({ color: COLORES.campo, transparent: true, opacity: 0.75 });
      this.grupoRotor.add(this.grupoLineasCampo);
      this.escena.add(this.grupoRotor);
    }

    _crearEstator() {
      const { estator } = this.config;
      this.grupoEstator = new THREE.Group();

      const placa = cilindroAxial(estator.diametroDiscoMm / 2, estator.espesorDiscoMm, 64, new THREE.MeshPhysicalMaterial({
        color: 0xf2f5ef, metalness: 0.0, roughness: 0.35, transmission: 0.4, transparent: true, opacity: 0.55,
      }));
      placa.position.z = estator.alturaBobinaMm - estator.profundidadAlojamientoMm + estator.espesorDiscoMm / 2;
      this.grupoEstator.add(placa);

      const pie = new THREE.Mesh(new THREE.BoxGeometry(24, 14, estator.espesorDiscoMm), material(COLORES.soporte, { metalness: 0.2 }));
      pie.position.set(0, -estator.diametroDiscoMm / 2, placa.position.z);
      this.grupoEstator.add(pie);

      const pasoHiloMm = this.config.alambre.diametroEsmaltadoMm;
      this.texturaBobinado = GA.Materiales.bobinado();
      this.relieveBobinado = GA.Materiales.relieveBobinado();
      [this.texturaBobinado, this.relieveBobinado].forEach((t) => t.repeat.set(1, 1 / (64 * pasoHiloMm)));
      const geometriaBobina = this._geometriaBobina();
      const geometriaAnillo = new THREE.RingGeometry(estator.diametroInteriorMm / 2, estator.diametroExteriorMm / 2, 32);
      for (let i = 0; i < estator.numeroBobinas; i++) {
        const { x, y } = posicionEnCorona(i, estator.numeroBobinas, this.config.rotor.radioMontajeMm);
        const bobina = new THREE.Mesh(geometriaBobina, material(0xffffff, {
          map: this.texturaBobinado, bumpMap: this.relieveBobinado, bumpScale: 0.35,
          metalness: 0.75, roughness: 0.32, emissive: 0x4a2408, emissiveIntensity: 0.2,
        }));
        bobina.position.set(x, y, 0);
        bobina.castShadow = true;

        const indicador = new THREE.Mesh(geometriaAnillo, new THREE.MeshBasicMaterial({
          color: COLORES.corriente, side: THREE.DoubleSide, transparent: true, opacity: 0, depthWrite: false,
        }));
        indicador.position.set(x, y, -0.3);

        this.grupoEstator.add(bobina, indicador);
        this.bobinas.push({ bobina, indicador });
      }
      this.escena.add(this.grupoEstator);
    }

    /** Anillo extruido: sección real de la bobina (Ø interior, Ø exterior, altura). */
    _geometriaBobina() {
      const { diametroInteriorMm, diametroExteriorMm, alturaBobinaMm } = this.config.estator;
      const ri = diametroInteriorMm / 2;
      const re = diametroExteriorMm / 2;
      const h = alturaBobinaMm;
      // Perfil rectangular revolucionado; las esquinas se duplican para que las normales queden planas por cara.
      const perfil = [[ri, h], [ri, 0], [ri, 0], [re, 0], [re, 0], [re, h], [re, h], [ri, h]]
        .map(([x, y]) => new THREE.Vector2(x, y));
      const geometria = new THREE.LatheGeometry(perfil, 64);
      geometria.rotateX(Math.PI / 2);

      // UV en mm: v = radio en las caras (anillos concéntricos), v = altura en los costados (espiras apiladas).
      const pos = geometria.attributes.position;
      const nor = geometria.attributes.normal;
      const uv = geometria.attributes.uv;
      for (let i = 0; i < pos.count; i++) {
        const x = pos.getX(i);
        const y = pos.getY(i);
        const enCara = Math.abs(nor.getZ(i)) > 0.5;
        uv.setXY(i, Math.atan2(y, x) / (2 * Math.PI) + 0.5, enCara ? Math.hypot(x, y) : pos.getZ(i));
      }
      return geometria;
    }

    /** Piloto de 5 mm de la salida DC del rectificador, en la cara frontal del controlador MPPT. */
    _crearLed() {
      const grupo = new THREE.Group();
      grupo.position.set(-88, Y_SUPERFICIE_BASE + 10, -22);
      grupo.rotation.x = Math.PI / 2;
      const materialLed = new THREE.MeshPhysicalMaterial({
        color: COLORES.led, emissive: COLORES.led, emissiveIntensity: 0, transparent: true, opacity: 0.8, roughness: 0.1,
      });
      this.led = new THREE.Mesh(new THREE.CylinderGeometry(2.5, 2.5, 3, 16), materialLed);
      this.led.position.y = 1.5;
      const cupula = new THREE.Mesh(new THREE.SphereGeometry(2.5, 16, 8, 0, Math.PI * 2, 0, Math.PI / 2), materialLed);
      cupula.position.y = 3;
      this.luzLed = new THREE.PointLight(COLORES.led, 0, 60);
      this.luzLed.position.y = 8;
      grupo.add(this.led, cupula, this.luzLed);
      this.escena.add(grupo);
    }

    _crearBateria() {
      const grupo = new THREE.Group();
      grupo.position.set(-85, Y_SUPERFICIE_BASE + 16, 30);

      const abs = material(0x2b302b, { roughness: 0.55, metalness: 0 });
      const rotulo = new THREE.MeshStandardMaterial({
        roughness: 0.4,
        metalness: 0,
        map: GA.Materiales.etiqueta({
          fondo: '#2b302b', franja: '#c8553d', tinta: '#eef1ea', ancho: 512, alto: 356,
          titulo: 'SLA 12V 7Ah', lineas: ['Plomo-ácido sellada · VRLA', 'Ciclo 14.4–14.7 V · Flot. 13.6–13.8 V'],
        }),
      });
      const cuerpo = new THREE.Mesh(new THREE.BoxGeometry(46, 32, 28), [abs, abs, abs, abs, rotulo, abs]);
      grupo.add(cuerpo);

      // Tapa superior
      const tapa = new THREE.Mesh(new THREE.BoxGeometry(48, 4, 30), material(0x1c201c, { roughness: 0.5 }));
      tapa.position.y = 17;
      grupo.add(tapa);

      // Bornes positivo (rojo) y negativo (negro)
      const borneGeo = new THREE.CylinderGeometry(2.5, 2.5, 5, 16);
      const plomo = material(0xa9adb0, { roughness: 0.45, metalness: 0.9 });
      const bornePos = new THREE.Mesh(borneGeo, plomo);
      bornePos.position.set(-14, 20, 0);
      const borneNeg = new THREE.Mesh(borneGeo, plomo);
      borneNeg.position.set(14, 20, 0);
      const capuchon = new THREE.CylinderGeometry(3.4, 3.8, 3, 16);
      const capPos = new THREE.Mesh(capuchon, material(0xd32f2f, { roughness: 0.5, metalness: 0 }));
      capPos.position.set(-14, 21, 0);
      const capNeg = new THREE.Mesh(capuchon, material(0x1b1b1b, { roughness: 0.5, metalness: 0 }));
      capNeg.position.set(14, 21, 0);
      grupo.add(bornePos, borneNeg, capPos, capNeg);

      // Barra LED indicadora de estado de carga (SoC) en la cara frontal
      this.barraSoC = new THREE.Mesh(
        new THREE.BoxGeometry(24, 4, 1),
        new THREE.MeshStandardMaterial({ color: 0x9be37f, emissive: 0x9be37f, emissiveIntensity: 0.9 })
      );
      this.barraSoC.position.set(0, -11, 14.5);
      this.anchoBarraSoC = 24;
      grupo.add(this.barraSoC);

      this.escena.add(grupo);
    }

    _crearControladorCarga() {
      const grupo = new THREE.Group();
      grupo.position.set(-80, Y_SUPERFICIE_BASE + 8, -35);

      // Carcasa de aluminio con aletas disipadoras
      const aluminio = material(0xb4bdb1, { metalness: 0.9, roughness: 0.38 });
      const frente = new THREE.MeshStandardMaterial({
        metalness: 0.2,
        roughness: 0.5,
        map: GA.Materiales.etiqueta({
          fondo: '#22364a', tinta: '#e9f0f5', ancho: 512, alto: 256,
          titulo: 'MPPT', lineas: ['Solar/Wind 12V · 10A', 'DC  ●   CHG ●'],
        }),
      });
      const caja = new THREE.Mesh(new THREE.BoxGeometry(32, 16, 26), [aluminio, aluminio, aluminio, aluminio, frente, aluminio]);
      grupo.add(caja);

      const matAleta = material(0xcad2c6, { metalness: 0.9, roughness: 0.32 });
      for (let i = -10; i <= 10; i += 5) {
        const aleta = new THREE.Mesh(new THREE.BoxGeometry(28, 3, 1), matAleta);
        aleta.position.set(0, 9, i);
        grupo.add(aleta);
      }

      // LED de carga (Charging LED)
      this.ledCargador = new THREE.Mesh(
        new THREE.CylinderGeometry(1.5, 1.5, 2, 12),
        new THREE.MeshStandardMaterial({ color: 0xff9100, emissive: 0xff9100, emissiveIntensity: 0.2 })
      );
      this.ledCargador.rotation.x = Math.PI / 2;
      this.ledCargador.position.set(8, 2, 13.5);
      grupo.add(this.ledCargador);

      this.escena.add(grupo);
    }

    _crearInversor() {
      const grupo = new THREE.Group();
      grupo.position.set(80, Y_SUPERFICIE_BASE + 12, -35);

      // Carcasa de inversor 12V -> 110V/220V (aluminio anodizado)
      const anodizado = material(0x3e4c3d, { metalness: 0.7, roughness: 0.42 });
      const tapa = new THREE.MeshStandardMaterial({
        metalness: 0.6,
        roughness: 0.45,
        map: GA.Materiales.etiqueta({
          fondo: '#3e4c3d', franja: '#f3c47c', tinta: '#f1f4ee', ancho: 512, alto: 348,
          titulo: 'INVERTER 150W', lineas: ['12 V DC  →  110/220 V AC', '60 Hz · Onda senoidal pura'],
        }),
      });
      const cuerpo = new THREE.Mesh(new THREE.BoxGeometry(50, 24, 34), [anodizado, anodizado, tapa, anodizado, anodizado, anodizado]);
      grupo.add(cuerpo);

      // Placa frontal con enchufe / tomacorriente residencial
      const placaFrontal = new THREE.Mesh(new THREE.BoxGeometry(16, 16, 1), material(0xe0e0e0, { roughness: 0.5 }));
      placaFrontal.position.set(-10, 0, 17.5);
      grupo.add(placaFrontal);

      const ranura1 = new THREE.Mesh(new THREE.BoxGeometry(1.5, 5, 0.5), material(0x111111));
      ranura1.position.set(-13, 0, 18.2);
      const ranura2 = new THREE.Mesh(new THREE.BoxGeometry(1.5, 5, 0.5), material(0x111111));
      ranura2.position.set(-7, 0, 18.2);
      grupo.add(ranura1, ranura2);

      // Interruptor luminoso de encendido
      this.ledInversor = new THREE.Mesh(
        new THREE.BoxGeometry(6, 6, 2),
        new THREE.MeshStandardMaterial({ color: 0x9be37f, emissive: 0x9be37f, emissiveIntensity: 0.8 })
      );
      this.ledInversor.position.set(15, 0, 17.5);
      grupo.add(this.ledInversor);

      this.escena.add(grupo);
    }

    /** Bombillo E27 apoyado en la mesa: roseta, casquillo roscado y bulbo que nace del borde del casquillo. */
    _crearBombilloResidencial() {
      const grupo = new THREE.Group();
      grupo.position.set(100, Y_SUPERFICIE_BASE, 42);

      const alturaRoseta = 8;
      const roseta = new THREE.Mesh(new THREE.CylinderGeometry(10, 12, alturaRoseta, 32), material(0x212121, { roughness: 0.7 }));
      roseta.position.y = alturaRoseta / 2;
      roseta.castShadow = true;
      grupo.add(roseta);

      const radioCasquillo = 6.5;
      const alturaCasquillo = 7;
      const casquillo = new THREE.Mesh(
        new THREE.CylinderGeometry(radioCasquillo, radioCasquillo, alturaCasquillo, 32),
        material(0xd4af37, { metalness: 0.5, roughness: 0.35 }),
      );
      casquillo.position.y = alturaRoseta + alturaCasquillo / 2;
      grupo.add(casquillo);

      // El centro del bulbo se eleva para que su sección a la altura del casquillo tenga el radio del casquillo.
      const radioBulbo = 12;
      const yBordeCasquillo = alturaRoseta + alturaCasquillo;
      const yCentroBulbo = yBordeCasquillo + Math.sqrt(radioBulbo ** 2 - radioCasquillo ** 2);
      this.bombilloVidrio = new THREE.Mesh(new THREE.SphereGeometry(radioBulbo, 32, 24), new THREE.MeshPhysicalMaterial({
        color: 0xf6efd8,
        emissive: 0xffe082,
        emissiveIntensity: 0.0,
        transparent: true,
        opacity: 0.8,
        roughness: 0.12,
        clearcoat: 1.0,
        clearcoatRoughness: 0.05,
      }));
      this.bombilloVidrio.position.y = yCentroBulbo;
      this.bombilloVidrio.castShadow = true;
      grupo.add(this.bombilloVidrio);

      this.bombilloFilamento = new THREE.Mesh(
        new THREE.CylinderGeometry(2, 2, 6, 12),
        new THREE.MeshStandardMaterial({ color: 0xffeb3b, emissive: 0xffeb3b, emissiveIntensity: 0.0 }),
      );
      this.bombilloFilamento.position.y = yCentroBulbo;
      grupo.add(this.bombilloFilamento);

      // Luz puntual emitida que alumbra la mesa y el generador
      this.luzBombillo = new THREE.PointLight(0xfff59d, 0.0, 160, 1.2);
      this.luzBombillo.position.y = yCentroBulbo;
      grupo.add(this.luzBombillo);

      this.escena.add(grupo);
    }

    _crearCables() {
      const grupoCables = new THREE.Group();
      const crearTubo = (puntos, color) => {
        const curva = new THREE.CatmullRomCurve3(puntos.map(([x, y, z]) => new THREE.Vector3(x, y, z)));
        const geo = new THREE.TubeGeometry(curva, 24, 1.2, 8, false);
        const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.45, metalness: 0 });
        return new THREE.Mesh(geo, mat);
      };

      // Cable estator a controlador DC (rojo y negro)
      grupoCables.add(crearTubo([
        [0, -50, 10], [-40, Y_SUPERFICIE_BASE + 2, 5], [-70, Y_SUPERFICIE_BASE + 6, -30],
      ], 0xd32f2f));
      grupoCables.add(crearTubo([
        [5, -50, 10], [-35, Y_SUPERFICIE_BASE + 2, 10], [-68, Y_SUPERFICIE_BASE + 6, -28],
      ], 0x212121));

      // Cable controlador a batería
      grupoCables.add(crearTubo([
        [-80, Y_SUPERFICIE_BASE + 4, -25], [-95, Y_SUPERFICIE_BASE + 2, 0], [-95, Y_SUPERFICIE_BASE + 12, 25], [-90, Y_SUPERFICIE_BASE + 22, 30],
      ], 0xd32f2f));

      // Cable batería a inversor (DC 12V potencia)
      grupoCables.add(crearTubo([
        [-70, Y_SUPERFICIE_BASE + 20, 30], [-30, Y_SUPERFICIE_BASE + 2, 15], [30, Y_SUPERFICIE_BASE + 2, -15], [65, Y_SUPERFICIE_BASE + 10, -30],
      ], 0xd32f2f));
      grupoCables.add(crearTubo([
        [-65, Y_SUPERFICIE_BASE + 20, 30], [-25, Y_SUPERFICIE_BASE + 2, 18], [35, Y_SUPERFICIE_BASE + 2, -12], [68, Y_SUPERFICIE_BASE + 10, -28],
      ], 0x212121));

      // Cable inversor a bombillo (AC 110V/220V azul y marrón)
      grupoCables.add(crearTubo([
        [75, Y_SUPERFICIE_BASE + 8, -20], [90, Y_SUPERFICIE_BASE + 1.5, 5], [97, Y_SUPERFICIE_BASE + 1.5, 26], [98, Y_SUPERFICIE_BASE + 4, 31],
      ], 0x0288d1));
      grupoCables.add(crearTubo([
        [78, Y_SUPERFICIE_BASE + 8, -20], [93, Y_SUPERFICIE_BASE + 1.5, 6], [101, Y_SUPERFICIE_BASE + 1.5, 26], [102, Y_SUPERFICIE_BASE + 4, 31],
      ], 0x5d4037));

      this.escena.add(grupoCables);
    }

    /** Líneas de B ilustrativas: salen de cada polo, atraviesan la bobina y vuelven al polo vecino. */
    _reconstruirLineasDeCampo() {
      this.grupoLineasCampo.children.forEach((linea) => linea.geometry.dispose());
      this.grupoLineasCampo.clear();

      const { rotor, estator } = this.config;
      const z0 = this.zCaraImanLocal;
      const zCumbre = z0 + this.entrehierroMm + estator.alturaBobinaMm + 4;
      const radios = [rotor.radioMontajeMm - 6, rotor.radioMontajeMm, rotor.radioMontajeMm + 6];

      for (let i = 0; i < rotor.numeroPolos; i++) {
        const a = (i * 2 * Math.PI) / rotor.numeroPolos;
        const b = ((i + 1) * 2 * Math.PI) / rotor.numeroPolos;
        radios.forEach((r) => {
          const curva = new THREE.CubicBezierCurve3(
            new THREE.Vector3(r * Math.cos(a), r * Math.sin(a), z0),
            new THREE.Vector3(r * Math.cos(a), r * Math.sin(a), zCumbre),
            new THREE.Vector3(r * Math.cos(b), r * Math.sin(b), zCumbre),
            new THREE.Vector3(r * Math.cos(b), r * Math.sin(b), z0),
          );
          const geometria = new THREE.BufferGeometry().setFromPoints(curva.getPoints(32));
          this.grupoLineasCampo.add(new THREE.Line(geometria, this.materialLineasCampo));
        });
      }
    }

    _actualizarPosicionEstator() {
      this.grupoEstator.position.z = Z_ROTOR + this.zCaraImanLocal + this.entrehierroMm + this.desplazamientoDespiece;
    }

    aplicarEstado(estado, cambiadas) {
      this.grupoLineasCampo.visible = estado.mostrarLineasCampo;
      this.bobinas.forEach(({ indicador }) => { indicador.visible = estado.mostrarCorrientes; });
      this.desplazamientoObjetivo = estado.vistaExplosionada ? DESPLAZAMIENTO_DESPIECE : 0;
      if (cambiadas.has('entrehierroMm')) {
        this.entrehierroMm = estado.entrehierroMm;
        this._reconstruirLineasDeCampo();
        this._actualizarPosicionEstator();
      }
    }

    /**
     * @param {number} dtS              Paso de tiempo [s].
     * @param {object} m                Instante de `Dinamica.SimulacionDinamica`.
     * @param {number} anguloElectrico  (P/2)·ángulo mecánico [rad].
     * @param {object} perfil           Perfil de flujo (forma de onda real de la fem).
     */
    actualizar(dtS, m, anguloElectrico, perfil) {
      this.grupoRotor.rotation.z = m.anguloRad;
      this.eje.rotation.y = m.anguloRad;

      const alfa = 1 - Math.exp(-dtS / CONSTANTE_TIEMPO_DESPIECE_S);
      this.desplazamientoDespiece += (this.desplazamientoObjetivo - this.desplazamientoDespiece) * alfa;
      this._actualizarPosicionEstator();

      const intensidad = m.femRmsV > 0 ? Math.abs(perfil.derivadaEn(anguloElectrico)) / perfil.picoDerivada : 0;
      this.bobinas.forEach(({ bobina, indicador }) => {
        indicador.material.opacity = intensidad * 0.85;
        bobina.material.emissiveIntensity = 0.2 + intensidad * 0.6;
      });

      const brillo = 2.5 * Math.min(1, m.corrienteLedA / this.config.indicador.corrienteMaximaLedA);
      this.luzLed.intensity = brillo;
      this.led.material.emissiveIntensity = brillo;

      const colorSoC = m.soc > 0.6 ? 0x9be37f : m.soc > 0.25 ? 0xf3c47c : 0xc8553d;
      this.barraSoC.material.color.setHex(colorSoC).convertSRGBToLinear();
      this.barraSoC.material.emissive.setHex(colorSoC).convertSRGBToLinear();
      const fraccion = Math.max(m.soc, 0.02);
      this.barraSoC.scale.x = fraccion;
      this.barraSoC.position.x = (-this.anchoBarraSoC * (1 - fraccion)) / 2;

      this.ledCargador.material.emissiveIntensity = m.corrienteCargaA > 0 ? 1.0 : 0.1;
      this.ledInversor.material.emissiveIntensity = m.inversorActivo ? 0.8 : 0.05;

      const brilloBombillo = m.potenciaAcW > 0 ? Math.min(2.5, (m.potenciaAcW / 15) * 1.5) : 0;
      this.luzBombillo.intensity = brilloBombillo * 1.8;
      this.bombilloVidrio.material.emissiveIntensity = brilloBombillo * 0.9;
      this.bombilloFilamento.material.emissiveIntensity = brilloBombillo * 2.5;
    }

    posicionarCamara(nombre) {
      const { posicion, objetivo } = CAMARAS[nombre];
      this.camara.position.set(...posicion);
      this.controles.target.set(...objetivo);
    }

    _tamanoContenedor() {
      return {
        ancho: Math.max(1, this.contenedor.clientWidth),
        alto: Math.max(1, this.contenedor.clientHeight),
      };
    }

    ajustarTamano() {
      const { ancho, alto } = this._tamanoContenedor();
      this.camara.aspect = ancho / alto;
      this.camara.updateProjectionMatrix();
      this.renderer.setSize(ancho, alto);
    }

    renderizar() {
      this.controles.update();
      this.renderer.render(this.escena, this.camara);
    }
  }

  GA.EscenaGenerador = EscenaGenerador;
})((window.GeneradorAxial = window.GeneradorAxial || {}));
