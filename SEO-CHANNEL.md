# TraderCockpit — channel SEO pack

Channel: youtube.com/@Thetradercockpit · Apply via `tools/channel_seo.py`
(needs one-time re-consent — broader `youtube` scope than upload token).

## Channel description (applied by script)

> Every trading strategy the internet sells you — coded honestly and executed
> through 12 phases of statistical torture. ICT, SMC, supply & demand, price
> action: if it can be written as falsifiable rules, it enters the gauntlet.
> Monte-Carlo shuffles, walk-forward, cost stress at 3x slippage, deflated
> Sharpe — whatever survives, survives. Whatever dies, dies on camera.
>
> No signals. No courses. No lambo. A research machine that refuses to say
> "validated" until the receipts exist — and publishes the kill list either way.
>
> Research instrument, paper-only by design. Nothing here is financial advice
> and no performance is promised or implied.
>
> 🧪 Run the mini-gauntlet: https://javin23863.github.io/soical/

## Channel keywords (applied by script)

trading strategy backtest, ICT trading tested, smart money concepts, SMC,
quant trading, algorithmic trading, monte carlo trading, walk-forward analysis,
backtest overfitting, futures trading, trading strategy tested, honest backtest

## Per-video SEO templates

**Title patterns** (pick per video, ≤60 chars visible):
- "I Tried to Code [X]. It's Not Even Possible."
- "I Coded [X] and Tested [N] Variants. Honest Numbers."
- "[N] Strategies Entered. Watch Phase [K] Kill Them."
- "Why Your [X] Backtest Is Lying To You"

**Description skeleton** (first 2 lines = search snippet, front-load keywords):
```
[Keyword-rich one-liner restating the title claim with numbers.]
[Second line: the honest verdict/counts.]

⏱ Chapters
00:00 [hook]
...

🧪 Run the mini-gauntlet in your browser: https://javin23863.github.io/soical/
📊 The machine: 12-phase robustness pipeline — MC shuffle, walk-forward,
cost stress, deflated Sharpe. Paper-only research instrument.

Research/education only. Not financial advice. No performance promised.
```

**Tags** (12–15 per video): mix 3 exact-match ("ict strategy tested"),
5 category ("quant trading", "backtesting", "algorithmic trading"),
4 long-tail from the video's claim ("monte carlo trade shuffle",
"walk forward analysis explained"), 2 brand ("tradercockpit", "trader cockpit").

**Category:** 27 (Education) — not 22. Set `--category 27` in publish.py.

**Chapters:** always — timestamps from produce.py sections.json map 1:1.

## Playlists (create as videos land)

1. "The Gauntlet — strategies executed on camera" (series spine)
2. "Why backtests lie" (methodology explainers)
3. "Receipts" (short verdict clips)

## Pinned comment template

> The config file that bans ICT from the arena + all counts in this video are
> real artifacts. Mini-gauntlet you can run yourself: [landing URL]. What
> strategy should enter next? Kill list is built from these comments.

## Notes

- Handle @Thetradercockpit ≠ display name. Display name should be
  "TraderCockpit" (set in YouTube Studio — API can't change display name).
- Upload cadence beats everything: algorithm needs 5–8 uploads to find the
  audience pocket. Judge faceless format only after that.
- Shorts carry channel discovery early: 2–3 shorts per long-form, each ending
  with the long-form hook.
