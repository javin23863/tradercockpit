import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #4 (speculative decoding) — beat: "Your model writes one token at a time. That is the speed ceiling."
 *
 * CONCEPT: a SINGLE token-cell crawls along a SERIAL CONVEYOR, one cell at a time, each new token only
 * starting after the previous one clears — it cannot go faster. Above, a hard glowing CEILING BAR caps a
 * slow tokens/sec gauge whose needle is PINNED low and bumps the ceiling. A "1× / one at a time" stamp + a
 * step-counter that ticks one token per beat make the serial bottleneck legible.
 *
 * NOVELTY (vs ledger — all FORBIDDEN families avoided): no particle-torrent, no devouring-core, no
 * liquid-tank, no node-graph, no cache-vault, no send-rail-ghost-trail, no twin-cost-bars, no
 * isometric-lanes, no router-diamond. NEW families: serial single-file conveyor with a hard speed-ceiling
 * bar, a needle-against-ceiling rate gauge, a one-token step-counter, a serial occupancy lock.
 *
 * RENDER-SAFE: imports only react + remotion (interpolate/spring). No useCurrentFrame/AbsoluteFill/three.
 * No Math.random/Date.now/new Date (deterministic rnd). All interpolate input ranges strictly increasing
 * (prop-derived ends guarded with Math.max). Deterministic number formatting. Stays inside 1080x820.
 */
