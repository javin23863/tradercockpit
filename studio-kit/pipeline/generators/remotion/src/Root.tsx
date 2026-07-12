import {Composition} from 'remotion';
import {LangSmithReel} from './LangSmithReel';
import {ClaudeMdReel} from './ClaudeMdReel';
import {CostReel} from './CostReel';
import {MemoryReel} from './MemoryReel';
import {SystemsReel} from './SystemsReel';
import {CloneTestReel} from './CloneTestReel';
import {HonestyReel} from './HonestyReel';
import {CompetitorReel} from './CompetitorReel';
import {AutoKillReel} from './AutoKillReel';
import {RulesReel} from './RulesReel';
import {TerminalReel} from './TerminalReel';
import {PortfolioReel} from './PortfolioReel';
import {StoryTipReel} from './StoryTipReel';
import {StoryTipDeep} from './StoryTipDeep';
import {ProductReel} from './ProductReel';
import {StoryOvernight} from './StoryOvernight';
import {StoryNews} from './StoryNews';
import {ShaderTest} from './ShaderTest';
import {StoryCinematic} from './StoryCinematic';
import {AgentReel} from './AgentReel';
import {ShaderMGReel} from './ShaderMGReel';
import {FluxMG} from './FluxMG';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* : CRAFTED motion graphics (custom easing + layered depth + grain/vignette/bloom + choreography), NO text */}
      <Composition
        id="KineticMG"
        component={FluxMG}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
      />
      {/* : REAL motion graphics ($0) — aurora GLSL shader + 3D particle field + glow, NO text */}
      <Composition
        id="ShaderMGReel"
        component={ShaderMGReel}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
      />
      {/* : genuinely-animated reel (kinetic typography + living bg + spring physics) — fixes the boring static-text reels */}
      <Composition
        id="AgentReel"
        component={AgentReel}
        durationInFrames={240}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="ShaderTest"
        component={ShaderTest}
        durationInFrames={120}
        fps={30}
        width={1080}
        height={1920}
      />
      {/* : StoryCinematic — cinematic 3D-depth rebuild. VO IS THE SPINE: comp length =
          measured VO duration + tail (calculateMetadata), so the voiceover can never cut off. */}
      <Composition
        id="StoryCinematic"
        component={StoryCinematic}
        durationInFrames={420}
        fps={30}
        width={1080}
        height={1920}
        calculateMetadata={({props}) => {
          const fps = 30;
          const voDurS = (props as {voDurS?: number}).voDurS;
          return {durationInFrames: voDurS ? Math.ceil((voDurS + 0.8) * fps) : 420, fps};
        }}
        defaultProps={{
          eyebrow: 'AI · RAG',
          accentA: '#8B5CF6',
          accentB: '#22D3EE',
          cta: 'START',
          tipId: 'AI-RAG-001',
        }}
      />
      <Composition
        id="LangSmithReel"
        component={LangSmithReel}
        durationInFrames={840}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="ClaudeMdReel"
        component={ClaudeMdReel}
        durationInFrames={525}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="CostReel"
        component={CostReel}
        durationInFrames={525}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="MemoryReel"
        component={MemoryReel}
        durationInFrames={525}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="SystemsReel"
        component={SystemsReel}
        durationInFrames={525}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="CloneTestReel"
        component={CloneTestReel}
        durationInFrames={600}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="HonestyReel"
        component={HonestyReel}
        durationInFrames={600}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="CompetitorReel"
        component={CompetitorReel}
        durationInFrames={600}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="AutoKillReel"
        component={AutoKillReel}
        durationInFrames={600}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="RulesReel"
        component={RulesReel}
        durationInFrames={420}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="TerminalReel"
        component={TerminalReel}
        durationInFrames={480}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="PortfolioReel"
        component={PortfolioReel}
        durationInFrames={1350}
        fps={30}
        width={1080}
        height={1920}
      />
      {/*  (2026-05-18 cycle 130): 7-second IG Story template. Daily tip
          + product-solution workflow + Reply 'START' CTA. Replaces stale
          carousel-slide PNGs per the creator ask. */}
      <Composition
        id="StoryTipReel"
        component={StoryTipReel}
        durationInFrames={210}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          hook: 'STOP USING ONE MODEL',
          body: ['Route 3 LLMs.', 'Watch costs drop 60 percent.'],
          tipId: 'T001',
          category: 'ai-stack',
        }}
      />
      {/*  (2026-06-02): StoryTipDeep — 10s, dynamic-opacity, high-retention,
          multi-beat teaching story. Rotates across all 7 AI types. Built from
          an internal spec */}
      <Composition
        id="StoryTipDeep"
        component={StoryTipDeep}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          tipId: 'AI-IMAGE-001',
          aiType: 'image' as const,
          hook: 'YOUR STYLE ISN’T RANDOM',
          stat: '1 SREF = 1 BRAND',
          problem: 'Every render looks like a different brand.',
          steps: ['Mint one --sref random', 'Lock that seed everywhere', 'Only change the subject'],
          proof: { kind: 'swatches' as const },
          result: 'One consistent style — every time.',
          cta: 'START',
        }}
      />
      {/* : "THE OVERNIGHT" — editorial concept+visual upgrade (StoryOvernight) */}
      <Composition
        id="StoryOvernight"
        component={StoryOvernight}
        durationInFrames={480}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          tipId: 'AI-NEWS-001',
          hook: 'IT SHIPPED 18 THINGS LAST NIGHT. YOU SLEPT.',
          stat: '24/7 AUTONOMOUS',
          problem: 'You’re asleep at the busywork an agent could run.',
          steps: ['Give it a goal in plain English', 'Wire it to your tools via MCP', 'Let it loop — ship, verify, repeat'],
          proof: { kind: 'counter', from: 0, to: 18, unit: '', prefix: '', note: 'shipped overnight — zero code' },
          result: 'An AI that works the night shift while you sleep.',
          cta: 'START',
          ctaVerb: 'Comment',
        }}
      />
      {/* : LIVE AI-news wire (StoryNews) — repopulated daily with real headlines */}
      <Composition
        id="StoryNews"
        component={StoryNews}
        durationInFrames={960}
        fps={60}
        width={1080}
        height={1920}
      />
      {/*  (2026-06-02): ProductReel — 15s PAIN->SOLUTION direct-response video for a
          yourstore.com digital product. Data from your product data. */}
      <Composition
        id="ProductReel"
        component={ProductReel}
        durationInFrames={450}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          slug: 'your-product',
          productName: 'YOUR PRODUCT',
          price: '$XX',
          accentA: '#F59E0B',
          accentB: '#F97316',
          painHook: 'STARTING AN AI AGENCY?',
          agitate: "You've got nothing to show a client.",
          pains: ['50 tutorials deep — still no system', 'No mockups to pitch with', 'No pages, no outreach, no pipeline'],
          solutionLabel: 'YOUR PRODUCT',
          whatsInside: ['Deliverable one', 'Deliverable two', 'Deliverable three', 'Deliverable four', 'Bonus resource'],
          outcome: 'Launch your agency this week.',
          cta: 'START',
          store: 'yourstore.com',
        }}
      />
    </>
  );
};
