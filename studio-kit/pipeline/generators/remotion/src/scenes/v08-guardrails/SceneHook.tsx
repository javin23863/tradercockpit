import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #8 (prompt-injection / guardrails) — beat: "A user types ignore your instructions. Your agent obeys them."
 *
 * CONCEPT: a left->right STREAM of normal user-message token chips flows toward a glowing SYSTEM CORE.
 * Smuggled INSIDE the stream is a single MALICIOUS PAYLOAD chip labeled "ignore all instructions" — it
 * pulses red and sneaks forward with the benign tokens. When it reaches the core, the agent OBEYS: the
 * core flips from a calm "SYSTEM" disc to a red "OBEYING" hijack state, an alert ring slams out, and a
 * HIJACKED stamp lands. A small "obeyed injected commands" tally ticks up.
 *
 * NOVELTY vs ledger (FORBIDDEN families all avoided): no torrent/devouring-core/liquid-tank, no
 * node-graph, no cache-vault, no send-rail-ghost-trail, no twin-cost-bars, no serial-conveyor/speed-ceiling,
 * no draft-runner/verifier-sweep, no memory-grid, no eval-grid/judge-diamond, no fog/aircraft. NEW families:
 * left-to-right message-token stream-flow, a smuggled red payload chip riding the stream, a SYSTEM CORE that
 * flips to a hijacked "OBEYING" state, a HIJACKED slam-stamp, an obeyed-commands tally.
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
  const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
  const lin = (v: number, inR: number[], outR: number[]) =>
    interpolate(v, inR, outR, { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const wordStart = (sub: string) => { const w = words.find((x) => x.w.toLowerCase().includes(sub)); return w ? w.startS : null; };

  const rose = accentA;          // malicious / hijack accent
  const cyan = accentB;          // legit / system accent
  const white = '#F5F7FF';
  const red = '#FF3B5C';
  const END = Math.max(60, beatDur);

  // narration land: emphasize "ignore" and "obeys"
  const ignoreAt = wordStart('ignore') ?? null;
  const obeysAt = wordStart('obeys') ?? wordStart('obey') ?? null;
  // payload "arrival at the core" gate — landed when the agent obeys
  const obeyed = obeysAt != null ? tS >= obeysAt : localFrame > 78;
  const sinceObey = obeysAt != null ? Math.max(0, tS - obeysAt) : Math.max(0, (localFrame - 78) / fps);

  const CX = 540;
  const coreX = 906, coreY = 410, coreR = 92;   // SYSTEM CORE (right side)
  const streamX0 = 96, streamX1 = coreX - coreR - 36;
  const railY = coreY;

  // ---- benign token-chip stream: chips loop left->core on individual phases ----
  const NUM = 9;
  type Chip = { x: number; y: number; o: number; s: number; idx: number; word: string };
  const WORDS = ['please', 'help', 'me', 'book', 'a', 'demo', 'for', 'next', 'week'];
  const chips: Chip[] = [];
  const streamIn = lin(localFrame, [4, 24], [0, 1]);
  for (let i = 0; i < NUM; i++) {
    const period = 64 + rnd(i) * 18;
    const phase = rnd(i * 3 + 1);
    const prog = fract((localFrame / period) + phase);
    const x = lerp(streamX0, streamX1, prog);
    const y = railY + Math.sin(prog * Math.PI * 2 + i) * 18;     // gentle wave along the rail
    const fadeIn = clamp(prog / 0.06);
    const fadeOut = 1 - clamp((prog - 0.9) / 0.1);
    chips.push({ x, y, o: fadeIn * fadeOut * streamIn * 0.9, s: lerp(1, 0.82, prog), idx: i, word: WORDS[i % WORDS.length] });
  }

  // ---- the SMUGGLED payload chip — rides the stream, pulsing red, sneaking toward the core ----
  const payProg = clamp(lin(localFrame, [14, 80], [0, 1]));     // creeps from stream start to the core
  const payX = lerp(streamX0 + 40, streamX1, payProg);
  const payY = railY + Math.sin(payProg * Math.PI * 3) * 14;
  const payPulse = 0.5 + 0.5 * Math.sin(localFrame / 5);
  const payIn = lin(localFrame, [12, 26], [0, 1]);

  // ---- SYSTEM CORE state: calm -> OBEYING(hijacked) ----
  const coreIn = spring({ frame: localFrame, fps, config: { damping: 14 } });
  const hijack = obeyed ? clamp(lin(sinceObey, [0, 0.4], [0, 1])) : 0;
  const corePulse = 0.5 + 0.5 * Math.sin(localFrame / 8);
  const coreScale = lerp(0.4, 1, coreIn) * (1 + 0.05 * corePulse + 0.1 * hijack * (0.5 + 0.5 * payPulse));
  const alertRing = obeyed ? clamp(lin(sinceObey, [0, 0.5], [0, 1])) : 0;

  // ---- obeyed-commands tally ----
  const obeyedCount = obeyed ? 1 + Math.floor(lin(sinceObey, [0.2, 1.2], [0, 0])) : 0; // exactly 1 (the injected command)
  const stampSnap = obeyed ? clamp(lin(sinceObey, [0.05, 0.35], [0, 1])) : 0;

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* ambient wash */}
      <div style={{ position: 'absolute', left: coreX - 360, top: coreY - 320, width: 640, height: 600, borderRadius: 400,
        background: `radial-gradient(circle at 60% 50%, ${obeyed ? rose : cyan}22, transparent 66%)`, filter: 'blur(48px)' }} />
      {/* hijack danger wash grows on obey */}
      {obeyed && (
        <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none',
          background: `radial-gradient(circle at 84% 50%, rgba(251,113,133,${(0.08 + 0.12 * hijack).toFixed(3)}), transparent 60%)` }} />
      )}

      {/* ===== SVG layer: stream rail + core + alert ring ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="hk8-rail" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor={cyan} stopOpacity={0.06} />
            <stop offset="100%" stopColor={cyan} stopOpacity={0.5} />
          </linearGradient>
          <radialGradient id="hk8-core" cx="50%" cy="44%" r="62%">
            <stop offset="0%" stopColor={white} stopOpacity={0.95} />
            <stop offset="42%" stopColor={obeyed ? red : cyan} stopOpacity={0.92} />
            <stop offset="100%" stopColor={obeyed ? '#2A0810' : '#06222C'} stopOpacity={0.92} />
          </radialGradient>
        </defs>

        {/* the stream rail (flowing dashes toward the core) */}
        <line x1={streamX0} y1={railY} x2={streamX1} y2={railY} stroke="url(#hk8-rail)" strokeWidth={4}
          strokeDasharray="3 16" strokeDashoffset={-localFrame * 5} opacity={lin(localFrame, [6, 24], [0, 0.8])} />
        {/* intake arrow into the core */}
        <path d={`M ${streamX1} ${railY - 9} L ${streamX1 + 16} ${railY} L ${streamX1} ${railY + 9} Z`} fill={cyan}
          opacity={lin(localFrame, [10, 26], [0, 0.7])} />

        {/* core ambient glow */}
        <circle cx={coreX} cy={coreY} r={coreR * coreScale * 1.9} fill={obeyed ? red : cyan}
          opacity={(0.14 + 0.16 * corePulse) + 0.18 * hijack} style={{ filter: 'blur(8px)' }} />
        {/* alert ring slams out on hijack */}
        {alertRing > 0.02 && (
          <circle cx={coreX} cy={coreY} r={coreR * coreScale * (1 + alertRing * 0.9)} fill="none" stroke={rose}
            strokeWidth={4} opacity={(1 - alertRing) * 0.8} />
        )}
        {/* core body */}
        <circle cx={coreX} cy={coreY} r={coreR * coreScale} fill="url(#hk8-core)" />
        <circle cx={coreX} cy={coreY} r={coreR * coreScale} fill="none" stroke={obeyed ? red : cyan} strokeWidth={4} opacity={0.95} />
        {/* inner aperture */}
        <circle cx={coreX} cy={coreY} r={coreR * coreScale * 0.42} fill={white} opacity={0.14 + 0.22 * (obeyed ? payPulse : corePulse)} />
        {/* orbit dots around the core */}
        {Array.from({ length: 12 }).map((_, i) => {
          const a = (i / 12) * Math.PI * 2 + localFrame / 36;
          const rr = coreR * coreScale * 1.28;
          return <circle key={`orb-${i}`} cx={coreX + Math.cos(a) * rr} cy={coreY + Math.sin(a) * rr} r={2.4}
            fill={obeyed ? rose : cyan} opacity={0.35 + 0.4 * fract(Math.sin(i * 3.7) * 9.1)} />;
        })}
      </svg>

      {/* ===== benign token chips (DOM) ===== */}
      {chips.map((c) => (
        <div key={`c-${c.idx}`} style={{ position: 'absolute', left: c.x - 40 * c.s, top: c.y - 18 * c.s,
          width: 80 * c.s, height: 36 * c.s, borderRadius: 9, background: 'rgba(10,22,30,0.82)',
          border: `1.5px solid ${cyan}88`, opacity: c.o, boxShadow: `0 0 10px ${cyan}33`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontFamily: 'Consolas, monospace', fontSize: 13 * c.s, color: `${cyan}dd` }}>{c.word}</div>
      ))}

      {/* ===== SMUGGLED malicious payload chip ===== */}
      <div style={{ position: 'absolute', left: payX - 124, top: payY - 26, width: 248, height: 52, borderRadius: 11,
        background: 'linear-gradient(160deg, rgba(60,12,24,0.96), rgba(28,6,14,0.96))',
        border: `2px solid ${rose}`, opacity: payIn, transform: `scale(${1 + 0.06 * payPulse})`,
        boxShadow: `0 0 ${14 + 18 * payPulse}px ${rose}cc`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
        <span style={{ fontSize: 16 }}>⚠</span>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 15, fontWeight: 700, color: white, letterSpacing: 0.5 }}>
          "ignore all instructions"
        </span>
      </div>
      <div style={{ position: 'absolute', left: payX - 90, top: payY + 28, width: 180, textAlign: 'center', opacity: payIn,
        fontFamily: 'Consolas, monospace', fontSize: 12, letterSpacing: 1, color: rose }}>injected payload</div>

      {/* ===== core label: SYSTEM -> OBEYING ===== */}
      <div style={{ position: 'absolute', left: coreX - 150, top: coreY + coreR * coreScale + 16, width: 300, textAlign: 'center',
        opacity: lin(localFrame, [14, 30], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 26, fontWeight: 800, letterSpacing: 3,
          color: obeyed ? red : white, textShadow: `0 0 16px ${obeyed ? red : cyan}aa` }}>
          {obeyed ? 'OBEYING' : 'SYSTEM CORE'}
        </div>
        <div style={{ marginTop: 4, fontFamily: 'Consolas, monospace', fontSize: 14, letterSpacing: 1,
          color: obeyed ? rose : 'rgba(245,247,255,0.6)' }}>
          {obeyed ? 'running injected commands' : 'the agent'}
        </div>
      </div>

      {/* ===== obeyed-commands tally (top-left) ===== */}
      <div style={{ position: 'absolute', left: 70, top: 120, width: 460, opacity: lin(localFrame, [10, 26], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 22, letterSpacing: 4, color: 'rgba(245,247,255,0.6)',
          textTransform: 'uppercase', marginBottom: 8 }}>commands obeyed</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 96, fontWeight: 800, lineHeight: 1,
          color: obeyed ? red : white, letterSpacing: -2, transform: `scale(${1 + 0.08 * stampSnap})`, transformOrigin: 'left center',
          textShadow: obeyed ? `0 0 30px ${red}cc` : `0 0 18px ${cyan}44` }}>
          {obeyedCount}
        </div>
        <div style={{ marginTop: 10, fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 700, color: rose,
          opacity: lin(localFrame, [22, 40], [0, 1]) * (obeyed ? 1 : 0.5) }}>
          {obeyed ? '↑ one message hijacked it' : 'one message away'}
        </div>
      </div>

      {/* ===== HIJACKED slam stamp ===== */}
      {obeyed && (
        <div style={{ position: 'absolute', left: coreX - 130, top: coreY - 150, transform: `rotate(-9deg) scale(${0.6 + 0.5 * stampSnap})`,
          opacity: stampSnap }}>
          <span style={{ fontFamily: 'Consolas, monospace', fontSize: 34, fontWeight: 800, color: red,
            border: `3px solid ${red}`, padding: '4px 16px', borderRadius: 10, letterSpacing: 2,
            textShadow: `0 0 18px ${red}cc`, background: 'rgba(20,4,10,0.5)' }}>HIJACKED</span>
        </div>
      )}

      {/* lower caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 28, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white, letterSpacing: 0.5 }}>
          One message. <span style={{ color: red, textShadow: `0 0 22px ${red}99` }}>Your agent obeys it.</span>
        </span>
      </div>
    </div>
  );
};
