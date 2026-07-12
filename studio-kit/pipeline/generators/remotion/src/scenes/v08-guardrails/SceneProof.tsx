import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #8 (guardrails) — beat: "The attack is blocked. The real request still gets through."
 *
 * CONCEPT: a split-screen VERDICT. TOP lane = THE ATTACK: the payload chip ("ignore all instructions") slams
 * into a red BLOCKED barrier, gets a ✗ and drops into a sealed QUARANTINE lock (padlock snaps). BOTTOM lane =
 * THE REAL REQUEST: a benign chip glides cleanly through a green gate, gets a ✓ check, and lands on the SYSTEM
 * CORE which lights up "RUNNING". A central THREATS BLOCKED tally ticks up and a "0 reached the model" badge
 * seals on the spoken resolution.
 *
 * NOVELTY (vs ledger — FORBIDDEN families avoided): NEW family — a two-lane BLOCKED-vs-PASSED verdict (red
 * barrier slam + quarantine padlock-seal on top, green clean pass + core-RUNNING on bottom), a threats-blocked
 * count-up tally, a "0 reached the model" seal stamp. (No twin-cost-bars, delta-bracket, pass-fail-eval-gate,
 * node-graph, conveyor, verifier-sweep, etc.)
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

  const rose = accentA;          // attack / blocked accent
  const cyan = accentB;
  const white = '#F5F7FF';
  const red = '#FF3B5C';
  const green = '#34F5A0';

  // narration land
  const blockedAt = wordStart('blocked') ?? wordStart('attack') ?? null;
  const throughAt = wordStart('through') ?? wordStart('gets') ?? null;
  const blocked = blockedAt != null ? clamp(lin(tS - blockedAt, [0, 0.4], [0, 1])) : clamp(lin(localFrame, [30, 50], [0, 1]));
  const passed = throughAt != null ? clamp(lin(tS - throughAt, [0, 0.45], [0, 1])) : clamp(lin(localFrame, [64, 86], [0, 1]));

  // stage geometry: two horizontal lanes
  const topY = 256, botY = 540;
  const laneX0 = 120, barrierX = 660, coreX = 900;

  // ---- TOP lane: attack -> red barrier -> quarantine lock ----
  const atkProg = clamp(lin(localFrame, [10, 44], [0, 1]));        // approaches the barrier
  const atkX = lerp(laneX0 + 40, barrierX - 70, atkProg);
  const slamKick = blocked > 0 ? Math.exp(-blocked * 4) : 0;       // recoil at the barrier
  const quarLock = blocked;                                        // padlock seal progress
  const atkPulse = 0.5 + 0.5 * Math.sin(localFrame / 5);

  // ---- BOTTOM lane: real request -> green gate -> core RUNNING ----
  const reqProg = clamp(lin(localFrame, [30, 78], [0, 1]));        // glides toward the core
  const reqX = lerp(laneX0 + 40, coreX - 70, reqProg);
  const coreRun = passed;
  const checkPop = spring({ frame: Math.max(0, localFrame - 70), fps, config: { damping: 12 } });

  // ---- threats-blocked tally ----
  const tallySnap = blocked > 0 ? clamp(lin((blockedAt != null ? tS - blockedAt : (localFrame - 30) / fps), [0.05, 0.4], [0, 1])) : 0;
  const threatsBlocked = blocked > 0.3 ? 1 : 0;
  const sealIn = passed > 0.6 ? clamp((passed - 0.6) / 0.4) : 0;

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      <div style={{ position: 'absolute', left: 540 - 360, top: 160, width: 720, height: 560, borderRadius: 380,
        background: `radial-gradient(circle at 50% 50%, ${cyan}16, transparent 66%)`, filter: 'blur(48px)' }} />

      {/* eyebrow */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 90, textAlign: 'center', opacity: lin(localFrame, [4, 20], [0, 1]),
        fontFamily: 'Consolas, monospace', fontSize: 24, letterSpacing: 6, color: 'rgba(245,247,255,0.6)', textTransform: 'uppercase' }}>
        same gate · two outcomes
      </div>

      {/* ===== SVG layer: two lanes + barrier + quarantine + core ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="pf8-red" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={rose} stopOpacity={0.4} />
            <stop offset="100%" stopColor={red} stopOpacity={0.1} />
          </linearGradient>
          <linearGradient id="pf8-grn" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={green} stopOpacity={0.12} />
            <stop offset="100%" stopColor={green} stopOpacity={0.5} />
          </linearGradient>
        </defs>

        {/* ---- TOP lane (attack, blocked at barrier) ---- */}
        <line x1={laneX0} y1={topY} x2={barrierX - 10} y2={topY} stroke="url(#pf8-red)" strokeWidth={4}
          strokeDasharray="3 14" strokeDashoffset={-localFrame * 4} opacity={lin(localFrame, [6, 22], [0, 0.8])} />
        {/* red BLOCKED barrier */}
        <g opacity={lin(localFrame, [8, 24], [0, 1])}>
          <rect x={barrierX - 6} y={topY - 64} width={12} height={128} rx={4} fill={red}
            opacity={0.7 + 0.3 * blocked} transform={`translate(${slamKick * 8},0)`} />
          {/* barrier hazard hatch */}
          {Array.from({ length: 5 }).map((_, i) => (
            <line key={`bh-${i}`} x1={barrierX - 18} y1={topY - 56 + i * 28} x2={barrierX - 30} y2={topY - 56 + i * 28 + 14}
              stroke={red} strokeWidth={3} opacity={0.5 + 0.3 * blocked} />
          ))}
          {/* block shock ring */}
          {slamKick > 0.04 && (
            <circle cx={barrierX - 40} cy={topY} r={20 + (1 - slamKick) * 60} fill="none" stroke={rose}
              strokeWidth={3} opacity={slamKick * 0.7} />
          )}
        </g>
        {/* quarantine lock zone (right of barrier on top lane) */}
        {quarLock > 0.05 && (
          <g opacity={quarLock}>
            <rect x={barrierX + 40} y={topY - 54} width={150} height={108} rx={12}
              fill="rgba(30,6,14,0.7)" stroke={rose} strokeWidth={3} />
            {Array.from({ length: 3 }).map((_, i) => (
              <line key={`qh-${i}`} x1={barrierX + 52 + i * 46} y1={topY + 44} x2={barrierX + 52 + i * 46 + 28} y2={topY - 44}
                stroke={`${rose}33`} strokeWidth={6} />
            ))}
          </g>
        )}

        {/* ---- BOTTOM lane (real request, clean pass to core) ---- */}
        <line x1={laneX0} y1={botY} x2={coreX - 64} y2={botY} stroke="url(#pf8-grn)" strokeWidth={4}
          strokeDasharray="3 14" strokeDashoffset={-localFrame * 6} opacity={lin(localFrame, [10, 26], [0, 0.85])} />
        {/* green pass gate */}
        <g opacity={lin(localFrame, [12, 28], [0, 1])}>
          <line x1={barrierX} y1={botY - 58} x2={barrierX} y2={botY + 58} stroke={green} strokeWidth={3} strokeDasharray="6 8" opacity={0.6} />
          <path d={`M ${barrierX - 16} ${botY} L ${barrierX} ${botY - 16} L ${barrierX} ${botY + 16} Z`} fill={green} opacity={0.5} />
        </g>
        {/* SYSTEM CORE (bottom-right), lights up on pass */}
        <circle cx={coreX} cy={botY} r={coreRun > 0 ? 70 : 56} fill={green} opacity={0.12 + 0.16 * coreRun} style={{ filter: 'blur(6px)' }} />
        <circle cx={coreX} cy={botY} r={56} fill={coreRun > 0.5 ? 'rgba(6,30,22,0.9)' : 'rgba(10,16,24,0.85)'}
          stroke={coreRun > 0.5 ? green : 'rgba(245,247,255,0.4)'} strokeWidth={3} />
        <circle cx={coreX} cy={botY} r={56 * (1 + 0.1 * coreRun * (0.5 + 0.5 * Math.sin(localFrame / 7)))} fill="none"
          stroke={green} strokeWidth={2} opacity={coreRun * 0.5} />
        <circle cx={coreX} cy={botY} r={24} fill={white} opacity={0.14 + 0.16 * coreRun} />
      </svg>

      {/* ===== TOP attack chip ===== */}
      <div style={{ position: 'absolute', left: atkX - 116, top: topY - 24,
        width: 232, height: 48, borderRadius: 10, background: 'linear-gradient(160deg, rgba(60,12,24,0.96), rgba(28,6,14,0.96))',
        border: `2px solid ${rose}`, opacity: lin(localFrame, [6, 20], [0, 1]),
        transform: `translateX(${-slamKick * 14}px) scale(${1 + 0.05 * (blocked > 0 ? 0 : atkPulse)})`,
        boxShadow: `0 0 14px ${rose}cc`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
        <span style={{ fontSize: 14 }}>{blocked > 0.5 ? '🔒' : '⚠'}</span>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 14, fontWeight: 700, color: white }}>"ignore all instructions"</span>
      </div>
      {/* BLOCKED ✗ stamp */}
      {blocked > 0.1 && (
        <div style={{ position: 'absolute', left: barrierX - 96, top: topY - 116, transform: `rotate(-8deg) scale(${0.6 + 0.5 * blocked})`, opacity: blocked }}>
          <span style={{ fontFamily: 'Consolas, monospace', fontSize: 30, fontWeight: 800, color: red,
            border: `3px solid ${red}`, padding: '4px 14px', borderRadius: 10, letterSpacing: 1,
            textShadow: `0 0 16px ${red}cc`, background: 'rgba(20,4,10,0.5)' }}>✗ BLOCKED</span>
        </div>
      )}
      {/* top lane label */}
      <div style={{ position: 'absolute', left: laneX0, top: topY - 96, fontFamily: 'Consolas, monospace',
        fontSize: 17, letterSpacing: 2, color: rose, opacity: lin(localFrame, [6, 22], [0, 1]) }}>THE ATTACK</div>

      {/* ===== BOTTOM real-request chip ===== */}
      <div style={{ position: 'absolute', left: reqX - 92, top: botY - 22,
        width: 184, height: 44, borderRadius: 9, background: passed > 0.5 ? 'rgba(6,30,22,0.9)' : 'rgba(10,22,30,0.85)',
        border: `2px solid ${passed > 0.5 ? green : cyan}`, opacity: lin(localFrame, [28, 42], [0, 1]),
        boxShadow: `0 0 12px ${passed > 0.5 ? green : cyan}55`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 14, fontWeight: 700, color: white }}>"book a demo"</span>
      </div>
      {/* PASSED ✓ stamp */}
      {passed > 0.1 && (
        <div style={{ position: 'absolute', left: coreX - 86, top: botY - 124, transform: `scale(${checkPop})`, opacity: passed }}>
          <span style={{ fontFamily: 'Consolas, monospace', fontSize: 28, fontWeight: 800, color: green,
            border: `3px solid ${green}`, padding: '4px 14px', borderRadius: 10, letterSpacing: 1,
            textShadow: `0 0 16px ${green}cc`, background: 'rgba(4,20,14,0.5)' }}>✓ PASSED</span>
        </div>
      )}
      {/* core RUNNING label */}
      <div style={{ position: 'absolute', left: coreX - 90, top: botY + 64, width: 180, textAlign: 'center',
        opacity: lin(localFrame, [40, 56], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 16, fontWeight: 700, letterSpacing: 2,
          color: coreRun > 0.5 ? green : 'rgba(245,247,255,0.55)' }}>{coreRun > 0.5 ? 'RUNNING ✓' : 'SYSTEM'}</div>
      </div>
      {/* bottom lane label */}
      <div style={{ position: 'absolute', left: laneX0, top: botY - 92, fontFamily: 'Consolas, monospace',
        fontSize: 17, letterSpacing: 2, color: green, opacity: lin(localFrame, [28, 42], [0, 1]) }}>THE REAL REQUEST</div>

      {/* ===== center: THREATS BLOCKED tally + "0 reached the model" seal ===== */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 388, textAlign: 'center', opacity: lin(localFrame, [20, 36], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 18, letterSpacing: 4, color: 'rgba(245,247,255,0.6)', textTransform: 'uppercase' }}>
          threats blocked
        </div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 76, fontWeight: 800, lineHeight: 1.05, color: red,
          letterSpacing: -1, transform: `scale(${1 + 0.1 * tallySnap})`, textShadow: `0 0 26px ${red}88` }}>
          {threatsBlocked}
        </div>
      </div>
      {sealIn > 0.02 && (
        <div style={{ position: 'absolute', left: 0, right: 0, top: 470, textAlign: 'center', opacity: sealIn,
          transform: `scale(${0.8 + 0.2 * sealIn})` }}>
          <span style={{ fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 700, color: green, letterSpacing: 1,
            border: `2px solid ${green}`, padding: '4px 16px', borderRadius: 999, textShadow: `0 0 14px ${green}aa`,
            background: 'rgba(4,20,14,0.45)' }}>0 reached the model</span>
        </div>
      )}

      {/* caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 26, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 38, fontWeight: 800, color: white }}>
          Attack <span style={{ color: red, textShadow: `0 0 22px ${red}99` }}>blocked.</span>{' '}
          Real request <span style={{ color: green, textShadow: `0 0 22px ${green}99` }}>gets through.</span>
        </span>
      </div>
    </div>
  );
};
