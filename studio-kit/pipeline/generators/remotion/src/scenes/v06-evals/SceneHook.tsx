import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #6 (shipping LLM features without evals) — beat:
 * "You changed the prompt. Did it get better, or silently worse?"
 *
 * CONCEPT — FLYING BLIND: a new prompt VERSION is a tiny aircraft gliding through dark fog with a
 * DEAD instrument panel — the attitude/altitude/airspeed gauges are frozen/null, no horizon line —
 * heading straight toward a HIDDEN REGRESSION: a mountain-ridge silhouette that only materializes out
 * of the fog right in front of it. A blind "NO INSTRUMENTS" alarm pulses. About to crash, can't see it.
 *
 * NOVELTY (vs ledger — forbidden families avoided): NO particle-torrent/devouring-core/draining-tank,
 * NO isometric routing lanes, NO node-graph/similarity-ring, NO cache-vault/lightning, NO twin-cost-bars,
 * NO send-rail/full-price-stamp, NO liquid columns. NEW families introduced here:
 *   - dead-instrument-panel (three frozen aviation gauges reading null / no-signal)
 *   - drifting fog-veil bands (parallax translucent strata that occlude the scene)
 *   - terrain-proximity regression silhouette that rises out of the fog ahead of the craft
 *   - version-aircraft glide with banking bob along a flight path
 *   - blind alarm (NO INSTRUMENTS chip) flashing on the spoken word
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

  const rose = accentA;            // danger / blind accent
  const mint = accentB;
  const white = '#F5F7FF';
  const red = '#FF3B5C';
  const END = Math.max(60, beatDur);

  // narration land: "worse" is the moment the hidden ridge reveals
  const worseAt = wordStart('worse') ?? wordStart('silently') ?? null;
  const blindOn = worseAt != null ? tS >= worseAt : localFrame > 64;
  const sinceBlind = worseAt != null ? Math.max(0, tS - worseAt) : (localFrame > 64 ? (localFrame - 64) / fps : 0);

  const CX = 540;

  // ---- the version aircraft glides along a gently bobbing path ----
  const planeIn = spring({ frame: localFrame, fps, config: { damping: 16 } });
  const planeX = lerp(180, 470, lin(localFrame, [6, 70], [0, 1]));   // creeps toward the ridge
  const planeBaseY = 300;
  const planeBob = Math.sin(localFrame / 13) * 14;
  const planeBank = Math.sin(localFrame / 17) * 7;                   // gentle roll degrees
  const planeY = planeBaseY + planeBob;

  // ---- hidden REGRESSION ridge rises out of the fog ahead of the plane ----
  const ridgeReveal = clamp(lin(sinceBlind, [0, 0.7], [0, 1]));       // 0 hidden -> 1 looming
  const ridgeBaseY = 560;
  const ridgeTop = lerp(ridgeBaseY, 360, ridgeReveal);               // peak climbs up toward the craft

  // deterministic jagged ridge silhouette across the right side
  const ridgePath = (() => {
    const x0 = 520, x1 = 1040, n = 9;
    let d = `M ${x0} 760`;
    for (let k = 0; k <= n; k++) {
      const t = k / n;
      const x = lerp(x0, x1, t);
      const jag = (rnd(k * 2 + 3) - 0.5) * 70;
      // tallest near the plane's path then receding
      const heightFactor = Math.sin(t * Math.PI * 0.9 + 0.3);
      const y = lerp(760, ridgeTop, clamp(heightFactor)) + jag * (1 - ridgeReveal * 0.4);
      d += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
    }
    d += ` L 1040 760 Z`;
    return d;
  })();

  // ---- three DEAD instrument gauges (frozen / null readouts) ----
  const gaugeFlicker = (seed: number) => 0.25 + 0.18 * Math.abs(Math.sin(localFrame / (7 + seed) + seed)); // sick flicker
  const gauges = [
    { cx: 150, label: 'ATTITUDE' },
    { cx: 270, label: 'ALTITUDE' },
    { cx: 390, label: 'AIRSPEED' },
  ];
  const gaugeY = 700;
  const gaugeR = 46;
  const panelIn = lin(localFrame, [10, 28], [0, 1]);

  // ---- fog-veil drifting bands (parallax strata) ----
  const fog: { y: number; o: number; x: number; h: number }[] = [];
  for (let i = 0; i < 5; i++) {
    const speed = 0.4 + rnd(i) * 0.6;
    const x = -120 + fract((localFrame * speed) / 220 + rnd(i + 9)) * 240 - 120;
    const y = lerp(180, 540, rnd(i * 3 + 1));
    const o = (0.10 + rnd(i + 2) * 0.12) * lin(localFrame, [0, 20], [0, 1]);
    fog.push({ y, o, x, h: 70 + rnd(i + 5) * 70 });
  }

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);
  const alarmPulse = blindOn ? 0.5 + 0.5 * Math.sin(localFrame / 4) : 0;

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* murky sky wash (no opaque paint) */}
      <div style={{ position: 'absolute', left: CX - 420, top: 120, width: 840, height: 560, borderRadius: 420,
        background: `radial-gradient(circle at 46% 40%, ${rose}14, transparent 66%)`, filter: 'blur(54px)' }} />

      {/* danger wash as the ridge reveals */}
      {blindOn && (
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none',
          background: `radial-gradient(circle at 70% 55%, rgba(255,59,92,${(0.06 + 0.12 * ridgeReveal).toFixed(3)}), transparent 60%)` }} />
      )}

      {/* ===== drifting fog-veil bands (behind the craft) ===== */}
      {fog.map((f, i) => (
        <div key={`fog-${i}`} style={{ position: 'absolute', left: f.x, top: f.y, width: 1320, height: f.h,
          borderRadius: f.h, background: `linear-gradient(90deg, transparent, rgba(200,205,235,${f.o}), transparent)`,
          filter: 'blur(20px)', pointerEvents: 'none' }} />
      ))}

      {/* ===== hidden REGRESSION ridge (SVG) ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="hk6-ridge" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={red} stopOpacity={0.55} />
            <stop offset="100%" stopColor={'#2A0712'} stopOpacity={0.92} />
          </linearGradient>
        </defs>
        <path d={ridgePath} fill="url(#hk6-ridge)" stroke={red} strokeWidth={2.5} opacity={0.35 + 0.55 * ridgeReveal} />
        {/* danger crest line on the peak when revealed */}
        {ridgeReveal > 0.25 && (
          <path d={ridgePath} fill="none" stroke={red} strokeWidth={3}
            strokeDasharray="3 12" strokeDashoffset={-localFrame * 4} opacity={ridgeReveal * 0.9} />
        )}

        {/* flight path dashes ahead of the craft (uncertain trajectory) */}
        <path d={`M ${planeX + 40} ${planeY} Q ${planeX + 180} ${planeY - 20} ${planeX + 320} ${ridgeTop + 30}`}
          fill="none" stroke={rose} strokeWidth={2.5} strokeDasharray="2 12"
          strokeDashoffset={-localFrame * 3} opacity={lin(localFrame, [14, 34], [0, 0.6])} />
      </svg>

      {/* ===== the VERSION aircraft (DOM, banking glide) ===== */}
      <div style={{ position: 'absolute', left: planeX - 46, top: planeY - 34, width: 92, height: 68,
        transform: `rotate(${planeBank}deg) scale(${lerp(0.6, 1, planeIn)})`, transformOrigin: 'center' }}>
        {/* glow */}
        <div style={{ position: 'absolute', inset: -16, borderRadius: 40, background: `radial-gradient(circle, ${rose}44, transparent 70%)`, filter: 'blur(8px)' }} />
        {/* fuselage */}
        <svg width={92} height={68} viewBox="0 0 92 68">
          <path d="M 6 34 L 60 26 L 86 30 L 86 38 L 60 42 L 6 34 Z" fill="rgba(20,16,30,0.95)" stroke={rose} strokeWidth={2.5} />
          {/* wings */}
          <path d="M 40 30 L 28 6 L 36 6 L 52 28 Z" fill="rgba(20,16,30,0.95)" stroke={rose} strokeWidth={2} />
          <path d="M 40 38 L 28 62 L 36 62 L 52 40 Z" fill="rgba(20,16,30,0.95)" stroke={rose} strokeWidth={2} />
          {/* nose light blinking */}
          <circle cx={84} cy={34} r={4} fill={red} opacity={0.5 + 0.5 * Math.abs(Math.sin(localFrame / 5))} />
        </svg>
        {/* version tag */}
        <div style={{ position: 'absolute', left: -8, top: -26, fontFamily: 'Consolas, monospace', fontSize: 15,
          fontWeight: 800, color: rose, letterSpacing: 1, textShadow: `0 0 10px ${rose}aa`, whiteSpace: 'nowrap' }}>
          prompt v2
        </div>
      </div>

      {/* ===== DEAD instrument panel (three frozen null gauges) ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0, opacity: panelIn }}>
        {gauges.map((g, i) => {
          const fl = gaugeFlicker(i + 1);
          return (
            <g key={`gauge-${i}`}>
              <circle cx={g.cx} cy={gaugeY} r={gaugeR} fill="rgba(8,6,18,0.82)" stroke="rgba(245,247,255,0.22)" strokeWidth={2.5} />
              {/* ticks */}
              {Array.from({ length: 8 }).map((_, k) => {
                const a = (k / 8) * Math.PI * 2;
                return <line key={`t-${i}-${k}`} x1={g.cx + Math.cos(a) * (gaugeR - 8)} y1={gaugeY + Math.sin(a) * (gaugeR - 8)}
                  x2={g.cx + Math.cos(a) * (gaugeR - 2)} y2={gaugeY + Math.sin(a) * (gaugeR - 2)}
                  stroke="rgba(245,247,255,0.3)" strokeWidth={2} />;
              })}
              {/* DEAD needle: frozen, slumped down (no signal) + sick flicker */}
              <line x1={g.cx} y1={gaugeY} x2={g.cx - 4} y2={gaugeY + gaugeR - 12}
                stroke={red} strokeWidth={3} opacity={0.4 + fl} />
              <circle cx={g.cx} cy={gaugeY} r={4} fill={red} opacity={0.5 + 0.4 * fl} />
              {/* null readout */}
              <text x={g.cx} y={gaugeY + 4} textAnchor="middle" fontFamily="Consolas, monospace" fontSize={16}
                fontWeight={800} fill={red} opacity={0.55 + 0.4 * fl}>--</text>
            </g>
          );
        })}
      </svg>
      {/* gauge labels (DOM for crisp text) */}
      {gauges.map((g, i) => (
        <div key={`gl-${i}`} style={{ position: 'absolute', left: g.cx - 60, top: gaugeY + gaugeR + 8, width: 120,
          textAlign: 'center', fontFamily: 'Consolas, monospace', fontSize: 12, letterSpacing: 1,
          color: 'rgba(245,247,255,0.5)', opacity: panelIn }}>{g.label}</div>
      ))}

      {/* NO INSTRUMENTS blind alarm */}
      <div style={{ position: 'absolute', left: 92, top: 600, opacity: lin(localFrame, [16, 32], [0, 1]) }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 20, fontWeight: 800, letterSpacing: 2,
          color: red, border: `2px solid ${red}`, borderRadius: 8, padding: '4px 12px',
          background: `rgba(255,59,92,${(0.08 + 0.18 * alarmPulse).toFixed(3)})`,
          boxShadow: blindOn ? `0 0 ${10 + 16 * alarmPulse}px ${red}99` : 'none' }}>
          ⚠ NO INSTRUMENTS
        </span>
      </div>

      {/* big question readout (top-left) */}
      <div style={{ position: 'absolute', left: 70, top: 120, width: 440, opacity: lin(localFrame, [8, 26], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 22, letterSpacing: 3, color: 'rgba(245,247,255,0.55)',
          textTransform: 'uppercase', marginBottom: 8 }}>did it improve?</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 78, fontWeight: 800, lineHeight: 1, letterSpacing: -2,
          color: blindOn ? red : white, textShadow: blindOn ? `0 0 30px ${red}cc` : `0 0 20px ${rose}55` }}>
          ?
        </div>
        <div style={{ marginTop: 10, fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 700,
          color: blindOn ? red : rose, opacity: lin(localFrame, [22, 40], [0, 1]) }}>
          {blindOn ? 'silently worse' : 'no way to tell'}
        </div>
      </div>

      {/* lower caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 26, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white, letterSpacing: 0.5 }}>
          You shipped it{' '}
          <span style={{ color: red, textShadow: `0 0 22px ${red}99` }}>flying blind.</span>
        </span>
      </div>
    </div>
  );
};
