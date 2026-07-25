---
name: weekly-market-recap
description: "Produce TraderCockpit's Saturday weekly market recap in the current channel format: the week's important economic and market news, cross-asset conclusions, and the coming week's official catalysts. Use for Saturday videos, weekly market recaps, week-in-review scripts, or next-week market outlook packages."
---

# Weekly market recap

Read `../daily-news-video/SKILL.md`, `../market-analysis/SKILL.md`, `../social-ops-luna/SKILL.md`,
and `../tradercockpit-free-media/SKILL.md` completely. This skill defines only the Saturday delta;
the daily workflow remains authoritative for voice, evidence, production, approval, and publication.

## Format spec (locked — operator ruling 2026-07-18, reaffirmed 2026-07-26)

Runtime **15–20 min**. This overrides the daily's 10–12 min; without it stated here the daily
contract silently applies and the weekly gets scripted at two thirds length.

Word budget is derived, never copied: **runtime × the currently measured clone rate**. Time the
first minute of `build/vo-full.wav` and divide. At the 2026-07-18 rate of 191 wpm the band was
3,100–3,500 words; the voice-v2 reference and `--cfg 0.35` slow delivery, so re-measure before
budgeting. <!-- ponytail: 191 wpm is a measurement of the OLD reference, not a target -->

Pure charts and q-cards. No Godseye, no news shots, no blank charts — weekly charts keep the
standing indicators ON (SR-Dynamic + SMC). Ciovacco-style question-driven skeleton, 15 sections,
alternating question card and answer, proven on `productions/video-03-weekly-2026-07-18`:

| # | section | what it does |
|---|---|---|
| 01 | title-card | defining question + the week's two competing stories + roadmap |
| 02–03 | q-numbers → weekly-numbers | Friday-to-Friday closes off the 1W bars, index by index |
| 04–05 | q-breadth → breadth | did the selling spread — RSP/SPY, small caps, the falsification test |
| 06–07 | q-sectors → sector-ratios | where the money went — XLE, XLY/XLP, SMH/SPX, HYG/IEF |
| 08–09 | q-trend → trend | is the primary trend intact — structure, not the week |
| 10–11 | q-bonds → divergences | what the bond market says — yields, gold, credit, dollar |
| 12–13 | q-verdict → weight-of-evidence | both columns, concern first, then the honest tally |
| 14 | levels-ahead | the lines that trigger each scenario + next week's dated calendar |
| 15 | outro | three-line recap, weekly closes not headlines, subscribe |

Every question card is a real question the viewer would ask, answered immediately in the next
section. Q-cards render via `tools/visuals/qcard.html` through
`render_thumb.cjs --html qcard.html --size 1920x1080`.

## The first 15 seconds (blocking — the measured defect)

The 2026-07-18 edition averaged **14 seconds of watch time at 1.6% viewed** while its own shorts
ran 36–61%. The defining question was in the title but did not land in the script until roughly a
minute in, behind a two-story setup and a roadmap.

- The **defining question lands inside the first 15 seconds**, cold, with its chart already on
  screen. Setup, roadmap and "we'll walk it the same way every Saturday" come after it, or not
  at all.
- Title, thumbnail and that first sentence express **one** promise. If a viewer who clicked would
  feel baited by any of the three, rewrite the open before polishing anything else.
- Title leads with the claim, never the label. `Stock Market Weekly Review: …` took 3 views;
  the same week's `What the week ACTUALLY did` short took 58 at 50.9%. Bind the long-form title
  to whichever claim the week's strongest short is built on.

## Output contract

- Publish no Sunday video. Sunday belongs to analytics and process review.
- Re-derive the completed Monday–Friday week from dated primary sources; do not stitch daily scripts
  together or repeat every headline.
- Explain the week's dominant economic/market mechanisms and the cross-asset confirmation or
  divergence in equities, rates, dollar, credit, commodities, and relevant sectors.
- Build next week's watchlist only from scheduled official releases, central-bank events, earnings,
  policy/legal dates, and known geopolitical catalysts. Separate calendar fact from scenario.
- Use the existing operator voice and visual language. Charts dominate; Godseye appears only when a
  geographic mechanism materially improves the explanation.
- Keep the standard exact-hash approval, claims, source, final-export, and publication gates.

## Procedure

1. Audit the five weekday packages and public receipts, then re-check every retained claim against
   current primary sources. Carry corrections forward explicitly.
2. Run the TradingView dashboard on weekly context. Select only the charts needed to explain the
   week's price action and the levels that matter next week.
3. Write one weekly thesis, three to five supporting mechanisms, a compact cross-asset scorecard,
   and the official next-week catalyst calendar before scripting.
4. Structure the script as: defining take; what changed; why assets reacted; what the market did not
   confirm; next week's dated catalysts; levels or conditions that invalidate the thesis; CTA.
5. Produce and QA through the daily-news-video pipeline. Reuse accepted weekday assets only when
   their timestamp, crop, and narration beat remain correct.
6. Prepare the exact-hash social batch. Publish only with current approval/authentication, preserve
   existing uploads, and update the vault with the weekly receipt.

## Saturday craft rules (learned on the 2026-07-18 build — do not rediscover)

- **No TradingView replay pinning.** The last completed 1W bar *is* the reviewed week. Verify the
  bar time via `ohlcv --count 1` before minting claims; on 07-18 the week-of-07-13 bar close
  matched Friday exactly.
- Ratio symbols work directly as TV symbols on 1W — `AMEX:RSP/AMEX:SPY`, `AMEX:SMH/SP:SPX`,
  `AMEX:HYG/NASDAQ:IEF`, `AMEX:XLY/AMEX:XLP`.
- **The chart is the source of truth for levels; press percentages are not.** They disagree
  because the press quotes a different instrument and window (07-18: UKOIL +17.35% on the chart
  vs "12–14%" in the press, which was Sept futures). Chart-read numbers go on screen; the press
  figure goes in the banned list.
- `claims.yaml` is a top-level LIST; `vo-receipts.yaml` is `{"NN": [{quote, claim, attributed}]}`
  with `quote` a verbatim substring. Ordinals and cardinals ("first", "two thousand") count as
  number regions — rephrase the rhetorical ones, cover the honest ones with sentence quotes.

The Saturday run is an established Luna lane only after its first real end-to-end acceptance passes.
Until then Sol owns it under the `social-ops-luna` delegation gate. After delegation, every weekly
candidate still returns to Sol for final consumer-facing quality control before operator approval.

