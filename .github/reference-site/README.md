# Reference-site integration tooling

Status: source imported and adapted; owner visual approval recorded. The current PR #52 candidate is review-ready only after its exact-head verification receipts remain green. No production deployment is authorized by these tools.

The historical input is `TraderCockpit-homepage-proof-source.zip`, SHA-256 `0b0ee403e7f21773a1fb1c61520f467c39987a1dce44c7ed69aca8e5599f3a4c`. Keep the archive intact. The importer reads only explicitly listed runtime members and never performs general ZIP extraction. Unmasked source artwork is not copied to the publishing tree.

## Historical import sequence
Run from the repository root, using Python 3.10+:

```text
python .github/scripts/test_reference_import.py
python .github/scripts/import_reference_site.py
python .github/scripts/import_reference_site.py --apply
python .github/scripts/import_reference_site.py --check
```

The importer is intentionally conservative: planning is read-only; apply is refused outside the isolated integration branch, on changed publishing destinations, on conflicting new assets, or when product/commerce authority no longer matches the expected prelaunch boundary. Importing source bytes alone never awards review or release readiness.

The initial source homepage carried review-era metadata and copy. The reviewed integration deliberately adapts that material: the public homepage is indexable, social/Organization metadata is present, public release-process wording is removed, and checkout remains closed. Regression checks reject reintroducing the homepage `noindex` state or customer-facing review/proof language. Intentional `noindex` on error/confirmation utility pages is unaffected.

## Browser and bridge fixtures
`test_reference_bridge.mjs` exercises the real integration and product/prelaunch modules over loopback HTTP. It checks valid/invalid commerce, failed product loading, native-link enhancement, same-origin CTA resolution and configured-but-unsubmitted waitlist behavior.

The complete candidate is tested separately by the served-site and journey suites over the production path prefix. Import fixtures, bridge fixtures and source receipts do not substitute for those complete browser runs.

## Imported and adapted site
The original import receipt remains historical. Current adapted-site integrity is enforced by `check_reference_site.py`, the 14 mutation tests, the source-bound screen-layer generator/test, public UX/claims/hardening checks, and the exact-head continuity verifier.

Use `.github/website-reference-readiness.json` for the current review gate. Owner visual approval is already recorded; an independent exact-head Codex review with zero unresolved findings is still required before merge. Deployment remains a separate authorization.
