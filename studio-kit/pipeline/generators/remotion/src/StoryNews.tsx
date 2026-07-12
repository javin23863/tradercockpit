//  (2026-06-10): StoryNews — LIVE AI-news wire in "THE OVERNIGHT" editorial aesthetic.
// the creator: "do live news with this... so ppl get actual live news coming out in real time" + "animations
// representing the video topics in real time." Real headlines stream in like a Bloomberg terminal wire;
// the hero headline + the giant topic number + the streaming source-tagged stories ARE the live topic.
// Props-driven so a daily pipeline can repopulate it with whatever's fresh. 480f @ 30fps, 1080x1920.
import React from 'react';
import {
  AbsoluteFill, Audio, staticFile, Sequence,
  useCurrentFrame, useVideoConfig, interpolate, spring, Easing,
} from 'remotion';
import { CameraMotionBlur } from '@remotion/motion-blur';
import { FitText } from './components/FitText';
import { KineticCaptions } from './components/KineticCaptions';

export interface NewsItem { src: string; text: string }
export interface StoryNewsProps {
  dateLabel?: string;
  kicker?: string;
  headline?: string;
  heroNum?: string;        // e.g. "$965B"
  heroNumLabel?: string;   // e.g. "VALUATION"
  items?: NewsItem[];
  cta?: string;            // the comment keyword
  ctaVerb?: string;
  ctaLine?: string;
  voSrc?: string;
  voIntro?: string;        // : 3 sectioned VO clips, placed at their visual beats (sync)
  voWire?: string;
  voCta?: string;
  voIntroText?: string;    // : the spoken text of each section, for word-level kinetic captions
  voWireText?: string;
  voCtaText?: string;
  voIntroDurS?: number;    // : real audio duration (s) of each section, for caption timing
  voWireDurS?: number;
  voCtaDurS?: number;
  mbSamples?: number;
  accent?: string;         // : per-video palette + motion from the RL style selector
  accent2?: string;
  hot?: string;
  motion?: 'cinematic' | 'kinetic' | 'wave' | 'snap';
}

const FONT = '"Archivo Black", "Arial Black", "Helvetica Neue", system-ui, sans-serif';
const BODY = '"Archivo", "Helvetica Neue", "Segoe UI", system-ui, sans-serif';
const MONO = '"Consolas", "SF Mono", monospace';
const INK = '#050505';
const PAPER = '#F4F1EA';
const DIM = '#6E6A60';
const BRAND_A = '#FF8A00'; // default accent — the RL style selector overrides this per-video
const BRAND_B = '#FFB347'; // default hot/accent2
const LIVE = '#FF453A'; // breaking-red, used ONLY for the LIVE badge + fresh-dot
const GRAIN =
  "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E\")";

const clamp = { extrapolateLeft: 'clamp' as const, extrapolateRight: 'clamp' as const };
const ramp = (f: number, a: number, b: number) =>
  interpolate(f, [a, b], [0, 1], { ...clamp, easing: Easing.inOut(Easing.cubic) });
const beat = (f: number, inA: number, inB: number, outA: number, outB: number) =>
  Math.min(ramp(f, inA, inB), 1 - ramp(f, outA, outB));

