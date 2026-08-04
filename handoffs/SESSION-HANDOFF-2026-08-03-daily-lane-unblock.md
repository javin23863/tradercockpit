# Daily lane unblock — voice, browser, insight gate, A6

> **STATUS 2026-08-03 (ET) / 2026-08-04 (local):** code MERGED and PUSHED —
> `c601679` on `fix/news-shot-capture-and-visual-qa-master`, pushed to **`ops`**
> (`34c14c2..c601679`). **No video shipped.** The 20:27 ET run reached the operator's
> real TradingView layout and was refused by a Chrome extension permission. The lane is
> otherwise unblocked: preflight now exits 0.
>
> This wave is **PAUSED, not finished**. One operator click resumes it.

---

## The single thing that resumes this

`productions/daily-2026-08-03` is still owed its content artifacts. The blocker is
**not** in this repo:

```
CHROME_CONTROL_PERMISSION_DENIED
accessDeniedByBrowserPermission : true
targetUrl                       : https://www.tradingview.com/chart/wbXb26vP/
targetTitle                     : "INTC 91.00 ▲ +0.89% main"
```

The agent found the operator's **signed-in saved layout** (`wbXb26vP`, named "main")
and refused to touch it because it could not verify the black theme or the two
indicators. Nothing was changed or captured. Receipt:
`productions/daily-2026-08-03/content-step-receipt-2026-08-04-chrome.json`.

**Operator action (cannot be automated — granting a browser extension access to a tab
is a security boundary):** in Chrome, with the TradingView tab focused, click the
Codex/ChatGPT extension icon and allow access to `tradingview.com`. Grant at **site**
level, not one-tab-once — the layout sits on INTC and the agent must switch symbols.

Then, from `C:\Users\MSI\Documents\tradercockpit`:

```bash
OpenMontage\.venv\Scripts\python.exe tools\daily_lane.py
```

No `--at-production-hour` — that flag stands the lane down outside the 16:00 ET hour,
and this is a catch-up run. `eastern_now()` still resolves to 2026-08-03 until 00:00 ET,
so it resumes the same production folder. After that it mints `daily-2026-08-04`.

---

## What changed and why (the traps)

**1. The lane was handing the agent a logged-out browser.** `ensure_tradingview()`
launched the lane's OWN Chrome profile on CDP `:9222`. That profile was never signed
into TradingView, so the content agent took the browser that was in front of it and
found `BATS:AAPL` with `Volume` only. It correctly refused — on 07-29, 07-30, 07-31 and
08-03. **The decoy was the defect, not TradingView.** Codex reaches the operator's real
Chrome through its own extension (`hehggadaopoacecdllhhajmbjkdcmajg`, backends
`chrome,iab`). The launcher is deleted.

**2. A preflight row that could not observe its subject is worse than no row.** The
TradingView check tested only whether port 9222 was open — so it would have reported
PASS on the decoy while the real chart went unchecked. Deleted with the launcher. Chart
eligibility now lives in the agent prompt, which names the unauthenticated feed prefixes
(`BATS:`, `SP_NAUTH:`, `NASDAQ_DLY:`) as refusal triggers.

**3. Speaking rate is a property of the VOICE, so the word budget moves with it.** The
lane moved to Higgsfield Marcus (included Max credits, ~1.2 of 3,530 a night) because
the ElevenLabs Creator tier had 18,051 chars against a 10,332 night and no reset until
08-27 — one more night, then a 23-day stall. Marcus measures **198 wpm**, so the band is
**2,000–2,350 words**. That is what actually shipped at this rate: 07-20 was 2,029 words
/ 10.0 min / 202 wpm, 07-21 was 2,202 / 10.9 / 202. The 1,450–1,700 @ 145 band belongs
to the ElevenLabs clone and now applies only on that fallback route. Left in place it
would have shipped an 8-minute video against a 10–12 min ad floor.

