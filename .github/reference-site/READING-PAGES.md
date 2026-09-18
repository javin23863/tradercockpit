# Reference-based reading pages

Status: integrated and owner visually approved on 2026-09-18. Independent exact-head Codex review and any production deployment remain separate gates.

## Scope
The approved cinematic room-and-laptop composition, scene artwork, and screen-placement authority remain governed by the reference/provenance records. Subsequent homepage changes corrected public metadata, customer-facing copy, source-link behavior, and evidence binding without replacing the approved visual direction.

Thirty-nine retained HTML documents use an additive `data-reference-content` shell and a shared screen-only stylesheet. Docs uses the verified original Charts capture as a labelled product reference. Learn uses the existing two-layer laptop scene and identifies the synthetic development data. Existing public URLs and anchors remain intact. Article text and links remain byte-accounted against the historical import except for explicitly declared factual corrections recorded in `.github/reference-content-manifest.json`.

The Search module keeps its local index, dialog, keyboard and privacy behavior. It guards against inserting the retired decorative article-hero SVG and explicitly handles Escape because the search input previously consumed Escape without closing the dialog. Existing topic links remain readable indexes rather than invented diagrams.

The printable strategy-claim checklist has normal site navigation and local Search on screen. Added navigation is hidden in print. The original checklist and print behavior remain intact.

## Findings addressed during implementation
- Retained pages used a different cyan/orbit design from the approved reference homepage.
- Generated decorative research diagrams appeared on Support, Trust, Pricing and Concept pages despite not carrying data.
- An inherited heading rule broke the Support label inside the word Documentation.
- Inherited hero dimensions and pseudo-elements left excessive gaps or obsolete decorations after the first CSS pass.
- The checklist had no primary website navigation.
- The public UX contract still described a single pricing plan and carried historical visual PASS labels from a rejected appearance.
- Enhanced journey evidence links exposed a rejected historical GitHub website commit instead of the current public source pages.
- The Privacy article falsely stated that public code did not call `localStorage`, while the optional research-notes journey reads a saved local copy and writes only when the user chooses “Save on this device.”

## Declared privacy correction
The historical imported Privacy article hash remains recorded as `before_sha256`. The current Privacy page explicitly describes optional research-notes `localStorage` behavior: the journey may read a saved copy, writes only after “Save on this device,” sends those notes to no server, and warns that clearing browser data can remove the saved copy.

The correction is not a general exemption from article preservation. Its reason, corrected unwrapped SHA-256, and final wrapped SHA-256 are pinned in `.github/reference-content-manifest.json` under `trust/privacy.html`.

## Verification boundaries
`check_reference_content.py` verifies reversible reading-shell additions, the source-bound stylesheet, explicit UX-metadata transformation, and the single declared corrected-reading-shell contract. Original scene and product-image checks remain in `check_reference_site.py`. Mutation cases reject undeclared article edits, link edits, privacy-disclosure drift, CSS drift, source-image substitution, unlisted artwork, price changes, signup fail-open behavior, and reintroduction of historical repository links into public journeys.

`test_reference_content.mjs --all` renders all 39 retained reading pages at 1440 and 390 pixels from the complete publishing directory over loopback HTTP. It checks navigation, touch targets, type size, errors, images, overflow and absence of retired decorative article SVG. Browser and structural checks do not create visual approval; the owner approval is recorded separately in the readiness and UX-contract records.

Mutable Codex request, reaction, finding and completion state is GitHub PR state and is deliberately not source-controlled.

## Still open
A fresh independent Codex review of the exact current PR #52 head with zero unresolved findings is required before merge. Production deployment remains separately unauthorized.
