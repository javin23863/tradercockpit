# TraderCockpit — channel SEO pack

Channel: youtube.com/@Thetradercockpit · Apply via `tools/channel_seo.py`
(needs one-time re-consent — broader `youtube` scope than upload token).

## Channel description (applied by script) — REVISED 2026-07-13, news-first pivot

> A machine that watches markets in near-real-time and reports what matters — asset
> classes, indices, and the geopolitics moving them, translated into what it means
> for your portfolio. Oil, equities, rates, currencies, chokepoints: if it moves
> markets, the machine tracks it and says so plainly.
>
> No signals. No courses. No lambo. Nothing here is financial advice and no
> performance is promised or implied — this is a news instrument, not a trading
> service.
>
> 🧪 Explore the simulated product preview: https://javin23863.github.io/tradercockpit/

## Channel keywords (applied by script) — REVISED 2026-07-13, news intent

market news today, stock market news, oil price, strait of hormuz oil,
geopolitics markets, S&P 500 analysis, futures market, portfolio, economic
news today, market impact analysis, oil futures, geopolitical risk markets

## Per-video SEO templates

**Title patterns** (pick per video, ≤60 chars visible) — REVISED 2026-07-13, news-first:
- "[Event]: What It Means For Your Portfolio"
- "The Machine Watched [X]. Here's What Matters."
- "[Asset/Index] Today: The [N]-Second Verdict"
- "Why [Event] Is Moving [Market] Right Now"

**Description skeleton** (first 2 lines = search snippet, front-load keywords) — REVISED 2026-07-13:
```
[Keyword-rich one-liner: what happened + why it moves markets.]
[Second line: what it means for your portfolio, plainly.]

⏱ Chapters
00:00 [hook]
...

📡 TraderCockpit publishes market analysis and the evidence behind it.
🧪 Simulated product preview: https://javin23863.github.io/tradercockpit/

News/education only. Not financial advice. No performance promised.
```

**Tags** (12–15 per video): mix 3 exact-match ("ict strategy tested"),
5 category ("quant trading", "backtesting", "algorithmic trading"),
4 long-tail from the video's claim ("monte carlo trade shuffle",
"walk forward analysis explained"), 2 brand ("tradercockpit", "trader cockpit").

**Category:** 27 (Education) — not 22. Set `--category 27` in publish.py.

**Chapters:** always — timestamps from produce.py sections.json map 1:1.

## Playlists (create as videos land) — REVISED 2026-07-13, news-first

1. "Today in Markets" — daily news spine: what moved, why, and what it means
   for your portfolio.
2. "Chokepoints" — geopolitics deep-dives on the flashpoints moving oil,
   indices, and rates.
3. "The Gauntlet — product concepts explained" (evergreen education lane,
   not the daily spine).

## Pinned comment template — REVISED 2026-07-13, news framing

> Sources and observation times are listed with the video. What should we examine
> next? Drop the asset, index, or region below.

## Notes

- Handle @Thetradercockpit ≠ display name. Display name should be
  "TraderCockpit" (set in YouTube Studio — API can't change display name).
- Evaluate formats against the channel's own retention and referral data.
- Reuse long-form evidence in short clips when the claim and context survive the edit.
