// : StoryCinematic — the rebuilt motion language the creator asked for: "cinematic 3D depth."
// A real GLSL aurora-depth background with a slow camera fly (AuroraShader), text on faux-glass
// panels, clip-wipe beat reveals, and headlines whose WORDS ILLUMINATE exactly as the voiceover
// says them (per-word ElevenLabs timestamps) — so the on-screen text literally tracks the voice.
// The VOICEOVER IS THE SPINE: every beat's in/out is the word-timestamp window, and the comp length
// (calculateMetadata in Root) = VO duration + tail, so the VO can NEVER cut off. No hinge-flips,
// no dust, no per-word rise-deblur — a different grammar from the old story comps.
import React from 'react';
import {
  AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig, interpolate, spring, Easing,
} from 'remotion';
import { AuroraShader } from './components/AuroraShader';
import { fitFontSize } from './components/fitFontSize';
// /3107: per-beat illustration scenes — motion graphics that DEPICT what the narration says.
// Imported from the ACTIVE registry, which the evolving engine rewrites per video so every render
// uses that video's own unique, freshly-generated animations (no two videos share scenes).
import { SceneHook, SceneInsight, SceneProof } from './scenes/active';

type SceneProps = {
  localFrame: number; tS: number; fps: number; beatDur: number;
  accentA: string; accentB: string; words: { w: string; startS: number; endS: number }[];
};
const SCENE_BY_KIND: Record<string, React.FC<SceneProps>> = {
  hook: SceneHook, insight: SceneInsight, proof: SceneProof,
};

type Word = { w: string; startS: number; endS: number };
type Seg = {
  kind: 'hook' | 'insight' | 'proof' | 'cta';
  text: string;
  big?: string;        // proof punch (e.g. "90%")
  eyebrow?: string;
  startS: number;
  endS: number;
  words?: Word[];
};

export interface StoryCinematicProps {
  ink?: string;
  accentA?: string;
  accentB?: string;
  eyebrow?: string;     // e.g. "AI · RAG"
  segments?: Seg[];
  cta?: string;         // keyword, e.g. "START"
  tagline?: string;     // one the studio positioning line on the end-card
  voSrc?: string;
  voDurS?: number;
  tipId?: string;
}

const DISPLAY = '"Archivo Black", "Arial Black", "Helvetica Neue", system-ui, sans-serif';
const BODY = '"Archivo", "Helvetica Neue", "Segoe UI", system-ui, sans-serif';
const MONO = '"Consolas", "SF Mono", monospace';
const GRAIN =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")";

const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };

const DEFAULT_SEGMENTS: Seg[] = [
  { kind: 'hook', text: 'YOUR RAG IS LYING TO YOU', startS: 0, endS: 2.4 },
  { kind: 'insight', text: 'Vector search misses exact terms — then invents the source.', startS: 2.5, endS: 7.0 },
  { kind: 'proof', text: 'Add a reranker. Faithfulness jumps to', big: '94%', startS: 7.1, endS: 10.5 },
  { kind: 'cta', text: 'Comment for the full breakdown', startS: 10.6, endS: 13.5 },
];

// ── faux-glass panel (no backdrop-filter dependency — reads as lit glass on the depth bg) ──
const Glass: React.FC<{ children: React.ReactNode; style?: React.CSSProperties; reveal: number; accent: string }> = ({ children, style, reveal, accent }) => {
  // reveal 0..1 drives a diagonal clip-wipe entrance
  const wipe = interpolate(reveal, [0, 1], [110, 0]);
  return (
    <div style={{
      position: 'relative', borderRadius: 30, padding: '54px 56px',
      background: 'linear-gradient(160deg, rgba(255,255,255,0.075), rgba(255,255,255,0.025))',
      border: '1px solid rgba(255,255,255,0.14)',
      boxShadow: `0 40px 120px rgba(0,0,0,0.55), inset 0 1px 0 rgba(255,255,255,0.28), 0 0 80px ${accent}22`,
      clipPath: `polygon(0 0, 100% 0, 100% 100%, 0% 100%)`,
      WebkitMaskImage: `linear-gradient(115deg, #000 ${100 - wipe}%, transparent ${100 - wipe + 6}%)`,
      maskImage: `linear-gradient(115deg, #000 ${100 - wipe}%, transparent ${100 - wipe + 6}%)`,
      ...style,
    }}>
      {/* lit top edge */}
      <div style={{ position: 'absolute', top: 0, left: 28, right: 28, height: 1.5, borderRadius: 2, background: `linear-gradient(90deg, transparent, ${accent}cc, transparent)`, opacity: 0.8 }} />
      {children}
    </div>
  );
};

