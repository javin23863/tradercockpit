# TraderCockpit Measured Demo Visual Authority — v6

Status: measured from the owner-supplied 2026-09-11 demo image. This file is the dimensional and palette authority for public-site presentation. Earlier visual specs remain semantic constraints, but where spacing, density, scale, or color differ, this measured reference wins.

## Reference coordinate system
- Source image: 935 × 1683 px.
- Treat measurements as ratios, not fixed browser pixels.
- Scale factor to a 1440px desktop: 1.5401×.
- Main left gutter: 50px = 5.35% width ≈ 77px at 1440.
- Main right gutter: 44px = 4.71% width ≈ 68px at 1440.
- Effective content span: about 841px = 89.95% width ≈ 1295px at 1440.
- Header visual height: about 52px ≈ 80px at 1440.

## Vertical composition
| Band | Reference y | Height | Share of page | 1440-width scaled height |
|---|---:|---:|---:|---:|
| Hero + product stage | 0–840 | 840 | 49.9% | ~1294px |
| Video / How it works | 840–1040 | 200 | 11.9% | ~308px |
| Pricing | 1040–1410 | 370 | 22.0% | ~570px |
| Docs & How-Tos | 1410–1590 | 180 | 10.7% | ~277px |
| Footer | 1590–1683 | 93 | 5.5% | ~143px |

The page is intentionally compact below the product stage. Large empty vertical gaps or 500–700px generic marketing sections are not reference-compliant.

## Measured homepage geometry
- Hero copy: x≈50–435, y≈90–400. Width ≈41% of reference.
- Hero headline box: x≈50, y≈118, w≈380, h≈76. At 1440 this is ≈585×117px.
- Hero body copy: x≈50, y≈205, w≈315, h≈40.
- CTA row: x≈50, y≈262, w≈274, h≈40.
- Four-value/feature strip: x≈50, y≈333, w≈305, h≈68.
- Quant scene begins around x≈395 and owns the right ≈58% of the frame.
- Dominant globe center ≈(616,197), radius ≈162px; at 1440 ≈(949,304), radius ≈250px.
- Orbit/terrain effects intentionally bleed beyond the globe and to the right edge.
- Product device/capture: x≈158, y≈445, w≈733, h≈365; ≈1129×562px at 1440.
- Product device occupies ≈78.4% of page width and is centered slightly right of page center.

## Lower-band geometry
- Video intro: x≈48–306. Featured visual: x≈347–590. Catalog: x≈603–889.
- Pricing columns: Explorer/reference slot x≈47–257; primary x≈270–512; secondary x≈526–740; promo/context x≈751–891.
- Pricing column gaps are only ≈13–16px in the 935px reference.
- Docs intro: x≈48–308. Four compact cards run from x≈320 through x≈891.
- Footer content uses the same ≈5% page gutter and remains a single compact horizontal band.

## Density rule
The visual authority is not “large dark sections with one graphic.” It is layered density: primary message + finance/research graphic + compact secondary information occupying the same viewport. Desktop sections after the hero must generally expose their full purpose without requiring an additional screen of scrolling.

## Measured palette
Pixel clustering and direct sampling from the reference produce these working tokens:
- Page void: `#010509` / `#01070B`.
- Elevated field: `#040E14`.
- Standard panel: `#0A1219`.
- Lit/depth panel: `#081B24` to `#0F2633`.
- Deep cyan border/support: `#16485B`.
- Primary luminous teal: `#3CFAD2` / `#3DFAD2`.
- Secondary cyan-blue: `#3DAED3`.
- Negative red: `#E54A5A`; darker red depth: `#AB1925`.
- Primary text: `#FFFFFF` to `#F6F8FA`.
- Secondary text: `#A4ABB3`.
- Tertiary text: `#6B747D`.

Primary teal is the strongest chromatic signal. Red is reserved for negative/risk semantics. Cyan-blue supports charts, outlines, and depth. Most of the page remains in the `#010509`–`#0A1219` range; brightness is localized around data graphics, CTA edges, and device/globe highlights.

