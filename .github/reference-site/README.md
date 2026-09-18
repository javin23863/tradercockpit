# Reference-site integration tooling

Status: tooling implemented; the reference artwork and homepage have NOT been imported into this worktree. This is not a review-ready website.

The input is `TraderCockpit-homepage-proof-source.zip`, SHA-256 `0b0ee403e7f21773a1fb1c61520f467c39987a1dce44c7ed69aca8e5599f3a4c`. Keep the archive intact. The importer reads only explicitly listed runtime members; it never performs general ZIP extraction. Unmasked source artwork is not copied to the publishing tree.

## Import sequence
Run from the repository root, using an available Python 3.10+ interpreter:

```text
python .github/scripts/test_reference_import.py
python .github/scripts/import_reference_site.py
python .github/scripts/import_reference_site.py --apply
python .github/scripts/import_reference_site.py --check
```

By default, the ZIP is read from the user's Downloads folder. For another path, set `TC_REFERENCE_ARCHIVE` for tests and pass `--source <path>` to the importer. The default importer command is planning-only. Apply is refused outside the isolated integration branch, on a changed publishing tree, on conflicting new assets, or on changed product/commerce authority.

The importer preserves all existing public documents except the homepage and the explicitly reconciled four-tier commerce record. It restores the existing product-manifest and prelaunch modules, meaningful non-JavaScript navigation, canonical metadata and a fail-closed waitlist surface. No real signup submission is part of testing. The imported homepage remains noindex until release review. Existing old-theme-specific checks still require a deliberate migration after import; do not remove checks merely to get a PASS.

## Bridge browser fixture
`node .github/scripts/test_reference_bridge.mjs` uses an installed Puppeteer package. Set `TC_PUPPETEER_MODULE` to its module file and `TC_CHROME` to an installed browser when those are not locally resolvable. No dependency, browser, credential or account is installed by this test.

The fixture serves the real integration module and existing product/prelaunch modules over loopback HTTP. It checks valid/invalid commerce, failed product loading, native-link enhancement, same-origin CTA resolution and configured-but-unsubmitted waitlist behavior. It is NOT a complete website render or a visual approval.

Archive-dependent tests are explicitly skipped when the pinned ZIP is absent. Skipped tests do not close import or review readiness. Import receipts likewise do not award served-browser acceptance or visual approval. The complete integrated site must still be reviewed and tested under its actual publishing path before Codex review.

## Imported and adapted site
The source was imported from the exact downloaded archive. The original import receipt remains historical. After the documented navigation, pricing, capture and access corrections, use `python .github/scripts/check_reference_site.py` and the served-browser tests for the current implementation; importer `--check` intentionally detects those post-import changes.
