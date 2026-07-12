// mg-core.js — reusable motion-graphics primitives (unasked animation-benefit build).
// Every Hyperframes/Three.js composition imports from here so each piece STARTS from accumulated craft
// (easing, palette, PRNG, glow sprite, camera rigs, curl flow) instead of re-coding it. Pure ES module,
// browser-side, served by html3d-render.cjs — the shared shader/helper library for the compositions.

// ---- deterministic RNG (seeded → identical frames run-to-run) ----
export function mulberry32(a) {
  return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}

// ---- math + easing (custom curves — never linear/default-spring) ----
export const TAU = Math.PI * 2;
export const clamp01 = x => Math.max(0, Math.min(1, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const mix3 = (c1, c2, t) => [c1[0] + (c2[0] - c1[0]) * t, c1[1] + (c2[1] - c1[1]) * t, c1[2] + (c2[2] - c1[2]) * t];
export const smoothstep = (e0, e1, x) => { const t = clamp01((x - e0) / (e1 - e0)); return t * t * (3 - 2 * t); };
export const easeOut = x => 1 - Math.pow(1 - x, 3);                 // easeOutCubic
export const easeOutExpo = x => x >= 1 ? 1 : 1 - Math.pow(2, -10 * x);
export const easeInOut = x => x < 0.5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2; // easeInOutQuad
export const easeInOutQuint = x => x < 0.5 ? 16 * x * x * x * x * x : 1 - Math.pow(-2 * x + 2, 5) / 2;
export const backOut = (x, s = 1.70158) => { const c = x - 1; return 1 + (s + 1) * c * c * c + s * c * c; }; // overshoot
// — full easing family + stagger/loop helpers (harvested into mg-core, animation-mastery-playbook §1/§7).
export const easeOutQuint = t => 1 - Math.pow(1 - t, 5);
export const easeOutQuart = t => 1 - Math.pow(1 - t, 4);
export const easeInExpo = t => t <= 0 ? 0 : Math.pow(2, 10 * t - 10);                                   // EXITS — never ease-out an exit
export const easeInOutExpo = t => t === 0 ? 0 : t === 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2; // A→B travel
export const easeInOutSine = t => -(Math.cos(Math.PI * t) - 1) / 2;                                      // loop/breathe
const _C4 = (2 * Math.PI) / 3;
export const easeOutElastic = t => t === 0 ? 0 : t === 1 ? 1 : Math.pow(2, -10 * t) * Math.sin((t * 10 - 0.75) * _C4) + 1;
export const staggerP = (frame, i, dur, stride = 2) => clamp01((frame - i * stride) / dur);              // per-child cascade progress
// seamless-loop phase: drive ANY continuous drift off cx/sx so frame 0 ≡ frame N at constant speed (sine-alone has a zero-velocity turnaround)
export function loopPhase(frame, durationInFrames) { const t = (frame % durationInFrames) / durationInFrames; return { t, cx: Math.cos(TAU * t), sx: Math.sin(TAU * t) }; }

// ---- palette (restrained: deep ink base + violet/cyan accents) ----
export const PAL = { ink: 0x05060d, violet: [0.46, 0.30, 1.0], cyan: [0.16, 0.88, 0.97], pink: [0.95, 0.36, 0.85], white: [0.95, 0.97, 1.0] };

// ---- soft circular sprite for glowing additive points (premium glow, not hard dots) ----
export function softDot(THREE, falloff = 'tight') {
  const s = 64, c = document.createElement('canvas'); c.width = c.height = s;
  const g = c.getContext('2d');
  const gr = g.createRadialGradient(s / 2, s / 2, 0, s / 2, s / 2, s / 2);
  if (falloff === 'wide') { gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.25, 'rgba(255,255,255,0.85)'); gr.addColorStop(0.55, 'rgba(255,255,255,0.25)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); }
  else { gr.addColorStop(0, 'rgba(255,255,255,1)'); gr.addColorStop(0.3, 'rgba(255,255,255,0.7)'); gr.addColorStop(0.6, 'rgba(255,255,255,0.18)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); }
  g.fillStyle = gr; g.fillRect(0, 0, s, s);
  const tx = new THREE.CanvasTexture(c); tx.needsUpdate = true; return tx;
}

// ---- camera rig: eased orbit + dolly + bob, always looking at origin (the workhorse 3D move) ----
// o = { t, p, ang0, angSpan, rad0, radPull, height, bob, bobSpeed }
export function orbitCamera(camera, o) {
  const orbit = easeInOut(o.p);
  const ang = (o.ang0 || 0) + orbit * (o.angSpan || 0);
  const radius = (o.rad0 || 6) - easeOut(o.p) * (o.radPull || 0);
  camera.position.set(Math.sin(ang) * radius, (o.height || 0) + Math.sin(o.t * (o.bobSpeed ?? 0.3)) * (o.bob || 0), Math.cos(ang) * radius);
  camera.lookAt(o.lookY ? 0 : 0, o.lookY || 0, 0);
}

// ---- fresnel-rim material (glowing-edge crystal/glass look; flat normals → gem facets) ----
// o = { rimA, rimB, core, power, intensity } — rimA=face color, rimB=hot silhouette edge.
export function fresnelMaterial(THREE, o = {}) {
  const rimA = o.rimA || PAL.violet, rimB = o.rimB || PAL.cyan, core = o.core || [0.02, 0.02, 0.07];
  return new THREE.ShaderMaterial({
    uniforms: {
      rimA: { value: new THREE.Color().fromArray(rimA) }, rimB: { value: new THREE.Color().fromArray(rimB) },
      core: { value: new THREE.Color().fromArray(core) }, power: { value: o.power ?? 2.5 }, intensity: { value: o.intensity ?? 1.8 },
    },
    vertexShader: `varying vec3 vN; varying vec3 vV;
      void main(){ vec4 mv = modelViewMatrix * vec4(position,1.0); vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }`,
    fragmentShader: `varying vec3 vN; varying vec3 vV; uniform vec3 rimA; uniform vec3 rimB; uniform vec3 core; uniform float power; uniform float intensity;
      void main(){ float f = pow(1.0 - max(dot(normalize(vN), normalize(vV)), 0.0), power);
        vec3 col = mix(core, mix(rimA, rimB, f), f); col += rimA * 0.16; col += rimB * pow(f, 4.0) * 0.7;
        gl_FragColor = vec4(col * intensity, 1.0); }`,
  });
}

// ---- analytic curl-ish swirl (deterministic organic displacement; returns [dx,dy,dz]) ----
export function curlSwirl(x, y, z, t, amp = 0.1) {
  return [
    Math.sin(y * 1.3 + t * 0.9) * amp + Math.sin(z * 0.7 - t * 0.5) * amp * 0.6,
    Math.cos(x * 1.1 - t * 0.7) * amp + Math.cos(z * 0.9 + t * 0.4) * amp * 0.6,
    Math.sin(x * 0.8 + t) * amp + Math.cos(y * 1.2 - t * 0.6) * amp * 0.6,
  ];
}

// REAL divergence-free CURL NOISE for premium particle advection — the
// curl of a 3-channel value-noise potential via finite differences. Unlike curlSwirl (a sine approximation that clumps),
// curl noise never collapses → smoke/ink/energy flow that defines pro abstract particle MG. Returns a flow vector [dx,dy,dz].
function _h3(x, y, z) { const s = Math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453; return s - Math.floor(s); }
function _vnoise(x, y, z) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z), xf = x - xi, yf = y - yi, zf = z - zi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf), w = zf * zf * (3 - 2 * zf), L = (a, b, t) => a + (b - a) * t;
  return (L(L(L(_h3(xi, yi, zi), _h3(xi + 1, yi, zi), u), L(_h3(xi, yi + 1, zi), _h3(xi + 1, yi + 1, zi), u), v),
    L(L(_h3(xi, yi, zi + 1), _h3(xi + 1, yi, zi + 1), u), L(_h3(xi, yi + 1, zi + 1), _h3(xi + 1, yi + 1, zi + 1), u), v), w)) * 2 - 1;
}
export function curlNoise(x, y, z, eps = 0.1) {
  const n1 = (a, b, c) => _vnoise(a, b, c), n2 = (a, b, c) => _vnoise(a + 31.4, b + 17.2, c + 9.1), n3 = (a, b, c) => _vnoise(a - 12.3, b + 5.6, c - 7.8);
  const k = 1 / (2 * eps);
  const dz_dy = (n3(x, y + eps, z) - n3(x, y - eps, z)) * k, dy_dz = (n2(x, y, z + eps) - n2(x, y, z - eps)) * k;
  const dx_dz = (n1(x, y, z + eps) - n1(x, y, z - eps)) * k, dz_dx = (n3(x + eps, y, z) - n3(x - eps, y, z)) * k;
  const dy_dx = (n2(x + eps, y, z) - n2(x - eps, y, z)) * k, dx_dy = (n1(x, y + eps, z) - n1(x, y - eps, z)) * k;
  return [dz_dy - dy_dz, dx_dz - dz_dx, dy_dx - dx_dy];
}

// (harvested, playbook §4): domain-warped fbm "aurora" gradient-mesh — a LIVING color field for backdrops (BackSide
// sphere or plane). Kept DIM (uAmp) so it doesn't trip bloom. Update uniforms.uTime each frame. A liquid backdrop > a flat fill.
export function gradientMeshMaterial(THREE, o = {}) {
  const cA = o.cA || [0.03, 0.03, 0.06], cB = o.cB || PAL.violet, cC = o.cC || PAL.cyan;
  return new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 }, cA: { value: new THREE.Color().fromArray(cA) }, cB: { value: new THREE.Color().fromArray(cB) }, cC: { value: new THREE.Color().fromArray(cC) }, uAmp: { value: o.amp ?? 0.34 } },
    side: THREE.BackSide, depthWrite: false, toneMapped: true,
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `varying vec2 vUv; uniform float uTime; uniform vec3 cA, cB, cC; uniform float uAmp;
      float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      float noise(vec2 p){ vec2 i = floor(p), f = fract(p), u = f*f*(3.0-2.0*f); return mix(mix(hash(i), hash(i+vec2(1,0)), u.x), mix(hash(i+vec2(0,1)), hash(i+vec2(1,1)), u.x), u.y); }
      float fbm(vec2 p){ float v=0.0, a=0.5; for(int i=0;i<5;i++){ v += a*noise(p); p*=2.0; a*=0.5; } return v; }
      void main(){ vec2 p = vUv*3.0; float t = uTime*0.05;
        vec2 q = vec2(fbm(p+vec2(0.0,t)), fbm(p+vec2(5.2,1.3)));
        vec2 r = vec2(fbm(p+4.0*q+vec2(1.7,9.2)+t), fbm(p+4.0*q+vec2(8.3,2.8)));
        float f = fbm(p+4.0*r);
        vec3 col = mix(cA, cB, smoothstep(0.1, 0.95, f)); col = mix(col, cC, smoothstep(0.55, 1.0, r.x)*0.7);
        gl_FragColor = vec4(col*uAmp + cA, 1.0); }`,
  });
}

