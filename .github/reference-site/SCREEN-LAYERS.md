# Reference scene screen layers

Status: integrated quality improvement; not a release or owner visual approval.

## Purpose

The room and laptop artwork are unchanged. Only the screen pixels placed inside the existing monitor/laptop quadrilaterals are regenerated from the verified full-resolution TraderCockpit development captures.

## Sources

- Room / Charts: `docs/assets/reference-site/original-charts.png`, 1220×886, SHA-256 `bc2746d1fdda38c5cdcea0a74d9f82e78d0fb6cb9f98844023b4283f55aad9ae`.
- Laptop / Models: `docs/assets/reference-site/original-models.png`, 1440×1000, SHA-256 `3a63057265cb14c7640883cbba1144907c7dd2e2e5419b8f37fcb5ca14ff3bc6`.

Both remain labelled synthetic development evidence and are not release-performance claims.

## Geometry

The compositor uses the existing `.github/reference-site/provenance/screen-placement.json` homographies and screen quadrilaterals. It does not move, crop, recolor, redraw or resize the room/laptop artwork.

The rendered overlay files have 2× raster density while retaining the same CSS footprint:
- `room-screen.webp`: 2048×884 pixels displayed in the 1024×442 scene layer.
- `laptop-screen.webp`: 2048×628 pixels displayed in the 1024×314 scene layer.

The complete projected screen plane is opaque so the prior illustrative dashboard cannot leak around the verified capture.

## Reproducibility

`.github/scripts/generate_reference_screen_layers.mjs` rebuilds both overlays from the verified originals. `.github/scripts/test_reference_screen_layers.mjs` checks source identities, output dimensions, output scale, generator identity and projected alpha bounds.

`check_reference_site.py` binds the generated layers into the main integrity gate. Mutation tests reject:
- replacing an output layer,
- changing the historical scene-placement authority,
- changing the generator identity,
- or downgrading the source back to the reduced preview captures.

The generator must be byte-deterministic on the authorized Windows browser environment.

## Acceptance boundary

This improves screen fidelity only. The supplied room/laptop scene artwork remains the current owner reference asset. Its final aesthetic acceptance, the integrated page appraisal, and independent Codex review remain separate gates.
