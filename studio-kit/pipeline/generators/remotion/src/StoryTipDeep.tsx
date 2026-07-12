// /2699 (2026-06-02): StoryTipDeep — 15-second, 3D, dynamic-opacity, high-retention
// IG Story video engine. Built from an internal spec +
// the story-3d-and-tips design workflow (DepthDiorama 3D stage + 5 hero components).
// the creator asks (stacked): dynamic opacity, high retention, "15 seconds", "more 2d-3d component
// animations", "better tips", and an ElevenLabs voiceover baked in.
//
// 450 frames @ 30fps, 1080x1920. Beats: HOOK 0-60 / STAKES 60-120 / FIX 120-270 /
// PROOF 270-360 / CTA 360-450. Rotates across all 7 AI types (accent per type).
//
// 3D system (CSS transforms only — Chromium, no three.js/WebGL):
//   DepthDiorama  — global perspective stage, 3 parallax planes, slow camera orbit (motion every frame)
//   HingeFlipHeadline — hook/result words pivot in on a top hinge (rotateX) with extruded text-shadow
//   AICoreCube    — 6-face brand cube: HOOK hero -> docked spinning chip -> CTA
//   DeckFlip      — FIX steps as a 3D flip-card deck, active card lifts toward lens
//   ProofRig      — one 3D payoff per proof.kind (swatch stack / extruded counter / IDE window-stack)
//   PanelSwap     — 90deg 3D turn between beats
// Chromium traps respected: no blur on any 3D-transformed node; backface-hidden + opacity-gate
// past the half-turn on every flipping node; translateZ == half the rotation-axis dimension;
// grain/vignette are flat overlays OUTSIDE the 3D stage; deterministic random() only; shade() not color-mix.
import React from 'react';
import {
  AbsoluteFill, Audio, Sequence, staticFile,
  useCurrentFrame, useVideoConfig, interpolate, spring, Easing, random,
} from 'remotion';
import { CameraMotionBlur } from '@remotion/motion-blur';
import { fitFontSize } from './components/fitFontSize';
import { KineticCaptions } from './components/KineticCaptions';

export type AiType = 'llm' | 'image' | 'video' | 'voice' | 'code' | 'auto' | 'rag';

export interface StoryTipDeepProps {
  tipId?: string;
  aiType?: AiType;
  hook?: string;
  stat?: string;
  problem?: string;
  steps?: string[];
  proof?: { kind: 'demo' | 'counter' | 'swatches'; lines?: string[]; from?: number; to?: number; unit?: string; prefix?: string; note?: string };
  result?: string;
  cta?: string;
  ctaVerb?: string; //  : on-screen CTA verb. Defaults to 'Comment' = the PROVEN breakout format ("Comment '<KEYWORD>'", 5/5 of our top reels) — was hardcoded 'Reply'.
  voSrc?: string; // e.g. "vo/AI-IMG-001.mp3" — staticFile() under remotion-reel/public/
  voText?: string; // : the VO script — drives the word-level kinetic captions (the retention lever)
  voDurS?: number; // : measured VO duration (s) so captions track the real narration pace, not a guess
  mbSamples?: number; // CameraMotionBlur sub-frame samples (default 6); higher = smoother blur, slower render
}

const AI: Record<AiType, { a: string; b: string; label: string; glyph: string }> = {
  llm: { a: '#A855F7', b: '#6366F1', label: 'LLM · CHAT', glyph: '❝❞' },
  image: { a: '#06B6D4', b: '#3B82F6', label: 'IMAGE AI', glyph: '◫' },
  video: { a: '#F59E0B', b: '#F97316', label: 'VIDEO AI', glyph: '▶' },
  voice: { a: '#10B981', b: '#14B8A6', label: 'VOICE AI', glyph: ')))' },
  code: { a: '#F43F5E', b: '#FB7185', label: 'CODE AGENT', glyph: '{ }' },
  auto: { a: '#EC4899', b: '#A855F7', label: 'AUTOMATION', glyph: '⟳' },
  rag: { a: '#6366F1', b: '#818CF8', label: 'RESEARCH · RAG', glyph: '⌕' },
  news: { a: '#3B82F6', b: '#22D3EE', label: 'AI NEWS', glyph: '✦' },
};
const TYPE_ORDER: AiType[] = ['llm', 'image', 'video', 'voice', 'code', 'auto', 'rag'];

