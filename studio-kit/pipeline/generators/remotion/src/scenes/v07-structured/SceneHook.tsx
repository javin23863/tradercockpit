import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #7 (strict JSON) — beat: "You asked for JSON. It returned a paragraph that breaks your parser."
 *
 * CONCEPT: a messy free-text PROSE BLOB pours out of the model and SLAMS into a brittle PARSER plate.
 * The parser CRACKS (jagged fracture lines spread from the impact) and throws RED ERROR SPARKS. A
 * PARSER-STATUS LIGHT flips to a hard red "ERROR / SyntaxError", and a RETRY-LOOP counter climbs as the
 * parser keeps choking on the same unstructured text. The prose blob is alive — wobbling, leaking words.
 *
 * NOVELTY (vs ledger — all FORBIDDEN families avoided): no particle-torrent, no devouring-core, no
 * liquid-tank, no node-graph, no cache-vault, no send-rail-ghost-trail, no twin-cost-bars, no
 * isometric-lanes, no router-diamond, no serial-conveyor, no draft/verifier sweep, no gauge-needle.
 * NEW families: prose-blob-wobble, parser-plate-fracture, red error-spark burst, parser-status-light
 * flip, retry-loop counter climb.
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
  const rnd2 = (i: number) => fract(Math.sin(i * 78.233 + 4.17) * 24634.6345);
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
  const lin = (v: number, inR: number[], outR: number[]) =>
    interpolate(v, inR, outR, { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const wordStart = (sub: string) => { const w = words.find((x) => x.w.toLowerCase().includes(sub)); return w ? w.startS : null; };

  const cyan = accentA;
  const green = accentB;
  const white = '#F5F7FF';
  const red = '#FF3B5C';
  const amber = '#FFC542';
  const END = Math.max(60, beatDur);

  // narration land: "paragraph" and "breaks" escalate the failure
  const breakAt = wordStart('breaks') ?? wordStart('break') ?? null;
  const paraAt = wordStart('paragraph') ?? null;
  const broke = breakAt != null && tS >= breakAt;
  const sinceBreak = breakAt != null ? tS - breakAt : -1;

  const CX = 540;
  // parser plate (the brittle thing being hit), sits center-right
  const plateX = 560, plateY = 300, plateW = 380, plateH = 270;
  const pcx = plateX + plateW / 2, pcy = plateY + plateH / 2;

  // ---- the prose blob pours from the left and slams the plate on a cadence ----
  const pourIn = lin(localFrame, [4, 22], [0, 1]);
  const blobBob = Math.sin(localFrame / 9) * 6;
  // slam cadence: blob lurches into the plate repeatedly
  const slamRate = lin(localFrame, [10, 60, 110], [1.1, 1.6, 2.0]);
  const slamFloat = (Math.max(0, localFrame - 10) / fps) * slamRate;
  const slamCount = Math.floor(slamFloat);
  const slamPhase = fract(slamFloat);
  const slamPulse = Math.exp(-slamPhase * 6);

  // fracture intensity grows with each slam and HARD on "breaks"
  const fracBase = lin(localFrame, [16, 60], [0, 0.6]);
  const fracBreak = broke ? lin(sinceBreak, [0, 0.4], [0, 0.4]) : 0;
  const fracture = clamp(fracBase + fracBreak + 0.18 * slamPulse, 0, 1);

  // retry-loop counter climbs as the parser keeps choking
  const retryRate = lin(localFrame, [20, 80], [0.4, 1.1]);
  const retryCount = Math.floor((Math.max(0, localFrame - 20) / fps) * retryRate) + (broke ? 3 : 0);

  // status light: flips to ERROR once slams begin landing (or hard on "breaks")
  const errorOn = broke || localFrame > 40;
  const errBlink = errorOn ? 0.6 + 0.4 * Math.sin(localFrame / 4) : 0.2;

  // jagged fracture path across the plate (deterministic), grows with `fracture`
  const crackPath = (seed: number, spread: number) => {
    const sx = pcx + (rnd(seed) - 0.5) * 40;
    const sy = plateY + 6;
    let d = `M ${sx.toFixed(1)} ${sy.toFixed(1)}`;
    const segs = 6;
    for (let i = 1; i <= segs; i++) {
      const t = i / segs;
      const jx = (rnd(i * 3 + seed) - 0.5) * 70 * spread;
      const x = (pcx + (rnd(seed + 9) - 0.5) * 120 * spread) * t + sx * (1 - t) + jx;
      const y = lerp(sy, plateY + plateH - 6, t);
      d += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
    }
    return d;
  };

  // red error sparks bursting from the impact point on each slam
  const sparks: { x: number; y: number; o: number; s: number }[] = [];
  for (let k = 0; k < 14; k++) {
    const impIdx = slamCount - (k % 3);
    if (impIdx < 0) continue;
    const age = (slamFloat - impIdx) / slamRate;
    const t = clamp(age / 0.6);
    if (t <= 0 || t >= 1) continue;
    const ang = rnd(k * 7 + impIdx) * Math.PI * 2;
    const dist = lerp(6, 70 + rnd2(k) * 40, t);
    sparks.push({
      x: plateX + 8 + Math.cos(ang) * dist,
      y: pcy + Math.sin(ang) * dist,
      o: (1 - t) * 0.9,
      s: lerp(5, 1.5, t),
    });
  }

  // the prose blob's leaking words (free-text spilling out, unstructured)
  const proseWords = ['the answer', 'is roughly', 'about', 'see above', 'I think', 'maybe', 'etc.'];

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);
  const shake = broke ? Math.exp(-Math.max(0, sinceBreak) * 4) * 4 : 0;

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* ambient wash */}
      <div style={{ position: 'absolute', left: CX - 380, top: plateY - 220, width: 760, height: 620, borderRadius: 420,
        background: `radial-gradient(circle at 40% 45%, ${red}1c, transparent 66%)`, filter: 'blur(50px)' }} />

      <div style={{ position: 'absolute', inset: 0, transform: `translate(${Math.sin(localFrame * 1.7) * shake}px, ${Math.cos(localFrame * 2.1) * shake}px)` }}>
        {/* ===== the messy PROSE BLOB (organic, wobbling, spilling words) ===== */}
        <div style={{ position: 'absolute', left: 120, top: plateY - 20 + blobBob, width: 360, height: 300, opacity: pourIn }}>
          <svg width={360} height={300} viewBox="0 0 360 300" style={{ position: 'absolute', inset: 0 }}>
            <defs>
              <radialGradient id="hk7-blob" cx="42%" cy="40%" r="62%">
                <stop offset="0%" stopColor={amber} stopOpacity={0.5} />
                <stop offset="60%" stopColor={'#8A5A12'} stopOpacity={0.55} />
                <stop offset="100%" stopColor={'#2A1A06'} stopOpacity={0.85} />
              </radialGradient>
            </defs>
            {/* wobbling blob outline — a closed path with sin-perturbed radius */}
            <path
              d={(() => {
                const cx = 170, cy = 150; const pts = 22; let d = '';
                for (let i = 0; i <= pts; i++) {
                  const a = (i / pts) * Math.PI * 2;
                  const r = 120 + Math.sin(a * 3 + localFrame / 7) * 16 + Math.sin(a * 5 - localFrame / 11) * 10;
                  const x = cx + Math.cos(a) * r * 1.18;
                  const y = cy + Math.sin(a) * r * 0.92;
                  d += (i === 0 ? 'M' : 'L') + ` ${x.toFixed(1)} ${y.toFixed(1)}`;
                }
                return d + ' Z';
              })()}
              fill="url(#hk7-blob)" stroke={amber} strokeWidth={2} opacity={0.92}
            />
          </svg>
          {/* spilling free-text lines inside the blob */}
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center',
            paddingLeft: 56, paddingRight: 40, gap: 7 }}>
            {proseWords.map((pw, i) => (
              <div key={`pw-${i}`} style={{ fontFamily: 'Consolas, monospace', fontSize: 15,
                color: i % 2 ? 'rgba(245,247,255,0.85)' : amber, opacity: lin(localFrame, [12 + i * 2, 26 + i * 2], [0, 0.92]),
                transform: `translateX(${Math.sin(localFrame / 8 + i) * 3}px)`, whiteSpace: 'nowrap' }}>{pw}</div>
            ))}
          </div>
          <div style={{ position: 'absolute', left: 0, bottom: -34, width: 360, textAlign: 'center',
            fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 700, letterSpacing: 2, color: amber,
            opacity: lin(localFrame, [14, 30], [0, 1]) }}>FREE-TEXT PROSE</div>
        </div>

        {/* connector: blob lurching arrow into the plate (pulses per slam) */}
        <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
          {Array.from({ length: 5 }).map((_, i) => {
            const per = 30; const prog = fract((localFrame + i * 6) / per);
            const x = lerp(470, plateX - 4, prog);
            return <path key={`ar-${i}`} d={`M ${x} ${pcy - 9} L ${x + 16} ${pcy} L ${x} ${pcy + 9} Z`}
              fill={amber} opacity={(1 - prog) * 0.55} />;
          })}

          {/* ===== the brittle PARSER PLATE (gets cracked) ===== */}
          <rect x={plateX} y={plateY} width={plateW} height={plateH} rx={14}
            fill={'rgba(10,14,26,0.82)'} stroke={broke ? red : 'rgba(245,247,255,0.4)'} strokeWidth={3}
            opacity={lin(localFrame, [6, 22], [0, 1])} />
          {/* impact glow on the left edge where the blob slams */}
          <circle cx={plateX + 8} cy={pcy} r={18 + 22 * slamPulse} fill={red} opacity={slamPulse * 0.5} />

          {/* fracture lines spreading across the plate */}
          {[0, 1, 2, 3].map((k) => (
            <path key={`cr-${k}`} d={crackPath(k * 5 + 2, 0.4 + 0.6 * fracture)} fill="none"
              stroke={red} strokeWidth={lin(fracture, [0, 1], [1, 3])} opacity={clamp(fracture * (1 - k * 0.18)) * 0.9}
              style={{ filter: `drop-shadow(0 0 5px ${red})` }} />
          ))}
        </svg>

        {/* red error sparks (DOM, glowing) */}
        {sparks.map((sp, i) => (
          <div key={`sp-${i}`} style={{ position: 'absolute', left: sp.x - sp.s, top: sp.y - sp.s,
            width: sp.s * 2, height: sp.s * 2, borderRadius: sp.s, background: i % 3 === 0 ? amber : red,
            opacity: sp.o, boxShadow: `0 0 ${5 + sp.s * 2}px ${red}` }} />
        ))}

        {/* parser label + the broken { } it's choking on */}
        <div style={{ position: 'absolute', left: plateX, top: plateY + plateH / 2 - 46, width: plateW, textAlign: 'center' }}>
          <div style={{ fontFamily: 'Consolas, monospace', fontSize: 58, fontWeight: 800,
            color: broke ? red : 'rgba(245,247,255,0.55)', letterSpacing: 4,
            textShadow: broke ? `0 0 26px ${red}cc` : 'none' }}>{'{ ? }'}</div>
          <div style={{ marginTop: 6, fontFamily: 'Consolas, monospace', fontSize: 20, fontWeight: 700,
            letterSpacing: 3, color: broke ? red : 'rgba(245,247,255,0.5)' }}>JSON.parse()</div>
        </div>
      </div>

      {/* ===== PARSER-STATUS LIGHT (flips to ERROR, top-left) ===== */}
      <div style={{ position: 'absolute', left: 70, top: 96, width: 470, opacity: lin(localFrame, [8, 26], [0, 1]) }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 34, height: 34, borderRadius: 17, background: errorOn ? red : '#2A2F3A',
            boxShadow: errorOn ? `0 0 ${10 + 18 * errBlink}px ${red}` : 'none', opacity: errorOn ? errBlink : 0.4,
            border: `2px solid ${errorOn ? red : 'rgba(245,247,255,0.25)'}` }} />
          <span style={{ fontFamily: 'Consolas, monospace', fontSize: 40, fontWeight: 800, letterSpacing: 2,
            color: errorOn ? red : 'rgba(245,247,255,0.6)', textShadow: errorOn ? `0 0 22px ${red}aa` : 'none' }}>
            {errorOn ? 'ERROR' : 'PARSE'}
          </span>
        </div>
        <div style={{ marginTop: 12, fontFamily: 'Consolas, monospace', fontSize: 20, color: errorOn ? red : 'rgba(245,247,255,0.5)',
          opacity: lin(localFrame, [22, 40], [0, 1]) }}>
          SyntaxError: Unexpected token in prose
        </div>
        {/* retry-loop counter climbing */}
        <div style={{ marginTop: 18, fontFamily: 'Consolas, monospace', fontSize: 24, fontWeight: 700,
          color: amber, opacity: lin(localFrame, [26, 44], [0, 1]) }}>
          ↻ retries: <span style={{ color: red, fontSize: 30 }}>{retryCount}</span>
        </div>
      </div>

      {/* lower caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 28, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white, letterSpacing: 0.5 }}>
          You asked for JSON. <span style={{ color: red, textShadow: `0 0 22px ${red}99` }}>It broke your parser.</span>
        </span>
      </div>
    </div>
  );
};
