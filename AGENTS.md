# TraderCockpit public-site agent rules

These instructions apply to the entire repository.

## Mandatory visual authority

Any change that affects something a customer can see must begin by reading:

- `DESIGN.md`
- `development/visual-skills/README.md`
- `development/visual-skills/CHECKLIST.md`
- the applicable vendored skills under `development/visual-skills/vendor/`
- the relevant owner-approved visual authority under `.github/`

Visible work includes HTML, CSS, JS-rendered UI, WebGL/VTK scenes, screenshots, video or image presentation, responsive behavior, motion, documentation graphics, commerce surfaces, and utility/error states.

The vendored skills are mandatory process/reference material. TraderCockpit product truth, measured visual authority, accessibility, data provenance, and public-claim boundaries outrank any conflicting third-party suggestion.
## Implementation rules

Preserve the existing static HTML/CSS/JS architecture and the existing production WebGL/VTK renderers unless an approved plan explicitly changes them. Do not add a framework or visual dependency merely because a third-party skill recommends one.

Do not invent market data, metrics, product state, prices, claims, screenshots, testimonials, or analytical dimensions. Keep synthetic examples labeled. Use the same deterministic records for a data graphic and its displayed readout when the graphic represents analysis.

Do not solve site-wide visual work by restyling only Home, Pricing, and Research Lab. Generated pages and every public page family are part of acceptance. Fix generators before generated output when appropriate.

## Completion rule

Source inspection is insufficient for visible work. Before declaring a visual change complete:

1. Run the website integrity/public claim/UX checks and the mandatory visual-skill authority check.
2. Re-run generators and prove generated output is current.
3. Render all public HTML pages at desktop and mobile acceptance widths.
4. Produce current evidence and inspect the major families individually, not only a contact sheet.
5. Compare the homepage to the measured owner reference and record any remaining parity gap.

Never convert a prior audit status into a new PASS without fresh rendered evidence from the reviewed commit.