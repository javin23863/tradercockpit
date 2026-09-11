import * as THREE from 'three';
import { BloomEffect, EffectComposer, EffectPass, RenderPass } from 'postprocessing';

(() => {
  'use strict';
  const canvas = document.querySelector('#quant-universe-canvas');
  if (!canvas) return;

  const pause = document.querySelector('#quant-universe-pause');
  const reset = document.querySelector('#quant-universe-reset');
  const readout = document.querySelector('#quant-universe-readout');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const mobile = matchMedia('(max-width: 760px)').matches;
  const TEAL = new THREE.Color('#3cfad2');
  const RED = new THREE.Color('#e54a5a');
  const CYAN = new THREE.Color('#3daed3');
  const DEEP = new THREE.Color('#06131c');

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({
      canvas,
      alpha: true,
      antialias: false,
      powerPreference: 'high-performance',
      preserveDrawingBuffer: false,
    });
    renderer.getContext();
  } catch {
    document.documentElement.dataset.quantRenderer = 'canvas2d-fallback';
    return;
  }

  window.__tcWebGLHero = true;
  document.documentElement.dataset.quantRenderer = 'three-webgl';
  canvas.dataset.renderer = 'three-webgl';

  renderer.setClearColor(0x000000, 0);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;

  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x010509, 0.055);
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 60);
  camera.position.set(0.15, 1.15, 9.5);
  camera.lookAt(0, 0.15, 0);

  const root = new THREE.Group();
  root.rotation.x = -0.05;
  scene.add(root);

  scene.add(new THREE.HemisphereLight(0x8eefff, 0x010509, 0.8));
  const tealLight = new THREE.PointLight(0x3cfad2, 18, 13, 2.1);
  tealLight.position.set(-3.2, 3.6, 4.8);
  scene.add(tealLight);
  const redLight = new THREE.PointLight(0xe54a5a, 9, 10, 2.2);
  redLight.position.set(4.0, -0.8, 3.2);
  scene.add(redLight);

  const globe = new THREE.Mesh(
    new THREE.SphereGeometry(2.22, mobile ? 40 : 64, mobile ? 26 : 40),
    new THREE.MeshPhysicalMaterial({
      color: 0x04131b,
      emissive: 0x062a32,
      emissiveIntensity: 0.9,
      roughness: 0.34,
      metalness: 0.18,
      clearcoat: 0.55,
      clearcoatRoughness: 0.35,
    }),
  );
  globe.position.y = 0.42;
  root.add(globe);

  const shell = new THREE.Mesh(
    new THREE.SphereGeometry(2.245, mobile ? 28 : 48, mobile ? 18 : 32),
    new THREE.MeshBasicMaterial({
      color: 0x3daed3,
      wireframe: true,
      transparent: true,
      opacity: 0.095,
      depthWrite: false,
    }),
  );
  shell.position.copy(globe.position);
  root.add(shell);

  const atmosphere = new THREE.Mesh(
    new THREE.SphereGeometry(2.43, 32, 20),
    new THREE.MeshBasicMaterial({
      color: 0x3cfad2,
      transparent: true,
      opacity: 0.035,
      side: THREE.BackSide,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
  atmosphere.position.copy(globe.position);
  root.add(atmosphere);

  function mulberry32(seed) {
    return () => {
      seed |= 0;
      seed = seed + 0x6D2B79F5 | 0;
      let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  const random = mulberry32(0x5eeda11);
  const particleCount = mobile ? 360 : 720;
  const positions = new Float32Array(particleCount * 3);
  const colors = new Float32Array(particleCount * 3);
  const pointColor = new THREE.Color();
  for (let i = 0; i < particleCount; i += 1) {
    const theta = random() * Math.PI * 2;
    const phi = Math.acos(2 * random() - 1);
    const radius = 2.34 + random() * 1.05;
    const score = random() * 2 - 1;
    positions[i * 3] = radius * Math.sin(phi) * Math.cos(theta);
    positions[i * 3 + 1] = globe.position.y + radius * Math.cos(phi);
    positions[i * 3 + 2] = radius * Math.sin(phi) * Math.sin(theta);
    pointColor.copy(score > 0.12 ? TEAL : score < -0.12 ? RED : CYAN);
    colors[i * 3] = pointColor.r;
    colors[i * 3 + 1] = pointColor.g;
    colors[i * 3 + 2] = pointColor.b;
  }
  const pointGeometry = new THREE.BufferGeometry();
  pointGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  pointGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  const points = new THREE.Points(
    pointGeometry,
    new THREE.PointsMaterial({
      size: mobile ? 0.035 : 0.048,
      vertexColors: true,
      transparent: true,
      opacity: 0.94,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    }),
  );
  root.add(points);

  const orbitGroup = new THREE.Group();
  orbitGroup.position.copy(globe.position);
  root.add(orbitGroup);
  const orbitSpecs = [
    [3.8, 1.22, -0.16, TEAL, 0.56],
    [3.35, 0.93, 0.38, RED, 0.33],
    [3.02, 0.72, -0.52, CYAN, 0.28],
    [2.68, 0.54, 0.66, CYAN, 0.20],
  ];
  orbitSpecs.forEach(([rx, ry, tilt, color, opacity]) => {
    const curve = new THREE.EllipseCurve(0, 0, rx, ry, 0, Math.PI * 2, false, 0);
    const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(128));
    const line = new THREE.LineLoop(geometry, new THREE.LineBasicMaterial({ color, transparent: true, opacity }));
    line.rotation.x = Math.PI / 2.15;
    line.rotation.z = tilt;
    orbitGroup.add(line);
  });

  const satellites = [];
  for (let i = 0; i < 7; i += 1) {
    const material = new THREE.MeshStandardMaterial({
      color: i % 3 === 0 ? TEAL : i % 3 === 1 ? CYAN : RED,
      emissive: i % 3 === 0 ? TEAL : i % 3 === 1 ? CYAN : RED,
      emissiveIntensity: 2.2,
      roughness: 0.25,
    });
    const mesh = new THREE.Mesh(new THREE.SphereGeometry(0.055 + (i % 2) * 0.018, 12, 8), material);
    mesh.userData.radius = 2.75 + i * 0.15;
    mesh.userData.speed = 0.24 + i * 0.025;
    mesh.userData.offset = i * Math.PI * 2 / 7;
    satellites.push(mesh);
    orbitGroup.add(mesh);
  }

  const grid = new THREE.GridHelper(18, 28, 0x3daed3, 0x16485b);
  grid.position.set(0, -2.25, 1.5);
  grid.material.transparent = true;
  grid.material.opacity = 0.18;
  root.add(grid);

  const candleCount = mobile ? 54 : 92;
  const bodyGeometry = new THREE.BoxGeometry(0.105, 1, 0.105);
  const bodyMaterial = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.32,
    metalness: 0.14,
    vertexColors: true,
  });
  const candleBodies = new THREE.InstancedMesh(bodyGeometry, bodyMaterial, candleCount);
  candleBodies.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const matrix = new THREE.Matrix4();
  const candleColor = new THREE.Color();
  const wickPositions = [];
  const wickColors = [];
  for (let i = 0; i < candleCount; i += 1) {
    const t = i / Math.max(1, candleCount - 1);
    const lane = i % 4;
    const x = -5.9 + t * 11.8;
    const z = 2.15 + lane * 0.62 + Math.sin(i * 0.37) * 0.15;
    const delta = Math.sin(i * 0.61) * 0.7 + (random() - 0.5) * 0.65;
    const bodyH = 0.12 + Math.abs(delta) * 0.6;
    const baseline = -2.05 + lane * 0.035;
    const centerY = baseline + delta * 0.31;
    matrix.compose(
      new THREE.Vector3(x, centerY, z),
      new THREE.Quaternion(),
      new THREE.Vector3(1, bodyH, 1),
    );
    candleBodies.setMatrixAt(i, matrix);
    candleColor.copy(delta >= 0 ? TEAL : RED);
    candleBodies.setColorAt(i, candleColor);
    const wickHalf = bodyH * 0.76 + 0.12 + random() * 0.12;
    wickPositions.push(x, centerY - wickHalf, z, x, centerY + wickHalf, z);
    wickColors.push(candleColor.r, candleColor.g, candleColor.b, candleColor.r, candleColor.g, candleColor.b);
  }
  candleBodies.instanceMatrix.needsUpdate = true;
  if (candleBodies.instanceColor) candleBodies.instanceColor.needsUpdate = true;
  root.add(candleBodies);

  const wickGeometry = new THREE.BufferGeometry();
  wickGeometry.setAttribute('position', new THREE.Float32BufferAttribute(wickPositions, 3));
  wickGeometry.setAttribute('color', new THREE.Float32BufferAttribute(wickColors, 3));
  root.add(new THREE.LineSegments(
    wickGeometry,
    new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.86 }),
  ));

  const composer = new EffectComposer(renderer, { multisampling: mobile ? 0 : 2 });
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new BloomEffect({
    intensity: mobile ? 0.55 : 0.78,
    luminanceThreshold: 0.18,
    luminanceSmoothing: 0.72,
    mipmapBlur: true,
  });
  composer.addPass(new EffectPass(camera, bloom));

  let width = 1;
  let height = 1;
  function resize() {
    const rect = canvas.getBoundingClientRect();
    const nextW = Math.max(300, Math.round(rect.width));
    const nextH = Math.max(430, Math.round(rect.height));
    if (nextW === width && nextH === height) return;
    width = nextW;
    height = nextH;
    const dpr = Math.min(devicePixelRatio || 1, mobile ? 1.35 : 1.75);
    renderer.setPixelRatio(dpr);
    renderer.setSize(width, height, false);
    composer.setSize(width, height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }

  let autoMotion = !reduced;
  let raf = 0;
  let last = performance.now();
  let targetYaw = -0.18;
  let targetPitch = -0.04;
  let yaw = targetYaw;
  let pitch = targetPitch;

  function render(now = performance.now()) {
    resize();
    const dt = Math.min(0.05, Math.max(0, (now - last) / 1000));
    last = now;
    if (autoMotion && !document.hidden) targetYaw += dt * 0.055;
    yaw += (targetYaw - yaw) * Math.min(1, dt * 4.5);
    pitch += (targetPitch - pitch) * Math.min(1, dt * 4.5);
    root.rotation.y = yaw;
    root.rotation.x = -0.05 + pitch;
    globe.rotation.y += autoMotion ? dt * 0.045 : 0;
    shell.rotation.y = globe.rotation.y * 0.78;
    points.rotation.y = -globe.rotation.y * 0.42;
    satellites.forEach((mesh, i) => {
      const a = now * 0.001 * mesh.userData.speed + mesh.userData.offset;
      const r = mesh.userData.radius;
      mesh.position.set(Math.cos(a) * r, Math.sin(a * 1.11) * 0.5, Math.sin(a) * r * 0.42);
    });
    composer.render();
  }

  function frame(now) {
    raf = 0;
    render(now);
    if (autoMotion && !document.hidden) raf = requestAnimationFrame(frame);
  }
  function start() {
    if (!autoMotion || document.hidden || raf) return;
    last = performance.now();
    raf = requestAnimationFrame(frame);
  }
  function stop() {
    if (raf) cancelAnimationFrame(raf);
    raf = 0;
  }

  pause?.addEventListener('click', () => {
    autoMotion = !autoMotion;
    pause.textContent = autoMotion ? 'Pause motion' : 'Resume motion';
    pause.setAttribute('aria-pressed', String(!autoMotion));
    if (autoMotion) start(); else { stop(); render(); }
  });
  reset?.addEventListener('click', () => {
    targetYaw = -0.18;
    targetPitch = -0.04;
    yaw = targetYaw;
    pitch = targetPitch;
    render();
  });
  canvas.addEventListener('pointermove', (event) => {
    if (reduced) return;
    const rect = canvas.getBoundingClientRect();
    targetYaw = -0.18 + ((event.clientX - rect.left) / rect.width - 0.5) * 0.48;
    targetPitch = -0.04 - ((event.clientY - rect.top) / rect.height - 0.5) * 0.18;
    if (!autoMotion) render();
  }, { passive: true });
  canvas.addEventListener('webglcontextlost', (event) => {
    event.preventDefault();
    stop();
    document.documentElement.dataset.quantRenderer = 'webgl-context-lost';
    if (readout) readout.textContent = '3D renderer unavailable ? refresh to restore visualization';
  });
  addEventListener('resize', () => { width = 0; render(); }, { passive: true });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop(); else if (autoMotion) start(); else render();
  });

  if (readout) readout.textContent = 'WebGL strategy field ? teal gains / red losses / cyan neutral ? illustrative research geometry';
  if (reduced) {
    pause?.setAttribute('hidden', '');
    autoMotion = false;
    render(0);
  } else {
    render();
    start();
  }
})();
