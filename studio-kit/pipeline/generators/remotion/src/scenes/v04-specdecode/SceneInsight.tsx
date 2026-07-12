import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #4 (speculative decoding) — beat: "A tiny draft model guesses ahead. The big model verifies a
 * whole batch at once."
 *
 * CONCEPT: a SMALL fast DRAFT model (left) races ahead, rapidly emitting a ROW of GUESS-TOKEN chips
 * (a speculative batch laid out left->right, each chip popping in fast with a "?" guess). Then the BIG
 * VERIFIER model (right) fires ONE verification SWEEP-BAR that travels across the ENTIRE batch in a single
 * pass — accepting a contiguous PREFIX RUN (turns green, "accept-streak") and rejecting the tail (turns
 * red with an X). One verify pass validates many tokens.
 *
 * NOVELTY (vs ledger): NEW families — fast draft-runner emitting a guess-token batch row, a single-pass
 * verifier sweep-bar over the whole batch, a contiguous green accept-streak + red reject tail, a "1 pass /
 * N tokens" badge. (No torrent/core/tank, no node-graph, no cache-vault/lightning, no send-rail, no
 * isometric lanes, no router diamond.)
 *
 * RENDER-SAFE: react + remotion only. No useCurrentFrame/AbsoluteFill/three. No Math.random/Date.now.
 * Strictly-increasing interpolate ranges (prop-derived ends guarded). 1080x820.
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

  const cyan = accentA;
  const green = accentB;
  const white = '#F5F7FF';
  const red = '#FF5470';
  const END = Math.max(60, beatDur);

  const draftAt = wordStart('draft') ?? wordStart('guesses') ?? null;
  const verifyAt = wordStart('verifies') ?? wordStart('batch') ?? null;

  // batch geometry — a row of guess chips between draft (left) and verifier (right)
  const N = 7;                 // guess-tokens in the speculative batch
  const ACCEPT = 5;            // contiguous accepted prefix (green streak)
  const rowY = 350;
  const chipW = 78, chipGap = 14;
  const rowX0 = 250;
  const chipX = (i: number) => rowX0 + i * (chipW + chipGap);

  // draft emits chips fast, left->right, one every ~4 frames
  const emitStart = 16;
  const emitPer = 4;
  const emittedF = (localFrame - emitStart) / emitPer;
  const draftBob = Math.sin(localFrame / 7) * 4;
  const draftPulse = Math.exp(-fract(Math.max(0, emittedF)) * 4); // pops on each emit

  // verifier sweep: AFTER the batch is laid out, one bar travels across all N chips in a single pass
  const sweepStart = emitStart + N * emitPer + 6; // begins once the row is emitted
  const sweepDur = 26;
  const verifyAtFrame = verifyAt != null ? null : sweepStart; // word-sync OR frame fallback
  const sweepT = verifyAt != null
    ? clamp(lin(tS - verifyAt, [0, sweepDur / fps], [0, 1]))
    : clamp(lin(localFrame, [sweepStart, sweepStart + sweepDur], [0, 1]));
  const sweepX = lerp(rowX0 - 10, chipX(N - 1) + chipW + 14, sweepT);
  const sweeping = sweepT > 0 && sweepT < 1;
  const sweepDone = sweepT >= 1;

  // verifier model (right) impact when the sweep launches/finishes
  const verifierFire = sweepT > 0 ? Math.exp(-sweepT * 3) : 0;
  const verifierBob = Math.sin(localFrame / 9) * 3;

  // small intake stream dashes from draft -> batch
  const sceneIn = lin(localFrame, [0, 10], [0, 1]);

  const vx = 880, vy = rowY + chipW / 2; // verifier center
  const dx = 150, dy = rowY + chipW / 2; // draft center

  // accept count badge ticks up as the sweep passes each accepted chip
  const passedCount = Math.min(N, Math.floor(sweepT * N + 0.0001));
  const acceptedShown = Math.min(ACCEPT, passedCount);

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      <div style={{ position: 'absolute', left: 540 - 360, top: rowY - 220, width: 720, height: 560, borderRadius: 400,
        background: `radial-gradient(circle at 50% 45%, ${green}1c, transparent 66%)`, filter: 'blur(48px)' }} />

      {/* ===== SVG: connectors + sweep bar ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="in4-stream" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={cyan} stopOpacity={0.6} />
            <stop offset="100%" stopColor={cyan} stopOpacity={0.1} />
          </linearGradient>
        </defs>
        {/* draft -> batch intake stream */}
        <line x1={dx + 60} y1={dy} x2={rowX0 - 6} y2={rowY + chipW / 2} stroke="url(#in4-stream)" strokeWidth={4}
          strokeDasharray="4 10" strokeDashoffset={-localFrame * 6} opacity={lin(localFrame, [10, 26], [0, 0.9])} />
        {/* batch -> verifier link */}
        <line x1={chipX(N - 1) + chipW + 6} y1={rowY + chipW / 2} x2={vx - 64} y2={vy}
          stroke={'rgba(245,247,255,0.25)'} strokeWidth={3} strokeDasharray="3 9"
          strokeDashoffset={-localFrame * 3} opacity={lin(localFrame, [sweepStart - 6, sweepStart + 6], [0, 0.8])} />

        {/* the single-pass VERIFY SWEEP BAR over the whole batch */}
        {sweepT > 0 && (
          <>
            <line x1={sweepX} y1={rowY - 26} x2={sweepX} y2={rowY + chipW + 26}
              stroke={green} strokeWidth={5} opacity={sweeping ? 0.9 : 0.3}
              style={{ filter: `drop-shadow(0 0 12px ${green})` }} />
            {/* leading glow band */}
            <rect x={sweepX - 30} y={rowY - 26} width={30} height={chipW + 52} rx={6}
              fill={green} opacity={sweeping ? 0.12 : 0} />
          </>
        )}
      </svg>

      {/* ===== DRAFT model (small, fast) ===== */}
      <div style={{ position: 'absolute', left: dx - 58, top: rowY - 26 + draftBob, width: 116, height: 116,
        borderRadius: 22, background: `radial-gradient(circle at 50% 38%, ${cyan}33, rgba(10,16,28,0.95) 78%)`,
        border: `2.5px solid ${cyan}`, boxShadow: `0 0 ${18 + 16 * draftPulse}px ${cyan}99`,
        transform: `scale(${1 + 0.05 * draftPulse})`, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 2 }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 800, color: white }}>DRAFT</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 12, color: cyan }}>tiny · fast</div>
        <div style={{ marginTop: 2, fontFamily: 'Consolas, monospace', fontSize: 11, color: 'rgba(245,247,255,0.5)' }}>guesses ahead »</div>
      </div>

      {/* ===== speculative GUESS-TOKEN batch row ===== */}
      {Array.from({ length: N }).map((_, i) => {
        // each chip pops in fast as the draft emits it
        const appear = clamp((emittedF - i) / 0.9);
        const pop = appear <= 0 ? 0 : spring({ frame: Math.max(0, localFrame - (emitStart + i * emitPer)), fps, config: { damping: 11 } });
        // verify state: this chip is decided once the sweep passes its right edge
        const decideX = chipX(i) + chipW;
        const decided = sweepX >= decideX;
        const accepted = decided && i < ACCEPT;
        const rejected = decided && i >= ACCEPT;
        const borderC = accepted ? green : rejected ? red : `${cyan}cc`;
        const bg = accepted ? `${green}22` : rejected ? `${red}1f` : 'rgba(20,28,44,0.9)';
        const justDecided = decided ? Math.exp(-Math.max(0, (sweepX - decideX)) / 40) : 0;
        return (
          <div key={`chip-${i}`} style={{ position: 'absolute', left: chipX(i), top: rowY,
            width: chipW, height: chipW, borderRadius: 12, background: bg, border: `2px solid ${borderC}`,
            opacity: appear, transform: `scale(${0.6 + 0.4 * pop + 0.06 * justDecided})`,
            boxShadow: accepted ? `0 0 16px ${green}88` : rejected ? `0 0 14px ${red}66` : `0 0 8px ${cyan}33`,
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
            <div style={{ fontFamily: 'Consolas, monospace', fontSize: 26, fontWeight: 800,
              color: accepted ? green : rejected ? red : white }}>
              {accepted ? '✓' : rejected ? '✕' : '?'}
            </div>
            <div style={{ fontFamily: 'Consolas, monospace', fontSize: 11, color: 'rgba(245,247,255,0.55)' }}>g{i + 1}</div>
          </div>
        );
      })}

      {/* accept-streak underline bracket under the green run */}
      {sweepX >= chipX(ACCEPT - 1) + chipW && (
        <div style={{ position: 'absolute', left: chipX(0), top: rowY + chipW + 12,
          width: ACCEPT * chipW + (ACCEPT - 1) * chipGap, height: 4, borderRadius: 2, background: green,
          opacity: 0.8, boxShadow: `0 0 12px ${green}aa` }} />
      )}
      {sweepX >= chipX(ACCEPT - 1) + chipW && (
        <div style={{ position: 'absolute', left: chipX(0), top: rowY + chipW + 22,
          width: ACCEPT * chipW + (ACCEPT - 1) * chipGap, textAlign: 'center',
          fontFamily: 'Consolas, monospace', fontSize: 16, fontWeight: 700, color: green }}>
          accept-streak ×{acceptedShown}
        </div>
      )}

      {/* ===== VERIFIER model (big) ===== */}
      <div style={{ position: 'absolute', left: vx - 70, top: vy - 70 + verifierBob, width: 140, height: 140,
        borderRadius: 26, background: `radial-gradient(circle at 50% 38%, ${green}2e, rgba(8,16,12,0.95) 78%)`,
        border: `3px solid ${green}`, boxShadow: `0 0 ${20 + 26 * verifierFire}px ${green}aa`,
        transform: `scale(${1 + 0.06 * verifierFire})`, display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', gap: 3 }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 800, color: white }}>VERIFIER</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 12, color: green }}>big · one pass</div>
        {sweeping && (
          <div style={{ position: 'absolute', inset: -7, borderRadius: 30, border: `3px solid ${green}`,
            opacity: verifierFire * 0.7, transform: `scale(${1 + (1 - sweepT) * 0.2})` }} />
        )}
      </div>

      {/* "1 pass / N tokens" badge */}
      <div style={{ position: 'absolute', left: vx - 80, top: vy + 80, width: 160, textAlign: 'center',
        opacity: lin(localFrame, [sweepStart - 4, sweepStart + 10], [0, 1]) }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 18, fontWeight: 700, color: green,
          border: `2px solid ${green}`, padding: '3px 12px', borderRadius: 10,
          boxShadow: sweepDone ? `0 0 14px ${green}88` : 'none' }}>1 pass · {N} tokens</span>
      </div>

      {/* top-left readout */}
      <div style={{ position: 'absolute', left: 70, top: 120, width: 460, opacity: lin(localFrame, [10, 28], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 22, letterSpacing: 3, color: 'rgba(245,247,255,0.6)', textTransform: 'uppercase', marginBottom: 8 }}>
          one verify pass
        </div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 60, fontWeight: 800, lineHeight: 1, letterSpacing: -1,
          color: sweepDone ? green : white, textShadow: sweepDone ? `0 0 24px ${green}aa` : `0 0 16px ${cyan}55` }}>
          {sweepDone ? `+${ACCEPT} tokens` : 'guess » verify'}
        </div>
        <div style={{ marginTop: 10, fontFamily: 'Consolas, monospace', fontSize: 20, color: cyan }}>
          {sweepDone ? 'accepted in bulk · 1 pass' : 'draft guesses · big model checks'}
        </div>
      </div>

      {/* caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 28, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white }}>
          Draft guesses ahead. <span style={{ color: green, textShadow: `0 0 22px ${green}99` }}>Verified in one batch.</span>
        </span>
      </div>
    </div>
  );
};
