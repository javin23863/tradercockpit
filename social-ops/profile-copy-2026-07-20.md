# TraderCockpit profile copy — approval sheet — 2026-07-20

**Status:** APPROVAL REQUIRED. Nothing in this sheet has been applied. Profile names, handles,
bios, links, categories, buttons, and images remain operator-interactive changes under Channel SEO.

**Current-state basis:** `PROFILE-READINESS-2026-07-15.md` and
`analytics-latest.json` generated 2026-07-20. The live handles are not in parity:
YouTube `@Thetradercockpit`, Instagram `@tradercockpit`, and TikTok `@trader.cockpit`.
This sheet does not authorize a handle change.

## Avatar approval

### Honest current read

The canonical local `tools/visuals/brand/avatar.png` is coherent at 800 px, but it is two marks stacked together: a detailed gauge
and a small `TC`. At 110 px the mark reads, but the eye has to choose between the dial and the
letters. At 32 px the `TC`, fine ticks, dim left arc, and glow collapse into ambiguous pixels.
The icon is recognizable only after someone already knows it. The palette math matches the visual
read: accent red on ground is 5.31:1, while the dim `#7a142e` arc on ground is only 1.91:1.
The readiness artifact did not store a clean live-avatar screenshot, so platform upload parity is
not verified by this assessment.

### Candidates

| Candidate | 800 px master | True-size read | Verdict |
|---|---|---|---|
| **A — needle** | `tools/visuals/avatar-candidates/needle-master-800.png` | The open gauge and needle remain distinct at 32 px. It is the existing Instrument motif with detail removed. | **Recommend.** Strongest silhouette and best brand continuity. |
| **B — contrast** | `tools/visuals/avatar-candidates/contrast-master-800.png` | The ink needle separates cleanly from the red ring, but the circular dial is more generic. | Good fallback for maximum dark-mode contrast. |
| **C — monogram** | `tools/visuals/avatar-candidates/monogram-master-800.png` | `TC` remains legible at 32 px, but it gives up the cockpit-gauge identity. | Clear control, weaker brand ownership. |

All candidates are centered inside the circular crop and rendered at 32 px compact comments,
40 px YouTube comments, 98 px YouTube profile, 100 px TikTok profile, 110 px Instagram profile,
176 px Facebook profile, and 800 px master. The critical operator-specified Instagram checks are
the 32 px comment surface and 110 px profile surface. Source: `BRAND.md` and the existing Instrument SVG geometry. Tool:
local HTML/SVG plus the repository's existing Puppeteer install. External cost: **$0**. No
generative model, paid provider, or new dependency was used.

Regenerate: `node tools/visuals/render_avatar_candidates.cjs`.

Approval target if selected: `needle-master-800.png`. Do not replace
`tools/visuals/brand/avatar.png` or upload it until the operator approves the exact file hash:
`F357FD9617C27AC4E89A9E44E1FE8CF1442C104D0D4CC02237A9387E8C59E084`.

Alternate master hashes:

- Contrast: `3D70847DAC46EA18BF21451C9B66CFBC2A37E7861AC2677FF056BD19A1F66918`
- Monogram: `7F014809C2561B312611BA0AA1F7F798F2A5AA3F7E5C113471DF99A853352615`

## YouTube

**Channel name**

```text
TraderCockpit
```

**Handle**

```text
@thetradercockpit
```

The live handle differs only by capitalization. Do not initiate a handle edit from this sheet.

**Description**

```text
TraderCockpit helps self-directed investors connect market news to portfolio impact through sourced cross-asset analysis and geopolitical context.

Watch the latest market breakdowns here on YouTube.

Research tooling, not financial advice. No performance is promised or implied.
```

**Keywords**

```text
market news, stock market news, oil market news, interest rates, geopolitics and markets, S&P 500, Nasdaq, crude oil, market analysis, economic news, portfolio impact
```

The keywords remove the pre-pivot `ICT`, `smart money concepts`, `backtest`, and strategy-testing
terms still present in `tools/channel_seo.py`.

## Instagram

**Name field** — 28/30 characters; `Market News` is the searchable phrase.

```text
TraderCockpit · Market News
```

**Bio** — 146/150 characters including line breaks.

```text
I help investors map news to portfolio impact.
Watch on YouTube ↓
Research tooling, not financial advice. No performance is promised or implied.
```

**Link today**

```text
https://www.youtube.com/@Thetradercockpit
```

Keep the live `@tradercockpit` handle unless the operator separately approves a rename after an
availability check.

## TikTok

**Display name** — 28/30 characters; this field appears beside comments.

```text
TraderCockpit · Market News
```

**Bio** — 78/80 characters. The mandatory disclosure leaves no honest room for a profile CTA.

```text
Research tooling, not financial advice. No performance is promised or implied.
```

**CTA today:** keep the CTA in approved post copy or a pinned comment, not in the 80-character bio.

```text
Watch @thetradercockpit on YouTube.
```

Do not change the live `@trader.cockpit` handle from this sheet. If TikTok exposes a clickable
website field, point it to YouTube today; otherwise leave it empty rather than publish a dead or
unclickable signup URL.

## Facebook Page

**Page name**

```text
TraderCockpit
```

**Username requested for parity** — availability and change remain operator-gated.

```text
@thetradercockpit
```

**Categories**

```text
Media/News Company
Financial Service
```

**Intro**

```text
Research tooling, not financial advice. No performance is promised or implied.
```

**About / description**

```text
TraderCockpit helps self-directed investors connect market news to portfolio impact through sourced cross-asset analysis and geopolitical context.

Watch the latest market breakdowns on YouTube.

Research tooling, not financial advice. No performance is promised or implied.
```

**Website today**

```text
https://www.youtube.com/@Thetradercockpit
```

**Action button today**

```text
Watch Video
```

## CTA state change

There is no live offer and Buttondown remains under provider review. Today, every profile routes
to working YouTube content. No profile points at an email signup.

Only after the signup completes a real submit → confirmation → subscriber readback should the
following copy replace the YouTube CTA:

| Surface | Today | After the list is verified live |
|---|---|---|
| YouTube | `Watch the latest market breakdowns here on YouTube.` | `Get the free daily market map: https://javin23863.github.io/tradercockpit/` |
| Instagram bio | `I help investors map news to portfolio impact.`<br>`Watch on YouTube ↓` | `I help investors map news to portfolios.`<br>`Get the daily market map ↓` |
| Instagram link | YouTube | `https://javin23863.github.io/tradercockpit/` |
| TikTok | Bio remains the exact disclaimer; YouTube CTA stays in post copy. | Bio remains the exact disclaimer; use the verified list URL only if a website field is available. |
| Facebook | Website = YouTube; button = `Watch Video` | Website = verified list URL; button = `Sign Up`; description CTA = `Get the free daily market map.` |

## Style-gate receipt

Interpreter: `OpenMontage\.venv\Scripts\python.exe`  
Gate: `tools/script_style_gate.py` → `audit_text()` with each exact audience-facing line supplied
separately over JSON stdin.  
Result: **24/24 exact field lines PASS; 0 BLOCK.** The assembled YouTube description,
Instagram bio, TikTok bio, Facebook description, and future Instagram bio also each PASS.

Advisory warnings on the line-by-line run: `missing editorial owner` 24 (expected on names,
handles, URLs, labels, and neutral institutional copy), `automatic summary ending` 14 (single-field
fragments), `uniform sentence rhythm` 2 (URLs), and `ornamental group of three` 1 (the machine
keyword list). None is a block or a performance/claims finding. Any future `BLOCK` makes this sheet
unapprovable.
