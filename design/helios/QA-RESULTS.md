# HELIOS v27 — Animation Runtime QA

## Deliverables under test

- Canonical board: `helios-board.html`
- Standalone test build: `helios-animation-test.html`
- Reference asset: `REFERENCE-PARITY.png`
- Reference geometry: **1536 × 1024**

## Automated checks

| Check | Result |
|---|---|
| Canonical board inline JavaScript syntax | PASS — 3/3 script blocks |
| Standalone test inline JavaScript syntax | PASS — 3/3 script blocks |
| `helios-core.html` inline JavaScript syntax | PASS — 1/1 script block |
| `helios-tuner.html` inline JavaScript syntax | PASS — 1/1 script block |
| Standalone test has no external asset dependency | PASS — reference image embedded |
| Overlay starts when OS reports reduced motion | PASS — test override active |
| Explicit `reduced=1` path | PASS — deterministic still path retained |
| Live canvas changes over elapsed time | PASS |
| Pause holds the exact current frame | PASS |
| Resume advances from the held frame | PASS |
| Same deterministic time produces same canvas hash | PASS |
| Different deterministic times produce different canvas hashes | PASS |
| Test HUD is visible in standalone build | PASS |
| Page errors during runtime test | PASS — none observed |

## Runtime defect corrections verified

### 1. Canvas presentation

The overlay no longer requests a `desynchronized` 2D context. In headless Chromium,
two live screenshots taken approximately 0.9 seconds apart now differ across the
animated graphic regions. The prior compositor path could expose changing canvas
pixels through `getImageData()` while repeatedly presenting an unchanged composed
frame.

### 2. Missing-parameter parsing

Absent `fps`, `speed`, `intensity`, and `time` parameters now use their declared
defaults rather than becoming numeric zero through `Number(null)`.

Verified defaults:

| Setting | Value |
|---|---:|
| Target cadence | 24 fps |
| Motion speed | 1.00× |
| Kinetic intensity | 1.45 |
| Internal overlay scale | 0.78 |
| Snapshot fallback time | 12 seconds |

### 3. Performance

Software-rendered Chromium QA measured approximately **18–20 presented frames per
second** against a 24 fps target at the 0.78 internal render scale. This is a
substantial improvement over the shadow-filter implementation and is sufficient to
verify continuous motion without a discrete frame slideshow.

Performance changes:

- cached glow sprites;
- manual two-pass line glow;
- no per-path `shadowBlur`;
- one `requestAnimationFrame` scheduler;
- delta-time animation clock;
- 0.78 internal overlay scale.

## Determinism assertions

The automated runtime test performed the following sequence:

1. Start live motion while Chromium reports `prefers-reduced-motion: reduce`.
2. Confirm the canvas hash changes after elapsed time.
3. Pause and confirm the hash remains identical.
4. Resume and confirm the hash changes.
5. Render time `2`, then time `8`, then time `2` again.
6. Confirm the two time-`2` hashes match and the time-`8` hash differs.

All assertions passed.

## Reproduction paths

```text
helios-animation-test.html
helios-board.html
helios-board.html?test=1
helios-board.html?snapshot=1&time=12
helios-board.html?reduced=1
helios-board.html?respectReduced=1
helios-board.html?fx=0
helios-board.html?native=1
```
