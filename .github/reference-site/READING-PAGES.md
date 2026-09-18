# Reference-based reading pages

Status: implemented for browser appraisal; not owner-approved or ready for release.

## Scope
The homepage and Research Lab HTML are byte-identical to checkpoint `aceeef931a54d230133e53296fb810d94e0dd0a7`. The scene assets and screen layers are also unchanged. This is a reading/navigation continuation, not another homepage redesign.

Thirty-nine existing HTML documents receive an additive `data-reference-content` shell and a shared screen-only stylesheet. Docs uses the verified original Charts capture as a labelled product reference. Learn uses the existing two-layer laptop scene and identifies the synthetic development data. Every existing article, public URL, anchor and original link remains intact. Removing only the declared additions restores each prior document byte-for-byte. The generated Concept templates apply the same wrapper.

The Search module keeps its existing index, dialog, keyboard and privacy behavior. It adds a guard against inserting the retired decorative article-hero SVG on the migrated pages and an explicit Escape handler, because the search input consumed Escape without closing the dialog. Existing topic links are retained as readable indexes instead of orbiting an invented diagram.

The printable strategy-claim checklist gains normal site navigation and local Search on screen. Added navigation is explicitly hidden in print. The print stylesheet and original checklist remain intact.

## Findings addressed during implementation
- Retained pages used a different cyan/orbit design from the reference homepage.
- Generated decorative research diagrams appeared on Support, Trust, Pricing and Concept pages despite not carrying data.
- An inherited heading rule broke the Support label inside the word Documentation.
- Inherited hero dimensions and pseudo-elements left excessive gaps or obsolete decorations after the first CSS pass.
- The checklist had no primary website navigation.
- The public UX contract still described a single pricing plan and carried historical visual PASS labels for the rejected appearance.

## Verification boundaries
`check_reference_content.py` verifies the reversible additions, the source-bound stylesheet and the explicit UX-metadata transformation. Original scene and product-image checks remain in `check_reference_site.py`. Mutation cases reject article edits, link edits, CSS drift, source-image substitution, unlisted artwork, price changes and signup fail-open changes.

`test_reference_content.mjs --all` captures all 39 reading pages at 1440 and 390 pixels from the complete publishing directory served over loopback HTTP. It checks navigation, touch targets, type size, errors, images, overflow and absence of the retired decorative article SVG. Full-page captures and the earlier failing baseline are retained separately. These conditions do not award aesthetic approval.

The historical UX-contract JSON is preserved under `.github/reference-site/ux-contracts-before.json`. Current contracts retain all eight structural dimensions and all routes, but explicitly mark human visual approval pending. A checker requiring the word PASS inside an appraisal was not a valid visual gate.

## Still open
Production finishing of the supplied scene artwork, final owner appraisal of the integrated homepage and reading pages, and independent review. No Codex review, merge, checkout activation or deployment is requested by this checkpoint.
