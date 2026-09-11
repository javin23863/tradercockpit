(() => {
  'use strict';

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

  function fitCanvas(canvas, cssHeight) {
    const rect = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(320, Math.floor(rect.width));
    const height = Math.max(260, Math.floor(cssHeight || rect.height));
    const pixelWidth = Math.floor(width * dpr);
    const pixelHeight = Math.floor(height * dpr);
    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, width, height, dpr };
  }

  function initStrategyUniverse() {
    const canvas = document.querySelector('#strategy-universe-canvas');
    if (!canvas) return;

    const readout = document.querySelector('#candidate-readout');
    const pauseButton = document.querySelector('#universe-pause');
    const resetButton = document.querySelector('#universe-reset');
    const previousButton = document.querySelector('#candidate-prev');
    const nextButton = document.querySelector('#candidate-next');
    const random = mulberry32(23863);

    const points = Array.from({ length: 150 }, (_, index) => {
      // Deliberately synthetic, bounded dimensions. They are not market results.
      const dispersion = random();
      const drawdown = random();
      const disagreement = random();
      const evidence = 0.35 + random() * 0.65;
      const family = index % 3;
      return {
        index, dispersion, drawdown, disagreement, evidence, family,
        x: dispersion * 2 - 1,
        y: drawdown * 2 - 1,
        z: disagreement * 2 - 1
      };
    });

    let yaw = -0.45;
    let pitch = 0.18;
    let selected = 0;
    let running = !reducedMotion;
    let raf = 0;
    let lastTime = performance.now();

    function familyLabel(family) {
      return ['A', 'B', 'C'][family] || 'A';
    }

    function updateReadout() {
      if (!readout) return;
      const point = points[selected];
      readout.textContent = `Synthetic candidate ${String(point.index + 1).padStart(3, '0')} · family ${familyLabel(point.family)} · dispersion ${point.dispersion.toFixed(2)} · drawdown severity ${point.drawdown.toFixed(2)} · IS/OOS disagreement ${point.disagreement.toFixed(2)}`;
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
      const perspective = 2.8;
      const depth = perspective - rotated.z;
      const scale = Math.min(width, height) * 0.33 / depth;
      return {
        x: width * 0.5 + rotated.x * scale,
        y: height * 0.50 - rotated.y * scale,
        z: rotated.z,
        scale: Math.max(0.6, Math.min(1.55, 2.25 / depth))
      };
    }

    function drawAxes(ctx, width, height) {
      ctx.save();
      ctx.strokeStyle = 'rgba(61,232,255,.14)';
      ctx.lineWidth = 1;
      const origin = project({ x: 0, y: 0, z: 0 }, width, height);
      const axes = [
        { p: { x: 1.15, y: 0, z: 0 }, label: 'dispersion', color: 'rgba(61,232,255,.55)' },
        { p: { x: 0, y: 1.15, z: 0 }, label: 'drawdown axis', color: 'rgba(119,228,220,.55)' },
        { p: { x: 0, y: 0, z: 1.15 }, label: 'IS/OOS disagreement', color: 'rgba(108,167,255,.55)' }
      ];
      ctx.font = '11px Cascadia Mono, Consolas, monospace';
      for (const axis of axes) {
        const end = project(axis.p, width, height);
        ctx.beginPath();
        ctx.moveTo(origin.x, origin.y);
        ctx.lineTo(end.x, end.y);
        ctx.strokeStyle = axis.color;
        ctx.stroke();
        ctx.fillStyle = axis.color;
        ctx.fillText(axis.label, end.x + 7, end.y - 4);
      }
      ctx.restore();
    }

    function draw() {
      const sizing = fitCanvas(canvas, canvas.getBoundingClientRect().height || 520);
      if (!sizing) return;
      const { ctx, width, height } = sizing;
      ctx.clearRect(0, 0, width, height);

      const glow = ctx.createRadialGradient(width * .5, height * .48, 10, width * .5, height * .48, Math.max(width, height) * .6);
      glow.addColorStop(0, 'rgba(255,82,110,.095)');
      glow.addColorStop(.42, 'rgba(73,239,154,.025)');
      glow.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, width, height);

      drawAxes(ctx, width, height);

      const projected = points
        .map((point) => ({ point, screen: project(point, width, height) }))
        .sort((a, b) => a.screen.z - b.screen.z);

      for (const item of projected) {
        const { point, screen } = item;
        const isSelected = point.index === selected;
        const baseRadius = 2.1 + point.evidence * 2.7;
        const radius = baseRadius * screen.scale * (isSelected ? 1.45 : 1);
        const familyColor = point.family === 0
          ? [73, 239, 154]
          : point.family === 1
            ? [255, 82, 110]
            : [61, 232, 255];
        const alpha = 0.28 + point.evidence * 0.62;

        ctx.beginPath();
        ctx.arc(screen.x, screen.y, radius, 0, TAU);
        ctx.fillStyle = `rgba(${familyColor.join(',')},${alpha.toFixed(3)})`;
        ctx.fill();

        if (isSelected) {
          ctx.beginPath();
          ctx.arc(screen.x, screen.y, radius + 7, 0, TAU);
          ctx.strokeStyle = 'rgba(238,252,255,.92)';
          ctx.lineWidth = 1.3;
          ctx.stroke();
        }
      }
    }

    function frame(now) {
      raf = 0;
      const dt = Math.min(40, now - lastTime);
      lastTime = now;
      if (running && !document.hidden) yaw += dt * 0.000075;
      draw();
      raf = window.requestAnimationFrame(frame);
    }

    function select(step) {
      selected = (selected + step + points.length) % points.length;
      updateReadout();
      if (!running) draw();
    }

    pauseButton?.addEventListener('click', () => {
      running = !running;
      pauseButton.textContent = running ? 'Pause motion' : 'Resume motion';
      pauseButton.setAttribute('aria-pressed', String(!running));
      draw();
    });

    resetButton?.addEventListener('click', () => {
      yaw = -0.45;
      pitch = 0.18;
      selected = 0;
      updateReadout();
      draw();
    });

    previousButton?.addEventListener('click', () => select(-1));
    nextButton?.addEventListener('click', () => select(1));

    canvas.addEventListener('pointermove', (event) => {
      if (reducedMotion) return;
      const rect = canvas.getBoundingClientRect();
      const nx = (event.clientX - rect.left) / rect.width - .5;
      const ny = (event.clientY - rect.top) / rect.height - .5;
      yaw = -0.45 + nx * .72;
      pitch = 0.18 - ny * .42;
    }, { passive: true });

    canvas.addEventListener('pointerleave', () => {
      if (reducedMotion) return;
      pitch = 0.18;
    });

    window.addEventListener('resize', draw, { passive: true });
    document.addEventListener('visibilitychange', () => {
      if (reducedMotion) { draw(); return; }
      if (document.hidden) {
        if (raf) window.cancelAnimationFrame(raf);
        raf = 0;
      } else if (!raf) {
        lastTime = performance.now();
        raf = window.requestAnimationFrame(frame);
      }
    });

    updateReadout();
    draw();
    if (reducedMotion) {
      pauseButton?.setAttribute('hidden', '');
    } else {
      raf = window.requestAnimationFrame(frame);
    }

    window.addEventListener('pagehide', () => {
      if (raf) window.cancelAnimationFrame(raf);
    }, { once: true });
  }

  function initMonteCarlo() {
    const canvas = document.querySelector('#monte-carlo-canvas');
    if (!canvas) return;

    const regenerate = document.querySelector('#mc-regenerate');
    const p10Node = document.querySelector('#mc-p10');
    const p50Node = document.querySelector('#mc-p50');
    const p90Node = document.querySelector('#mc-p90');
    let seed = 1442953;

    function buildPaths(currentSeed) {
      const random = mulberry32(currentSeed);
      const pathCount = 64;
      const steps = 90;
      const paths = [];
      for (let p = 0; p < pathCount; p += 1) {
        let value = 0;
        const path = [value];
        for (let step = 1; step < steps; step += 1) {
          // Synthetic zero-drift increments with bounded noise. Not a forecast or market model.
          const u1 = Math.max(1e-9, random());
          const u2 = Math.max(1e-9, random());
          const normal = Math.sqrt(-2 * Math.log(u1)) * Math.cos(TAU * u2);
          value += normal * 0.12;
          path.push(value);
        }
        paths.push(path);
      }
      return paths;
    }

    function percentile(values, q) {
      const sorted = [...values].sort((a, b) => a - b);
      const index = (sorted.length - 1) * q;
      const lower = Math.floor(index);
      const upper = Math.ceil(index);
      if (lower === upper) return sorted[lower];
      const weight = index - lower;
      return sorted[lower] * (1 - weight) + sorted[upper] * weight;
    }

    function render() {
      const sizing = fitCanvas(canvas, canvas.getBoundingClientRect().height || 380);
      if (!sizing) return;
      const { ctx, width, height } = sizing;
      const paths = buildPaths(seed);
      ctx.clearRect(0, 0, width, height);

      const padding = { left: 38, right: 18, top: 22, bottom: 30 };
      const plotWidth = width - padding.left - padding.right;
      const plotHeight = height - padding.top - padding.bottom;
      const allValues = paths.flat();
      const min = Math.min(...allValues);
      const max = Math.max(...allValues);
      const range = Math.max(.0001, max - min);

      ctx.strokeStyle = 'rgba(255,255,255,.07)';
      ctx.lineWidth = 1;
      for (let i = 0; i <= 4; i += 1) {
        const y = padding.top + plotHeight * (i / 4);
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
      }

      paths.forEach((path, pathIndex) => {
        ctx.beginPath();
        path.forEach((value, step) => {
          const x = padding.left + plotWidth * (step / (path.length - 1));
          const y = padding.top + plotHeight * (1 - (value - min) / range);
          if (step === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        });
        const alpha = pathIndex % 8 === 0 ? .40 : .14;
        ctx.strokeStyle = pathIndex % 3 === 0
          ? `rgba(61,232,255,${alpha})`
          : pathIndex % 3 === 1
            ? `rgba(255,82,110,${alpha})`
            : `rgba(108,167,255,${alpha})`;
        ctx.lineWidth = pathIndex % 8 === 0 ? 1.35 : 1;
        ctx.stroke();
      });

      ctx.fillStyle = 'rgba(158,184,201,.72)';
      ctx.font = '11px Cascadia Mono, Consolas, monospace';
      ctx.fillText('synthetic path step', width - 132, height - 10);
      ctx.save();
      ctx.translate(12, height * .63);
      ctx.rotate(-Math.PI / 2);
      ctx.fillText('normalized cumulative outcome', 0, 0);
      ctx.restore();

      const terminals = paths.map((path) => path[path.length - 1]);
      if (p10Node) p10Node.textContent = percentile(terminals, .10).toFixed(2);
      if (p50Node) p50Node.textContent = percentile(terminals, .50).toFixed(2);
      if (p90Node) p90Node.textContent = percentile(terminals, .90).toFixed(2);
    }

    regenerate?.addEventListener('click', () => {
      seed += 97;
      render();
    });
    window.addEventListener('resize', render, { passive: true });

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          render();
          observer.disconnect();
        }
      }, { rootMargin: '180px' });
      observer.observe(canvas);
    } else {
      render();
    }
  }

  initStrategyUniverse();
  initMonteCarlo();
})();
