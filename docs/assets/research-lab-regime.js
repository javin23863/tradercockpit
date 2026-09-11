(() => {
  'use strict';

  const host = document.querySelector('[data-regime-explorer]');
  const canvas = document.querySelector('#regime-canvas');
  if (!host || !canvas) return;

  const TAU = Math.PI * 2;
  const filterButtons = [...host.querySelectorAll('[data-regime-filter]')];
  const left = document.querySelector('#regime-rotate-left');
  const right = document.querySelector('#regime-rotate-right');
  const previous = document.querySelector('#regime-prev');
  const next = document.querySelector('#regime-next');
  const readout = document.querySelector('#regime-readout');
  const directionNode = document.querySelector('#regime-direction');
  const volatilityNode = document.querySelector('#regime-volatility');
  const stressNode = document.querySelector('#regime-stress');

  function mulberry32(seed) {
    let value = seed >>> 0;
    return () => {
      value += 0x6D2B79F5;
      let t = value;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const random = mulberry32(90517);
  const points = Array.from({ length: 96 }, (_, index) => {
    const direction = random() * 2 - 1;
    const volatility = random();
    const stress = random();
    return {
      index,
      direction,
      volatility,
      stress,
      x: direction,
      y: volatility * 2 - 1,
      z: stress * 2 - 1
    };
  });

  function label(point) {
    if (point.stress >= .66) return 'Liquidity stress';
    if (point.volatility >= .62 && Math.abs(point.direction) >= .45) return 'Volatile directional';
    if (point.volatility >= .62) return 'Volatile range';
    if (Math.abs(point.direction) >= .45) return 'Directional';
    return 'Quiet range';
  }

  const colors = {
    'Liquidity stress': [255, 82, 110],
    'Volatile directional': [90, 167, 255],
    'Volatile range': [73, 239, 154],
    'Directional': [61, 232, 255],
    'Quiet range': [119, 228, 220]
  };
  let yaw = -.62;
  let selected = 0;
  let filter = 'all';

  function fitCanvas() {
    const rect = canvas.getBoundingClientRect();
    const width = Math.max(280, Math.floor(rect.width));
    const height = Math.max(300, Math.floor(rect.height));
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, width, height };
  }

  function rotate(point) {
    const cy = Math.cos(yaw);
    const sy = Math.sin(yaw);
    const pitch = -.34;
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
    const depth = 3.3 - rotated.z;
    const scale = Math.min(width, height) * .40 / depth;
    return {
      x: width * .5 + rotated.x * scale,
      y: height * .53 - rotated.y * scale,
      z: rotated.z,
      scale: Math.max(.65, Math.min(1.45, 2.4 / depth))
    };
  }

  const cubeVertices = [
    [-1,-1,-1], [1,-1,-1], [-1,1,-1], [1,1,-1],
    [-1,-1,1], [1,-1,1], [-1,1,1], [1,1,1]
  ].map(([x,y,z]) => ({x,y,z}));
  const cubeEdges = [
    [0,1],[0,2],[1,3],[2,3],
    [4,5],[4,6],[5,7],[6,7],
    [0,4],[1,5],[2,6],[3,7]
  ];

  function visiblePoints() {
    if (filter === 'low') return points.filter((point) => point.stress < .5);
    if (filter === 'high') return points.filter((point) => point.stress >= .5);
    return points;
  }
  function updateReadout() {
    const point = points[selected];
    if (directionNode) directionNode.textContent = point.direction.toFixed(2);
    if (volatilityNode) volatilityNode.textContent = point.volatility.toFixed(2);
    if (stressNode) stressNode.textContent = point.stress.toFixed(2);
    if (readout) {
      readout.textContent = `Synthetic observation ${String(point.index + 1).padStart(2,'0')} · ${label(point)} · direction ${point.direction.toFixed(2)} · volatility ${point.volatility.toFixed(2)} · liquidity stress ${point.stress.toFixed(2)}`;
    }
  }

  function drawCube(ctx, width, height) {
    const projected = cubeVertices.map((point) => project(point, width, height));
    ctx.save();
    ctx.lineWidth = 1;
    for (const [a,b] of cubeEdges) {
      ctx.beginPath();
      ctx.moveTo(projected[a].x, projected[a].y);
      ctx.lineTo(projected[b].x, projected[b].y);
      ctx.strokeStyle = 'rgba(61,232,255,.18)';
      ctx.stroke();
    }
    ctx.restore();
  }

  function drawAxes(ctx, width, height) {
    const origin = project({x:-1,y:-1,z:-1}, width, height);
    const axes = [
      [{x:1.25,y:-1,z:-1}, 'direction →', 'rgba(108,167,255,.65)'],
      [{x:-1,y:1.25,z:-1}, 'volatility ↑', 'rgba(61,232,255,.65)'],
      [{x:-1,y:-1,z:1.25}, 'stress ↗', 'rgba(255,82,110,.65)']
    ];
    ctx.save();
    ctx.font = '10px Cascadia Mono, Consolas, monospace';
    for (const [axis,labelText,color] of axes) {
      const end = project(axis, width, height);
      ctx.beginPath();
      ctx.moveTo(origin.x, origin.y);
      ctx.lineTo(end.x, end.y);
      ctx.strokeStyle = color;
      ctx.stroke();
      ctx.fillStyle = color;
      ctx.fillText(labelText, end.x + 5, end.y - 4);
    }
    ctx.restore();
  }
  function draw() {
    const sizing = fitCanvas();
    if (!sizing) return;
    const {ctx,width,height} = sizing;
    ctx.clearRect(0,0,width,height);
    const glow = ctx.createRadialGradient(width*.5,height*.5,12,width*.5,height*.5,Math.max(width,height)*.62);
    glow.addColorStop(0,'rgba(108,167,255,.08)');
    glow.addColorStop(.45,'rgba(255,82,110,.035)');
    glow.addColorStop(1,'rgba(0,0,0,0)');
    ctx.fillStyle = glow;
    ctx.fillRect(0,0,width,height);
    drawCube(ctx,width,height);
    drawAxes(ctx,width,height);

    const visible = visiblePoints()
      .map((point) => ({point,screen:project(point,width,height)}))
      .sort((a,b) => a.screen.z - b.screen.z);
    for (const {point,screen} of visible) {
      const [r,g,b] = colors[label(point)];
      const isSelected = point.index === selected;
      const radius = (isSelected ? 5.2 : 2.7) * screen.scale;
      ctx.beginPath();
      ctx.arc(screen.x,screen.y,radius,0,TAU);
      ctx.fillStyle = `rgba(${r},${g},${b},${isSelected ? .98 : .58})`;
      ctx.fill();
      if (isSelected) {
        ctx.beginPath();
        ctx.arc(screen.x,screen.y,radius+7,0,TAU);
        ctx.strokeStyle='rgba(238,252,255,.92)';
        ctx.lineWidth=1.4;
        ctx.stroke();
        ctx.fillStyle='rgba(238,252,255,.92)';
        ctx.font='10px Cascadia Mono, Consolas, monospace';
        ctx.fillText(label(point),screen.x+12,screen.y-9);
      }
    }
    updateReadout();
  }
  function choose(step) {
    const visible = visiblePoints();
    if (!visible.length) return;
    const currentIndex = visible.findIndex((point) => point.index === selected);
    const nextIndex = currentIndex < 0 ? 0 : (currentIndex + step + visible.length) % visible.length;
    selected = visible[nextIndex].index;
    draw();
  }

  filterButtons.forEach((button) => button.addEventListener('click', () => {
    filter = button.dataset.regimeFilter || 'all';
    filterButtons.forEach((candidate) => candidate.setAttribute('aria-pressed', String(candidate === button)));
    const visible = visiblePoints();
    if (!visible.some((point) => point.index === selected) && visible.length) selected = visible[0].index;
    draw();
  }));
  left?.addEventListener('click', () => { yaw -= .22; draw(); });
  right?.addEventListener('click', () => { yaw += .22; draw(); });
  previous?.addEventListener('click', () => choose(-1));
  next?.addEventListener('click', () => choose(1));
  window.addEventListener('resize', draw, {passive:true});

  function init() {
    draw();
  }
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        init();
        observer.disconnect();
      }
    }, {rootMargin:'180px'});
    observer.observe(host);
  } else {
    init();
  }
})();