**4. The strongest quality rule in the vault was prose wearing a gate's citation.**
`GTM/Pipeline/Video Format v2 — StockedUp Model.md` cited "Machine enforcement:
`MARKET-ANALYSIS-DOCTRINE.md` §0.05". **There is no §0.05**, and no reference to the
insight bar existed anywhere in `tools/` or the skills. Eleven gates ran on the daily and
none asked whether the claim was worth making — which is how "boring, surface-level"
passed a clean gate stack on 07-27. `tools/insight_gate.py` now hard-fails in
`daily_postclose.collect_gates`. The vault note carries a dated amendment.

**5. A6 needed no schema change.** The plan called it a claims-schema problem. It is not:
each claim's receipt already records its timeframe (`swing-receipts-*.json` stamps
`params.timeframe`; ohlcv-feed receipts are settled session bars by construction). Levels
key by `(symbol, timeframe)` **only once a symbol is charted at more than one**, so
single-TF nights are unchanged. Also fixed latent: `swing_levels.py --tf 1W` wrote the
daily's filename and would have silently overwritten it.

**6. Four failed nights were silent** because `notify()` had been reduced to log-only.
Restored, catching `SystemExit` as well as `Exception` — `notify_telegram` raises the
former, and without that a blocked lane exits 0 through the alert path and reads as a
clean night.

---

## Stated ceilings

- **`insight_gate`'s `answer` and `move` lines are DECLARATIONS**, written by the same
  pass that writes the brief. A writing agent can satisfy both by typing the expected
  words. The load-bearing check is the **comparison** requirement (thesis names ≥2
  instruments that are `subject`s in `claims.yaml`) — the half word choice cannot fake.
  The mandatory second-model critic still owns the judgment half. This is documented in
  the module docstring; do not let a future reader over-trust the weak half.
- **198 wpm rests on a 19-word smoke** (`job 18d03139`) plus the 202 wpm precedent from
  two shipped masters. The first full run should be measured; `tts_higgsfield` prints the
  correction and a `--speech-rate` knob exists. Do not tune it before there is a real
  measurement.
- **`insight_gate` has never seen a live brief.** If it blocks the first run, read the
  brief before assuming a bug — a block on a real recap is the gate working.
- The shipped `daily-2026-07-27` brief clears the comparison check (NVDA + VIX) but
  predates the `Insight-bar move:` field, so it blocks on that line alone. Expected.
- **Post-reopen bars:** after ~18:00 ET (indices/US10Y feeds) and 20:00 ET (energy), the
  native last bar is a live stub, not the settled session. Cash symbols keep a settled
  daily bar. Standing rule is unchanged — drop the asset, never claim it off a stub.
- `pagefile AutomaticManagedPagefile=False` is still WARN, but it is **no longer the TTS
  risk it was**: `OSError 1455` was a local-model failure (Chatterbox loading 4–5 GB).
  Marcus is an API call and does not touch that path.

## Coordination

- **6 unpushed commits sit on `codex/series-quality-system`** (another session's series-
  quality wave) — not touched here, still on one disk.
- 8 files were already dirty in this checkout when the wave started (`ai_writing_gate`,
  `cut_derivatives`, `episode_gate`, `generate_series_higgsfield_narration`,
  `promote_daily`, `script_arc_gate`, `social_batch`, `thumb_gate`, plus two skills).
  **Deliberately not committed** — they belong to other waves.
- `generate_series_higgsfield_narration.py` is **read-only from the daily lane**: its
  sha256 is bound into the Episode 4 approval receipts. `tts_higgsfield` imports its
  constants rather than editing or copying it.
- `daily_lane.py` and `daily_postclose.py` were restored to **LF**; uncommitted work had
  flipped them to CRLF against a repo that pins `* -text`.

## Verification

```
insight_gate      8/8      editorial_gate A6   2/2
daily_preflight   8/8      tts_higgsfield      5/5
daily_lane        4/4      claims_gate        11/11
swing_levels      8/8
```

Regression: `daily-2026-07-27` level-binding PASS and spoken/visible PASS, unchanged.
Live preflight exits 0 (WARN on pagefile only). Local `pytest` is blocked by the
no-local-compute hook; every check above is an in-module selftest run directly.
