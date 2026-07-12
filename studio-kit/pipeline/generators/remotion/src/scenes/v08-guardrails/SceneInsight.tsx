import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #8 (guardrails) — beat: "Screen every input. Quarantine injection before it reaches the model."
 *
 * CONCEPT: a GUARDRAIL SCANNER gate stands in the middle of the input stream. A vertical scan-beam sweeps
 * across the incoming chips; benign tokens light GREEN and pass through to the SYSTEM CORE on the right.
 * The malicious payload chip ("ignore all instructions") trips the scanner RED, gets a lock icon, and is
 * YANKED off the rail down into a sealed QUARANTINE box (lid snaps shut, padlock locks). A "screened" tally
 * climbs as chips pass.
 *
 * NOVELTY (vs ledger — FORBIDDEN families avoided): NEW families — a guardrail SCANNER GATE with a vertical
 * sweeping scan-beam, a flag-and-lock on a tripped chip, a YANK-arc that pulls the payload off-rail into a
 * sealing quarantine box, a green pass-through lane to the core, a screened-count tally. (No node-graph,
 * cache-vault, conveyor, verifier-sweep, eval-grid, etc.)
 *
 * RENDER-SAFE: react + remotion only. No useCurrentFrame/AbsoluteFill/three. No Math.random/Date.now.
 * Strictly-increasing interpolate ranges (prop ends guarded). Manual number formatting. 1080x820.
 */
