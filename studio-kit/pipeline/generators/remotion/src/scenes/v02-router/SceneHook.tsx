import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #2 — beat: "One model is draining your budget."
 *
 * CONCEPT: a single overpriced PREMIUM MODEL devours every incoming request.
 * A torrent of REQUEST particles rains from the top and funnels into ONE glowing
 * "$$$ PREMIUM" core. Every request that hits it ejects a coin that arcs down into
 * a draining BUDGET tank (liquid fill that visibly empties), while a fast mono COST
 * counter ticks up and spikes RED on "draining"/"budget". Pay too much, bill explodes.
 *
 * 7 choreographed, synchronized layers (staged arrival -> devour -> drain -> resolve):
 *   1. Request-token particle torrent (deterministic particle system, funnels in)
 *   2. Convergence funnel cone (SVG, intake guides + flowing dashes)
 *   3. The PREMIUM MODEL core (pulsing, devouring, impact-scaled, spark ring)
 *   4. Coin/dollar ejecta (physics-ish parabolic arcs, one per consumed request)
 *   5. Draining BUDGET tank (liquid fill technique — wave surface that empties)
 *   6. Rising COST counter (mono, odometer-ish, spikes red on the word)
 *   7. Ambient overpay warning wash + floating "$" embers (alive backdrop)
 *
 * NOVELTY vs video #1 (forbidden): no glass-card-scene, typewriter-stream,
 * confidence-badge-flip, chromatic-glitch, scanline-sweep, source-link-break,
 * node-graph, similarity-ring, relevance-bars, radial-gauge, ranked list reorder,
 * or "AI fabricates an answer" beat. New families used here: deterministic
 * particle-system, convergence funnel, devouring core, physics-ish coin ejecta,
 * liquid-fill draining tank, mono cost-odometer, floating embers.
 *
 * RENDER-SAFE: imports only react + remotion (interpolate/spring). No
 * useCurrentFrame/AbsoluteFill/three. No Math.random/Date.now/new Date. All
 * interpolate() input ranges are strictly increasing (prop-derived ends are
 * guarded). Manual deterministic number formatting (no toLocaleString). Stays
 * inside the 1080x820 stage.
 */
