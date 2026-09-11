# TraderCockpit Homepage Visual Authority — Cinematic Quant Universe v4

Status: approved visual-direction correction based on the owner-provided 2026-09-11 reference image.

## Purpose
The homepage must read as a premium quantitative-research cockpit, not a conventional SaaS page with decorative panels. The owner reference is authoritative for depth, spatial composition, luminous contrast, scene density, and the relationship between finance data graphics and the hero copy.

## Non-negotiable visual hierarchy
1. The hero is a cinematic scene, not a bordered card. The right 60–68% of desktop space is a large layered Quant Universe; the left 32–40% carries copy and calls to action.
2. The globe is the dominant object: approximately 520–680 CSS px across on a 1440px desktop, with a dark volumetric core, cyan/green edge light, latitude/longitude structure, point clouds, orbital arcs, and foreground/background overlap.
3. The scene must visibly occupy at least four depth planes: distant stars/grid, globe/orbits, floating glass HUD cards, and foreground candlestick/market terrain.
4. Green and red are semantic market contrasts, not accents. Cyan/teal is neutral research/infrastructure. Purple/blue may support depth but must not dominate.
5. The foreground market terrain must be perspective-driven: converging grid lines, candle bodies/wicks, glow, and horizon falloff. It cannot read as a flat row of bars.
6. Instrumentation must float around the universe at varied scales and z-depth. Cards use translucent navy glass, narrow luminous borders, subtle internal charts, compact labels, and synthetic/illustrative values only.
7. Background illumination is localized. Use bloom around the globe, cards, and terrain instead of a uniform blue wash.
8. The hero must feel dense but not cluttered: major objects overlap, negative space remains behind the primary headline, and visual energy concentrates around the globe center/right.

## Scene composition at 1440px
- Hero minimum height: 820–900px.
- Copy column: x≈6–38% viewport; headline begins in upper third.
- Globe center: x≈68–73%, y≈42–47% of hero; radius≈270–330px.
- Major orbit ring: extends beyond the globe by 12–28% and may bleed outside the visual column.
- Primary positive HUD: upper-right quadrant.
- Primary negative HUD: mid-right or lower-right quadrant.
- Secondary neutral/infrastructure HUD: upper-left of globe.
- Candlestick terrain: horizon around 64–70% hero height, expanding toward bottom edge.
- Lower instrumentation deck: compact glass cards layered above the terrain, never a full-width flat dashboard row.

## Materials and lighting
- Page base: #02060b to #06101a.
- Glass surface: rgba(4, 14, 24, .58–.82), 12–20px backdrop blur.
- Cyan neutral: #3de8ff / #55dfff.
- Green positive: #49ef9a / #36f1c1.
- Red negative: #ff526e / #ff657f.
- Borders: 8–24% alpha; bright edges only near active/glowing features.
- Bloom: soft, spatially localized, never a white drop-shadow around every panel.

## Motion
- Globe rotates slowly and continuously unless reduced motion is requested.
- Orbital arcs and point-cloud shimmer may move at different rates to create parallax.
- Pointer movement may alter yaw/pitch by a small bounded amount on desktop.
- Foreground terrain may drift subtly in perspective; no rapid trading-animation effect.
- `prefers-reduced-motion: reduce` must freeze decorative motion and preserve the full composition.

## Content/truth constraints
- All hero values and microcharts are deterministic synthetic illustrations and must remain labeled as such in accessible text or nearby copy.
- No synthetic number may be described as product performance, live market data, customer return, or a verified capability.
- Product availability remains governed by `product-manifest.v1.json`; marketing art cannot override it.
- Checkout stays governed by `commerce-public.v1.json`.

## Responsive behavior
- At <=1100px, copy stacks above the scene while the globe remains dominant.
- At <=760px, keep one large globe, two or three HUD cards, and a cropped foreground terrain. Remove low-value labels before shrinking everything into unreadability.
- No horizontal overflow at 390px.
- Mobile must still feel like the same cinematic system, not a fallback collection of ordinary cards.

## Acceptance criteria
- The Quant Universe has no visible rounded-rectangle container boundary on desktop.
- At least four distinct depth planes are visible.
- The globe is the largest visual object in the hero.
- Perspective candles/grid clearly occupy the foreground.
- At least four floating HUD surfaces surround the globe on desktop; at least two survive on mobile.
- Positive/negative synthetic regions are immediately distinguishable by green/red semantics.
- Desktop 1440 and mobile 390 screenshots have no overflow or console errors.
- Reduced-motion rendering is compositionally complete and non-animated.
- Existing website integrity, hardening, public-claims, and product-state checks remain green.
