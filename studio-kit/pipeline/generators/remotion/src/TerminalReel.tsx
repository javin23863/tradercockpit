import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  interpolate,
} from 'remotion';

const SLIDE_DURATION = 120;

const base: React.CSSProperties = {
  background: '#1e1e2e',
  display: 'flex',
  flexDirection: 'column',
  fontFamily: "'Courier New', 'JetBrains Mono', monospace",
  padding: 40,
};

const TypeWriter: React.FC<{text: string; speed?: number; color?: string; delay?: number}> = ({
  text, speed = 2, color = '#a6e3a1', delay = 0,
}) => {
  const frame = useCurrentFrame();
  const chars = Math.floor(Math.max(0, (frame - delay) / speed));
  const visible = text.substring(0, chars);
  const showCursor = frame % 30 < 20 && chars < text.length;
  return (
    <span style={{color}}>
      {visible}
      {showCursor && <span style={{color: '#f5c2e7'}}>|</span>}
    </span>
  );
};

const Prompt: React.FC<{children: React.ReactNode; delay?: number}> = ({children, delay = 0}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame - delay, [0, 5], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <div style={{opacity, marginBottom: 8, fontSize: 18, lineHeight: 1.6}}>
      <span style={{color: '#89b4fa'}}>studio</span>
      <span style={{color: '#6c7086'}}>@</span>
      <span style={{color: '#f5c2e7'}}>system</span>
      <span style={{color: '#6c7086'}}> $ </span>
      {children}
    </div>
  );
};

const Output: React.FC<{text: string; color?: string; delay?: number}> = ({text, color = '#cdd6f4', delay = 0}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame - delay, [0, 8], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <div style={{opacity, color, fontSize: 16, marginBottom: 4, paddingLeft: 20, lineHeight: 1.5}}>
      {text}
    </div>
  );
};

// Slide 1: Terminal boot
const Slide1 = () => (
  <AbsoluteFill style={{...base, justifyContent: 'center'}}>
    <div style={{fontSize: 14, color: '#6c7086', marginBottom: 20}}>STUDIO SYSTEM v2.0</div>
    <Prompt><TypeWriter text="cat CLAUDE.md | wc -l" speed={1.5} /></Prompt>
    <Output text="241" color="#a6e3a1" delay={30} />
    <Output text="" delay={35} />
    <Prompt delay={40}><TypeWriter text="cat memory/learnings.md | grep '### L-' | wc -l" speed={1} delay={40} /></Prompt>
    <Output text="16" color="#a6e3a1" delay={75} />
    <Output text="" delay={80} />
    <Prompt delay={85}><TypeWriter text="node scripts/langsmith-observer.mjs stats" speed={1} delay={85} /></Prompt>
    <div style={{position: 'absolute', bottom: 40, left: 40, color: '#45475a', fontSize: 14}}>@yourhandle</div>
  </AbsoluteFill>
);

// Slide 2: Stats output
const Slide2 = () => (
  <AbsoluteFill style={base}>
    <div style={{fontSize: 14, color: '#6c7086', marginBottom: 12}}>SYSTEM BEHAVIORAL STATS</div>
    <div style={{fontSize: 14, color: '#45475a', marginBottom: 16}}>{'='.repeat(40)}</div>
    <Output text="Total actions logged: 150" delay={5} />
    <Output text="Sessions: 6" delay={12} />
    <Output text="" delay={16} />
    <Output text="Action breakdown:" delay={20} />
    <Output text="  Operational:  50 (33%)" color="#89b4fa" delay={28} />
    <Output text="  Exploration:  0 (0%)" color="#6c7086" delay={35} />
    <Output text="  Proactive:    94 (63%)" color="#a6e3a1" delay={42} />
    <Output text="  Failures:     5" color="#f38ba8" delay={49} />
    <Output text="" delay={55} />
    <Output text="Proactive rate: 63% (target: 40%)" color="#a6e3a1" delay={60} />
    <div style={{position: 'absolute', bottom: 40, left: 40, color: '#45475a', fontSize: 14}}>@yourhandle</div>
  </AbsoluteFill>
);

// Slide 3: The rewrite
const Slide3 = () => (
  <AbsoluteFill style={base}>
    <Prompt><TypeWriter text="git diff --stat HEAD~1 CLAUDE.md" speed={1} /></Prompt>
    <Output text="" delay={30} />
    <Output text=" CLAUDE.md | 464 ++++++---------- 241" delay={35} />
    <Output text="" delay={42} />
    <Output text=" 223 deletions(-), 0 insertions(+)" color="#f38ba8" delay={48} />
    <Output text="" delay={55} />
    <Prompt delay={60}><TypeWriter text="# 48% deleted. Only evidence survived." speed={1.5} color="#6c7086" delay={60} /></Prompt>
    <Output text="" delay={90} />
    <Output text="DSPy test: cognitive loop = 0 improvement" color="#f38ba8" delay={95} />
    <Output text="LangSmith: 4 hidden failures found" color="#f38ba8" delay={100} />
    <Output text="Isolation test: memory = identity (proved)" color="#a6e3a1" delay={105} />
    <div style={{position: 'absolute', bottom: 40, left: 40, color: '#45475a', fontSize: 14}}>@yourhandle</div>
  </AbsoluteFill>
);

// Slide 4: CTA
const Slide4 = () => (
  <AbsoluteFill style={{...base, justifyContent: 'center', alignItems: 'center'}}>
    <div style={{fontSize: 28, color: '#a6e3a1', textAlign: 'center', lineHeight: 1.6}}>
      <TypeWriter text="The system doesn't need to be bigger." speed={2} />
    </div>
    <div style={{fontSize: 28, color: '#f5c2e7', textAlign: 'center', lineHeight: 1.6, marginTop: 20}}>
      <TypeWriter text="It needs to be turned on." speed={2} delay={40} />
    </div>
    <div style={{fontSize: 18, color: '#6c7086', textAlign: 'center', marginTop: 40}}>
      <TypeWriter text="Comment STUDIO for the system." speed={1.5} delay={70} color="#89b4fa" />
    </div>
    <div style={{position: 'absolute', bottom: 40, color: '#45475a', fontSize: 14}}>@yourhandle</div>
  </AbsoluteFill>
);

export const TerminalReel: React.FC = () => {
  const slides = [Slide1, Slide2, Slide3, Slide4];
  return (
    <AbsoluteFill style={{background: '#1e1e2e'}}>
      {slides.map((S, i) => (
        <Sequence key={i} from={i * SLIDE_DURATION} durationInFrames={SLIDE_DURATION}>
          <S />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
