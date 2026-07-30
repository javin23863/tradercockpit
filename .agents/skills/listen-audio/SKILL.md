---
name: listen-audio
description: Inspect and QA the actual bytes of local audio or video audio tracks with full decoding, signal measurements, offline transcription, waveform and spectrogram review, and a human playback handoff. Use whenever Codex is asked to listen to, hear, transcribe, review, approve, compare, or diagnose narration, dialogue, voice memos, music, mixes, TTS, podcasts, or rendered video audio.
---

# Listen to audio

Never infer audio quality from a script, filename, render log, or declared duration. Run the
bundled listener against the actual delivered file.

## Run

1. Use a Python runtime that imports `faster_whisper`. Probe installed runtimes before installing
   anything. Use a cached Whisper model; never download one implicitly.
2. Resolve FFmpeg from `PATH`, then `<repo>/OpenMontage/.tools/ffmpeg/bin`. Pass `--ffmpeg-dir`
   only when neither is discoverable.
3. For narration, dialogue, voice memos, TTS, or spoken video:

```powershell
python .agents/skills/listen-audio/scripts/listen.py INPUT `
  --out RECEIPT_DIR --speech-required --expected-script SCRIPT `
  --target-lufs -16 --true-peak-ceiling -1.5
```

Omit `--expected-script` and production level limits for an unscripted input memo. Omit
`--speech-required` for music or effects. Use the active production's declared audio limits;
`-16 LUFS` and `-1.5 dBFS` above are the existing OpenMontage narration defaults, not universal
constants.

4. Open `waveform.png` and `spectrogram.png` with the image viewer. Inspect the beginning, middle,
   end, long gaps, abrupt cutoff, empty channels, and visible distortion.
5. Read `listening-receipt.json`. For spoken audio, read the transcript from the receipt and
   compare it with the intended words. Spot-check every reported word difference and implausible
   phrase against the source.
6. Render the actual audio in the app for operator playback when cadence, pronunciation, emotion,
   voice identity, music balance, or subjective sound quality matters.

## Pass contract

- Full-file decode succeeds.
- An audio stream exists.
- Spoken content has a transcript derived from the rendered bytes.
- When an expected script exists, the ending is present and similarity clears the declared floor.
- When production limits are supplied, loudness and true peak are inside them.
- Waveform and spectrogram are inspected.
- The operator hears the playable file before final voice, cadence, or mix approval.

The script's `pass` means the machine checks completed. It never means the voice or mix is
operator-approved.

## Fail closed

- Do not call copied script text a transcript.
- Do not say audio "sounds good" from metrics or ASR alone.
- If decode, required speech recognition, or required comparison fails, stop the approval path.
- Do not install a package, download a model, upload audio, or use paid/cloud transcription
  without separate operator authority.
- Keep external provider cost at `$0`.

Run this skill on every generated narration variant, final narration, audio bed, final mix, and
rendered master before asking for approval. Preserve its receipt with the production artifacts.
