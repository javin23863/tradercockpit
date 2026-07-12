import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #5 (persistent memory) — beat: "Context survives. The agent compounds instead of resetting."
 *
 * CONCEPT: two timelines drawn across the same session axis. The RED "RESETTING" line is a sawtooth —
 * it climbs within a session then DROPS back to zero at every session boundary (a broken continuity line).
 * The GREEN "COMPOUNDING" line is a rising STAIRCASE — it carries its level across each boundary and keeps
 * climbing (a continuous line). On the spoken "survives/compounds", a "CONTEXT SURVIVES" seal stamps and the
 * green line pulls decisively above the red. Same agent, two fates: reset vs compound.
 *
 * NOVELTY (vs ledger): NEW family — a dual continuity timeline (broken sawtooth vs compounding staircase)
 * drawn over a session axis, with a stamping CONTEXT-SURVIVES seal. (No torrent/core/tank, no cache-vault,
 * no twin-cost-bars/delta-bracket — this is a line-chart continuity story, not bars.)
 *
 * RENDER-SAFE: react + remotion only. No useCurrentFrame/AbsoluteFill/three. No Math.random/Date.now.
 * Strictly-increasing interpolate ranges (prop ends guarded). Manual number formatting. 1080x820.
 */
export const SceneProof: React.FC<{
  localFrame: number; tS: number; fps: number; beatDur: number;
  accentA: string; accentB: string;
  words: { w: string; startS: number; endS: number }[];
}> = ({ localFrame, tS, fps, beatDur, accentA, accentB, words }) => {
  const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v));
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
  const lin = (v: number, inR: number[], outR: number[]) =>
    interpolate(v, inR, outR, { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const wordStart = (sub: string) => { const w = words.find((x) => x.w.toLowerCase().includes(sub)); return w ? w.startS : null; };

  const violet = accentA;
  const amber = accentB;
  const white = '#F5F7FF';
  const red = '#FF3B5C';
  const green = '#34F5A0';

  // narration sync — stamp the seal on "survives" or "compounds"
  const survivesAt = wordStart('surviv') ?? wordStart('compound') ?? null;
  const sealT = survivesAt != null ? clamp(lin(tS - survivesAt, [0, 0.34], [0, 1])) : clamp(lin(localFrame, [60, 76], [0, 1]));

  // ---- chart geometry (within 1080x820) ----
  const chartX = 150, chartY = 250, chartW = 780, chartH = 320;
  const baseY = chartY + chartH;      // y at level 0
  const topY = chartY;                // y at level max
  const SESSIONS = 5;
  const segW = chartW / SESSIONS;

  // animated draw progress across the 5 sessions
  const drawn = clamp(lin(localFrame, [10, 56], [0, SESSIONS])); // how many session-segments are drawn

  const yFor = (level: number) => lerp(baseY, topY, clamp(level)); // level 0..1 -> y

  // Build the RED resetting (sawtooth) and GREEN compounding (staircase) point lists.
  // Each session s spans x in [chartX + s*segW, chartX + (s+1)*segW].
  // RED: rises from 0 to ~0.55 within a session, then drops to 0 at the boundary.
  // GREEN: rises from prevLevel to prevLevel + step, carries the level forward.
  const redPts: { x: number; y: number }[] = [];
  const greenPts: { x: number; y: number }[] = [];
  for (let s = 0; s < SESSIONS; s++) {
    const segDrawn = clamp(drawn - s); // 0..1 how much of this segment is drawn
    if (segDrawn <= 0) break;
    const x0 = chartX + s * segW;
    const innerSteps = 12;
    const greenStart = s / SESSIONS * 0.92;            // compounding base climbs per session
    const greenEnd = (s + 1) / SESSIONS * 0.92;
    for (let k = 0; k <= innerSteps; k++) {
      const tt = (k / innerSteps);
      if (tt > segDrawn + 0.0001) break;
      const x = x0 + tt * segW;
      // RED sawtooth: up within the session then sharp drop near the end
      const redLevel = tt < 0.82 ? lin(tt, [0, 0.82], [0.04, 0.5]) : lin(tt, [0.82, 1], [0.5, 0.03]);
      redPts.push({ x, y: yFor(redLevel) });
      // GREEN staircase: smooth climb that carries forward (no drop)
      const greenLevel = lerp(greenStart, greenEnd, tt);
      greenPts.push({ x, y: yFor(greenLevel) });
    }
  }
  const toPath = (pts: { x: number; y: number }[]) =>
    pts.length ? 'M ' + pts.map((p) => `${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' L ') : '';
  const redPath = toPath(redPts);
  const greenPath = toPath(greenPts);
  const greenHead = greenPts.length ? greenPts[greenPts.length - 1] : { x: chartX, y: baseY };
  const redHead = redPts.length ? redPts[redPts.length - 1] : { x: chartX, y: baseY };

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);
  const sealPop = spring({ frame: Math.max(0, Math.round((sealT) * 14)), fps, config: { damping: 11 } });

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      <div style={{ position: 'absolute', left: 540 - 380, top: 200, width: 760, height: 540, borderRadius: 400,
        background: `radial-gradient(circle at 50% 55%, ${green}16, transparent 66%)`, filter: 'blur(48px)' }} />

      {/* eyebrow */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 100, textAlign: 'center', opacity: lin(localFrame, [4, 20], [0, 1]),
        fontFamily: 'Consolas, monospace', fontSize: 24, letterSpacing: 6, color: 'rgba(245,247,255,0.6)', textTransform: 'uppercase' }}>
        capability across sessions
      </div>

      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="pf5-green" x1="0" y1="1" x2="1" y2="0">
            <stop offset="0%" stopColor={green} stopOpacity={0.9} />
            <stop offset="100%" stopColor={amber} stopOpacity={0.95} />
          </linearGradient>
        </defs>

        {/* baseline + session gridlines */}
        <line x1={chartX} y1={baseY} x2={chartX + chartW} y2={baseY} stroke="rgba(245,247,255,0.28)" strokeWidth={2} />
        {Array.from({ length: SESSIONS + 1 }).map((_, i) => (
          <line key={`gl-${i}`} x1={chartX + i * segW} y1={chartY - 6} x2={chartX + i * segW} y2={baseY}
            stroke="rgba(245,247,255,0.10)" strokeWidth={1.5} strokeDasharray="3 8" />
        ))}
        {/* session labels */}
        {Array.from({ length: SESSIONS }).map((_, i) => (
          <text key={`sl-${i}`} x={chartX + i * segW + segW / 2} y={baseY + 28} textAnchor="middle"
            fontFamily="Consolas, monospace" fontSize={15} fill="rgba(245,247,255,0.45)">
            {`S${i + 1}`}
          </text>
        ))}

        {/* RED resetting line (sawtooth — drops to zero each session) */}
        {redPath && <path d={redPath} fill="none" stroke={red} strokeWidth={4} strokeLinejoin="round"
          opacity={0.85} style={{ filter: `drop-shadow(0 0 6px ${red}88)` }} />}
        {redPts.length > 0 && <circle cx={redHead.x} cy={redHead.y} r={6} fill={red} />}

        {/* GREEN compounding line (staircase — carries forward) */}
        {greenPath && <path d={greenPath} fill="none" stroke="url(#pf5-green)" strokeWidth={6} strokeLinejoin="round"
          strokeLinecap="round" style={{ filter: `drop-shadow(0 0 10px ${green}aa)` }} />}
        {greenPts.length > 0 && (
          <>
            <circle cx={greenHead.x} cy={greenHead.y} r={9 + 3 * Math.sin(localFrame / 6)} fill="none" stroke={green} strokeWidth={2} opacity={0.6} />
            <circle cx={greenHead.x} cy={greenHead.y} r={7} fill={green} style={{ filter: `drop-shadow(0 0 8px ${green})` }} />
          </>
        )}
      </svg>

      {/* line legends near their heads */}
      <div style={{ position: 'absolute', left: Math.min(940, redHead.x + 14), top: redHead.y - 36, opacity: lin(localFrame, [30, 46], [0, 1]) }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 19, fontWeight: 700, color: red, textShadow: `0 0 12px ${red}88` }}>RESETTING ↓</span>
      </div>
      <div style={{ position: 'absolute', left: Math.min(900, greenHead.x + 14), top: greenHead.y - 14, opacity: lin(localFrame, [30, 46], [0, 1]) }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 21, fontWeight: 800, color: green, textShadow: `0 0 14px ${green}aa` }}>COMPOUNDING ↑</span>
      </div>

      {/* CONTEXT SURVIVES seal (stamps on the spoken word) */}
      {sealT > 0.01 && (
        <div style={{ position: 'absolute', left: 540 - 175, top: chartY - 16, width: 350, textAlign: 'center',
          transform: `scale(${lerp(0.6, 1, sealPop)}) rotate(-7deg)`, opacity: clamp(sealT * 1.4) }}>
          <span style={{ fontFamily: 'Consolas, monospace', fontSize: 34, fontWeight: 800, color: green,
            textShadow: `0 0 20px ${green}cc`, border: `4px solid ${green}`, borderRadius: 14, padding: '8px 22px',
            background: 'rgba(8,18,14,0.7)', display: 'inline-block', letterSpacing: 1 }}>
            CONTEXT SURVIVES
          </span>
        </div>
      )}

      {/* caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 28, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white }}>
          It compounds{' '}
          <span style={{ color: green, textShadow: `0 0 22px ${green}99` }}>instead of resetting.</span>
        </span>
      </div>
    </div>
  );
};
