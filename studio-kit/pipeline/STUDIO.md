# 🎬 AI video & animation studio — master pipeline

**The single process for ANY video / animation request.** When you want to make a video, animation, or motion graphic — any shape or form — or you have reference videos to learn from, run this process end to end. Home: `pipeline/`.

> North star: AI-niche, detailed, professional motion graphics — learned from real references, not guessed.

## ♻️ The flywheel (why this compounds)
Every stage feeds the next, and each pass sharpens the shared skill library that lifts every engine:

**LEARN** (`generators/build-video-skills.cjs` digests a reference → compounds the `skills/` cards) → **AUTHOR** (`generators/generate-shot-pack.cjs` fills every gap from those skills) → **RENDER** (Hyperframes / Remotion / Unreal / cloud gen, orchestrated by `cookbooks/`) → **CRITIQUE** (`generators/slideshow-risk.cjs` on the plan for $0, then TribeV2 via `generators/qa-attention-gate.cjs` on the cut) → **IMPROVE** (`generators/diagnose-generation.cjs` prescribes the fix, which loops back into the next generation and the skill cards). Feed it more references, the whole studio gets better. Full routing logic: `STUDIO-ROUTER.md`.

> **⭐ CINEMATIC SKILLS GATE — every video:** before generating ANY shot, walk `skills/00-CINEMATIC-CHECKLIST.md` and apply every craft skill — *idea · characters · props · locations · image-generation · consistency · camera angle · camera movement · realism/detail · prompting · transitions/VFX · editing · voiceover · hook · local/cloud generation.* Each skill card **compounds** from every reference you digest (`build-video-skills.cjs <transcript>`). Cinematic quality isn't optional — it's this gate, walked every time, getting sharper as you study more.
>
> **▶ GENERATE from the skills — for EVERY video, pic, first/last frame, and character:**
> ```
> node generators/generate-shot-pack.cjs --concept="..." [--shots=6] [--aspect=9:16] [--realism=ugc|hero]
>   (default)   VIDEO shot pack (text-to-video)
>   --frames    FIRST-FRAME / LAST-FRAME image-to-video (start image + end image + motion prompt)
>   --pic       standalone IMAGE / PICTURE prompts (product shots, character sheets, scene stills)
>   --character build a reusable CHARACTER BIBLE first, then reference it in every shot
> ```
> It LOADS every compounded skill + the reference playbooks and produces the production-ready pack → `generators/output/<slug>.md`. **BINDING RULE:** don't hand-write a raw prompt for any generation — the prompt fed to Higgsfield / Seedance / Kling (or built for the local engines) comes from this generator, so every generation applies the skills. It runs on **your own LLM** (`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL`, `OPENAI_API_KEY`, or a local Ollama via `generators/llm.cjs`) — or, with no key, it saves a ready-to-paste prompt.
>
> **📖 COOKBOOKS (`cookbooks/`) — the ORDER you walk the skills for a whole PIECE.** For any narrative / multi-shot film, walk `cookbooks/ai-film-full-workflow.md` (script → style-prefix → assets → shot list → generate → diagnose → iterate → QA → lock). It encodes the iteration loop where the real quality comes from (batch → skim → diagnose → fix → regenerate-to-lock).

---

## 0. Drop zone (references → replication)
- **Reference videos:** keep a `references/` folder — download good MG/AI videos into it, and note a one-line intent per clip (e.g. "the 0:08 particle-to-logo").
- **What the studio does with each:** extract frames (`ffmpeg -i ref.mp4 -vf fps=2 frame_%03d.png`) → **READ the frames** (viewer seat) → break down palette / element density / motion easing & timing / depth & DOF / post stack (bloom, chromatic aberration, grain) / pacing → write a **replication playbook** to `playbooks/<name>.md` → replicate in the chosen engine → iterate against the reference until it LANDS. (Transcribe the clip and feed it to `build-video-skills.cjs` to also compound the craft into the skill cards.)

