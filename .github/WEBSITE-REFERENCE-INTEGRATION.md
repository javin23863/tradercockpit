# Reference-based website integration

Status: NOT READY FOR CODEX REVIEW. This is a separate continuation from main, not PR #51.

## Implementation boundary
The reference-based room-and-laptop preview is the design input. Preserve its composition, native controls, real labelled development captures, bounded motion and six reading/access views. Do not translate it into the rejected CSS-drawn room or restart the visual theme.

The source archive and local runtime bundle hashes are recorded in `website-reference-readiness.json`. Import the verified archive before claiming the preview exists in this branch. No preview source or scene assets have been imported yet.

## Work required before review notification
1. Integrate the preview source and its runtime assets into the actual `docs/` publishing tree. Preserve existing public documents, incoming URLs, canonical metadata and no-JavaScript access. Keep source artwork containing fictional dashboards out of runtime delivery.
2. Restore a single authoritative product/commerce contract. Preserve the four approved monthly prices, waitlist state and disabled checkout. Do not fabricate entitlements, sign-ins, market results or customer evidence.
3. Finish scene quality and product-capture publication checks. Distinguish decorative artwork from actual captures; retain provenance and synthetic-data labels. Unapproved assets and visible cleanup defects remain findings, not silent passes.
4. Serve the complete integrated `docs/` tree under the production path prefix and navigate it with a real browser. In-memory HTML rendering and minimal fixtures are insufficient. Test all existing and new routes, mobile, keyboard, reduced motion, lazy video consent, notes save/reload/restart, corrupt storage and recovery, imports/exports and missing routes.
5. Capture the real served homepage and major page families; compare against the supplied reference at matching proportions. Keep owner visual acceptance separate from automated browser health.
6. Run repository integrity, public claims, UX, generation and production-build checks on the exact candidate. Preserve required checks; a missing runner is neither a product failure nor a pass. Do not buy Actions capacity or dispatch workflows manually.
7. Bind receipts and screenshot hashes to the reviewed implementation and public tree. Identify any documentation-only certification delta. Do not award readiness because a document contains a readiness label.

## Review and release
Notify the owner only when the actual integrated candidate is ready for Codex review, with the branch, exact commit, served-browser evidence and remaining release conditions. Do not submit the rejected PR #51. Do not request a new review, merge, deploy, change protections, or enable checkout as part of the notification.

Readiness and release are different gates. Independent review findings must be corrected and re-reviewed on the latest candidate before a live-site cutover. Keep the current live website and historical branches unchanged until that separate step is authorized.

## Executable tooling checkpoint
The verified importer now exists at `.github/scripts/import_reference_site.py`; its default command makes a plan without writing. Usage and environment requirements are in `.github/reference-site/README.md`.

Ten exact-archive import/mutation tests passed in temporary container fixtures. The Windows bridge test exercised the real integration module and existing product/prelaunch modules over loopback HTTP, with seven checks and no external request. Its scope is explicitly a minimal fixture, not the complete website.

The exact source ZIP is still absent from the authorized Windows Downloads folder. Windows archive-dependent tests therefore remain skipped, and no source artwork or homepage has been installed into `docs/`. The existing publishing tree remains unchanged. Local and Windows evidence is under `.github/evidence/reference-integration-tooling/`; those helper receipts do not close any served-site, visual approval or review-readiness gate.
