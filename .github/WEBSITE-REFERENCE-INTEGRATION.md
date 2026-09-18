# Reference-based website integration

Status: OWNER APPROVED; READY FOR EXACT-HEAD CODEX REVIEW. PR #52 remains unmerged. No production deployment is authorized.

The exact downloaded archive matched SHA-256 `0b0ee403e7f21773a1fb1c61520f467c39987a1dce44c7ed69aca8e5599f3a4c`. The approved cinematic room-and-laptop artwork is integrated into the actual `docs/` publishing tree with native text, controls, enhanced learning/access journeys, and the existing public documentation/support surfaces.

The import receipt is a historical inventory of the initial copy, not a claim that reviewed post-import adaptations equal the archive bytes. Use `.github/website-reference-readiness.json` and the newest `.github/evidence/reference-continuity-served/checkpoint.json` for current candidate identity and verification.

## Deliberate integration changes
- Existing product-manifest, waitlist, privacy and commerce modules remain authoritative. Checkout stays closed and fail-closed.
- All four monthly plans are exposed from the public commerce record without inventing entitlements.
- Learning/access hash journeys preserve meaningful no-JavaScript destinations.
- Charts and Models use hash-verified retained development captures with synthetic test data; full-resolution originals remain available for inspection.
- Room/laptop screen layers are deterministically regenerated at 2x raster density from those originals while preserving the approved scene geometry.
- The homepage is indexable; Open Graph, Twitter and Organization metadata are retained. Intentional `noindex` remains only on utility confirmation/error pages.
- Customer-facing release-process language such as site-level “preview”, “homepage proof” and “under visual review” is prohibited by regression checks.
- The 39 retained reading pages use a reversible additive shell; their prior article text, links and anchors remain byte-accounted.

## Acceptance boundary
The complete `docs/` tree is exercised over loopback HTTP with the production path prefix. Current acceptance includes all served routes, retained-page desktop/mobile renders, interaction journeys, content controls, source/provenance checks, production build and dependency audit.

Automated checks do not grant visual approval. The owner explicitly approved the integrated visual candidate on 2026-09-18; that approval is recorded separately in `.github/website-reference-readiness.json` and `docs/ux-page-contracts.v1.json`.

The remaining merge gate is a fresh independent Codex review of the exact current PR #52 head with zero unresolved findings. Do not merge or deploy a superseded head, enable checkout, or treat development screenshots as live-market/performance evidence.

Codex request, reaction, findings, and completion state are mutable GitHub PR state and are deliberately not source-controlled. Repository readiness can say that review is required; only PR #52 itself can prove whether the current head has actually been requested or reviewed.