// ── headline whose words illuminate as the VO speaks them ──
const SpokenHeadline: React.FC<{ seg: Seg; tS: number; fontSize: number; accentA: string; accentB: string }> = ({ seg, tS, fontSize, accentA, accentB }) => {
  const words = seg.words && seg.words.length ? seg.words : seg.text.split(/\s+/).map((w, i, arr) => ({ w, startS: seg.startS + (seg.endS - seg.startS) * (i / arr.length), endS: seg.startS + (seg.endS - seg.startS) * ((i + 1) / arr.length) }));
  return (
    <h1 style={{ margin: 0, fontFamily: DISPLAY, fontSize, fontWeight: 900, lineHeight: 1.02, letterSpacing: '-0.02em', display: 'flex', flexWrap: 'wrap', gap: '0 0.28em' }}>
      {words.map((wd, i) => {
        const spoken = tS >= wd.startS - 0.05;
        const active = tS >= wd.startS - 0.05 && tS < wd.endS + 0.12;
        const isNum = /\d/.test(wd.w); // proof numbers ("94%", "60%") get the brand gradient punch
        if (isNum) {
          return (
            <span key={i} style={{
              background: `linear-gradient(120deg, ${accentA}, ${accentB})`, WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent',
              opacity: spoken ? 1 : 0.32,
              filter: active ? `drop-shadow(0 0 34px ${accentA}aa)` : 'none',
              transform: active ? 'scale(1.06)' : 'none', display: 'inline-block',
            }}>{wd.w}</span>
          );
        }
        return (
          <span key={i} style={{
            color: spoken ? '#FFFFFF' : 'rgba(255,255,255,0.30)',
            textShadow: active ? `0 0 34px ${accentA}cc, 0 0 60px ${accentB}66` : (spoken ? '0 4px 28px rgba(0,0,0,0.5)' : 'none'),
            transform: active ? 'translateY(-2px)' : 'none',
            transition: 'none',
          }}>{wd.w}</span>
        );
      })}
    </h1>
  );
};

