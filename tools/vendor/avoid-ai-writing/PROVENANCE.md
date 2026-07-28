# Provenance

Source: https://github.com/conorbronsdon/avoid-ai-writing
Installed: 2026-07-28, on operator instruction ("install repo, add to ai write gates for
social media department"). Board card `social.ai-writing-gate`.
Commit: 27156c7ae69fade80f2a3410e6899b780248709d (detector package version 3.16.0)
License: MIT — see LICENSE.

## What is vendored, and why verbatim

- `detector/patterns.js` — the whole engine, 1,754 lines of regex, stylometry and AI-tool
  fingerprints. Vendored unchanged so a version bump is a clean file swap. Porting it to
  Python would fork it on day one.
- `detector/patterns.test.js`, `detector/categories.test.js`, `detector/CATEGORIES.md`,
  `package.json` — upstream's own suite, so a bump is verifiable rather than trusted.
- `runner.js` — the ONLY local addition. Upstream ships no CLI; this reads stdin and prints
  the analysis as JSON so `tools/ai_writing_gate.py` can call it.

Not vendored: SKILL.md (installed separately at `.claude/skills/avoid-ai-writing/`),
plugins/, cursor-rules/, docs/, .github/ — other agent platforms and CI we do not use.

## Bumping it

1. Re-clone upstream, copy the files above, update the commit hash and version here and in
   `VERSION`.
2. `npm --prefix tools/vendor/avoid-ai-writing test` — upstream's suite must pass.
3. `py tools/ai_writing_gate.py --survey productions/*/vo.txt` and over the shipped social
   copy. It exits non-zero if any armed BLOCK category now fires on known-good copy.
   A new upstream category defaults to WARN; promote it only after that survey is clean.

A bump that skips step 3 can red the nightly social batch on correct copy, which trains
people to bypass the gate — the failure `tools/script_style_gate.py:445` already documents.
