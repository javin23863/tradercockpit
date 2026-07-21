# HELIOS v27 — Reference-Locked Motion Specification

The v27 target is not an approximate recreation of the approved board. It is the
approved board itself, with a restrained live-energy layer that makes the image
behave like a running interface.

## 1. Non-negotiable visual contract

The following must remain pixel-locked to `REFERENCE-PARITY.png` in default mode:

- panel dimensions, radii, spacing, and border treatment;
- all visible wording, capitalization, labels, and hierarchy;
- the five desktop tabs, two phone mockups, five motion studies, and footer;
- the detailed orange filament network and violet/blue conductance channel;
- graph-node placement, orbital paths, legends, chips, and navigation;
- the relative scale of every core and motion-study element.

Animation may add light. It may not redraw, recolor, displace, blur, or obscure the
approved chrome and typography.

## 2. Global motion rules

1. **Reference first.** Static fidelity comes from the approved backplate; the
   kinetic layer is transparent and additive.
2. **Energy follows structure.** Every animated point or line belongs to a filament,
   prominence, particle path, orbital rail, wavefront, or probability trajectory.
3. **No synchronized wobble.** Surface currents, particles, shells, wavefronts,
   packets, prominences, and graph couriers run at different incommensurate rates.
4. **Low amplitude.** At a frozen frame, most pixels must remain identical to the
   reference. Animation is read over time, not through a brighter still image.
5. **Deterministic seeds.** `time=12` always produces the same overlay frame.
6. **Responsive UI thread.** The kinetic layer uses one frame-gated `requestAnimationFrame` loop, cached glow sprites, and a reduced internal render scale.
7. **Reduced motion remains coherent.** `?reduced=1` displays one deterministic living frame. `?respectReduced=1` follows the operating-system preference; the animation-test build otherwise overrides it so a trading workstation with desktop animations disabled can still test Helios.

## 3. Core motion stack

Every visible Helios body may receive these additive layers:

| Layer | Behavior | Purpose |
|---|---|---|
| Fine current paths | Seeded spiral/flow paths migrate slowly within the disc | Makes the filament web conduct rather than flicker globally |
| Current knots | Small packets move along selected internal paths | Shows local reasoning activity |
| S-channel edge shimmer | Narrow violet and ion-blue traces migrate independently | Preserves the Helios identity without overpowering orange plasma |
| Prominence topology | Asymmetric bezier arches breathe at independent rates | Gives the silhouette living solar physics |
| Sparse ejecta | Rare warm sparks drift outside the limb | Adds depth without a particle fog |
| Pointer depth | Sub-pixel-to-low-pixel offset on the additive layer only | Reveals separation between art and live energy |

The backplate already contains the final surface detail. The overlay must not try to
replace it with a second opaque sun.

## 4. Desktop-tab motion

### Home — Apollo

- The hero core has the richest but still restrained current activity.
- Prominences remain irregular and non-radial.
- Exterior sparks are sparse.
- The board copy and four evidence chips do not move.

### Test — Particle Genesis

- Parameter dust travels from left to right.
- Spread decreases as particles approach the candidate core.
- Three aggregation wells make the progression visible:
  parameter particles → candidate nuclei → accretion.
- Particle size and trail length increase near the core.
- Respawn is hidden by alpha and phase; no point may visibly teleport.

### Strategies — Knowledge Atlas

- The central core receives normal filament motion.
- Small evidence couriers move from the core toward graph nodes at independent rates.
- Node positions, labels, and lines remain locked to the reference.

### Live — Execution Eligibility

- Two dashed rails counter-rotate at low amplitude.
- A bright verification packet moves around the outer ring.
- Eight minor checkpoints pulse independently.
- The kill-switch, status copy, and certification shield remain fixed.

### Settings — System Constellation

- The central core remains calmer than Home.
- Couriers move between the core and model, broker, data, privacy, quality, motion,
  and accessibility nodes.
- The system-control cards do not drift or pulse.

## 5. Motion-study acceptance

### A. Particle Genesis

The approved frame already contains the four visual stages. The live layer must make
the progression legible over time:

