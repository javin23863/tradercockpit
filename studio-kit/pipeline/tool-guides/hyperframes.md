# Hyperframes

**What it is:** Our hand-coded 3D motion-graphics engine — it renders glowing, abstract, "AI-looking" scenes (neural nets, particles, energy cores) into finished video clips, all on your own machine for $0.

## Why it's in the pipeline

When a video needs those signature animated backdrops — the glowing neural-net swirl, drifting particles, the abstract sense of "intelligence happening" — Hyperframes makes them. Instead of paying a stock site or an AI service per clip, we *build* the scene in code and render it ourselves. That means total control over the look, no per-clip fees, and no waiting on an outside service. It's the part of the studio that produces the high-end, branded "tech magic" moments.

## Where it lives

It's in the kit's generators folder:

```
pipeline/generators/
```

Inside that folder: `html3d-render.cjs` is the renderer (the thing that turns a scene into a video), and `compositions/*.html` are the individual scenes (e.g. `itm-3-ignite.html`, `ai-neural-net.html`, `crystal-core.html`). Each scene is a small web page that draws itself in 3D; the renderer photographs it one frame at a time and stitches those frames into an MP4.

## How to use it

First (once per machine), install the generator dependencies:

```
cd pipeline/generators && npm install
```

This pulls **puppeteer** (the headless browser the renderer photographs frames with) and **minimist** (used by the voiceover tool). Then, from inside `pipeline/generators/`, render a 5-second vertical (1080×1920) clip at 30fps:

```
node html3d-render.cjs --html compositions/itm-3-ignite.html --out out.mp4 --fps 30 --dur 5 --w 1080 --h 1920
```

Want to eyeball the look before committing to a full render? Grab a single still frame instead:

```
node html3d-render.cjs --html compositions/itm-3-ignite.html --still 90 --stillout f.png
```

Open `f.png`, confirm it looks right, then run the full clip.

---

**Complements:** Hyperframes makes the abstract MG backdrops; pair it with the editor/compositor that lays voiceover, text, and footage over those clips to assemble the finished video.
