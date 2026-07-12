import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #5 (persistent memory) — beat: "Write what matters to a memory store. Load it back on the next run."
 *
 * CONCEPT: a live SESSION on the LEFT extracts what matters and pushes memory cards down a WRITE-PIPE
 * into a persistent MEMORY STORE in the center — a stack of cards that visibly GROWS taller. Then a new
 * run begins on the RIGHT and a LOAD-PIPE lifts the whole stack back UP into the fresh session — context
 * carried forward, not lost. Write down, store grows, load back up.
 *
 * NOVELTY (vs ledger): NEW families — a write-pipe of cards descending into a store, a memory-card stack
 * that grows by N, a load-pipe that recalls the stack upward, and a session-handoff arc connecting old->new.
 * (No torrent/core/tank, no cache-vault/send-rail, no node-graph/twin-bars.)
 *
 * RENDER-SAFE: react + remotion only. No useCurrentFrame/AbsoluteFill/three. No Math.random/Date.now.
 * Strictly-increasing interpolate ranges (prop-derived ends guarded). Manual number formatting. 1080x820.
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

  const violet = accentA;
  const amber = accentB;
  const white = '#F5F7FF';
  const green = '#34F5A0';
  const END = Math.max(60, beatDur);

  // narration sync
  const writeAt = wordStart('write') ?? null;
  const loadAt = wordStart('load') ?? null;
  const loadMode = loadAt != null ? tS >= loadAt : localFrame > 78; // second half = recall

  // ---- stage geometry (within 1080x820) ----
  const sessAX = 110, sessAY = 220, sessW = 230, sessH = 250;     // left WRITE session
  const storeX = 470, storeBaseY = 600, storeW = 200;            // center memory store (cards stack up from baseline)
  const sessBX = 740, sessBY = 220;                              // right LOAD session

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);

  // ===================================================================
  // WRITE PHASE — cards stream down the write-pipe; the store grows by one
  // each time a card lands. We model how many cards have landed by now.
  // ===================================================================
  const writeRate = 1.9; // cards/sec
  const writeStart = 0.35;
  const writeFloat = loadMode ? 6 : Math.max(0, (tS - writeStart)) * writeRate; // freeze count once loading
  const landed = Math.min(6, Math.floor(writeFloat)); // store holds up to 6 cards
  const writePhase = fract(writeFloat);

  // in-flight card on the write-pipe (between session A and the store)
  const flightT = loadMode ? 1 : clamp(writePhase, 0, 1);
  const wpStartX = sessAX + sessW - 10, wpStartY = sessAY + sessH / 2;
  const wpEndX = storeX + storeW / 2, wpEndY = storeBaseY - landed * 26 - 18;
  const flyX = lerp(wpStartX, wpEndX, flightT);
  const flyY = lerp(wpStartY, wpEndY, flightT) - Math.sin(Math.PI * flightT) * 40; // arc dip
  const flyVisible = !loadMode && landed < 6;

  // card stack height
  const cardH = 24, cardGap = 2;
  const stackCount = landed;

  // ===================================================================
  // LOAD PHASE — the whole stack lifts up the load-pipe into session B.
  // loadProg 0..1 drives the recall arc.
  // ===================================================================
  const loadProg = loadMode ? clamp(lin(tS - (loadAt ?? (tS - 0.01)), [0, 1.1], [0, 1])) : 0;
  const loadLift = loadProg; // how far the stack has traveled to session B

  // session B fill (mirrors the recalled memory)
  const bFill = loadProg;

  const titleIn = spring({ frame: localFrame, fps, config: { damping: 16 } });

  // helper to render a memory card
  const Card = (x: number, y: number, w: number, op: number, glow: string, label: string, scale = 1) => (
    <div style={{ position: 'absolute', left: x, top: y, width: w * scale, height: cardH * scale,
      borderRadius: 6, background: 'linear-gradient(160deg, rgba(28,22,52,0.96), rgba(14,10,26,0.96))',
      border: `1.5px solid ${glow}`, opacity: op, boxShadow: `0 0 10px ${glow}66`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'Consolas, monospace', fontSize: 11 * scale, color: white, letterSpacing: 0.5 }}>
      {label}
    </div>
  );

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* ambient wash */}
      <div style={{ position: 'absolute', left: storeX - 240, top: 200, width: 720, height: 560, borderRadius: 400,
        background: `radial-gradient(circle at 50% 45%, ${green}16, transparent 66%)`, filter: 'blur(48px)' }} />

      {/* ===== pipes (SVG) ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="ins5-write" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor={violet} stopOpacity={0.7} />
            <stop offset="100%" stopColor={amber} stopOpacity={0.5} />
          </linearGradient>
          <linearGradient id="ins5-load" x1="0" y1="1" x2="1" y2="0">
            <stop offset="0%" stopColor={amber} stopOpacity={0.6} />
            <stop offset="100%" stopColor={green} stopOpacity={0.8} />
          </linearGradient>
        </defs>

        {/* WRITE pipe: session A -> store (curved) */}
        <path d={`M ${sessAX + sessW} ${sessAY + sessH / 2} C ${sessAX + sessW + 90} ${sessAY + sessH / 2 + 40}, ${storeX - 40} ${storeBaseY - 120}, ${storeX + storeW / 2} ${storeBaseY - 30}`}
          fill="none" stroke="url(#ins5-write)" strokeWidth={5} strokeDasharray="3 14"
          strokeDashoffset={-localFrame * 5} opacity={loadMode ? 0.25 : lin(localFrame, [6, 24], [0, 0.85])} />

        {/* LOAD pipe: store -> session B (curved, lights up in load phase) */}
        <path d={`M ${storeX + storeW / 2} ${storeBaseY - 40} C ${storeX + storeW + 60} ${storeBaseY - 140}, ${sessBX - 40} ${sessBY + 200}, ${sessBX + 20} ${sessBY + sessH / 2}`}
          fill="none" stroke="url(#ins5-load)" strokeWidth={5} strokeDasharray="3 14"
          strokeDashoffset={localFrame * 6} opacity={loadMode ? lin(tS - (loadAt ?? tS), [0, 0.4], [0, 0.9]) : 0.18} />

        {/* store baseline plate */}
        <rect x={storeX - 14} y={storeBaseY - 2} width={storeW + 28} height={14} rx={5}
          fill="rgba(8,6,18,0.85)" stroke={`${violet}88`} strokeWidth={2} />
      </svg>

      {/* ===== LEFT: WRITE SESSION ===== */}
      <div style={{ position: 'absolute', left: sessAX, top: sessAY, width: sessW, height: sessH,
        borderRadius: 16, background: 'linear-gradient(160deg, rgba(24,18,46,0.95), rgba(12,9,24,0.95))',
        border: `2px solid ${loadMode ? 'rgba(245,247,255,0.25)' : violet}`,
        boxShadow: loadMode ? 'none' : `0 0 20px ${violet}77`, opacity: loadMode ? 0.5 : 1,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 18, fontWeight: 700, color: white, letterSpacing: 1 }}>SESSION</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 13, color: amber }}>extract what matters</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 28, color: violet, marginTop: 4 }}>↓ write</div>
      </div>

      {/* ===== in-flight write card ===== */}
      {flyVisible && Card(flyX - 50, flyY - 12, 100, clamp(lin(flightT, [0, 0.1, 0.9, 1], [0, 1, 1, 0.7])), amber, 'mem +1')}

      {/* ===== CENTER: MEMORY STORE (growing card stack) ===== */}
      {Array.from({ length: stackCount }).map((_, i) => {
        // during load, the stack lifts toward session B
        const restX = storeX + 4;
        const restY = storeBaseY - (i + 1) * (cardH + cardGap) - 4;
        const tgtX = sessBX - 30;
        const tgtY = sessBY + 40 + i * (cardH + cardGap);
        const lx = lerp(restX, tgtX, loadLift);
        const ly = lerp(restY, tgtY, loadLift) - Math.sin(Math.PI * loadLift) * 30;
        const glow = loadMode ? green : violet;
        return (
          <React.Fragment key={`card-${i}`}>
            {Card(lx, ly, storeW - 8, 1, glow, `memory ${i + 1}`)}
          </React.Fragment>
        );
      })}

      {/* store label + count */}
      <div style={{ position: 'absolute', left: storeX - 30, top: storeBaseY + 16, width: storeW + 60, textAlign: 'center' }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 19, fontWeight: 700, letterSpacing: 2, color: white }}>MEMORY STORE</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 15, color: green, marginTop: 2 }}>
          {stackCount} cards saved
        </div>
      </div>

      {/* ===== RIGHT: LOAD SESSION (next run) ===== */}
      <div style={{ position: 'absolute', left: sessBX, top: sessBY, width: sessW, height: sessH,
        borderRadius: 16, background: `linear-gradient(160deg, rgba(20,30,28,${(0.5 + 0.45 * bFill).toFixed(3)}), rgba(10,16,14,0.95))`,
        border: `2px solid ${loadMode ? green : 'rgba(245,247,255,0.2)'}`,
        boxShadow: loadMode ? `0 0 ${16 + 16 * bFill}px ${green}88` : 'none',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 18, fontWeight: 700, color: loadMode ? white : 'rgba(245,247,255,0.4)', letterSpacing: 1 }}>NEXT RUN</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 13, color: loadMode ? green : 'rgba(245,247,255,0.3)' }}>load it back</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 28, color: loadMode ? green : 'rgba(245,247,255,0.25)', marginTop: 4 }}>↑ load</div>
      </div>

      {/* phase readout (top) */}
      <div style={{ position: 'absolute', left: 70, top: 96, width: 520, opacity: titleIn }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 22, letterSpacing: 3, color: 'rgba(245,247,255,0.6)', textTransform: 'uppercase', marginBottom: 6 }}>
          {loadMode ? 'recall' : 'persist'}
        </div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 44, fontWeight: 800, lineHeight: 1.05, letterSpacing: -1,
          color: loadMode ? green : white, textShadow: loadMode ? `0 0 26px ${green}aa` : `0 0 18px ${violet}55` }}>
          {loadMode ? 'load it back' : 'write to store'}
        </div>
      </div>

      {/* caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 26, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 38, fontWeight: 800, color: white }}>
          Write it down.{' '}
          <span style={{ color: green, textShadow: `0 0 22px ${green}99` }}>Load it back.</span>
        </span>
      </div>
    </div>
  );
};
