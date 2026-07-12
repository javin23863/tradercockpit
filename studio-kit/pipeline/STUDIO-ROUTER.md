# 🧭 The Studio Router — the brain that sends every brief down the right lane

This studio is not one tool. It's several complementary engines plus a shared skill library, and **the router is what maps a request to the right combination.** Read the intent → route it to the engine(s) and skills that fit → and when a video needs more than one, make them cooperate. This is real-time, per-request intelligence, not a fixed running order.

The rule underneath everything: **every skill benefits every engine, and every engine feeds the next.** A lighting rule learned from a reference clip sharpens a cloud photoreal prompt *and* a local motion-graphics backdrop *and* a Remotion title card. That's why routing is a decision, not a recipe.

---

## ♻️ THE FLYWHEEL — why the whole studio gets better the more you use it

The parts don't just sit next to each other; they feed each other in a loop. Each turn makes the shared skill library sharper, and a sharper library lifts **every** lane at once.

```
        ┌──────────────────────────────────────────────────────────────┐
        │                                                              │
        ▼                                                              │
  ① LEARN            ② AUTHOR              ③ RENDER          ④ CRITIQUE  │  ⑤ IMPROVE
  digest a ref  ─►   fill every gap   ─►   make the pixels ─► grade it  ─► prescribe the fix
  video into        from the skills                          before &     and feed it back
  craft skills                                               after render
```

1. **LEARN — compound craft from real references.** Point `generators/build-video-skills.cjs` at a transcript of a good video. It separates that video into the fixed craft categories and **appends** the new rules into the 15 skill cards in `skills/` — the library *compounds*. The more references you feed it, the sharper the whole studio gets.
   `node generators/build-video-skills.cjs transcript.txt --title="…"`
2. **AUTHOR — the skills auto-fill every generation, cloud and local.** `generators/generate-shot-pack.cjs` loads the whole compounded library + reference playbooks and turns a one-line brief into a production-ready pack — a pro prompt for the **cloud** engines (Higgsfield / Seedance / Kling), or the shot plan you build in the **local** engines (Hyperframes / Remotion). Either way the craft is applied for you.
   `node generators/generate-shot-pack.cjs --concept="…"` (`--character` · `--frames` · `--pic`)
3. **RENDER — the cookbooks orchestrate the end-to-end run.** `cookbooks/ai-film-full-workflow.md` walks the full pipeline (script → style prefix → assets → shot list → generate → assemble), routing each beat to Hyperframes / Remotion / Unreal / a cloud gen and muxing with ffmpeg.
4. **CRITIQUE — grade the cut, $0 first then TribeV2.** `generators/slideshow-risk.cjs` scores the PLAN before you spend a render (catches "slideshow feel" for free); `generators/qa-attention-gate.cjs` scores the FINISHED cut with TribeV2 attention and pulls the exact dipped frames. **Any finished MP4 feeds this same gate** — a Hyperframes render, a Remotion render, or a short cut from the kit's auto-clipper (`clipper/`) — so attention scoring is the one shared critique step every lane funnels into.
5. **IMPROVE — prescribe the fix, then loop.** `generators/diagnose-generation.cjs` names the failure mode (plasticky, drift, weak motion…) and gives the exact prompt fix, each citing a skill. That fix flows back into the next generation — and, when it's a durable lesson, into the skill cards (step ①). The loop closes.

**So "every skill benefits every pipeline" is literal:** one library, authored once from your references, is pulled into whichever lane runs. Feed the flywheel more references and cloud photoreal, local MG, kinetic titles, and QA all improve together.

> **No API key? Every generator still delivers.** With an LLM configured (`LLM_BASE_URL`/`LLM_API_KEY`/`LLM_MODEL`, or `OPENAI_API_KEY`, or a local Ollama — see `generators/llm.cjs`) the authoring/diagnosis steps run automatically. With **no** key they drop to **paste-mode**: they save the fully-assembled pro prompt to `generators/output/` so you can paste it into ChatGPT / Claude / any LLM. The tools always produce value.

---

## 🚦 Routing decision table

