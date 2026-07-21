# Analysis Brief — War premium without broad panic — 2026-07-15

shock_class: geopolitical risk premium + supply shock

cutoff: 2026-07-15 15:17 ICT / 04:17 EDT

Feed rule: TradingView supplies prices and levels; official sources supply events. The
2026-07-15 commodity, rates, FX, gold, and VIX bars below were still in progress at the
cutoff. U.S. equity closes are through 2026-07-14.

## 1 What moved

- Brent (`TVC:UKOIL`, 1D) closed 83.31 on July 13 and 85.15 on July 14, then traded
  86.46 at the cutoff. That is a 3.8% extension from the July 13 close, with the current
  session still incomplete.
- XLE confirmed the producer channel: 55.08 on July 10, 56.74 on July 13, and 56.95 on
  July 14. XOM moved 138.88 -> 144.51 -> 145.09 over the same completed sessions. CVX
  moved 176.40 -> 182.20 -> 181.76.
- Broad fear did not confirm. SPX recovered from 7,515.34 on July 13 to 7,543.59 on
  July 14; Nasdaq recovered from 25,873.18 to 26,107.01. VIX eased from 17.16 on July 10
  to 16.50 on July 13 and traded 16.27 at the cutoff.
- The macro gauges were mixed rather than uniformly risk-off: US10Y traded 4.602 after
  a 4.587 July 14 close; DXY traded 100.926 after 100.940; gold traded 4,018.29 after a
  4,052.86 July 14 close.

## 2 Why

Renewed attacks on commercial shipping around Hormuz plus July 14 U.S. sanctions on an
Iran-linked oil/shipping network -> higher perceived transit, insurance, and oil-flow
friction -> Brent reprices first -> energy producers and XLE benefit -> persistent crude
strength can feed inflation-sensitive rates and pressure energy-consuming margins.

Observed event sources: [IMO Council, July 13](https://www.imo.org/en/mediacentre/pressbriefings/pages/imo-council-reaffirms-commitment-to-protecting-vital-shipping-lanes.aspx),
[IMO statement, July 8](https://www.imo.org/en/mediacentre/pressbriefings/pages/imo-secretary-general-condemns-new-attacks-on-ships-in-strait-of-hormuz.aspx),
[U.S. Treasury, July 14](https://home.treasury.gov/news/press-releases/sb0562), and
[OFAC Iran sanctions](https://ofac.treasury.gov/sanctions-programs-and-country-information/iran-sanctions).

## 3 Paid / hurt

- Paid: crude and energy producers. XLE, XOM, and CVX confirmed the first producer
  repricing, although CVX gave back a small part of Monday's move on July 14.
- Hurt mechanism: energy-consuming sectors face higher fuel and transport costs if the
  crude move persists. This is a mechanism to test, not a confirmed sector move in this
  brief; no uncharted company claim belongs in the script.
- Inflation-sensitive assets become the next test. US10Y has not broken above Monday's
  4.624 close, so a full inflation transmission is not yet confirmed.

## 4 Confirmation

- Oil up + XLE/XOM up: **confirmed**. The supply-risk premium reached producers.
- Oil up + US10Y decisively up: **not confirmed**. The yield remains inside the recent
  4.525-4.636 range.
- Scary conflict headline + VIX up + ES/SPX down: **not confirmed**. VIX eased and SPX
  recovered part of Monday's decline.
- US10Y up + gold up: **not confirmed at the cutoff**. Gold reversed lower while the
  yield edged higher.
- Divergence promoted: the story is an energy premium without a broad-panic confirmation,
  not a claim that every portfolio is in a synchronized risk-off move.

## 5 Priced in

The largest producer repricing occurred on July 13: XLE +3.0%, XOM +4.1%, and CVX +3.3%
from their July 10 closes. Brent then extended from 83.31 to 85.15 on July 14 and 86.46
at the cutoff, while XLE added only 0.4% on July 14 and CVX slipped 0.2%. The market has
priced an energy premium; it has not yet priced a coherent broad-risk or rates shock.

The EIA July outlook is only a pre-attack baseline because it was completed July 1. It
cannot prove that normalization is still on track after the July 6-7 attacks.
[EIA July STEO](https://www.eia.gov/outlooks/steo/report/global_oil.php?src=Petroleum-b1)

## 6 Map

These are conditional ranges, not predictions.

- **Base:** Brent holds roughly 83-88, XLE holds 56.3-57.2, and VIX remains below
  17.4-17.6. That is an energy-specific premium with limited broad contagion.
- **Escalation:** a verified new shipping disruption or enforcement action plus a Brent
  daily close above 87.5-88. Confirmation would be US10Y above 4.62-4.64 and/or VIX above
  17.4-17.6 rather than oil moving alone.
- **De-escalation:** an official transit-normalization development plus Brent losing
  83-84 and XLE losing 56.3. Without both the event and chart confirmation, do not call
  the premium unwound.

## 7 Watch next

- EIA Weekly Petroleum Status Report after 10:30 EDT on July 15:
  [official report](https://www.eia.gov/petroleum/supply/weekly/).
- Event-driven IMO incident/transit updates and OFAC/Treasury sanctions updates.
- Primary chart: Brent 1D at 83-84 support and 87.5-88 resistance.
- Confirmation charts: XLE 56.3-57.2, US10Y 4.62-4.64, VIX 17.4-17.6, and SPX
  7,506-7,515 support.

## Feeds

claims:

- Each official event above -> `claims.yaml` candidate from the dated fact pack.
- Every price, percentage, high, low, close, and scenario range -> a timestamped
  `clm-chart-*` candidate from the TradingView 1D feed.
- Partial 2026-07-15 bars must be labeled `as_of` and refreshed before scripting or capture.

charts:

1. `TVC:UKOIL` 1D — 83-84 support; 87.5-88 resistance; current-session status.
2. `AMEX:XLE` 1D — 56.3 support; 57.2 resistance.
3. `NYSE:XOM` 1D — July 10/13/14 producer confirmation.
4. `NYSE:CVX` 1D — July 10/13/14 producer confirmation and minor giveback.
5. `SP:SPX` 1D — 7,506-7,515 support; broad-risk divergence.
6. `NASDAQ:IXIC` 1D — July 13 decline and July 14 recovery.
7. `TVC:US10Y` 1D — 4.62-4.64 confirmation range.
8. `TVC:DXY` 1D — lack of dollar-haven confirmation.
9. `TVC:GOLD` 1D — reversal versus the conflict headline.
10. `CBOE:VIX` 1D — 17.4-17.6 fear-confirmation range.