export const SceneHook: React.FC<{
  localFrame: number; tS: number; fps: number; beatDur: number;
  accentA: string; accentB: string;
  words: { w: string; startS: number; endS: number }[];
}> = ({ localFrame, tS, fps, beatDur, accentA, accentB, words }) => {
  const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const fract = (x: number) => x - Math.floor(x);
  const rnd = (i: number) => fract(Math.sin(i * 12.9898) * 43758.5453);
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
  const lin = (v: number, inR: number[], outR: number[]) =>
    interpolate(v, inR, outR, { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const wordStart = (sub: string) => { const w = words.find((x) => x.w.toLowerCase().includes(sub)); return w ? w.startS : null; };

  const cyan = accentA;          // serial / speed accent
  const green = accentB;
  const white = '#F5F7FF';
  const red = '#FF5470';
  const END = Math.max(60, beatDur);

  // narration land: emphasize "one" and "ceiling"
  const oneAt = wordStart('one') ?? null;
  const ceilingAt = wordStart('ceiling') ?? wordStart('speed') ?? null;
  const ceilHit = ceilingAt != null && tS >= ceilingAt;

  const CX = 540;
  const railY = 470;            // serial conveyor y
  const railX0 = 110;          // conveyor start
  const railX1 = 970;          // conveyor end (the wall)
  const cellW = 84;            // token-cell width
  const slotGap = 96;          // slot pitch

  // ---- SERIAL cadence: one token enters only after the previous clears (cannot parallelize) ----
  const tokRate = lin(localFrame, [10, 60, 110], [0.9, 1.25, 1.45]); // tokens/sec — capped low, barely rises
  const tokFloat = (Math.max(0, localFrame - 10) / fps) * tokRate;
  const tokCount = Math.floor(tokFloat);
  const tokPhase = fract(tokFloat);
  const tokPulse = Math.exp(-tokPhase * 5);

  // the active token-cell crawls one slot per token; it occupies the rail ALONE (serial lock)
  const cellX = lerp(railX0 + 60, railX1 - cellW - 40, tokPhase);
  // a couple of faint "waiting" tokens queued at the start (they CAN'T move until the active one clears)
  const queued = [0, 1, 2].map((k) => ({
    x: railX0 + 6 + k * 30,
    o: lin(localFrame, [12, 30], [0, 1]) * (1 - k * 0.22),
    s: 0.62 - k * 0.06,
  }));

  // rate gauge needle: pinned low, bumps the ceiling on cadence
  const needleBase = lin(localFrame, [12, 40], [0, 0.30]);          // 0..1 of the dial, stays low
  const needleBump = 0.30 + 0.05 * tokPulse + (ceilHit ? 0.02 : 0); // taps the ceiling, never past it
  const needleT = clamp(needleBase < needleBump ? needleBump : needleBase, 0, 0.34);
  // dial spans -120deg..+120deg; ceiling sits at the low end (~ -30deg)
  const needleAng = lerp(-120, 120, needleT);
  const gx = 330, gy = 175, gr = 96;

  // token/sec readout — crawls up but caps ~1×
  const tpsVal = (1.0 * needleT / 0.30); // ~1.0 at the pin
  const tpsStr = tpsVal.toFixed(1);

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);
  const ceilGlow = ceilHit ? 0.5 + 0.5 * Math.sin(localFrame / 6) : 0.3;

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* ambient wash */}
      <div style={{ position: 'absolute', left: CX - 380, top: railY - 360, width: 760, height: 640, borderRadius: 420,
        background: `radial-gradient(circle at 50% 45%, ${cyan}1e, transparent 66%)`, filter: 'blur(50px)' }} />

      {/* ===== SVG layer: ceiling bar + rate gauge ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="hk4-rail" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={cyan} stopOpacity={0.1} />
            <stop offset="100%" stopColor={cyan} stopOpacity={0.5} />
          </linearGradient>
          <radialGradient id="hk4-dial" cx="50%" cy="50%" r="60%">
            <stop offset="0%" stopColor={'#0E1626'} stopOpacity={0.95} />
            <stop offset="100%" stopColor={'#070B14'} stopOpacity={0.95} />
          </radialGradient>
        </defs>

        {/* ---- hard SPEED CEILING bar across the top of the stage ---- */}
        <line x1={120} y1={92} x2={960} y2={92} stroke={red} strokeWidth={5}
          opacity={lin(localFrame, [6, 24], [0, 0.85])} strokeDasharray="14 8" />
        {/* downward hatch ticks under the ceiling (it presses down) */}
        {Array.from({ length: 18 }).map((_, i) => {
          const x = 130 + i * 47;
          return <line key={`ch-${i}`} x1={x} y1={92} x2={x - 9} y2={108} stroke={red} strokeWidth={2.5}
            opacity={lin(localFrame, [8, 26], [0, 0.5])} />;
        })}

        {/* ---- RATE GAUGE (needle pinned low, bumps ceiling) ---- */}
        <circle cx={gx} cy={gy} r={gr} fill="url(#hk4-dial)" stroke={'rgba(245,247,255,0.18)'} strokeWidth={2} />
        {/* dial arc */}
        {Array.from({ length: 21 }).map((_, i) => {
          const t = i / 20; const a = lerp(-120, 120, t) * Math.PI / 180;
          const r1 = gr - 14, r2 = gr - 4;
          const lowZone = t <= 0.34;
          return <line key={`gt-${i}`}
            x1={gx + Math.sin(a) * r1} y1={gy - Math.cos(a) * r1}
            x2={gx + Math.sin(a) * r2} y2={gy - Math.cos(a) * r2}
            stroke={lowZone ? red : 'rgba(245,247,255,0.3)'} strokeWidth={lowZone ? 3 : 2}
            opacity={lin(localFrame, [10, 28], [0, 0.9])} />;
        })}
        {/* ceiling marker on the dial (the cap the needle can't pass) */}
        {(() => { const a = lerp(-120, 120, 0.34) * Math.PI / 180; const r1 = gr - 16, r2 = gr + 8;
          return <line x1={gx + Math.sin(a) * r1} y1={gy - Math.cos(a) * r1}
            x2={gx + Math.sin(a) * r2} y2={gy - Math.cos(a) * r2}
            stroke={red} strokeWidth={4} opacity={0.5 + 0.5 * ceilGlow} />; })()}
        {/* needle */}
        {(() => { const a = needleAng * Math.PI / 180; const len = gr - 22;
          return <line x1={gx} y1={gy} x2={gx + Math.sin(a) * len} y2={gy - Math.cos(a) * len}
            stroke={cyan} strokeWidth={5} strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 8px ${cyan})` }} />; })()}
        <circle cx={gx} cy={gy} r={7} fill={cyan} />

        {/* ---- SERIAL CONVEYOR rail ---- */}
        <line x1={railX0} y1={railY + 44} x2={railX1} y2={railY + 44} stroke="url(#hk4-rail)" strokeWidth={4}
          opacity={lin(localFrame, [8, 26], [0, 0.8])} />
        {/* slot dividers — one-at-a-time lanes */}
        {Array.from({ length: 9 }).map((_, i) => {
          const x = railX0 + 50 + i * slotGap;
          if (x > railX1 - 30) return null;
          return <line key={`sl-${i}`} x1={x} y1={railY - 8} x2={x} y2={railY + 44} stroke={'rgba(245,247,255,0.14)'} strokeWidth={1.5} />;
        })}
        {/* the WALL at the end (output bottleneck) */}
        <rect x={railX1 - 8} y={railY - 30} width={10} height={92} rx={3} fill={red} opacity={0.7} />
        {/* serial lock indicator: a single occupancy badge over the rail */}
        <rect x={railX0 + 40} y={railY - 50} width={railX1 - railX0 - 80} height={6} rx={3}
          fill={'none'} stroke={'rgba(245,247,255,0.12)'} strokeWidth={1} />
      </svg>

      {/* ---- queued (waiting) tokens — blocked, can't move ---- */}
      {queued.map((q, i) => (
        <div key={`q-${i}`} style={{ position: 'absolute', left: q.x, top: railY - 8 + (1 - q.s) * 30,
          width: cellW * q.s, height: 56 * q.s, borderRadius: 10, background: 'rgba(20,28,44,0.82)',
          border: `1.5px solid ${cyan}66`, opacity: q.o * 0.7, display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontFamily: 'Consolas, monospace', fontSize: 14 * q.s, color: `${cyan}aa` }}>
          tok
        </div>
      ))}

      {/* ---- the ACTIVE token-cell (alone on the rail — serial) ---- */}
      <div style={{ position: 'absolute', left: cellX, top: railY - 14 + tokPulse * -2, width: cellW, height: 60,
        borderRadius: 12, background: 'linear-gradient(160deg, rgba(30,40,60,0.96), rgba(12,18,30,0.96))',
        border: `2px solid ${cyan}`, boxShadow: `0 0 ${14 + 18 * tokPulse}px ${cyan}aa`,
        transform: `scale(${1 + 0.04 * tokPulse})`, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 2 }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 17, fontWeight: 700, color: white, letterSpacing: 1 }}>token</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 11, color: cyan, opacity: 0.85 }}>#{tokCount}</div>
      </div>

      {/* ---- "one at a time" stamp near the active cell ---- */}
      <div style={{ position: 'absolute', left: cellX - 6, top: railY + 60, width: cellW + 12, textAlign: 'center',
        opacity: lin(localFrame, [18, 34], [0, 1]) }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 13, letterSpacing: 1, color: 'rgba(245,247,255,0.55)' }}>
          one at a time
        </span>
      </div>

      {/* ---- tokens/sec readout (top-left, capped at ~1×) ---- */}
      <div style={{ position: 'absolute', left: 70, top: 150, width: 420, opacity: lin(localFrame, [8, 26], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 22, letterSpacing: 4, color: 'rgba(245,247,255,0.6)', textTransform: 'uppercase', marginBottom: 8 }}>
          tokens / sec
        </div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 86, fontWeight: 800, lineHeight: 1, color: ceilHit ? red : white,
          letterSpacing: -2, transform: `scale(${1 + 0.05 * tokPulse})`, transformOrigin: 'left center',
          textShadow: ceilHit ? `0 0 28px ${red}cc` : `0 0 20px ${cyan}55`, whiteSpace: 'nowrap' }}>
          {tpsStr}×
        </div>
        <div style={{ marginTop: 10, fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 700, color: red, opacity: lin(localFrame, [24, 42], [0, 1]) }}>
          ↑ stuck at the ceiling
        </div>
      </div>

      {/* lower caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 28, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white, letterSpacing: 0.5 }}>
          One token at a time. <span style={{ color: red, textShadow: `0 0 22px ${red}99` }}>That is the ceiling.</span>
        </span>
      </div>
    </div>
  );
};
