//  (2026-05-18 cycle 130): 7-second IG Story Remotion template.
//  (2026-06-02): PREMIUM REBUILD. the creator: "very nice remotion / animations
// for stories ... current pipeline is very bad animations / quality." This composition
// keeps the EXACT same props interface (hook / body / tipId / category) and the
// 210-frame / 1080x1920 / 30fps spec — so gen-daily-tip-video.cjs, Root.tsx
// defaultProps and ig-story-autopost.cjs all keep working untouched — but the motion
// design is fully reworked: animated aurora background (drifting orbs), film grain +
// vignette, an IG story progress bar, kinetic per-word headline reveals (rise +
// de-blur + spring overshoot), staggered body reveals with accent ticks, and a CTA
// pill with a looping shimmer sweep + breathing glow. Continuous motion across all 7s
// so no frame ever looks frozen (the old version's core "static" complaint).
//
// Composition: 7 seconds @ 30fps = 210 frames. 1080x1920 vertical.
// Driven by ig-story-autopost.cjs which renders this with daily tip text
// from memory/daily-tip-bank.json.
//
// Props passed in at render time:
//   - hook: string ("STOP USING ONE MODEL")
//   - body: string[] (["Route 3 LLMs.", "Watch costs drop 60 percent."])
//   - tipId: string ("T001")
//   - category: string ("ai-stack" — controls accent color)
import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Easing,
  random,
} from 'remotion';
import { fitFontSize } from './components/fitFontSize';

export interface StoryTipProps {
  hook: string;
  body: string[];
  tipId?: string;
  category?: string;
}

// Category → {accent, accent2} gradient pair. Richer than the old single color so the
// background orbs and CTA gradient have real depth.
const CATEGORY_COLORS: Record<string, { a: string; b: string }> = {
  'ai-stack': { a: '#A855F7', b: '#6366F1' }, // purple → indigo (primary AI brand)
  automation: { a: '#06B6D4', b: '#3B82F6' }, // cyan → blue (workflow)
  operator: { a: '#F59E0B', b: '#F97316' },   // amber → orange (leverage)
  prompts: { a: '#10B981', b: '#14B8A6' },     // emerald → teal (craft)
  discipline: { a: '#EF4444', b: '#F43F5E' },  // red → rose (rules)
  content: { a: '#EC4899', b: '#A855F7' },     // pink → purple (creative)
  default: { a: '#A855F7', b: '#6366F1' },
};

const FONT = '"Segoe UI", "Helvetica Neue", "Arial Black", system-ui, sans-serif';

// Cheap, robust film grain — inline SVG fractal noise as a data URI, tiled small.
const GRAIN =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")";

