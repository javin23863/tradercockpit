import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #6 (evals) — beat: "Run every version through an eval set. An LLM judge scores each one."
 *
 * CONCEPT — THE EVAL HARNESS: a prompt VERSION chip rides a conveyor into a TEST-SET GRID — a column
 * of test cases that light up one-by-one as a scan-line sweeps down them, each resolving to PASS (mint)
 * or FAIL (rose). Then an LLM-JUDGE (a glowing rotating diamond "eye") STAMPS a numeric score onto the
 * version. A running score tally climbs. Now every version is measured, not guessed.
 *
 * NOVELTY (vs ledger): NEW families — test-case-grid scan-line resolve, version-conveyor feed,
 * llm-judge rotating-diamond stamp, score-readout tally. (No tank/torrent/core, no routing lanes,
 * no node-graph, no cache-vault, no twin-cost-bars, no liquid columns, no send-rail.)
 *
 * RENDER-SAFE: react + remotion only. No useCurrentFrame/AbsoluteFill/three. No Math.random/Date.now.
 * Strictly-increasing interpolate ranges (prop-ends guarded). Deterministic number formatting. 1080x820.
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

  const rose = accentA;
  const mint = accentB;
  const white = '#F5F7FF';
  const END = Math.max(60, beatDur);

  // narration land: "judge" / "scores" -> the judge stamps the score
  const judgeAt = wordStart('judge') ?? wordStart('scores') ?? wordStart('score') ?? null;
  const judging = judgeAt != null ? tS >= judgeAt : localFrame > 64;
  const sinceJudge = judgeAt != null ? Math.max(0, tS - judgeAt) : (localFrame > 64 ? (localFrame - 64) / fps : 0);

  // ---- stage geometry ----
  const gridX = 470, gridTop = 230, cellW = 320, cellH = 56, rows = 6, gap = 12;
  const judgeX = 880, judgeY = 360;

  // ---- conveyor: version chip rides in from the left into the grid ----
  const convIn = spring({ frame: localFrame, fps, config: { damping: 16 } });
  const versionX = lerp(90, gridX - 168, lin(localFrame, [4, 28], [0, 1]));
  const versionY = gridTop + (rows * (cellH + gap)) / 2 - 36;

  // ---- test-case grid: a scan-line sweeps down, lighting + resolving each row ----
  // each row resolves pass/fail at its own time; deterministic verdicts (mostly pass, a couple fail)
  const scanStart = 26;
  const perRow = 6.5; // frames between row resolves
  const scanRow = (localFrame - scanStart) / perRow; // fractional row being scanned
  const verdicts = [true, true, false, true, true, true]; // pass=true
  // overall measured score (fraction of resolved rows that passed, scaled to a clean number)
  const resolvedCount = clamp(Math.floor(scanRow + 1), 0, rows);
  let passSoFar = 0;
  for (let r = 0; r < resolvedCount; r++) if (verdicts[r]) passSoFar++;
  const scorePct = resolvedCount > 0 ? Math.round((passSoFar / resolvedCount) * 100) : 0;
  // final stamped score appears on judge action
  const finalScore = 83;
  const stampScore = judging ? finalScore : scorePct;

  // ---- LLM judge diamond pulse ----
  const judgeIn = lin(localFrame, [12, 30], [0, 1]);
  const judgePulse = 0.5 + 0.5 * Math.sin(localFrame / 8);
  const stampPop = judging ? spring({ frame: Math.max(0, localFrame - Math.round((sinceJudge) * fps)), fps, config: { damping: 11 } }) : 0;

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* ambient wash */}
      <div style={{ position: 'absolute', left: 360, top: 160, width: 720, height: 560, borderRadius: 380,
        background: `radial-gradient(circle at 50% 45%, ${mint}16, transparent 66%)`, filter: 'blur(50px)' }} />

      {/* ===== conveyor rail feeding the grid ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <line x1={70} y1={versionY + 36} x2={gridX - 6} y2={versionY + 36} stroke={rose} strokeWidth={4}
          strokeDasharray="3 14" strokeDashoffset={-localFrame * 5} opacity={lin(localFrame, [4, 22], [0, 0.7])} />
        {/* arrowhead into grid */}
        <path d={`M ${gridX - 14} ${versionY + 30} L ${gridX - 2} ${versionY + 36} L ${gridX - 14} ${versionY + 42} Z`}
          fill={rose} opacity={lin(localFrame, [6, 22], [0, 0.8])} />
      </svg>

      {/* version chip on the conveyor */}
      <div style={{ position: 'absolute', left: versionX, top: versionY, width: 156, height: 72, borderRadius: 14,
        background: 'linear-gradient(160deg, rgba(30,22,38,0.96), rgba(14,10,22,0.96))', border: `2px solid ${rose}`,
        boxShadow: `0 0 18px ${rose}66`, transform: `scale(${lerp(0.7, 1, convIn)})`,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 3 }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 18, fontWeight: 800, color: white, letterSpacing: 1 }}>VERSION</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 13, color: rose }}>prompt · candidate</div>
      </div>

      {/* ===== TEST-SET GRID (rows of cases, scan-line resolves each) ===== */}
      <div style={{ position: 'absolute', left: gridX, top: gridTop - 40, width: cellW, textAlign: 'left',
        fontFamily: 'Consolas, monospace', fontSize: 16, letterSpacing: 2, color: 'rgba(245,247,255,0.6)',
        textTransform: 'uppercase', opacity: lin(localFrame, [8, 24], [0, 1]) }}>eval set · {rows} cases</div>
      {verdicts.map((pass, r) => {
        const cy = gridTop + r * (cellH + gap);
        const reached = scanRow >= r;
        const justHit = scanRow >= r && scanRow < r + 1.2;
        const settle = clamp((scanRow - r) / 0.8);
        const col = !reached ? 'rgba(245,247,255,0.16)' : pass ? mint : rose;
        const cellAppear = lin(localFrame, [14 + r * 2, 28 + r * 2], [0, 1]);
        return (
          <div key={`cell-${r}`} style={{ position: 'absolute', left: gridX, top: cy, width: cellW, height: cellH,
            borderRadius: 10, background: reached ? `${col}1f` : 'rgba(10,8,20,0.6)',
            border: `2px solid ${col}`, opacity: cellAppear,
            boxShadow: justHit ? `0 0 18px ${col}aa` : 'none', transform: `scale(${lerp(0.96, 1, settle)})`,
            display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 16px' }}>
            <span style={{ fontFamily: 'Consolas, monospace', fontSize: 15, color: 'rgba(245,247,255,0.8)' }}>case {r + 1}</span>
            <span style={{ fontFamily: 'Consolas, monospace', fontSize: 18, fontWeight: 800,
              color: reached ? col : 'rgba(245,247,255,0.3)', opacity: reached ? settle : 0.4 }}>
              {reached ? (pass ? '✓ PASS' : '✗ FAIL') : '· · ·'}
            </span>
          </div>
        );
      })}
      {/* scan line sweeping down the grid */}
      {scanRow >= -0.3 && scanRow <= rows && (
        <div style={{ position: 'absolute', left: gridX - 6, top: gridTop + clamp(scanRow, 0, rows) * (cellH + gap) - 2,
          width: cellW + 12, height: 4, borderRadius: 2,
          background: `linear-gradient(90deg, transparent, ${mint}, transparent)`,
          boxShadow: `0 0 14px ${mint}`, opacity: 0.9 }} />
      )}

      {/* ===== LLM JUDGE (rotating diamond eye) that stamps the score ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0, opacity: judgeIn }}>
        <defs>
          <radialGradient id="ins6-judge" cx="50%" cy="42%" r="60%">
            <stop offset="0%" stopColor={white} stopOpacity={0.9} />
            <stop offset="45%" stopColor={mint} stopOpacity={0.85} />
            <stop offset="100%" stopColor={'#06231A'} stopOpacity={0.9} />
          </radialGradient>
        </defs>
        {/* link from grid to judge */}
        <line x1={gridX + cellW + 6} y1={judgeY} x2={judgeX - 64} y2={judgeY} stroke={mint} strokeWidth={2.5}
          strokeDasharray="2 12" strokeDashoffset={-localFrame * 3} opacity={0.6} />
        {/* outer rotating diamond */}
        <g transform={`rotate(${localFrame * 1.4} ${judgeX} ${judgeY})`}>
          <rect x={judgeX - 58} y={judgeY - 58} width={116} height={116} rx={14} fill="none"
            stroke={mint} strokeWidth={2.5} opacity={0.5 + 0.3 * judgePulse} transform={`rotate(45 ${judgeX} ${judgeY})`} />
        </g>
        {/* inner counter-rotating diamond */}
        <g transform={`rotate(${-localFrame * 2.2} ${judgeX} ${judgeY})`}>
          <rect x={judgeX - 40} y={judgeY - 40} width={80} height={80} rx={10} fill="url(#ins6-judge)"
            stroke={mint} strokeWidth={3} transform={`rotate(45 ${judgeX} ${judgeY})`} />
        </g>
        {/* eye pupil */}
        <circle cx={judgeX} cy={judgeY} r={12 + 3 * judgePulse} fill={white} opacity={0.85} />
        <circle cx={judgeX} cy={judgeY} r={5} fill={'#06231A'} />
      </svg>

      {/* judge label */}
      <div style={{ position: 'absolute', left: judgeX - 90, top: judgeY + 70, width: 180, textAlign: 'center', opacity: judgeIn }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 20, fontWeight: 800, letterSpacing: 2, color: mint,
          textShadow: `0 0 14px ${mint}aa` }}>LLM JUDGE</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 13, color: 'rgba(245,247,255,0.55)', marginTop: 4 }}>scores each version</div>
      </div>

      {/* stamped SCORE badge (snaps in when judging) */}
      <div style={{ position: 'absolute', left: judgeX - 64, top: judgeY - 150, width: 128, textAlign: 'center',
        opacity: lin(localFrame, [18, 32], [0, 1]), transform: `scale(${0.8 + 0.3 * (judging ? stampPop : judgePulse * 0.2 + 0.8)})` }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 14, letterSpacing: 2, color: 'rgba(245,247,255,0.6)' }}>SCORE</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 56, fontWeight: 800, lineHeight: 1,
          color: judging ? mint : white, textShadow: judging ? `0 0 26px ${mint}cc` : `0 0 16px ${mint}55` }}>
          {stampScore}
        </div>
        {judging && (
          <div style={{ position: 'absolute', left: -6, top: -6, right: -6, bottom: -6, border: `3px solid ${mint}`,
            borderRadius: 12, opacity: clamp(1 - stampPop) * 0.8, transform: `scale(${1 + (1 - stampPop) * 0.3})` }} />
        )}
      </div>

      {/* caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 26, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white }}>
          Every version{' '}
          <span style={{ color: mint, textShadow: `0 0 22px ${mint}99` }}>measured, not guessed.</span>
        </span>
      </div>
    </div>
  );
};
