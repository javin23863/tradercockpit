# Practice derivatives — blocked pre-render

Date: 2026-07-20
Status: blocked before the first MP4
External provider cost: $0
Public writes: 0

## Accepted local masters verified

- `productions/video-03-war-premium/build/master-clean.mp4`
  - SHA-256: `3947493ff2b5e9d347408c8082251bd2187454ab307a9ec7e6c4d1de7ca98039`
  - 578.760s, 1920x1080, H.264/AAC
- `productions/video-04-iran-regime-v2/build/master.mp4`
  - SHA-256: `80e0eb7b5eb5b50b0e56bb6a685b3fcbc9086ff3049e37292fc63e150b19b00a`
  - 616.620s, 1920x1080, H.264/AAC
- `productions/video-05-deadline-day/build/master.mp4`
  - SHA-256: `9c32e5c3d83a75799931409954b933d52cb9ef992b4cdcbbbaec1d498d3fbf33`
  - 638.867s, 1920x1080, H.264/AAC

The asserted eight accepted masters were not all present locally. The China master was explicitly
excluded because `publishing-package.json` says it is rejected evidence and must never be used for
derivatives. Historical video-01, video-02, video-02-v4, and weekly master files were absent; no
master was reconstructed or re-rendered.

## Selection receipt

The existing `clip.js --mode ai` selector path was run offline through its bundled
`highlight-select.cjs` regex fallback against each accepted master's existing `captions.srt`.
It produced 16 ranked candidates per master. Eight non-even cuts survived standalone, sentence
boundary, number-plus-named-asset, and prior-cut overlap review:

- War premium: 2 planned — Treasury sanctions tied to Iranian oil; Brent/XLE producer confirmation.
- Iran regime: 3 planned — 57 incidents/selective tape; Brent 10.75% repricing; Brent/XLE/VIX base map.
- Deadline day: 3 planned — TSMC 77.4% rotation hook; General License X oil deadline; TSMC record quarter sold.

Exact timestamps and selection notes remain under `candidates/` so the run can resume without
rescoring.

## Render blocker

Requested settings were locked before the attempt:

- `CLIP_LAYOUT=fit`
- `CLIP_CLEAN_VERTICAL=1`
- existing measured caption style unchanged
- staging output only

Node and the repository's Python venv were available. Global `ffmpeg` and `ffprobe` were absent.
The only repository-local binaries were Remotion's bundled FFmpeg/ffprobe n7.1. The hero render
failed before producing an MP4 because that FFmpeg build has no libass subtitle filter:

```text
Unknown filter 'subtitles'.
```

No already-installed full FFmpeg was found in the accessible global install locations. Installing
one would violate the task's no-new-dependencies constraint, and substituting a different caption
renderer would violate the measured-style requirement.

## Gate results

- Rendered verticals: 0
- `visual_qa.py`: not run; there was no render to inspect
- Visual QA pass/fail: 0 pass / 0 fail
- Caption drafts: 0
- `script_style_gate.py`: not run
- `social-batch/v2`: not created; creating a batch with missing or ungated assets would be invalid
- Published/uploaded/scheduled: nothing

The clipper's temporary transcript/SRT/manifest files from the failed hero attempt were removed.
No accepted master, existing production folder, or `studio-kit/clipper/output` file was changed.
The temporary subtitle-path compatibility edit to `clip.js` was reverted after it proved unrelated
to the missing filter.

## Resume condition

Resume only when a full FFmpeg build with the `subtitles` filter is already available within this
repository or the operator explicitly changes the no-new-dependencies constraint. First rerun the
single Iran hero clip and `tools/visual_qa.py`; continue the remaining seven only after that passes.
