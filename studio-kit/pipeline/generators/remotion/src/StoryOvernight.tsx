//  (2026-06-10): StoryOvernight — "THE OVERNIGHT" direction (concept+visual upgrade).
// A Bloomberg-grade editorial title film. Concept: sell the future as ALREADY-ARRIVED, not as a tip.
// A single amber clock ticks past 3 AM in total stillness (the pattern-interrupt on a noisy feed),
// then the value lands as huge editorial type on near-black, climaxing in one colossal amber number,
// and the same clock returns reading 07:00 AM — you've literally watched a night pass. "While you
// slept" becomes something the viewer WITNESSED. Near-monochrome, ONE searing amber, awe over hype.
//
// 450 frames @ 30fps, 1080x1920. Beats: CLOCK 0-78 / HOOK+STAKES 78-155 / FIX 155-300 /
// PROOF(count) 300-366 / CTA 366-450. Props-compatible with StoryTipDeep (drop-in for the tip bank).
import React from 'react';
import {
  AbsoluteFill, Audio, staticFile,
  useCurrentFrame, useVideoConfig, interpolate, spring, Easing,
} from 'remotion';
import { CameraMotionBlur } from '@remotion/motion-blur';
import { fitFontSize } from './components/fitFontSize';

export interface StoryOvernightProps {
  tipId?: string;
  aiType?: string;
  hook?: string;
  stat?: string;
  problem?: string;
  steps?: string[];
  proof?: { kind?: string; from?: number; to?: number; unit?: string; prefix?: string; note?: string };
  result?: string;
  cta?: string;
  ctaVerb?: string;
  voSrc?: string;
  mbSamples?: number;
}

// Editorial heavy face — Arial Black renders instantly (no font-load race in render); Archivo if installed.
const FONT = '"Archivo Black", "Arial Black", "Helvetica Neue", system-ui, sans-serif';
const BODY = '"Archivo", "Helvetica Neue", "Segoe UI", system-ui, sans-serif';
const MONO = '"Consolas", "SF Mono", monospace';
// Near-monochrome grade — violet pulled OUT
const INK = '#050505';      // base
const PAPER = '#F4F1EA';    // warm paper-white type
const DIM = '#6E6A60';      // warm grey
const AMBER = '#FF8A00';    // searing accent
const HOT = '#FFB347';      // hot glow core
const GRAIN =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")";

const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };
const ramp = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
const beat = (f: number, inA: number, inB: number, outA: number, outB: number) =>
  Math.min(ramp(f, inA, inB), 1 - ramp(f, outA, outB));

