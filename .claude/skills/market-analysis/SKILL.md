---
name: market-analysis
description: >
  Run the TraderCockpit repeatable market-analysis brainstorm: classify the day's shock,
  walk the transmission map, cross-asset confirm, and emit analysis-brief.md that feeds
  the script, claims gate, and chart shot list. Use when analyzing a market story, a
  headline's impact, cross-asset moves, or before writing any video/short script.
---

# market-analysis

Doctrine: `MARKET-ANALYSIS-DOCTRINE.md` in the current repo root. Read it first. Resolve all
paths from the active TraderCockpit checkout; never use the former desktop checkout.

## Procedure

1. **Gather facts** — day's fact pack (or build one: headlines with outlet+date, and feed
   levels via the TradingView tools per vault [[TradingView TA Runbook]]). No numbers from
   memory.
2. **Dashboard sweep** — doctrine §1 fixed watchlist, in order, levels off the feed.
   Note anything moving more than noise.
3. **Classify** — doctrine §2 shock taxonomy. One class (two max) per story.
4. **Run the 7-question brainstorm** — doctrine §7, verbatim, in order, in writing.
   Use §3 (transmission map, ≤4 links), §4 (cross-asset confirmation — divergence gets
   promoted), §5 (what's priced), §6 (three scenarios with chart levels + triggers).
5. **Emit `analysis-brief.md`** in the production folder:

```markdown
# Analysis Brief — <story> — <date>
shock_class: <§2 class>
## 1 What moved        <asset, size, TF, feed-read>
## 2 Why               <chain: A → B → C → D>
## 3 Paid / hurt       <winners/losers + mechanism each>
## 4 Confirmation      <pairs checked; confirmed/diverged; divergence promoted? y/n>
## 5 Priced in         <pre-event level vs now; recorded consensus cited>
## 6 Map               <base / escalation / de-escalation — each: level + trigger + source>
## 7 Watch next        <dates, levels, the one chart>
## Feeds
claims: <each factual claim → claims.yaml candidate>
charts: <each §2 link + §6 level → one chart shot, symbol + TF>
```

6. **Hand off** — the brief feeds `daily-news-video` (script written FROM the brief),
   `claims.yaml` (every claim), and the chart shot list. Script may not introduce an
   analytical claim that is not in the brief.

Timebox the dashboard, classification, and seven-question brief to 30 minutes. If a missing fact
or feed prevents a defensible answer, mark the gap and choose another story; do not turn research
into an open-ended production delay.

## Hard rules
- Chart = LEVELS, news = EVENTS. UNVERIFIED numbers banned.
- No predictions; scenarios need triggers. Ranges, never single prices. Not advice.
- Litmus: can't name the affected asset class in one sentence → skip the topic.
