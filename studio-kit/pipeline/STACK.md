# 🎬 Video production stack — master map (read this first, never get lost)

The single navigation map for all video / animation / virality work. Any time the task touches video, start here, then `STUDIO-ROUTER.md` to pick the lane and `STUDIO.md` for the step-by-step process.

## The pipeline in one line
**Brief → study references → build visuals (Hyperframes / Remotion / Unreal / cloud gen) → voiceover → assemble (ffmpeg) → SCORE & improve (slideshow-risk + TribeV2) → output.**

---

## What each tool actually is (plain English)

### 🎨 Visual engines — make the moving pictures
- **Hyperframes** — `pipeline/generators/` — a hand-coded engine: HTML + **Three.js** (3D in a browser) rendered frame-by-frame to MP4 (Puppeteer screenshots → ffmpeg). For bespoke abstract / AI motion graphics (neural nets, particles, energy cores). **$0, local.** Renderer: `generators/html3d-render.cjs`. Scenes: `generators/compositions/*.html`.
- **Remotion** — `pipeline/generators/remotion/` — programmatic video in React. You write components, it renders an MP4. Best for text / captions / data-driven videos and narration where words light up in sync. **$0, local.** (`npx remotion studio` / `render`.)
- **Cloud AI-gen (Higgsfield / Seedance / Kling)** — for photoreal footage the local engines can't hand-code (real people/products/places). Entry: `generators/generate-shot-pack.cjs` builds the pro prompt; you run it on the service. Costs credits.
- **Unreal Engine** — a AAA game/film engine: real 3D worlds, photoreal lighting, cinematic cameras, true depth. Highest detail ceiling. You install it; see `tool-guides/unreal.md`.

### 🎙️ Voice + audio
- **VoxCPM** — the FREE, LOCAL voiceover engine (default). Tokenizer-free TTS, 30 languages, voice cloning, studio quality. Runs on your PC → no per-character cost, no API delay. Setup: `tool-guides/voxcpm.md`.
- **ElevenLabs** — paid cloud TTS, the fallback. Driver: `generators/gen-vo.cjs` (needs `ELEVENLABS_API_KEY`).
- **Whisper** — speech-to-TEXT (the opposite of a TTS). Listens to a video's audio and writes the transcript with word-level timestamps → (1) perfectly-timed captions, (2) aligns the attention curve to what's said each second. Runs locally, free. Setup: `tool-guides/whisper.md`.

### 🧠 Virality / attention analysis — score the video, then improve it
- **slideshow-risk** — `generators/slideshow-risk.cjs` — a $0 deterministic PRE-render scorer. Scores your plan/shot-list across 6 dimensions that predict "slideshow feel" — catch it for free before you spend a render.
- **TribeV2** — a brain-encoding model that predicts second-by-second attention on a FINISHED cut. Three runtimes of the same model (`model/` Python, `rust/` faster, `viral-analyser/` a local web app). You install it; see `tool-guides/tribev2.md`. **License: CC BY-NC 4.0 — non-commercial evaluation only; not sold or bundled.**
- **Watch-and-diagnose (the QA pair)** — the studio extracts the flagged frames and *actually looks*. TribeV2 = the objective score (*where* attention dips); `generators/qa-attention-gate.cjs` + `generators/diagnose-generation.cjs` = the qualitative judgment (*why*, and the exact fix). Loop: render → score → diagnose the dipped seconds → fix → re-score.

### 🔧 Infrastructure — the plumbing it all runs on
- **PyTorch** — the deep-learning framework that runs the local neural models (TribeV2, Whisper, VoxCPM) on CPU or GPU. See `tool-guides/python-torch.md`.
- **ffmpeg** — the universal video swiss-army knife: encodes frames → MP4, muxes voiceover + captions, extracts frames for QA. The assembly step. See `tool-guides/ffmpeg.md`.
- **Puppeteer** — headless Chrome; Hyperframes uses it to screenshot each animation frame (installed via `generators/package.json`).

---

## Where everything lives (so you never hunt)
| Thing | Path |
|---|---|
| Routing brain | `pipeline/STUDIO-ROUTER.md` |
| This map | `pipeline/STACK.md` |
| Studio process (step-by-step) | `pipeline/STUDIO.md` |
| Editing rulebook | `pipeline/MONTAGE-CRAFT.md` |
| Hyperframes renderer + scenes | `pipeline/generators/html3d-render.cjs`, `pipeline/generators/compositions/` |
| Shot-pack / prompt author | `pipeline/generators/generate-shot-pack.cjs` |
| Skill cards + checklist | `pipeline/skills/` (`00-CINEMATIC-CHECKLIST.md`) |
| Reference playbooks | `pipeline/playbooks/` |
| Remotion | `pipeline/generators/remotion/` |
| Voiceover generator | `pipeline/generators/gen-vo.cjs` |
| $0 plan scorer | `pipeline/generators/slideshow-risk.cjs` |
| Attention QA gate | `pipeline/generators/qa-attention-gate.cjs` |
| CC0 asset pack + fetcher | `assets/`, `assets/arsenal-fetch.cjs` |

## Bring your own LLM (or paste-mode)
The authoring tools (`generate-shot-pack`, `build-video-skills`, `diagnose-generation`, `qa-attention-gate`) call `generators/llm.cjs`. Set `LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL`, or `OPENAI_API_KEY`, or run a local Ollama, and they generate automatically. With no key they save a ready-to-paste prompt to `generators/output/` — the tools always produce value.

**Rule: when a video task starts, read `STUDIO-ROUTER.md` + `STUDIO.md` + `MONTAGE-CRAFT.md`. Update this map whenever a tool's setup changes.**