const Scene: React.FC<StoryOvernightProps> = ({
  tipId = 'AI-NEWS-001',
  hook = 'IT SHIPPED 18 THINGS LAST NIGHT. YOU SLEPT.',
  stat = '24/7 AUTONOMOUS',
  problem = 'You’re asleep at the busywork an agent could run.',
  steps = ['Give it a goal in plain English', 'Wire it to your tools via MCP', 'Let it loop — ship, verify, repeat'],
  proof = { kind: 'counter', from: 0, to: 18, unit: '', prefix: '', note: 'shipped overnight — zero code' },
  result = 'An AI that works the night shift while you sleep.',
  cta = 'START',
  ctaVerb = 'Comment',
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();
  const X = 92; // left editorial margin

  // ── Camera: dead-still for the open, then a slow confident dolly + faint parallax ──
  const dollyPersp = interpolate(frame, [78, durationInFrames], [1700, 1240], { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const yaw = frame < 88 ? 0 : Math.sin((frame - 88) / 220) * interpolate(frame, [88, 170], [4.5, 1.6], clamp);
  const pitch = frame < 88 ? 0 : Math.cos(frame / 240) * 1.8;
  const keyDx = Math.sin(frame / 90) * 16, keyDy = Math.cos(frame / 110) * 13;

  // ── Beat opacities (cross-fades, no 3D turns) ──
  const oClock = beat(frame, 6, 30, 72, 84);
  const oHook = beat(frame, 80, 96, 150, 166);
  const oFix = beat(frame, 158, 176, 286, 300);
  const oProof = beat(frame, 300, 318, 416, 430);
  const oCta = ramp(frame, 424, 446);

  // ── Clock motif (03:14 → 03:15) ──
  const mins = Math.floor(interpolate(frame, [38, 58], [14, 15], clamp));
  const clockY = interpolate(frame, [72, 84], [0, -300], clamp);
  const ruleW = ramp(frame, 32, 68);

  // ── Hero reveal: clip-path wipe (top→down) ──
  const heroClip = interpolate(ramp(frame, 80, 98), [0, 1], [100, 0]);
  const heroShadow = interpolate(ramp(frame, 80, 116), [0, 1], [4, 38]);

  // ── PROOF: live overnight task feed ( B-blend — watch the agent ship 18 while you sleep) ──
  const DONE = '#3FB950';
  const lerpColor = (ha: string, hb: string, t: number) => {
    const a = parseInt(ha.slice(1), 16), b = parseInt(hb.slice(1), 16);
    const m = (sh: number) => Math.round(((a >> sh) & 255) + (((b >> sh) & 255) - ((a >> sh) & 255)) * t);
    return `rgb(${m(16)},${m(8)},${m(0)})`;
  };
  const LINES = ['enriched 142 cold leads', 'verified 38 mockup links', 'drafted 9 outreach replies', 'patched stripe webhook 404', 'reconciled 15 store charges', 'redeployed delivery CDN', 'scrubbed PII from 3 zips', 'posted IG story · daily tip', 'audited send-pipeline gate', 'backfilled 17 lead emails', 're-enabled stripe endpoint', 'rebuilt CRM revenue tile', 'scored 291 predictions', 'updated self-model', 'revived soma heartbeat', 'flagged 1 sponsor handoff', 'synced knowledge graph', 'shipped 18 — you slept'];
  const PROOF0 = 300, STAGGER = 6, HOLD = 5, ROW = 64, WINDOW = 9;
  const lineStart = (i: number) => PROOF0 + 6 + i * STAGGER;
  const flipAt = (i: number) => lineStart(i) + HOLD;
  const ts = (i: number) => { const s = 14 * 60 + 7 + i * 4; const mm = Math.floor(s / 60) % 60, ss = s % 60; return `03:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`; };
  const shippedCount = LINES.filter((_, i) => frame >= flipAt(i)).length;
  const visibleCount = LINES.filter((_, i) => frame >= lineStart(i)).length;
  const lastFlip = Math.max(PROOF0, ...LINES.map((_, i) => flipAt(i)).filter((f) => f <= frame));
  const countPop = interpolate(spring({ frame: frame - lastFlip, fps, config: { damping: 14, stiffness: 240 } }), [0, 1], [1.18, 1]);
  const conveyorY = -Math.max(0, visibleCount - WINDOW) * ROW;
  const asleepMin = Math.floor(interpolate(frame, [PROOF0, 413], [14, 52], clamp));
  const cursorOn = Math.floor(frame / 8) % 2 === 0;
  const brkPulse = 0.5 + 0.5 * Math.abs(Math.sin(frame / 16));

  // ── CTA ──
  const ctaScale = interpolate(spring({ frame: frame - 428, fps, config: { damping: 13, stiffness: 130 } }), [0, 1], [0.9, 1]);
  const arrow = Math.sin(frame / 7) * 6;
  const progress = interpolate(frame, [4, durationInFrames - 2], [0, 1], clamp);

  // film-grain dust (static drift)
  const dust = Array.from({ length: 10 }, (_, i) => ({
    x: ((i * 137) % width) + Math.cos(frame / 50 + i) * 10,
    y: ((i * 311) % height) + Math.sin(frame / 44 + i) * 12,
    s: 2 + (i % 3), o: 0.05 + (i % 4) * 0.015,
  }));

  return (
    <AbsoluteFill style={{ backgroundColor: INK, fontFamily: FONT }}>
      {/* depth stage */}
      <AbsoluteFill style={{ perspective: dollyPersp, perspectiveOrigin: '34% 28%', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, transformStyle: 'preserve-3d', transform: `rotateX(${pitch}deg) rotateY(${yaw}deg)` }}>
          {/* BG + single amber key light (top-left), parallax-back */}
          <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden', transform: 'translateZ(-360px) scale(1.3)' }}>
            <AbsoluteFill style={{ background: `linear-gradient(160deg, #070605 0%, ${INK} 60%)` }} />
            <div style={{ position: 'absolute', top: -260, left: -160, width: 1180, height: 1180, borderRadius: '50%', background: `radial-gradient(circle, ${AMBER}3a 0%, ${AMBER}00 62%)`, filter: 'blur(96px)', transform: `translate(${keyDx}px, ${keyDy}px)` }} />
            {dust.map((d, i) => <div key={i} style={{ position: 'absolute', left: d.x, top: d.y, width: d.s, height: d.s, borderRadius: '50%', background: PAPER, opacity: d.o }} />)}
          </div>

          {/* FG content plane */}
          <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden', transform: 'translateZ(40px)' }}>

            {/* ── CLOCK (open) ── */}
            <div style={{ position: 'absolute', top: 360, left: 0, right: 0, textAlign: 'center', opacity: oClock, transform: `translateY(${clockY}px)` }}>
              <div style={{ fontFamily: MONO, fontSize: 72, fontWeight: 700, color: AMBER, letterSpacing: 4, fontVariantNumeric: 'tabular-nums', textShadow: `0 0 40px ${AMBER}55` }}>
                {`03:${String(mins).padStart(2, '0')} AM`}
              </div>
              <div style={{ width: 520, height: 2, margin: '26px auto 0', background: AMBER, transform: `scaleX(${ruleW})`, transformOrigin: 'center', boxShadow: `0 0 12px ${AMBER}` }} />
              <div style={{ marginTop: 30, fontSize: 30, fontWeight: 700, letterSpacing: 10, color: DIM, fontFamily: BODY }}>MEANWHILE…</div>
            </div>

            {/* ── HOOK + STAKES ── */}
            <div style={{ position: 'absolute', top: 360, left: X, right: 72, opacity: oHook }}>
              <div style={{ fontSize: 30, fontWeight: 800, letterSpacing: 8, color: AMBER, fontFamily: BODY, marginBottom: 26 }}>{stat}</div>
              <h1 style={{ margin: 0, fontSize: fitFontSize({ text: hook, width: 916, maxFontSize: 116, minFontSize: 56, maxLines: 3, fontFamily: FONT, fontWeight: 900, letterSpacing: '-5px' }), fontWeight: 900, lineHeight: 0.96, letterSpacing: -5, color: PAPER, clipPath: `inset(${heroClip}% 0 0 0)`, textShadow: `0 ${heroShadow}px 60px rgba(0,0,0,0.7)` }}>
                {hook}
              </h1>
              <div style={{ marginTop: 40, fontSize: 44, fontWeight: 600, lineHeight: 1.25, color: DIM, fontFamily: BODY, letterSpacing: -0.5, maxWidth: 880, opacity: ramp(frame, 104, 124) }}>
                {problem}
              </div>
            </div>

            {/* ── FIX (editorial numbered list) ── */}
            <div style={{ position: 'absolute', top: 470, left: X, right: 72, opacity: oFix }}>
              <div style={{ fontSize: 30, fontWeight: 800, letterSpacing: 8, color: AMBER, fontFamily: BODY, marginBottom: 40 }}>THE PLAYBOOK</div>
              {steps.map((s, i) => {
                const st = 175 + i * 30;
                const rv = ramp(frame, st, st + 16);
                const sup = i < steps.length - 1 ? ramp(frame, 175 + (i + 1) * 30, 175 + (i + 1) * 30 + 16) : 0;
                return (
                  <div key={i} style={{ borderTop: `1px solid ${PAPER}22`, padding: '30px 0', display: 'flex', alignItems: 'baseline', gap: 30, transform: `translateY(${interpolate(rv, [0, 1], [26, 0])}px)`, opacity: rv * (1 - sup * 0.72) }}>
                    <div style={{ fontFamily: MONO, fontSize: 40, fontWeight: 700, color: AMBER, minWidth: 84 }}>{String(i + 1).padStart(2, '0')}</div>
                    <div style={{ fontSize: 54, fontWeight: 800, color: sup > 0.4 ? DIM : PAPER, lineHeight: 1.08, letterSpacing: -1 }}>{s}</div>
                  </div>
                );
              })}
            </div>

            {/* ── PROOF: live overnight task feed ── */}
            <div style={{ position: 'absolute', top: 300, left: X, right: 72, opacity: oProof }}>
              <div style={{ fontSize: 30, fontWeight: 800, letterSpacing: 5, color: AMBER, fontFamily: BODY, marginBottom: 4 }}>WHILE YOU SLEPT, IT SHIPPED:</div>
              <div style={{ fontFamily: MONO, fontSize: 24, color: DIM, letterSpacing: 1, marginBottom: 22 }}>one agent. one night. zero code.</div>
              <div style={{ position: 'relative', height: WINDOW * ROW, overflow: 'hidden' }}>
                <div style={{ transform: `translateY(${conveyorY}px)` }}>
                  {LINES.map((t, i) => {
                    if (frame < lineStart(i)) return null;
                    const rv = ramp(frame, lineStart(i), lineStart(i) + 6);
                    const flipped = frame >= flipAt(i);
                    const flipP = ramp(frame, flipAt(i), flipAt(i) + 5);
                    const markPop = flipped ? interpolate(spring({ frame: frame - flipAt(i), fps, config: { damping: 12, stiffness: 200 } }), [0, 1], [0.4, 1]) : 1;
                    const ghostO = beat(frame, flipAt(i), flipAt(i) + 4, flipAt(i) + 14, flipAt(i) + 22);
                    const ghostY = interpolate(ramp(frame, flipAt(i), flipAt(i) + 22), [0, 1], [0, -22]);
                    const flash = beat(frame, flipAt(i), flipAt(i) + 1, flipAt(i) + 3, flipAt(i) + 8) * 0.1;
                    return (
                      <div key={i} style={{ height: ROW, display: 'flex', alignItems: 'center', gap: 18, opacity: rv, transform: `translateY(${interpolate(rv, [0, 1], [18, 0])}px)`, fontFamily: MONO, fontSize: 37, position: 'relative', background: `rgba(63,185,80,${flash})`, borderRadius: 6 }}>
                        <div style={{ width: 38, display: 'flex', justifyContent: 'center', transform: `scale(${markPop})` }}>
                          {flipped
                            ? <span style={{ color: DONE, fontWeight: 700 }}>✓</span>
                            : <span style={{ width: 15, height: 15, border: `2px solid ${AMBER}`, transform: 'rotate(45deg)', display: 'inline-block' }} />}
                        </div>
                        <span style={{ color: DIM, fontSize: 27, minWidth: 158, fontVariantNumeric: 'tabular-nums' }}>{ts(i)}</span>
                        <span style={{ color: flipped ? lerpColor(DIM, PAPER, flipP) : DIM, fontWeight: 600, letterSpacing: -0.5 }}>
                          {t}{!flipped && cursorOn ? <span style={{ color: AMBER }}>_</span> : null}
                        </span>
                        {ghostO > 0.01 ? <span style={{ position: 'absolute', right: 4, color: DONE, fontSize: 30, fontWeight: 700, opacity: ghostO, transform: `translateY(${ghostY}px)` }}>+1</span> : null}
                      </div>
                    );
                  })}
                </div>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 64, background: `linear-gradient(180deg, ${INK}, transparent)`, pointerEvents: 'none' }} />
                <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 64, background: `linear-gradient(0deg, ${INK}, transparent)`, pointerEvents: 'none' }} />
              </div>
            </div>
            {/* ── COUNT + ASLEEP-CLOCK BAR ── */}
            <div style={{ position: 'absolute', bottom: 250, left: X, right: 72, display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', opacity: oProof }}>
              <div style={{ transform: `scale(${countPop})`, transformOrigin: 'left bottom' }}>
                <div style={{ fontSize: 196, fontWeight: 900, color: HOT, letterSpacing: -8, lineHeight: 0.82, fontVariantNumeric: 'tabular-nums', textShadow: `0 0 ${ramp(frame, 304, 360) * 60}px ${AMBER}55` }}>{shippedCount}</div>
                <div style={{ fontSize: 26, fontWeight: 800, letterSpacing: 8, color: DIM, fontFamily: BODY, marginTop: 6 }}>SHIPPED</div>
              </div>
              <div style={{ fontFamily: MONO, fontSize: 33, color: DIM, letterSpacing: 1, marginBottom: 16, fontVariantNumeric: 'tabular-nums' }}>
                <span style={{ opacity: brkPulse }}>[ </span>ASLEEP · <span style={{ color: AMBER }}>{`03:${String(asleepMin).padStart(2, '0')} AM`}</span><span style={{ opacity: brkPulse }}> ]</span>
              </div>
            </div>

            {/* ── CTA ── */}
            <div style={{ position: 'absolute', bottom: 240, left: X, right: 72, opacity: oCta }}>
              <div style={{ fontSize: 44, fontWeight: 800, color: PAPER, lineHeight: 1.15, letterSpacing: -1, marginBottom: 40, maxWidth: 860 }}>{result}</div>
              <div style={{ transform: `scale(${ctaScale})`, transformOrigin: 'left center' }}>
                <div style={{ display: 'inline-flex', flexDirection: 'column', gap: 10, border: `2px solid ${AMBER}`, borderRadius: 4, padding: '30px 40px', background: 'transparent', boxShadow: `0 0 40px ${AMBER}22` }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 16, color: PAPER, fontSize: 44, fontWeight: 800 }}>
                    {ctaVerb} <span style={{ color: AMBER, fontFamily: MONO, fontWeight: 700 }}>{cta}</span>
                  </div>
                  <div style={{ color: DIM, fontSize: 28, fontFamily: BODY, fontWeight: 600 }}>and I’ll send the build <span style={{ display: 'inline-block', transform: `translateX(${arrow}px)`, color: AMBER }}>→</span></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </AbsoluteFill>

      {/* ── FLAT OVERLAYS (film grade) ── */}
      <AbsoluteFill style={{ background: 'radial-gradient(100% 80% at 30% 24%, transparent 34%, rgba(0,0,0,0.80) 100%)', pointerEvents: 'none' }} />
      <AbsoluteFill style={{ backgroundImage: GRAIN, backgroundSize: '200px 200px', mixBlendMode: 'overlay', opacity: 0.05, pointerEvents: 'none' }} />

      {/* top progress (flat amber) */}
      <div style={{ position: 'absolute', top: 40, left: 56, right: 56, height: 4, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
        <div style={{ width: `${progress * 100}%`, height: '100%', background: AMBER }} />
      </div>
      {/* corner brand + the returning clock (07:00 AM) */}
      <div style={{ position: 'absolute', top: 78, left: 60, fontSize: 26, letterSpacing: 7, fontWeight: 700, color: DIM, fontFamily: BODY, opacity: interpolate(frame, [6, 20], [0, 1], clamp) }}>PULSE · DAILY</div>
      <div style={{ position: 'absolute', bottom: 60, right: 60, fontFamily: MONO, fontSize: 30, fontWeight: 700, color: AMBER, letterSpacing: 2, fontVariantNumeric: 'tabular-nums', opacity: ramp(frame, 440, 460) }}>07:00 AM</div>
      <div style={{ position: 'absolute', bottom: 60, left: 60, fontFamily: MONO, fontSize: 22, color: DIM, letterSpacing: 2, opacity: 0.6 }}>{tipId} · @yourhandle</div>
    </AbsoluteFill>
  );
};

export const StoryOvernight: React.FC<StoryOvernightProps> = (props) => {
  const samples = props.mbSamples ?? 8;
  return (
    <AbsoluteFill style={{ backgroundColor: INK }}>
      {props.voSrc ? <Audio src={staticFile(props.voSrc)} /> : null}
      <CameraMotionBlur samples={samples} shutterAngle={180}>
        <Scene {...props} />
      </CameraMotionBlur>
    </AbsoluteFill>
  );
};
