import React from 'react';
import { interpolate, spring } from 'remotion';

/**
 * VIDEO #7 (strict JSON) — beat: "Every response parses. Zero retry loops."
 *
 * CONCEPT: a column of incoming responses runs through the parser; each row's status pip FLIPS from red
 * ERROR to green VALID as a check-sweep passes it (every one parses now). A big PARSER-STATUS LIGHT flips
 * hard from red "ERROR" to green "VALID", and a RETRY-LOOP odometer counts DOWN to 0 with a "0" snap on
 * "zero". A parse-success ring fills to 100%.
 *
 * NOVELTY (vs ledger — all FORBIDDEN families avoided): no twin-cost-bars, no delta-bracket, no
 * radial-gauge-SWEEP (this is a fill RING from a different family + status-flip rows), no minus-90-snap.
 * NEW families: per-row status-pip flip (red→green) cascade, big parser-status-light hard flip, retry
 * odometer COUNT-DOWN to a zero-snap, parse-success fill ring.
 *
 * RENDER-SAFE: react + remotion only. No useCurrentFrame/AbsoluteFill/three. No Math.random/Date.now.
 * Strictly-increasing interpolate ranges. Deterministic formatting. 1080x820.
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

  const cyan = accentA;
  const green = accentB;
  const white = '#F5F7FF';
  const red = '#FF3B5C';

  const zeroAt = wordStart('zero') ?? wordStart('retry') ?? null;
  const parseAt = wordStart('parses') ?? wordStart('every') ?? null;
  const zeroSnap = zeroAt != null ? clamp(lin(tS - zeroAt, [0, 0.35], [0, 1])) : clamp(lin(localFrame, [70, 86], [0, 1]));

  // rows of responses, each flips red→green as the sweep passes (cascade)
  const ROWS = 7;
  const rowX = 130, rowY0 = 250, rowW = 470, rowH = 50, rowGap = 12;
  const flipStart = 14;
  const flipStep = 7;

  // big status light flips once a majority have gone green
  const allGreen = localFrame > flipStart + ROWS * flipStep + 4;
  const statusFlip = clamp(lin(localFrame, [flipStart + ROWS * flipStep, flipStart + ROWS * flipStep + 8], [0, 1]));
  const okBlink = allGreen ? 0.55 + 0.45 * Math.sin(localFrame / 7) : 0;

  // parse-success fill ring: climbs to 100%
  const ringPct = clamp(lin(localFrame, [16, flipStart + ROWS * flipStep + 6], [0, 1]));
  const pctVal = Math.round(ringPct * 100);
  const rcx = 800, rcy = 300, rr = 110;
  const circ = 2 * Math.PI * rr;

  // retry odometer counts DOWN from a high number to 0, snaps to 0 on "zero"
  const retryStart = 17;
  const retryCountDown = Math.round(lerp(retryStart, 0, clamp(lin(localFrame, [20, 72], [0, 1]))));
  const retryDisplay = zeroSnap >= 0.5 ? 0 : retryCountDown;

  const sceneIn = lin(localFrame, [0, 10], [0, 1]);

  return (
    <div style={{ position: 'absolute', inset: 0, fontFamily: 'Archivo, system-ui, sans-serif', opacity: sceneIn }}>
      {/* ambient wash */}
      <div style={{ position: 'absolute', left: 540 - 360, top: 200, width: 720, height: 560, borderRadius: 380,
        background: `radial-gradient(circle at 50% 50%, ${green}1c, transparent 66%)`, filter: 'blur(48px)' }} />

      {/* eyebrow */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 92, textAlign: 'center', opacity: lin(localFrame, [4, 20], [0, 1]),
        fontFamily: 'Consolas, monospace', fontSize: 24, letterSpacing: 6, color: 'rgba(245,247,255,0.6)', textTransform: 'uppercase' }}>
        every response · parsed
      </div>

      {/* ===== rows of responses flipping red ERROR -> green VALID ===== */}
      {Array.from({ length: ROWS }).map((_, i) => {
        const y = rowY0 + i * (rowH + rowGap);
        const t0 = flipStart + i * flipStep;
        const flip = clamp(lin(localFrame, [t0, t0 + 5], [0, 1]));   // 0=red, 1=green
        const isGreen = flip > 0.5;
        const col = isGreen ? green : red;
        const pop = i === ROWS - 1 ? 1 : 1; // (kept simple/deterministic)
        return (
          <div key={`row-${i}`} style={{ position: 'absolute', left: rowX, top: y, width: rowW, height: rowH,
            borderRadius: 9, background: `rgba(${isGreen ? '16,28,24' : '30,12,18'},0.9)`,
            border: `2px solid ${col}`, boxShadow: `0 0 ${8 + 8 * flip}px ${col}55`,
            display: 'flex', alignItems: 'center', padding: '0 16px', gap: 14,
            opacity: lin(localFrame, [6 + i, 18 + i], [0, 1]), transform: `scale(${0.97 + 0.03 * flip})` }}>
            {/* status pip */}
            <div style={{ width: 22, height: 22, borderRadius: 11, background: col, flexShrink: 0,
              boxShadow: `0 0 10px ${col}`, display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: 'Consolas, monospace', fontSize: 14, color: '#0A0A12', fontWeight: 800 }}>
              {isGreen ? '✓' : '!'}
            </div>
            <span style={{ fontFamily: 'Consolas, monospace', fontSize: 18, color: 'rgba(245,247,255,0.7)' }}>
              response_{i + 1}.json
            </span>
            <span style={{ marginLeft: 'auto', fontFamily: 'Consolas, monospace', fontSize: 17, fontWeight: 700,
              color: col, letterSpacing: 1 }}>{isGreen ? 'VALID' : 'ERROR'}</span>
          </div>
        );
      })}

      {/* ===== parse-success fill RING ===== */}
      <svg width={1080} height={820} viewBox="0 0 1080 820" style={{ position: 'absolute', inset: 0 }}>
        <circle cx={rcx} cy={rcy} r={rr} fill="none" stroke={'rgba(245,247,255,0.12)'} strokeWidth={16} />
        <circle cx={rcx} cy={rcy} r={rr} fill="none" stroke={green} strokeWidth={16} strokeLinecap="round"
          strokeDasharray={`${(circ * ringPct).toFixed(1)} ${circ.toFixed(1)}`}
          transform={`rotate(-90 ${rcx} ${rcy})`} style={{ filter: `drop-shadow(0 0 10px ${green}aa)` }} />
        {ringPct >= 0.999 && (
          <circle cx={rcx} cy={rcy} r={rr + 10} fill="none" stroke={green} strokeWidth={3}
            opacity={okBlink * 0.5} />
        )}
      </svg>
      <div style={{ position: 'absolute', left: rcx - 110, top: rcy - 56, width: 220, textAlign: 'center' }}>
        <div style={{ fontFamily: 'Consolas, monospace', fontSize: 66, fontWeight: 800, lineHeight: 1, color: green,
          letterSpacing: -2, textShadow: `0 0 24px ${green}aa` }}>{pctVal}%</div>
        <div style={{ marginTop: 4, fontFamily: 'Consolas, monospace', fontSize: 18, letterSpacing: 2, color: 'rgba(245,247,255,0.65)' }}>
          parse rate
        </div>
      </div>

      {/* ===== big PARSER-STATUS LIGHT: hard flip ERROR -> VALID ===== */}
      <div style={{ position: 'absolute', left: rcx - 150, top: rcy + 90, width: 300, textAlign: 'center',
        opacity: lin(localFrame, [10, 24], [0, 1]) }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 12, padding: '8px 20px', borderRadius: 12,
          border: `2px solid ${allGreen ? green : red}`, background: 'rgba(8,10,18,0.7)',
          boxShadow: allGreen ? `0 0 ${10 + 16 * okBlink}px ${green}66` : `0 0 12px ${red}44` }}>
          <div style={{ width: 26, height: 26, borderRadius: 13, background: allGreen ? green : red,
            opacity: allGreen ? okBlink : 0.85, boxShadow: `0 0 12px ${allGreen ? green : red}` }} />
          <span style={{ fontFamily: 'Consolas, monospace', fontSize: 34, fontWeight: 800, letterSpacing: 2,
            color: allGreen ? green : red, textShadow: `0 0 18px ${allGreen ? green : red}aa` }}>
            {allGreen ? 'VALID' : 'ERROR'}
          </span>
        </div>
      </div>

      {/* ===== retry-loop odometer counting DOWN to 0 ===== */}
      <div style={{ position: 'absolute', left: 130, top: rowY0 + ROWS * (rowH + rowGap) + 22, width: 470,
        opacity: lin(localFrame, [18, 32], [0, 1]) }}>
        <span style={{ fontFamily: 'Consolas, monospace', fontSize: 22, fontWeight: 700, color: 'rgba(245,247,255,0.6)' }}>
          ↻ retry loops:
        </span>
        <span style={{ marginLeft: 14, fontFamily: 'Consolas, monospace', fontSize: 56, fontWeight: 800,
          color: retryDisplay === 0 ? green : red, letterSpacing: -1,
          transform: `scale(${1 + 0.18 * zeroSnap * (retryDisplay === 0 ? 1 : 0)})`, display: 'inline-block',
          transformOrigin: 'left center', textShadow: retryDisplay === 0 ? `0 0 24px ${green}cc` : `0 0 16px ${red}88` }}>
          {retryDisplay}
        </span>
      </div>

      {/* caption */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 26, textAlign: 'center', opacity: lin(localFrame, [16, 34], [0, 1]) }}>
        <span style={{ fontSize: 40, fontWeight: 800, color: white }}>
          Every response parses. <span style={{ color: green, textShadow: `0 0 22px ${green}99` }}>Zero retry loops.</span>
        </span>
      </div>
    </div>
  );
};