1. fine dust with narrow streaks;
2. small candidate nuclei;
3. denser aggregation wells;
4. accelerated accretion into the living core.

Particle color stays in ember, orange, gold, and rare hot-white. No blue particle
blob or diffuse brown fog is permitted.

### B. Chronosphere

- Seven elliptical temporal shells retain the reference geometry.
- Dash phase moves independently per shell.
- One courier travels on each shell, alternating direction.
- Warm past shells transition through green/cyan into blue/violet future shells.
- The core remains in front of the reference shells where drawn; the overlay does not
  repaint occlusion.

### C. Correlation Gravity Field

- Green in-sample fronts originate from the left.
- Blue out-of-sample fronts originate from the right.
- Six fronts per side move inward on offset phases.
- Small white-gold truth sparks appear near constructive interference at center.
- The approved warped grid remains a static secondary detail; the overlay does not
  brighten it into a dominant lattice.

### D. Probability Corona

- Seven quantile trajectories preserve their ordering.
- The median remains visually dominant and near-neutral.
- Each band carries one independent outward packet.
- Shorter mirrored bands remain visible on the left side of the core, matching the
  enveloping corona in the approved image.
- The result must read as a probability distribution, not a rainbow exhaust fan.

### E. Voice States

The five states must be distinguishable without reading labels:

| State | Required live grammar |
|---|---|
| Listening | Cool receptive sweep plus inbound evidence motes |
| Reasoning | Counter-rotating elliptical loops and inference couriers |
| Retrieving | Locator orbit, cited-object packet, and a reaching filament |
| Speaking | Outward pulse rings and asymmetric bilateral jets |
| Interrupted | Dim broken holding ring and intermittent shutter line |

The original sun silhouette remains visible in every state.

## 6. Deterministic controls

```js
window.__renderAt({ time: 12, paused: true });
window.__renderParityAt({ time: 12, paused: true });
window.__pause();
window.__resume();
window.__heliosMotion.setSpeed(2);
window.__heliosMotion.setIntensity(2.1);
window.__heliosMotion.status();
```

The default URL form is:

```text
helios-board.html?snapshot=1&time=12
```

Use `&fx=0` to obtain the exact unanimated source frame.

## 7. Visual QA checklist

- [ ] Default view is exactly 1536 × 1024 before uniform viewport scaling.
- [ ] All visible copy matches `REFERENCE-PARITY.png` because the approved source is
      the visible composition.
- [ ] No overlay line crosses header text, panel titles, chips, legends, or footer.
- [ ] Motion A reads as staged aggregation, not generic particles.
- [ ] Motion B has independently moving shell couriers.
- [ ] Motion C fronts visibly travel from both sides toward truth.
- [ ] Motion D retains seven ordered quantile paths and a dominant median.
- [ ] Motion E states remain distinct at one-second glance duration.
- [ ] Static frame difference is confined to graphic regions and remains low amplitude.
- [ ] `fx=0` matches the supplied source exactly.
- [ ] `snapshot=1&time=12` repeats deterministically.
- [ ] `?native=1` still opens the procedural board without JavaScript errors.
- [ ] Hidden-tab pause and resume work.
- [ ] `?reduced=1` starts no loop.
- [ ] The standalone animation-test build runs even when the OS advertises reduced motion.
- [ ] Pause, resume, speed, and intensity controls update the visible canvas.

## 8. Performance budget

The overlay remains lighter than a full-board procedural redraw:

- Reference coordinate system: 1536 × 1024.
- Default internal overlay scale: 0.78.
- Target kinetic cadence: 24 fps.
- Scheduler: one frame-gated `requestAnimationFrame` loop.
- Canvas context: synchronized alpha 2D context; do not reintroduce `desynchronized: true`.
- Glow paths: cached radial sprites and manual two-pass strokes.
- No per-frame image decoding or text/layout mutation.

Reduce cost in this order:

1. lower `quality` toward 0.65;
2. lower `fps` toward 18;
3. reduce mini-core filament counts;
4. reduce voice-state sparks;
5. remove secondary broad glow passes.

Do not reduce fidelity by recompressing the approved backplate or replacing it with a reconstructed gradient approximation.
