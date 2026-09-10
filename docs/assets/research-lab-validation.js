(() => {
  'use strict';

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

  function initWalkForward() {
    const host = document.querySelector('[data-walk-forward-explorer]');
    const canvas = document.querySelector('#walk-forward-canvas');
    if (!host || !canvas) return;
    const modeButtons = [...host.querySelectorAll('[data-wf-mode]')];
    const previous = document.querySelector('#wf-prev');
    const next = document.querySelector('#wf-next');
    const readout = document.querySelector('#wf-readout');
    const trainSpanNode = document.querySelector('#wf-train-span');
    let mode = 'rolling';
    let selected = 3;
    const foldCount = 7;
    const evalSpan = 10;

    function folds() {
      return Array.from({ length: foldCount }, (_, index) => {
        const trainStart = mode === 'rolling' ? index * 8 : 0;
        const trainEnd = 42 + index * 8;
        return {
          index,
          trainStart,
          trainEnd,
          evalStart: trainEnd,
          evalEnd: trainEnd + evalSpan
        };
      });
    }

    function platform(ctx, x0, x1, y, height, skew, fill, stroke) {
      ctx.beginPath();
      ctx.moveTo(x0, y);
      ctx.lineTo(x1, y);
      ctx.lineTo(x1 + skew, y + height);
      ctx.lineTo(x0 + skew, y + height);
      ctx.closePath();
      ctx.fillStyle = fill;
      ctx.fill();
      ctx.strokeStyle = stroke;
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    function draw() {
      const sizing = fit(canvas, 450);
      if (!sizing) return;
      const { ctx, width, height } = sizing;
      const rows = folds();
      ctx.clearRect(0, 0, width, height);
      const bg = ctx.createLinearGradient(0, 0, width, height);
      bg.addColorStop(0, 'rgba(108,167,255,.06)');
      bg.addColorStop(.55, 'rgba(255,23,68,.025)');
      bg.addColorStop(1, 'rgba(255,183,43,.055)');
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);

      const left = Math.max(34, width * .06);
      const right = Math.max(28, width * .05);
      const plotWidth = width - left - right - 18;
      const mapX = (time) => left + (time / 100) * plotWidth;
      const top = 52;
      const rowGap = Math.min(52, (height - 115) / foldCount);
      rows.forEach((fold) => {
        const y = top + fold.index * rowGap;
        const skew = Math.min(12, width * .025);
        const active = fold.index === selected;
        platform(ctx, mapX(0), mapX(100), y, 20, skew, 'rgba(255,255,255,.018)', 'rgba(255,255,255,.055)');
        platform(ctx, mapX(fold.trainStart), mapX(fold.trainEnd), y, 20, skew, active ? 'rgba(108,167,255,.62)' : 'rgba(108,167,255,.28)', active ? 'rgba(180,214,255,.85)' : 'rgba(108,167,255,.26)');
        platform(ctx, mapX(fold.evalStart), mapX(fold.evalEnd), y, 20, skew, active ? 'rgba(255,183,43,.78)' : 'rgba(255,183,43,.38)', active ? 'rgba(255,236,180,.90)' : 'rgba(255,183,43,.32)');
        if (active) {
          ctx.strokeStyle = 'rgba(255,245,238,.78)';
          ctx.lineWidth = 1;
          ctx.strokeRect(mapX(fold.trainStart) - 3, y - 4, mapX(fold.evalEnd) - mapX(fold.trainStart) + skew + 6, 28);
        }
        ctx.fillStyle = active ? 'rgba(255,245,238,.95)' : 'rgba(213,171,176,.56)';
        ctx.font = `${active ? 700 : 500} 10px Cascadia Mono, Consolas, monospace`;
        ctx.fillText(`F${fold.index + 1}`, 8, y + 14);
      });

      ctx.fillStyle = 'rgba(213,171,176,.62)';
      ctx.font = '10px Cascadia Mono, Consolas, monospace';
      ctx.fillText('0', left - 2, height - 20);
      ctx.fillText('50', mapX(50) - 7, height - 20);
      ctx.fillText('100 synthetic time →', Math.max(left, width - 145), height - 20);
      const fold = rows[selected];
      if (readout) readout.textContent = `Fold ${fold.index + 1} of ${foldCount} · train ${fold.trainStart}–${fold.trainEnd} · evaluate ${fold.evalStart}–${fold.evalEnd} synthetic time units`;
      if (trainSpanNode) trainSpanNode.textContent = String(fold.trainEnd - fold.trainStart);
    }

    previous?.addEventListener('click', () => { selected = (selected + foldCount - 1) % foldCount; draw(); });
    next?.addEventListener('click', () => { selected = (selected + 1) % foldCount; draw(); });
    modeButtons.forEach((button) => button.addEventListener('click', () => {
      mode = button.dataset.wfMode || 'rolling';
      modeButtons.forEach((candidate) => candidate.setAttribute('aria-pressed', String(candidate === button)));
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

  function arrowHead(ctx, fromX, fromY, toX, toY, size = 7) {
    const angle = Math.atan2(toY - fromY, toX - fromX);
    ctx.beginPath();
    ctx.moveTo(toX, toY);
    ctx.lineTo(toX - Math.cos(angle - .52) * size, toY - Math.sin(angle - .52) * size);
    ctx.lineTo(toX - Math.cos(angle + .52) * size, toY - Math.sin(angle + .52) * size);
    ctx.closePath();
    ctx.fill();
  }

  function initOosBoundary() {
    const host = document.querySelector('[data-oos-explorer]');
    const canvas = document.querySelector('#oos-canvas');
    if (!host || !canvas) return;
    const buttons = [...host.querySelectorAll('[data-oos-mode]')];
    const stateNode = document.querySelector('#oos-boundary-state');
    const feedbackNode = document.querySelector('#oos-feedback');
    const notice = document.querySelector('#oos-notice');
    let mode = 'clean';

    function draw() {
      const sizing = fit(canvas, 430);
      if (!sizing) return;
      const { ctx, width, height } = sizing;
      const boundary = width * .59;
      const selectX = boundary - Math.min(72, width * .13);
      const selectY = height * .52;
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = 'rgba(108,167,255,.045)';
      ctx.fillRect(0, 0, boundary, height);
      ctx.fillStyle = mode === 'clean' ? 'rgba(255,183,43,.035)' : 'rgba(255,92,119,.055)';
      ctx.fillRect(boundary, 0, width - boundary, height);

      ctx.strokeStyle = mode === 'clean' ? 'rgba(255,183,43,.78)' : 'rgba(255,92,119,.82)';
      ctx.lineWidth = 1.6;
      ctx.setLineDash([5, 6]);
      ctx.beginPath();
      ctx.moveTo(boundary, 34);
      ctx.lineTo(boundary, height - 36);
      ctx.stroke();
      ctx.setLineDash([]);
      const random = mulberry32(44021);
      const candidates = Array.from({ length: 36 }, (_, index) => ({
        index,
        x: 28 + random() * Math.min(88, width * .12),
        y: 66 + random() * (height - 132),
        bend: (random() - .5) * 82
      }));
      const selectedIndex = 11;
      candidates.forEach((candidate) => {
        const selected = candidate.index === selectedIndex;
        ctx.beginPath();
        ctx.moveTo(candidate.x, candidate.y);
        ctx.bezierCurveTo(width * .25, candidate.y + candidate.bend, width * .40, selectY - candidate.bend * .25, selectX, selectY);
        ctx.strokeStyle = selected ? 'rgba(255,183,43,.92)' : 'rgba(108,167,255,.105)';
        ctx.lineWidth = selected ? 2.1 : .7;
        ctx.stroke();
        if (!selected) {
          ctx.beginPath();
          ctx.arc(candidate.x, candidate.y, 2.1, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(108,167,255,.38)';
          ctx.fill();
        }
      });

      ctx.beginPath();
      ctx.arc(selectX, selectY, 9, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,183,43,.92)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(255,245,238,.90)';
      ctx.lineWidth = 1.4;
      ctx.stroke();

      const evalPoints = [
        { x: boundary + 24, y: selectY - 18 },
        { x: boundary + (width - boundary) * .38, y: selectY + 24 },
        { x: boundary + (width - boundary) * .68, y: selectY - 35 },
        { x: width - 28, y: selectY + 8 }
      ];
      ctx.beginPath();
      ctx.moveTo(selectX, selectY);
      evalPoints.forEach((point) => ctx.lineTo(point.x, point.y));
      ctx.strokeStyle = 'rgba(255,183,43,.82)';
      ctx.lineWidth = 2.2;
      ctx.stroke();
      evalPoints.forEach((point, index) => {
        ctx.beginPath();
        ctx.arc(point.x, point.y, index === evalPoints.length - 1 ? 4.2 : 3.2, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255,183,43,.86)';
        ctx.fill();
      });

      if (mode === 'peek') {
        const sources = evalPoints.slice(0, 4);
        sources.forEach((source, index) => {
          const targetY = selectY + (index - 1.5) * 17;
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          ctx.bezierCurveTo(boundary + 18, source.y - 32, boundary - 28, targetY + 28, selectX + 4, targetY);
          ctx.strokeStyle = 'rgba(255,92,119,.72)';
          ctx.lineWidth = 1.4;
          ctx.setLineDash([4, 5]);
          ctx.stroke();
          ctx.setLineDash([]);
          ctx.fillStyle = 'rgba(255,92,119,.88)';
          arrowHead(ctx, boundary - 14, targetY + 12, selectX + 4, targetY, 7);
        });
      }

      ctx.fillStyle = 'rgba(213,171,176,.70)';
      ctx.font = '10px Cascadia Mono, Consolas, monospace';
      ctx.fillText('DEVELOP + SELECT', 16, 24);
      ctx.fillText('HELD-OUT EVALUATION', Math.min(width - 142, boundary + 12), 24);
      ctx.save();
      ctx.translate(boundary + 12, height - 44);
      ctx.rotate(-Math.PI / 2);
      ctx.fillStyle = mode === 'clean' ? 'rgba(255,183,43,.82)' : 'rgba(255,92,119,.88)';
      ctx.fillText('information boundary', 0, 0);
      ctx.restore();
      ctx.fillStyle = 'rgba(255,183,43,.94)';
      ctx.fillText(mode === 'clean' ? 'selected once' : 'selection + feedback', selectX - 38, selectY - 16);

      if (stateNode) stateNode.textContent = mode === 'clean' ? 'Preserved' : 'Compromised';
      if (feedbackNode) feedbackNode.textContent = mode === 'clean' ? '0' : '4 illustrative';
      if (notice) {
        const label = document.createElement('strong');
        label.textContent = mode === 'clean' ? 'Preserved holdout:' : 'Repeated peek:';
        const detail = mode === 'clean'
          ? ' selection does not receive feedback from the illustrative evaluation region before the one-time evaluation shown here.'
          : ' this illustration feeds holdout information back into selection four times, so the holdout is no longer independent of the depicted selection process.';
        notice.replaceChildren(label, document.createTextNode(detail));
      }
    }

    buttons.forEach((button) => button.addEventListener('click', () => {
      mode = button.dataset.oosMode || 'clean';
      buttons.forEach((candidate) => candidate.setAttribute('aria-pressed', String(candidate === button)));
      draw();
    }));
    window.addEventListener('resize', draw, { passive: true });
    draw();
  }

  const walkForwardHost = document.querySelector('[data-walk-forward-explorer]');
  const oosHost = document.querySelector('[data-oos-explorer]');
  if (walkForwardHost) whenVisible(walkForwardHost, initWalkForward);
  if (oosHost) whenVisible(oosHost, initOosBoundary);
})();
