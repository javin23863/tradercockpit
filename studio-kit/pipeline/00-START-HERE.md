# 🎬 The Studio — start here

This `pipeline/` folder is the creation studio: the generators that author and render, the compounding skill library, plain-English tool guides, and the end-to-end process. Everything you need to take a brief to a finished, higher-retention video lives here.

---

## ♻️ The one idea: a compounding flywheel

Every part of this studio feeds the next, and each turn makes the shared skill library sharper — which lifts **every** engine at once:

**LEARN** → **AUTHOR** → **RENDER** → **CRITIQUE** → **IMPROVE** → (back to LEARN)

1. **LEARN** — `generators/build-video-skills.cjs` digests a reference video's transcript and **compounds** new craft rules into the 15 skill cards in `skills/`.
2. **AUTHOR** — `generators/generate-shot-pack.cjs` loads that whole library and turns a one-line brief into a production-ready pack: a pro prompt for cloud gen (Higgsfield / Seedance / Kling) *or* the plan you build in the local engines.
3. **RENDER** — the `cookbooks/` orchestrate the run across Hyperframes (local 3D MG), Remotion (kinetic text/captions), Unreal (photoreal), assembled with ffmpeg.
4. **CRITIQUE** — `generators/slideshow-risk.cjs` grades the plan for $0 before you render; `generators/qa-attention-gate.cjs` grades the finished cut with TribeV2 attention.
5. **IMPROVE** — `generators/diagnose-generation.cjs` prescribes the exact fix, which loops back into the next generation and the skill cards.

Feed it more references and the whole studio gets better. The full logic — which brief goes to which engine + skills, and how they cooperate — is the **`STUDIO-ROUTER.md`**. Read that next.

---

## 🗺️ What's in here

| Path | What it is |
|---|---|
| **`STUDIO-ROUTER.md`** | 🧭 The routing brain — maps any brief to the right engine(s) + skills, or makes them cooperate. **Read this first.** |
| **`STUDIO.md`** | The step-by-step pro process for making a video, end to end. |
| **`STACK.md`** | The master tool map — what each engine is and where it lives. |
| **`MONTAGE-CRAFT.md`** | The pro-editing rulebook (hooks, cut rhythm, captions, audio, color) — read before cutting any video. |
| **`skills/`** | The 15 compounding craft cards + `skills/00-CINEMATIC-CHECKLIST.md` (the per-video gate). |
| **`tool-guides/`** | A plain-English one-pager per tool (hyperframes, remotion, unreal, voxcpm, whisper, tribev2, ffmpeg, python-torch). |
| **`generators/`** | The runnable tools — shot-pack authoring, the Hyperframes ($0) renderer, local voiceover, the QA attention gate, the diagnosis tool, and the $0 slideshow-risk scorer. |
| **`playbooks/`** | Reference-video breakdowns you build as you study clips. |
| **`cookbooks/`** | End-to-end pipelines that orchestrate the engines for a whole piece. |
| `../assets/` | Sample CC0 assets (HDRIs, textures, props) + a fetcher for the full free library. |

---

## ▶️ Make your first video

1. **Set up the generators** (once): `cd generators && npm install` (pulls puppeteer + minimist). Optional: set `LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL` (or `OPENAI_API_KEY`, or run Ollama) so the authoring tools run automatically — with no key they save a ready-to-paste prompt instead.
2. **Author a shot pack:** `node generators/generate-shot-pack.cjs --concept="a barista making latte art"` → the compounded skills fill every gap into `generators/output/`.
3. **Render something local + free:** open `tool-guides/hyperframes.md` and render a Hyperframes clip, or `tool-guides/remotion.md` for kinetic text.
4. **Voice it** (if narrated): `generators/gen-vo.cjs`. **Assemble** with ffmpeg (`tool-guides/ffmpeg.md`).
5. **Grade it:** `node generators/slideshow-risk.cjs <plan>` before rendering; `node generators/qa-attention-gate.cjs --video=<cut.mp4>` after (needs TribeV2 — see `tool-guides/tribev2.md`).

---

## 🧰 The engines at a glance

- **Hyperframes** — hand-coded 3D motion-graphics (Three.js → MP4), $0 local. `generators/html3d-render.cjs` + `generators/compositions/*.html`. → `tool-guides/hyperframes.md`
- **Remotion** — programmatic video in React (kinetic text, captions, data overlays), $0 local. `generators/remotion/`. → `tool-guides/remotion.md`
- **Unreal Engine** — photoreal cinematic 3D (you install it). → `tool-guides/unreal.md`
- **Voiceover** — a local TTS (VoxCPM) or ElevenLabs (`generators/gen-vo.cjs`). → `tool-guides/voxcpm.md`
- **Whisper** — speech-to-text for perfectly-timed captions. → `tool-guides/whisper.md`
- **TribeV2** — the virality/attention scorer (you install it). → `tool-guides/tribev2.md`
- **ffmpeg** — the assembly step (encode + mux + captions). → `tool-guides/ffmpeg.md`

Supporting tech: **Python / PyTorch** power the local AI models (`tool-guides/python-torch.md`).
