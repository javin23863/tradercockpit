# TribeV2

**What it is:** Meta's brain-encoding research model that predicts how a human brain responds to a video — attention and engagement, second by second.

## Why it's in the pipeline / what job it does

Most tools help you *make* a cut. TribeV2 tells you whether that cut actually *holds people*. It runs a simulated viewer's brain over your finished video and produces an **engagement curve over time** — so you can see, frame by frame, where attention climbs and where it dips.

That turns "I think the middle drags" into "attention drops at 0:14." You score a finished cut, the model flags the weak moments, you re-edit exactly those seconds — tighten a slow beat, move the payoff earlier, cut the clutter — and re-score to confirm the dip is gone. It's the measuring tape for the edit, not another way to generate footage.

## Setting it up (external install — non-commercial)

TribeV2 is a research model you install yourself, directly from its official source, under its own free license (see the note below). Fetch it from Meta's TRIBE repository and place it in a `tribev2/` folder the studio can find (the QA gate looks for `tribev2/viral-analyser`). It runs on PyTorch (`python-torch.md`).

Inside are three ways to run the same model:

- `model/` — the Python reference version (the official research code)
- `rust/` — a faster build of the same thing
- `viral-analyser/` — a small local web app: upload a video, get back the engagement curve, a weak-moment finder, and plain-English editing recommendations

For everyday use, the `viral-analyser` web app is the front door.

## How to use it

Render your cut, open the `viral-analyser` app, and drop the video in. It hands back the response-over-time curve plus a list of timestamps where attention dips. Click a flagged moment, fix those exact seconds in your edit, then re-upload the new version and watch the curve — the goal is to lift the dips and confirm the fix actually landed. You can also compare 2–4 versions side by side to find the strongest sections across cuts and assemble the best of each.

## License (important)

TribeV2 is **Meta's model under CC BY-NC 4.0 — non-commercial**. It's free to *use* for evaluating your own work, but it is never sold or bundled into anything we charge for. The studio installs it from Meta's official source for the user's own non-commercial use only.

## Complements

Pairs with **Whisper** (lines the attention curve up against what's actually being said each second) and with **Claude-watch** — once TribeV2 flags *where* attention dips, Claude pulls those exact frames and looks at them to tell you *why*.
