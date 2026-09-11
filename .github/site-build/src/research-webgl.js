import * as THREE from 'three';

(() => {
  'use strict';
  const SURFACE_IDS = [
    'strategy-universe-canvas', 'monte-carlo-canvas', 'robustness-canvas',
    'correlation-canvas', 'distribution-canvas', 'regime-canvas',
    'walk-forward-canvas', 'oos-canvas', 'drawdown-canvas', 'selection-canvas',
  ];
  if (!SURFACE_IDS.some((id) => document.getElementById(id))) return;

  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const mobile = matchMedia('(max-width: 760px)').matches;
  const TEAL = new THREE.Color('#3cfad2');
  const RED = new THREE.Color('#e54a5a');
  const CYAN = new THREE.Color('#3daed3');
  const BLUE = new THREE.Color('#3b779a');
  const WHITE = new THREE.Color('#f6f8fa');
  const BG = 0x010509;
  const registry = new Set();
  window.__tcResearchWebGL = { surfaces: registry, data: {} };

  function mulberry32(seed) {
    return () => {
      seed |= 0;
      seed = seed + 0x6D2B79F5 | 0;
      let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }

  function line(points, color = CYAN, opacity = 0.65) {
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    return new THREE.Line(geometry, new THREE.LineBasicMaterial({
      color, transparent: opacity < 1, opacity, depthWrite: false,
    }));
  }

  function segments(points, colors = null, opacity = 0.7) {
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({
      color: colors ? 0xffffff : CYAN,
      vertexColors: Boolean(colors), transparent: true, opacity, depthWrite: false,
    });
    if (colors) geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
    return new THREE.LineSegments(geometry, material);
  }

  function signedColor(value, deadband = 0.08) {
    return value > deadband ? TEAL : value < -deadband ? RED : CYAN;
  }


  function gaussian(random) {
    const u1 = Math.max(1e-9, random());
    const u2 = Math.max(1e-9, random());
    return Math.sqrt(-2 * Math.log(u1)) * Math.cos(Math.PI * 2 * u2);
  }

  function percentile(values, q) {
    const sorted = [...values].sort((a, b) => a - b);
    const index = (sorted.length - 1) * q;
    const lower = Math.floor(index), upper = Math.ceil(index);
    if (lower === upper) return sorted[lower];
    const weight = index - lower;
    return sorted[lower] * (1 - weight) + sorted[upper] * weight;
  }

  function standardize(values) {
    const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
    const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length;
    const scale = Math.sqrt(Math.max(variance, 1e-9));
    return values.map((value) => (value - mean) / scale);
  }


  function annotationText(ctx, text, x, y, color = 'rgba(164,171,179,.78)', align = 'left') {
    ctx.save();
    ctx.font = '600 10px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace';
    ctx.textAlign = align; ctx.textBaseline = 'middle';
    ctx.fillStyle = 'rgba(1,5,9,.72)';
    const width = ctx.measureText(text).width + 10;
    const left = align === 'right' ? x - width : align === 'center' ? x - width / 2 : x;
    ctx.fillRect(left - 2, y - 8, width + 4, 16);
    ctx.fillStyle = color; ctx.fillText(text, x + (align === 'left' ? 3 : 0), y);
    ctx.restore();
  }

  function projectPoint(point, camera, root, width, height) {
    root.updateWorldMatrix(true, false); camera.updateMatrixWorld();
    const projected = point.clone(); root.localToWorld(projected); projected.project(camera);
    return {x:(projected.x * .5 + .5) * width, y:(-.5 * projected.y + .5) * height, visible:projected.z > -1 && projected.z < 1};
  }

  function setupSurface(id, builder, cameraPosition = [0, 3.2, 7.6]) {
    const base = document.getElementById(id);
    if (!base || base.closest('.lab-canvas-stack')) return null;
    const wrapper = document.createElement('div');
    wrapper.className = `lab-canvas-stack lab-canvas-stack-${id.replace('-canvas', '')}`;
    base.before(wrapper);
    wrapper.append(base);
    const overlay = document.createElement('canvas');
    overlay.className = 'lab-webgl-overlay';
    overlay.setAttribute('aria-hidden', 'true');
    overlay.dataset.renderer = 'three-webgl';
    wrapper.append(overlay);
    const context = overlay.getContext('webgl2', {alpha:true, antialias:false, powerPreference:'high-performance'});
    if (!context) { overlay.remove(); wrapper.before(base); wrapper.remove(); return null; }
    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({canvas: overlay, context, alpha:true, antialias:false, powerPreference:'high-performance'});
    } catch {
      overlay.remove(); wrapper.before(base); wrapper.remove();
      return null;
    }
    renderer.setClearColor(BG, 0);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;

    const annotations = document.createElement('canvas');
    annotations.className = 'lab-webgl-annotations';
    annotations.setAttribute('aria-hidden', 'true');
    wrapper.append(annotations);
    const annotationContext = annotations.getContext('2d');

    const scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(BG, 0.075);
    const camera = new THREE.PerspectiveCamera(43, 1, 0.1, 50);
    const baseCameraPosition = new THREE.Vector3(...cameraPosition);
    camera.position.copy(baseCameraPosition);
    camera.lookAt(0, 0.25, 0);
    const root = new THREE.Group();
    scene.add(root);
    scene.add(new THREE.HemisphereLight(0x8feeff, 0x010509, 0.72));
    const key = new THREE.PointLight(0x3cfad2, 11, 14, 2);
    key.position.set(-3.5, 4.5, 4.5); scene.add(key);
    const risk = new THREE.PointLight(0xe54a5a, 5, 10, 2.2);
    risk.position.set(3.6, -0.3, 3); scene.add(risk);

    const view = {yaw: 0, pitch: 0, hoverYaw: 0, hoverPitch: 0};
    let state = null;
    let visible = false;
    let raf = 0;
    let width = 0, height = 0, last = performance.now(), fallbackActive = false;

    function resize() {
      const rect = overlay.getBoundingClientRect();
      const w = Math.max(280, Math.round(rect.width));
      const h = Math.max(220, Math.round(rect.height));
      if (w === width && h === height) return;
      width = w; height = h;
      const pixelRatio = Math.min(devicePixelRatio || 1, mobile ? 1.15 : 1.5);
      renderer.setPixelRatio(pixelRatio);
      renderer.setSize(w, h, false);
      camera.aspect = w / h;
      camera.position.copy(baseCameraPosition);
      camera.position.z = baseCameraPosition.z * Math.max(1, 1.30 / camera.aspect);
      camera.updateProjectionMatrix();
      const annotationRatio = Math.min(devicePixelRatio || 1, 1.5);
      annotations.width = Math.round(w * annotationRatio); annotations.height = Math.round(h * annotationRatio);
      annotations.style.width = `${w}px`; annotations.style.height = `${h}px`;
      annotationContext?.setTransform(annotationRatio,0,0,annotationRatio,0,0);
    }
    function render(now = performance.now()) {
      if (fallbackActive) return;
      resize();
      const dt = Math.min(0.05, Math.max(0, (now - last) / 1000)); last = now;
      state?.animate?.(now, dt);
      root.rotation.y = view.yaw + view.hoverYaw;
      root.rotation.x = view.pitch + view.hoverPitch;
      renderer.render(scene, camera);
      if (annotationContext) {
        annotationContext.clearRect(0,0,width,height);
        state?.annotate?.(annotationContext,width,height,camera,root);
      }
    }
    function frame(now) {
      raf = 0; render(now);
      if (state?.animate && visible && !reduced && !document.hidden) raf = requestAnimationFrame(frame);
    }
    function start() {
      if (fallbackActive || raf || !visible || document.hidden) return;
      if (reduced || !state?.animate) { render(reduced ? 0 : performance.now()); return; }
      last = performance.now(); raf = requestAnimationFrame(frame);
    }
    function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
    const invalidate = () => { if (!fallbackActive && (visible || reduced)) render(); };
    state = builder({scene, root, camera, renderer, base, overlay, wrapper, view, invalidate, random: mulberry32(id.length * 7331 + 17)}) || {};

    overlay.addEventListener('pointermove', (event) => {
      if (reduced) return;
      const r = overlay.getBoundingClientRect();
      view.hoverYaw = ((event.clientX - r.left) / r.width - 0.5) * 0.26;
      view.hoverPitch = -((event.clientY - r.top) / r.height - 0.5) * 0.12;
      if (!raf) invalidate();
    }, {passive: true});
    overlay.addEventListener('pointerleave', () => { view.hoverYaw = 0; view.hoverPitch = 0; invalidate(); }, {passive: true});
    overlay.addEventListener('webglcontextlost', (event) => {
      event.preventDefault(); fallbackActive = true; stop();
      overlay.style.display = 'none'; annotations.style.display = 'none';
      base.style.opacity = ''; base.style.pointerEvents = '';
      wrapper.dataset.webgl = 'fallback';
    });
    const observer = new IntersectionObserver((entries) => {
      visible = entries.some((entry) => entry.isIntersecting);
      if (visible) start(); else stop();
    }, {rootMargin: '180px'});
    observer.observe(wrapper);
    addEventListener('resize', () => { width = 0; invalidate(); }, {passive: true});
    document.addEventListener('visibilitychange', () => document.hidden ? stop() : start());

    base.style.opacity = '0';
    base.style.pointerEvents = 'none';
    wrapper.dataset.webgl = 'active';
    registry.add(id);
    render(reduced ? 0 : performance.now());
    return {root, scene, camera, view, invalidate, state};
  }

  function addFloor(root, size = 8, divisions = 16) {
    const grid = new THREE.GridHelper(size, divisions, 0x3daed3, 0x16485b);
    grid.material.transparent = true; grid.material.opacity = 0.19; grid.position.y = -1.65;
    root.add(grid); return grid;
  }


  function disposeObject(object) {
    object.traverse?.((child) => {
      child.geometry?.dispose?.();
      if (Array.isArray(child.material)) child.material.forEach((material) => material?.dispose?.());
      else child.material?.dispose?.();
    });
    object.removeFromParent?.();
  }

  function buildStrategyUniverse({root, view, invalidate}) {
    addFloor(root, 9, 18);
    const random = mulberry32(23863);
    const source = Array.from({length: 150}, (_, index) => {
      const dispersion = random(), drawdown = random(), disagreement = random();
      const evidence = 0.35 + random() * 0.65, family = index % 3;
      return {index, dispersion, drawdown, disagreement, evidence, family,
        x: dispersion * 2 - 1, y: drawdown * 2 - 1, z: disagreement * 2 - 1};
    });
    const positions = new Float32Array(source.length * 3), colors = new Float32Array(source.length * 3), color = new THREE.Color();
    source.forEach((point, i) => {
      positions.set([point.x * 2.7, point.y * 2.0, point.z * 2.2], i * 3);
      color.copy(point.family === 0 ? TEAL : point.family === 1 ? RED : CYAN);
      colors.set([color.r, color.g, color.b], i * 3);
    });
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    const points = new THREE.Points(geometry, new THREE.PointsMaterial({size:.09,vertexColors:true,transparent:true,opacity:.9,blending:THREE.AdditiveBlending,depthWrite:false}));
    root.add(points);
    root.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(5.7,4.2,4.6)),new THREE.LineBasicMaterial({color:0x3daed3,transparent:true,opacity:.2})));
    const marker = new THREE.Mesh(new THREE.SphereGeometry(.16, 16, 12), new THREE.MeshBasicMaterial({color:WHITE,wireframe:true,transparent:true,opacity:.95}));
    points.add(marker);
    let selected = 0, paused = false;
    const syncMarker = () => {
      const point = source[selected]; marker.position.set(point.x*2.7, point.y*2.0, point.z*2.2); marker.scale.setScalar(1.35 + point.evidence * .35); window.__tcResearchWebGL.data.strategyUniverse = {count: source.length, selected, paused}; invalidate();
    };
    syncMarker();
    document.querySelector('#universe-pause')?.addEventListener('click',()=>{paused=!paused;invalidate()});
    document.querySelector('#candidate-prev')?.addEventListener('click',()=>{selected=(selected+source.length-1)%source.length;syncMarker()});
    document.querySelector('#candidate-next')?.addEventListener('click',()=>{selected=(selected+1)%source.length;syncMarker()});
    document.querySelector('#universe-reset')?.addEventListener('click',()=>{selected=0;view.yaw=0;view.pitch=0;points.rotation.y=0;syncMarker()});
    return {animate:(now,dt)=>{if(!paused)points.rotation.y+=dt*.055},annotate:(ctx,w,h)=>{annotationText(ctx,'X ? dispersion',12,h-15,'rgba(61,174,211,.85)');annotationText(ctx,'Y ? drawdown severity',12,16,'rgba(229,74,90,.82)');annotationText(ctx,'Z ? IS/OOS disagreement',w-12,16,'rgba(61,174,211,.82)','right')}};
  }

  function buildMonteCarlo({root, invalidate}) {
    addFloor(root,8,16);
    const group = new THREE.Group(); root.add(group); let seed = 1442953;
    const buildPaths = (currentSeed) => {
      const random = mulberry32(currentSeed), paths = [];
      for (let p=0;p<64;p++) {
        let value=0; const path=[value];
        for (let step=1;step<90;step++) { value += gaussian(random) * .12; path.push(value); }
        paths.push(path);
      }
      return paths;
    };
    const rebuild = () => {
      for (const child of [...group.children]) disposeObject(child);
      const paths = buildPaths(seed), terminals = paths.map((path)=>path[path.length-1]);
      const allValues = paths.flat(), min = Math.min(...allValues), max = Math.max(...allValues), range = Math.max(.0001,max-min);
      paths.forEach((path,p) => {
        const z = (p/(paths.length-1)-.5)*4.2;
        const points = path.map((value,step)=>new THREE.Vector3(-3.15+(step/(path.length-1))*6.3, ((value-min)/range-.5)*3.0, z));
        group.add(line(points, signedColor(path[path.length-1], .1), p%8===0?.62:.28));
      });
      window.__tcResearchWebGL.data.monteCarlo = {seed,p10:percentile(terminals,.10),p50:percentile(terminals,.50),p90:percentile(terminals,.90)};
      invalidate();
    };
    rebuild();
    document.querySelector('#mc-regenerate')?.addEventListener('click',()=>{seed+=97;rebuild()});
    return {annotate:(ctx,w,h)=>{annotationText(ctx,'normalized cumulative outcome',12,16);annotationText(ctx,'synthetic path step ?',w-12,h-15,'rgba(164,171,179,.78)','right')}};
  }

  function robustnessValue(mode,u,v){const x=u-.5,y=v-.5;if(mode==='spike'){const d=(u-.58)**2+(v-.44)**2;return .12+.82*Math.exp(-62*d)}if(mode==='ridge'){const d=v-(.28+.42*u);return .15+.67*Math.exp(-32*d*d)*(.88+.08*Math.cos(u*Math.PI*4))}return .28+.52*Math.exp(-3.8*(x*x+y*y))+.035*Math.cos(u*Math.PI*4)*Math.cos(v*Math.PI*4)}
  function buildRobustness({root,invalidate}) {
    addFloor(root,7,14); let mesh=null,wire=null;
    const rebuild=()=>{if(mesh)disposeObject(mesh);if(wire)disposeObject(wire);const mode=document.querySelector('[data-surface-mode][aria-pressed="true"]')?.dataset.surfaceMode||'plateau';const g=new THREE.PlaneGeometry(5.7,4.4,34,26);g.rotateX(-Math.PI/2);const pos=g.attributes.position,cols=[];const c=new THREE.Color();for(let i=0;i<pos.count;i++){const u=pos.getX(i)/5.7+.5,v=pos.getZ(i)/4.4+.5,val=Math.max(0,Math.min(1,robustnessValue(mode,u,v)));pos.setY(i,val*2.25-1.2);c.copy(val>.67?TEAL:val<.48?RED:CYAN);cols.push(c.r,c.g,c.b)}g.setAttribute('color',new THREE.Float32BufferAttribute(cols,3));g.computeVertexNormals();mesh=new THREE.Mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,roughness:.36,metalness:.08,emissive:0x062630,emissiveIntensity:.85,side:THREE.DoubleSide,transparent:true,opacity:.94}));root.add(mesh);const edges=new THREE.WireframeGeometry(g);wire=new THREE.LineSegments(edges,new THREE.LineBasicMaterial({color:0x3daed3,transparent:true,opacity:.11}));root.add(wire);invalidate()};
    rebuild(); document.querySelectorAll('[data-surface-mode]').forEach(b=>b.addEventListener('click',()=>setTimeout(rebuild,0))); return {annotate:(ctx,w,h)=>{annotationText(ctx,'parameter A',12,h-15);annotationText(ctx,'parameter B',w-12,h-15,'rgba(61,174,211,.78)','right');annotationText(ctx,'response ?',12,16,'rgba(60,250,210,.82)')}};
  }

  function buildCorrelation({root,camera,invalidate}) {
    addFloor(root,7,14);
    const source=[];
    for(let family=0;family<3;family++) for(let member=0;member<6;member++) source.push({family,member,label:`${String.fromCharCode(65+family)}${member+1}`});
    const pairNoise=(i,j)=>{const lo=Math.min(i,j)+1,hi=Math.max(i,j)+1,raw=Math.sin(lo*12.9898+hi*78.233)*43758.5453;return raw-Math.floor(raw)};
    const relation=(i,j)=>{if(i===j)return 1;const same=source[i].family===source[j].family,noise=pairNoise(i,j);if((i===5&&j===6)||(i===6&&j===5))return .74;return same?.64+noise*.31:-.28+noise*.68};
    const positions=source.map((node,index)=>{const angle=(node.member/6)*Math.PI*2+node.family*.33,r=1.2+node.family*.55;return new THREE.Vector3(Math.cos(angle)*r,(node.family-1)*.72+Math.sin(angle*2)*.25,Math.sin(angle)*r)});
    const nodes=positions.map((position,index)=>{const node=source[index],color=[TEAL,RED,CYAN][node.family],mesh=new THREE.Mesh(new THREE.SphereGeometry(.14+(node.member%3)*.02,14,10),new THREE.MeshStandardMaterial({color,emissive:color,emissiveIntensity:1.15,roughness:.3}));mesh.position.copy(position);root.add(mesh);return mesh});
    const edges=[];
    for(let i=0;i<source.length;i++) for(let j=i+1;j<source.length;j++){const value=relation(i,j);if(Math.abs(value)<.62)continue;const edge=line([positions[i],positions[j]],value>=0?TEAL:RED,.34+Math.abs(value)*.35);edge.userData={i,j};edges.push(edge);root.add(edge)}
    const marker=new THREE.Mesh(new THREE.SphereGeometry(.24,16,12),new THREE.MeshBasicMaterial({color:WHITE,wireframe:true,transparent:true,opacity:.9}));root.add(marker);
    let selected=0,focus=false;
    const sync=()=>{nodes.forEach((node,index)=>node.scale.setScalar(index===selected?1.5:1));marker.position.copy(positions[selected]);edges.forEach((edge)=>{edge.visible=!focus||edge.userData.i===selected||edge.userData.j===selected});window.__tcResearchWebGL.data.correlation={selected,focus};invalidate()};
    sync();
    document.querySelector('#network-prev')?.addEventListener('click',()=>{selected=(selected+source.length-1)%source.length;sync()});
    document.querySelector('#network-next')?.addEventListener('click',()=>{selected=(selected+1)%source.length;sync()});
    document.querySelector('#network-focus')?.addEventListener('click',()=>{focus=!focus;sync()});
    return {annotate:(ctx,w,h)=>{source.forEach((node,index)=>{const pos=projectPoint(positions[index],camera,root,w,h);if(pos.visible)annotationText(ctx,node.label,pos.x+5,pos.y-7,index===selected?'rgba(246,248,250,.98)':'rgba(164,171,179,.72)')})}};
  }

  function buildDistribution({root,camera,invalidate}) {
    addFloor(root,8,16);
    const bins=34;
    const bars=new THREE.InstancedMesh(new THREE.BoxGeometry(.16,1,.6),new THREE.MeshBasicMaterial({color:0xffffff,transparent:true,opacity:.92}),bins);
    root.add(bars);
    const matrix=new THREE.Matrix4(), quaternion=new THREE.Quaternion(), color=new THREE.Color();
    const gaussian=(random)=>{const u=Math.max(Number.EPSILON,random()),v=Math.max(Number.EPSILON,random());return Math.sqrt(-2*Math.log(u))*Math.cos(Math.PI*2*v)};
    const standardized=(values)=>{const mean=values.reduce((sum,value)=>sum+value,0)/values.length;const variance=values.reduce((sum,value)=>sum+(value-mean)**2,0)/values.length;const scale=Math.sqrt(variance)||1;return values.map((value)=>(value-mean)/scale)};
    const makeValues=(mode)=>{const random=mulberry32(mode==='symmetric'?5041:mode==='skewed'?9107:17713),values=[];for(let i=0;i<4000;i++){const z=gaussian(random);if(mode==='skewed'){const w=gaussian(random);values.push(.68*z+.33*(w*w-1))}else if(mode==='heavy'){values.push(z*(random()<.075?3.2:1))}else values.push(z)}return standardized(values)};
    const rebuild=()=>{
      const mode=document.querySelector('[data-distribution-mode][aria-pressed="true"]')?.dataset.distributionMode||'symmetric',counts=new Array(bins).fill(0);
      for(const value of makeValues(mode)){const index=Math.max(0,Math.min(bins-1,Math.floor((value+3.5)/7*bins)));counts[index]++}
      const max=Math.max(...counts,1),threshold=Number(document.querySelector('#distribution-threshold')?.value??-1);
      for(let i=0;i<bins;i++){const x=-3.1+i*(6.2/(bins-1)),h=.08+counts[i]/max*2.8,center=-3.5+(i+.5)/bins*7;matrix.compose(new THREE.Vector3(x,-1.55+h/2,0),quaternion,new THREE.Vector3(1,h,1));bars.setMatrixAt(i,matrix);color.copy(center<=threshold?RED:center>.5?TEAL:CYAN);bars.setColorAt(i,color)}
      bars.instanceMatrix.needsUpdate=true;if(bars.instanceColor)bars.instanceColor.needsUpdate=true;invalidate();
    };
    rebuild();document.querySelector('#distribution-threshold')?.addEventListener('input',rebuild);document.querySelectorAll('[data-distribution-mode]').forEach((button)=>button.addEventListener('click',()=>setTimeout(rebuild,0)));return {annotate:(ctx,w,h)=>{const threshold=Number(document.querySelector('#distribution-threshold')?.value??-1),x=((threshold+3.5)/7)*6.2-3.1,a=projectPoint(new THREE.Vector3(x,-1.55,0),camera,root,w,h),b=projectPoint(new THREE.Vector3(x,1.45,0),camera,root,w,h);ctx.save();ctx.setLineDash([4,4]);ctx.strokeStyle='rgba(229,74,90,.85)';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();ctx.restore();annotationText(ctx,`threshold ${threshold.toFixed(1)}`,Math.min(w-8,Math.max(8,b.x+5)),Math.max(15,b.y-8),'rgba(229,74,90,.9)');annotationText(ctx,'standardized synthetic outcome ?',w-12,h-15,'rgba(164,171,179,.72)','right')}};
  }

  function buildRegime({root,view,invalidate}) {
    root.add(new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(5.3,4.2,4.2)),new THREE.LineBasicMaterial({color:0x3daed3,transparent:true,opacity:.3})));
    const random=mulberry32(90517),source=Array.from({length:96},(_,index)=>{const direction=random()*2-1,volatility=random(),stress=random();return {index,direction,volatility,stress}});
    const geometry=new THREE.BufferGeometry(),points=new THREE.Points(geometry,new THREE.PointsMaterial({size:.095,vertexColors:true,transparent:true,opacity:.92,blending:THREE.AdditiveBlending,depthWrite:false}));root.add(points);
    const marker=new THREE.Mesh(new THREE.SphereGeometry(.16,16,12),new THREE.MeshBasicMaterial({color:WHITE,wireframe:true,transparent:true,opacity:.95}));root.add(marker);
    let selected=0,visibleSource=source;
    const updateGeometry=()=>{
      const filter=document.querySelector('[data-regime-filter][aria-pressed="true"]')?.dataset.regimeFilter||'all';
      visibleSource=source.filter((point)=>filter==='low'?point.stress<.5:filter==='high'?point.stress>=.5:true);
      if(!visibleSource.some((point)=>point.index===selected)&&visibleSource.length)selected=visibleSource[0].index;
      const positions=new Float32Array(visibleSource.length*3),colors=new Float32Array(visibleSource.length*3),color=new THREE.Color();
      visibleSource.forEach((point,i)=>{positions.set([point.direction*2.45,point.volatility*3.6-1.8,point.stress*3.7-1.85],i*3);color.copy(point.direction>.25?TEAL:point.direction<-.25?RED:CYAN);colors.set([color.r,color.g,color.b],i*3)});
      geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));geometry.computeBoundingSphere();
      const current=source[selected];marker.position.set(current.direction*2.45,current.volatility*3.6-1.8,current.stress*3.7-1.85);marker.visible=visibleSource.some((point)=>point.index===selected);
      window.__tcResearchWebGL.data.regime={filter,count:visibleSource.length,selected};invalidate();
    };
    const select=(step)=>{if(!visibleSource.length)return;const index=visibleSource.findIndex((point)=>point.index===selected),next=index<0?0:(index+step+visibleSource.length)%visibleSource.length;selected=visibleSource[next].index;updateGeometry()};
    updateGeometry();
    document.querySelector('#regime-rotate-left')?.addEventListener('click',()=>{view.yaw-=.28;invalidate()});
    document.querySelector('#regime-rotate-right')?.addEventListener('click',()=>{view.yaw+=.28;invalidate()});
    document.querySelector('#regime-prev')?.addEventListener('click',()=>select(-1));
    document.querySelector('#regime-next')?.addEventListener('click',()=>select(1));
    document.querySelectorAll('[data-regime-filter]').forEach((button)=>button.addEventListener('click',()=>setTimeout(updateGeometry,0)));
    return {annotate:(ctx,w,h)=>{annotationText(ctx,'X ? direction',12,h-15);annotationText(ctx,'Y ? volatility',12,16,'rgba(60,250,210,.78)');annotationText(ctx,'Z ? liquidity stress',w-12,16,'rgba(229,74,90,.78)','right')}};
  }

  function buildWalkForward({root,invalidate}) {
    addFloor(root,9,18);const group=new THREE.Group();root.add(group);const mapX=(time)=>-3.35+(time/100)*6.7;let selected=3;
    const rebuild=()=>{
      for(const child of [...group.children])disposeObject(child);
      const anchored=document.querySelector('[data-wf-mode][aria-pressed="true"]')?.dataset.wfMode==='anchored';
      for(let i=0;i<7;i++){
        const z=(i-3)*.54,trainStart=anchored?0:i*8,trainEnd=42+i*8,evalEnd=trainEnd+10,x0=mapX(trainStart),x1=mapX(trainEnd),x2=mapX(evalEnd),y=-.65+i*.08,active=i===selected;
        const train=new THREE.Mesh(new THREE.BoxGeometry(Math.max(.08,x1-x0),active?.44:.32,.38),new THREE.MeshStandardMaterial({color:CYAN,emissive:active?0x1b6675:0x123d49,emissiveIntensity:active?1.5:1,roughness:.35}));train.position.set((x0+x1)/2,y,z);group.add(train);
        const test=new THREE.Mesh(new THREE.BoxGeometry(Math.max(.08,x2-x1),active?.58:.46,.38),new THREE.MeshStandardMaterial({color:TEAL,emissive:active?0x237a68:0x164d43,emissiveIntensity:active?1.6:1,roughness:.3}));test.position.set((x1+x2)/2,y+.07,z);group.add(test);
      }
      window.__tcResearchWebGL.data.walkForward={anchored,selected,trainStart:anchored?0:selected*8,trainEnd:42+selected*8};invalidate();
    };
    rebuild();
    document.querySelectorAll('[data-wf-mode]').forEach((button)=>button.addEventListener('click',()=>setTimeout(rebuild,0)));
    document.querySelector('#wf-prev')?.addEventListener('click',()=>{selected=(selected+6)%7;rebuild()});
    document.querySelector('#wf-next')?.addEventListener('click',()=>{selected=(selected+1)%7;rebuild()});
    return {annotate:(ctx,w,h)=>{annotationText(ctx,'synthetic time ?',w-12,h-15,'rgba(164,171,179,.75)','right');annotationText(ctx,`selected fold F${selected+1}`,12,16,'rgba(60,250,210,.85)')}};
  }

  function buildOos({root,invalidate}) {
    addFloor(root,8,16);const group=new THREE.Group();root.add(group);
    const rebuild=()=>{
      for(const child of [...group.children])disposeObject(child);
      const repeated=document.querySelector('[data-oos-mode][aria-pressed="true"]')?.dataset.oosMode==='peek';
      const boundaryX=.65;
      const boundary=new THREE.Mesh(new THREE.PlaneGeometry(3.8,3.8),new THREE.MeshBasicMaterial({color:repeated?RED:CYAN,transparent:true,opacity:.08,side:THREE.DoubleSide,depthWrite:false}));boundary.rotation.y=Math.PI/2;boundary.position.x=boundaryX;group.add(boundary);
      const edge=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(3.8,3.8)),new THREE.LineBasicMaterial({color:repeated?RED:CYAN,transparent:true,opacity:.55}));edge.rotation.y=Math.PI/2;edge.position.x=boundaryX;group.add(edge);
      const random=mulberry32(44021),select=new THREE.Vector3(-.35,0,0),selectedIndex=11;
      const candidates=Array.from({length:36},(_,index)=>({index,y:-1.55+random()*3.1,z:-1.45+random()*2.9,bend:(random()-.5)*.9}));
      candidates.forEach((candidate)=>{const start=new THREE.Vector3(-3.1,candidate.y,candidate.z),mid=new THREE.Vector3(-1.45,candidate.y+candidate.bend,candidate.z*.45),selected=candidate.index===selectedIndex;group.add(line([start,mid,select],selected?TEAL:BLUE,selected?.92:.15))});
      const selectNode=new THREE.Mesh(new THREE.SphereGeometry(.13,14,10),new THREE.MeshStandardMaterial({color:TEAL,emissive:TEAL,emissiveIntensity:1.6,roughness:.3}));selectNode.position.copy(select);group.add(selectNode);
      const evalPoints=[new THREE.Vector3(1.05,-.35,-.55),new THREE.Vector3(1.75,.45,.25),new THREE.Vector3(2.45,-.55,.65),new THREE.Vector3(3.05,.12,-.15)];
      group.add(line([select,...evalPoints],TEAL,.9));
      evalPoints.forEach((point)=>{const node=new THREE.Mesh(new THREE.SphereGeometry(.08,10,8),new THREE.MeshBasicMaterial({color:TEAL}));node.position.copy(point);group.add(node)});
      if(repeated) evalPoints.forEach((point,index)=>group.add(line([point,new THREE.Vector3(-.25,(index-1.5)*.32,.2*(index-1.5))],RED,.72)));
      window.__tcResearchWebGL.data.oos={mode:repeated?'peek':'clean',candidates:36,selectedIndex,feedback:repeated?4:0};invalidate();
    };
    rebuild();document.querySelectorAll('[data-oos-mode]').forEach((button)=>button.addEventListener('click',()=>setTimeout(rebuild,0)));return {annotate:(ctx,w,h)=>{annotationText(ctx,'DEVELOP + SELECT',12,16,'rgba(61,174,211,.8)');annotationText(ctx,'HELD-OUT EVALUATION',w-12,16,'rgba(60,250,210,.8)','right');annotationText(ctx,'information boundary',w*.58,h-15,document.querySelector('[data-oos-mode][aria-pressed="true"]')?.dataset.oosMode==='peek'?'rgba(229,74,90,.85)':'rgba(61,174,211,.85)','center')}};
  }

  function buildDrawdown({root,invalidate}) {
    addFloor(root,8,16);const group=new THREE.Group();root.add(group);
    const buildPath=(mode)=>Array.from({length:120},(_,index)=>{const trend=100+index*.18,wave=1.8*Math.sin(index/7.5)+.9*Math.sin(index/3.9);let valley=0;if(mode==='long')valley=17*Math.exp(-Math.pow((index-64)/27,2));else if(mode==='repeat')valley=13*Math.exp(-Math.pow((index-31)/8,2))+16*Math.exp(-Math.pow((index-69)/10,2))+12*Math.exp(-Math.pow((index-101)/8,2));else valley=30*Math.exp(-Math.pow((index-61)/11,2));return trend+wave-valley});
    const rebuild=()=>{
      for(const child of [...group.children])disposeObject(child);
      const mode=document.querySelector('[data-drawdown-mode][aria-pressed="true"]')?.dataset.drawdownMode||'deep',values=buildPath(mode),peaks=[];let peak=values[0];values.forEach((value)=>{peak=Math.max(peak,value);peaks.push(peak)});
      const min=Math.min(...values)-2,max=Math.max(...peaks)+2,scale=(value)=>(value-min)/(max-min)*3.1-1.55,path=[],peakPath=[],drops=[];
      values.forEach((value,index)=>{const x=-3.25+(index/(values.length-1))*6.5,z=Math.sin(index*.1)*.08,y=scale(value),py=scale(peaks[index]);path.push(new THREE.Vector3(x,y,z));peakPath.push(new THREE.Vector3(x,py,z));if(peaks[index]-value>.4)drops.push(new THREE.Vector3(x,y,z),new THREE.Vector3(x,py,z))});
      const ribbon=[];for(let i=0;i<path.length-1;i++)ribbon.push(path[i],path[i+1],peakPath[i+1],path[i],peakPath[i+1],peakPath[i]);
      group.add(new THREE.Mesh(new THREE.BufferGeometry().setFromPoints(ribbon),new THREE.MeshBasicMaterial({color:RED,transparent:true,opacity:.28,side:THREE.DoubleSide,depthWrite:false})));
      group.add(line(peakPath,TEAL,.72));group.add(line(path,WHITE,.92));const dropLines=segments(drops,null,.52);dropLines.material.color.copy(RED);group.add(dropLines);
      const drawdowns=values.map((value,index)=>Math.max(0,(peaks[index]-value)/peaks[index]));window.__tcResearchWebGL.data.drawdown={mode,maxDrawdown:Math.max(...drawdowns),steps:values.length};invalidate();
    };
    rebuild();document.querySelectorAll('[data-drawdown-mode]').forEach((button)=>button.addEventListener('click',()=>setTimeout(rebuild,0)));return {annotate:(ctx,w,h)=>{annotationText(ctx,'running peak',12,16,'rgba(60,250,210,.82)');annotationText(ctx,'red field ? drawdown depth',w-12,16,'rgba(229,74,90,.85)','right');annotationText(ctx,'synthetic path step ?',w-12,h-15,'rgba(164,171,179,.72)','right')}};
  }

  function buildSelection({root,invalidate}) {
    addFloor(root,8,16);const group=new THREE.Group();root.add(group);
    const rebuild=()=>{
      for(const child of [...group.children])disposeObject(child);
      const exponent=Number(document.querySelector('#selection-family')?.value||6),familySize=2**exponent,random=mulberry32(91001+familySize*17);
      const scores=Array.from({length:familySize},(_,id)=>({id,score:gaussian(random)})).sort((a,b)=>b.score-a.score),stageCounts=[familySize,Math.max(1,Math.ceil(familySize*.25)),Math.max(1,Math.ceil(familySize*.05)),1];
      const min=-3.3,max=Math.max(4.2,scores[0].score+.35),mapY=(score)=>(score-min)/(max-min)*3.5-1.65;
      stageCounts.forEach((count,stage)=>{
        const z=-2.25+stage*1.5,retained=scores.slice(0,count),displayCount=Math.min(retained.length,stage===0?(mobile?100:150):stage===1?110:stage===2?70:1),jitter=mulberry32(familySize*97+stage*1301);
        const positions=[],colors=[],color=new THREE.Color();
        for(let i=0;i<displayCount;i++){const sourceIndex=displayCount===1?0:Math.floor(i*(retained.length-1)/Math.max(1,displayCount-1)),score=retained[sourceIndex].score;positions.push((jitter()-.5)*1.0,mapY(score),z+(jitter()-.5)*.32);color.copy(stage===3?RED:stage>=2?TEAL:CYAN);colors.push(color.r,color.g,color.b)}
        const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.setAttribute('color',new THREE.Float32BufferAttribute(colors,3));group.add(new THREE.Points(geometry,new THREE.PointsMaterial({size:stage===3?.16:.075,vertexColors:true,transparent:true,opacity:.92,blending:THREE.AdditiveBlending,depthWrite:false})));
        const ring=new THREE.Mesh(new THREE.TorusGeometry(.72,.018,6,56),new THREE.MeshBasicMaterial({color:stage===3?RED:CYAN,transparent:true,opacity:.38+stage*.1}));ring.rotation.x=Math.PI/2;ring.position.set(0,-1.72,z);group.add(ring);
      });
      window.__tcResearchWebGL.data.selection={familySize,observed:scores[0].score,stageCounts};invalidate();
    };
    rebuild();document.querySelector('#selection-family')?.addEventListener('input',rebuild);return {annotate:(ctx,w,h)=>{['family','top 25%','top 5%','selected max'].forEach((label,index)=>annotationText(ctx,label,12+index*(w-24)/3,h-15,index===3?'rgba(229,74,90,.86)':'rgba(61,174,211,.75)',index===3?'right':index===0?'left':'center'))}};
  }

  setupSurface('strategy-universe-canvas', buildStrategyUniverse, [0, 1.4, 8.4]);
  setupSurface('monte-carlo-canvas', buildMonteCarlo, [0, 2.4, 7.5]);
  setupSurface('robustness-canvas', buildRobustness, [0, 3.7, 7.0]);
  setupSurface('correlation-canvas', buildCorrelation, [0, 2.2, 7.0]);
  setupSurface('distribution-canvas', buildDistribution, [0, 2.7, 7.8]);
  setupSurface('regime-canvas', buildRegime, [0, 2.0, 7.6]);
  setupSurface('walk-forward-canvas', buildWalkForward, [0, 2.7, 8.4]);
  setupSurface('oos-canvas', buildOos, [0, 2.2, 8.0]);
  setupSurface('drawdown-canvas', buildDrawdown, [0, 2.2, 8.0]);
  setupSurface('selection-canvas', buildSelection, [0, 2.8, 8.0]);

  document.documentElement.dataset.researchRenderer = registry.size === SURFACE_IDS.length ? 'three-webgl' : 'hybrid-fallback';
})();
