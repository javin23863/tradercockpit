import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #5 (persistent memory) — beat: "Every new session, your agent forgets everything it ever learned."
 *
 * CONCEPT: a CONTEXT-WINDOW panel fills with glowing memory tokens during a session, then on each new
 * SESSION boundary the panel WIPES TO BLANK and every token EVAPORATES upward as fading sparks — a
 * goldfish/reset loop. A SESSION counter ticks up each wipe; a "RETAINED" gauge stays pinned at 0% no
 * matter how many sessions pass. The agent learns, forgets, learns, forgets.
 *
 * NOVELTY (vs ledger — forbidden families avoided): no particle-torrent/devouring-core/liquid-tank,
 * no send-rail/cache-vault, no twin-cost-bars, no node-graph/typewriter/glass-card. NEW families:
 * a periodic session-wipe flash, memory-evaporation sparks rising off the cleared panel, a RETAINED-0%
 * gauge that refuses to move, and a reset-loop session counter.
 *
 * RENDER-SAFE: imports only react + remotion (interpolate/spring). No useCurrentFrame/AbsoluteFill/three.
 * No Math.random/Date.now/new Date (deterministic rnd). All interpolate input ranges strictly increasing
 * (prop-derived ends guarded with Math.max). Manual number formatting. Stays inside 1080x820.
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

  const violet = accentA;
  const amber = accentB;
  const white = '#F5F7FF';
  const red = '#FF3B5C';
  const END = Math.max(60, beatDur);

  // narration: emphasize "forgets" and "everything"
  const forgetsAt = wordStart('forget') ?? null;
  const forgetHit = forgetsAt != null && tS >= forgetsAt;

  // ---- stage geometry (within 1080x820) ----
  const panelX = 150, panelY = 196, panelW = 520, panelH = 360; // the context window
  const cols = 6, rows = 5; // memory-token grid

  // ===================================================================
  // SESSION RESET CADENCE — a wipe fires on a steady beat; tokens fill,
  // then evaporate, then a fresh (empty) session begins. Loop forever.
  // ===================================================================
  const sessionLen = 1.55; // seconds per session cycle
  const startDelay = 0.25;
  const sFloat = Math.max(0, (tS - startDelay)) / sessionLen;
  const sessionCount = Math.floor(sFloat) + 1; // SESSION #
  const sPhase = fract(sFloat);                 // 0..1 inside the current session

  // within a session: 0..0.62 = tokens fill in; 0.62..0.80 = WIPE/evaporate; 0.80..1 = blank
  const fillT = clamp(lin(sPhase, [0.02, 0.58], [0, 1]));
  const wipeT = clamp(lin(sPhase, [0.62, 0.80], [0, 1]));   // 0 -> 1 as the panel clears
  const wipeFlash = Math.exp(-Math.max(0, sPhase - 0.62) * 22); // sharp flash at the wipe instant
  const blank = sPhase > 0.80;

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);
  const panelShake = wipeFlash * (rnd(sessionCount) - 0.5) * 10;

  // tokens: a grid that lights up during fill, then is wiped
  type Tok = { x: number; y: number; lit: number; key: number };
  const toks: Tok[] = [];
  const cellW = (panelW - 64) / cols;
  const cellH = (panelH - 80) / rows;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const k = r * cols + c;
      const order = (k + 0.5) / (cols * rows); // fill order across the grid
      const appear = clamp((fillT - order * 0.85) / 0.18);
      const lit = blank ? 0 : appear * (1 - wipeT);
      toks.push({
        x: panelX + 40 + c * cellW + cellW / 2,
        y: panelY + 56 + r * cellH + cellH / 2,
        lit,
        key: k,
      });
    }
  }

  // evaporation sparks: during the wipe window, tokens rise + fade upward off the panel
  const sparks: { x: number; y: number; o: number; s: number }[] = [];
  if (wipeT > 0 && wipeT < 1) {
    for (let i = 0; i < 26; i++) {
      const sx = panelX + 30 + rnd(i + sessionCount * 7) * (panelW - 60);
      const baseY = panelY + 40 + rnd2(i + sessionCount * 3) * (panelH - 60);
      const rise = wipeT * (90 + rnd(i) * 70);
      const o = clamp(lin(wipeT, [0, 0.15, 0.7, 1], [0, 0.9, 0.6, 0])) * (0.4 + 0.6 * rnd2(i));
      sparks.push({ x: sx, y: baseY - rise, o, s: 3 + rnd(i * 5) * 4 });
    }
  }

  // ===================================================================
  // RETAINED gauge — semicircle that NEVER moves off 0% (the joke: it forgets)
  // ===================================================================
  const gCx = 830, gCy = 470, gR = 96;
  // it twitches toward filling during each session, then snaps back to 0 on the wipe
  const gaugeTry = fillT * 0.0; // intentionally zero retained — context is lost every time
  const retainedPct = 0;
  // arc path helper (semicircle, left->right)
  const arcPoint = (t: number) => {
    const a = Math.PI - t * Math.PI; // PI..0
    return { x: gCx + Math.cos(a) * gR, y: gCy - Math.sin(a) * gR };
  };
  const p0 = arcPoint(0), p1 = arcPoint(1);

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* ambient wash */}
      <div style={{ position: 'absolute', left: panelX - 60, top: panelY - 120, width: 760, height: 620, borderRadius: 420,
        background: `radial-gradient(circle at 40% 40%, ${violet}1f, transparent 66%)`, filter: 'blur(48px)' }} />

      {/* ===== CONTEXT WINDOW PANEL (wipes to blank each session) ===== */}
      <div style={{ position: 'absolute', left: panelX + panelShake, top: panelY, width: panelW, height: panelH,
        borderRadius: 20, background: 'linear-gradient(160deg, rgba(22,18,40,0.92), rgba(10,8,22,0.95))',
        border: `2px solid ${blank ? red : violet}`,
        boxShadow: `0 0 ${22 + 40 * wipeFlash}px ${(blank ? red : violet)}aa, inset 0 0 60px rgba(0,0,0,0.5)` }}>
        {/* panel title bar */}
        <div style={{ position: 'absolute', top: 12, left: 20, right: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontFamily: 'Consolas, monospace', fontSize: 17, letterSpacing: 2, color: 'rgba(245,247,255,0.65)' }}>CONTEXT WINDOW</span>
          <span style={{ fontFamily: 'Consolas, monospace', fontSize: 17, fontWeight: 800, color: blank ? red : amber }}>
            {blank ? 'WIPED' : 'filling'}
          </span>
        </div>
        {/* blank-flash overlay on wipe */}
        <div style={{ position: 'absolute', inset: 2, borderRadius: 18, background: `rgba(255,255,255,${(0.5 * wipeFlash).toFixed(3)})`, pointerEvents: 'none' }} />
      </div>

      {/* ===== memory tokens (DOM chips lighting up, then cleared) ===== */}
      {toks.map((t) => (
        <div key={`tk-${t.key}`} style={{ position: 'absolute', left: t.x - 24 + panelShake, top: t.y - 12, width: 48, height: 24,
          borderRadius: 6, background: `rgba(139,92,246,${(0.18 + 0.5 * t.lit).toFixed(3)})`,
          border: `1.5px solid ${amber}`, opacity: t.lit, boxShadow: `0 0 ${10 * t.lit}px ${amber}88`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'Consolas, monospace', fontSize: 11, color: white }}>
          mem
        </div>
      ))}

      {/* ===== evaporation sparks rising off the cleared panel ===== */}
      {sparks.map((sp, i) => (
        <div key={`sp-${i}`} style={{ position: 'absolute', left: sp.x, top: sp.y, width: sp.s, height: sp.s,
          borderRadius: sp.s, background: amber, opacity: sp.o, boxShadow: `0 0 8px ${amber}cc` }} />
      ))}

      {/* loop arrow under the panel (goldfish reset loop) */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <path d={`M ${panelX + 60} ${panelY + panelH + 40} a 90 26 0 1 0 ${panelW - 120} 0`} fill="none"
          stroke={`${violet}aa`} strokeWidth={3} strokeDasharray="4 12" strokeDashoffset={-localFrame * 5} />
        <path d={`M ${panelX + 60} ${panelY + panelH + 40} l -10 -8 l 0 16 Z`} fill={violet} opacity={0.9} />

        {/* RETAINED semicircle gauge — track + (zero) fill */}
        <path d={`M ${p0.x} ${p0.y} A ${gR} ${gR} 0 0 1 ${p1.x} ${p1.y}`} fill="none"
          stroke="rgba(245,247,255,0.18)" strokeWidth={16} strokeLinecap="round" />
        {/* the needle stuck at 0 (far left), twitching on each wipe but never advancing */}
        {(() => {
          const twitch = wipeFlash * 0.10; // small twitch, snaps back
          const np = arcPoint(twitch);
          return <line x1={gCx} y1={gCy} x2={np.x} y2={np.y} stroke={red} strokeWidth={5} strokeLinecap="round" />;
        })()}
        <circle cx={gCx} cy={gCy} r={7} fill={red} />
      </svg>

      {/* gauge label */}
      <div style={{ position: 'absolute', left: gCx - 120, top: gCy + 14, width: 240, textAlign: 'center' }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 20, letterSpacing: 3, color: 'rgba(245,247,255,0.6)', textTransform: 'uppercase' }}>retained</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 64, fontWeight: 800, lineHeight: 1, color: red,
          textShadow: `0 0 26px ${red}aa`, transform: `scale(${1 + 0.08 * wipeFlash})`, transformOrigin: 'center' }}>
          {retainedPct}%
        </div>
      </div>

      {/* SESSION counter (top-left) — ticks up every wipe */}
      <div style={{ position: 'absolute', left: 70, top: 96, width: 360, opacity: lin(localFrame, [8, 24], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 22, letterSpacing: 4, color: 'rgba(245,247,255,0.6)', textTransform: 'uppercase', marginBottom: 6 }}>session</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 80, fontWeight: 800, lineHeight: 1, color: white,
          letterSpacing: -1, transform: `scale(${1 + 0.10 * wipeFlash})`, transformOrigin: 'left center',
          textShadow: `0 0 22px ${violet}66` }}>
          #{sessionCount}
        </div>
        <div style={{ marginTop: 10, fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 700, color: forgetHit ? red : amber,
          opacity: lin(localFrame, [22, 40], [0, 1]) }}>
          ↺ starts from zero
        </div>
      </div>

      {/* lower caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 26, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white, letterSpacing: 0.5 }}>
          Every session, it{' '}
          <span style={{ color: red, textShadow: `0 0 22px ${red}99` }}>forgets everything.</span>
        </span>
      </div>
    </div>
  );
};