export const StoryTipReel: React.FC<StoryTipProps> = ({
  hook = 'STOP USING ONE MODEL',
  body = ['Route 3 LLMs.', 'Watch costs drop 60 percent.'],
  tipId = 'T001',
  category = 'ai-stack',
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width, height } = useVideoConfig();
  const { a: accent, b: accent2 } = CATEGORY_COLORS[category] || CATEGORY_COLORS.default;

  // ── Global "breathing" + Ken-Burns settle so the whole frame is always alive ──
  const breathe = Math.sin(frame / 26) * 0.5 + 0.5; // 0..1 slow
  const kenBurns = interpolate(frame, [0, durationInFrames], [1.0, 1.045], {
    extrapolateRight: 'clamp',
  });
  const introFade = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: 'clamp' });

  // ── Drifting aurora orbs (continuous motion the entire 7s) ──
  const orb1X = Math.sin(frame / 60) * 90;
  const orb1Y = Math.cos(frame / 75) * 70;
  const orb2X = Math.cos(frame / 52) * 110;
  const orb2Y = Math.sin(frame / 68) * 90;
  const orbScale = 1 + breathe * 0.08;

  // ── Story progress bar (IG convention — instantly reads as "a story") ──
  const progress = interpolate(frame, [4, durationInFrames - 2], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // ── Top chrome (brand + category pill) ──
  const chromeT = spring({ frame: frame - 6, fps, config: { damping: 200, stiffness: 120 } });
  const chromeY = interpolate(chromeT, [0, 1], [-30, 0]);

  // ── Kinetic hook: per-word rise + de-blur + spring overshoot ──
  const words = String(hook).toUpperCase().split(/\s+/).filter(Boolean);
  // : fit the hook size to ≤3 lines so a long headline shrinks instead of clipping — applied
  // to the per-word fontSize so the rise/de-blur/overshoot animation is fully preserved.
  const hookSize = fitFontSize({ text: hook, width: 952, maxFontSize: 118, minFontSize: 58, maxLines: 3, fontFamily: FONT, fontWeight: 900, letterSpacing: '-3px', textTransform: 'uppercase' });
  const HOOK_START = 12;
  const HOOK_STAGGER = 4;
  const wordAnim = (i: number) => {
    const local = frame - (HOOK_START + i * HOOK_STAGGER);
    const s = spring({ frame: local, fps, config: { damping: 14, stiffness: 130, mass: 0.7 } });
    const o = interpolate(local, [0, 10], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    const y = interpolate(s, [0, 1], [70, 0]);
    const blur = interpolate(local, [0, 12], [14, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    return { o, y, blur };
  };
  const lastWordDone = HOOK_START + (words.length - 1) * HOOK_STAGGER + 14;

  // ── Accent underline wipes in under the hook once words have landed ──
  const underline = interpolate(frame, [lastWordDone, lastWordDone + 16], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // ── Body lines: staggered clip + slide + de-blur, with an accent tick ──
  const BODY_START = lastWordDone + 6;
  const bodyAnim = (i: number) => {
    const start = BODY_START + i * 12;
    const local = frame - start;
    const o = interpolate(local, [0, 14], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    const x = interpolate(local, [0, 16], [-26, 0], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.out(Easing.cubic),
    });
    const tick = interpolate(local, [0, 12], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    return { o, x, tick };
  };

  // ── CTA: spring pop + breathing glow + looping shimmer sweep ──
  const CTA_START = 150;
  const ctaT = spring({ frame: frame - CTA_START, fps, config: { damping: 12, stiffness: 140, mass: 0.8 } });
  const ctaScale = interpolate(ctaT, [0, 1], [0.82, 1]);
  const ctaOpacity = interpolate(frame, [CTA_START, CTA_START + 12], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const ctaGlow = 0.5 + breathe * 0.5; // 0..1
  // shimmer sweeps left→right on a ~36-frame loop after the CTA appears
  const shimmer = ((frame - CTA_START) % 36) / 36;
  const shimmerX = interpolate(shimmer, [0, 1], [-60, 160]);
  const arrowNudge = Math.sin(frame / 6) * 6;

  // ── Deterministic floating dust (random() is stable per-seed; no per-frame flicker) ──
  const dust = Array.from({ length: 16 }, (_, i) => {
    const bx = random(`x${i}`) * width;
    const by = random(`y${i}`) * height;
    const driftY = Math.sin(frame / (24 + random(`s${i}`) * 30) + i) * 22;
    const driftX = Math.cos(frame / (30 + random(`t${i}`) * 26) + i) * 14;
    const size = 2 + random(`r${i}`) * 4;
    const op = (0.12 + random(`o${i}`) * 0.22) * (0.5 + breathe * 0.5);
    return { x: bx + driftX, y: by + driftY, size, op, key: i };
  });

  return (
    <AbsoluteFill style={{ backgroundColor: '#04020A', fontFamily: FONT, opacity: introFade }}>
      {/* ── Animated aurora background ── */}
      <AbsoluteFill style={{ transform: `scale(${kenBurns})`, transformOrigin: 'center' }}>
        <AbsoluteFill
          style={{ background: 'linear-gradient(165deg, #07030F 0%, #0C0518 55%, #05030D 100%)' }}
        />
        {/* orb 1 — accent, upper area */}
        <div
          style={{
            position: 'absolute',
            top: 120,
            left: '50%',
            width: 1000,
            height: 1000,
            marginLeft: -500,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${accent}55 0%, ${accent}00 62%)`,
            filter: 'blur(70px)',
            transform: `translate(${orb1X}px, ${orb1Y}px) scale(${orbScale})`,
          }}
        />
        {/* orb 2 — secondary accent, lower-left */}
        <div
          style={{
            position: 'absolute',
            bottom: 80,
            left: -120,
            width: 900,
            height: 900,
            borderRadius: '50%',
            background: `radial-gradient(circle, ${accent2}4d 0%, ${accent2}00 60%)`,
            filter: 'blur(80px)',
            transform: `translate(${orb2X}px, ${orb2Y}px) scale(${orbScale})`,
          }}
        />
        {/* floating dust */}
        {dust.map((d) => (
          <div
            key={d.key}
            style={{
              position: 'absolute',
              left: d.x,
              top: d.y,
              width: d.size,
              height: d.size,
              borderRadius: '50%',
              background: '#FFFFFF',
              opacity: d.op,
              filter: 'blur(0.5px)',
            }}
          />
        ))}
      </AbsoluteFill>

      {/* ── Vignette for depth ── */}
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(120% 80% at 50% 38%, transparent 40%, rgba(0,0,0,0.55) 100%)',
          pointerEvents: 'none',
        }}
      />
      {/* ── Film grain ── */}
      <AbsoluteFill
        style={{
          backgroundImage: GRAIN,
          backgroundSize: '180px 180px',
          mixBlendMode: 'overlay',
          opacity: 0.07 + breathe * 0.04,
          pointerEvents: 'none',
        }}
      />

      {/* ── Story progress bar ── */}
      <div
        style={{
          position: 'absolute',
          top: 36,
          left: 48,
          right: 48,
          height: 7,
          borderRadius: 999,
          background: 'rgba(255,255,255,0.14)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${progress * 100}%`,
            height: '100%',
            borderRadius: 999,
            background: `linear-gradient(90deg, ${accent}, ${accent2})`,
            boxShadow: `0 0 14px ${accent}cc`,
          }}
        />
      </div>

      {/* ── Top chrome: brand + category pill ── */}
      <div
        style={{
          position: 'absolute',
          top: 86,
          left: 56,
          right: 56,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          transform: `translateY(${chromeY}px)`,
          opacity: chromeT,
        }}
      >
        <span style={{ color: '#9D9ABF', fontSize: 28, letterSpacing: 6, fontWeight: 700 }}>
          PULSE · DAILY
        </span>
        <span
          style={{
            color: '#FFFFFF',
            fontSize: 26,
            letterSpacing: 3,
            fontWeight: 800,
            padding: '10px 22px',
            background: `linear-gradient(135deg, ${accent}33, ${accent2}22)`,
            border: `1.5px solid ${accent}aa`,
            borderRadius: 999,
            textTransform: 'uppercase',
            boxShadow: `0 0 22px ${accent}44`,
          }}
        >
          {category}
        </span>
      </div>

      {/* ── Hook — kinetic per-word reveal ── */}
      <div style={{ position: 'absolute', top: 300, left: 64, right: 64 }}>
        <h1
          style={{
            margin: 0,
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0 24px',
            color: '#FFFFFF',
            fontSize: hookSize,
            fontWeight: 900,
            lineHeight: 1.0,
            letterSpacing: -3,
          }}
        >
          {words.map((w, i) => {
            const { o, y, blur } = wordAnim(i);
            return (
              <span
                key={i}
                style={{
                  display: 'inline-block',
                  opacity: o,
                  transform: `translateY(${y}px)`,
                  filter: blur > 0.1 ? `blur(${blur}px)` : 'none',
                  textShadow: '0 6px 40px rgba(0,0,0,0.45)',
                }}
              >
                {w}
              </span>
            );
          })}
        </h1>
        {/* accent underline wipe */}
        <div
          style={{
            marginTop: 28,
            height: 10,
            width: interpolate(underline, [0, 1], [0, 240]),
            borderRadius: 999,
            background: `linear-gradient(90deg, ${accent}, ${accent2})`,
            boxShadow: `0 0 24px ${accent}aa`,
          }}
        />
      </div>

      {/* ── Body — staggered reveal with accent ticks ── */}
      <div
        style={{
          position: 'absolute',
          top: 960,
          left: 64,
          right: 64,
          display: 'flex',
          flexDirection: 'column',
          gap: 30,
        }}
      >
        {body.map((line, i) => {
          const { o, x, tick } = bodyAnim(i);
          return (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 22,
                opacity: o,
                transform: `translateX(${x}px)`,
              }}
            >
              <div
                style={{
                  marginTop: 18,
                  width: 14,
                  height: 14 + tick * 26,
                  flexShrink: 0,
                  borderRadius: 4,
                  background: `linear-gradient(180deg, ${accent}, ${accent2})`,
                  boxShadow: `0 0 16px ${accent}88`,
                }}
              />
              <p
                style={{
                  margin: 0,
                  color: '#ECEAFB',
                  fontSize: 54,
                  fontWeight: 600,
                  lineHeight: 1.25,
                }}
              >
                {line}
              </p>
            </div>
          );
        })}
      </div>

      {/* ── CTA — spring pop + breathing glow + shimmer sweep ── */}
      <div
        style={{
          position: 'absolute',
          bottom: 210,
          left: 64,
          right: 64,
          opacity: ctaOpacity,
          transform: `scale(${ctaScale})`,
          transformOrigin: 'center',
        }}
      >
        <div
          style={{
            position: 'relative',
            overflow: 'hidden',
            background: `linear-gradient(135deg, ${accent} 0%, ${accent2} 100%)`,
            borderRadius: 28,
            padding: '40px 44px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            boxShadow: `0 26px 70px ${accent}${ctaGlow > 0.66 ? '88' : '55'}`,
          }}
        >
          {/* shimmer sweep */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              bottom: 0,
              left: `${shimmerX}%`,
              width: '40%',
              background:
                'linear-gradient(105deg, transparent 0%, rgba(255,255,255,0.35) 50%, transparent 100%)',
              transform: 'skewX(-18deg)',
              pointerEvents: 'none',
            }}
          />
          <p
            style={{
              margin: 0,
              color: '#FFFFFF',
              fontSize: 40,
              fontWeight: 800,
              textAlign: 'center',
              letterSpacing: 0.5,
              display: 'flex',
              alignItems: 'center',
              gap: 14,
            }}
          >
            Reply
            <span
              style={{
                background: 'rgba(0,0,0,0.38)',
                padding: '6px 20px',
                borderRadius: 14,
                fontFamily: '"Consolas", "SF Mono", monospace',
                fontWeight: 700,
                letterSpacing: 1,
              }}
            >
              START
            </span>
          </p>
          <p
            style={{
              margin: '12px 0 0 0',
              color: '#FFFFFFdd',
              fontSize: 30,
              fontWeight: 500,
              textAlign: 'center',
            }}
          >
            for the full system{' '}
            <span style={{ display: 'inline-block', transform: `translateX(${arrowNudge}px)` }}>→</span>
          </p>
        </div>
      </div>

      {/* ── Watermark ── */}
      <div
        style={{
          position: 'absolute',
          bottom: 56,
          left: 0,
          right: 0,
          textAlign: 'center',
          color: '#6E6A8C',
          fontSize: 24,
          fontFamily: '"Consolas", monospace',
          letterSpacing: 2,
          opacity: introFade * 0.6,
        }}
      >
        {tipId} · @yourhandle
      </div>
    </AbsoluteFill>
  );
};