const Scene: React.FC<StoryCinematicProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames, width } = useVideoConfig();
  const tS = frame / fps;
  const accentA = props.accentA || '#8B5CF6';
  const accentB = props.accentB || '#22D3EE';
  const segs = props.segments && props.segments.length ? props.segments : DEFAULT_SEGMENTS;
  const cta = props.cta || 'START';
  const eyebrow = props.eyebrow || 'PULSE · DAILY';
  const tagline = props.tagline || 'The AI that runs my business while I sleep.';

  const fr = (s: number) => s * fps;
  const progress = interpolate(frame, [0, durationInFrames - 2], [0, 1], clamp);

  // a faint parallax light streak for extra depth (HTML, on top of the shader)
  const streakY = interpolate(frame, [0, durationInFrames], [-120, 120]);

  return (
    <AbsoluteFill style={{ backgroundColor: props.ink || '#0A0A12' }}>
      {/* ── cinematic depth background (real shader) ── */}
      <AuroraShader ink={props.ink || '#0A0A12'} accentA={accentA} accentB={accentB} intensity={1} />

      {/* depth scrim for legibility + parallax streak */}
      <AbsoluteFill style={{ background: 'radial-gradient(125% 95% at 50% 42%, transparent 30%, rgba(5,4,12,0.72) 100%)', pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', left: -200, right: -200, top: 520 + streakY, height: 380, background: `linear-gradient(180deg, transparent, ${accentB}14, transparent)`, transform: 'rotate(-8deg)', filter: 'blur(40px)', pointerEvents: 'none' }} />

      {/* ── top chrome ── */}
      <div style={{ position: 'absolute', top: 64, left: 64, right: 64, display: 'flex', justifyContent: 'space-between', alignItems: 'center', opacity: interpolate(frame, [4, 16], [0, 1], clamp) }}>
        <span style={{ color: '#C9C5E8', fontSize: 26, letterSpacing: 7, fontWeight: 800, fontFamily: BODY }}>{eyebrow.toUpperCase()}</span>
        <span style={{ width: 12, height: 12, borderRadius: '50%', background: accentB, boxShadow: `0 0 16px ${accentB}`, opacity: 0.5 + 0.5 * Math.abs(Math.sin(frame / 16)) }} />
      </div>
      {/* thin progress line */}
      <div style={{ position: 'absolute', top: 112, left: 64, right: 64, height: 3, borderRadius: 2, background: 'rgba(255,255,255,0.10)', overflow: 'hidden' }}>
        <div style={{ width: `${progress * 100}%`, height: '100%', background: `linear-gradient(90deg, ${accentA}, ${accentB})`, boxShadow: `0 0 12px ${accentA}` }} />
      </div>

      {/* ── beats (VO-locked) ── */}
      {segs.map((seg, i) => {
        const from = fr(seg.startS);
        const to = i === segs.length - 1 ? durationInFrames : fr(seg.endS) + 6;
        const local = frame - from;
        const enter = interpolate(local, [0, 11], [0, 1], { ...clamp, easing: Easing.out(Easing.cubic) });
        const reveal = spring({ frame: local, fps, config: { damping: 18, stiffness: 120, mass: 0.9 } });
        // fade out as the next beat takes over
        const out = i === segs.length - 1 ? 1 : 1 - interpolate(frame, [fr(seg.endS), fr(seg.endS) + 8], [0, 1], clamp);
        const visible = frame >= from - 8 && frame < to;
        if (!visible) return null;
        const baseY = interpolate(reveal, [0, 1], [40, 0]);
        const opacity = Math.min(enter, out);

        if (seg.kind === 'cta') {
          const pop = spring({ frame: local, fps, config: { damping: 13, stiffness: 130 } });
          const arrow = Math.sin(frame / 6) * 7;
          return (
            <AbsoluteFill key={i} style={{ alignItems: 'center', justifyContent: 'center', opacity, padding: '0 70px' }}>
              <div style={{ transform: `scale(${interpolate(pop, [0, 1], [0.86, 1])}) translateY(${baseY}px)`, width: '100%' }}>
                <Glass reveal={enter} accent={accentA} style={{ textAlign: 'center', padding: '64px 56px' }}>
                  <div style={{ fontFamily: BODY, fontSize: 28, letterSpacing: 6, fontWeight: 800, color: accentB, marginBottom: 26 }}>FOR THE FULL BREAKDOWN</div>
                  <div style={{ fontFamily: DISPLAY, fontSize: 88, fontWeight: 900, color: '#fff', lineHeight: 1.0, letterSpacing: '-0.02em' }}>
                    Comment{' '}
                    <span style={{ background: `linear-gradient(120deg, ${accentA}, ${accentB})`, WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' }}>{cta}</span>
                  </div>
                  <div style={{ marginTop: 22, fontFamily: BODY, fontSize: 38, fontWeight: 700, color: '#E7E4F7' }}>
                    and I’ll send it over <span style={{ display: 'inline-block', transform: `translateX(${arrow}px)`, color: accentB }}>→</span>
                  </div>
                  <div style={{ marginTop: 34, height: 1, background: 'rgba(255,255,255,0.12)' }} />
                  <div style={{ marginTop: 28, fontFamily: BODY, fontSize: 27, fontWeight: 500, color: '#A9A4C8', fontStyle: 'italic' }}>{tagline}</div>
                </Glass>
              </div>
            </AbsoluteFill>
          );
        }

        // hook / insight / proof — illustration (top) DEPICTS the line; word-lit caption on glass (lower)
        const isHook = seg.kind === 'hook';
        const Scene = SCENE_BY_KIND[seg.kind];
        const headFont = fitFontSize({
          text: seg.text, width: 820,
          maxFontSize: isHook ? 80 : 46, minFontSize: 32,
          maxLines: 3, fontFamily: DISPLAY, fontWeight: 900, letterSpacing: '-0.02em',
        });
        return (
          <AbsoluteFill key={i} style={{ opacity }}>
            {/* dark STAGE behind the illustration so the motion graphics read at full contrast over the
                aurora instead of washing out (the "too transparent" fix). Soft radial + rounded = premium. */}
            <div style={{ position: 'absolute', top: 168, left: 40, right: 40, height: 884, borderRadius: 40, background: 'radial-gradient(125% 100% at 50% 42%, rgba(6,5,14,0.86) 0%, rgba(6,5,14,0.62) 68%, rgba(6,5,14,0.30) 100%)', boxShadow: 'inset 0 0 170px rgba(0,0,0,0.6), 0 38px 90px rgba(0,0,0,0.5)', border: '1px solid rgba(255,255,255,0.07)' }} />
            {/* illustration stage (1080 x 830) — contrast/brightness boosted so the elements POP */}
            <div style={{ position: 'absolute', top: 196, left: 0, right: 0, height: 830, filter: 'brightness(1.2) contrast(1.16) saturate(1.1)' }}>
              {Scene ? <Scene localFrame={local} tS={tS} fps={fps} beatDur={to - from} accentA={accentA} accentB={accentB} words={seg.words || []} /> : null}
            </div>
            {/* word-illuminated caption on glass (lower third) */}
            <div style={{ position: 'absolute', top: 1150, left: 70, right: 70, transform: `translateY(${baseY}px)` }}>
              <Glass reveal={enter} accent={accentA} style={{ padding: '34px 46px' }}>
                {seg.eyebrow ? <div style={{ fontFamily: BODY, fontSize: 24, letterSpacing: 5, fontWeight: 800, color: accentB, marginBottom: 16 }}>{seg.eyebrow.toUpperCase()}</div> : null}
                <SpokenHeadline seg={seg} tS={tS} fontSize={headFont} accentA={accentA} accentB={accentB} />
              </Glass>
            </div>
          </AbsoluteFill>
        );
      })}

      {/* ── flat film overlays ── */}
      <AbsoluteFill style={{ backgroundImage: GRAIN, backgroundSize: '200px 200px', mixBlendMode: 'overlay', opacity: 0.05, pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', bottom: 54, left: 0, right: 0, textAlign: 'center', color: '#7B76A0', fontSize: 23, fontFamily: MONO, letterSpacing: 2, opacity: 0.65 }}>{props.tipId ? `${props.tipId} · ` : ''}@yourhandle</div>
    </AbsoluteFill>
  );
};

export const StoryCinematic: React.FC<StoryCinematicProps> = (props) => {
  return (
    <AbsoluteFill style={{ backgroundColor: props.ink || '#0A0A12' }}>
      {props.voSrc ? <Audio src={staticFile(props.voSrc)} /> : null}
      <Scene {...props} />
    </AbsoluteFill>
  );
};
