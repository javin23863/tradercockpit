# Remotion — Video Built From Code

**What it is:** Remotion makes video out of React code. You describe each scene as a component — text, colors, timing, motion — and Remotion renders it into a finished MP4. No timeline, no mouse-dragging; the video *is* the code.

## Why it's in the pipeline

It's our specialist for the "words and numbers" half of video — the stuff that has to be pixel-perfect and exactly on the beat:

- **Kinetic typography** — headlines and phrases that snap, slide, and scale on cue.
- **Captions** — clean, synced subtitles that match the voiceover.
- **Data-driven overlays** — charts, counters, and stats that animate from real numbers.
- **Narration sync** — words that light up in time with the spoken track.

Because it's code, the same template can spit out a hundred variations (swap the text, swap the data) without re-editing anything by hand. It runs locally and costs **$0** — no render farm, no subscription.

## Where it lives

It's a self-contained Remotion project in the kit:

```
pipeline/generators/remotion/
```

Inside that folder, `src/` holds the reel components — each `.tsx` file is one video template (for example `CostReel.tsx`, `MemoryReel.tsx`, `TerminalReel.tsx`). Think of every file as a reusable, fill-in-the-blanks video. See that folder's `README.md` for the full list.

## How to use it

You run Remotion directly. Once (per machine):

```
cd pipeline/generators/remotion
npm install
```

Then preview any template live and scrub the timeline:

```
npx remotion studio
```

When it looks right, render a composition to an MP4 (the `id` comes from `src/Root.tsx`), passing data for the data-driven ones:

```
npx remotion render CostReel out.mp4
npx remotion render ProductReel out.mp4 --props='{"productName":"Your Product","price":"$XX"}'
```

So a request like *"a 15-second clip where the cost numbers count up while the narration explains them"* becomes a data-driven Remotion reel, rendered to a file, ready to post. You bring the story; it brings the polish.

---

**Complements:** Remotion (kinetic text, captions, data) pairs with **Hyperframes** for abstract 3D backdrops and **Unreal** for photoreal cinematic shots — words from one, atmosphere from the others.