const FONT = '"Segoe UI", "Helvetica Neue", "Arial Black", system-ui, sans-serif';
const MONO = '"Consolas", "SF Mono", monospace';
const GRAIN =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")";

const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
// ease-in/ease-out reveal ramp (the creator: "ease in and ease out for all motion")
const ramp = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.inOut(Easing.cubic) });
// darken/lighten a #hex deterministically (avoids color-mix() Chromium-version drift)
const shade = (hex: string, pct: number) => {
  const n = parseInt(hex.slice(1), 16);
  const c = (v: number) => Math.max(0, Math.min(255, Math.round(v)));
  const r = c(((n >> 16) & 255) * (1 + pct)), g = c(((n >> 8) & 255) * (1 + pct)), b = c((n & 255) * (1 + pct));
  return `rgb(${r},${g},${b})`;
};

const StoryScene: React.FC<StoryTipDeepProps> = ({
  tipId = 'AI-IMAGE-001',
  aiType = 'image',
  hook = 'YOUR STYLE ISN’T RANDOM',
  stat = '1 SREF = 1 BRAND',
  problem = 'Every render looks like a different brand.',
  steps = ['Mint one --sref random', 'Lock that seed everywhere', 'Only change the subject'],
  proof = { kind: 'swatches' },
  result = 'One consistent style — every time.',
  cta = 'START',
  ctaVerb = 'Comment',
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();
  const T = AI[aiType] || AI.llm;
  const accent = T.a, accent2 = T.b;

  const breathe = Math.sin(frame / 26) * 0.5 + 0.5;
  const progress = interpolate(frame, [3, durationInFrames - 2], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  // ── Camera orbit (DepthDiorama). sin/cos return ~0 at f=0 & f=450 → loop-seamless. ──
  const leanAt = (b: number) => spring({ frame: frame - b, fps, config: { damping: 14, stiffness: 90, mass: 1.1 } }) * interpolate(frame - b, [0, 40], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) * 2.2;
  const yaw = Math.sin(frame / 150) * 5 + (frame >= 120 ? leanAt(120) : 0) + (frame >= 270 ? leanAt(270) : 0) + (frame >= 360 ? leanAt(360) : 0);
  const pitch = Math.cos(frame / 190) * 3;
  const counterRot = -yaw * 0.45; // text counter-rotate so type never shears

  // ──  cinematic upgrades: dolly push-in + hook light-bloom + beat-swap light sweep ──
  // Slow perspective pull (1520→1230) reads as a cinematic dolly toward the diorama (respects preserve-3d, no scale-flatten).
  const dollyPersp = interpolate(frame, [0, durationInFrames], [1520, 1230], { extrapolateRight: 'clamp' });
  // Accent bloom that blooms behind the hook as the words hinge in, then settles to a soft glow.
  const hookBloom = interpolate(frame, [6, 38, 84], [0, 0.95, 0.28], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  // Brief screen-blend light sweep at each beat boundary (HOOK→FIX 120, FIX→PROOF 270, PROOF→CTA 360).
  const beatFlash = Math.max(
    interpolate(frame, [118, 123, 142], [0, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
    interpolate(frame, [268, 273, 292], [0, 0.9, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
    interpolate(frame, [358, 363, 382], [0, 1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
  );

  // ── Aurora orbs (blur stays on the orb CHILD, never on a translateZ'd plane) ──
  const o1x = Math.sin(frame / 58) * 90, o1y = Math.cos(frame / 72) * 70;
  const o2x = Math.cos(frame / 50) * 110, o2y = Math.sin(frame / 66) * 90;
  const orbScale = 1 + breathe * 0.08;

  // ── PanelSwap: each beat-panel is a layer that turns in/out on rotateY (3D beat transition) ──
  const panel = (start: number, end: number | null) => {
    const inP = start === 0 ? 1 : clamp01(spring({ frame: frame - start, fps, config: { damping: 18, stiffness: 120, mass: 1 } }));
    const outP = end === null ? 0 : clamp01(spring({ frame: frame - end, fps, config: { damping: 18, stiffness: 120, mass: 1 } }));
    const rotY = (1 - inP) * 90 - outP * 90;
    const opacity = clamp01(interpolate(Math.abs(rotY), [0, 50, 70], [1, 1, 0])) * inP * (1 - outP);
    const bright = interpolate(Math.abs(rotY), [0, 90], [1, 0.4]);
    return { rotY, opacity, bright };
  };
  const pHook = panel(0, 120);
  const pFix = panel(120, 270);
  const pProof = panel(270, 360);
  const pCta = panel(360, null);

  // ── HingeFlipHeadline word renderer ──
  const depthShadow = Array.from({ length: 12 }, (_, d) => `0 ${d}px 0 rgba(8,4,18,${(0.9 - d * 0.05).toFixed(2)})`).join(',') + `, 0 22px 34px ${accent}55`;
  const HingeWords = ({ text, baseStart, stagger, stiffness, size }: { text: string; baseStart: number; stagger: number; stiffness: number; size: number }) => {
    const ws = String(text).toUpperCase().split(/\s+/).filter(Boolean);
    // : shrink-to-fit so a long live hook wraps to ≤3 lines instead of clipping mid-word —
    // size is the MAX; fitFontSize returns the largest that fits the real text within the panel width.
    const fontSize = fitFontSize({ text, width: 916, maxFontSize: size, minFontSize: 56, maxLines: 3, fontFamily: FONT, fontWeight: 900, letterSpacing: '-3px', textTransform: 'uppercase' });
    return (
      <h1 style={{ margin: 0, display: 'flex', flexWrap: 'wrap', gap: `0 22px`, perspective: 1400, perspectiveOrigin: '50% 0%', color: '#fff', fontSize, fontWeight: 900, lineHeight: 1.0, letterSpacing: -3 }}>
        {ws.map((w, i) => {
          const local = frame - (baseStart + i * stagger);
          const s = spring({ frame: local, fps, config: { damping: 13, stiffness, mass: 0.7 } });
          const rotX = interpolate(s, [0, 1], [-92, 0]);
          const o = interpolate(local, [0, 2], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          return (
            <span key={i} style={{ display: 'inline-block', transformStyle: 'preserve-3d', transformOrigin: '50% 0%', backfaceVisibility: 'hidden', transform: `rotateX(${rotX}deg)`, opacity: o, textShadow: depthShadow }}>{w}</span>
          );
        })}
      </h1>
    );
  };

  // ── AICoreCube (persistent brand mascot) ──
  const cubeRy = interpolate(frame, [0, 45], [-220, -8], { easing: Easing.out(Easing.cubic), extrapolateRight: 'clamp', extrapolateLeft: 'clamp' }) + (frame > 45 ? (frame - 45) * 0.32 : 0);
  const cubeRx = Math.sin(frame / 38) * 8 - 6;
  const popScale = spring({ frame, fps, config: { damping: 12, stiffness: 150 } });
  const dock = ramp(frame, 45, 62); // 0 hero -> 1 docked chip
  const EDGE = 300, HALF = EDGE / 2;
  const heroSize = interpolate(dock, [0, 1], [1, 0.34]);
  const cubeScale = interpolate(popScale, [0, 1], [0.2, 1]) * heroSize;
  // hero center sits in the empty mid-band UNDER the headline (~760), then docks to the top-right chip (~895,150)
  const cubeX = interpolate(dock, [0, 1], [540, 892]);
  const cubeY = interpolate(dock, [0, 1], [770, 150]);
  const faceTransforms = [
    `rotateY(0deg) translateZ(${HALF}px)`, `rotateY(90deg) translateZ(${HALF}px)`,
    `rotateY(180deg) translateZ(${HALF}px)`, `rotateY(-90deg) translateZ(${HALF}px)`,
    `rotateX(90deg) translateZ(${HALF}px)`, `rotateX(-90deg) translateZ(${HALF}px)`,
  ];
  const faceAngles = [0, 90, 180, 270, 0, 0];
  // faces carry AI types, active type on the front face
  const others = TYPE_ORDER.filter((t) => t !== aiType);
  const faceTypes: AiType[] = [aiType, others[0], others[1], others[2], others[3], others[4]];

  // ── DeckFlip card state ──
  const FIX_BASE = 140, STG = 26;
  const cardState = (i: number) => {
    const start = FIX_BASE + i * STG;
    const reveal = clamp01(spring({ frame: frame - start, fps, config: { damping: 14, stiffness: 140, mass: 0.7 } }));
    const supersede = i < steps.length - 1 ? clamp01(spring({ frame: frame - (FIX_BASE + (i + 1) * STG), fps, config: { damping: 14, stiffness: 140, mass: 0.7 } })) : 0;
    const activeAmt = reveal * (1 - supersede);
    const z = activeAmt * 90 - supersede * 46;
    const y = supersede * 18;
    const rotY = interpolate(reveal, [0, 1], [-92, 0]);
    const rotZ = (random('yaw' + i) * 2 - 1) * 1.5 * supersede;
    const opacity = interpolate(reveal, [0.5, 0.62], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    return { z, y, rotY, rotZ, opacity, activeAmt };
  };

  // ── ProofRig ──
  const proofLocal = frame - 280;
  const renderProof = () => {
    if (proof.kind === 'counter') {
      const v = interpolate(proofLocal, [4, 40], [proof.from ?? 0, proof.to ?? 100], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic) });
      const rise = clamp01(spring({ frame: proofLocal, fps, config: { damping: 16, stiffness: 90 } }));
      const ty = interpolate(rise, [0, 1], [150, 0]);
      const decimals = (proof.to ?? 0) % 1 !== 0 || (proof.from ?? 0) % 1 !== 0 ? 2 : 0;
      const numShadow = Array.from({ length: 9 }, (_, d) => `${d}px ${d}px 0 ${shade(accent, -0.5)}`).join(',');
      const bigNum = `${proof.prefix ?? ''}${v.toFixed(decimals)}${proof.unit ?? ''}`;
      // scale the slab font down for longer strings so it never kisses the safe edges
      const numFont = bigNum.length > 9 ? 124 : bigNum.length > 6 ? 150 : 184;
      return (
        <div style={{ textAlign: 'center', transform: `translateY(${ty}px)`, maxWidth: 940 }}>
          <div style={{ display: 'inline-block', maxWidth: 940, padding: '26px 40px', borderRadius: 26, background: `linear-gradient(150deg, ${shade(accent, -0.55)}, ${shade(accent2, -0.6)})`, border: `1px solid ${accent}66`, boxShadow: `0 30px 70px rgba(0,0,0,0.5), 0 0 ${rise * 40}px ${accent}66` }}>
            <div style={{ fontSize: numFont, fontWeight: 900, color: '#fff', letterSpacing: -4, lineHeight: 1.0, whiteSpace: 'nowrap', fontVariantNumeric: 'tabular-nums', textShadow: numShadow }}>
              {bigNum}
            </div>
          </div>
          {proof.note ? <div style={{ fontSize: 27, color: '#B9B6D6', opacity: ramp(frame, 320, 340), maxWidth: 720, margin: '24px auto 0', lineHeight: 1.3 }}>{proof.note}</div> : null}
        </div>
      );
    }
    if (proof.kind === 'demo') {
      const lines = proof.lines ?? ['$ run', '> working...', 'ok done'];
      return (
        <div style={{ position: 'relative', perspective: 1400 }}>
          {/* two stacked dim windows behind (IDE stack) */}
          {[140, 70].map((zb, k) => (
            <div key={k} style={{ position: 'absolute', inset: 0, transform: `translateZ(-${zb}px) translateY(${-18 - k * 8}px) scale(${1 - (k + 1) * 0.05})`, background: 'rgba(10,8,22,0.6)', border: `1px solid ${accent}33`, borderRadius: 22, opacity: ramp(frame, 280, 300) }} />
          ))}
          <div style={{ position: 'relative', background: 'rgba(8,6,18,0.94)', border: `1px solid ${accent}66`, borderRadius: 22, padding: '30px 32px', fontFamily: MONO, fontSize: 33, boxShadow: `0 26px 64px ${accent}33`, transform: 'translateZ(40px)' }}>
            <div style={{ display: 'flex', gap: 11, marginBottom: 22 }}>
              {['#FF5F56', '#FFBD2E', '#27C93F'].map((c) => <div key={c} style={{ width: 16, height: 16, borderRadius: '50%', background: c }} />)}
            </div>
            {lines.map((ln, i) => {
              const start = 14 + i * 16;
              const chars = Math.max(0, Math.floor((proofLocal - start) * 2.0));
              const shown = ln.slice(0, chars);
              const ok = /^\s*(\+|ok|✓)/.test(ln) || /passing/.test(ln);
              const bad = /^\s*(x|✗|×)/.test(ln) || /does not exist/.test(ln);
              const arrow = /->|=>|^\s*>/.test(ln);
              const col = ok ? '#27C93F' : bad ? '#FF6B6B' : arrow ? '#9CC3FF' : '#D8D5F0';
              return (
                <div key={i} style={{ color: col, lineHeight: 1.5, whiteSpace: 'pre', opacity: ramp(frame, 280 + start - 2, 280 + start + 5) }}>
                  {shown}{chars < ln.length && proofLocal - start > 0 ? <span style={{ opacity: breathe > 0.5 ? 1 : 0.1 }}>▋</span> : null}
                </div>
              );
            })}
          </div>
        </div>
      );
    }
    // swatches — 3 tiles fan out into depth + lock to the accent house style
    const lock = ramp(frame, 290, 332);
    const mismatched = ['#7c8a99', '#b06a4a', '#4a7c5a'];
    return (
      <div style={{ display: 'flex', gap: 0, justifyContent: 'center', alignItems: 'center', perspective: 1400 }}>
        {[0, 1, 2].map((i) => {
          const tx = (i - 1) * interpolate(lock, [0, 1], [4, 150]);
          const z = (1 - i) * 100 * lock;
          const ry = (i - 1) * -6 * lock;
          const dim = interpolate(z, [-100, 0, 100], [0.6, 1, 1]);
          return (
            <div key={i} style={{ position: 'relative', width: 200, height: 256, borderRadius: 22, overflow: 'hidden', transform: `translateX(${tx}px) translateZ(${z}px) rotateY(${ry}deg)`, opacity: ramp(frame, 274 + i * 5, 288 + i * 5) * dim, filter: i === 2 && lock > 0 ? `blur(${(2.2 * lock).toFixed(2)}px)` : 'none', boxShadow: `0 18px 44px rgba(0,0,0,0.55), 0 0 ${lock * 26}px ${accent}${lock > 0.5 ? '88' : '00'}`, backfaceVisibility: 'hidden' }}>
              <div style={{ position: 'absolute', inset: 0, background: mismatched[i], opacity: 1 - lock }} />
              <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(150deg, ${accent}, ${accent2})`, opacity: lock }} />
            </div>
          );
        })}
      </div>
    );
  };

  // ── CTA pill state ──
  const ctaSpring = clamp01(spring({ frame: frame - 372, fps, config: { damping: 12, stiffness: 140, mass: 0.8 } }));
  const ctaScale = interpolate(ctaSpring, [0, 1], [0.84, 1]);
  const shimmerX = interpolate(((frame - 372) % 36) / 36, [0, 1], [-60, 160]);
  const arrowNudge = Math.sin(frame / 6) * 6;

  // dust (deterministic)
  const dust = Array.from({ length: 16 }, (_, i) => {
    const bx = random('x' + i) * width, by = random('y' + i) * height;
    const dy = Math.sin(frame / (24 + random('s' + i) * 30) + i) * 22;
    const dx = Math.cos(frame / (30 + random('t' + i) * 26) + i) * 14;
    return { x: bx + dx, y: by + dy, size: 2 + random('r' + i) * 4, op: (0.1 + random('o' + i) * 0.2) * (0.5 + breathe * 0.5), key: i };
  });

  const planeBase: React.CSSProperties = { position: 'absolute', inset: 0, backfaceVisibility: 'hidden' };

  return (
    <AbsoluteFill style={{ backgroundColor: '#04020A', fontFamily: FONT }}>
      {/* ════ 3D STAGE (DepthDiorama) ════ */}
      <AbsoluteFill style={{ perspective: dollyPersp, perspectiveOrigin: '50% 42%', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, transformStyle: 'preserve-3d', transform: `rotateX(${pitch}deg) rotateY(${yaw}deg)` }}>

          {/* BG plane */}
          <div style={{ ...planeBase, transform: 'translateZ(-520px) scale(1.42)' }}>
            <AbsoluteFill style={{ background: 'linear-gradient(165deg, #07030F 0%, #0C0518 55%, #05030D 100%)' }} />
            <div style={{ position: 'absolute', top: 100, left: '50%', width: 1000, height: 1000, marginLeft: -500, borderRadius: '50%', background: `radial-gradient(circle, ${accent}55 0%, ${accent}00 62%)`, filter: 'blur(70px)', transform: `translate(${o1x}px, ${o1y}px) scale(${orbScale})` }} />
            <div style={{ position: 'absolute', bottom: 60, left: -120, width: 900, height: 900, borderRadius: '50%', background: `radial-gradient(circle, ${accent2}4d 0%, ${accent2}00 60%)`, filter: 'blur(80px)', transform: `translate(${o2x}px, ${o2y}px) scale(${orbScale})` }} />
            {dust.map((d) => <div key={d.key} style={{ position: 'absolute', left: d.x, top: d.y, width: d.size, height: d.size, borderRadius: '50%', background: '#fff', opacity: d.op }} />)}
          </div>

          {/* MID plane — FIX + PROOF */}
          <div style={{ ...planeBase, transform: 'translateZ(-120px) scale(1.09)' }}>
            {/* FIX panel */}
            <div style={{ position: 'absolute', top: 540, left: 64, right: 64, transformStyle: 'preserve-3d', transform: `rotateY(${pFix.rotY}deg)`, opacity: pFix.opacity, filter: `brightness(${pFix.bright})` }}>
              <div style={{ fontSize: 34, fontWeight: 800, letterSpacing: 4, color: accent, marginBottom: 30, transform: `rotateY(${counterRot}deg)` }}>THE FIX</div>
              <div style={{ position: 'relative', perspective: 1400 }}>
                <div style={{ transformStyle: 'preserve-3d', transform: 'rotateX(6deg)' }}>
                  {steps.map((s, i) => {
                    const c = cardState(i);
                    return (
                      <div key={i} style={{ position: 'relative', marginBottom: 22, transformStyle: 'preserve-3d', transform: `translateY(${c.y}px) translateZ(${c.z + i * -0.5}px) rotateX(${-2 * (1 - c.activeAmt)}deg) rotateY(${c.rotY}deg) rotateZ(${c.rotZ}deg)`, opacity: c.opacity, backfaceVisibility: 'hidden' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 24, maxWidth: 560, padding: '22px 26px', borderRadius: 20, background: 'rgba(8,6,18,0.9)', border: `1px solid ${accent}55`, boxShadow: `0 ${10 + c.activeAmt * 20}px ${30 + c.activeAmt * 30}px rgba(0,0,0,0.5), 0 0 ${c.activeAmt * 26}px ${accent}66`, transform: 'rotateX(-6deg)' }}>
                          <div style={{ flexShrink: 0, width: 60, height: 60, borderRadius: 15, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 34, fontWeight: 900, color: '#fff', background: `linear-gradient(135deg, ${accent}, ${accent2})`, boxShadow: `0 0 ${c.activeAmt * 20}px ${accent}88` }}>{i + 1}</div>
                          <div style={{ fontSize: fitFontSize({ text: s, width: 424, maxFontSize: 46, minFontSize: 28, maxLines: 2, fontFamily: FONT, fontWeight: 700 }), fontWeight: 700, color: '#F2F0FF', lineHeight: 1.12 }}>{s}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
            {/* PROOF panel */}
            <div style={{ position: 'absolute', top: 0, left: 64, right: 64, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', transformStyle: 'preserve-3d', transform: `rotateY(${pProof.rotY}deg)`, opacity: pProof.opacity, filter: `brightness(${pProof.bright})` }}>
              {renderProof()}
            </div>
          </div>

          {/* FG plane — HOOK/STAKES + CTA + cube */}
          <div style={{ ...planeBase, transform: 'translateZ(90px) scale(0.94)' }}>
            {/* HOOK + STAKES panel */}
            <div style={{ position: 'absolute', top: 300, left: 64, right: 64, transformStyle: 'preserve-3d', transform: `rotateY(${pHook.rotY}deg)`, opacity: pHook.opacity, filter: `brightness(${pHook.bright})` }}>
              <div style={{ position: 'absolute', left: 0, top: -40, width: 760, height: 360, borderRadius: '50%', background: `radial-gradient(circle, ${accent}77 0%, ${accent}00 66%)`, filter: 'blur(55px)', opacity: hookBloom, pointerEvents: 'none' }} />
              <div style={{ transform: `rotateY(${counterRot}deg)`, position: 'relative' }}>
                <HingeWords text={hook} baseStart={6} stagger={5} stiffness={170} size={112} />
              </div>
              <div style={{ marginTop: 36, display: 'flex', alignItems: 'center', gap: 22, flexWrap: 'wrap', transform: `rotateY(${counterRot}deg)` }}>
                <span style={{ opacity: clamp01(ramp(frame, 62, 80)), transform: `scale(${interpolate(clamp01(spring({ frame: frame - 64, fps, config: { damping: 11, stiffness: 150 } })), [0, 1], [0.7, 1])})`, transformOrigin: 'left center', fontSize: fitFontSize({ text: stat, width: 540, maxFontSize: 40, minFontSize: 24, maxLines: 1, fontFamily: FONT, fontWeight: 900 }), fontWeight: 900, color: '#fff', background: `linear-gradient(135deg, ${accent}, ${accent2})`, padding: '10px 24px', borderRadius: 14, letterSpacing: 1, boxShadow: `0 0 28px ${accent}88`, whiteSpace: 'nowrap' }}>{stat}</span>
                <span style={{ opacity: clamp01(ramp(frame, 70, 88)), fontSize: 38, fontWeight: 600, color: '#CFCDE8', lineHeight: 1.25 }}>{problem}</span>
              </div>
            </div>

            {/* CTA panel */}
            <div style={{ position: 'absolute', bottom: 200, left: 64, right: 64, transformStyle: 'preserve-3d', transform: `rotateY(${pCta.rotY}deg)`, opacity: pCta.opacity }}>
              <div style={{ transform: `rotateY(${counterRot}deg)`, textAlign: 'center', marginBottom: 36 }}>
                <div style={{ fontSize: fitFontSize({ text: result, width: 920, maxFontSize: 50, minFontSize: 32, maxLines: 2, fontFamily: FONT, fontWeight: 800 }), fontWeight: 800, color: '#fff', lineHeight: 1.15, textShadow: `0 0 40px ${accent}55` }}>{result}</div>
              </div>
              <div style={{ transform: `scale(${ctaScale}) rotateY(${counterRot}deg)`, transformOrigin: 'center' }}>
                <div style={{ position: 'relative', overflow: 'hidden', background: `linear-gradient(135deg, ${accent} 0%, ${accent2} 100%)`, borderRadius: 28, padding: '36px 44px', display: 'flex', flexDirection: 'column', alignItems: 'center', boxShadow: `0 26px 70px ${accent}${breathe > 0.5 ? '88' : '55'}` }}>
                  <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${shimmerX}%`, width: '40%', background: 'linear-gradient(105deg, transparent 0%, rgba(255,255,255,0.35) 50%, transparent 100%)', transform: 'skewX(-18deg)' }} />
                  <p style={{ margin: 0, color: '#fff', fontSize: 40, fontWeight: 800, display: 'flex', alignItems: 'center', gap: 14 }}>
                    {ctaVerb} <span style={{ background: 'rgba(0,0,0,0.38)', padding: '6px 20px', borderRadius: 14, fontFamily: MONO, fontWeight: 700 }}>{cta}</span>
                  </p>
                  <p style={{ margin: '12px 0 0 0', color: '#FFFFFFdd', fontSize: 29, fontWeight: 500 }}>for the full breakdown <span style={{ display: 'inline-block', transform: `translateX(${arrowNudge}px)` }}>→</span></p>
                </div>
              </div>
            </div>

            {/* AICoreCube — persistent mascot */}
            <div style={{ position: 'absolute', left: cubeX, top: cubeY, width: EDGE, height: EDGE, marginLeft: -HALF, marginTop: -HALF, perspective: 900, perspectiveOrigin: '50% 42%', opacity: clamp01(interpolate(frame, [0, 10], [0, 1])) }}>
              <div style={{ position: 'absolute', inset: 0, transformStyle: 'preserve-3d', transform: `scale(${cubeScale}) rotateX(${cubeRx}deg) rotateY(${cubeRy}deg)` }}>
                {faceTransforms.map((ft, fi) => {
                  const ft2 = AI[faceTypes[fi]];
                  const litFront = Math.max(0, Math.cos((cubeRy - faceAngles[fi]) * Math.PI / 180));
                  const isActive = fi === 0;
                  return (
                    <div key={fi} style={{ position: 'absolute', width: EDGE, height: EDGE, backfaceVisibility: 'hidden', transform: ft, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14, borderRadius: 18, border: `1px solid ${ft2.a}77`, background: isActive ? `linear-gradient(135deg, ${ft2.a}, ${ft2.b})` : `${shade(ft2.a, -0.6)}`, opacity: 0.2 + 0.8 * litFront, boxShadow: `inset 0 0 60px ${ft2.a}44` }}>
                      <div style={{ fontSize: 92, fontWeight: 900, color: '#fff' }}>{ft2.glyph}</div>
                      <div style={{ fontSize: 28, fontWeight: 800, letterSpacing: 3, color: '#fff' }}>{ft2.label}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

        </div>
      </AbsoluteFill>

      {/* ════ FLAT OVERLAYS (outside the 3D stage) ════ */}
      <AbsoluteFill style={{ background: 'radial-gradient(120% 80% at 50% 40%, transparent 40%, rgba(0,0,0,0.55) 100%)', pointerEvents: 'none' }} />
      <AbsoluteFill style={{ backgroundImage: GRAIN, backgroundSize: '180px 180px', mixBlendMode: 'overlay', opacity: 0.07 + breathe * 0.04, pointerEvents: 'none' }} />
      {/*  beat-swap light sweep — a brief accent bloom punctuates each 3D panel turn */}
      <AbsoluteFill style={{ background: `radial-gradient(130% 90% at 50% 44%, ${accent}, transparent 58%)`, opacity: beatFlash * 0.42, mixBlendMode: 'screen', pointerEvents: 'none' }} />

      <div style={{ position: 'absolute', top: 36, left: 48, right: 48, height: 7, borderRadius: 999, background: 'rgba(255,255,255,0.14)', overflow: 'hidden' }}>
        <div style={{ width: `${progress * 100}%`, height: '100%', borderRadius: 999, background: `linear-gradient(90deg, ${accent}, ${accent2})`, boxShadow: `0 0 14px ${accent}cc` }} />
      </div>
      <div style={{ position: 'absolute', top: 86, left: 56, display: 'flex', alignItems: 'center', opacity: interpolate(frame, [4, 14], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>
        <span style={{ color: '#9D9ABF', fontSize: 28, letterSpacing: 6, fontWeight: 700 }}>PULSE · DAILY</span>
      </div>
      <div style={{ position: 'absolute', bottom: 56, left: 0, right: 0, textAlign: 'center', color: '#6E6A8C', fontSize: 24, fontFamily: MONO, letterSpacing: 2, opacity: 0.6 }}>{tipId} · @yourhandle</div>
    </AbsoluteFill>
  );
};

//  (2026-06-02): the creator — "add motion blur and ease in and ease out for all motion."
// CameraMotionBlur renders StoryScene at sub-frame samples and composites them → real,
// velocity-correct motion blur on EVERYTHING (3D transforms included) without any CSS
// blur() filter (which would flatten preserve-3d). Static elements sample to the same
// position → stay crisp; only moving elements blur. <Audio> stays OUTSIDE the blur so the
// VO isn't sub-sampled. Ease-in/out lives in the spring()/Easing.inOut reveals inside StoryScene.
export const StoryTipDeep: React.FC<StoryTipDeepProps> = (props) => {
  const samples = props.mbSamples ?? 6;
  const { fps } = useVideoConfig();
  // : word-level kinetic captions — placed OUTSIDE CameraMotionBlur (so the text pops stay
  // crisp, not sub-sampled) and OVER the single VO. Words distribute across the MEASURED VO duration
  // so they track the real narration; the Sequence clips at ~frame 352 so captions stop before the
  // CTA beat fills the lower third (no collision). Accent matches the tip's AI-type.
  const capAccent = (AI[(props.aiType as AiType)] || AI.image).a;
  const voDurFrames = Math.round((props.voDurS || 13) * fps);
  const capDur = Math.min(voDurFrames, 352);
  return (
    <AbsoluteFill style={{ backgroundColor: '#04020A' }}>
      {props.voSrc ? <Audio src={staticFile(props.voSrc)} /> : null}
      <CameraMotionBlur samples={samples} shutterAngle={180}>
        <StoryScene {...props} />
      </CameraMotionBlur>
      {props.voText ? (
        <Sequence from={0} durationInFrames={capDur}>
          <KineticCaptions text={props.voText} audioDurFrames={voDurFrames} fps={fps} accent={capAccent} bottom={384} fontSize={54} />
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};
