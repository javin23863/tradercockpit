# E18 move manifest — javin23863/tradercockpit public-surface split

Date: 2026-07-26 · Branch: `feat/public-surface-hygiene` · Prepared by subagent, NOT executed.
All sizes/counts measured on tracked files at this branch head with
`git ls-files -z | xargs -0 stat -c '%s'` aggregated per top-level path (working tree, ignored
files excluded). Total: **1,072 tracked files, 124,431,408 bytes (118.7 MB)**.

## Honest scope statement

**History stays public regardless of this move.** Every file below has been disclosed in the
public git history of `javin23863/tradercockpit` and remains fetchable from that history after
deletion. The move limits FUTURE exposure only — new doctrine, new productions, new ops notes
stop landing in public. It removes nothing already disclosed, and nothing here claims otherwise.
(Credential scan of the tracked tree is clean — see the E18 report — so there is nothing to
rotate; the exposure is business documents.)

## STAY (public — matches `.github/workflows/public-surface-allowlist.yml`)

| path | files | bytes | why |
|---|---:|---:|---|
| `docs/` | 14 | 907,575 | GitHub Pages publishing source (site: javin23863.github.io/tradercockpit). No `CNAME`, no `.nojekyll` exist anywhere in the repo — the site uses the default domain and neither file is needed. See ambiguity A1 for one file inside docs/. |
| `.github/` | 1 | (new) | `public-surface-allowlist.yml` itself — the repo has no other workflows |
| `.gitattributes` | 1 | 276 | `* -text` byte contract; docs/ JSON manifests (`product-manifest.v1.json`, `prelaunch-config.v1.json`) rely on stable bytes |
| `.gitignore` | 1 | 2,220 | repo plumbing (rewrite after move — most patterns reference moved dirs) |
| `README.md` | 1 | 5,830 | public landing; **needs rewrite** — it links doctrine files and `.agents/skills/` paths that move private (ambiguity A2) |

Stay total: **17 tracked files today (18 with the new workflow), ~0.92 MB**.

## MOVE (to the new private repo)

| path | files | bytes | what it is |
|---|---:|---:|---|
| `productions/` | 440 | 54,148,899 | video production packages, approvals, receipts |
| `studio-kit/` | 369 | 53,444,878 | studio pipeline + vendored three.js media kit (~51 MB) |
| `music_library/` | 2 | 7,109,180 | licensed/track assets |
| `design/` | 11 | 5,634,591 | helios design assets |
| `tools/` | 112 | 2,147,440 | publish/upload/analytics tooling (includes credential-custody machinery) |
| `social-ops/` | 36 | 423,380 | growth ledgers, analytics snapshots, profile state |
| `thumb.png` | 1 | 236,246 | thumbnail asset (referenced only by `tools/visuals/render_thumb.cjs` — moves with tools) |
| `tests/` | 12 | 81,833 | tests for the moved tooling |
| `archive/` | 13 | 73,499 | old strategy docs + postiz compose stack |
| `.claude/` | 8 | 58,851 | agent skills/settings for the media op |
| `ops/` | 10 | 32,160 | SEO/meta/creds setup docs |
| `.agents/` | 17 | 19,194 | agent skill definitions |
| `handoffs/` | 3 | 17,419 | session handoffs |
| `staging/` | 9 | 12,690 | practice-derivatives staging |
| `SOCIAL-MARKETING-PRELAUNCH-PLAN.md` | 1 | 11,102 | doctrine |
| `AGENTS.md` | 1 | 10,677 | agent doctrine |
| `MARKET-ANALYSIS-DOCTRINE.md` | 1 | 10,363 | doctrine |
| `research/` | 1 | 9,707 | script-style research |
| `APOLLO-CONSUMER-AND-SOCIAL-PLAN.md` | 1 | 9,368 | doctrine |
| `GROWTH-AUTHORITY-PLAYBOOK.md` | 1 | 7,853 | doctrine |
| `operator-hq.html` | 1 | 6,689 | internal HQ page (links `file:///` paths) |
| `BRAND.md` | 1 | 4,278 | brand doctrine (see ambiguity A3) |
| `GROWTH-EXPERIMENT-SYSTEM.md` | 1 | 4,270 | doctrine |
| `CLAUDE.md` | 1 | 772 | agent instructions |
| `dashboard-live.bat` | 1 | 88 | local launcher |
| `dashboard.bat` | 1 | 80 | local launcher |

Move total: **1,055 tracked files, 123,515,507 bytes (117.8 MB)** — exactly the 1,055
violations the allowlist check reports on the current tree.

## Ambiguities — operator must rule

- **A1 `docs/TRUST-RECOVERY-PLAN-v2.md`** (8,142 bytes, inside the STAY set): internal
  trust-recovery/release-gate governance, publicly served from the Pages source today. The
  allowlist will NOT flag it because it lives under `docs/`. Rule: keep serving it publicly,
  or move it private with the rest of the governance docs.
- **A2 `README.md`**: kept in the allowlist as the public repo landing, but its current text
  describes the private media operation and links files that move. Needs a rewrite to a
  marketing-site README, or removal from the allowlist.
- **A3 `BRAND.md`**: brand identity (palette, tagline, handles) — arguably harmless public,
  but it is doctrine paired with `GROWTH-AUTHORITY-PLAYBOOK.md`. Listed as MOVE; flag if the
  operator wants it public.
- **A4 `docs/strategy-claim-audit-checklist.html` / `docs/refund-policy.html`**: assumed
  intentional public pages (linked site content); not moved. Flagged only for completeness.
- **A5 untracked-but-present local state** (e.g., `OpenMontage/`, `tools/token*.json` are
  gitignored): NOT covered by this manifest — git history and the allowlist see tracked files
  only. The physical move of the working clone must carry these local files to the private
  clone or they are lost.

## Sequencing note for the main thread

The allowlist check is **expected RED** on the current tree (1,055 violations, verified
locally). Order: create private repo → move paths → check goes green → THEN mark it a
required status check, together with "Require a pull request before merging" and
"Do not allow bypassing the above settings" (a required check gates PR merges, not direct
pushes).
