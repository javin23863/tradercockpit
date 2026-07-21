# Helios v27 integration gaps

**Status:** accepted as a visual/motion reference package, not as the public site or
downloadable application.

## What this package proves

- `REFERENCE-PARITY.png` is pixel-identical to the supplied 1536 x 1024 Helios v2
  reference (1,572,864 of 1,572,864 pixels match).
- `helios-board.html?fx=0` renders that reference unchanged.
- The v27 receipt verifies deterministic Canvas motion, pause/resume, reduced-motion
  test paths, and a clean browser runtime.

It does **not** prove application behavior. Default parity mode is a fixed image
backplate plus an additive Canvas layer. The pictured Home, Test, Strategies, Live,
Settings, and mobile controls are not interactive product controls.

Local integration verification on 2026-07-18:

- all 10 supplied package files matched their source SHA-256 hashes;
- all 8 inline JavaScript blocks passed Node syntax parsing;
- headless Chrome at 1536 x 1024 produced an `fx=0` frame with zero pixel
  difference from `REFERENCE-PARITY.png`;
- deterministic frames at time 2 and time 8 differed only in the intended graphic
  region (`17,88` through `1510,930`; RGB RMS difference about 1.88/2.15/2.19).

## Three surfaces, three responsibilities

| Surface | Current truth | Missing work |
|---|---|---|
| Public site (`docs/`) | Static GitHub Pages landing; Apollo remains a manifest-gated concept | Port the Helios panel, typography, state, and motion language into the existing semantic, responsive landing without weakening manifest, waitlist, accessibility, or claims gates |
| Visual reference (`design/helios/`) | Exact backplate and deterministic motion laboratory | Finish operator visual tuning: motion placement, amplitude, distinct state grammar, target-device performance, and production reduced-motion behavior |
| Downloadable app (currently `futures/apps/cockpit`, later `trader-cockpit-app`) | Five real destinations and signed-record flow exist in the accepted consumer baseline | Implement selected v27 visual deltas as live semantic UI driven by real state; do not ship the reference backplate as the application |

## Public-site gaps

1. The current landing uses the older Apollo visual system; v27 is not wired into
   `docs/index.html`.
2. The landing must remain responsive. The reference board is fixed at 1536 x 1024
   and its phone views are pictures, not a mobile layout.
3. Meaningful copy and controls must remain semantic DOM content. Canvas/image-only
   presentation is not keyboard- or screen-reader-complete.
4. `product-manifest/v1`, simulated-preview labels, no-performance claims, waitlist
   consent, and reduced-motion behavior must remain fail-closed.
5. Desktop and mobile screenshot receipts plus operator visual acceptance are still
   required before the live Pages deployment.

## Downloadable-app gaps

1. Bind motion and chrome to real application states and signed evidence records;
   the v27 overlay currently has no market, model, voice, retrieval, or execution
   telemetry.
2. Rebuild the five views as functional controls and evidence surfaces rather than
   image regions. Preserve confirmation, authorization, and kill-switch ownership
   outside Apollo.
3. Define the shared visual-state contract for listening, reasoning, retrieving,
   speaking, interrupted, pipeline phase, evidence status, and execution eligibility.
4. Verify resize/DPI behavior, keyboard navigation, screen readers, contrast, and
   production `prefers-reduced-motion` behavior.
5. Meet the motion budget on target customer hardware. The supplied software-rendered
   receipt measured about 18-20 presented fps against a 24 fps target.
6. Finish the separate distribution lane: consumer-repo extraction, customer edition,
   installer/signing, licensing/entitlements, secure local storage, update/rollback,
   crash recovery, and release receipts. These do not belong in this public repository.

## Tracked work

- `growth.landing-helios-parity`: public landing implementation in this repository.
- `consumer.helios-v27-parity-polish`: desktop semantic/motion integration in the
  current consumer source repository; keep Ready until separately dispatched.
- `consumer.repo-boundary-gate`: protects the factory/app seam before the later
  `trader-cockpit-app` extraction.
