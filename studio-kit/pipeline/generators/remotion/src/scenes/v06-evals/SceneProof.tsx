import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #6 (evals) — beat: "Regressions caught before they ship. You ship on evidence."
 *
 * CONCEPT — THE EVIDENCE GATE: two lanes lead to a SHIP gate. The TOP lane carries a REGRESSING
 * version (score 71, down arrow) that hits a RED barrier which SLAMS DOWN to block it — "BLOCKED".
 * The BOTTOM lane carries a BETTER version (score 92, up arrow) and a GREEN barrier LIFTS to let it
 * through — "SHIPPED". An "ON EVIDENCE" seal stamps on the spoken word. The eval is the gatekeeper.
 *
 * NOVELTY (vs ledger): NEW families — pass/fail gate barriers (one drops red to block, one lifts green
 * to pass), twin-lane version race with score+trend chips, an evidence seal stamp. (No twin-cost-bars,
 * no delta-bracket, no minus-90-snap, no radial gauge, no liquid columns, no tank/torrent/core.)
 *
 * RENDER-SAFE: react + remotion only. No useCurrentFrame/AbsoluteFill/three. No Math.random/Date.now.
 * Strictly-increasing interpolate ranges (prop-ends guarded). Deterministic number formatting. 1080x820.
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

  const rose = accentA;
  const mint = accentB;
  const white = '#F5F7FF';
  const red = '#FF3B5C';
  const END = Math.max(60, beatDur);

  // narration land: "evidence" -> the seal stamps
  const evidenceAt = wordStart('evidence') ?? wordStart('ship') ?? null;
  const sealed = evidenceAt != null ? tS >= evidenceAt : localFrame > 56;
  const sinceSeal = evidenceAt != null ? Math.max(0, tS - evidenceAt) : (localFrame > 56 ? (localFrame - 56) / fps : 0);

  // ---- lanes geometry ----
  const laneL = 130;            // version start x
  const gateX = 720;            // barrier x
  const topY = 290;             // regress lane
  const botY = 510;             // pass lane
  const laneR = 1000;           // ship target x

  // version travel — both glide toward the gate; the regress one stalls at the barrier
  const travel = lin(localFrame, [8, 44], [0, 1]);
  // regressing version stops just before the gate (blocked)
  const regressX = lerp(laneL, gateX - 96, clamp(travel * 1.1));
  // better version passes the gate and continues to ship
  const passX = lerp(laneL, laneR - 70, travel);

  // ---- barriers: red drops to block (top), green lifts to pass (bottom) ----
  const barrierAt = lin(localFrame, [30, 46], [0, 1]); // when barriers actuate
  const redDrop = clamp(barrierAt);                    // 0 up -> 1 down (blocking)
  const greenLift = clamp(barrierAt);                  // 0 down -> 1 up (clearing)
  // red barrier rotates DOWN into the lane; green rotates UP out of the lane
  const redAngle = lerp(-78, 0, redDrop);              // -78deg (raised) -> 0 (horizontal block)
  const greenAngle = lerp(0, -82, greenLift);          // 0 (blocking) -> -82 (lifted)

  const blockedFlash = redDrop > 0.6 ? 0.5 + 0.5 * Math.sin(localFrame / 4) : 0;

  // ---- seal stamp ----
  const sealPop = sealed ? spring({ frame: Math.max(0, localFrame - Math.round(sinceSeal * fps)), fps, config: { damping: 10 } }) : 0;

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);

  // a version puck (DOM) with score + trend
  const Puck = (x: number, y: number, label: string, score: number, up: boolean, color: string, blocked: boolean) => (
    <div style={{ position: 'absolute', left: x - 60, top: y - 38, width: 120, height: 76, borderRadius: 14,
      background: 'linear-gradient(160deg, rgba(24,18,32,0.96), rgba(12,9,20,0.96))', border: `2.5px solid ${color}`,
      boxShadow: `0 0 ${blocked ? 10 + 14 * blockedFlash : 16}px ${color}88`,
      display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
      <div style={{ fontFamily: 'Consolas, monospace', fontSize: 13, fontWeight: 800, color: white, letterSpacing: 1 }}>{label}</div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 26, fontWeight: 800, color }}>{score}</span>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 18, fontWeight: 800, color }}>{up ? '↑' : '↓'}</span>
      </div>
    </div>
  );

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* ambient wash */}
      <div style={{ position: 'absolute', left: 360, top: 160, width: 760, height: 540, borderRadius: 380,
        background: `radial-gradient(circle at 60% 50%, ${mint}16, transparent 66%)`, filter: 'blur(50px)' }} />

      {/* ===== lanes + barriers (SVG) ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        {/* lane rails */}
        {[topY, botY].map((ly, i) => (
          <line key={`rail-${i}`} x1={laneL} y1={ly} x2={i === 0 ? gateX - 20 : laneR} y2={ly}
            stroke={i === 0 ? red : mint} strokeWidth={4} strokeDasharray="3 14"
            strokeDashoffset={-localFrame * 5} opacity={lin(localFrame, [4, 22], [0, 0.6])} />
        ))}

        {/* gate posts */}
        <line x1={gateX} y1={topY - 70} x2={gateX} y2={topY + 16} stroke="rgba(245,247,255,0.4)" strokeWidth={5} />
        <line x1={gateX} y1={botY - 70} x2={gateX} y2={botY + 16} stroke="rgba(245,247,255,0.4)" strokeWidth={5} />

        {/* RED barrier (drops to block top lane) */}
        <g transform={`rotate(${redAngle} ${gateX} ${topY})`}>
          <rect x={gateX} y={topY - 7} width={120} height={14} rx={4} fill={red} opacity={0.95} />
          {/* hazard stripes */}
          {[0, 1, 2, 3].map((k) => (
            <rect key={`rs-${k}`} x={gateX + 8 + k * 28} y={topY - 7} width={12} height={14} fill="rgba(10,8,18,0.7)" />
          ))}
        </g>
        {/* GREEN barrier (lifts to clear bottom lane) */}
        <g transform={`rotate(${greenAngle} ${gateX} ${botY})`}>
          <rect x={gateX} y={botY - 7} width={120} height={14} rx={4} fill={mint} opacity={0.95} />
          {[0, 1, 2, 3].map((k) => (
            <rect key={`gs-${k}`} x={gateX + 8 + k * 28} y={botY - 7} width={12} height={14} fill="rgba(6,20,16,0.6)" />
          ))}
        </g>

        {/* ship-success trail off the green lane */}
        {greenLift > 0.5 && (
          <line x1={gateX + 30} y1={botY} x2={laneR} y2={botY} stroke={mint} strokeWidth={3}
            strokeDasharray="2 10" strokeDashoffset={-localFrame * 6} opacity={0.7} />
        )}
      </svg>

      {/* ===== version pucks ===== */}
      {Puck(regressX, topY, 'v.regress', 71, false, red, true)}
      {Puck(passX, botY, 'v.better', 92, true, mint, false)}

      {/* BLOCKED tag on top lane */}
      <div style={{ position: 'absolute', left: gateX - 30, top: topY - 118, opacity: lin(localFrame, [34, 46], [0, 1]),
        transform: `scale(${lerp(0.8, 1, redDrop)})` }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 800, letterSpacing: 2, color: red,
          border: `2px solid ${red}`, borderRadius: 8, padding: '4px 12px',
          background: `rgba(255,59,92,${(0.1 + 0.18 * blockedFlash).toFixed(3)})`,
          boxShadow: `0 0 ${10 + 14 * blockedFlash}px ${red}88` }}>✗ BLOCKED</span>
      </div>

      {/* SHIPPED tag on bottom lane */}
      <div style={{ position: 'absolute', left: laneR - 150, top: botY + 28, opacity: greenLift > 0.5 ? lin(localFrame, [40, 52], [0, 1]) : 0 }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 800, letterSpacing: 2, color: mint,
          border: `2px solid ${mint}`, borderRadius: 8, padding: '4px 12px', background: `rgba(52,245,160,0.1)`,
          boxShadow: `0 0 14px ${mint}88` }}>✓ SHIPPED</span>
      </div>

      {/* gate label */}
      <div style={{ position: 'absolute', left: gateX - 70, top: 150, width: 160, textAlign: 'center', opacity: lin(localFrame, [10, 26], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 20, fontWeight: 800, letterSpacing: 2, color: white }}>EVAL GATE</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 13, color: 'rgba(245,247,255,0.55)', marginTop: 4 }}>blocks regressions</div>
      </div>

      {/* ON EVIDENCE seal stamp (snaps on the word) */}
      <div style={{ position: 'absolute', left: 90, top: 140, width: 230, textAlign: 'center',
        opacity: sealed ? clamp(sealPop + 0.1) : 0, transform: `rotate(-9deg) scale(${0.6 + 0.5 * sealPop})` }}>
        <div style={{ border: `4px solid ${mint}`, borderRadius: 14, padding: '10px 8px',
          boxShadow: `0 0 26px ${mint}66` }}>
          <div style={{ fontFamily: 'Consolas, monospace', fontSize: 16, letterSpacing: 3, color: mint, fontWeight: 700 }}>SHIPPED</div>
          <div style={{ fontFamily: 'Consolas, monospace', fontSize: 34, fontWeight: 800, color: mint, lineHeight: 1.05,
            textShadow: `0 0 18px ${mint}aa` }}>ON<br />EVIDENCE</div>
        </div>
      </div>

      {/* caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 26, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white }}>
          Regressions blocked.{' '}
          <span style={{ color: mint, textShadow: `0 0 22px ${mint}99` }}>Ship on evidence.</span>
        </span>
      </div>
    </div>
  );
};
