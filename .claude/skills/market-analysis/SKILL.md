---
name: market-analysis
description: >
  Run the TraderCockpit repeatable post-close market-analysis brainstorm: classify the shock the
  session delivered, walk the transmission map, cross-asset confirm on settled prints, and emit
  analysis-brief.md that feeds the script, claims gate, and chart shot list. Use when analyzing
  the day's close, a headline's realized impact, cross-asset moves, or before writing any
  video/short script.
---

# market-analysis

Doctrine: `MARKET-ANALYSIS-DOCTRINE.md` in the current repo root. Read it first. Resolve all
paths from the active TraderCockpit checkout; never use the former desktop checkout.

## Procedure

The daily publishes 17:00 US/Eastern, after the 16:00 cash close. The subject is what the session
DID — settled closing prints, not intraday guesses or an open that hasn't happened. Run this after
the close; every level is a settled or official close unless labelled otherwise.

1. **Gather facts** — the closed session's fact pack (or build one: headlines with outlet+date, and
   settled closing levels via the TradingView tools per vault [[TradingView TA Runbook]]). No numbers
   from memory.
2. **Dashboard sweep** — doctrine §1 fixed watchlist, in order, closing prints off the feed.
   Note what closed more than noise away from the prior close, plus closing internals and sector
   breadth (what led, what lagged, how broad the move was).
3. **Classify** — doctrine §2 shock taxonomy, applied to what the session delivered.
   One class (two max) per story.
4. **Run the 7-question brainstorm** — doctrine §7, verbatim, in order, in writing.
   Read each question retrospectively: what did this do to the tape today, and what does the
   close set up for the next session. Use §3 (transmission map, ≤4 links — which links actually
   fired today), §4 (cross-asset confirmation on closing prints — did the confirm hold into the
   bell; divergence gets promoted), §5 (what was already priced going in), §6 (three forward
   scenarios with chart levels + triggers, anchored to today's close).
5. **Emit `analysis-brief.md`** in the production folder:

```markdown
# Analysis Brief — <story> — <date>
shock_class: <§2 class>
## 1 What moved        <asset, size on the close, TF, feed-read; sector breadth + closing internals>
## 2 Why               <chain: A → B → C → D — the links that actually fired today>
## 3 Paid / hurt       <winners/losers on the close + mechanism each>
## 4 Confirmation      <pairs checked on closing prints; confirmed/diverged into the bell; divergence promoted? y/n>
## 5 Priced in         <pre-event level vs the close; recorded consensus cited>
## 6 Map               <base / escalation / de-escalation from here — each: level + trigger + source>
## 7 Watch next        <next session: dates, levels off today's close, the one chart>
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
