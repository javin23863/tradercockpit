# studio-kit ↔ OpenMontage wiring

`studio-kit/` = extracted ai-video-studio-kit (free, redistributable — LICENSES.md
kept; do not bundle the TRIBE v2 scorer weights, install-yourself only,
**non-commercial → internal QA use only, never a paid service**).

## What it adds to our pipeline (division of labor)

| Need | Before | Now |
|---|---|---|
| Long-form → Shorts | manual ffmpeg crop | `studio-kit/clipper/` — whisper transcript → AI/offline highlight pick → subject-following 9:16 reframe → word-burned captions |
| 3D motion-graphic B-roll | OpenMontage HyperFrames (write your own) | 20+ ready compositions (`pipeline/generators/compositions/*.html`: neural-genesis, data-corridor, crystal-core, sdf-mandelbulb, text-hero…) rendered by `html3d-render.cjs` — self-contained three.js, $0 |
| Kinetic captions / data reels | Remotion from scratch | `pipeline/generators/remotion/` template library incl. `KineticCaptions.tsx`, Story*/Reel* comps |
| Editing craft | tribal knowledge | `EDITING-CRAFT.md` + `pipeline/MONTAGE-CRAFT.md` + 15 skill cards (`pipeline/skills/`) — READ BEFORE CUTTING |
| Brief → shot plan | ad hoc | `generate-shot-pack.cjs` (LLM optional; saves paste-ready prompt without key) |
| Retention QA | none | `qa-attention-gate.cjs` + TRIBE v2 (install-yourself; internal QA only) + `slideshow-risk.cjs` ($0 pre-render grade) |

## Video #1 concrete usage

1. Concept cards (beat 6, 10 strategies): `text-hero.html` / `data-corridor.html`
   variants recolored to HUD palette (#08030a / #FF1744) via `html3d-render.cjs`.
2. Odometer cold-open B-roll: Remotion (`CostReel.tsx` pattern) or composition.
3. A-roll cut rhythm: apply `MONTAGE-CRAFT.md` + `00-CINEMATIC-CHECKLIST.md` gate.
4. Shorts: feed finished 16:9 master to `clipper/` (`node clip.js --mode ai --reframe`,
   offline hook-detector works without any key) → 9:16 cuts for `publish.py`.
5. Optional: `qa-attention-gate.cjs` on the cut before upload (internal QA).

## Setup (deferred to first use — heavy npm pulls)

- `cd studio-kit/clipper && npm install && node check-deps.js` (ffmpeg/yt-dlp/whisper — all already on box or in OpenMontage venv)
- `cd studio-kit/pipeline/generators && npm install` (puppeteer ~300 MB — first render only)
- LLM for authoring/highlight-pick: optional; point `LLM_BASE_URL` at local Ollama or leave unset (offline fallbacks run)
- `assets/samples/` is gitignored — re-fetch full CC0 library via `assets/arsenal-fetch.cjs` (Poly Haven)

## Voice note

Kit's VO engine = VoxCPM; our ladder stays Kokoro → Piper (already installed).
Use kit's `gen-vo.cjs` only if VoxCPM quality beats Kokoro for a given read.
