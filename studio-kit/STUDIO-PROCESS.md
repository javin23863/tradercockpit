# 🛠️ The Studio Process — how a pro reel gets made

This is the exact workflow the app automates. You can follow it by clicking buttons, or read it here to understand what's happening under the hood.

---

## The pipeline in one line

**Brief → (optional: study a reference) → build the visuals → add the voiceover → assemble → score & improve → export.**

---

## Step 1 — Brief

Decide the one idea the video sells and who it's for. Write a short script (3–6 lines). The clearer the line, the cleaner everything downstream.

## Step 2 — (Optional) Learn from a reference

If you have a video whose style you love, drop it in the `references/` folder. The app pulls still frames so you can match its palette, pacing, and energy. Replicate what works; don't copy blindly.

## Step 3 — Build the visuals

Pick a motion-graphics template (a glowing neural net, a dense neural cortex) or generate a fresh one. The engine renders it to video frame-by-frame, with depth, controlled glow (bloom), and film grain — the details that make it read as real motion design instead of a flat preset.

**The detail rule that makes or breaks it:** detail = *many small, sharp, glowing elements layered in depth* — not a few big, soft, smooth blobs. Fog + depth-of-field + controlled bloom + grain + a moving camera. That's the difference between "AI video" and "screensaver."

## Step 4 — Add the voiceover

Paste your script. The voiceover engine generates a natural narration on your machine, free. Regenerate as many times as you like until the read is right.

## Step 5 — Assemble

The app stitches animation + voiceover + captions into one MP4. Captions are auto-timed to the voice down to the word.

## Step 6 — Score & improve (optional add-on)

Run the virality scorer. It returns a second-by-second attention curve and flags the weak moments. Watch those exact seconds, fix them (tighten the cut, change the line, add motion), and re-score. Quantitative (the curve says *where*) + your own eye (you decide *why* and *how to fix*) — together, neither alone.

## Step 7 — Export

Export the finished reel to the `output/` folder. Post it.

---

## The improvement loop (this is the secret)

```
render → score → scorer flags weak seconds → watch those frames →
diagnose + fix → re-score → repeat until the curve holds.
```

A video isn't "done" when it's assembled. It's done when the attention curve stops dipping. That loop is what separates a reel that holds viewers from one that loses them at second 3.
