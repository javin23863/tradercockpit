import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #7 (strict JSON) — beat: "Constrain the output to a schema. The model can only emit valid fields."
 *
 * CONCEPT: a rigid SCHEMA MOLD / die-stamp descends and PRESSES the raw output through it. What comes out
 * the bottom is forced into the mold's shape — clean, aligned JSON key:value FIELDS that SNAP into pre-cut
 * slots one by one (spring overshoot per snap). The mold shows the required keys as cut-out cavities; only
 * a value that fits the cavity passes. A "schema-locked" seal sets once all fields have snapped home.
 *
 * NOVELTY (vs ledger — all FORBIDDEN families avoided): no node-graph, no cache-vault, no lanes, no
 * conveyor, no draft/verifier sweep, no gauge. NEW families: descending schema die-stamp press with a
 * compression squash, key-cavity cut-outs in the die, field-into-slot snap (spring), schema-lock seal.
 *
 * RENDER-SAFE: react + remotion only. No useCurrentFrame/AbsoluteFill/three. No Math.random/Date.now.
 * Strictly-increasing interpolate ranges. Deterministic formatting. 1080x820.
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
  const amber = '#FFC542';
  const END = Math.max(60, beatDur);

  const schemaAt = wordStart('schema') ?? null;
  const validAt = wordStart('valid') ?? wordStart('fields') ?? null;
  const pressed = schemaAt != null ? clamp(lin(tS - schemaAt, [0, 0.55], [0, 1])) : clamp(lin(localFrame, [18, 44], [0, 1]));
  const locked = validAt != null ? tS >= validAt : localFrame > 88;

  // ---- the four schema fields that snap into slots ----
  const FIELDS = [
    { key: 'intent', val: '"book_call"' },
    { key: 'date', val: '"2026-06-18"' },
    { key: 'priority', val: 'high' },
    { key: 'confirmed', val: 'true' },
  ];
  const stageX = 300, stageW = 480;       // the field column area
  const slotY0 = 318, slotH = 64, slotGap = 14;

  // die-stamp press: descends, presses, springs back slightly (the squash on contact)
  const pressDrop = clamp(lin(localFrame, [10, 30], [0, 1]));   // mold comes down
  const dieY = lerp(70, 250, pressDrop);
  const contact = pressDrop >= 1;
  const squash = contact ? Math.exp(-Math.max(0, localFrame - 30) / 6) : 0; // squash flash on contact

  // each field snaps into its slot in sequence, with a spring pop
  const snapStart = 34;
  const fieldState = FIELDS.map((f, i) => {
    const t0 = snapStart + i * 9;
    const sp = spring({ frame: Math.max(0, localFrame - t0), fps, config: { damping: 11, mass: 0.7 } });
    const present = localFrame >= t0;
    return { ...f, sp: clamp(sp), present, pop: present ? sp : 0 };
  });
  const snappedCount = fieldState.filter((f) => f.present).length;

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);
  const lockPulse = locked ? 0.5 + 0.5 * Math.sin(localFrame / 7) : 0;

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* ambient wash */}
      <div style={{ position: 'absolute', left: 540 - 360, top: 180, width: 720, height: 560, borderRadius: 380,
        background: `radial-gradient(circle at 50% 45%, ${green}1c, transparent 66%)`, filter: 'blur(48px)' }} />

      {/* ===== the SCHEMA DIE-STAMP (descends from top, presses) ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id="in7-die" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={cyan} stopOpacity={0.4} />
            <stop offset="100%" stopColor={'#0A1622'} stopOpacity={0.92} />
          </linearGradient>
        </defs>
        {/* die body (with the key cavities cut into its underside) */}
        <g transform={`translate(0, ${(squash * -6).toFixed(2)})`}>
          <rect x={stageX - 40} y={dieY - 150} width={stageW + 80} height={150} rx={12}
            fill="url(#in7-die)" stroke={cyan} strokeWidth={2.5} opacity={lin(localFrame, [6, 22], [0, 0.95])} />
          {/* SCHEMA label on the die */}
          <text x={540} y={dieY - 95} textAnchor="middle" fontFamily="Consolas, monospace" fontSize={26} fontWeight={700}
            fill={white} letterSpacing={4} opacity={lin(localFrame, [10, 24], [0, 0.9])}>SCHEMA · DIE</text>
          {/* key cavities — the required key cut-outs on the die underside */}
          {FIELDS.map((f, i) => {
            const cx = stageX + 30 + (i % 2) * 230;
            const cyy = dieY - 56 + Math.floor(i / 2) * 34;
            return <g key={`cav-${i}`}>
              <rect x={cx} y={cyy} width={196} height={24} rx={5} fill={'rgba(0,0,0,0.45)'}
                stroke={cyan} strokeWidth={1.5} opacity={lin(localFrame, [14, 26], [0, 0.8])} />
              <text x={cx + 10} y={cyy + 17} fontFamily="Consolas, monospace" fontSize={14} fill={cyan}
                opacity={lin(localFrame, [16, 28], [0, 0.85])}>{f.key}:</text>
            </g>;
          })}
          {/* press guide rails */}
          {[stageX - 40, stageX + stageW + 40].map((x, i) => (
            <line key={`rail-${i}`} x1={x} y1={20} x2={x} y2={dieY} stroke={'rgba(34,211,238,0.25)'} strokeWidth={2}
              strokeDasharray="3 10" strokeDashoffset={-localFrame * 3} opacity={lin(localFrame, [6, 22], [0, 0.7])} />
          ))}
        </g>

        {/* compression flash line where the die meets the output on contact */}
        {contact && squash > 0.04 && (
          <line x1={stageX - 30} y1={dieY + 4} x2={stageX + stageW + 30} y2={dieY + 4}
            stroke={white} strokeWidth={2 + 6 * squash} opacity={squash * 0.8}
            style={{ filter: `drop-shadow(0 0 8px ${cyan})` }} />
        )}

        {/* the output slot bed (pre-cut slots the fields snap into) */}
        {FIELDS.map((_, i) => {
          const y = slotY0 + i * (slotH + slotGap);
          return <rect key={`slot-${i}`} x={stageX} y={y} width={stageW} height={slotH} rx={10}
            fill={'rgba(8,12,22,0.6)'} stroke={'rgba(245,247,255,0.14)'} strokeWidth={1.5}
            strokeDasharray="6 8" opacity={lin(localFrame, [24, 36], [0, 0.9])} />;
        })}
      </svg>

      {/* ===== the clean JSON FIELDS snapping into the slots ===== */}
      {/* opening brace */}
      <div style={{ position: 'absolute', left: stageX - 40, top: slotY0 - 44, fontFamily: 'Consolas, monospace',
        fontSize: 40, fontWeight: 800, color: green, opacity: lin(localFrame, [30, 42], [0, 0.95]),
        textShadow: `0 0 14px ${green}66` }}>{'{'}</div>

      {fieldState.map((f, i) => {
        const y = slotY0 + i * (slotH + slotGap);
        // field enters from above (the press direction) and snaps to its slot
        const enterY = lerp(y - 110, y, f.pop);
        const op = f.present ? clamp(f.pop * 1.4) : 0;
        return (
          <div key={`field-${i}`} style={{ position: 'absolute', left: stageX + 14, top: enterY + 8,
            width: stageW - 28, height: slotH - 16, borderRadius: 8,
            background: 'linear-gradient(160deg, rgba(20,32,30,0.96), rgba(10,18,20,0.96))',
            border: `2px solid ${green}`, boxShadow: `0 0 ${10 + 8 * f.pop}px ${green}88`,
            transform: `scale(${0.9 + 0.1 * f.pop})`, opacity: op, display: 'flex', alignItems: 'center',
            justifyContent: 'space-between', padding: '0 18px', fontFamily: 'Consolas, monospace' }}>
            <span style={{ fontSize: 22, fontWeight: 700, color: cyan }}>"{f.key}"</span>
            <span style={{ fontSize: 16, color: 'rgba(245,247,255,0.4)' }}>:</span>
            <span style={{ fontSize: 22, fontWeight: 700, color: white }}>{f.val}{i < fieldState.length - 1 ? ',' : ''}</span>
          </div>
        );
      })}

      {/* closing brace */}
      <div style={{ position: 'absolute', left: stageX - 40, top: slotY0 + FIELDS.length * (slotH + slotGap) - 8,
        fontFamily: 'Consolas, monospace', fontSize: 40, fontWeight: 800, color: green,
        opacity: lin(localFrame, [snapStart + FIELDS.length * 9, snapStart + FIELDS.length * 9 + 12], [0, 0.95]),
        textShadow: `0 0 14px ${green}66` }}>{'}'}</div>

      {/* ===== SCHEMA-LOCKED seal (sets once all fields snapped) ===== */}
      {locked && (
        <div style={{ position: 'absolute', right: 70, top: 320, width: 200, textAlign: 'center',
          opacity: 0.6 + 0.4 * lockPulse, transform: `rotate(-7deg) scale(${1 + 0.06 * lockPulse})` }}>
          <div style={{ fontSize: 50, lineHeight: 1 }}>🔒</div>
          <div style={{ marginTop: 6, fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 800, letterSpacing: 2,
            color: green, border: `3px solid ${green}`, borderRadius: 10, padding: '6px 10px',
            textShadow: `0 0 16px ${green}cc` }}>SCHEMA<br />LOCKED</div>
        </div>
      )}

      {/* fields-emitted readout (top-left) */}
      <div style={{ position: 'absolute', left: 70, top: 120, width: 200, opacity: lin(localFrame, [12, 28], [0, 1]) }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 20, letterSpacing: 3, color: 'rgba(245,247,255,0.6)',
          textTransform: 'uppercase', marginBottom: 6 }}>valid fields</div>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 70, fontWeight: 800, lineHeight: 1, letterSpacing: -1,
          color: green, textShadow: `0 0 22px ${green}66` }}>{snappedCount}/{FIELDS.length}</div>
      </div>

      {/* caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 28, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white }}>
          Press it through a schema. <span style={{ color: green, textShadow: `0 0 22px ${green}99` }}>Only valid fields pass.</span>
        </span>
      </div>
    </div>
  );
};
