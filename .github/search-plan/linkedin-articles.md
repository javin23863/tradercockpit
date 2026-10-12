# LinkedIn drafts (DRAFT; for mike or the coordinator to publish)

Company tagline: **Trading strategy research and education for systematic traders.**

About: *We're building TraderCockpit, a Windows desktop app for trading strategy research, and we publish free guides to backtesting, out-of-sample testing and Monte Carlo analysis. The app is in development and not yet released. Our guides are educational, not financial advice.* Website: https://trader-cockpit.com/?utm_source=linkedin&utm_medium=social&utm_campaign=company-page

Each article takes a different angle from its guide and links to the full guide for the method. Byline: the TraderCockpit company page. Every article ends with the same note: *Educational material, not financial advice. Examples use made-up numbers.*

---

## 1. Worked example: "Same four trades, two different drawdowns"

**Angle:** a worked example with numbers small enough to check by hand. **Full guide:** Monte Carlo Simulation for Trading Strategies.

Take four trades with fixed size: +$60, −$40, +$60, −$40. Start with $1,000. You end at $1,040, and the worst peak-to-trough drop is $40.

Now take the same four trades in a different order: +$60, +$60, −$40, −$40. You still end at $1,040, but the drop is now $80, twice as deep. Nothing about the strategy changed. Only the order did.

That is the question a Monte Carlo reshuffle asks: how much of the drawdown you saw comes from the strategy, and how much comes from the one order history happened to deal you? Shuffle the trade list a few thousand times and you get a range of drawdowns instead of a single number.

Three things the reshuffle can't do:

- **Make up trades you never had.** Shuffling without replacement keeps the total profit fixed. Resampling with replacement changes it, but only by repeating or leaving out trades you already have.
- **Keep streaks real markets produce.** If losses cluster in volatile periods, a plain shuffle breaks that up and makes the risk look smaller. Block resampling keeps short runs of trades together.
- **Promise a worst case.** A 95th-percentile drawdown describes your simulation rules, not the future.

Before you quote a Monte Carlo drawdown, write down what was shuffled, with or without replacement, the block size if any, how many runs, and the position sizing.

Full guide, including the assumptions to record: https://trader-cockpit.com/learn/concepts/monte-carlo.html?utm_source=linkedin&utm_medium=social&utm_campaign=monte-carlo

---

## 2. Common mistake: "When your out-of-sample test stops being out of sample"

**Angle:** the mistake people make, told as a sequence of reasonable-looking steps. **Full guide:** In-Sample vs Out-of-Sample Backtesting.

You hold back the last two years of data. You build on the rest, test once on the held-back years, and the result is mediocre. So you tweak the exit, test again, and it's better. You tweak the filter, and it's better again.

Each step looked reasonable. Between them, the held-back years quietly became development data. The file is still labelled "out-of-sample", but every decision you made after looking at it used it. The final result is an in-sample result with a nicer name.

Three habits that keep a holdout honest:

1. **Decide the pass/fail rule before you open it.** Write down the metric and threshold first.
2. **Count the looks.** If you opened the holdout five times, report five looks, not one.
3. **Keep one more period sealed.** Walk-forward windows or a final untouched period give you something you haven't tuned against.

Cross-validation inside data you've already seen doesn't fix this. It answers a different question.

Full guide, including how to recognise data leakage: https://trader-cockpit.com/learn/concepts/out-of-sample.html?utm_source=linkedin&utm_medium=social&utm_campaign=out-of-sample

---

## 3. Case study: "Reading a screenshot backtest, one question at a time"

**Angle:** a case study that walks one made-up claim through the checklist. **Full guide:** Trading Strategy Backtest Checklist.

A post shows an equity curve: 100 trades, $1,000 gross profit, "works on any market". Here's how we'd read it.

- **Costs.** At an assumed $8 round trip per trade, $1,000 gross becomes $200 net. Add $3 of slippage per trade and it becomes a $100 loss. The screenshot doesn't say which applies.
- **Selection.** How many versions were tried before this one? The best of fifty variations needs a much tougher bar than a single planned test.
- **Held-back data.** Was any period set aside before development and opened once? If not, the whole curve is discovery data.
- **Timing.** Do entries use the bar's close or the next bar's open? A one-bar difference can turn a curve upside down.
- **Comparison.** Did it beat a simple baseline (buy and hold, or random entries of the same size and holding time) chosen in advance?

None of these questions says the strategy is bad. They say what evidence is missing before the curve means anything. "Can't verify" is a valid outcome.

The full checklist, printable on one page: https://trader-cockpit.com/strategy-claim-audit-checklist.html?utm_source=linkedin&utm_medium=social&utm_campaign=backtest-checklist
