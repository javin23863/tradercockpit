# Indicator-confluence primary-source research

Date: 2026-07-30  
Scope: TradingView screening for RSI, MACD, DMI/ADX, and LuxAlgo premium/equilibrium/discount context. This note defines indicator semantics and a testable research hypothesis; it does not recommend trades.

## Bottom line

The proposed alignment is coherent as a **user-defined regime hypothesis**, not a documented market law:

- RSI 60 is not TradingView's standard bullish/bearish threshold. TradingView documents Wilder's 70/30 overbought/oversold levels, a neutral 30–70 range, and approximately 50 as “no trend.” A 60 threshold therefore needs instrument-, asset-class-, timeframe-, and session-specific validation.
- MACD 7/28/7 means a 7-period fast average minus a 28-period slow average, smoothed by a 7-period signal average. Its crossovers, zero-line position, and divergences describe momentum relationships; they do not by themselves establish a reliable entry or exit.
- ADX measures trend strength, not direction. +DI and −DI provide direction. Calling the colored DI lines “money flow” would be technically inaccurate unless the chart uses a different, explicitly volume-based indicator.
- LuxAlgo's upper **premium**, central **equilibrium** (not “equity”), and lower **discount** areas provide location. LuxAlgo says a bullish condition in discount or a bearish condition in premium has a higher chance of causing a reversal, and that the areas can act as support or resistance. The zone alone is not a direction signal.

The regular Stock Screener is useful for a coarse first pass. Reproducing the exact confluence requires one Pine Screener-compatible script that calculates and exposes every required state.

## TradingView screening support and limits

TradingView's Stock Screener supports technical filters, including oscillators, and specifically documents expanded parameters for RSI and several other studies. Its built-in Oscillators Rating includes RSI (14), ADX (14, 14), and MACD (12, 26, 9). The rating reduces them to simple states: RSI uses 30/70 plus direction, ADX combines DI ordering with ADX above 20 and rising, and MACD compares its main and signal lines. This is not the same as RSI 60, MACD 7/28/7 divergence, DMI color/pressure interpretation, or LuxAlgo zone confluence. ([Stock Screener](https://www.tradingview.com/support/solutions/43000718866-tradingview-stock-screener-trade-smarter-not-harder/); [Screener ratings](https://www.tradingview.com/support/solutions/43000475547-what-do-the-ratings-in-the-screener-mean/))

TradingView's Pine Screener can scan a watchlist using a personal Pine script, a built-in indicator, or a favorited public-library indicator. Filters can use the selected indicator's plots and alert conditions. Relevant documented constraints are:

- one indicator per screen;
- only the first ten plots and two alert conditions are initially exposed;
- only the selected script's plots can become table columns;
- no indicator-on-indicator calculations;
- supported chart intervals only: 1, 5, 15, and 30 minutes; 1, 2, and 4 hours; 1 day; 1 week; and 1 month;
- at most five distinct `request.*()` calls, using supported timeframes;
- one scan running at a time; and
- calculations use only the latest 500 bars.

Therefore the smallest exact scanner is a single Pine indicator that computes all components internally and outputs bounded Boolean/numeric plots such as `rsi_regime`, `macd_state`, `divergence_state`, `di_direction`, `adx_strength`, and `location_state`. The 500-bar calculation ceiling makes Pine Screener suitable for finding current candidates, not proving the historical edge. ([Pine Screener requirements](https://www.tradingview.com/support/solutions/43000742436-tradingview-pine-screener-key-features-and-requirements/))

## Standard semantics versus the hypothesis

### RSI

TradingView defines RSI as a 0–100 momentum oscillator. Its cited standard interpretation is above 70 overbought, below 30 oversold, 30–70 neutral, and around 50 “no trend”; it also says traders may alter ranges at their discretion. Thus “below 60 lacks enough strength to push upward and usually trends down” is a legitimate rule to test, but not a standard RSI definition. The test must distinguish `RSI < 60`, a cross below 60, failure to reclaim 60, and the slope of RSI because those are different events. ([TradingView RSI](https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/))

### MACD 7/28/7 and divergence

TradingView defines:

```text
MACD = fast MA − slow MA
Signal = moving average of MACD
Histogram = MACD − Signal
```

For 7/28/7, those lengths are fast 7, slow 28, and signal 7; the MA type still matters. MACD above zero means the fast average exceeds the slow average. MACD above its signal, or a positive histogram, indicates increasing upward momentum or decreasing downward momentum; the inverse applies below the signal.

TradingView describes regular divergence as possible trend weakening/reversal and hidden divergence as possible trend continuation. Its language is deliberately conditional (“might,” “suggesting,” “possible”), and its separate divergence guidance says divergence should not be used alone and is not present at every reversal. A reproducible test must define the pivot algorithm, lookback, confirmation delay, regular versus hidden class, and whether signals are accepted only after bar close. ([TradingView MACD](https://www.tradingview.com/support/solutions/43000502344-moving-average-convergence-divergence-macd-indicator/); [TradingView divergence limitations](https://www.tradingview.com/support/solutions/43000589127-rsi-divergence-indicator/))

### DMI/ADX

DMI combines ADX, +DI, and −DI. TradingView states that ADX indicates whether a trend is present but has no direction; +DI above −DI indicates bullish direction, while −DI above +DI indicates bearish direction. Wilder's general strength guide is ADX above 25 for a strong trend, below 20 for weak/nonexistent, and 20–25 indeterminate. TradingView explicitly says those thresholds depend on the instrument and should be historically analyzed. Rising ADX means the current directional trend is strengthening, not necessarily that price is rising.

The “green positive / red negative / purple pressure” interpretation is safe only after mapping colors to actual series: if green and red are +DI and −DI, they measure directional movement derived from price and ATR, not money flow; if purple is ADX, it measures magnitude of trend strength without direction. ([TradingView DMI](https://www.tradingview.com/support/solutions/43000502250-directional-movement-dmi/))

### Premium, equilibrium, discount, support, and resistance

LuxAlgo defines premium as the upper area, equilibrium as the central area, and discount as the lower area. It says an uptrend condition occurring in discount has a higher chance of causing a reversal, with the inverse for a downtrend condition in premium, and says each area can serve as support or resistance. This supports using location as context for already-defined momentum/trend conditions; it does not establish that discount means buy or premium means sell. ([LuxAlgo Premium & Discount Zones](https://docs.luxalgo.com/docs/algos/price-action-concepts/pdzones))

## Minimum evidence needed before calling the alignment historical

Freeze these definitions before scanning or backtesting:

1. symbol universe and asset class;
2. chart timeframe, session, and closed-bar rule;
3. RSI length and whether 60 is a state, cross, failed reclaim, or slope condition;
4. MACD MA types, 7/28/7 lengths, divergence class, pivot/lookback rules, and confirmation delay;
5. DMI/ADX lengths, minimum ADX, and what “purple pressure” means numerically;
6. the exact premium/equilibrium/discount and support/resistance implementation, plus boundary tolerance; and
7. separate in-sample calibration and out-of-sample evaluation, including signal count, forward returns, drawdown/adverse excursion, fees, and results by asset class.

Until those are fixed and tested, the alignment should be described as a candidate confluence filter, not a validated buy/sell system.