## Material treatment
- Cards use near-black navy glass rather than gray SaaS panels.
- Typical border is 1px at 10–22% cyan/white alpha.
- Radius is restrained: ~10–16px for HUD/data cards, ~16–20px for content cards, ~24px only for major device/feature frames.
- Shadow direction is downward/deep; glow is local and colored, never a uniform white halo.
- Use backdrop blur only where an object visibly floats over another depth plane.
- Large illustrations can bleed outside their nominal columns; copy may not.

## Typography measurements and hierarchy
- Reference headline occupies ~41% of page width and is approximately 38–42px tall per line on the 935px image; target ≈58–65px at 1440.
- Primary section headings are approximately 28–32px on the reference; target ≈43–49px at 1440.
- Body copy is approximately 14–16px on the reference; target ≈20–23px at 1440 only in the hero, with lower sections staying closer to 15–18px CSS for density.
- Eyebrows, nav, HUD metadata, and pricing detail use compact 9–12px reference text with increased letter spacing.
- Headings are heavy grotesk/sans, tight tracking, ~0.92–1.0 line-height. Body text uses a clean neutral sans. HUD/data labels use mono.

## Graphic grammar
Every major page must combine at least three visible depth cues from this set: volumetric sphere/field, orbit geometry, candlestick/path terrain, floating glass instrumentation, perspective grid, layered device/window, network graph, distribution field, timeline/validation lanes, or metric rings.

Homepage requires all four reference planes: star/background field; globe/orbits; HUD cards; foreground market terrain/device. Detail pages may use fewer planes but must retain overlap, localized lighting, and subject-specific geometry.

## Production rendering contract
The measured composition remains the visual authority, but the homepage Quant Universe is no longer allowed to satisfy the depth requirement with manual 2D projection alone. The production implementation must use a WebGL renderer with a perspective camera, true XYZ geometry, depth-tested meshes or instancing, scene lighting, and GPU post-processing.

The strategy field and foreground market terrain must preserve the measured semantic palette: teal `#3CFAD2` for positive/gain examples, red `#E54A5A` for negative/loss examples, and cyan `#3DAED3` for neutral/supporting values. Color may not be the only distinction; height, position, geometry, or labels must carry the same meaning.

The WebGL scene must retain reduced-motion behavior, pause/reset controls, mobile pixel-density limits, document-visibility throttling, and a local non-network fallback when WebGL cannot initialize. The generated browser bundle is reproducibly built from checked-in source and pinned dependencies; generated output may not be hand-edited.

The same production-rendering rule applies to all ten Research Lab atlas canvases. Their legacy 2D renderers may remain as local fallbacks and as the metric/control logic authority, but when WebGL is available the visible strategy field, Monte Carlo fan, robustness terrain, network, distribution, regime cube, walk-forward blocks, holdout boundary, drawdown field, and selection funnel must use true perspective/depth geometry rather than 2D projection alone.

WebGL geometry must visualize the same deterministic synthetic records that drive each module?s metrics and readouts; a visually similar parallel sample is not acceptable. Axis/threshold/node annotations remain visible in the 3D path. Narrow canvases must fit complete analytical geometry rather than crop endpoints. Context loss permanently hands that surface back to the 2D fallback for the page lifetime so two renderers can never overlap.

## Responsive translation
- Desktop ≥1100px preserves the measured left/right composition and dense first viewport.
- Tablet <1100px stacks copy above the subject visual; no side-by-side squeeze.
- Mobile keeps the same palette/materials, one dominant visual, one or two supporting glass layers, and compact vertical rhythm.
- Never preserve desktop density by shrinking critical text below legibility; remove secondary decoration first.

## Acceptance
Rendered appraisal must compare section heights, gutters, palette, headline scale, card radii, and graphic density against these measurements—not only check that cyan/green/red are present.