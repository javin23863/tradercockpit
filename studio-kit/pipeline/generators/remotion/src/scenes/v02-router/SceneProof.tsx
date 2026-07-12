import React from 'react';
import { interpolate, spring, Easing } from 'remotion';

/**
 * VIDEO #2 — SceneProof  (complexity level 2)
 * Beat narration: "Same quality. Sixty percent lower bill."
 *
 * DEVICE: BEFORE vs AFTER cost comparison — two liquid-filled "bill" bars on a
 * keynote pedestal. The BEFORE bar fills tall; the AFTER bar liquid-DRAINS to 40%
 * height as a huge accent "-60%" slab SLAMS in (physics overshoot + impact shockwave).
 * A QUALITY meter (held 100 + checkmark, two quality marks) stays pinned — quality unchanged.
 *
 * Deliberately shares NOTHING with video #1's SceneProof (chunk-card reorder stack +
 * radial faithfulness gauge + orbiting ticks + relevance bars). New technique families:
 * liquid/fill, bar-race, currency particle-system, physics-ish slam with shockwave, perspective floor.
 *
 * >= 6 synchronized, staged layers:
 *   L1 perspective floor grid + ambient floor glow (depth)
 *   L2 dual pedestals + center divider wipe (scaffold arrival)
 *   L3 BEFORE liquid bill-bar fills (rising liquid + meniscus wobble)
 *   L4 AFTER liquid bill-bar DRAINS to 40% on "sixty" (bar-race / liquid drain)
 *   L5 held QUALITY meter (100 + check + twin quality marks) — pinned, alive
 *   L6 "-60%" hero slab SLAM + impact shockwave ring + screen shake
 *   L7 currency particle-system (coins rise from BEFORE, droplets drain from AFTER)
 *   L8 savings delta bracket connecting bar tops + "LOWER BILL" caption
 */

