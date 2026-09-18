# TraderCockpit — marketing site

This repository serves the public TraderCockpit landing page via GitHub Pages, and nothing else.

- **Site:** <https://javin23863.github.io/tradercockpit/>
- **Channel:** [@Thetradercockpit](https://youtube.com/@Thetradercockpit)

Everything published here lives under `docs/`.

## What is in here

| Path | What it is |
|---|---|
| `docs/index.html` | the landing page (Pages publishing source) |
| `docs/product-manifest.v1.json` | product availability/status, verified capabilities, platform support, and the product CTA |
| `docs/commerce-public.v1.json` | public plan names, prices, and checkout state |
| `docs/prelaunch-config.v1.json` | pre-launch waitlist submission and surface configuration |
| `docs/confirmed.html`, `docs/thanks.html` | waitlist confirmation pages |
| `docs/refund-policy.html`, `docs/strategy-claim-audit-checklist.html` | published policy pages |
| `.github/workflows/public-surface-allowlist.yml` | the check that keeps this repo public-safe |

## The rule this repo enforces

**Only `docs/` (plus repo plumbing) may live here.** This repository is PUBLIC, so anything
committed to it is disclosed permanently — deleting a file later does not undisclose it, because
the history remains fetchable.

`public-surface-allowlist.yml` fails the build when the tree contains anything outside the
allowlist. That check exists because this repo previously carried the entire media operation —
growth doctrine, ops runbooks, publish tooling, production media, session handoffs — in public.
That content now lives in the private `tradercockpit-ops` repository.

If you need to add something here, ask first whether it is meant to be readable by anyone on the
internet, forever. If not, it belongs in the private repo.

## Product boundary

The landing page is a marketing surface only. Product availability/status, verified capabilities,
platform support, and the product CTA come from `docs/product-manifest.v1.json`. Public plan names,
prices, and checkout state come from `docs/commerce-public.v1.json`. Waitlist submission behavior
comes from `docs/prelaunch-config.v1.json`. Static no-JavaScript price copy may mirror the commerce
record for accessibility, but integrity checks must keep that mirror exact; page markup is not an
independent commerce authority. The current records are non-transactional pre-launch records:
capabilities must be published as verified by the product repository before this site may present
them as available, and checkout remains closed until its public commerce record enables it.
