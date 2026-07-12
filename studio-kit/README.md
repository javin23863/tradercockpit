# 🎬 AI Video Studio Kit

**Build your own local AI video studio — and edit like a pro. Free.**
Score videos like a neuroscientist, animate like a motion designer, voice them like a studio — all on your own machine, **completely free**, no per-use cost, nothing uploaded.

This kit is the **complete blueprint** — the exact end-to-end process, a professional editing-craft rulebook, plain-English guides to every free tool, and the one-window app design — **plus a real, runnable auto-clipper** (`clipper/`) that turns any long video into short-form-ready cuts on your own machine. Everything you need to assemble a studio that clips, scores, animates, voices, captions, and exports video locally for $0.

---

## What you can build with it

A fully local pipeline (no subscriptions, no credits, nothing leaves your machine) that takes a raw clip and helps you:

1. **Score it** — a second-by-second "where does attention drop?" curve from a real brain-response model.
2. **Animate it** — glowing, AI-themed **motion-graphics** (neural nets, signal flow, depth) *plus* photoreal cinematic 3D.
3. **Voice it** — a natural **AI voiceover**, generated free on your own machine.
4. **Caption it** — auto-transcribe and burn in **perfectly timed, word-by-word captions**.
5. **Export it** — one finished, higher-retention reel.

---

## How to use this kit

1. Read **`STUDIO-PROCESS.md`** — the step-by-step pipeline (brief → visuals → voice → assemble → score → export).
2. Read **`EDITING-CRAFT.md`** — the pro rulebook that makes every cut look professionally edited (hooks, rhythm, captions, audio, color).
3. Set up the free tools (each is open-source / free; the workflow names them and how they fit).
4. Read **`LICENSES.md`** before any commercial use — one component is free for **non-commercial** use only.

> This free edition is the **blueprint + craft + process + a working auto-clipper** — the knowledge to run the whole studio, plus a real tool (`clipper/`) you can run today. `APP-CONCEPT.md` documents the one-window app design (the roadmap for the full GUI).

---

## What's inside the box

| File | What it is |
|---|---|
| `README.md` | This file — start here. |
| `STUDIO-PROCESS.md` | The exact end-to-end pro workflow, step by step. |
| `EDITING-CRAFT.md` | 🎚️ The pro-editing rulebook — hooks, cut rhythm, word-by-word captions, audio, color, depth. |
| `BENEFITS.md` | Why this approach beats the alternatives — the full feature list. |
| `APP-CONCEPT.md` | The one-window "Studio" app design (the roadmap concept). |
| `LICENSES.md` | Plain-English licensing. **Read this before commercial use.** |
| `templates/` | Notes on the AI motion-graphics scene styles. |
| `pipeline/` | 🎬 **The creation studio** — the generators (shot-pack authoring, the $0 Hyperframes renderer, voiceover, QA scorers), the 15 compounding skill cards, plain-English tool guides, compositions, and the Remotion project. |
| `assets/` | Sample CC0 assets (HDRIs, textures, props) + a fetcher for the full free library. |
| `clipper/` | 🎬 **The runnable auto-clipper** — paste a long video / URL, get short-form-ready cuts. See below. |

> **New here?** Open `pipeline/00-START-HERE.md`, then `pipeline/tool-guides/hyperframes.md` to run your first render.

---

## 🎬 The Auto-Clipper (included — run it today)

Inside `clipper/` is a working, 100%-local short-form clipper. Point it at a long video or a URL and it:

1. **Hears + transcribes** the audio (Whisper) — every word, timed.
2. **Picks the moments** — an AI reads the transcript and selects the genuinely clip-worthy segments (real hooks, payoffs, quotable lines) *with a reason for each*. No API key? A built-in hook-detector still finds them offline.
3. **Reframes to 9:16** — auto-converts landscape into vertical that **follows the subject** (a moving crop), not a dumb center-crop.
4. **Cuts + captions** — trims each moment and burns word-by-word captions.

```bash
cd clipper
node check-deps.js              # one-time: checks ffmpeg / yt-dlp / whisper
node clip.js                    # interactive — paste a URL or file
node clip.js --mode ai --reframe   # AI moment-picking + vertical reframe
```

Zero per-clip fees, nothing uploaded. Optional: set `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` (DeepSeek, OpenAI, Ollama, LM Studio…) to turn on AI moment-selection; without it, the local hook-detector runs.

---

## The engines, in plain English

You never touch these directly — the app drives them — but here's what's under the hood:

- **Motion-graphics engine** — renders custom 3D animations (glowing neural networks, signal pulses, particle depth) frame-by-frame into video. This is the part that makes your intro *look* like AI, not like a stock template.
- **Voiceover engine (VoxCPM)** — turns your script into a natural human-sounding voice, generated free on your own computer. No per-word fees, no API delay.
- **Captions engine (Whisper)** — listens to your audio and writes the transcript *with exact word timing*, so captions land on the beat.
- **Assembly (ffmpeg)** — stitches animation + voice + captions into one clean MP4.
- **Virality scorer (optional add-on)** — predicts how a human brain responds to your video, second by second, so you can see exactly where attention dips and fix it. *(See Licensing — this is a free "install-it-yourself" component, not sold.)*

---

## Licensing — read this (it protects you)

This kit is built from cleanly-licensed tools you are free to use commercially:
**the motion-graphics engine, the voiceover engine (Apache-2.0), the captions engine (MIT), and ffmpeg.**

The **virality scorer** is powered by a **free research model (TRIBE v2)** that is licensed **non-commercial only**. So it is **not sold and not bundled** here. Instead, the app gives you a one-click button to download it *yourself*, directly from its official source, under its own free license — for your own evaluation. Full details and the exact terms are in **`LICENSES.md`**. When in doubt, read that file first.

---

## Requirements

- Windows, macOS, or Linux.
- ~5 GB free disk (for the free engines downloaded on first run).
- That's it. A graphics card makes scoring faster but is **not** required.

---

*Built from a real, in-production video pipeline — not theory. Everything here ships exactly as it runs.*