// Anamorphic lens-STREAK — a single-pass HORIZONTAL smear of the thresholded-bright pixels, added back over the scene.
// The signature cinematic flare: where UnrealBloom blooms RADIALLY, a real anamorphic lens throws a sharp horizontal
// LINE through every bright point (the hot fresnel rim, a glowing core). $0, dependency-free; returns a ShaderPass
// descriptor — `composer.addPass(new ShaderPass(anamorphicStreak(THREE, W, H, {tint,strength,threshold,spread})))`.
// Place AFTER UnrealBloom (streak the already-bloomed brights), BEFORE OutputPass. Harvested 2026-06-24 (Bart Wronski
// anamorphic-flares / R3F-Ultimate-Lens-Flare — both extract bright, blur on ONE axis, screen-add). 49 luminance-gated
// taps, gaussian-weighted; threshold keeps it OFF the dim faces so only the crisp edge streaks (no full-frame wash).
export function anamorphicStreak(THREE, W, H, o = {}) {
  return {
    uniforms: {
      tDiffuse: { value: null },
      uTexel: { value: new THREE.Vector2(1 / W, 1 / H) },
      uThreshold: { value: o.threshold ?? 0.62 },   // luminance floor — below it, no streak (keeps faces crisp)
      uStrength: { value: o.strength ?? 2.2 },       // smear intensity (ramp this in __seek for a fade-in)
      uSpread: { value: o.spread ?? 3.0 },           // px between taps → reach ≈ 24*spread each side
      uTint: { value: new THREE.Vector3().fromArray(o.tint || [0.45, 0.85, 1.0]) }, // cyan = the cool anamorphic streak
    },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `precision highp float; varying vec2 vUv; uniform sampler2D tDiffuse; uniform vec2 uTexel;
      uniform float uThreshold, uStrength, uSpread; uniform vec3 uTint;
      void main(){ vec4 base = texture2D(tDiffuse, vUv); vec3 streak = vec3(0.0); float wsum = 0.0;
        for(int i=-24;i<=24;i++){ float fi = float(i); float w = exp(-fi*fi/200.0);
          vec3 s = texture2D(tDiffuse, vUv + vec2(fi*uTexel.x*uSpread, 0.0)).rgb;
          float lum = max(0.0, dot(s, vec3(0.2126, 0.7152, 0.0722)) - uThreshold);
          streak += s * lum * w; wsum += w; }
        streak = streak / wsum * uStrength * uTint;
        gl_FragColor = vec4(base.rgb + streak, base.a); }`,
  };
}

