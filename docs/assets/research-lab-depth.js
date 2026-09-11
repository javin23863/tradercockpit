(() => {
  'use strict';

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

  function fit(canvas, cssHeight = 440) {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(280, Math.floor(rect.width));
    const height = Math.max(260, Math.floor(cssHeight));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, width, height };
  }

  function whenVisible(element, init) {
    let started = false;
    const start = () => {
      if (started) return;
      started = true;
      init();
    };
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          observer.disconnect();
          start();
        }
      }, { rootMargin: '220px' });
      observer.observe(element);
    } else {
      start();
    }
  }

  function percentile(values, q) {
    const sorted = [...values].sort((a, b) => a - b);
    const index = (sorted.length - 1) * q;
    const lo = Math.floor(index);
    const hi = Math.ceil(index);
    if (lo === hi) return sorted[lo];
    const weight = index - lo;
    return sorted[lo] * (1 - weight) + sorted[hi] * weight;
  }

  function surfaceValue(mode, u, v) {
    const x = u - 0.5;
    const y = v - 0.5;
    let value;
    if (mode === 'spike') {
      const d2 = (u - 0.58) ** 2 + (v - 0.44) ** 2;
      value = 0.12 + 0.82 * Math.exp(-62 * d2) + 0.04 * Math.exp(-5 * (x * x + y * y));
    } else if (mode === 'ridge') {
      const ridge = v - (0.28 + 0.42 * u);
      value = 0.15 + 0.67 * Math.exp(-32 * ridge * ridge) * (0.88 + 0.08 * Math.cos(u * TAU * 2));
    } else {
      const radius = x * x + y * y;
      value = 0.28 + 0.52 * Math.exp(-3.8 * radius) + 0.035 * Math.cos(u * TAU * 2) * Math.cos(v * TAU * 2);
    }
    return Math.max(0, Math.min(1, value));
  }

  function initRobustness() {
    const host = document.querySelector('[data-robustness-explorer]');
    const canvas = document.querySelector('#robustness-canvas');
    if (!host || !canvas) return;
    const buttons = [...host.querySelectorAll('[data-surface-mode]')];
    const peakNode = document.querySelector('#robustness-peak');
    const meanNode = document.querySelector('#robustness-neighborhood');
    const rangeNode = document.querySelector('#robustness-range');
    let mode = 'plateau';

    function buildGrid() {
      const size = 21;
      const grid = [];
      for (let row = 0; row < size; row += 1) {
        const line = [];
        for (let col = 0; col < size; col += 1) {
          const u = col / (size - 1);
          const v = row / (size - 1);
          line.push(surfaceValue(mode, u, v));
        }
        grid.push(line);
      }
      return grid;
    }

    function project(u, v, heightValue, width, height) {
      const span = Math.min(width * 0.42, 350);
      const depth = Math.min(height * 0.25, 120);
      const lift = Math.min(height * 0.42, 190);
      return {
        x: width * 0.5 + (u - v) * span,
        y: height * 0.70 + (u + v - 1) * depth - heightValue * lift
      };
    }

    function updateMetrics(grid) {
      let peak = -Infinity;
      let peakRow = 0;
      let peakCol = 0;
      grid.forEach((row, r) => row.forEach((value, c) => {
        if (value > peak) { peak = value; peakRow = r; peakCol = c; }
      }));
      const neighbors = [];
      for (let dr = -2; dr <= 2; dr += 1) {
        for (let dc = -2; dc <= 2; dc += 1) {
          const r = peakRow + dr;
          const c = peakCol + dc;
          if (grid[r]?.[c] !== undefined) neighbors.push(grid[r][c]);
        }
      }
      const mean = neighbors.reduce((sum, value) => sum + value, 0) / neighbors.length;
      const range = Math.max(...neighbors) - Math.min(...neighbors);
      if (peakNode) peakNode.textContent = peak.toFixed(2);
      if (meanNode) meanNode.textContent = mean.toFixed(2);
      if (rangeNode) rangeNode.textContent = range.toFixed(2);
    }

    function draw() {
      const sizing = fit(canvas, canvas.getBoundingClientRect().height || 470);
      if (!sizing) return;
      const { ctx, width, height } = sizing;
      const grid = buildGrid();
      ctx.clearRect(0, 0, width, height);
      const bg = ctx.createRadialGradient(width * .5, height * .48, 10, width * .5, height * .52, width * .62);
      bg.addColorStop(0, 'rgba(73,239,154,.10)');
      bg.addColorStop(.55, 'rgba(255,82,110,.035)');
      bg.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);
      const size = grid.length;
      for (let diagonal = 0; diagonal < (size - 1) * 2; diagonal += 1) {
        for (let row = 0; row < size - 1; row += 1) {
          const col = diagonal - row;
          if (col < 0 || col >= size - 1) continue;
          const u0 = col / (size - 1);
          const v0 = row / (size - 1);
          const u1 = (col + 1) / (size - 1);
          const v1 = (row + 1) / (size - 1);
          const values = [grid[row][col], grid[row][col + 1], grid[row + 1][col + 1], grid[row + 1][col]];
          const points = [project(u0, v0, values[0], width, height), project(u1, v0, values[1], width, height), project(u1, v1, values[2], width, height), project(u0, v1, values[3], width, height)];
          const average = values.reduce((sum, value) => sum + value, 0) / values.length;
          ctx.beginPath();
          ctx.moveTo(points[0].x, points[0].y);
          points.slice(1).forEach((point) => ctx.lineTo(point.x, point.y));
          ctx.closePath();
          ctx.fillStyle = `rgba(${Math.round(45 + average * 28)},${Math.round(190 + average * 49)},${Math.round(220 - average * 60)},${(0.20 + average * 0.52).toFixed(3)})`;
          ctx.fill();
          ctx.strokeStyle = `rgba(166,244,232,${(0.05 + average * 0.18).toFixed(3)})`;
          ctx.lineWidth = .7;
          ctx.stroke();
        }
      }
      const origin = project(0, 0, 0, width, height);
      const endA = project(1, 0, 0, width, height);
      const endB = project(0, 1, 0, width, height);
      ctx.strokeStyle = 'rgba(238,252,255,.34)';
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(origin.x, origin.y); ctx.lineTo(endA.x, endA.y); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(origin.x, origin.y); ctx.lineTo(endB.x, endB.y); ctx.stroke();
      ctx.fillStyle = 'rgba(158,184,201,.82)';
      ctx.font = '11px Cascadia Mono, Consolas, monospace';
      ctx.fillText('parameter A →', endA.x - 76, endA.y + 18);
      ctx.fillText('parameter B →', endB.x + 8, endB.y + 18);
      ctx.fillText('height = synthetic response', 16, 24);
      updateMetrics(grid);
    }

    buttons.forEach((button) => button.addEventListener('click', () => {
      mode = button.dataset.surfaceMode || 'plateau';
      buttons.forEach((candidate) => candidate.setAttribute('aria-pressed', String(candidate === button)));
      draw();
    }));
    window.addEventListener('resize', draw, { passive: true });
    draw();
  }

  const pairNoise = (i, j) => {
    const lo = Math.min(i, j) + 1;
    const hi = Math.max(i, j) + 1;
    const raw = Math.sin(lo * 12.9898 + hi * 78.233) * 43758.5453;
    return raw - Math.floor(raw);
  };

  function correlationValue(i, j, nodes) {
    if (i === j) return 1;
    const sameFamily = nodes[i].family === nodes[j].family;
    const noise = pairNoise(i, j);
    if ((i === 5 && j === 6) || (i === 6 && j === 5)) return 0.74;
    if (sameFamily) return 0.64 + noise * 0.31;
    return -0.28 + noise * 0.68;
  }

  function initCorrelation() {
    const host = document.querySelector('[data-correlation-explorer]');
    const canvas = document.querySelector('#correlation-canvas');
    if (!host || !canvas) return;
    const previous = document.querySelector('#network-prev');
    const next = document.querySelector('#network-next');
    const focusButton = document.querySelector('#network-focus');
    const readout = document.querySelector('#network-readout');
    const nodes = [];
    for (let family = 0; family < 3; family += 1) {
      for (let member = 0; member < 6; member += 1) {
        nodes.push({ family, member, label: `${String.fromCharCode(65 + family)}${member + 1}` });
      }
    }
    let selected = 0;
    let focusSelected = false;

    function layout(width, height) {
      const centers = [
        { x: width * .27, y: height * .46 },
        { x: width * .53, y: height * .34 },
        { x: width * .72, y: height * .62 }
      ];
      return nodes.map((node, index) => {
        const center = centers[node.family];
        const angle = (node.member / 6) * TAU + node.family * .33;
        const rx = Math.min(width * .12, 88);
        const ry = Math.min(height * .16, 68);
        const depth = .82 + ((index * 7) % 11) / 40;
        return {
          ...node,
          x: center.x + Math.cos(angle) * rx * depth,
          y: center.y + Math.sin(angle) * ry * depth,
          z: depth
        };
      });
    }

    function updateReadout() {
      if (!readout) return;
      let strongest = { index: -1, value: 0 };
      nodes.forEach((node, index) => {
        if (index === selected) return;
        const value = correlationValue(selected, index, nodes);
        if (Math.abs(value) > Math.abs(strongest.value)) strongest = { index, value };
      });
      const current = nodes[selected];
      const peer = nodes[strongest.index];
      readout.textContent = `Synthetic series ${current.label} · family ${String.fromCharCode(65 + current.family)} · strongest illustrative relation ${peer.label} ${strongest.value.toFixed(2)}`;
    }

    function draw() {
      const sizing = fit(canvas, canvas.getBoundingClientRect().height || 430);
      if (!sizing) return;
      const { ctx, width, height } = sizing;
      const placed = layout(width, height);
      ctx.clearRect(0, 0, width, height);
      const glow = ctx.createRadialGradient(width * .5, height * .5, 20, width * .5, height * .5, width * .55);
      glow.addColorStop(0, 'rgba(108,167,255,.075)');
      glow.addColorStop(.55, 'rgba(255,82,110,.035)');
      glow.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, width, height);

      for (let i = 0; i < placed.length; i += 1) {
        for (let j = i + 1; j < placed.length; j += 1) {
          const relation = correlationValue(i, j, nodes);
          if (Math.abs(relation) < .62) continue;
          if (focusSelected && i !== selected && j !== selected) continue;
          const active = i === selected || j === selected;
          ctx.beginPath();
          ctx.moveTo(placed[i].x, placed[i].y);
          ctx.lineTo(placed[j].x, placed[j].y);
          ctx.strokeStyle = active ? 'rgba(61,232,255,.58)' : 'rgba(158,184,201,.13)';
          ctx.lineWidth = active ? 1.2 + Math.abs(relation) * 2 : .5 + Math.abs(relation);
          ctx.stroke();
        }
      }
      const familyColors = [
        [73, 239, 154],
        [255, 82, 110],
        [61, 232, 255]
      ];
      placed.forEach((node, index) => {
        const [r, g, b] = familyColors[node.family];
        const isSelected = index === selected;
        const radius = (isSelected ? 8.5 : 5.2) * node.z;
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius + (isSelected ? 8 : 0), 0, TAU);
        if (isSelected) {
          ctx.strokeStyle = 'rgba(238,252,255,.92)';
          ctx.lineWidth = 1.4;
          ctx.stroke();
        }
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, TAU);
        ctx.fillStyle = `rgba(${r},${g},${b},${isSelected ? .96 : .78})`;
        ctx.fill();
        ctx.fillStyle = isSelected ? 'rgba(238,252,255,.98)' : 'rgba(158,184,201,.80)';
        ctx.font = `${isSelected ? 700 : 500} 11px Cascadia Mono, Consolas, monospace`;
        ctx.fillText(node.label, node.x + 9, node.y - 8);
      });

      ctx.fillStyle = 'rgba(158,184,201,.52)';
      ctx.font = '10px Cascadia Mono, Consolas, monospace';
      ctx.fillText('FAMILY A', 14, 22);
      ctx.fillText('FAMILY B', width * .47, 22);
      ctx.fillText('FAMILY C', width - 72, 22);
      updateReadout();
    }

    function select(step) {
      selected = (selected + step + nodes.length) % nodes.length;
      draw();
    }
    previous?.addEventListener('click', () => select(-1));
    next?.addEventListener('click', () => select(1));
    focusButton?.addEventListener('click', () => {
      focusSelected = !focusSelected;
      focusButton.setAttribute('aria-pressed', String(focusSelected));
      draw();
    });
    window.addEventListener('resize', draw, { passive: true });
    draw();
  }

  function standardize(values) {
    const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
    const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length;
    const scale = Math.sqrt(Math.max(variance, 1e-9));
    return values.map((value) => (value - mean) / scale);
  }

  function gaussian(random) {
    const u1 = Math.max(1e-9, random());
    const u2 = Math.max(1e-9, random());
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(TAU * u2);
  }

  function buildDistribution(mode) {
    const random = mulberry32(mode === 'symmetric' ? 5041 : mode === 'skewed' ? 9107 : 17713);
    const values = [];
    for (let index = 0; index < 4000; index += 1) {
      const z = gaussian(random);
      if (mode === 'skewed') {
        const w = gaussian(random);
        values.push(.68 * z + .33 * (w * w - 1));
      } else if (mode === 'heavy') {
        const shock = random() < .075 ? 3.2 : 1;
        values.push(z * shock);
      } else {
        values.push(z);
      }
    }
    return standardize(values);
  }

  function initDistribution() {
    const host = document.querySelector('[data-distribution-explorer]');
    const canvas = document.querySelector('#distribution-canvas');
    const thresholdInput = document.querySelector('#distribution-threshold');
    if (!host || !canvas || !thresholdInput) return;
    const buttons = [...host.querySelectorAll('[data-distribution-mode]')];
    const thresholdValue = document.querySelector('#distribution-threshold-value');
    const belowNode = document.querySelector('#distribution-below');
    const medianNode = document.querySelector('#distribution-median');
    const p01Node = document.querySelector('#distribution-p01');
    let mode = 'symmetric';
    let values = buildDistribution(mode);

    function draw() {
      const sizing = fit(canvas, canvas.getBoundingClientRect().height || 390);
      if (!sizing) return;
      const { ctx, width, height } = sizing;
      const threshold = Number(thresholdInput.value);
      const minX = -4;
      const maxX = 4;
      const binCount = 48;
      const bins = Array(binCount).fill(0);
      for (const value of values) {
        const normalized = (value - minX) / (maxX - minX);
        const index = Math.max(0, Math.min(binCount - 1, Math.floor(normalized * binCount)));
        bins[index] += 1;
      }
      const maxBin = Math.max(...bins);
      const pad = { left: 38, right: 18, top: 24, bottom: 36 };
      const plotWidth = width - pad.left - pad.right;
      const plotHeight = height - pad.top - pad.bottom;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = 'rgba(3,10,17,.78)';
      ctx.fillRect(0, 0, width, height);

      bins.forEach((count, index) => {
        const x0 = pad.left + plotWidth * (index / binCount);
        const x1 = pad.left + plotWidth * ((index + 1) / binCount);
        const center = minX + (maxX - minX) * ((index + .5) / binCount);
        const barHeight = plotHeight * (count / maxBin);
        ctx.fillStyle = center <= threshold ? 'rgba(255,82,110,.72)' : 'rgba(108,167,255,.48)';
        ctx.fillRect(x0 + 1, pad.top + plotHeight - barHeight, Math.max(1, x1 - x0 - 2), barHeight);
      });
      const thresholdX = pad.left + plotWidth * ((threshold - minX) / (maxX - minX));
      ctx.strokeStyle = 'rgba(61,232,255,.92)';
      ctx.lineWidth = 1.4;
      ctx.beginPath();
      ctx.moveTo(thresholdX, pad.top);
      ctx.lineTo(thresholdX, pad.top + plotHeight);
      ctx.stroke();
      ctx.fillStyle = 'rgba(61,232,255,.95)';
      ctx.font = '11px Cascadia Mono, Consolas, monospace';
      ctx.fillText(`threshold ${threshold.toFixed(1)}`, Math.max(8, Math.min(width - 112, thresholdX + 6)), 18);
      ctx.fillStyle = 'rgba(158,184,201,.65)';
      ctx.fillText('-4', pad.left - 5, height - 12);
      ctx.fillText('0', pad.left + plotWidth * .5 - 3, height - 12);
      ctx.fillText('+4 standardized outcome', width - 151, height - 12);

      const below = values.filter((value) => value <= threshold).length / values.length;
      if (thresholdValue) thresholdValue.textContent = threshold.toFixed(2);
      if (belowNode) belowNode.textContent = `${(below * 100).toFixed(1)}%`;
      if (medianNode) medianNode.textContent = percentile(values, .50).toFixed(2);
      if (p01Node) p01Node.textContent = percentile(values, .01).toFixed(2);
    }

    thresholdInput.addEventListener('input', draw);
    buttons.forEach((button) => button.addEventListener('click', () => {
      mode = button.dataset.distributionMode || 'symmetric';
      values = buildDistribution(mode);
      buttons.forEach((candidate) => candidate.setAttribute('aria-pressed', String(candidate === button)));
      draw();
    }));
    window.addEventListener('resize', draw, { passive: true });
    draw();
  }

  const robustnessHost = document.querySelector('[data-robustness-explorer]');
  const correlationHost = document.querySelector('[data-correlation-explorer]');
  const distributionHost = document.querySelector('[data-distribution-explorer]');

  if (robustnessHost) whenVisible(robustnessHost, initRobustness);
  if (correlationHost) whenVisible(correlationHost, initCorrelation);
  if (distributionHost) whenVisible(distributionHost, initDistribution);
})();
