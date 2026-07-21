# HELIOS EVIDENCE CORE — Developer Handoff

This package is the **v27 animation-test build** for the Apollo / Helios visual
system. The approved 1536 × 1024 composition remains the visible source of truth,
while a synchronized Canvas 2D layer supplies live filaments, particles, orbital
couriers, probability packets, and voice-state behavior.

The v27 pass specifically repairs the runtime conditions that could make the board
look static even though the canvas bitmap was changing internally.

## 1. Package contents

| File | Purpose | Status |
|---|---|---|
| `helios-board.html` | Canonical reference-locked animated board. Uses `REFERENCE-PARITY.png` beside it. | **Primary deliverable — v27** |
| `helios-animation-test.html` | Standalone test build with the reference image embedded and playback controls enabled. | **Open this first** |
| `REFERENCE-PARITY.png` | Approved 1536 × 1024 source of truth. | Required by canonical board; embedded in test build |
| `helios-core.html` | Standalone procedural hero core. | Supporting prototype |
| `helios-tuner.html` | Procedural shader tuner. | Design tool |
| `FILAMENT-GENESIS.md` | Algorithmic-art philosophy for the procedural core. | Reference |
| `MOTION-PARITY.md` | Motion grammar, controls, and acceptance criteria. | Implementation spec |
| `QA-RESULTS.md` | Syntax, runtime, determinism, and performance checks. | QA record |

There is no package-manager dependency and no build step.

## 2. Test the animation

Extract the zip first, then double-click:

```text
helios/helios-animation-test.html
```

This file is self-contained. It does not depend on a relative image path, web
server, external font, network call, or WebGL support. The test HUD appears in the
bottom-right corner.

Controls:

- **Pause / Play** — stops or resumes the kinetic layer.
- **Reset** — returns the animation clock to zero.
- **0.5× / 1× / 2×** — changes the motion clock.
- **Soft / Parity / High** — changes additive energy intensity.
- **Space** — play or pause.
- **R** — reset.
- **[ / ]** — decrease or increase speed.
- **H** — hide or show the test HUD.

The canonical presentation remains:

```text
helios/helios-board.html
```

## 3. JavaScript/runtime corrections in v27

### Synchronized canvas presentation

The prior overlay requested a `desynchronized` Canvas 2D context. That mode can
update the internal canvas bitmap without reliably presenting the newest frame to
browser screenshots or some compositor paths. v27 uses a normal alpha Canvas 2D
context so every completed draw is committed to the visible composition.

### Reduced-motion test override

Windows and Firefox can advertise `prefers-reduced-motion: reduce` when operating-
system animation effects are disabled. The old runtime treated that signal as a
hard stop, which could freeze the prototype on trading workstations configured for
minimal desktop animation.

Because this is an animation-test artifact, v27 animates by default. Accessibility
paths remain explicitly testable:

```text
helios-board.html?reduced=1
helios-board.html?respectReduced=1
```

- `reduced=1` forces a deterministic still frame.
- `respectReduced=1` follows the operating-system/browser preference.

### Correct query-parameter defaults

The runtime now distinguishes a missing URL parameter from numeric zero. The
previous `Number(null)` pattern could silently resolve absent values to `0`, causing
incorrect default time, speed, intensity, or snapshot values.

### Stable animation clock

The old loop mixed `setTimeout` and `requestAnimationFrame`. v27 uses one
`requestAnimationFrame` scheduler with a target cadence and a frame-time gate. The
motion clock advances by measured delta time, so pause, resume, speed changes, and
visibility changes remain coherent.

### Canvas performance path

The overlay now uses:

- a default **24 fps** target;
- a **0.78 internal render scale** while the approved backplate remains full
  resolution;
- cached radial glow sprites instead of creating a gradient for every moving dot;
- two-pass line glow instead of per-path `shadowBlur` filters.

These changes preserve the fine reference artwork while making the live layer
practical in Firefox, Chromium, and software-rendered QA environments.

## 4. Operating modes

### Reference parity — default

```text
helios-board.html
```

The page displays the exact supplied composition and starts the kinetic overlay.

### Animation controls

```text
helios-board.html?test=1
```

Adds the same test HUD used by `helios-animation-test.html`.

Optional tuning parameters:

```text
helios-board.html?fps=24&speed=1&intensity=1.45&quality=0.78
```

Supported ranges are clamped internally:

| Parameter | Meaning | Default | Range |
|---|---|---:|---:|
| `fps` | Target presentation cadence | 24 | 12–60 |
| `speed` | Motion-clock multiplier | 1.0 | 0.1–4.0 |
| `intensity` | Additive kinetic energy | 1.45 | 0.25–3.0 |
| `quality` | Internal overlay resolution scale | 0.78 | 0.5–1.0 |
| `start` | Initial animation time in seconds | 0 | Any finite value |

### Exact still

```text
helios-board.html?fx=0
```

### Deterministic frame

```text
helios-board.html?snapshot=1&time=12
```

### Native procedural engine

```text
helios-board.html?native=1
```

## 5. Runtime API

```js
window.__pause();
window.__resume();
window.__renderAt({ time: 12, paused: true });
window.__renderParityAt({ time: 12, paused: true });
window.__setView('native');
window.__setView('parity');

window.__heliosMotion.play();
window.__heliosMotion.pause();
window.__heliosMotion.toggle();
window.__heliosMotion.seek(8);
window.__heliosMotion.setSpeed(2);
window.__heliosMotion.setIntensity(2.1);
window.__heliosMotion.status();
```

The page dispatches a `helios:ready` event when the overlay is configured and its
initial frame has been rendered.

## 6. Architecture

### Reference backplate

`#parityBackplate` renders the approved board at exactly 1536 × 1024. The stage
scales uniformly and never independently reflows panel widths, phone positions,
copy, legends, or footer spacing.

### Kinetic overlay

`#parityFx` is a transparent Canvas 2D layer in the same coordinate system. It adds
only graphic-region energy. It does not repaint text or panel chrome.

### Native semantic/procedural layer

The complete DOM/CSS/WebGL board remains beneath the reference composition and is
available through `?native=1`. A null-context proxy prevents the hidden native
engine from failing while parity mode is active.

## 7. Deterministic QA

Recommended capture conditions:

- Chromium, Chrome, or Firefox;
- viewport 1536 × 1024;
- device scale factor 1;
- no browser zoom;
- `snapshot=1&time=12` for deterministic comparisons.

For exact reference comparison:

```text
helios-board.html?snapshot=1&time=12&fx=0
```

## 8. Integration guidance

Recommended location:

```text
repo/
  design/helios/
    helios-board.html
    helios-animation-test.html
    helios-core.html
    helios-tuner.html
    REFERENCE-PARITY.png
    FILAMENT-GENESIS.md
    MOTION-PARITY.md
    QA-RESULTS.md
    HANDOFF.md
```

Recommended branch and commit:

```bash
git checkout -b design/helios-animation-runtime-v27
git add design/helios
git commit -m "fix(design): make Helios parity animation visible and testable"
```

Do not run prettier, minifiers, image recompression, or automated shader rewrites in
the same commit. Review both default parity mode and `?native=1` after any change.

## 9. Known limits

- The parity composition is intentionally fixed to 1536 × 1024 and scales uniformly.
- Visible copy in parity mode comes from the approved backplate; the underlying DOM
  carries semantic prototype structure.
- The kinetic layer is not yet connected to live market, model, voice, retrieval, or
  execution telemetry.
- The test HUD intentionally overlays the bottom-right of the board and is not part
  of normal presentation mode.
