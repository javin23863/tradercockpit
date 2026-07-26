# Fact Pack Research — 2026-07-24

## Candidate headline

**Oil Fell Below $100. Why Friday Still Wasn't Risk-On.**

The cleanest session story is divergence, not direction. Brent's settlement fell back below
$100 and Treasury yields eased, but that macro relief did not produce a broad technology
rally. The S&P 500 finished almost flat and the Dow rose, while the Nasdaq composite fell.
Inside technology, Apple rose sharply while Micron fell.

## Final close facts

Associated Press final index recap, published 2026-07-24T20:36:04Z:

- S&P 500: 7,411.98, up 3.68 points, less than 0.1%.
- Dow Jones Industrial Average: 51,947.25, up 235.60 points, 0.5%.
- Nasdaq composite: 24,975.82, down 161.87 points, 0.6%.
- Russell 2000: 2,930.00, down 10.16 points, 0.3%.
- All three major indexes finished the week lower.
- Brent crude fell almost 4% to settle at $96.78 after reaching $102 a barrel the prior day.
- Treasury yields moved lower.

Source:
https://apnews.com/article/02d01b8f38ccd51f605c4414cdd4fa9b

The AP session story reported that worries about whether heavy AI investment would produce
profits sufficient to justify large valuations remained in focus. It identified Micron and
Broadcom as major reasons the Nasdaq lagged during the session. The article's body available
at retrieval time still contained an 11:50 a.m. market snapshot, so it is used for event
context and named-driver attribution, not final prices.

Source:
https://apnews.com/article/stocks-markets-tariffs-oil-trump-ai-0b9c3b2aa5ca83eb391c1388efe03c97

A Reuters-syndicated session report described the same selectivity: concern over AI spending
and cash burn weighed on technology, the Philadelphia semiconductor index fell, and real
estate led the S&P 500 sectors. Because that report was updated before the closing bell, it
supports the mechanism and breadth context only.

Source:
https://in.marketscreener.com/news/wall-st-set-for-higher-open-after-tech-rout-mideast-tariffs-in-focus-ce7f51dfdc81f12c

## Completed-session TradingView observations

These figures come from TradingView 1D main-series bars stamped
2026-07-24T13:30:00Z. All accepted captures show the regular cash-session close. Post-market
quotes visible in single-name side panels are excluded.

- SP:SPX — O 7,406.30; H 7,460.98; L 7,396.53; C 7,411.98; prior C 7,408.30.
- DJ:DJI — O 51,791.37; H 52,118.19; L 51,682.36; C 51,947.25; prior C 51,711.65.
- NASDAQ:AAPL — O 321.79; H 334.37; L 321.62; C 333.02; prior C 321.66.
- NASDAQ:MU — O 959.03; H 967.14; L 904.00; C 920.95; prior C 990.21.
- NASDAQ:AVGO — O 387.68; H 389.27; L 378.75; C 381.92; prior C 392.47.
  This valid capture was researched but not selected for the story.

Derived, reproducible arithmetic:

- SPX return: (7,411.98 - 7,408.30) / 7,408.30 = +0.0497%, displayed as +0.05%.
- DJI return: (51,947.25 - 51,711.65) / 51,711.65 = +0.4556%, displayed as +0.46%.
- AAPL return: (333.02 - 321.66) / 321.66 = +3.5317%, displayed as +3.53%.
- MU return: (920.95 - 990.21) / 990.21 = -6.9945%, displayed as -6.99%.
- SPX closed 15.45 points above its low inside a 64.45-point range, or 24.0% up
  from the low.
- MU closed 16.95 dollars above its low inside a 63.14-dollar range, or 26.8% up
  from the low.
- AAPL closed 1.35 dollars below its high inside a 12.75-dollar range.

Receipts:

- `ohlcv-feed-receipts-2026-07-24.json`
- `chart-capture-receipts.json`
- `chart-qa.md`

## Rejected captures

- NASDAQ:NDX — the image retained a current-bar countdown and said `Market open`.
- TVC:UKOIL — the image retained a countdown and said `Market open`; its CFD quote also
  did not equal AP's Brent settlement.

Both receipts are preserved, but neither image is working evidence and neither may be cited
as a chart in the script.

## Mechanism

Observed chain:

oil and yields eased -> one macro pressure on equities eased -> broad indexes did not move
as one block -> Micron remained weak while Apple rose -> the session
finished as a selective tape rather than a clean risk-on reversal.

The sources support continued concern about AI spending and profit conversion. They do not
prove a single cause for every stock move. The analysis should keep the Apple and Micron
bars as observed relative-strength evidence and avoid assigning undocumented
investor motives.

## Portfolio transmission

- Broad S&P exposure: almost unchanged on the day, but the close sat near the lower quarter
  of the captured session range.
- Dow exposure: positive close despite the mixed tape.
- Micron exposure: a direct loss despite lower oil and yields.
- Apple exposure: strong positive outlier inside a weak technology backdrop.
- Oil exposure: AP reported a lower settlement, reversing part of Thursday's surge.

## Next scheduled catalysts

- Federal Reserve: two-day FOMC meeting July 28-29, with the statement at 2:00 p.m. and
  press conference at 2:30 p.m. Eastern on July 29.
  https://www.federalreserve.gov/newsevents/calendar.htm
- BEA: advance Q2 GDP and June Personal Income and Outlays, including PCE price data, both
  scheduled for July 30 at 8:30 a.m. Eastern.
  https://www.bea.gov/news/schedule/

## Draft decision map

- Base: SPX remains inside 7,396.53-7,460.98 while MU remains inside
  904.00-967.14. Friday's selectivity persists.
- Broadening: SPX closes above 7,460.98 while MU closes above 967.14. Macro relief would
  then have broader chart confirmation.
- Breakdown: SPX closes below 7,396.53 while MU closes below 904.00. The mixed tape would
  become a broader risk-off move.
- Partial: only one of SPX or MU clears its required boundary. Selectivity remains until
  both required closes occur.
- Counterexample: AAPL's 334.37 high and 321.62 low define whether Friday's relative
  strength persists or fails.

These are conditional closes from accepted charts, not forecasts.
