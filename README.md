# TraderCockpit

This repo owns the **TraderCockpit media operation**: market analysis, long-form videos,
vertical cuts, publishing, and the marketing site. A market story goes in; a sourced video,
shorts, thumbnail, and platform copy come out. Trust-first: the consumer product is never
pitched on air.

The future consumer-product repository owns runtime behavior, releases, pricing,
platform support, and checkout. This repo may display those facts only through
`docs/product-manifest.v1.json`; it does not reimplement or redefine the product.

Channel: [@Thetradercockpit](https://youtube.com/@Thetradercockpit) · Landing: <https://javin23863.github.io/tradercockpit/>

---

## Read these first (they govern everything)

| Doc | What it decides |
|---|---|
| **`MARKET-ANALYSIS-DOCTRINE.md`** | *How we analyze a market.* Fixed watchlist, shock taxonomy, transmission map, cross-asset confirmation, scenario protocol, and the 7-question brainstorm that every script is written from. Makes two different writers produce the same analysis. |
| **`BRAND.md`** | *How we look and sound.* Red `#FF1744` on black, monospace, gauge mark; thumbnail rules; profile copy. |
| **`GROWTH-AUTHORITY-PLAYBOOK.md`** | *How each platform is played.* Per-platform doctrine sourced to the recognized authority (Galloway / Mosseri / TikTok Creator Portal / Graham Stephan). |

The skills below treat all three as mandatory inputs. Change the doctrine, and every future video changes with it.

## Making a video

```powershell
# Claude Code: the skill drives the whole pipeline
/daily-news-video            # or: "make today's video about <story>"
```

It runs: `market-analysis` (→ `analysis-brief.md`) → fact pack → script + `claims.yaml` →
**claims gate (blocking)** → TradingView chart capture → Godseye b-roll → cloned VO →
captions → assemble → shorts → thumbnail → publish. Detail:
[`.claude/skills/daily-news-video/SKILL.md`](.claude/skills/daily-news-video/SKILL.md).

Underneath, the stages are `tools/produce.py <prod> --stage vo|captions|assemble|shorts`
(engine venv: `OpenMontage\.venv\Scripts\python.exe`).

**The verticals recipe of record is `tools/handoff/recut_shorts.cjs`**, not `produce.py --stage shorts`
— the latter center-crops and cuts the price axis off the charts. See handoff scars 10-15.

**Quality floor:** `productions/video-02-hormuz-v4/` is the reference build (script, claims,
receipts, charts). Anything below it is a regression.

## Publishing

```powershell
& $py tools\publish.py <video.mp4> --title "..." --caption "..." `
    --platforms youtube instagram facebook tiktok --thumbnail <prod>\thumb.png
```

Public uploads are operator-gated. Credentials: [`ops/SETUP-CREDS.md`](ops/SETUP-CREDS.md).
TikTok's uploader library is broken against current Chrome; the working path is CDP
(`tools/handoff/tiktok_post_cdp.cjs` — see the handoff).

## Product boundary

The landing page (`docs/index.html`) is the marketing surface, served by GitHub Pages. Product
availability, pricing, platform support, and checkout come only from
`docs/product-manifest.v1.json`. Keep the funnel honest: no pitch in the VO, link in the
description only.

The current manifest is a non-transactional waitlist placeholder. It names **Apollo** only as
the assistant concept: local-first voice, ontology-grounded answers, free composition/preview,
and one confirmation before a verdict-producing full battery. The consumer repo must publish
those capabilities as verified before this site may present them as available.

## Layout

```
BRAND.md, GROWTH-AUTHORITY-PLAYBOOK.md, MARKET-ANALYSIS-DOCTRINE.md   the doctrine (root = first-class)
.claude/skills/     daily-news-video (pipeline) · market-analysis (the brainstorm) · godseye-footage (b-roll)
tools/              produce.py, publish.py, claims_gate.py, visuals/ (charts, news shots, brand, thumbnails)
tools/handoff/      the scripts that recovered/replaced live posts — CDP drivers, recut, platform replace
productions/        one dir per video: vo.txt, claims.yaml, receipts, charts, shorts  (v4 = the baseline)
docs/               the landing page (GitHub Pages) — the marketing surface
ops/                setup + SEO runbooks (creds, Meta/YouTube/social SEO, studio-kit wiring)
handoffs/           dated session handoffs — read the newest before you touch anything live
studio-kit/         extracted ai-video-studio-kit (clipper, generators)
archive/            superseded: the pre-pivot strategy, video-01, the universal-skill runtimes, postiz
OpenMontage/        the engine + its venv (gitignored — clone separately)
```

Knowledge base (outside this repo): `C:\Users\MSI\Desktop\TraderCockpit-Vault` — read `_meta/hot.md`.

## State

Current live URLs, what's been replaced, and the hard-won scars (aspect-ratio traps, TikTok
caption prefill, YouTube scopes, Meta tokens) live in **[`handoffs/2026-07-14.md`](handoffs/2026-07-14.md)**.
Read it before touching anything already published.