export const SceneProof: React.FC<{
  localFrame: number;   // 0 at this beat's start (entrance timing)
  tS: number;           // ABSOLUTE comp time in seconds; compare to words[k].startS to know what has been SAID
  fps: number;
  beatDur: number;      // this beat's length in frames
  accentA: string;
  accentB: string;
  words: { w: string; startS: number; endS: number }[]; // THIS beat's words with ABSOLUTE start/end seconds
}> = ({ localFrame, tS, fps, beatDur, accentA, accentB, words }) => {
  // ---------------- helpers ----------------
  const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
  const fract = (x: number) => x - Math.floor(x);
  const rnd = (i: number) => fract(Math.sin(i * 12.9898) * 43758.5453);
  const t = localFrame / fps;

  // word-sync: absolute start of a spoken substring (null if not present this beat)
  const wordTime = (sub: string): number | null => {
    const w = words.find((x) => x.w.toLowerCase().includes(sub.toLowerCase()));
    return w ? w.startS : null;
  };

  // ---- narration anchors ----
  // "Same quality."  -> quality meter pins
  // "Sixty percent"  -> after-bar drains + -60% slab slams
  // "lower bill"     -> savings bracket + caption resolve
  const tQuality = (() => {
    const w = wordTime('qual') ?? wordTime('same');
    return w != null ? w : (words[0]?.startS ?? tS);
  })();
  const tSixty = (() => {
    const w = wordTime('sixty') ?? wordTime('60') ?? wordTime('percent');
    return w != null ? w : tQuality + 1.1;
  })();
  const tBill = (() => {
    const w = wordTime('bill') ?? wordTime('lower');
    return w != null ? w : tSixty + 0.9;
  })();

  // ---------------- palette ----------------
  const white = '#F5F7FF';
  const subWhite = 'rgba(245,247,255,0.60)';
  const dark = 'rgba(8,6,18,0.72)';
  const gBefore = 'sp2-grad-before';
  const gAfter = 'sp2-grad-after';
  const gAccent = 'sp2-grad-accent';
  const gQual = 'sp2-grad-qual';
  const glowId = 'sp2-glow';
  const glowSoft = 'sp2-glow-soft';

  // ---------------- master entrance ----------------
  const ent = spring({ frame: localFrame, fps, config: { damping: 18, mass: 0.9, stiffness: 120 } });
  const breathe = 0.5 + 0.5 * Math.sin(t * 1.15);

  // =========================================================
  // GEOMETRY — bars sit on a pedestal in the lower-center
  // =========================================================
  const baseY = 668;            // pedestal top (bars grow up from here)
  const barW = 168;
  const barMaxH = 360;          // full BEFORE height (kept clear of the QUALITY pill above)
  const beforeX = 226;          // left bar left-edge
  const afterX = 686;           // right bar left-edge (mirrored around center 540)

  // BEFORE bar liquid fills 0->full early (staged arrival, before "sixty")
  const fillRaw = interpolate(localFrame, [10, 40], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const fillP = Easing.out(Easing.cubic)(fillRaw);
  const beforeH = barMaxH * fillP;

  // AFTER bar starts matched to BEFORE, then DRAINS to 40% when "sixty" is spoken
  const drainRaw = clamp((tS - tSixty) / 0.85, 0, 1);
  const drainP = Easing.inOut(Easing.cubic)(drainRaw);
  const afterFrac = lerp(1, 0.4, drainP);             // 1.0 -> 0.40 height
  const afterH = barMaxH * fillP * afterFrac;

  // liquid meniscus wobble (alive)
  const wob = (phase: number) => Math.sin(t * 3.0 + phase) * 3.2;

  // =========================================================
  // SLAM — "-60%" slab punches in on "sixty" with physics overshoot
  // =========================================================
  const slamSpring = spring({
    frame: Math.round((tS - tSixty) * fps),
    fps,
    config: { damping: 9, mass: 1.1, stiffness: 180 },
  });
  const slamIn = (tS >= tSixty) ? slamSpring : 0;
  // impact moment = first frame after slam roughly lands
  const impactRaw = clamp((tS - (tSixty + 0.12)) / 0.5, 0, 1);
  const shock = Easing.out(Easing.cubic)(impactRaw);        // 0->1 shockwave expand
  // screen shake decays after impact
  const sinceImpact = clamp(tS - (tSixty + 0.1), 0, 1);
  const shakeAmp = (tS >= tSixty + 0.1) ? Math.exp(-sinceImpact * 9) * 9 : 0;
  const shakeX = Math.sin(t * 60) * shakeAmp;
  const shakeY = Math.cos(t * 54) * shakeAmp * 0.7;

  // =========================================================
  // QUALITY meter — pins to 100 on "Same quality", holds forever
  // =========================================================
  const qPin = clamp((tS - tQuality) / 0.5, 0, 1);
  const qEase = Easing.out(Easing.cubic)(qPin);
  const qCheck = clamp((tS - (tQuality + 0.25)) / 0.4, 0, 1);
  const qPulse = (qPin > 0.99) ? 0.5 + 0.5 * Math.sin(t * 3.2) : 0;

  // savings bracket + caption resolve on "lower bill"
  const billP = clamp((tS - tBill) / 0.6, 0, 1);
  const billE = Easing.out(Easing.cubic)(billP);

  // bar-top y coords (for the savings bracket)
  const beforeTopY = baseY - beforeH;
  const afterTopY = baseY - afterH;

  return (
    <div style={{ position: 'absolute', inset: 0 }}>
      {/* ---------- SVG defs ---------- */}
      <svg width="0" height="0" style={{ position: 'absolute' }}>
        <defs>
          <linearGradient id={gBefore} x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="rgba(245,247,255,0.10)" />
            <stop offset="100%" stopColor="rgba(245,247,255,0.34)" />
          </linearGradient>
          <linearGradient id={gAfter} x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor={accentA} />
            <stop offset="100%" stopColor={accentB} />
          </linearGradient>
          <linearGradient id={gAccent} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={accentA} />
            <stop offset="100%" stopColor={accentB} />
          </linearGradient>
          <linearGradient id={gQual} x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#34D399" />
            <stop offset="100%" stopColor={accentB} />
          </linearGradient>
          <filter id={glowId} x="-80%" y="-80%" width="260%" height="260%">
            <feGaussianBlur stdDeviation="7" result="b" />
            <feMerge>
              <feMergeNode in="b" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id={glowSoft} x="-120%" y="-120%" width="340%" height="340%">
            <feGaussianBlur stdDeviation="16" />
          </filter>
        </defs>
      </svg>

      {/* =========================================================
          L1 — perspective floor grid + ambient floor glow (depth)
      ========================================================= */}
      <svg
        width="1080"
        height="820"
        viewBox="0 0 1080 820"
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          opacity: 0.5 * ent,
          transform: `translate(${shakeX * 0.3}px, ${shakeY * 0.3}px)`,
        }}
      >
        {/* receding horizontal floor lines below the pedestal */}
        {[0, 1, 2, 3, 4, 5].map((k) => {
          const f = k / 5;
          const y = baseY + 14 + f * f * 118;
          const inset = 220 * f;
          const op = (1 - f) * 0.22 * ent;
          return (
            <line
              key={`fl-${k}`}
              x1={120 + inset}
              y1={y}
              x2={960 - inset}
              y2={y}
              stroke={white}
              strokeWidth={1.2}
              opacity={op}
            />
          );
        })}
        {/* converging verticals */}
        {[-3, -2, -1, 0, 1, 2, 3].map((k) => {
          const x0 = 540 + k * 130;
          const x1 = 540 + k * 36;
          const op = (1 - Math.abs(k) / 4) * 0.16 * ent;
          return (
            <line
              key={`fv-${k}`}
              x1={x0}
              y1={baseY + 14}
              x2={x1}
              y2={baseY + 138}
              stroke={white}
              strokeWidth={1.1}
              opacity={op}
            />
          );
        })}
        {/* soft floor glow puddle under each bar */}
        <ellipse cx={beforeX + barW / 2} cy={baseY + 22} rx={150} ry={26}
          fill={white} opacity={0.06 * ent} filter={`url(#${glowSoft})`} />
        <ellipse cx={afterX + barW / 2} cy={baseY + 22} rx={150} ry={26}
          fill={accentB} opacity={(0.05 + 0.12 * drainP) * ent} filter={`url(#${glowSoft})`} />
      </svg>

      {/* everything that shakes together lives in this group */}
      <div style={{ position: 'absolute', inset: 0, transform: `translate(${shakeX}px, ${shakeY}px)` }}>

        {/* =========================================================
            L8a — section eyebrow
        ========================================================= */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: 36,
            textAlign: 'center',
            opacity: clamp(ent, 0, 1),
            transform: `translateY(${(1 - ent) * -12}px)`,
            fontFamily: 'Consolas, ui-monospace, monospace',
            fontSize: 24,
            letterSpacing: 8,
            color: subWhite,
            textTransform: 'uppercase',
          }}
        >
          monthly cost
        </div>

        {/* =========================================================
            L2 — dual pedestals + center divider wipe
        ========================================================= */}
        <svg width="1080" height="820" viewBox="0 0 1080 820"
          style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
          {/* pedestal slab under both bars */}
          {[beforeX, afterX].map((bx, i) => {
            const pedEnt = spring({ frame: localFrame - 4 - i * 3, fps, config: { damping: 16, stiffness: 130 } });
            const pw = barW + 56;
            return (
              <g key={`ped-${i}`} opacity={clamp(pedEnt, 0, 1)}>
                <rect x={bx - 28} y={baseY} width={pw} height={14} rx={5}
                  fill={dark} stroke="rgba(255,255,255,0.18)" strokeWidth={1.5} />
                <rect x={bx - 28} y={baseY} width={pw} height={3} rx={2}
                  fill="rgba(255,255,255,0.35)" />
              </g>
            );
          })}
          {/* center divider — vertical wipe-in line separating BEFORE | AFTER */}
          {(() => {
            const dvP = Easing.out(Easing.cubic)(clamp((localFrame - 8) / 22, 0, 1));
            const yTop = 96;
            const yBot = baseY + 8;
            const yNow = lerp(yTop, yBot, dvP);
            return (
              <g opacity={0.5}>
                <line x1={540} y1={yTop} x2={540} y2={yNow}
                  stroke={`url(#${gAccent})`} strokeWidth={2} strokeDasharray="2 9"
                  strokeLinecap="round" opacity={0.7} />
                <circle cx={540} cy={yNow} r={3.5} fill={white} filter={`url(#${glowId})`} opacity={dvP} />
              </g>
            );
          })()}
        </svg>

        {/* =========================================================
            L3 — BEFORE liquid bill-bar (left)
        ========================================================= */}
        {(() => {
          const topY = baseY - beforeH;
          const mw = wob(0.0);
          const labelEnt = spring({ frame: localFrame - 6, fps, config: { damping: 17, stiffness: 120 } });
          return (
            <div style={{ position: 'absolute', inset: 0 }}>
              {/* bar shell (dark backing) */}
              <div
                style={{
                  position: 'absolute',
                  left: beforeX,
                  top: baseY - barMaxH,
                  width: barW,
                  height: barMaxH,
                  borderRadius: 16,
                  background: 'rgba(8,6,18,0.45)',
                  border: '1.5px dashed rgba(255,255,255,0.18)',
                  opacity: clamp(ent, 0, 1),
                }}
              />
              {/* liquid fill */}
              <svg width="1080" height="820" viewBox="0 0 1080 820"
                style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
                {beforeH > 4 && (
                  <g>
                    <path
                      d={`M ${beforeX} ${baseY}
                          L ${beforeX} ${topY + 8 + mw}
                          Q ${beforeX + barW * 0.25} ${topY + mw} ${beforeX + barW * 0.5} ${topY + 5 + mw}
                          Q ${beforeX + barW * 0.75} ${topY + 10 + mw} ${beforeX + barW} ${topY + 4 - mw}
                          L ${beforeX + barW} ${baseY} Z`}
                      fill={`url(#${gBefore})`}
                      stroke="rgba(255,255,255,0.30)"
                      strokeWidth={2}
                    />
                    {/* meniscus highlight */}
                    <path
                      d={`M ${beforeX + 4} ${topY + 6 + mw}
                          Q ${beforeX + barW * 0.5} ${topY + mw} ${beforeX + barW - 4} ${topY + 5 - mw}`}
                      fill="none" stroke="rgba(255,255,255,0.55)" strokeWidth={2.5} strokeLinecap="round"
                    />
                  </g>
                )}
              </svg>
              {/* BEFORE label */}
              <div
                style={{
                  position: 'absolute',
                  left: beforeX - 28,
                  top: baseY + 26,
                  width: barW + 56,
                  textAlign: 'center',
                  opacity: clamp(labelEnt, 0, 1),
                  fontFamily: 'Consolas, monospace',
                  fontSize: 30,
                  letterSpacing: 6,
                  color: subWhite,
                  fontWeight: 700,
                }}
              >
                BEFORE
              </div>
              {/* $ amount riding the bar top */}
              <div
                style={{
                  position: 'absolute',
                  left: beforeX - 28,
                  top: topY - 56,
                  width: barW + 56,
                  textAlign: 'center',
                  opacity: clamp(fillP * 1.2, 0, 1),
                  fontFamily: 'Consolas, monospace',
                  fontSize: 40,
                  fontWeight: 800,
                  color: white,
                  textShadow: '0 2px 18px rgba(0,0,0,0.6)',
                }}
              >
                ${Math.round(lerp(0, 1000, fillP))}
              </div>
            </div>
          );
        })()}

        {/* =========================================================
            L4 — AFTER liquid bill-bar (right) — DRAINS to 40%
        ========================================================= */}
        {(() => {
          const topY = baseY - afterH;
          const mw = wob(1.6);
          const labelEnt = spring({ frame: localFrame - 9, fps, config: { damping: 17, stiffness: 120 } });
          // ghost outline of original (pre-drain) height to show what was removed
          const ghostTop = baseY - barMaxH * fillP;
          return (
            <div style={{ position: 'absolute', inset: 0 }}>
              {/* bar shell */}
              <div
                style={{
                  position: 'absolute',
                  left: afterX,
                  top: baseY - barMaxH,
                  width: barW,
                  height: barMaxH,
                  borderRadius: 16,
                  background: 'rgba(8,6,18,0.45)',
                  border: '1.5px dashed rgba(255,255,255,0.18)',
                  opacity: clamp(ent, 0, 1),
                }}
              />
              {/* drained-away zone (between ghostTop and current top) — faded accent */}
              <svg width="1080" height="820" viewBox="0 0 1080 820"
                style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
                {drainP > 0.02 && (
                  <rect
                    x={afterX + 2}
                    y={ghostTop}
                    width={barW - 4}
                    height={Math.max(0, topY - ghostTop)}
                    fill={accentB}
                    opacity={0.10 * drainP}
                  />
                )}
                {/* liquid fill (current) */}
                {afterH > 4 && (
                  <g filter={`url(#${glowId})`}>
                    <path
                      d={`M ${afterX} ${baseY}
                          L ${afterX} ${topY + 8 + mw}
                          Q ${afterX + barW * 0.25} ${topY + mw} ${afterX + barW * 0.5} ${topY + 5 + mw}
                          Q ${afterX + barW * 0.75} ${topY + 10 + mw} ${afterX + barW} ${topY + 4 - mw}
                          L ${afterX + barW} ${baseY} Z`}
                      fill={`url(#${gAfter})`}
                      stroke={accentB}
                      strokeWidth={2.5}
                      opacity={0.95}
                    />
                    <path
                      d={`M ${afterX + 4} ${topY + 6 + mw}
                          Q ${afterX + barW * 0.5} ${topY + mw} ${afterX + barW - 4} ${topY + 5 - mw}`}
                      fill="none" stroke="rgba(255,255,255,0.85)" strokeWidth={2.5} strokeLinecap="round"
                    />
                  </g>
                )}
                {/* 40% gridline marker that appears as it lands */}
                {drainP > 0.5 && (
                  <g opacity={clamp((drainP - 0.5) / 0.5, 0, 1)}>
                    <line x1={afterX - 14} y1={baseY - barMaxH * fillP * 0.4}
                      x2={afterX + barW + 14} y2={baseY - barMaxH * fillP * 0.4}
                      stroke={accentB} strokeWidth={2} strokeDasharray="6 6" opacity={0.7} />
                  </g>
                )}
              </svg>
              {/* AFTER label */}
              <div
                style={{
                  position: 'absolute',
                  left: afterX - 28,
                  top: baseY + 26,
                  width: barW + 56,
                  textAlign: 'center',
                  opacity: clamp(labelEnt, 0, 1),
                  fontFamily: 'Consolas, monospace',
                  fontSize: 30,
                  letterSpacing: 6,
                  color: accentB,
                  fontWeight: 800,
                  textShadow: `0 0 18px ${accentB}66`,
                }}
              >
                AFTER
              </div>
              {/* $ amount counting DOWN as it drains */}
              <div
                style={{
                  position: 'absolute',
                  left: afterX - 28,
                  top: topY - 56,
                  width: barW + 56,
                  textAlign: 'center',
                  opacity: clamp(fillP * 1.2, 0, 1),
                  fontFamily: 'Consolas, monospace',
                  fontSize: 40,
                  fontWeight: 800,
                  color: accentB,
                  textShadow: `0 2px 18px rgba(0,0,0,0.6), 0 0 22px ${accentB}55`,
                }}
              >
                ${Math.round(lerp(1000, 400, drainP))}
              </div>
            </div>
          );
        })()}

        {/* =========================================================
            L7 — currency particle-system
            coins rise off BEFORE bar; droplets shed off AFTER as it drains
        ========================================================= */}
        <svg width="1080" height="820" viewBox="0 0 1080 820"
          style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
          {/* rising coins from BEFORE (cost accumulating) */}
          {Array.from({ length: 9 }).map((_, k) => {
            const seed = rnd(k + 3);
            const seed2 = rnd(k + 21);
            const period = 2.2 + seed * 1.4;
            const ph = fract((t + seed * period) / period); // 0..1 loop
            const x = beforeX + 18 + seed2 * (barW - 36) + Math.sin(t * 1.4 + k) * 6;
            const yStart = baseY - beforeH - 6;
            const y = yStart - ph * 120;
            const op = fillP * (1 - ph) * 0.7 * (beforeH > 30 ? 1 : 0);
            const r = 6 + seed * 4;
            return (
              <g key={`coin-${k}`} opacity={op} transform={`translate(${x} ${y})`}>
                <circle r={r} fill="none" stroke="rgba(245,247,255,0.7)" strokeWidth={1.6} />
                <text x={0} y={r * 0.35} textAnchor="middle"
                  fontFamily="Consolas, monospace" fontSize={r * 1.1} fill="rgba(245,247,255,0.85)">$</text>
              </g>
            );
          })}
          {/* draining droplets from AFTER (cost leaving) — only during/after the drain */}
          {drainP > 0.02 && Array.from({ length: 11 }).map((_, k) => {
            const seed = rnd(k + 40);
            const seed2 = rnd(k + 60);
            const period = 1.2 + seed * 1.0;
            const tt = Math.max(0, tS - tSixty);
            const ph = fract((tt + seed * period) / period);
            const x = afterX + 16 + seed2 * (barW - 32);
            const y = (baseY - afterH) + ph * (afterH + 60) * 0.7 + 4;
            const op = drainP * (1 - ph) * 0.85;
            const r = 3 + seed * 3;
            return (
              <g key={`drop-${k}`} opacity={op} transform={`translate(${x} ${y})`}>
                <circle r={r} fill={accentB} opacity={0.85} />
                <circle r={r * 0.4} cx={-r * 0.25} cy={-r * 0.25} fill="rgba(255,255,255,0.7)" />
              </g>
            );
          })}
        </svg>

        {/* =========================================================
            L8b — savings delta bracket connecting bar tops + caption
        ========================================================= */}
        <svg width="1080" height="820" viewBox="0 0 1080 820"
          style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
          {billE > 0.01 && beforeH > 30 && (
            <g opacity={billE}>
              {/* horizontal guide at BEFORE top, dropping to AFTER top */}
              <line x1={beforeX + barW + 8} y1={beforeTopY}
                x2={afterX - 8} y2={beforeTopY}
                stroke={accentA} strokeWidth={2} strokeDasharray="5 7" opacity={0.45} />
              {/* the vertical "saved" span on the AFTER side */}
              <line x1={afterX - 8} y1={beforeTopY} x2={afterX - 8} y2={afterTopY}
                stroke={`url(#${gAccent})`} strokeWidth={3.5} strokeLinecap="round" />
              <path d={`M ${afterX - 14} ${beforeTopY + 8} L ${afterX - 8} ${beforeTopY} L ${afterX - 2} ${beforeTopY + 8}`}
                fill="none" stroke={accentA} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
              <path d={`M ${afterX - 14} ${afterTopY - 8} L ${afterX - 8} ${afterTopY} L ${afterX - 2} ${afterTopY - 8}`}
                fill="none" stroke={accentB} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
            </g>
          )}
        </svg>

        {/* =========================================================
            L5 — QUALITY meter (held 100 + check + twin quality marks)
            Pinned top-center region; UNCHANGED throughout.
        ========================================================= */}
        {(() => {
          const qx = 540;          // center
          const qy = 150;
          const qEnt = spring({ frame: localFrame - 12, fps, config: { damping: 16, stiffness: 120 } });
          const appear = clamp(qEnt, 0, 1) * clamp(0.25 + qEase, 0, 1);
          return (
            <div
              style={{
                position: 'absolute',
                left: qx - 200,
                top: qy - 64,
                width: 400,
                height: 128,
                opacity: appear,
                transform: `translateY(${(1 - qEnt) * -16}px) scale(${1 + qPulse * 0.01})`,
              }}
            >
              {/* backing pill */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  borderRadius: 22,
                  background: dark,
                  border: '1.5px solid rgba(255,255,255,0.16)',
                  boxShadow: `0 10px 36px rgba(0,0,0,0.4), 0 0 ${22 + qPulse * 26}px rgba(52,211,153,${0.10 + qPulse * 0.18})`,
                }}
              />
              {/* lit top edge */}
              <div style={{
                position: 'absolute', top: 0, left: 24, right: 24, height: 1,
                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)',
              }} />
              {/* label */}
              <div style={{
                position: 'absolute', left: 28, top: 20,
                fontFamily: 'Consolas, monospace', fontSize: 22, letterSpacing: 5,
                color: subWhite, textTransform: 'uppercase',
              }}>
                quality
              </div>
              {/* twin quality marks (===) — "two side-by-side quality marks" */}
              <div style={{ position: 'absolute', left: 28, top: 64, display: 'flex', gap: 10 }}>
                {[0, 1].map((m) => (
                  <div key={m} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {[0, 1, 2].map((r) => (
                      <div key={r} style={{
                        width: 30, height: 5, borderRadius: 3,
                        backgroundColor: '#34D399',
                        opacity: 0.85,
                      }} />
                    ))}
                  </div>
                ))}
              </div>
              {/* held 100 */}
              <div style={{
                position: 'absolute', right: 92, top: 30,
                fontFamily: 'Consolas, monospace', fontWeight: 800, fontSize: 64, lineHeight: 1,
                color: white,
                textShadow: `0 0 ${10 + qPulse * 16}px rgba(52,211,153,${0.3 + qPulse * 0.3})`,
              }}>
                100<span style={{ fontSize: 30 }}>%</span>
              </div>
              {/* check badge */}
              <svg width="56" height="56" viewBox="0 0 56 56"
                style={{ position: 'absolute', right: 24, top: 34, opacity: qCheck, transform: `scale(${0.6 + qCheck * 0.4})` }}>
                <circle cx="28" cy="28" r="24" fill="none" stroke={`url(#${gQual})`} strokeWidth="3" />
                <path d="M17 28.5 L25 36 L40 19"
                  fill="none" stroke={`url(#${gQual})`} strokeWidth="4.4"
                  strokeLinecap="round" strokeLinejoin="round"
                  style={{ strokeDasharray: 48, strokeDashoffset: 48 * (1 - clamp((qCheck - 0.15) / 0.7, 0, 1)) }} />
              </svg>
              {/* "unchanged" sub */}
              <div style={{
                position: 'absolute', left: 28, bottom: -30,
                fontFamily: 'Consolas, monospace', fontSize: 19, letterSpacing: 3,
                color: '#34D399', opacity: 0.85 * clamp((qCheck - 0.3) / 0.5, 0, 1),
              }}>
                UNCHANGED
              </div>
            </div>
          );
        })()}

        {/* =========================================================
            L6 — "-60%" hero slab SLAM + impact shockwave ring
        ========================================================= */}
        {(() => {
          if (tS < tSixty - 0.05) return null;
          const sx = 540;
          const sy = 430;
          // slam: comes from above + scales down with spring overshoot
          const enterY = lerp(-120, 0, clamp(slamIn, 0, 1.4));
          const sc = 0.6 + clamp(slamIn, 0, 1.2) * 0.42;
          const tilt = (1 - clamp(slamIn, 0, 1)) * -6;
          return (
            <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
              {/* impact shockwave ring (radii clamped to stay inside the 820 box) */}
              {shock > 0.01 && shock < 0.999 && (
                <svg width="1080" height="820" viewBox="0 0 1080 820"
                  style={{ position: 'absolute', inset: 0 }}>
                  <circle cx={sx} cy={sy} r={40 + shock * 300}
                    fill="none" stroke={`url(#${gAccent})`} strokeWidth={lerp(10, 1, shock)}
                    opacity={(1 - shock) * 0.7} />
                  <circle cx={sx} cy={sy} r={20 + shock * 210}
                    fill="none" stroke={white} strokeWidth={lerp(5, 0.5, shock)}
                    opacity={(1 - shock) * 0.4} />
                </svg>
              )}
              {/* the slab */}
              <div
                style={{
                  position: 'absolute',
                  left: sx - 290,
                  top: sy - 110 + enterY,
                  width: 580,
                  height: 220,
                  transform: `scale(${sc}) rotate(${tilt}deg)`,
                  transformOrigin: 'center',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {/* slab glow halo */}
                <div style={{
                  position: 'absolute', inset: -20, borderRadius: 40,
                  background: `radial-gradient(closest-side, ${accentA}55, transparent 75%)`,
                  filter: 'blur(8px)', opacity: clamp(slamIn, 0, 1),
                }} />
                {/* hero -60% */}
                <div style={{
                  fontFamily: 'Consolas, ui-monospace, monospace',
                  fontWeight: 900,
                  fontSize: 210,
                  lineHeight: 0.9,
                  letterSpacing: -8,
                  background: `linear-gradient(135deg, ${accentA}, ${accentB})`,
                  WebkitBackgroundClip: 'text',
                  backgroundClip: 'text',
                  color: 'transparent',
                  WebkitTextFillColor: 'transparent',
                  filter: `drop-shadow(0 8px 26px rgba(0,0,0,0.55)) drop-shadow(0 0 ${24 + breathe * 18}px ${accentA}88)`,
                }}>
                  -60<span style={{ fontSize: 120 }}>%</span>
                </div>
              </div>
            </div>
          );
        })()}

        {/* =========================================================
            L8c — "LOWER BILL" resolve caption (bottom, on "bill")
        ========================================================= */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 26,
            textAlign: 'center',
            opacity: billE,
            transform: `translateY(${(1 - billE) * 14}px)`,
            fontFamily: 'Consolas, monospace',
            fontSize: 34,
            fontWeight: 800,
            letterSpacing: 6,
            color: white,
          }}
        >
          <span style={{ color: subWhite }}>SAME QUALITY &middot; </span>
          <span style={{
            background: `linear-gradient(135deg, ${accentA}, ${accentB})`,
            WebkitBackgroundClip: 'text', backgroundClip: 'text',
            color: 'transparent', WebkitTextFillColor: 'transparent',
          }}>
            LOWER BILL
          </span>
        </div>
      </div>
    </div>
  );
};
