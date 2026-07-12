import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #4 (speculative decoding) — beat: "Accepted in bulk. Tokens per second doubles."
 *
 * CONCEPT: a big SPEEDOMETER (tokens/sec) whose NEEDLE sweeps from 1× to 2× on the spoken "doubles" — a
 * faint 1× GHOST needle stays pinned where it was, and the live needle slams to 2× with a "×2" snap. Below,
 * a BULK-ACCEPT burst: a stack of green accepted-token chips streams out per "tick", filling a throughput
 * meter to 2× the 1× baseline. One verify pass -> many tokens -> the rate doubles.
 *
 * NOVELTY (vs ledger): NEW family — a tokens/sec SWEEP SPEEDOMETER (1x ghost needle + 2x live needle +
 * ×2 snap) paired with a bulk-accepted-token throughput stream that fills to 2x the baseline tick-meter.
 * (No twin-cost-bars, no liquid columns, no delta-bracket of bars, no -90 snap, no torrent/core/tank,
 * no node-graph.)
 *
 * RENDER-SAFE: react + remotion only. No useCurrentFrame/AbsoluteFill/three. No Math.random/Date.now.
 * Strictly-increasing interpolate ranges (prop-derived ends guarded). 1080x820.
 */
export const SceneProof: React.FC<{
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

  const cyan = accentA;
  const green = accentB;
  const white = '#F5F7FF';
  const dim = 'rgba(245,247,255,0.45)';
  const END = Math.max(60, beatDur);

  const doublesAt = wordStart('doubles') ?? wordStart('second') ?? null;
  const bulkAt = wordStart('bulk') ?? wordStart('accepted') ?? null;

  // needle sweep 1x -> 2x: word-synced on "doubles", frame fallback otherwise
  const snap = doublesAt != null
    ? clamp(lin(tS - doublesAt, [0, 0.4], [0, 1]))
    : clamp(lin(localFrame, [40, 60], [0, 1]));
  // spring overshoot on the slam
  const slam = doublesAt != null
    ? spring({ frame: Math.max(0, Math.round((tS - doublesAt) * fps)), fps, config: { damping: 9, stiffness: 130 } })
    : spring({ frame: Math.max(0, localFrame - 40), fps, config: { damping: 9, stiffness: 130 } });

  // speedometer geometry — dial spans -120deg (0x) .. +120deg (2.4x), 1x at center-ish, 2x near top-right
  const gx = 540, gy = 330, gr = 168;
  const RATE_MAX = 2.4;
  const angForRate = (r: number) => lerp(-120, 120, clamp(r / RATE_MAX));
  const oneAng = angForRate(1.0);
  const liveRate = lerp(1.0, 2.0, snap * (0.85 + 0.15 * Math.min(1, slam))); // eases to ~2.0
  const liveAng = angForRate(liveRate);
  const rateStr = liveRate.toFixed(1);

  // bulk-accept throughput meter (baseline 1x bar vs live 2x bar) at the bottom
  const baseY = 690;
  const meterX = 230, meterW = 620, meterH = 30;
  const fillIn = clamp(lin(localFrame, [10, 40], [0, 1]));
  const liveFrac = clamp(liveRate / 2.0); // 0..1, fills to full at 2x

  // streaming accepted-token chips (bulk) flowing into the meter
  const chips: { x: number; y: number; o: number; s: number }[] = [];
  const chipRate = 10;
  const chipFloat = (Math.max(0, localFrame - 12) / fps) * chipRate;
  for (let k = 0; k < 14; k++) {
    const idx = Math.floor(chipFloat) - k;
    if (idx < 0) continue;
    const age = (chipFloat - idx) / chipRate;
    const t = clamp(age / 0.7);
    const x = lerp(gx + gr * 0.2, meterX + meterW * liveFrac * 0.92, t) + (rnd(idx) - 0.5) * 20;
    const y = lerp(gy + gr * 0.5, baseY - 6, t);
    const o = clamp(lin(t, [0, 0.1, 0.85, 1], [0, 1, 1, 0])) * fillIn;
    chips.push({ x, y, o, s: lerp(1, 0.6, t) });
  }

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);
  const x2Pop = snap > 0.02 ? slam : 0;

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      <div style={{ position: 'absolute', left: gx - 360, top: gy - 260, width: 720, height: 560, borderRadius: 380,
        background: `radial-gradient(circle at 50% 45%, ${green}1c, transparent 66%)`, filter: 'blur(48px)' }} />

      {/* eyebrow */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 96, textAlign: 'center', opacity: lin(localFrame, [4, 20], [0, 1]),
        fontFamily: 'Consolas, monospace', fontSize: 24, letterSpacing: 6, color: 'rgba(245,247,255,0.6)', textTransform: 'uppercase' }}>
        tokens / second
      </div>

      {/* ===== SPEEDOMETER ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <radialGradient id="pf4-face" cx="50%" cy="46%" r="62%">
            <stop offset="0%" stopColor={'#0C1620'} stopOpacity={0.95} />
            <stop offset="100%" stopColor={'#060B12'} stopOpacity={0.95} />
          </radialGradient>
        </defs>

        {/* dial face */}
        <circle cx={gx} cy={gy} r={gr} fill="url(#pf4-face)" stroke={'rgba(245,247,255,0.16)'} strokeWidth={2} />
        {/* tick marks 0..2.4x */}
        {Array.from({ length: 25 }).map((_, i) => {
          const t = i / 24; const a = lerp(-120, 120, t) * Math.PI / 180;
          const major = i % 5 === 0;
          const r1 = gr - (major ? 26 : 18), r2 = gr - 6;
          const rate = t * RATE_MAX;
          const hot = rate >= 1.0;
          return <line key={`pt-${i}`}
            x1={gx + Math.sin(a) * r1} y1={gy - Math.cos(a) * r1}
            x2={gx + Math.sin(a) * r2} y2={gy - Math.cos(a) * r2}
            stroke={hot ? green : 'rgba(245,247,255,0.32)'} strokeWidth={major ? 3.5 : 2}
            opacity={lin(localFrame, [8, 26], [0, 0.95])} />;
        })}
        {/* 1x label marker */}
        {(() => { const a = oneAng * Math.PI / 180; const r = gr - 44;
          return <text x={gx + Math.sin(a) * r} y={gy - Math.cos(a) * r + 6} fill={dim} fontSize={22}
            fontFamily="Consolas, monospace" textAnchor="middle">1×</text>; })()}
        {/* 2x label marker */}
        {(() => { const a = angForRate(2.0) * Math.PI / 180; const r = gr - 44;
          return <text x={gx + Math.sin(a) * r} y={gy - Math.cos(a) * r + 6} fill={green} fontSize={24} fontWeight={700}
            fontFamily="Consolas, monospace" textAnchor="middle">2×</text>; })()}

        {/* GHOST needle pinned at 1x (where it was) */}
        {(() => { const a = oneAng * Math.PI / 180; const len = gr - 34;
          return <line x1={gx} y1={gy} x2={gx + Math.sin(a) * len} y2={gy - Math.cos(a) * len}
            stroke={dim} strokeWidth={4} strokeLinecap="round" strokeDasharray="6 8" opacity={0.7} />; })()}

        {/* LIVE needle sweeping to 2x */}
        {(() => { const a = liveAng * Math.PI / 180; const len = gr - 26;
          return <line x1={gx} y1={gy} x2={gx + Math.sin(a) * len} y2={gy - Math.cos(a) * len}
            stroke={green} strokeWidth={6} strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 12px ${green})` }} />; })()}
        <circle cx={gx} cy={gy} r={11} fill={green} stroke={white} strokeWidth={2} />

        {/* sweep arc highlight from 1x to live */}
        {snap > 0.02 && (() => {
          const a0 = oneAng * Math.PI / 180; const a1 = liveAng * Math.PI / 180; const rr = gr - 12;
          const x0 = gx + Math.sin(a0) * rr, y0 = gy - Math.cos(a0) * rr;
          const x1 = gx + Math.sin(a1) * rr, y1 = gy - Math.cos(a1) * rr;
          const large = Math.abs(liveAng - oneAng) > 180 ? 1 : 0;
          return <path d={`M ${x0.toFixed(1)} ${y0.toFixed(1)} A ${rr} ${rr} 0 ${large} 1 ${x1.toFixed(1)} ${y1.toFixed(1)}`}
            fill="none" stroke={green} strokeWidth={4} opacity={0.55} />;
        })()}
      </svg>

      {/* live rate digital readout (center of dial, lower half) */}
      <div style={{ position: 'absolute', left: gx - 110, top: gy + 44, width: 220, textAlign: 'center' }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 46, fontWeight: 800,
          color: snap > 0.5 ? green : white, letterSpacing: -1,
          textShadow: snap > 0.5 ? `0 0 22px ${green}aa` : 'none' }}>
          {rateStr}×
        </div>
      </div>

      {/* ×2 hero snap */}
      <div style={{ position: 'absolute', left: gx + gr - 20, top: gy - gr - 14,
        transform: `scale(${0.5 + 0.6 * x2Pop}) rotate(${-8 + 8 * x2Pop}deg)`, opacity: snap }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 96, fontWeight: 800, color: green,
          letterSpacing: -3, textShadow: `0 0 40px ${green}cc, 0 0 10px ${green}` }}>×2</span>
      </div>

      {/* ===== BULK-ACCEPT throughput meter ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        {/* meter track */}
        <rect x={meterX} y={baseY - meterH} width={meterW} height={meterH} rx={meterH / 2}
          fill={'rgba(10,14,22,0.8)'} stroke={'rgba(245,247,255,0.2)'} strokeWidth={2} />
        {/* 1x baseline marker (half) */}
        <line x1={meterX + meterW * 0.5} y1={baseY - meterH - 12} x2={meterX + meterW * 0.5} y2={baseY + 4}
          stroke={dim} strokeWidth={2.5} strokeDasharray="5 6" opacity={0.8} />
        {/* live fill to 2x (full) */}
        <rect x={meterX} y={baseY - meterH} width={Math.max(1, meterW * liveFrac * fillIn)} height={meterH} rx={meterH / 2}
          fill={green} opacity={0.92} />
        {/* fill highlight */}
        <rect x={meterX} y={baseY - meterH} width={Math.max(1, meterW * liveFrac * fillIn)} height={meterH / 2.4} rx={meterH / 3}
          fill={white} opacity={0.18} />
      </svg>

      {/* meter labels */}
      <div style={{ position: 'absolute', left: meterX + meterW * 0.5 - 40, top: baseY + 12, width: 80, textAlign: 'center',
        fontFamily: 'Consolas, monospace', fontSize: 15, color: dim }}>1× before</div>
      <div style={{ position: 'absolute', left: meterX + meterW - 70, top: baseY + 12, width: 90, textAlign: 'right',
        fontFamily: 'Consolas, monospace', fontSize: 16, fontWeight: 700, color: green,
        opacity: lin(localFrame, [30, 48], [0, 1]) }}>2× after</div>

      {/* streaming accepted-token chips (bulk) */}
      {chips.map((c, i) => (
        <div key={`pc-${i}`} style={{ position: 'absolute', left: c.x - 11 * c.s, top: c.y - 11 * c.s,
          width: 22 * c.s, height: 22 * c.s, borderRadius: 6, background: `${green}cc`, border: `1.5px solid ${green}`,
          opacity: c.o, boxShadow: `0 0 10px ${green}88`, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'Consolas, monospace', fontSize: 12 * c.s, fontWeight: 800, color: '#08120C' }}>✓</div>
      ))}

      {/* "accepted in bulk" badge */}
      <div style={{ position: 'absolute', left: meterX, top: baseY - meterH - 52, width: meterW, textAlign: 'center',
        opacity: lin(localFrame, [14, 32], [0, 1]) }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 20, fontWeight: 700, letterSpacing: 2,
          color: bulkAt != null && tS >= bulkAt ? green : 'rgba(245,247,255,0.7)' }}>
          ACCEPTED IN BULK
        </span>
      </div>

      {/* caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 28, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white }}>
          Same model. <span style={{ color: green, textShadow: `0 0 22px ${green}99` }}>Twice the tokens per second.</span>
        </span>
      </div>
    </div>
  );
};
