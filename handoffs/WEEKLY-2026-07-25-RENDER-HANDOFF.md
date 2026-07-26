# Handoff — weekly-2026-07-25 render, off-MSI on a rented GPU — 2026-07-26

> STATUS: **master built, one gate legitimately BLOCKs.** The video is rendered and the
> narration is done. `audio_layer_gate` blocks because this cut has no SFX, and passing it
> is an operator decision the gate exists to force. Nothing has been published.

## Why the render moved off the MSI

`render-weekly-recap` run `30185564087` died at 33m40s in the Chatterbox step — not on the
GPU, on host RAM:

```
numpy.core._exceptions._ArrayMemoryError: Unable to allocate 7.15 MiB
for an array with shape (1874401,) and data type float32
```

A 7 MiB allocation failing means the MSI's system RAM was exhausted while librosa loaded the
reference wav. It was re-dispatched and held the single `msi-desktop` runner again, with
`ci / fast-suite` for another branch queued behind it for 44 minutes at zero seconds of
execution. That queue-blocking is the case for a job-level timeout on this workflow.

The Linux box has no GPU. The workflow comment's ~165 h CPU estimate held up: a benchmark
here never finished one chunk in 25 minutes on 16 cores.

## What ran where

Only the CUDA-bound stages went to the rented box. Everything else ran on the Linux box.

| Stage | Box | Result |
|---|---|---|
| narration (Chatterbox) | vast.ai RTX 4060 Ti | 8 sections, 10.8 min, ~8 min wall |
| captions (faster-whisper) | vast.ai RTX 4060 Ti | 449 cues, real word-level alignment |
| claims + style gates | Linux | PASS — 19 claims / 52 receipts; 2 style warns |
| stills → 1080p clips | Linux | 6 clips, `libx264` (no NVENC here) |
| editorial gate | Linux | PASS — 53 beats |
| assemble | Linux | `master.mp4`, 650.2 s, 1920x1080 h264/aac, 36,879,171 B |
| audio layer gate | Linux | **BLOCK** — see below |

Rented instance `45875060`, $0.134/hr, up 1.17 h, **destroyed**. vast.ai credit $3.31 → $2.87.
The Linux box's public key was added to the vast.ai account to reach it.

The master reproduces bit-for-bit across two independent assemble runs:
`sha256 91f5336c288b77a8f0ddcd33cf15428b6447915ea163bf0fae40343321189304`.

## Two defects found

**1. `audio_layer_gate` could never pass — fixed.** It is fail-closed on
`build/audio-layer-receipt.json` and nothing had ever written that file. `git log --all -S`
across every branch finds no producer side. The gate shipped in `b6c0595`, the same commit
that set up this production, and no render has reached the step since, so it has only ever
been able to BLOCK. `stage_assemble` now records what actually reached the mix.

Branch `fix/audio-layer-receipt` (`473f3ed`), pushed, no PR opened. Three tests in
`tests/test_produce.py` pin both halves of the contract — assemble writes the file, and the
keys it writes are the keys `evaluate()` reads, because field-name drift between the two is
how a green gate would start meaning nothing.

**2. The SFX assets are MSI-only — not fixed, not fixable here.**
`OpenMontage/.agents/skills/hyperframes-media/assets/sfx` does not exist anywhere on the
Linux box; a whole-filesystem search found no `whoosh-short.mp3` or `impact-bass-1.mp3`. So
this master carries narration plus a music bed at −40.1 dB and **no section transitions**.
That is exactly the silent degradation the gate was written to catch — `pick_music()` at
least logs when it skips, a missing SFX file does not — and with the receipt now written the
gate names it:

```
[audio-layer] SFX dir absent (.../assets/sfx) - whoosh/impact silently skipped
[audio-layer] BLOCK
```

## The decision waiting on the operator

The gate's own docstring: a reduced audio layer is *"an operator decision, not a pipeline
one"*, declared in `build/audio-layer-override.json`. **That override has deliberately not
been written** — writing it would forge the decision the gate exists to force.

Two ways forward:

1. **Ship this cut without SFX** — write the override, gate passes, master is ready.
2. **Re-mux on the MSI** where the SFX live — `--stage assemble` only, using the narration
   below. No TTS re-run, no GPU rental.

## Artifacts (on the Linux box, not in git — `build/` is gitignored)

`/root/fw-recap/productions/weekly-2026-07-25/build/`, 155 MB, `SHA256SUMS.txt` alongside.

| File | Size | Note |
|---|---|---|
| `master.mp4` | 36.9 MB | the cut under review |
| `vo-01..08.wav`, `vo-full.wav` | 124 MB | the GPU-rented narration — do not regenerate |
| `captions.srt` | 26 KB | faster-whisper, 449 cues |
| `sections.json`, `timeline.json` | 58 KB | |
| `audio-layer-receipt.json` | 253 B | written by the fix above |

`tradercockpit` is a **public** repo, so none of this was uploaded as a release asset. Pull
it over SSH from the MSI instead.

## Caveats

- `pytest` is not installed on the Linux box; the suite ran under `unittest`. 16 tests, the
  3 new ones pass. One pre-existing failure,
  `test_video_04_iran_regime_v2_matches_existing_sections_golden`, reads a gitignored
  `build/sections.json` that only exists on a box that has rendered that production.
  Unrelated to this change.
- Assemble logs `WARN 03-brent-1w.mp4 10.0s < half of 23.1s -> loop restart visible` on the
  longer beats. Harmless here — the clips are static PNGs held for 10 s, so a loop restart
  shows the identical frame. It would matter the moment a beat's visual is real motion.
- The clips were encoded with `libx264 -crf 19` rather than the workflow's
  `h264_nvenc -cq 19`. Different encoder, same source stills.
- `/root/fw-recap` is a detached worktree of `tradercockpit` with an untracked `OpenMontage`
  symlink pointing at the local checkout. Remove the worktree when the artifacts are off the
  box: `git -C /root/tradercockpit worktree remove --force /root/fw-recap`.