// FILM-GRAIN + VIGNETTE + DITHER — the cinematic FINISHING pass. Three jobs: (1) a subtle VIGNETTE darkens the corners
// (focus the eye), (2) animated FILM GRAIN adds organic texture (kills the "too-clean CGI" tell), (3) TRIANGULAR-PDF
// DITHER (~±1/255) breaks the float→8-bit quantization that BANDS dark violet→black gradients (the #1 amateur tell on
// dark MG). Place it LAST (after OutputPass) so it dithers in sRGB display space on the float buffer just before the
// 8-bit canvas write — exactly where banding lives (harvested 2026-06-24: shader-tutorial.dev banding/dither + "dither in
// sRGB"). Animate uTime in __seek so the grain shimmers. Returns a ShaderPass descriptor:
//   composer.addPass(new ShaderPass(grainVignette(THREE, W, H, {grain, vignette})))
export function grainVignette(THREE, W, H, o = {}) {
  return {
    uniforms: {
      tDiffuse: { value: null },
      uRes: { value: new THREE.Vector2(W, H) },
      uTime: { value: 0 },
      uGrain: { value: o.grain ?? 0.035 },       // grain amplitude (0 = off)
      uVignette: { value: o.vignette ?? 0.42 },  // corner darkening strength
    },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `precision highp float; varying vec2 vUv; uniform sampler2D tDiffuse; uniform vec2 uRes;
      uniform float uTime, uGrain, uVignette;
      float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
      void main(){ vec3 col = texture2D(tDiffuse, vUv).rgb;
        vec2 q = vUv - 0.5; float vig = 1.0 - uVignette * dot(q, q) * 2.2; col *= clamp(vig, 0.0, 1.0);
        col += (hash(vUv * uRes + uTime) - 0.5) * uGrain;                                   // animated film grain
        col += (hash(vUv * uRes + 0.5) + hash(vUv * uRes + 91.7) - 1.0) / 255.0;             // triangular dither (anti-band)
        gl_FragColor = vec4(col, 1.0); }`,
  };
}
