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

Kit's VO engine = VoxCPM; our ladder stays the existing project voice clone when configured,
then Piper (`en_US-lessac-medium`, installed locally).
Use kit's `gen-vo.cjs` only after an approved local quality comparison against that ladder.

## Zero-cost local runtime complements

The repository-local checkouts are installation surfaces, not evidence sources and not public
services. They are gitignored so their dependencies and model files cannot drift into the
TraderCockpit application graph.

| Runtime | Pinned commit | Enabled use | 2026-07-15 verified state |
|---|---|---|---|
| `Open-Generative-AI/` | `7c8df61ef5fe458339af03214d94e859a6a4a273` | Electron + `stable-diffusion.cpp` + DreamShaper 8 only | recursive clone, `npm run setup`, and `npm run build` pass; production audit reports 7 issues (4 moderate, 3 high, 0 critical). Electron launched locally, `sd.cpp` installed, DreamShaper is the only checkpoint, and a coherent 512x512 proof passed with seed `424242`. |
| `OpenMontage/` | `f8d94632ea9bd0057da31904acca1cefecf005dd` | Remotion, HyperFrames, FFmpeg, Piper, open footage; experimental Wan only after a safe smoke | Python 3.11 venv, core/dev requirements, Remotion, HyperFrames 0.7.58, Piper voice, and `yt-dlp` installed. Contract suite: 561 passed, 7 skipped. Piper WAV and a 3.5 MB zero-key Remotion demo rendered successfully. HyperFrames telemetry is disabled. |

Open Generative AI must launch with `OPEN_GENERATIVE_AI_LOCAL_AI_DIR` set to
`Open-Generative-AI/.local-ai` and `NEXT_TELEMETRY_DISABLED=1`. Never enter a provider key or
start its Next.js server as a public service.

DreamShaper receipt: 2,132,625,894 bytes, SHA-256
`879DB523C30D3B9017143D56705015E15A2CB5628762C11D086FED9538ABD7FD`.
The accepted smoke image and JSON provenance live under
`Open-Generative-AI/.local-ai/smoke/`; local CPU inference works but is slow, so Codex image
generation remains the normal interactive default.

Wan 2.1 1.3B is disabled. The official CUDA PyTorch wheel loaded an unsigned `torch_cpu.dll`
that Windows Enterprise App Control rejected under policy
`{0283ac0f-fff1-49ae-ada1-8a933130cad6}` (Code Integrity events 3033/3077). The unusable GPU
packages were removed from the isolated venv and no Wan weights were downloaded. Do not weaken
Windows security policy; use footage, Remotion, HyperFrames, FFmpeg, and Piper instead.

Verification receipts:

```powershell
git -C Open-Generative-AI rev-parse HEAD
git -C OpenMontage rev-parse HEAD
npm --prefix Open-Generative-AI run build
& OpenMontage\.venv\Scripts\python.exe -m pytest OpenMontage\tests
& OpenMontage\.venv\Scripts\python.exe OpenMontage\render_demo.py code-to-screen
```
