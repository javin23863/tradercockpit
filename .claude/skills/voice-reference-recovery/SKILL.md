---
name: voice-reference-recovery
description: "Derive a usable operator voice reference for Chatterbox TTS when productions/_voice/operator-clean.wav is absent — for example on a machine that is not the operator's. Downgraded quality by construction; use only as a fallback and label every render made with it."
---

# Voice reference recovery

`tools/tts_chatterbox.py` clones from `productions/_voice/operator-clean.wav`. That file is
**gitignored**, so any fresh checkout — Lenox, a rented box, a new worktree — has the engine but
no voice. This skill is the fallback when the real reference cannot be copied in.

## The honest ranking

1. **Copy the real `operator-clean.wav`** from the operator's machine. Always prefer this.
2. **Re-record** a clean reference. Better than 3, costs the operator two minutes.
3. **Derive one from our own published narration** (below). Works, but it is a clone of a clone.

Never use anyone else's voice. Never use a third party's audio. Only our own published output.

## Deriving from published narration

```bash
yt-dlp -q -f bestaudio -x --audio-format wav -o op.wav "https://www.youtube.com/watch?v=<OUR_ID>"

ffmpeg -y -ss 300 -t 16 -i op.wav -ac 1 -ar 24000 \
  -af "highpass=f=85,afftdn=nr=10:nf=-28,loudnorm=I=-18:TP=-2:LRA=9" \
  productions/_voice/operator-derived-fallback.wav

python tools/tts_chatterbox.py <production> \
  --operator-ref productions/_voice/operator-derived-fallback.wav
```

**Name it `operator-derived-fallback.wav`, never `operator-clean.wav`.** The canonical filename
must keep meaning "the real reference", or a downgraded clone silently becomes the house voice.

## What to expect, and what it costs

- Our masters carry a **music bed about 21.5 dB under the voice** (`produce.py MUSIC_UNDER_VO_DB`),
  so `silencedetect` finds no gaps and the reference is never fully clean. The high-pass and
  gentle `afftdn` above reduce it; they do not remove it.
- This is **clone-of-a-clone**. Expect drift in timbre and prosody against the real reference.
- Pick the segment from mid-video. Intros and outros carry stings, and the closing CTA is
  read in a different register.

## Rules

- Any master rendered from a derived reference is **labelled as such in its receipt** and is a
  candidate, never an accepted final. The operator decides whether it ships.
- Re-render from the real reference once it is available; do not leave a derived-voice master
  as the published artifact if a real one can be made.
- The operator's standing ruling is *"improve the audio as best as possible, always."* A derived
  reference is a compromise against that ruling and has to be surfaced, not buried.

## Related

`tools/tts_chatterbox.py` (`--operator-ref`, `--apollo-ref`, `--exaggeration`, `--cfg`);
`.claude/skills/x-chart-capture/SKILL.md` for the sibling problem — capturing charts on a
machine that is not the operator's.
