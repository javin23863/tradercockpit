(() => {
  'use strict';

  const canvas = document.querySelector('#home-universe-canvas');
  if (!canvas) return;

  const pauseButton = document.querySelector('#home-universe-pause');
  const resetButton = document.querySelector('#home-universe-reset');
  const readout = document.querySelector('#home-universe-readout');
  const controls = document.querySelector('.home-universe-controls');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const TAU = Math.PI * 2;

  function mulberry32(seed) {
    let value = seed >>> 0;
    return function random() {
      value += 0x6D2B79F5;
      let t = value;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  const random = mulberry32(23863);
  const points = Array.from({ length: 180 }, (_, index) => ({
    index,
    dispersion: random(),
    drawdown: random(),
    disagreement: random(),
    evidence: .25 + random() * .75,
    family: index % 3
  }));

  for (const point of points) {
    point.x = point.dispersion * 2 - 1;
    point.y = point.drawdown * 2 - 1;
    point.z = point.disagreement * 2 - 1;
  }

  let yaw = -.48;
  let pitch = .16;
  let paused = reducedMotion;
  let raf = 0;
  let lastTime = performance.now();

  function fitCanvas() {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(280, Math.floor(rect.width));
    const height = Math.max(360, Math.floor(rect.height));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const targetWidth = Math.floor(width * dpr);
    const targetHeight = Math.floor(height * dpr);
    if (canvas.width !== targetWidth || canvas.height !== targetHeight) {
      canvas.width = targetWidth;
      canvas.height = targetHeight;
    }
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, width, height };
  }

  function rotate(point) {
    const cy = Math.cos(yaw);
    const sy = Math.sin(yaw);
    const cp = Math.cos(pitch);
    const sp = Math.sin(pitch);
    const x1 = point.x * cy - point.z * sy;
    const z1 = point.x * sy + point.z * cy;
    const y1 = point.y * cp - z1 * sp;
    const z2 = point.y * sp + z1 * cp;
    return { x: x1, y: y1, z: z2 };
  }

  function project(point, width, height) {
    const rotated = rotate(point);
    const depth = 3 - rotated.z;
    const scale = Math.min(width, height) * .43 / depth;
    return {
      x: width * .5 + rotated.x * scale,
      y: height * .49 - rotated.y * scale,
      z: rotated.z,
      scale: Math.max(.65, Math.min(1.5, 2.25 / depth))
    };
  }
  function drawAxes(ctx, width, height) {
    const origin = project({ x: 0, y: 0, z: 0 }, width, height);
    const axes = [
      [{ x: 1.18, y: 0, z: 0 }, 'dispersion', 'rgba(255,183,43,.55)'],
      [{ x: 0, y: 1.18, z: 0 }, 'drawdown', 'rgba(119,228,220,.52)'],
      [{ x: 0, y: 0, z: 1.18 }, 'IS/OOS disagreement', 'rgba(108,167,255,.52)']
    ];
    ctx.save();
    ctx.font = '11px Cascadia Mono, Consolas, monospace';
    for (const [axisPoint, label, color] of axes) {
      const end = project(axisPoint, width, height);
      ctx.beginPath();
      ctx.moveTo(origin.x, origin.y);
      ctx.lineTo(end.x, end.y);
      ctx.strokeStyle = color;
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.fillStyle = color;
      ctx.fillText(label, end.x + 7, end.y - 4);
    }
    ctx.restore();
  }

  function draw() {
    const sizing = fitCanvas();
    if (!sizing) return;
    const { ctx, width, height } = sizing;
    ctx.clearRect(0, 0, width, height);
    const glow = ctx.createRadialGradient(width * .5, height * .48, 20, width * .5, height * .48, Math.max(width, height) * .58);
    glow.addColorStop(0, 'rgba(255,23,68,.12)');
    glow.addColorStop(.42, 'rgba(255,183,43,.035)');
    glow.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, width, height);
    drawAxes(ctx, width, height);

    const projected = points
      .map((point) => ({ point, screen: project(point, width, height) }))
      .sort((a, b) => a.screen.z - b.screen.z);

    for (const { point, screen } of projected) {
      const colors = point.family === 0 ? [255,183,43] : point.family === 1 ? [255,92,119] : [108,167,255];
      const radius = (1.7 + point.evidence * 3.3) * screen.scale;
      const alpha = .24 + point.evidence * .62;
      ctx.beginPath();
      ctx.arc(screen.x, screen.y, radius, 0, TAU);
      ctx.fillStyle = `rgba(${colors.join(',')},${alpha.toFixed(3)})`;
      ctx.fill();
    }

    ctx.save();
    ctx.strokeStyle = 'rgba(255,183,43,.13)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.ellipse(width * .5, height * .5, width * .34, height * .14, -.12, 0, TAU);
    ctx.stroke();
    ctx.beginPath();
    ctx.ellipse(width * .5, height * .5, width * .23, height * .095, .12, 0, TAU);
    ctx.strokeStyle = 'rgba(108,167,255,.12)';
    ctx.stroke();
    ctx.restore();
  }

  function updateReadout() {
    if (!readout) return;
    readout.textContent = '180 deterministic synthetic candidates · axes: outcome dispersion, drawdown severity, and in-sample/out-of-sample disagreement · no market data';
  }

  function frame(now) {
    raf = 0;
    const dt = Math.min(40, now - lastTime);
    lastTime = now;
    if (!paused && !document.hidden) yaw += dt * .00007;
    draw();
    if (!paused && !document.hidden) raf = window.requestAnimationFrame(frame);
  }

  function start() {
    if (paused || document.hidden || raf) return;
    lastTime = performance.now();
    raf = window.requestAnimationFrame(frame);
  }

  function stop() {
    if (raf) window.cancelAnimationFrame(raf);
    raf = 0;
  }
  pauseButton?.addEventListener('click', () => {
    paused = !paused;
    pauseButton.setAttribute('aria-pressed', String(paused));
    pauseButton.textContent = paused ? 'Resume rotation' : 'Pause rotation';
    if (paused) { stop(); draw(); } else { start(); }
  });

  resetButton?.addEventListener('click', () => {
    yaw = -.48;
    pitch = .16;
    draw();
  });

  canvas.addEventListener('pointermove', (event) => {
    if (reducedMotion) return;
    const rect = canvas.getBoundingClientRect();
    const nx = (event.clientX - rect.left) / Math.max(1, rect.width) - .5;
    const ny = (event.clientY - rect.top) / Math.max(1, rect.height) - .5;
    yaw = -.48 + nx * .68;
    pitch = .16 - ny * .38;
    if (paused) draw();
  }, { passive: true });

  canvas.addEventListener('pointerleave', () => {
    if (reducedMotion) return;
    pitch = .16;
    if (paused) draw();
  }, { passive: true });

  window.addEventListener('resize', draw, { passive: true });
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) stop();
    else if (!paused) start();
    else draw();
  });
  window.addEventListener('pagehide', stop, { once: true });

  controls?.removeAttribute('hidden');
  updateReadout();
  draw();
  if (reducedMotion) {
    pauseButton?.setAttribute('hidden', '');
  } else {
    start();
  }
})();