export const SceneHook: React.FC<{
  localFrame: number;
  tS: number;
  fps: number;
  beatDur: number;
  accentA: string;
  accentB: string;
  words: { w: string; startS: number; endS: number }[];
}> = ({ localFrame, tS, fps, beatDur, accentA, accentB, words }) => {
  // ---------------- helpers ----------------
  const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const fract = (x: number) => x - Math.floor(x);
  const rnd = (i: number) => fract(Math.sin(i * 12.9898) * 43758.5453);
  const rnd2 = (i: number) => fract(Math.sin(i * 78.233 + 4.17) * 24634.6345);
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
  const lin = (v: number, inR: number[], outR: number[]) =>
    interpolate(v, inR, outR, { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // deterministic "$12,345" formatter — avoids toLocaleString ICU/locale variance in headless render
  const money = (n: number) => {
    const v = Math.max(0, Math.floor(n));
    const s = String(v);
    let out = '';
    for (let k = 0; k < s.length; k++) {
      if (k > 0 && (s.length - k) % 3 === 0) out += ',';
      out += s[k];
    }
    return '$' + out;
  };

  // strictly-increasing end for any range that runs to the (prop-driven) beat length
  const END = Math.max(60, beatDur); // beatDur is in frames; guarantee end > 10 always

  const wordStart = (sub: string) => {
    const w = words.find((x) => x.w.toLowerCase().includes(sub));
    return w ? w.startS : null;
  };

  // ---------------- palette ----------------
  const gold = accentA;          // request/money accent A
  const violet = accentB;        // premium-model accent B
  const white = '#F5F7FF';
  const red = '#FF3B5C';
  const coinGold = '#FFC542';
  const danger = '#FF5470';

  // ---------------- narration sync ----------------
  // Key narrative escalations land on the spoken words.
  const drainAt = wordStart('draining') ?? wordStart('drain') ?? null;
  const budgetAt = wordStart('budget') ?? null;

  const draining = drainAt != null && tS >= drainAt;
  const budgetHit = budgetAt != null && tS >= budgetAt;
  const sinceDrain = drainAt != null ? tS - drainAt : -1;
  const sinceBudget = budgetAt != null ? tS - budgetAt : -1;

  // ---------------- stage geometry (within 1080 x 820) ----------------
  const CX = 540;
  const coreY = 366;            // premium model core center
  const coreR = 96;            // base core radius
  const tankX = 760;           // budget tank left
  const tankY = 150;           // budget tank top
  const tankW = 196;
  const tankH = 470;

  // ===================================================================
  // LAYER 3 — core devour cadence (drives impacts, ejecta, drain, counter)
  // Each "request" reaches the core on a steady cadence; we model N impacts
  // up to now and use the latest fractional impact for the pulse.
  // ===================================================================
  const coreIn = spring({ frame: localFrame, fps, config: { damping: 14, mass: 0.8 } });
  const coreScaleBase = lerp(0.2, 1, coreIn);

  // impacts/sec accelerates as the model "feeds" (overpaying spirals)
  const feedRate = lin(localFrame, [10, 40, 100], [3, 7, 11]); // impacts per second (range strictly increasing)
  const impactFloat = (Math.max(0, localFrame - 10) / fps) * feedRate;
  const impactCount = Math.floor(impactFloat);
  const impactPhase = fract(impactFloat); // 0->1 since last impact
  // sharp pulse right after each impact
  const impactPulse = Math.exp(-impactPhase * 7);
  const corePulse = 0.5 + 0.5 * Math.sin(localFrame / 9);
  const coreScale =
    coreScaleBase * (1 + 0.12 * impactPulse + 0.04 * corePulse) *
    (draining ? 1 + 0.06 * clamp(lin(sinceDrain, [0, 0.3], [0, 1])) : 1);

  // ===================================================================
  // LAYER 1 — REQUEST TOKEN TORRENT (deterministic particle system)
  // Particles spawn across the top, fall + are pulled toward the core.
  // ===================================================================
  const NUM_REQ = 46;
  type Req = {
    x: number; y: number; o: number; s: number; idx: number; hue: number;
  };
  const reqs: Req[] = [];
  const reqAppear = lin(localFrame, [4, 26], [0, 1]); // stream ramps in
  for (let i = 0; i < NUM_REQ; i++) {
    // each particle has its own loop period & phase so the torrent is continuous
    const period = 34 + rnd(i) * 26;             // frames for a full top->core trip
    const phase = rnd2(i);                       // 0..1 stagger
    const localProg = fract((localFrame / period) + phase); // 0..1 trip progress

    // spawn x spread across the top, biased toward center funnel
    const startX = lerp(120, 960, rnd(i * 3 + 1));
    const startY = -30 - rnd(i * 5 + 2) * 60;

    // ease the pull toward the core as it descends (funnel convergence)
    const pull = Math.pow(localProg, 1.7);
    const px = lerp(startX, CX + (rnd(i * 7) - 0.5) * 26, pull);
    const py = lerp(startY, coreY - coreR * 0.55, localProg);

    // visibility: fade in near top, fade out as it's devoured at the core
    const fadeIn = clamp(localProg / 0.08);
    const fadeOut = 1 - clamp((localProg - 0.9) / 0.1);
    const o = fadeIn * fadeOut * reqAppear;

    reqs.push({
      x: px,
      y: py,
      o,
      s: lerp(11, 5, localProg), // shrink as it's pulled in
      idx: i,
      hue: rnd(i * 11),
    });
  }

  // ===================================================================
  // LAYER 4 — COIN EJECTA (physics-ish parabolic arcs into the tank)
  // For each recent impact we spawn a coin that arcs from the core down-right
  // into the budget tank. We render the last ~12 coins by impact index.
  // ===================================================================
  const COIN_LIFE = 0.85; // seconds visible
  const coins: {
    x: number; y: number; o: number; rot: number; scale: number;
  }[] = [];
  for (let k = 0; k < 12; k++) {
    const impIdx = impactCount - k;
    if (impIdx < 0) continue;
    const age = (impactFloat - impIdx) / feedRate; // seconds since this coin spawned
    if (age < 0 || age > COIN_LIFE) continue;
    const t = clamp(age / COIN_LIFE); // 0..1 flight
    // launch from core toward tank surface; parabolic arc
    const sx = CX + coreR * 0.5;
    const sy = coreY - coreR * 0.2;
    const ex = tankX + tankW * 0.5;
    const ey = tankY + tankH * 0.18;
    const arcLift = 150 + rnd(impIdx) * 40; // peak height of arc (upward)
    const x = lerp(sx, ex, t);
    const y = lerp(sy, ey, t) - arcLift * Math.sin(Math.PI * t); // up then down
    const o = clamp(lin(t, [0, 0.08, 0.85, 1], [0, 1, 1, 0]));
    coins.push({
      x,
      y,
      o,
      rot: t * 540 + impIdx * 40,
      scale: lerp(1.05, 0.7, t),
    });
  }

  // ===================================================================
  // LAYER 5 — DRAINING BUDGET TANK (liquid fill)
  // Fill level starts high, drains as the model feeds; sharp drop on "draining".
  // ===================================================================
  // base steady drain from feeding (end guarded > start)
  const feedDrain = lin(localFrame, [10, END], [0, 0.42]);
  const drainSpike = draining ? lin(sinceDrain, [0, 0.6], [0, 0.34]) : 0;
  const budgetSpikeDrain = budgetHit ? lin(sinceBudget, [0, 0.5], [0, 0.16]) : 0;
  const fillLevel = clamp(1 - 0.06 - feedDrain - drainSpike - budgetSpikeDrain, 0.04, 0.96);
  // liquid surface y inside the tank
  const innerPad = 8;
  const innerH = tankH - innerPad * 2;
  const innerW = tankW - innerPad * 2;
  const surfaceY = tankY + innerPad + (1 - fillLevel) * innerH;
  // wave on the surface
  const waveAmp = 7 + 5 * impactPulse;
  const waveT = localFrame / 6;
  const buildWavePath = (yOff: number, amp: number, freq: number, phase: number) => {
    const left = tankX + innerPad;
    const right = tankX + innerPad + innerW;
    const top = surfaceY + yOff;
    const bottom = tankY + innerPad + innerH;
    let d = `M ${left} ${top.toFixed(1)}`;
    const steps = 14;
    for (let s = 0; s <= steps; s++) {
      const xx = left + (innerW * s) / steps;
      const yy = top + Math.sin((s / steps) * Math.PI * freq + waveT + phase) * amp;
      d += ` L ${xx.toFixed(1)} ${yy.toFixed(1)}`;
    }
    d += ` L ${right} ${bottom} L ${left} ${bottom} Z`;
    return d;
  };
  const liquidColor = fillLevel < 0.3 ? red : draining ? danger : gold;

  // ===================================================================
  // LAYER 6 — RISING COST COUNTER (mono) — spikes red on "draining"/"budget"
  // ===================================================================
  const baseCost = lin(localFrame, [10, END], [0, 9000]);
  const drainBoost = draining ? lin(sinceDrain, [0, 0.8], [0, 7400]) : 0;
  const budgetBoost = budgetHit ? lin(sinceBudget, [0, 0.6], [0, 5200]) : 0;
  const costVal = Math.floor((baseCost + drainBoost + budgetBoost) / 7) * 7; // jittery climb
  const costStr = money(costVal);
  const costRed = draining || budgetHit;
  const costKick = draining
    ? 1 + 0.14 * Math.exp(-Math.max(0, sinceDrain) * 5)
    : budgetHit
    ? 1 + 0.12 * Math.exp(-Math.max(0, sinceBudget) * 5)
    : 1;

  // label above counter
  const labelOpacity = lin(localFrame, [6, 24], [0, 1]);

  // ===================================================================
  // LAYER 7 — ambient overpay wash + floating "$" embers
  // ===================================================================
  const embers: { x: number; y: number; o: number; s: number }[] = [];
  for (let i = 0; i < 10; i++) {
    const per = 90 + rnd(i + 40) * 70;
    const prog = fract(localFrame / per + rnd2(i + 7));
    const ex = lerp(140, 940, rnd(i + 3));
    const ey = lerp(720, 220, prog);
    const eo = clamp(lin(prog, [0, 0.15, 0.8, 1], [0, 0.5, 0.5, 0])) * 0.6;
    embers.push({ x: ex, y: ey, o: eo, s: 14 + rnd(i) * 12 });
  }

  // danger-wash intensity (clamped 0..1 so opacity stays legal even before drain)
  const washAmt = draining ? clamp(lin(sinceDrain, [0, 0.5], [0, 1])) : 0;

  // overall scene fade-in
  const sceneIn = lin(localFrame, [0, 10], [0, 1]);

  // ---------------- render ----------------
  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* ===== LAYER 7a: overpay ambience (no full opaque paint) ===== */}
      <div
        style={{
          position: 'absolute',
          left: CX - 360,
          top: coreY - 320,
          width: 720,
          height: 640,
          borderRadius: 400,
          background: `radial-gradient(circle at 50% 45%, ${violet}26, transparent 68%)`,
          filter: 'blur(46px)',
          opacity: 0.9,
        }}
      />
      {/* danger wash grows as drain/budget land */}
      {(draining || budgetHit) && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(circle at 82% 30%, rgba(255,59,92,${(0.1 + 0.1 * washAmt).toFixed(3)}), transparent 62%)`,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* ===== LAYER 7b: floating $ embers ===== */}
      {embers.map((e, i) => (
        <span
          key={`em-${i}`}
          style={{
            position: 'absolute',
            left: e.x,
            top: e.y,
            fontFamily: 'Consolas, monospace',
            fontSize: e.s,
            color: coinGold,
            opacity: e.o,
            textShadow: `0 0 10px ${coinGold}88`,
          }}
        >
          $
        </span>
      ))}

      {/* ===== LAYER 2: convergence funnel (SVG intake cone + flowing dashes) ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="vc-funnelGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={gold} stopOpacity={0} />
            <stop offset="100%" stopColor={gold} stopOpacity={0.5} />
          </linearGradient>
          <radialGradient id="vc-coreGrad" cx="50%" cy="42%" r="60%">
            <stop offset="0%" stopColor={white} stopOpacity={0.95} />
            <stop offset="38%" stopColor={violet} stopOpacity={0.95} />
            <stop offset="100%" stopColor={'#1A0E33'} stopOpacity={0.92} />
          </radialGradient>
          <radialGradient id="vc-coreGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor={violet} stopOpacity={0.55} />
            <stop offset="100%" stopColor={violet} stopOpacity={0} />
          </radialGradient>
        </defs>

        {/* funnel intake lines: two converging guides from top corners to core */}
        {[-1, 1].map((dir) => {
          const topX = CX + dir * 380;
          const drawP = lin(localFrame, [8, 30], [0, 1]);
          const x2 = CX + dir * coreR * 0.7;
          const y2 = coreY - coreR * 0.5;
          return (
            <line
              key={`fn-${dir}`}
              x1={topX}
              y1={40}
              x2={lerp(topX, x2, drawP)}
              y2={lerp(40, y2, drawP)}
              stroke="url(#vc-funnelGrad)"
              strokeWidth={2.5}
              strokeDasharray="2 12"
              strokeDashoffset={-localFrame * 2}
              opacity={0.55}
            />
          );
        })}
        {/* center flow spine */}
        <line
          x1={CX}
          y1={30}
          x2={CX}
          y2={coreY - coreR * 0.6}
          stroke={gold}
          strokeWidth={3}
          strokeDasharray="4 14"
          strokeDashoffset={-localFrame * 4}
          opacity={lin(localFrame, [8, 28], [0, 0.5])}
        />

        {/* core ambient glow */}
        <circle
          cx={CX}
          cy={coreY}
          r={coreR * coreScale * 2.0}
          fill="url(#vc-coreGlow)"
          opacity={0.7 + 0.3 * impactPulse}
        />

        {/* ===== LAYER 3: spark ring around the devouring core ===== */}
        {Array.from({ length: 18 }).map((_, i) => {
          const a = (i / 18) * Math.PI * 2 + localFrame / 40;
          const rr = coreR * coreScale * (1.18 + 0.06 * Math.sin(localFrame / 7 + i));
          const sx = CX + Math.cos(a) * rr;
          const sy = coreY + Math.sin(a) * rr;
          const so = 0.3 + 0.5 * fract(Math.sin(i * 3.7) * 9.1);
          return (
            <circle
              key={`spk-${i}`}
              cx={sx}
              cy={sy}
              r={2 + 1.8 * impactPulse}
              fill={i % 3 === 0 ? coinGold : gold}
              opacity={so * (0.5 + 0.5 * impactPulse)}
            />
          );
        })}

        {/* core body */}
        <circle cx={CX} cy={coreY} r={coreR * coreScale} fill="url(#vc-coreGrad)" />
        <circle
          cx={CX}
          cy={coreY}
          r={coreR * coreScale}
          fill="none"
          stroke={violet}
          strokeWidth={4}
          opacity={0.95}
        />
        {/* devour shockwave on impact */}
        {impactPulse > 0.12 && (
          <circle
            cx={CX}
            cy={coreY}
            r={coreR * coreScale * (1 + (1 - impactPhase) * 0.7)}
            fill="none"
            stroke={gold}
            strokeWidth={3}
            opacity={impactPulse * 0.6}
          />
        )}
        {/* inner $$$ aperture pulse */}
        <circle
          cx={CX}
          cy={coreY}
          r={coreR * coreScale * (0.42 + 0.06 * impactPulse)}
          fill={white}
          opacity={0.16 + 0.2 * impactPulse}
        />
      </svg>

      {/* ===== LAYER 1: request token particles (DOM, glowing dollar pips) ===== */}
      {reqs.map((r) => (
        <div
          key={`rq-${r.idx}`}
          style={{
            position: 'absolute',
            left: r.x - r.s,
            top: r.y - r.s,
            width: r.s * 2,
            height: r.s * 2,
            borderRadius: r.s,
            background: r.hue > 0.6 ? coinGold : gold,
            opacity: r.o,
            boxShadow: `0 0 ${6 + r.s}px ${gold}cc`,
          }}
        />
      ))}

      {/* core label — PREMIUM MODEL */}
      <div
        style={{
          position: 'absolute',
          left: CX - 220,
          top: coreY + coreR * coreScale + 18,
          width: 440,
          textAlign: 'center',
          opacity: lin(localFrame, [14, 30], [0, 1]),
        }}
      >
        <div
          style={{
            fontFamily: 'Consolas, monospace',
            fontSize: 30,
            fontWeight: 700,
            letterSpacing: 4,
            color: white,
            textShadow: `0 0 18px ${violet}aa`,
          }}
        >
          $$$ PREMIUM MODEL
        </div>
        <div
          style={{
            marginTop: 6,
            fontFamily: 'Consolas, monospace',
            fontSize: 22,
            letterSpacing: 2,
            color: coinGold,
            opacity: 0.85,
          }}
        >
          every request &rarr; top tier
        </div>
      </div>

      {/* ===== LAYER 4: coin ejecta (DOM coins arcing to the tank) ===== */}
      {coins.map((c, i) => (
        <div
          key={`coin-${i}`}
          style={{
            position: 'absolute',
            left: c.x - 16 * c.scale,
            top: c.y - 16 * c.scale,
            width: 32 * c.scale,
            height: 32 * c.scale,
            borderRadius: 16 * c.scale,
            background: `radial-gradient(circle at 38% 32%, #FFF1C2, ${coinGold} 60%, #C8860B)`,
            border: `2px solid #FFE39A`,
            opacity: c.o,
            boxShadow: `0 0 14px ${coinGold}cc`,
            transform: `rotate(${c.rot}deg) scaleX(${0.5 + 0.5 * Math.abs(Math.cos((c.rot * Math.PI) / 180))})`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: 'Consolas, monospace',
            fontWeight: 800,
            fontSize: 16 * c.scale,
            color: '#7A4B00',
          }}
        >
          $
        </div>
      ))}

      {/* ===== LAYER 5: DRAINING BUDGET TANK ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="vc-liqGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={liquidColor} stopOpacity={0.95} />
            <stop offset="100%" stopColor={liquidColor} stopOpacity={0.55} />
          </linearGradient>
          <clipPath id="vc-tankClip">
            <rect
              x={tankX + innerPad}
              y={tankY + innerPad}
              width={innerW}
              height={innerH}
              rx={10}
            />
          </clipPath>
        </defs>

        {/* solid dark backing so liquid reads on transparent stage */}
        <rect
          x={tankX}
          y={tankY}
          width={tankW}
          height={tankH}
          rx={18}
          fill="rgba(8,6,18,0.72)"
          stroke="rgba(245,247,255,0.18)"
          strokeWidth={2}
        />

        {/* liquid (clipped) */}
        <g clipPath="url(#vc-tankClip)">
          {/* back wave (parallax) */}
          <path d={buildWavePath(6, waveAmp * 0.7, 2, 1.6)} fill="url(#vc-liqGrad)" opacity={0.5} />
          {/* front wave */}
          <path d={buildWavePath(0, waveAmp, 3, 0)} fill="url(#vc-liqGrad)" />
          {/* bright surface line */}
          <path
            d={(() => {
              const left = tankX + innerPad;
              let d = `M ${left} ${surfaceY.toFixed(1)}`;
              for (let s = 0; s <= 14; s++) {
                const xx = left + (innerW * s) / 14;
                const yy = surfaceY + Math.sin((s / 14) * Math.PI * 3 + waveT) * waveAmp;
                d += ` L ${xx.toFixed(1)} ${yy.toFixed(1)}`;
              }
              return d;
            })()}
            fill="none"
            stroke={white}
            strokeWidth={2.5}
            opacity={0.7}
          />
        </g>

        {/* drain level ticks */}
        {[0.25, 0.5, 0.75].map((p, i) => {
          const ty = tankY + innerPad + (1 - p) * innerH;
          return (
            <g key={`tick-${i}`}>
              <line
                x1={tankX}
                y1={ty}
                x2={tankX + 14}
                y2={ty}
                stroke="rgba(245,247,255,0.4)"
                strokeWidth={2}
              />
              <line
                x1={tankX + tankW - 14}
                y1={ty}
                x2={tankX + tankW}
                y2={ty}
                stroke="rgba(245,247,255,0.4)"
                strokeWidth={2}
              />
            </g>
          );
        })}

        {/* tank rim */}
        <rect
          x={tankX}
          y={tankY}
          width={tankW}
          height={tankH}
          rx={18}
          fill="none"
          stroke={fillLevel < 0.3 ? red : 'rgba(245,247,255,0.55)'}
          strokeWidth={3}
        />
        {/* draining drip out the bottom (animated) */}
        {Array.from({ length: 4 }).map((_, i) => {
          const per = 26 + i * 7;
          const prog = fract((localFrame + i * 9) / per);
          const dy = tankY + tankH + prog * 80;
          const dox = tankX + tankW * (0.3 + 0.16 * i);
          return (
            <circle
              key={`drip-${i}`}
              cx={dox}
              cy={dy}
              r={lerp(5, 2, prog)}
              fill={liquidColor}
              opacity={(1 - prog) * 0.8}
            />
          );
        })}
      </svg>

      {/* tank label */}
      <div
        style={{
          position: 'absolute',
          left: tankX,
          top: tankY - 44,
          width: tankW,
          textAlign: 'center',
          opacity: labelOpacity,
        }}
      >
        <span
          style={{
            fontFamily: 'Consolas, monospace',
            fontSize: 28,
            fontWeight: 700,
            letterSpacing: 3,
            color: fillLevel < 0.3 ? red : white,
            textShadow: fillLevel < 0.3 ? `0 0 16px ${red}aa` : 'none',
          }}
        >
          BUDGET
        </span>
        <div
          style={{
            fontFamily: 'Consolas, monospace',
            fontSize: 22,
            color: fillLevel < 0.3 ? red : 'rgba(245,247,255,0.65)',
          }}
        >
          {Math.round(fillLevel * 100)}%
        </div>
      </div>

      {/* ===== LAYER 6: RISING COST COUNTER ===== */}
      <div
        style={{
          position: 'absolute',
          left: 70,
          top: tankY + 20,
          width: 400,
          opacity: labelOpacity,
        }}
      >
        <div
          style={{
            fontFamily: 'Consolas, monospace',
            fontSize: 26,
            letterSpacing: 4,
            color: 'rgba(245,247,255,0.6)',
            textTransform: 'uppercase',
            marginBottom: 10,
          }}
        >
          monthly cost
        </div>
        <div
          style={{
            fontFamily: 'Consolas, monospace',
            fontSize: 104,
            fontWeight: 800,
            lineHeight: 1,
            color: costRed ? red : white,
            letterSpacing: -2,
            transform: `scale(${costKick})`,
            transformOrigin: 'left center',
            textShadow: costRed
              ? `0 0 34px ${red}cc, 0 0 8px ${red}`
              : `0 0 24px ${violet}66`,
            whiteSpace: 'nowrap',
          }}
        >
          {costStr}
        </div>
        {/* up-arrow surge indicator */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            marginTop: 14,
            opacity: lin(localFrame, [20, 40], [0, 1]),
          }}
        >
          <svg width={34} height={34} viewBox="0 0 34 34">
            <path
              d="M17 4 L30 22 L21 22 L21 32 L13 32 L13 22 L4 22 Z"
              fill={costRed ? red : coinGold}
              opacity={0.9}
              transform={`translate(0, ${-2 - 3 * impactPulse})`}
            />
          </svg>
          <span
            style={{
              fontFamily: 'Consolas, monospace',
              fontSize: 30,
              fontWeight: 700,
              color: costRed ? red : coinGold,
            }}
          >
            {costRed ? 'OVERPAYING' : 'climbing'}
          </span>
        </div>
      </div>

      {/* lower caption that states the idea (lands as words are spoken) */}
      <div
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 26,
          textAlign: 'center',
          opacity: lin(localFrame, [16, 34], [0, 1]),
        }}
      >
        <span style={{ fontSize: 40, fontWeight: 800, color: white, letterSpacing: 0.5 }}>
          One model.{' '}
          <span style={{ color: red, textShadow: `0 0 22px ${red}99` }}>
            Draining your budget.
          </span>
        </span>
      </div>
    </div>
  );
};