## 1. Brief (30 seconds)
topic · AI-niche angle · length · format (9:16 reel / 16:9 / 1:1) · narrated? · vibe/mood · reference(s) if any.

## 2. Tool routing — pick the engine by what the shot needs
| Need | Engine | Entry point | Cost |
|---|---|---|---|
| **Photoreal footage** (real people/products/places) | **Cloud AI-gen** (Higgsfield / Seedance / Kling) | `generators/generate-shot-pack.cjs` → paste the prompt into the service | credits |
| **Cinematic 3D depth, photoreal lit scenes, real geometry** | **Unreal Engine** | setup → `tool-guides/unreal.md` | $0 local (you install UE) |
| **Custom abstract/3D motion graphics** (particles, neural nets), full hand control | **Hyperframes** (Three.js seek-capture) | `generators/html3d-render.cjs` | $0 |
| **Text / data / caption-driven, word-illuminated narration** | **Remotion** (React video) | `generators/remotion/` | $0 |
| **Reference replication** | study frames → playbook → any engine above | `playbooks/` | $0 |

**Default for AI-niche reels:** Hyperframes for the hero motion + Remotion for narrated/caption pieces; Unreal (once installed) for the highest detail/depth ceiling; cloud gen for photoreal.

## 3. Voiceover (if narrated)
`node generators/gen-vo.cjs --in narration.txt --out vo.mp3` → ElevenLabs MP3 (needs `ELEVENLABS_API_KEY`), or use the free local VoxCPM (`tool-guides/voxcpm.md`). The VO is the spine everything syncs to.

## 4. Render
- **Hyperframes:** `node generators/html3d-render.cjs --html generators/compositions/<comp>.html --out out.mp4 --fps 30 --dur <s> --w 1080 --h 1920` (`--still <frame> --stillout f.png` for one frame to LOOK at first).
- **Remotion:** `cd generators/remotion && npx remotion render <CompositionId> out.mp4` (per-word caption comps sync to the VO).
- **Unreal:** drive the editor over its local bridge (build scene → Sequencer → Movie Render Queue).

## 5. Assembly (animation + VO + captions)
ffmpeg muxes the render + VO + timed captions. Caption gotcha: use a **relative font path** (keep a copy named `_capfont.ttf` in the working dir — a Windows drive-colon breaks the filtergraph parser), pass the drawtext chain via `-filter_complex_script`:
```
ffmpeg -y -i anim.mp4 -i vo.mp3 -filter_complex_script captions.txt -map "[v]" -map 1:a -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest out.mp4
```

## 6. Viewer-seat QA (mandatory — never skip)
Extract frames, **READ them**, compare to the reference, iterate until it genuinely lands. A clean still ≠ good motion — spot-check multiple timestamps. Ship nothing unseen. Score the plan for $0 with `generators/slideshow-risk.cjs`, and the finished cut with `generators/qa-attention-gate.cjs` (TribeV2); fix the dipped seconds and re-score.

## 7. Output
Final MP4 → a named output folder. Note the path + what to check.

---

## Detail principles (why early comps look flat)
1. **Detail = MANY small SHARP glowing elements layered in DEPTH** (fog/DOF), NOT a few big soft smooth blobs.
2. Density + depth-of-field + strong-but-controlled bloom + film grain + a cinematic camera move = *perceived* detail.
3. **Study references and replicate the exact** palette, motion easing, and post stack — don't invent from scratch.
4. Sharp tight-core sprites (crisp), thin bright edges, hundreds of traveling pulses > smooth matte surfaces.
5. AI-niche legibility: the visual should READ as AI (neural nets, signal flow, data) — abstract beauty alone isn't on-brand.

## Current scenes (`generators/compositions/`)
Hyperframes comps include `ai-cortex` (dense neural volume), `ai-neural-net` (legible feed-forward net), `crystal-core`, `flux-vortex`, `glass-knot`, `data-corridor`, and the `itm-*` sequence. Renderer: `generators/html3d-render.cjs`.
