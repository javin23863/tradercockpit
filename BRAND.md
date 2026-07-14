# TraderCockpit — Brand System

The one source of truth for the channel's identity. Every surface (YouTube, Facebook, Instagram,
TikTok) and every thumbnail/post pulls from here. Direction: **"Instrument"** (a cockpit gauge),
colored to match the product landing page (`docs/index.html`) — **red on black**.

Updated 2026-07-14. Pairs with `GROWTH-AUTHORITY-PLAYBOOK.md` (the growth doctrine).

## Name & handle
- **Name:** TraderCockpit
- **Unified handle everywhere:** `@thetradercockpit` (YouTube ✓; claim on FB / IG / TikTok)
- **Tagline:** *Markets, read plainly.*
- **One-liner:** Oil, equities, rates, and the geopolitics moving them — translated into what it
  means for your portfolio. Daily market news & education. **Not financial advice.**

## Palette (matches the landing page exactly)
| Token | Hex | Use |
|---|---|---|
| ground / black | `#08030a` | primary background |
| panel | `#0a0407` | cards, insets |
| line | `#3a0d1a` | hairlines, gauge ring, grid |
| **accent / red** | `#FF1744` | THE brand color — mark, wordmark accent, key numbers |
| accent-soft | `#7a142e` | secondary/"down" red, dim strokes |
| ink | `#F5E8EA` | primary text (warm off-white) |
| dim | `#c89aa3` | secondary text |
| faint | `#7a4a52` | tertiary / labels |

Semantic only (sparingly, for up/down data, never as the accent): green `#00E676`, amber `#FF9100`.
Default is **monochrome red-on-black** — that's the look.

The simulated Apollo consumer preview in `docs/index.html` is the deliberate exception: its
bioluminescent teal/violet organic system distinguishes a future assistant interface from the
TraderCockpit media brand. TraderCockpit navigation, publishing assets, and evidence surfaces
remain red-on-black; do not propagate Apollo's palette into channel branding.

## Typography
- **Brand voice = monospace** (a trading terminal): `"Cascadia Mono","Cascadia Code",Consolas,monospace`.
  Wordmark, labels, data all in mono. Tabular figures for aligned numbers.
- Wordmark: `TRADER` in ink + `COCKPIT` in red `#FF1744`, tight tracking.

## Logo & mark (files in `tools/visuals/brand/`)
- `logo.svg` — the gauge **mark** only, portable vector (dark-ground).
- `logo.png` 1200×320 — horizontal lockup (mark + wordmark), transparent, **for dark grounds**.
- `avatar.png` 800×800 — profile pic. **One pic for all four platforms.**
- `banner.png` 2560×1440 — YouTube channel art (text-safe center 1546×423).
- `fb-cover.png` 1640×624 — Facebook Page cover (content centered; mobile crops sides).
- `watermark.png` 150×150 — YouTube branding watermark (needle-only, transparent).
- **Regenerate any of these:** `node tools/visuals/render_brand.cjs` (edits live in `brand-v2.html`).
- Clear space ≥ the gauge's radius; never recolor the mark off the red/black system; mark is
  designed for dark grounds — don't place the transparent lockup on white.

## Thumbnails (rule, enforced by `tools/visuals/thumbnail.html`)
Graham-Stephan finance style, landing-matched: **≤5 words, lead with the number**, one subject,
2–3 colors, 4.5:1 contrast at mobile size, red `#FF1744` for the key figure on black, gauge mark in
a fixed corner every time. Generate with `node tools/visuals/render_thumb.cjs` (args or `--json`).
Package the thumbnail + title *before* cutting the video (Galloway).

## Captions / hashtags (per the playbook)
- Portfolio-first, plain, machine-persona. First 3s hook. No product pitch in VO — landing link in
  description/caption only. End: "Full breakdown on YouTube: youtube.com/@Thetradercockpit".
- **Core hashtag set:** `#stockmarket #investing #markets #finance #FinTok` + 2–4 topical
  (e.g. `#oil #geopolitics #earnings #fed`). TikTok: put tags in the caption/title; invite a reply.

## Profile copy (paste-ready — for the manual profile fields)
- **Name field (IG/TikTok, ≤30 char):** `TraderCockpit · Markets News`
- **Bio (≤150 char):**
  ```
  📊 Markets, read plainly.
  Oil • equities • rates • geopolitics → your portfolio.
  News & education, not advice.
  ▶️ Daily on YouTube 👇
  ```
- **Category:** Media/News Company (or Financial Service)
- **Link:** https://www.youtube.com/@Thetradercockpit
