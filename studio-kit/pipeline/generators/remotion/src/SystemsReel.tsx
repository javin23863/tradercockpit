import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  useCurrentFrame,
  interpolate,
} from 'remotion';

const SLIDE_DURATION = 105;

const FadeIn: React.FC<{children: React.ReactNode; delay?: number}> = ({children, delay = 0}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame - delay, [0, 15], [0, 1], {extrapolateRight: 'clamp'});
  const y = interpolate(frame - delay, [0, 15], [20, 0], {extrapolateRight: 'clamp'});
  return <div style={{opacity, transform: `translateY(${y}px)`}}>{children}</div>;
};

const base: React.CSSProperties = {
  background: '#0a0a0a',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  fontFamily: "'Segoe UI', sans-serif",
  padding: 60,
  textAlign: 'center',
};

const Slide1 = () => (
  <AbsoluteFill style={base}>
    <FadeIn>
      <div style={{fontSize: 48, fontWeight: 'bold', color: '#fff', lineHeight: 1.3}}>
        Stop building<br/>
        AI <span style={{color: '#ff4444', textDecoration: 'line-through'}}>products</span>.
      </div>
    </FadeIn>
    <FadeIn delay={20}>
      <div style={{fontSize: 48, fontWeight: 'bold', color: '#00ff88', marginTop: 15}}>
        Build AI systems.
      </div>
    </FadeIn>
    <FadeIn delay={35}>
      <div style={{fontSize: 28, color: '#888', marginTop: 20}}>
        There's a $50K/month difference.
      </div>
    </FadeIn>
    <div style={{position: 'absolute', bottom: 40, color: '#333', fontSize: 20}}>@yourhandle</div>
  </AbsoluteFill>
);

const CompareRow: React.FC<{product: string; system: string; delay: number}> = ({product, system, delay}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame - delay, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <div style={{opacity, display: 'flex', width: '90%', marginBottom: 8}}>
      <div style={{flex: 1, padding: '12px 16px', background: '#1a0a0a', borderRadius: '8px 0 0 8px', borderLeft: '3px solid #ff4444'}}>
        <span style={{fontSize: 18, color: '#ff9999'}}>{product}</span>
      </div>
      <div style={{flex: 1, padding: '12px 16px', background: '#0a1a0a', borderRadius: '0 8px 8px 0', borderRight: '3px solid #00ff88'}}>
        <span style={{fontSize: 18, color: '#aaffaa'}}>{system}</span>
      </div>
    </div>
  );
};

const Slide2 = () => (
  <AbsoluteFill style={{...base, justifyContent: 'flex-start', paddingTop: 180}}>
    <FadeIn>
      <div style={{display: 'flex', width: '90%', marginBottom: 15}}>
        <div style={{flex: 1, fontSize: 20, color: '#ff4444', fontWeight: 'bold', textAlign: 'center'}}>PRODUCT</div>
        <div style={{flex: 1, fontSize: 20, color: '#00ff88', fontWeight: 'bold', textAlign: 'center'}}>SYSTEM</div>
      </div>
    </FadeIn>
    <CompareRow product="One chatbot" system="Agent fleet" delay={8} />
    <CompareRow product="Sells once" system="Compounds" delay={16} />
    <CompareRow product="Needs marketing" system="IS the marketing" delay={24} />
    <CompareRow product="$500 project" system="$5K/mo retainer" delay={32} />
    <CompareRow product="Client says 'done'" system="Client says 'more'" delay={40} />
    <CompareRow product="You work for them" system="System works for them" delay={48} />
    <div style={{position: 'absolute', bottom: 40, color: '#333', fontSize: 20}}>@yourhandle</div>
  </AbsoluteFill>
);

const Slide3 = () => (
  <AbsoluteFill style={base}>
    <FadeIn>
      <div style={{fontSize: 36, fontWeight: 'bold', color: '#fff', marginBottom: 25}}>My system right now:</div>
    </FadeIn>
    <FadeIn delay={10}>
      <div style={{
        background: '#0d0d0d', border: '1px solid #333', borderRadius: 12, padding: 25,
        fontFamily: 'monospace', fontSize: 20, textAlign: 'left', width: '90%', color: '#00ff88', lineHeight: 2,
      }}>
        Auto-poster → runs 24/7 on $3.50 server<br/>
        Competitor scraper → 10 profiles daily<br/>
        Content generator → 20 scripts from data<br/>
        Email sequence → 3 emails auto-send<br/>
        Landing page → captures emails<br/>
        LangSmith → measures my AI's behavior<br/>
        Total cost: $38/month
      </div>
    </FadeIn>
    <div style={{position: 'absolute', bottom: 40, color: '#333', fontSize: 20}}>@yourhandle</div>
  </AbsoluteFill>
);

const Slide4 = () => (
  <AbsoluteFill style={base}>
    <FadeIn>
      <div style={{fontSize: 42, fontWeight: 'bold', color: '#00ff88', lineHeight: 1.4}}>
        The system produces content.<br/>
        The content proves the system works.<br/>
        The proof sells the system.
      </div>
    </FadeIn>
    <FadeIn delay={25}>
      <div style={{fontSize: 26, color: '#888', marginTop: 25}}>That's a flywheel. Not a product.</div>
    </FadeIn>
    <div style={{position: 'absolute', bottom: 40, color: '#333', fontSize: 20}}>@yourhandle</div>
  </AbsoluteFill>
);

const Slide5 = () => (
  <AbsoluteFill style={base}>
    <FadeIn>
      <div style={{fontSize: 44, fontWeight: 'bold', color: '#fff', lineHeight: 1.3}}>
        Most AI tools are toys.<br/>
        <span style={{color: '#00ff88'}}>Real power comes from<br/>combining them into systems.</span>
      </div>
    </FadeIn>
    <FadeIn delay={20}>
      <div style={{fontSize: 26, color: '#888', marginTop: 25}}>
        Comment SYSTEM to get the full stack.
      </div>
    </FadeIn>
    <div style={{position: 'absolute', bottom: 40, color: '#333', fontSize: 20}}>@yourhandle</div>
  </AbsoluteFill>
);

export const SystemsReel: React.FC = () => {
  const slides = [Slide1, Slide2, Slide3, Slide4, Slide5];
  return (
    <AbsoluteFill style={{background: '#0a0a0a'}}>
      {slides.map((S, i) => (
        <Sequence key={i} from={i * SLIDE_DURATION} durationInFrames={SLIDE_DURATION}>
          <S />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
