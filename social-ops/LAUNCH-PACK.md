# TraderCockpit prelaunch-to-launch pack

**Status:** Ready for verified product inputs. Every token in braces is deliberately unresolved.
Do not publish this pack until the consumer-product manifest and real release-candidate media pass review.

## Product fact map

| Launch claim | `product-manifest/v1` source | Current value |
|---|---|---|
| Product name and one-line summary | `product.name`, `product.summary` | `PENDING VERIFICATION` |
| Availability | `status`, `generatedAt` | `waitlist` |
| Apollo state | `assistant.name`, `assistant.status` | Concept only |
| Capabilities | `verifiedCapabilities[]` | None verified |
| Supported platforms | `platforms[]` | `PENDING VERIFICATION` |
| Price/offer | `offer.display` | `PENDING VERIFICATION` |
| Main action | `cta` or `checkout` | Waitlist only |
| Support and refund terms | `support`, `refund` | `PENDING VERIFICATION` |

Validation: `node tools/check_product_manifest.mjs --browser`

## Launch landing copy slots

- Eyebrow: `TRADERCOCKPIT // {VERIFIED RELEASE STATUS}`
- Headline: `{PRODUCT.NAME}`
- Summary: `{PRODUCT.SUMMARY}`
- Proof rows: render only labels and summaries present in `verifiedCapabilities[]`.
- Platform row: render only `platforms[]` supplied by the product.
- Offer: render only `offer.display`; never infer savings, returns, or urgency.
- Primary CTA: `checkout` only when `status=available`; otherwise `cta`.
- Boundary line: “Research tooling, not financial advice. No performance is promised or implied.”

## 60-second product-demo storyboard

| Time | Real capture required | Verified label slot |
|---:|---|---|
| 0–5s | Release-candidate opening state | `{PRODUCT.SUMMARY}` |
| 5–14s | User enters a real strategy specification | `{CAPABILITY_1}` |
| 14–24s | Rules/evidence receipt appears | `{CAPABILITY_2}` |
| 24–36s | Preview or test flow, exactly as shipped | `{CAPABILITY_3}` |
| 36–47s | Limitation/failure state | `{KNOWN_LIMITATION}` |
| 47–55s | Result or receipt with no performance promise | `{VERIFIED_OUTPUT}` |
| 55–60s | Availability and action | `{PLATFORMS}` + `{CTA_OR_CHECKOUT}` |

No simulated landing-page theater may be cut to imply a real product run.

## Launch-day content

### Long-form outline

1. The portfolio/research problem the release addresses—without promising a winner.
2. What shipped, sourced line-by-line from the manifest.
3. One complete real workflow from input to receipt.
4. What the product refuses or cannot do.
5. Platform, price, support, and refund facts.
6. CTA, followed by the not-advice/no-performance boundary.

### Vertical hooks

- “Most strategy claims fail before the backtest. Here is the exact step `{PRODUCT.NAME}` verifies first.”
- “This screen is the difference between a strategy preview and an evidence verdict.”

Both remain `PENDING VERIFICATION`; replace the braces and re-run the claims gate.

### Launch email

**Subject:** `{PRODUCT.NAME} is {VERIFIED STATUS}`

TraderCockpit built its audience by separating confirmed facts, mechanisms, and scenarios. The same
standard applies here. `{PRODUCT.SUMMARY}`

What is verified today:

- `{VERIFIED CAPABILITY}`
- `{SUPPORTED PLATFORM}`
- `{KNOWN LIMITATION}`

`{OFFER}` · `{SUPPORT}` · `{REFUND}`

`{CTA OR CHECKOUT}`

Research tooling only. No performance is promised or implied.

### FAQ

- What is available now? — Answer only from `status` and `verifiedCapabilities[]`.
- Which platforms are supported? — Answer only from `platforms[]`.
- Does it guarantee an edge or returns? — No.
- What data and limitations apply? — `{PENDING PRODUCT VERIFICATION}`.
- What does it cost? — `{OFFER.DISPLAY}`.
- Where are support and refund terms? — `{SUPPORT.URL}` and `{REFUND.URL}`.

### Rollback/correction copy

“UPDATE `{TIMESTAMP WITH TIMEZONE}`: We paused `{FEATURE/OFFER/AVAILABILITY}` after the release facts
changed. The prior wording was `{OLD CLAIM}`. The verified state is now `{NEW CLAIM}`. Current source:
`{MANIFEST OR SUPPORT URL}`.”

## Creator/press kit

- One-liner: TraderCockpit maps the day’s economic facts into portfolio transmission channels, with
  primary sources, timestamps, and visible corrections.
- Audience promise: facts first; mechanism second; scenario only with a trigger.
- Contact: `joshuajacob2386@gmail.com`
- Brand assets: `tools/visuals/brand/`
- Source policy: primary releases first; chart/feed for levels; no silent corrections.
- Product fields: all remain `PENDING VERIFICATION` until supplied by `product-manifest/v1`.

## Editorial collaboration shortlist

These are editorial-fit targets, not partners. Draft only; do not send a product-demo pitch before a
real demo exists.

| Target | Fit | First ask |
|---|---|---|
| The Compound and Friends | Retail-investor market context | Exchange a sourced week-ahead chart or guest reaction |
| Bloomberg Odd Lots | Deep macro/market mechanisms | Offer a primary-source research note, not a product pitch |
| Finimize Daily Brief | Concise what-happened/why-it-matters format | Propose a co-explained portfolio transmission map |
| Real Vision Daily Briefing | Daily macro and cross-asset discussion | Offer a post-event chart pack or specialist guest idea |
| Independent macro newsletters | Direct relationship and faster tests | Cross-link one primary-source calendar or correction explainer |

Draft outreach: “TraderCockpit publishes timestamped, primary-source market maps for self-directed
investors. We are preparing `{TOPIC}` and can contribute a compact source pack plus the cross-asset
transmission map. If that is useful editorially, I can send the one-page brief. No sponsorship or
product placement is implied.”

## Two-week launch calendar

Dates stay blank until `generatedAt` and the release date are verified.

| Day | Asset | Gate |
|---:|---|---|
| -7 | Problem/standard explainer; no product claim | Editorial approval |
| -6 | Source-and-corrections policy | Editorial approval |
| -5 | Real workflow teaser | Release-candidate capture verified |
| -4 | Capability #1 | Manifest claim verified |
| -3 | Limitation/failure-state post | Product limitation verified |
| -2 | Platform/support explainer | Platform and support links verified |
| -1 | Release clock | Real date/time verified |
| 0 | Landing, long-form, two verticals, email | Exact-asset batch approved |
| +1 | FAQ and first corrections | Support facts refreshed |
| +2 | Full workflow cut | Real capture verified |
| +3 | “What it does not do” | Legal/product review |
| +4 | User questions, no testimonials invented | Source comments recorded |
| +5 | Release-week market map; no product pitch in VO | Daily claims gate |
| +6 | Known limitations and roadmap boundary | Product owner approval |
| +7 | Seven-day evidence recap | Metrics complete |

## Plug-in receipt

Before scheduling anything, require: valid manifest; real screenshots/video; reproducible demo flow;
price/date/eligibility/platform/support/refund/limitations; exact claims approval; accessibility check;
claims gate; operator fingerprint; publisher dry run. If any input is absent, only that dependent item
remains blocked.