| Request | Route to (engine + exact entry) | Skills to pull | Notes |
|---|---|---|---|
| **Photoreal person / product shot** | Cloud AI-gen → `generators/generate-shot-pack.cjs` (default mode) → paste the prompt into Higgsfield / Seedance / Kling | image_generation, realism_detail, prompting, locations, props | Costs credits on the service. Solve variants in image-land, not video-land. |
| **Consistent recurring character** | `generators/generate-shot-pack.cjs --character` (builds a character bible first), then reference it in every shot | characters, consistency_continuity, image_generation, realism_detail | Lock identity/wardrobe once; reuse the bible across the whole video. |
| **Most controllable motion (hero move)** | `generators/generate-shot-pack.cjs --frames` (first-frame / last-frame image-to-video) | camera_movement, transitions_vfx, prompting, consistency_continuity | Two locked frames + only the motion between = predictable result. |
| **Standalone images (sheets, stills)** | `generators/generate-shot-pack.cjs --pic` | image_generation, props, characters, realism_detail | Batch on a gray background, pick the winner. |
| **Abstract tech backdrop / energy animation** | Hyperframes → `generators/html3d-render.cjs --html compositions/<scene>.html …` | idea_concept, transitions_vfx, realism_detail, local_generation | $0, local, total control. Eyeball one still (`--still`) before the full render. |
| **Kinetic titles / synced captions** | Remotion → `generators/remotion/` (`npx remotion studio` / `render`) | hook_structure, prompting, voiceover_audio, local_generation | Pixel-perfect words on the beat. Same template → 100 data-swapped variants. |
| **Data / stats overlay** | Remotion → `generators/remotion/` (data-driven comps via `--props`) | idea_concept, hook_structure, local_generation | Counters/charts that animate from real numbers. |
| **Cinematic photoreal environment** | Unreal → setup in `tool-guides/unreal.md` (drive the editor over its local bridge) | locations, camera_angle, camera_movement, realism_detail | Highest depth/lighting ceiling; real 3D + real cameras. |
| **Voiceover for any lane** | `generators/gen-vo.cjs --in narration.txt --out …` (ElevenLabs) or a local TTS | voiceover_audio | The spine everything else syncs to. |
| **Full narrated reel (multi-shot)** | Cookbook → `cookbooks/ai-film-full-workflow.md` (routes each beat + assembles with ffmpeg) | ALL — the checklist is walked end to end | Cloud hero shots + local MG/titles, cut to the VO. |
| **Score a cut before posting** | `generators/slideshow-risk.cjs <plan>` ($0, pre-render) → `generators/qa-attention-gate.cjs --video=…` (TribeV2, post-render) | editing_iteration, hook_structure | Fix the plan for free first; then grade the finished cut and fix the dipped seconds. |
| **A shot missed — why + fix** | `generators/diagnose-generation.cjs --issue="…" [--prompt="…"]` | realism_detail, prompting, consistency_continuity, camera_angle | Names the slop category and gives the exact ADD/REMOVE prompt fix. |
| **Backgrounds / props / HDRIs** | `assets/` sample pack + `assets/arsenal-fetch.cjs` (CC0 library) | props, locations, realism_detail | Free CC0 assets to dress Hyperframes / Unreal scenes. |

---

## 🔗 Cooperation patterns — engines complementing each other

**1. The flagship reel — photoreal hero + local polish + QA.**
`generate-shot-pack.cjs` (photoreal hero shots → Higgsfield/Seedance) → `html3d-render.cjs` (a Hyperframes MG title/backdrop, $0) → Remotion (word-by-word captions synced to `gen-vo.cjs`) → `slideshow-risk.cjs` on the plan, then `qa-attention-gate.cjs` on the cut (TribeV2) → **ffmpeg** assembles it all into one finished reel. *Cloud brings realism; local brings the words and the branded moments; QA proves it holds attention.*

**2. Narrated explainer — words-and-numbers first.**
`gen-vo.cjs` (the VO spine) → Whisper times the captions → Remotion renders kinetic type + data overlays on the beat → a Hyperframes backdrop drops behind the title → ffmpeg muxes VO + captions. *No cloud spend; Remotion + Hyperframes + a local voice do the whole job.*

**3. Consistent character mini-story.**
`generate-shot-pack.cjs --character` (build the bible) → `--frames` per beat (first/last-frame image-to-video for controlled motion) → any dropped shot goes to `diagnose-generation.cjs` for the exact fix → re-generate → assemble. *One locked identity carried across every shot; the diagnosis loop protects consistency.*

**4. Learn-then-make (feed the flywheel).**
Drop a great reference video's transcript into `build-video-skills.cjs` → the skill cards compound → immediately run `generate-shot-pack.cjs` on your concept and watch the new craft show up in the prompt → render → `qa-attention-gate.cjs`. *Every reference you digest makes the next generation sharper.*

---

## 🧠 How to think about routing — the quick heuristic

- **Photoreal human / product / place?** → Cloud AI-gen (`generate-shot-pack.cjs`).
- **Abstract, tech, energy, "AI-looking" backdrop or logo moment?** → Hyperframes (`html3d-render.cjs`).
- **Text, captions, counters, or a hundred data-swapped variants?** → Remotion.
- **Needs real 3D depth + real cinematic lighting?** → Unreal.
- **Narrated?** → make the voiceover first (`gen-vo.cjs`); it's the spine everything syncs to.
- **More than one of the above?** → it's a cooperation pattern: cloud for realism, local for words + branded moments, ffmpeg to assemble.
- **Before you render:** run `slideshow-risk.cjs` on the plan (it's free). **After you render:** run `qa-attention-gate.cjs` (TribeV2). **When a shot misses:** `diagnose-generation.cjs`.
- **When in doubt about the look:** don't guess — digest a reference with `build-video-skills.cjs` and let the skills carry it.

---

**This router is the brain.** Tell it what you want; it sends the work down the right lane(s) with the right skills — or makes them cooperate — and every pass compounds the craft library so the next brief comes out sharper. New here? Start at `00-START-HERE.md`, then run your first render from `tool-guides/hyperframes.md`.