export const SceneInsight: React.FC<{
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

  const rose = accentA;          // flagged / quarantine accent
  const cyan = accentB;          // scanner / system accent
  const white = '#F5F7FF';
  const green = '#34F5A0';
  const END = Math.max(60, beatDur);

  // narration land: emphasize "screen" and "quarantine"
  const screenAt = wordStart('screen') ?? null;
  const quarAt = wordStart('quarantine') ?? wordStart('injection') ?? null;
  const scanning = screenAt != null ? tS >= screenAt : localFrame > 16;
  const quarantined = quarAt != null ? tS >= quarAt : localFrame > 70;
  const sinceQuar = quarAt != null ? Math.max(0, tS - quarAt) : Math.max(0, (localFrame - 70) / fps);

  const railY = 360;
  const gateX = 540;             // scanner gate x (center)
  const coreX = 944, coreY = railY, coreR = 64;
  const streamX0 = 96;
  const qBoxX = gateX - 88, qBoxY = 600, qBoxW = 176, qBoxH = 150;   // quarantine box (below the gate)

  // ---- scan-beam sweeps across the gate window repeatedly ----
  const beamPeriod = 46;
  const beamPhase = fract(localFrame / beamPeriod);
  const beamX = lerp(gateX - 70, gateX + 70, beamPhase);
  const beamFlash = Math.exp(-fract(beamPhase * 1) * 3);

  // ---- benign chips: flow left, pass the gate, light green, continue to core ----
  const NUM = 7;
  const WORDS = ['book', 'a', 'demo', 'next', 'week', 'for', 'me'];
  const gateIn = lin(localFrame, [4, 22], [0, 1]);
  type Chip = { x: number; y: number; o: number; passed: boolean; word: string; idx: number };
  const chips: Chip[] = [];
  for (let i = 0; i < NUM; i++) {
    const period = 70 + rnd(i) * 16;
    const phase = rnd(i * 3 + 2);
    const prog = fract((localFrame / period) + phase);
    const x = lerp(streamX0, coreX - coreR - 26, prog);
    const passed = x > gateX;     // green once past the gate window
    const fadeIn = clamp(prog / 0.06);
    const fadeOut = 1 - clamp((prog - 0.92) / 0.08);
    chips.push({ x, y: railY, o: fadeIn * fadeOut * gateIn * 0.95, passed, word: WORDS[i % WORDS.length], idx: i });
  }

  // ---- malicious payload: rides to the gate, trips RED, then is YANKED into quarantine ----
  const payToGate = clamp(lin(localFrame, [10, 56], [0, 1]));       // reaches the gate window
  const flagged = scanning && payToGate > 0.92;                     // tripped at the gate
  // yank arc: from gate (on rail) down into the box
  const yankT = quarantined ? clamp(lin(sinceQuar, [0, 0.5], [0, 1])) : 0;
  const payOnRailX = lerp(streamX0 + 30, gateX, payToGate);
  const payX = lerp(payOnRailX, qBoxX + qBoxW / 2, yankT);
  const payY = lerp(railY, qBoxY + qBoxH * 0.52, yankT) - (yankT > 0 ? Math.sin(Math.PI * yankT) * 70 : 0); // arc lift
  const payPulse = 0.5 + 0.5 * Math.sin(localFrame / 5);
  const payIn = lin(localFrame, [8, 22], [0, 1]);
  const payScale = lerp(1, 0.66, yankT);

  // ---- quarantine box seal (lid + padlock) ----
  const sealed = quarantined ? clamp(lin(sinceQuar, [0.4, 0.9], [0, 1])) : 0;
  const lidDrop = quarantined ? clamp(lin(sinceQuar, [0.35, 0.75], [0, 1])) : 0;

  // ---- screened tally ----
  const screenedCount = Math.max(0, Math.floor(lin(localFrame, [16, 110], [0, 8])));

  const gateBuild = spring({ frame: localFrame, fps, config: { damping: 16 } });
  const sceneIn = lin(localFrame, [0, 10], [0, 1]);

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      <div style={{ position: 'absolute', left: gateX - 320, top: railY - 300, width: 640, height: 600, borderRadius: 400,
        background: `radial-gradient(circle at 50% 45%, ${cyan}1e, transparent 66%)`, filter: 'blur(48px)' }} />

      {/* ===== SVG layer: rail + scanner gate + scan-beam + quarantine box + core ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="in8-rail" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={cyan} stopOpacity={0.08} />
            <stop offset="100%" stopColor={green} stopOpacity={0.5} />
          </linearGradient>
          <linearGradient id="in8-beam" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={cyan} stopOpacity={0} />
            <stop offset="50%" stopColor={cyan} stopOpacity={0.85} />
            <stop offset="100%" stopColor={cyan} stopOpacity={0} />
          </linearGradient>
        </defs>

        {/* input rail (left -> gate, dim cyan) */}
        <line x1={streamX0} y1={railY} x2={gateX} y2={railY} stroke={`${cyan}55`} strokeWidth={4}
          strokeDasharray="3 14" strokeDashoffset={-localFrame * 5} opacity={lin(localFrame, [6, 22], [0, 0.8])} />
        {/* clean pass-through rail (gate -> core, green) */}
        <line x1={gateX} y1={railY} x2={coreX - coreR} y2={railY} stroke="url(#in8-rail)" strokeWidth={4}
          strokeDasharray="3 14" strokeDashoffset={-localFrame * 6} opacity={lin(localFrame, [10, 26], [0, 0.85])} />

        {/* ---- SCANNER GATE frame (vertical posts + window) ---- */}
        {(() => {
          const gw = 150, gh = 220, gx = gateX - gw / 2, gy = railY - gh / 2;
          const draw = clamp(gateBuild);
          return (
            <g opacity={lin(localFrame, [4, 20], [0, 1])}>
              <rect x={gx} y={gy} width={gw} height={gh} rx={16} fill="rgba(8,16,24,0.55)"
                stroke={scanning ? cyan : 'rgba(245,247,255,0.3)'} strokeWidth={3} />
              {/* corner brackets */}
              {[[gx, gy, 1, 1], [gx + gw, gy, -1, 1], [gx, gy + gh, 1, -1], [gx + gw, gy + gh, -1, -1]].map((c, i) => (
                <path key={`br-${i}`} d={`M ${c[0] + (c[2] as number) * 22} ${c[1]} L ${c[0]} ${c[1]} L ${c[0]} ${c[1] + (c[3] as number) * 22}`}
                  fill="none" stroke={cyan} strokeWidth={3} opacity={0.8 * draw} />
              ))}
              {/* scan-beam */}
              {scanning && (
                <rect x={beamX - 4} y={gy + 6} width={8} height={gh - 12} fill="url(#in8-beam)"
                  opacity={0.5 + 0.5 * beamFlash} />
              )}
              {/* faint scan grid */}
              {Array.from({ length: 5 }).map((_, i) => (
                <line key={`sg-${i}`} x1={gx + 8} y1={gy + 28 + i * 40} x2={gx + gw - 8} y2={gy + 28 + i * 40}
                  stroke={`${cyan}22`} strokeWidth={1} />
              ))}
            </g>
          );
        })()}

        {/* ---- QUARANTINE BOX ---- */}
        <g opacity={lin(localFrame, [30, 48], [0, 1])}>
          {/* box body */}
          <rect x={qBoxX} y={qBoxY} width={qBoxW} height={qBoxH} rx={14} fill="rgba(30,6,14,0.7)"
            stroke={rose} strokeWidth={3} />
          {/* hazard hatch stripes inside */}
          {Array.from({ length: 4 }).map((_, i) => (
            <line key={`hz-${i}`} x1={qBoxX + 10 + i * 46} y1={qBoxY + qBoxH - 10} x2={qBoxX + 10 + i * 46 + 34} y2={qBoxY + 14}
              stroke={`${rose}33`} strokeWidth={6} />
          ))}
          {/* lid that drops to seal */}
          <rect x={qBoxX - 6} y={qBoxY - 18 + lidDrop * 16} width={qBoxW + 12} height={20} rx={6}
            fill={rose} opacity={0.55 + 0.4 * sealed} />
          {/* drop-funnel guides from gate to box */}
          <line x1={gateX - 26} y1={railY + 70} x2={qBoxX + 18} y2={qBoxY - 6} stroke={`${rose}44`} strokeWidth={2} strokeDasharray="4 8" />
          <line x1={gateX + 26} y1={railY + 70} x2={qBoxX + qBoxW - 18} y2={qBoxY - 6} stroke={`${rose}44`} strokeWidth={2} strokeDasharray="4 8" />
        </g>

        {/* ---- SYSTEM CORE (right, stays green/safe) ---- */}
        <circle cx={coreX} cy={coreY} r={coreR * 1.7} fill={green} opacity={0.12} style={{ filter: 'blur(6px)' }} />
        <circle cx={coreX} cy={coreY} r={coreR} fill="rgba(6,30,22,0.85)" stroke={green} strokeWidth={3} />
        <circle cx={coreX} cy={coreY} r={coreR * 0.42} fill={white} opacity={0.16 + 0.14 * (0.5 + 0.5 * Math.sin(localFrame / 8))} />
      </svg>

      {/* ===== benign chips (DOM) — green once past the gate ===== */}
      {chips.map((c) => (
        <div key={`c-${c.idx}`} style={{ position: 'absolute', left: c.x - 38, top: c.y - 17,
          width: 76, height: 34, borderRadius: 8, background: c.passed ? 'rgba(6,30,22,0.85)' : 'rgba(10,22,30,0.82)',
          border: `1.5px solid ${c.passed ? green : cyan}99`, opacity: c.o,
          boxShadow: `0 0 10px ${c.passed ? green : cyan}33`, display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'Consolas, monospace', fontSize: 12, color: c.passed ? `${green}ee` : `${cyan}dd` }}>
          {c.passed ? '✓ ' : ''}{c.word}
        </div>
      ))}

      {/* ===== malicious payload chip — trips red, gets locked, yanked to quarantine ===== */}
      <div style={{ position: 'absolute', left: payX - 120 * payScale, top: payY - 24 * payScale,
        width: 240 * payScale, height: 48 * payScale, borderRadius: 10,
        background: 'linear-gradient(160deg, rgba(60,12,24,0.96), rgba(28,6,14,0.96))',
        border: `2px solid ${rose}`, opacity: payIn, transform: `scale(${1 + 0.05 * payPulse})`,
        boxShadow: `0 0 ${12 + 16 * (flagged ? 1 : payPulse)}px ${rose}cc`,
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
        <span style={{ fontSize: 14 * payScale }}>{sealed > 0.5 ? '🔒' : '⚠'}</span>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 14 * payScale, fontWeight: 700, color: white }}>
          "ignore all…"
        </span>
      </div>
      {/* FLAGGED tag at the gate */}
      {flagged && yankT < 0.2 && (
        <div style={{ position: 'absolute', left: gateX - 60, top: railY - 86, width: 120, textAlign: 'center',
          transform: `scale(${0.7 + 0.3 * (0.5 + 0.5 * payPulse)})` }}>
          <span style={{ fontFamily: 'Consolas, monospace', fontSize: 18, fontWeight: 800, color: rose,
            border: `2px solid ${rose}`, padding: '2px 10px', borderRadius: 8, letterSpacing: 1,
            textShadow: `0 0 12px ${rose}cc` }}>FLAGGED</span>
        </div>
      )}

      {/* ===== gate label ===== */}
      <div style={{ position: 'absolute', left: gateX - 150, top: railY - 156, width: 300, textAlign: 'center',
        opacity: lin(localFrame, [12, 28], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 800, letterSpacing: 2, color: cyan,
          textShadow: `0 0 14px ${cyan}aa` }}>GUARDRAIL SCANNER</div>
        <div style={{ marginTop: 3, fontFamily: 'Consolas, monospace', fontSize: 13, color: 'rgba(245,247,255,0.6)' }}>
          screens every input
        </div>
      </div>

      {/* quarantine label */}
      <div style={{ position: 'absolute', left: qBoxX - 12, top: qBoxY + qBoxH + 8, width: qBoxW + 24, textAlign: 'center',
        opacity: lin(localFrame, [34, 50], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 17, fontWeight: 700, letterSpacing: 2,
          color: sealed > 0.5 ? rose : 'rgba(245,247,255,0.7)' }}>QUARANTINE {sealed > 0.5 ? '· LOCKED' : ''}</div>
      </div>

      {/* ===== screened tally (top-left) ===== */}
      <div style={{ position: 'absolute', left: 70, top: 96, width: 380, opacity: lin(localFrame, [14, 30], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 20, letterSpacing: 3, color: 'rgba(245,247,255,0.6)',
          textTransform: 'uppercase', marginBottom: 6 }}>inputs screened</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 64, fontWeight: 800, lineHeight: 1, color: green,
          letterSpacing: -1, textShadow: `0 0 20px ${green}66` }}>{screenedCount}</div>
        <div style={{ marginTop: 6, fontFamily: 'Consolas, monospace', fontSize: 16, color: rose,
          opacity: quarantined ? 1 : 0.4 }}>{quarantined ? '1 injection quarantined' : 'scanning…'}</div>
      </div>

      {/* caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 28, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 38, fontWeight: 800, color: white }}>
          Screen it. <span style={{ color: rose, textShadow: `0 0 22px ${rose}99` }}>Quarantine the injection</span>{' '}
          <span style={{ color: green, textShadow: `0 0 22px ${green}99` }}>before the model.</span>
        </span>
      </div>
    </div>
  );
};
