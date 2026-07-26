# Chatterbox reference-audio research

Reviewed 2026-07-24 against Resemble AI’s official Chatterbox pages and the official `resemble-ai/chatterbox` repository. This describes current upstream `master`; the installed package must be checked separately because its version may differ.

## Recommendation

Use **one selected, clean reference candidate**, not the full long recording. For original English Chatterbox or Chatterbox Multilingual, target about **8–10 seconds** and put the strongest, most representative uninterrupted speech in the **first 6 seconds**. For Turbo/Nano, use **10–15 seconds**; upstream requires more than 5 seconds and its T3 prompt window is 15 seconds. These choices sit inside Resemble’s documented 5–20-second range while filling the useful conditioning windows. ([Resemble Chatterbox page](https://www.resemble.ai/learn/models/chatterbox), [original source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/tts.py), [multilingual source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/mtl_tts.py), [Turbo source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/tts_turbo.py))

Keep any long recording only as a source pool from which to cut and audition several short candidates. There is no official evidence that feeding progressively longer audio monotonically improves a clone; Resemble showcases five-second cloning, documents 5–20 seconds, and reports evaluations using 7–20-second references. ([Resemble Chatterbox page](https://www.resemble.ai/learn/models/chatterbox))

## What happens to the reference

| Variant | Speech-token/style prompt | S3Gen acoustic prompt | Speaker identity |
|---|---:|---:|---|
| Original English | first 6 s | first 10 s | full resampled clip |
| Multilingual | first 6 s | first 10 s | full resampled clip |
| Turbo/Nano | first 15 s | first 10 s | full resampled clip |

The upstream implementations load the reference at the S3Gen rate, create a 16 kHz copy, explicitly slice the prompt paths to the windows above, but pass the entire 16 kHz copy to the voice encoder. ([original source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/tts.py), [multilingual source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/mtl_tts.py), [Turbo source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/tts_turbo.py))

The voice encoder trims low-energy material at the boundaries, divides the remaining waveform into overlapping partial utterances, then averages and normalizes those partial embeddings. Thus audio beyond 10 seconds can still alter speaker identity, but it no longer adds S3Gen prompt content; beyond 6 seconds in original/multilingual, it also no longer adds T3 prompt content. For Turbo, the T3 path can use up to 15 seconds. This is a direct inference from the official code, not a published quality guarantee. ([voice-encoder source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/models/voice_encoder/voice_encoder.py), [original source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/tts.py), [Turbo source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/tts_turbo.py))

## Reference structure

- Use one speaker only, with no cross-talk. Because the code produces one averaged speaker embedding, multiple voices or strongly changing acoustics would be mixed into that identity representation; this is a code-derived inference. ([voice-encoder source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/models/voice_encoder/voice_encoder.py))
- Start promptly with natural, continuous speech. Put the clearest, most representative timbre, cadence, and delivery first, since the first 6 seconds drive the original/multilingual speech-token prompt and the first 10 seconds drive S3Gen. ([original source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/tts.py), [multilingual source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/mtl_tts.py))
- Keep delivery internally consistent unless the desired output should inherit a conspicuous style. The official README warns that reference language/accent and fast speaking style affect the result; for multilingual work, match the reference clip to the requested language tag. ([official README](https://github.com/resemble-ai/chatterbox#original-chatterbox-tips))
- Prefer a complete phrase with normal phonetic variety over isolated words, laughter, music, breaths, long pauses, or an edited montage. Resemble’s general recording guidance calls for a quiet, acoustically controlled room, minimal external noise, and a good microphone. ([Resemble recording guidance](https://www.resemble.ai/cloned/))

## Acoustic and file format

- Use a clean, dry, unclipped recording with stable distance, level, microphone, and room. Resemble recommends soft acoustics to reduce echo/background noise, sound isolation, a good microphone, at least 44.1 kHz/16-bit capture, and lossless WAV. ([Resemble recording guidance](https://www.resemble.ai/cloned/))
- WAV is the conservative handoff format: the official examples use `.wav`/`reference.wav`. Upstream code resamples internally to its required rates, so a clean 44.1 or 48 kHz source does not need manual pre-resampling merely to match the model. ([official README](https://github.com/resemble-ai/chatterbox#usage), [Resemble quickstart](https://www.resemble.ai/learn/models/chatterbox), [original source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/tts.py))
- Turbo/Nano rejects references of 5 seconds or less and, by default, normalizes reference loudness to `-27 LUFS` before conditioning. The original and multilingual loaders do not apply that Turbo loudness-normalization step. ([Turbo source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/tts_turbo.py), [original source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/tts.py), [multilingual source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/mtl_tts.py))

## Candidate-selection rule

From a long session, cut a few clean candidates at the relevant window length and audition the same test sentence with each. Choose by actual speaker similarity, stability, pronunciation, and pacing. Do not assume the longest candidate wins: after the fixed prompt windows, extra audio affects only the averaged speaker embedding and can introduce more room, noise, or delivery variation. The “can introduce” conclusion is an inference from the averaging implementation; upstream publishes no longer-is-better rule. ([voice-encoder source](https://github.com/resemble-ai/chatterbox/blob/master/src/chatterbox/models/voice_encoder/voice_encoder.py), [Resemble Chatterbox page](https://www.resemble.ai/learn/models/chatterbox))
