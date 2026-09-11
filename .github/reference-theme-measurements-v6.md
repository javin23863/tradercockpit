# TraderCockpit Reference Theme Measurements v6

Authority: owner-provided 2026-09-11 reference image, measured at 935×1683 px.

## Page composition
- Global width basis: 935 px reference canvas.
- Navigation: ~0–64 px, about 3.8% of page height.
- Research hero: ~64–445 px, about 22.6%.
- Product showcase: ~445–803 px, about 21.3%.
- How-it-works/video band: ~803–1020 px, about 12.9%.
- Pricing band: ~1020–1395 px, about 22.3%.
- Docs/how-to band: ~1395–1585 px, about 11.3%.
- Footer: ~1585–1683 px, about 5.8%.

These ratios define density and pacing. Pages may vary by purpose, but should preserve the same alternation between cinematic scene, product evidence, learning, commercial, and reference bands.

## Horizontal geometry
- Main content gutters: approximately 46–55 px each, about 5–6% of canvas width.
- Hero copy occupies roughly 36–40% of the viewport; the visual scene owns the remaining 60–64%.
- Major product mockup spans roughly 72–78% of viewport width and is centered with a slight perspective tilt.
- Pricing uses three primary columns/cards across roughly 76–80% of the canvas, plus a narrower supporting visual card.
- Docs tiles use four equal cards across the right two-thirds of the section.

## Measured palette
Pixel clustering from the authority image gives these dominant families:
- Near-black base: `#010508`, `#02090E`, `#051016`.
- Navy surfaces: `#0B151C`, `#0F232D`.
- Deep cyan shadow: `#133F49`.
- Muted text/steel: `#414C57`, `#6C7681`, `#BBBFC5`.
- Primary luminous mint: approximately `#3CF5D3`.
- Supporting cyan/teal: approximately `#31A7AE`, with bright cyan highlights around `#38F8E8`.
- Negative/risk red: approximately `#A81828`–`#B81828`; brighter red is reserved for chart emphasis.
- Blue informational highlight: approximately `#3888F8`.

Bright accents are sparse. The authority image is overwhelmingly black/navy; cyan/green/red occupy a small minority of pixels. Do not turn the page into a uniformly glowing neon field.

## Lighting and material
- Background is not flat black: use layered navy-black gradients and localized cyan/teal bloom.
- Bloom is concentrated around the globe, chart terrain, product frame edges, active pricing card, and key CTAs.
- Glass panels use dark translucent fill, 1 px luminous borders, restrained blur, and one-sided edge light.
- Shadows are deep and broad rather than soft gray card shadows.
- Red and green are semantic financial colors; cyan is infrastructure/neutral research.
- Major scenes need foreground, middle, and background overlap. Glow without depth does not qualify.

## Typography and rhythm
- Navigation/eyebrows use compact uppercase tracking; body copy is restrained and secondary.
- Hero headline is the dominant text object, roughly 34–44 px at the 935 px reference width, with tight leading around 0.95–1.02.
- Section headlines are materially smaller than the hero but remain bold and high contrast.
- Pricing numerals are oversized and visually dominant inside each card.
- Cards use compact internal spacing; the reference achieves richness through graphics and hierarchy, not large empty padding.
- Section transitions are marked by subtle cyan rules, shifts in scene density, or perspective ground changes rather than large blank gaps.

## Graphic density requirements
- Hero: dominant globe/planet, orbital geometry, finance terrain/candles, 3–4 floating data HUDs, stars/particles, and at least one foreground overlap plane.
- Product showcase: real TraderCockpit capture is the visual anchor; it must be large enough to inspect and may use perspective/frame lighting.
- Learning/video: one featured card plus multiple smaller thumbnails; avoid a plain text list.
- Pricing: one visually emphasized active card and reserved expansion capacity. Future tiers remain structurally empty until verified.
- Docs: icon-led tiles with distinct silhouettes and enough contrast to read as navigable objects.
- Detail pages: subject-specific scene geometry must replace generic decoration.

## Responsive translation
- At <=1100 px, scene and copy stack; never squeeze the reference split-screen composition until text and graphics collide.
- At <=760 px, keep the dominant subject graphic, one or two support surfaces, and semantic color contrast; remove secondary ornament first.
- At 390 px there must be no horizontal overflow, clipped primary text, or unreadably scaled HUD labels.
- Reduced motion freezes animation but retains all depth planes.

## Acceptance
A page is not visually compliant because it shares the colors. It must also match the reference's density, sectional pacing, foreground/background depth, glass/material hierarchy, semantic chart color, and large visual-to-text ratio. Review must be rendered, not source-only.
