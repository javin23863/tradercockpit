# VoxCPM — Free, Local AI Voiceover

**What it is:** A free AI voiceover engine that turns written text into spoken narration, running entirely on your own machine.

## Why it's in the pipeline

Every video needs a voice. VoxCPM is the studio's in-house narrator. It's the open-source OpenBMB 2B text-to-speech model — tokenizer-free, 48kHz studio-quality audio, 30 languages, and it can even clone a voice. Because it runs locally, there's **no per-character cost and no API delay** — you're not paying a cloud service or waiting on the internet for every line. That's the win: it beats ElevenLabs on both price and speed.

ElevenLabs stays in the toolbox as a **paid cloud fallback** (with a cloned voice) for moments you'd rather hand off, but VoxCPM is the default for day-to-day narration.

One honest caveat: here it runs on CPU (no graphics-card acceleration), so it's slower — roughly **3 minutes of processing for ~25 seconds of finished audio**. Fine for batch jobs; just don't expect instant.

## Setting it up (free, local install)

VoxCPM is open-source — you install it once on your machine:

- Get it from its project page: [github.com/OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM).
- Give it its **own** self-contained Python environment (a `.venv`) so it won't clash with anything else — `python -m venv .venv`, activate it, then `pip install` per the project's README. The model weights download from Hugging Face on first run.
- Point the studio at wherever you installed it.

## How to use it

The core is a few lines of Python. Load the model once, then generate audio from text:

```python
from voxcpm import VoxCPM
import soundfile

m = VoxCPM.from_pretrained('openbmb/VoxCPM2', load_denoiser=False)
wav = m.generate(text="...", cfg_value=2.0, inference_timesteps=10)
soundfile.write(out, wav, m.tts_model.sample_rate)
```

**Want a specific vibe?** Steer the voice by prefixing your text with a description in parentheses. For a movie-trailer feel:

> `(a deep cinematic narrator)` Your narration script goes here...

That prefix shapes the delivery; the rest is your actual line.

---

**Complements:** Pairs with the video/animation tools (Remotion, the render stack) — VoxCPM lays down the narration track that gets married to the visuals; ElevenLabs is the paid cloud fallback when you need it.
