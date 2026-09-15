# Mandatory visual review checklist

Use this before implementation and again before a visible change is called complete.

## Authority and intent

- Read the owner-approved screenshots and measured TraderCockpit visual authority first.
- Read the vendored Vercel web-design guidance and Taste redesign/image-to-code guidance.
- Choose relevant `awesome-design-md` references for the page's job; never copy their branding.
- Identify the page's one primary user intent, primary action, and evidence boundary.
- Preserve product truth: no invented prices, product capabilities, metrics, states, market data, screenshots, or analytical dimensions.

## Composition and depth

- Do not reuse one generic hero composition for unrelated page families.
- Avoid endless equal-size cards, nested bordered boxes, and decorative pill clusters.
- Use a clear foreground/midground/background hierarchy where the visual authority calls for depth.
- Give important product captures, charts, and research geometry enough scale to be the visual subject.
- Use semantic positive/negative/risk color deliberately; do not make financial graphics monochrome decoration.
- Keep 3D meaningful: data geometry must derive from the same records/readouts when it represents analysis.
- Decorative atmosphere must stay visually subordinate and must not masquerade as data.
## Interaction and accessibility

- Keyboard focus is visible and every interactive element has an accessible name.
- Touch targets remain at least 44px where the local contract requires it.
- Hover-only information has a keyboard/touch equivalent.
- Motion uses transforms/opacity where practical, respects `prefers-reduced-motion`, and stops when it no longer communicates useful state.
- Loading, empty, error, unavailable, disabled, and recovery states are intentionally designed.
- Numeric comparisons use tabular numerals.
- Headings, controls, and navigation remain usable at narrow mobile widths and browser zoom.

## Rendered acceptance

- Render every public HTML page at the required desktop viewport; do not infer all-page quality from three representative pages.
- Render every public page at the required mobile viewport.
- Produce an all-page contact sheet plus full-resolution evidence for the major page families.
- Compare Home directly to the measured owner reference and preserve its four-plane Quant Universe hierarchy.
- Inspect Pricing, Docs, Learn, Methods, How-To, Examples, Updates, Support, Trust, utility pages, and generated Concept pages separately.
- Confirm generated pages retain the visual system after the generator is rerun.
- Review at least one keyboard-only journey and one reduced-motion render.
- A visual PASS requires actual rendered evidence and no unresolved high-impact parity finding.

## Review output

Record the reviewed commit SHA, viewport(s), evidence paths, material findings, and disposition. If an external skill snapshot is refreshed, update `UPSTREAMS.json` and preserve its license/source notice in the same change.