const Scene: React.FC<StoryNewsProps> = ({
  dateLabel = 'MONTH DD, YYYY',
  kicker = 'TODAY IN [TOPIC]',
  headline = 'YOUR HEADLINE GOES HERE.',
  heroNum = '$1.2B',
  heroNumLabel = 'VALUATION',
  items = [
    { src: 'BREAKING', text: 'your top story headline — swap in your own' },
    { src: 'MARKET', text: 'a second wire item streams in' },
    { src: 'UPDATE', text: 'third source-tagged headline' },
    { src: 'TREND', text: 'fourth topic beat in the feed' },
    { src: 'LIVE', text: 'fifth streaming story' },
    { src: 'WIRE', text: 'sixth headline in the stream' },
    { src: 'DESK', text: 'seventh item on the wire' },
    { src: 'FEED', text: 'eighth — then the wire loops' },
  ],
  cta = 'START',
  ctaVerb = 'Comment',
  ctaLine = 'for the full breakdown',
  accent = BRAND_A,
  accent2 = BRAND_B,
  hot = BRAND_B,
  motion = 'cinematic',
}) => {
  // : render at 60fps for buttery motion. Normalize to a virtual 30fps timeline so every
  // tuned timing below stays correct — the curves are sampled twice as often (+ motion blur between).
  const { fps: realFps, durationInFrames: realDur, width, height } = useVideoConfig();
  const frame = useCurrentFrame() * 30 / realFps;
  const durationInFrames = realDur * 30 / realFps;
  const fps = 30;
  const X = 92;

  // camera: still open → dolly + faint parallax. Range varies by motion preset ( variety).
  const M_DOLLY: Record<string, [number, number]> = { cinematic: [1700, 1240], kinetic: [1500, 1170], wave: [1820, 1290], snap: [1420, 1330] };
  const dollyPersp = interpolate(frame, [78, durationInFrames], M_DOLLY[motion] || M_DOLLY.cinematic, { ...clamp, easing: Easing.bezier(0.16, 1, 0.3, 1) });
  const yaw = frame < 88 ? 0 : Math.sin((frame - 88) / 220) * interpolate(frame, [88, 170], [4.5, 1.6], clamp);
  const pitch = frame < 88 ? 0 : Math.cos(frame / 240) * 1.8;
  const keyDx = Math.sin(frame / 90) * 16, keyDy = Math.cos(frame / 110) * 13;

  // beats — clean gaps between so they never overlay 
  const oOpen = beat(frame, 6, 30, 80, 94);
  const oHero = beat(frame, 100, 116, 190, 206);
  const oWire = beat(frame, 214, 232, 414, 430);
  const oCta = ramp(frame, 426, 448);
  // : smooth slide-in-from-below + slide-out-upward per beat (the "smooth in and out" the creator asked for)
  const beatY = (inA: number, inB: number, outA: number, outB: number) =>
    interpolate(ramp(frame, inA, inB), [0, 1], [34, 0]) + interpolate(ramp(frame, outA, outB), [0, 1], [0, -34]);
  const yOpen = beatY(6, 30, 80, 94);
  const yHero = beatY(100, 116, 190, 206);
  const yWire = beatY(214, 232, 414, 430);
  const yCta = interpolate(ramp(frame, 426, 448), [0, 1], [34, 0]);

  // LIVE badge pulse (deterministic)
  const livePulse = 0.55 + 0.45 * Math.abs(Math.sin(frame / 9));
  // : the HERO entrance is a different animation per motion preset (so no two videos look alike):
  // cinematic = top-down clip-wipe · snap = fast left→right wipe · kinetic = scale-pop · wave = slide-in.
  const heroIn = ramp(frame, 96, 118);
  const heroSpring = spring({ frame: frame - 96, fps, config: { damping: 12, stiffness: 140 } });
  const heroClip = motion === 'cinematic' ? `inset(${interpolate(heroIn, [0, 1], [100, 0])}% 0 0 0)`
    : motion === 'snap' ? `inset(0 ${interpolate(ramp(frame, 98, 108), [0, 1], [100, 0])}% 0 0)`
    : 'none';
  const heroTransform = motion === 'kinetic' ? `scale(${interpolate(heroSpring, [0, 1], [0.72, 1])})`
    : motion === 'wave' ? `translateX(${interpolate(heroIn, [0, 1], [-100, 0])}px)`
    : 'none';
  const heroNumPop = interpolate(spring({ frame: frame - 118, fps, config: { damping: 13, stiffness: 150 } }), [0, 1], [0.6, 1]);

  // wire feed timing — ROW sized for a clean single-line headline (no 2-line overlap)
  const WIRE0 = 234, STG = 22, ROW = 104, WINDOW = 5;
  const lineStart = (i: number) => WIRE0 + i * STG;
  const ats = (i: number) => { const s = 41 + i * 3; return `09:${String(s).padStart(2, '0')} ET`; };
  const visible = items.filter((_, i) => frame >= lineStart(i)).length;
  const conveyorY = -Math.max(0, visible - WINDOW) * ROW;

  const progress = interpolate(frame, [4, durationInFrames - 2], [0, 1], clamp);
  const dust = Array.from({ length: 9 }, (_, i) => ({ x: ((i * 149) % width) + Math.cos(frame / 50 + i) * 10, y: ((i * 277) % height) + Math.sin(frame / 44 + i) * 12, s: 2 + (i % 3), o: 0.05 + (i % 4) * 0.014 }));

  return (
    <AbsoluteFill style={{ backgroundColor: INK, fontFamily: FONT }}>
      <AbsoluteFill style={{ perspective: dollyPersp, perspectiveOrigin: '34% 28%', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', inset: 0, transformStyle: 'preserve-3d', transform: `rotateX(${pitch}deg) rotateY(${yaw}deg)` }}>
          {/* BG + amber key light */}
          <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden', transform: 'translateZ(-360px) scale(1.3)' }}>
            <AbsoluteFill style={{ background: `linear-gradient(160deg, #0b0814 0%, ${INK} 52%, #06090f 100%)` }} />
            {/* : dual drifting aurora-mesh (depth + fills the dead space) — GPU-cheap, blur/translate only */}
            <div style={{ position: 'absolute', top: -280, left: -180, width: 1240, height: 1240, borderRadius: '50%', background: `radial-gradient(circle, ${accent}46 0%, ${accent}00 60%)`, filter: 'blur(100px)', transform: `translate(${keyDx}px, ${keyDy}px)` }} />
            <div style={{ position: 'absolute', bottom: -360, right: -260, width: 1360, height: 1360, borderRadius: '50%', background: `radial-gradient(circle, ${accent2}3a 0%, ${accent2}00 62%)`, filter: 'blur(124px)', transform: `translate(${-keyDx * 0.8}px, ${-keyDy * 0.8}px)` }} />
            <div style={{ position: 'absolute', top: '40%', left: '50%', width: 820, height: 820, borderRadius: '50%', background: `radial-gradient(circle, ${hot}26 0%, ${hot}00 60%)`, filter: 'blur(118px)', transform: `translate(${Math.sin(frame / 120) * 44 - 410}px, ${Math.cos(frame / 130) * 36 - 410}px)` }} />
            {dust.map((d, i) => <div key={i} style={{ position: 'absolute', left: d.x, top: d.y, width: d.s, height: d.s, borderRadius: '50%', background: PAPER, opacity: d.o }} />)}
          </div>

          <div style={{ position: 'absolute', inset: 0, backfaceVisibility: 'hidden', transform: 'translateZ(40px)' }}>

            {/* ── OPEN: LIVE badge ── */}
            <div style={{ position: 'absolute', top: 380, left: 0, right: 0, textAlign: 'center', opacity: oOpen, transform: `translateY(${yOpen}px)` }}>
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 16, border: `2px solid ${LIVE}`, borderRadius: 6, padding: '14px 28px' }}>
                <span style={{ width: 18, height: 18, borderRadius: '50%', background: LIVE, opacity: livePulse, boxShadow: `0 0 ${livePulse * 24}px ${LIVE}` }} />
                <span style={{ fontFamily: MONO, fontSize: 44, fontWeight: 700, letterSpacing: 6, color: PAPER }}>LIVE</span>
              </div>
              <div style={{ marginTop: 36, fontSize: 36, fontWeight: 800, letterSpacing: 10, color: accent, fontFamily: BODY }}>{kicker}</div>
              <div style={{ marginTop: 12, fontFamily: MONO, fontSize: 28, color: DIM, letterSpacing: 3 }}>{dateLabel}</div>
            </div>

            {/* ── HERO headline + topic number ── */}
            <div style={{ position: 'absolute', top: 320, left: X, right: 72, opacity: oHero, transform: `translateY(${yHero}px)` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 26 }}>
                <span style={{ width: 14, height: 14, borderRadius: '50%', background: LIVE, opacity: livePulse }} />
                <span style={{ fontSize: 30, fontWeight: 800, letterSpacing: 7, color: LIVE, fontFamily: BODY }}>BREAKING</span>
              </div>
              {/* : auto-fit headline — wraps + shrinks to fit (kills the "GUARDRAILS O..." mid-word clip) */}
              <div style={{ clipPath: heroClip, transform: heroTransform, transformOrigin: 'left center' }}>
                <FitText text={headline} width={916} maxFontSize={112} minFontSize={52} maxLines={3}
                  fontFamily={FONT} fontWeight={900} letterSpacing="-4px" lineHeight={0.95}
                  style={{ margin: 0, color: PAPER, textShadow: '0 32px 60px rgba(0,0,0,0.7)' }} />
              </div>
              {heroNum ? (
                <div style={{ marginTop: 50, display: 'flex', alignItems: 'baseline', gap: 24, transform: `scale(${heroNumPop})`, transformOrigin: 'left bottom' }}>
                  <span style={{ fontSize: 170, fontWeight: 900, color: hot, letterSpacing: -6, lineHeight: 0.85, fontVariantNumeric: 'tabular-nums', textShadow: `0 0 ${ramp(frame, 116, 150) * 60}px ${accent}55` }}>{heroNum}</span>
                  <span style={{ fontSize: 30, fontWeight: 800, letterSpacing: 6, color: DIM, fontFamily: BODY }}>{heroNumLabel}</span>
                </div>
              ) : null}
            </div>

            {/* ── WIRE: live headlines streaming ── */}
            <div style={{ position: 'absolute', top: 300, left: X, right: 72, opacity: oWire, transform: `translateY(${yWire}px)` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 26 }}>
                <span style={{ width: 13, height: 13, borderRadius: '50%', background: LIVE, opacity: livePulse }} />
                <span style={{ fontSize: 28, fontWeight: 800, letterSpacing: 6, color: accent, fontFamily: BODY }}>THE WIRE · {dateLabel}</span>
              </div>
              <div style={{ position: 'relative', height: WINDOW * ROW, overflow: 'hidden' }}>
                <div style={{ transform: `translateY(${conveyorY}px)` }}>
                  {items.map((it, i) => {
                    if (frame < lineStart(i)) return null;
                    const rv = ramp(frame, lineStart(i), lineStart(i) + 8);
                    const fresh = frame < lineStart(i) + 30;
                    const enter = motion === 'kinetic' ? `translateY(${interpolate(rv, [0, 1], [24, 0])}px) scale(${interpolate(rv, [0, 1], [0.8, 1])})`
                      : motion === 'wave' ? `translateX(${interpolate(rv, [0, 1], [-78, 0])}px)`
                      : motion === 'snap' ? `translateY(${interpolate(rv, [0, 1], [12, 0])}px)`
                      : `translateX(${interpolate(rv, [0, 1], [-46, 0])}px) scale(${interpolate(rv, [0, 1], [0.95, 1])})`;
                    return (
                      <div key={i} style={{ height: ROW, opacity: rv, transform: enter, transformOrigin: 'left center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
                          <span style={{ width: 11, height: 11, borderRadius: '50%', background: fresh ? LIVE : DIM, opacity: fresh ? livePulse : 0.45, boxShadow: fresh ? `0 0 ${livePulse * 14}px ${LIVE}` : 'none' }} />
                          <span style={{ fontFamily: MONO, fontSize: 23, fontWeight: 700, letterSpacing: 2, color: accent }}>{it.src}</span>
                          <span style={{ fontFamily: MONO, fontSize: 21, color: DIM, letterSpacing: 1 }}>{ats(i)}</span>
                          {fresh ? <span style={{ fontFamily: MONO, fontSize: 19, color: LIVE, letterSpacing: 1, opacity: livePulse }}>● LIVE</span> : null}
                        </div>
                        {/* : auto-fit wire row — shrinks to fit one line (kills the "...tr..." ellipsis) */}
                        <div style={{ borderLeft: `3px solid ${accent}`, paddingLeft: 20, boxShadow: fresh ? `-4px 0 ${livePulse * 22}px ${accent}66` : 'none' }}>
                          <FitText text={it.text} width={868} maxFontSize={37} minFontSize={22} maxLines={1}
                            fontFamily={BODY} fontWeight={800} letterSpacing="-1px" lineHeight={1.0}
                            style={{ color: PAPER, whiteSpace: 'nowrap' }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: 50, background: `linear-gradient(180deg, ${INK}, transparent)`, pointerEvents: 'none' }} />
                <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 60, background: `linear-gradient(0deg, ${INK}, transparent)`, pointerEvents: 'none' }} />
              </div>
            </div>

            {/* ── CTA ── */}
            <div style={{ position: 'absolute', bottom: 250, left: X, right: 72, opacity: oCta, transform: `translateY(${yCta}px)` }}>
              <div style={{ fontSize: 40, fontWeight: 800, color: PAPER, lineHeight: 1.18, letterSpacing: -1, marginBottom: 36, maxWidth: 860 }}>The whole AI world moved today. Don’t fall behind.</div>
              <div style={{ display: 'inline-flex', flexDirection: 'column', gap: 10, border: `2px solid ${accent}`, borderRadius: 4, padding: '30px 40px', boxShadow: `0 0 40px ${accent}22` }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16, color: PAPER, fontSize: 44, fontWeight: 800 }}>
                  {ctaVerb} <span style={{ color: accent, fontFamily: MONO, fontWeight: 700 }}>{cta}</span>
                </div>
                <div style={{ color: DIM, fontSize: 28, fontFamily: BODY, fontWeight: 600 }}>{ctaLine} <span style={{ display: 'inline-block', transform: `translateX(${Math.sin(frame / 7) * 6}px)`, color: accent }}>→</span></div>
              </div>
            </div>
          </div>
        </div>
      </AbsoluteFill>

      {/* flat overlays */}
      <AbsoluteFill style={{ background: 'radial-gradient(120% 90% at 38% 30%, transparent 46%, rgba(0,0,0,0.52) 100%)', pointerEvents: 'none' }} />
      <AbsoluteFill style={{ backgroundImage: GRAIN, backgroundSize: '200px 200px', mixBlendMode: 'overlay', opacity: 0.05, pointerEvents: 'none' }} />
      <div style={{ position: 'absolute', top: 40, left: 56, right: 56, height: 4, background: 'rgba(255,255,255,0.1)', overflow: 'hidden' }}>
        <div style={{ width: `${progress * 100}%`, height: '100%', background: accent }} />
      </div>
      <div style={{ position: 'absolute', top: 78, left: 60, fontSize: 26, letterSpacing: 7, fontWeight: 700, color: DIM, fontFamily: BODY, opacity: interpolate(frame, [6, 20], [0, 1], clamp) }}>PULSE · AI NEWS</div>
      <div style={{ position: 'absolute', bottom: 60, right: 60, display: 'flex', alignItems: 'center', gap: 10, opacity: ramp(frame, 12, 28) }}>
        <span style={{ width: 11, height: 11, borderRadius: '50%', background: LIVE, opacity: livePulse }} />
        <span style={{ fontFamily: MONO, fontSize: 26, fontWeight: 700, color: LIVE, letterSpacing: 2 }}>LIVE</span>
      </div>
      <div style={{ position: 'absolute', bottom: 60, left: 60, fontFamily: MONO, fontSize: 22, color: DIM, letterSpacing: 2, opacity: 0.6 }}>@yourhandle</div>
    </AbsoluteFill>
  );
};

export const StoryNews: React.FC<StoryNewsProps> = (props) => {
  const samples = props.mbSamples ?? 8;
  const { fps: capFps } = useVideoConfig();
  const fr = (s?: number) => Math.round((s ?? 0) * capFps);
  const capAccent = props.accent || BRAND_A;
  return (
    <AbsoluteFill style={{ backgroundColor: INK }}>
      {/* : sectioned VO placed at the matching visual beats (60fps frames) so the narration tracks the screen.
           (the creator 2026-06-14: "two voice overs happening at the same time near the end of the 4 seconds"):
          each Sequence had a start frame but NO length cap and each <Audio> had no endAt — so an over-long TTS
          section (the wire VO ~9.4s) kept narrating past its slot and overlapped the next section's VO (the CTA),
          producing 2 simultaneous voices at the end EVERY day. Bound each Sequence to its beat window (so it can't
          bleed into the next) AND hard-trim the <Audio> via endAt. Windows: intro 150→446, wire 446→836,
          cta 836→960 (the 960f/16s comp boundary). This is TTS-length-proof: no section can ever overlap another. */}
      {props.voIntro ? <Sequence from={150} durationInFrames={296}><Audio src={staticFile(props.voIntro)} endAt={296} /></Sequence> : null}
      {props.voWire ? <Sequence from={446} durationInFrames={390}><Audio src={staticFile(props.voWire)} endAt={390} /></Sequence> : null}
      {props.voCta ? <Sequence from={836} durationInFrames={124}><Audio src={staticFile(props.voCta)} endAt={124} /></Sequence> : null}
      {props.voSrc ? <Audio src={staticFile(props.voSrc)} /> : null}
      <CameraMotionBlur samples={samples} shutterAngle={180}>
        <Scene {...props} />
      </CameraMotionBlur>
      {/* : word-level kinetic captions on top, each clipped to its VO window (synced + auto-trimmed with the audio) */}
      {props.voIntroText ? <Sequence from={150} durationInFrames={296}><KineticCaptions text={props.voIntroText} audioDurFrames={fr(props.voIntroDurS) || 296} fps={capFps} accent={capAccent} bottom={620} /></Sequence> : null}
      {props.voWireText ? <Sequence from={446} durationInFrames={390}><KineticCaptions text={props.voWireText} audioDurFrames={fr(props.voWireDurS) || 390} fps={capFps} accent={capAccent} bottom={620} /></Sequence> : null}
      {props.voCtaText ? <Sequence from={836} durationInFrames={124}><KineticCaptions text={props.voCtaText} audioDurFrames={fr(props.voCtaDurS) || 124} fps={capFps} accent={capAccent} bottom={620} /></Sequence> : null}
    </AbsoluteFill>
  );
};
