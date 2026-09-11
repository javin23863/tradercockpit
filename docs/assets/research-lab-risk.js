(() => {
  'use strict';

  const TAU = Math.PI * 2;

  function fit(canvas, fallbackHeight = 430) {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(280, Math.floor(rect.width));
    const height = Math.max(260, Math.floor(rect.height || fallbackHeight));
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
    const start = () => { if (!started) { started = true; init(); } };
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          observer.disconnect();
          start();
        }
      }, { rootMargin: '220px' });
      observer.observe(element);
    } else start();
  }

  function buildPath(mode) {
    const values = [];
    for (let index = 0; index < 120; index += 1) {
      const trend = 100 + index * .18;
      const wave = 1.8 * Math.sin(index / 7.5) + .9 * Math.sin(index / 3.9);
      let valley = 0;
      if (mode === 'long') {
        valley = 17 * Math.exp(-Math.pow((index - 64) / 27, 2));
      } else if (mode === 'repeat') {
        valley = 13 * Math.exp(-Math.pow((index - 31) / 8, 2))
          + 16 * Math.exp(-Math.pow((index - 69) / 10, 2))
          + 12 * Math.exp(-Math.pow((index - 101) / 8, 2));
      } else {
        valley = 30 * Math.exp(-Math.pow((index - 61) / 11, 2));
      }
      values.push(trend + wave - valley);
    }
    return values;
  }

  function drawdownStats(values) {
    const peaks = [];
    const drawdowns = [];
    let peak = values[0];
    let longest = 0;
    let current = 0;
    let recoveries = 0;
    let underwater = false;
    for (const value of values) {
      peak = Math.max(peak, value);
      peaks.push(peak);
      const dd = Math.max(0, (peak - value) / peak);
      drawdowns.push(dd);
      if (dd > 1e-6) {
        current += 1;
        underwater = true;
        longest = Math.max(longest, current);
      } else {
        if (underwater) recoveries += 1;
        underwater = false;
        current = 0;
      }
    }
    return {
      peaks,
      drawdowns,
      maxDrawdown: Math.max(...drawdowns),
      longest,
      recoveries
    };
  }

  function initDrawdown() {
    const host = document.querySelector('[data-drawdown-explorer]');
    const canvas = document.querySelector('#drawdown-canvas');
    if (!host || !canvas) return;
    const buttons = [...host.querySelectorAll('[data-drawdown-mode]')];
    const maxNode = document.querySelector('#drawdown-max');
    const durationNode = document.querySelector('#drawdown-duration');
    const recoveryNode = document.querySelector('#drawdown-recoveries');
    let mode = 'deep';

    function draw() {
      const sizing = fit(canvas, 430);
      if (!sizing) return;
      const { ctx, width, height } = sizing;
      const values = buildPath(mode);
      const stats = drawdownStats(values);
      const minValue = Math.min(...values) - 2;
      const maxValue = Math.max(...stats.peaks) + 2;
      const pad = { left: 36, right: 18, top: 28, bottom: 34 };
      const plotWidth = width - pad.left - pad.right;
      const plotHeight = height - pad.top - pad.bottom;
      const x = (index) => pad.left + (index / (values.length - 1)) * plotWidth;
      const y = (value) => pad.top + (1 - (value - minValue) / (maxValue - minValue)) * plotHeight;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = 'rgba(3,10,17,.80)';
      ctx.fillRect(0, 0, width, height);

      ctx.beginPath();
      stats.peaks.forEach((value, index) => {
        if (index === 0) ctx.moveTo(x(index), y(value));
        else ctx.lineTo(x(index), y(value));
      });
      for (let index = values.length - 1; index >= 0; index -= 1) {
        ctx.lineTo(x(index), y(values[index]));
      }
      ctx.closePath();
      const fill = ctx.createLinearGradient(0, pad.top, 0, height - pad.bottom);
      fill.addColorStop(0, 'rgba(61,232,255,.04)');
      fill.addColorStop(.45, 'rgba(255,82,110,.14)');
      fill.addColorStop(1, 'rgba(255,82,110,.38)');
      ctx.fillStyle = fill;
      ctx.fill();

      for (let index = 0; index < values.length; index += 5) {
        if (stats.drawdowns[index] < .004) continue;
        ctx.beginPath();
        ctx.moveTo(x(index), y(stats.peaks[index]));
        ctx.lineTo(x(index), y(values[index]));
        ctx.strokeStyle = `rgba(255,82,110,${Math.min(.5, .12 + stats.drawdowns[index] * 1.8).toFixed(3)})`;
        ctx.lineWidth = 1;
        ctx.stroke();
      }

      ctx.beginPath();
      stats.peaks.forEach((value, index) => {
        if (index === 0) ctx.moveTo(x(index), y(value));
        else ctx.lineTo(x(index), y(value));
      });
      ctx.strokeStyle = 'rgba(61,232,255,.72)';
      ctx.lineWidth = 1.2;
      ctx.setLineDash([5, 5]);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.beginPath();
      values.forEach((value, index) => {
        if (index === 0) ctx.moveTo(x(index), y(value));
        else ctx.lineTo(x(index), y(value));
      });
      ctx.strokeStyle = 'rgba(238,252,255,.90)';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.fillStyle = 'rgba(158,184,201,.66)';
      ctx.font = '10px Cascadia Mono, Consolas, monospace';
      ctx.fillText('synthetic path step →', Math.max(pad.left, width - 145), height - 12);
      ctx.fillStyle = 'rgba(61,232,255,.86)';
      ctx.fillText('running peak', 12, 18);
      ctx.fillStyle = 'rgba(255,82,110,.82)';
      ctx.fillText('shaded gap = drawdown', 103, 18);

      if (maxNode) maxNode.textContent = `${(stats.maxDrawdown * 100).toFixed(1)}%`;
      if (durationNode) durationNode.textContent = `${stats.longest} steps`;
      if (recoveryNode) recoveryNode.textContent = String(stats.recoveries);
    }

    buttons.forEach((button) => button.addEventListener('click', () => {
      mode = button.dataset.drawdownMode || 'deep';
      buttons.forEach((candidate) => candidate.setAttribute('aria-pressed', String(candidate === button)));
      draw();
    }));
    window.addEventListener('resize', draw, { passive: true });
    draw();
  }

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

  function gaussian(random) {
    const u1 = Math.max(1e-9, random());
    const u2 = Math.max(1e-9, random());
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(TAU * u2);
  }

  function normalCdf(x) {
    const absolute = Math.abs(x);
    const t = 1 / (1 + .2316419 * absolute);
    const density = .3989422804 * Math.exp(-.5 * absolute * absolute);
    const tail = density * t * (.319381530 + t * (-.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))));
    const positive = 1 - tail;
    return x >= 0 ? positive : 1 - positive;
  }

  function normalQuantile(probability) {
    let lo = -6;
    let hi = 6;
    for (let iteration = 0; iteration < 70; iteration += 1) {
      const mid = (lo + hi) / 2;
      if (normalCdf(mid) < probability) lo = mid;
      else hi = mid;
    }
    return (lo + hi) / 2;
  }

  function typicalMaximum(count) {
    const plottingPosition = (count - .375) / (count + .25);
    return normalQuantile(plottingPosition);
  }

  function buildScores(count) {
    const random = mulberry32(91001 + count * 17);
    return Array.from({ length: count }, (_, index) => ({
      id: index,
      score: gaussian(random)
    })).sort((a, b) => b.score - a.score);
  }

  function initSelection() {
    const host = document.querySelector('[data-selection-explorer]');
    const canvas = document.querySelector('#selection-canvas');
    const familyInput = document.querySelector('#selection-family');
    if (!host || !canvas || !familyInput) return;
    const familyValue = document.querySelector('#selection-family-value');
    const observedNode = document.querySelector('#selection-observed');
    const typicalNode = document.querySelector('#selection-typical');
    const survivorNode = document.querySelector('#selection-survivors');

    function draw() {
      const sizing = fit(canvas, 440);
      if (!sizing) return;
      const { ctx, width, height } = sizing;
      const exponent = Number(familyInput.value);
      const count = 2 ** exponent;
      const scores = buildScores(count);
      const observed = scores[0].score;
      const typical = typicalMaximum(count);
      const stageCounts = [count, Math.max(1, Math.ceil(count * .25)), Math.max(1, Math.ceil(count * .05)), 1];
      const stageX = [width * .12, width * .39, width * .66, width * .88];
      const padTop = 42;
      const padBottom = 45;
      const plotHeight = height - padTop - padBottom;
      const minScore = -3.3;
      const maxScore = Math.max(3.8, observed + .35);
      const mapY = (score) => padTop + (1 - (score - minScore) / (maxScore - minScore)) * plotHeight;
      ctx.clearRect(0, 0, width, height);
      const bg = ctx.createLinearGradient(0, 0, width, 0);
      bg.addColorStop(0, 'rgba(108,167,255,.055)');
      bg.addColorStop(.6, 'rgba(255,82,110,.035)');
      bg.addColorStop(1, 'rgba(61,232,255,.065)');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);

      const typicalY = mapY(typical);
      ctx.strokeStyle = 'rgba(61,232,255,.64)';
      ctx.lineWidth = 1;
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(28, typicalY);
      ctx.lineTo(width - 18, typicalY);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = 'rgba(61,232,255,.88)';
      ctx.font = '10px Cascadia Mono, Consolas, monospace';
      ctx.fillText(`approx. typical max ${typical.toFixed(2)}`, 34, Math.max(16, typicalY - 6));

      const stageLabels = ['family', 'top 25%', 'top 5%', 'selected max'];
      stageX.forEach((xCenter, index) => {
        const retained = scores.slice(0, stageCounts[index]);
        const displayCount = Math.min(retained.length, index === 0 ? 150 : index === 1 ? 110 : index === 2 ? 70 : 1);
        ctx.fillStyle = 'rgba(255,255,255,.018)';
        ctx.fillRect(xCenter - 20, padTop - 8, 40, plotHeight + 16);
        ctx.strokeStyle = 'rgba(255,255,255,.065)';
        ctx.strokeRect(xCenter - 20, padTop - 8, 40, plotHeight + 16);
        const jitter = mulberry32(count * 97 + index * 1301);
        for (let point = 0; point < displayCount; point += 1) {
          const sourceIndex = displayCount === 1 ? 0 : Math.floor(point * (retained.length - 1) / Math.max(1, displayCount - 1));
          const item = retained[sourceIndex];
          const px = xCenter + (jitter() - .5) * (index === 0 ? 32 : index === 1 ? 27 : index === 2 ? 21 : 0);
          const py = mapY(item.score);
          ctx.beginPath();
          ctx.arc(px, py, index === 3 ? 5.5 : 1.8 + index * .28, 0, TAU);
          ctx.fillStyle = index === 0 ? 'rgba(108,167,255,.45)' : index === 1 ? 'rgba(255,82,110,.50)' : index === 2 ? 'rgba(73,239,154,.62)' : 'rgba(61,232,255,.96)';
          ctx.fill();
        }
        ctx.fillStyle = 'rgba(158,184,201,.72)';
        ctx.font = '10px Cascadia Mono, Consolas, monospace';
        ctx.textAlign = 'center';
        ctx.fillText(stageLabels[index], xCenter, height - 21);
        ctx.fillText(index === 3 ? '1' : String(stageCounts[index]), xCenter, height - 8);
      });
      ctx.textAlign = 'left';

      ctx.beginPath();
      stageX.forEach((xCenter, index) => {
        const cutoff = scores[stageCounts[index] - 1].score;
        if (index === 0) ctx.moveTo(xCenter, mapY(cutoff));
        else ctx.lineTo(xCenter, mapY(cutoff));
      });
      ctx.strokeStyle = 'rgba(255,82,110,.58)';
      ctx.lineWidth = 1.4;
      ctx.stroke();

      ctx.beginPath();
      stageX.forEach((xCenter, index) => {
        if (index === 0) ctx.moveTo(xCenter, mapY(observed));
        else ctx.lineTo(xCenter, mapY(observed));
      });
      ctx.strokeStyle = 'rgba(61,232,255,.72)';
      ctx.lineWidth = 1.2;
      ctx.stroke();

      ctx.fillStyle = 'rgba(158,184,201,.62)';
      ctx.font = '10px Cascadia Mono, Consolas, monospace';
      ctx.fillText('higher synthetic z (up)', 12, 18);
      if (familyValue) familyValue.textContent = String(count);
      familyInput.setAttribute('aria-valuetext', `${count} synthetic candidates`);
      if (observedNode) observedNode.textContent = observed.toFixed(2);
      if (typicalNode) typicalNode.textContent = typical.toFixed(2);
      if (survivorNode) survivorNode.textContent = `1 of ${count}`;
    }


    familyInput.addEventListener('input', draw);
    window.addEventListener('resize', draw, { passive: true });
    draw();
  }

  const drawdownHost = document.querySelector('[data-drawdown-explorer]');
  const selectionHost = document.querySelector('[data-selection-explorer]');
  if (drawdownHost) whenVisible(drawdownHost, initDrawdown);
  if (selectionHost) whenVisible(selectionHost, initSelection);
})();
