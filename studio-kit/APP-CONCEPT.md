# 🪟 The App Concept — "Studio" (one window, drop-and-go)

This is the most user-friendly shape for the whole stack: **one launcher, one browser window, four big buttons.** It's built on the proven local web-app shell (the virality analyser already runs as a "drop your video" FastAPI app) — extended from *analyze-only* to *analyze + create + export*.

---

## The whole product is one screen

```
┌──────────────────────────────────────────────────────────────┐
│  STUDIO                                          ● running     │
│ ┌──────────────────────────────────────────────────────────┐ │
│ │                                                          │ │
│ │            ⬇  Drop a video here                          │ │
│ │            (or pick a template to start fresh)           │ │
│ │                                                          │ │
│ └──────────────────────────────────────────────────────────┘ │
│                                                              │
│   [ 📊 Score ]  [ ✨ Dress ]  [ 🎙 Voice ]  [ 💬 Caption ]   │
│                                                              │
│   ── attention curve ─────────────────────────────────────  │
│   100 ┤█                                                     │
│    50 ┤█  █                                                  │
│     0 ┤█  █  █          ⚠ weak moment @ 0:02 — tighten cut   │
│       └────────────────────────────────────────────         │
│                                                              │
│                                   [ ⬇ Export finished reel ] │
└──────────────────────────────────────────────────────────────┘
```

That's the entire interface. No menus to learn.

---

## What each button does

- **📊 Score** — runs the virality scorer, draws the second-by-second attention curve, and lists the weak moments with one-line fixes. *(First use: a friendly "Get the free scorer" button installs the model — see LICENSES.md.)*
- **✨ Dress** — generates a custom AI motion-graphics intro (pick a style: neural net, cortex, signal flow) and prepends it.
- **🎙 Voice** — paste a script → generates a free local voiceover → lays it under the video.
- **💬 Caption** — auto-transcribes and burns in word-timed captions.
- **⬇ Export** — renders the final MP4 to `output/`.

---

## Why this is the right concept (the design principles)

1. **One launcher, zero terminal.** Double-click `START-HERE`; the browser opens. The user never sees a command line.
2. **Self-healing first run.** On first launch the app checks for its free engines and installs whatever's missing, with a progress bar — not an error.
3. **Friendly failures.** Anything that can go wrong becomes a button: "Get the free scorer," "Download voice engine," "Open output folder." Never a stack trace.
4. **Drop-first.** The primary action is dragging a file in. Everything else is optional polish.
5. **Local & private by default.** A visible "● running locally — nothing uploaded" badge. Trust is the feature.
6. **Sample in, sample out.** Ships with one example clip and its finished result so the buyer sees the payoff in 60 seconds.

---

## Build status & next steps

| Piece | State |
|---|---|
| Analyze/score web-app shell (FastAPI) | ✅ exists & proven (scored a real clip end-to-end) |
| Voiceover engine | ✅ installed & importing |
| Captions engine | ✅ installed |
| Motion-graphics templates | ✅ rendering (neural net, cortex) |
| **Create + Export tab in the app** | 🔧 to build (wire the existing engines into the analyser shell) |
| **One-click launcher + first-run installer** | 🔧 to build |
| **Sanitized bundle (no weights, no venv, no paths)** | 🔧 to assemble |

The foundation is real and running. What remains is wiring the create/export buttons into the existing window and packaging it as a clean, double-clickable bundle.
