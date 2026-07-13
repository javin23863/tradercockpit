# VIDEO #1 — "I Tried to Code ICT. It's Not Even Possible."

**FORMAT REVISED 2026-07-13: FACELESS + AUTOMATED.** Production source of truth =
`productions/video-01/vo.txt` (12 VO sections, Kokoro) + one visual per section in
`productions/video-01/visuals/NN-*.mp4|png`, assembled by `tools/produce.py`.
Target length ~10 min (faceless retention math). A-roll beats below kept as the
narrative skeleton; "you on camera" columns are superseded. Upload with
`publish.py --category 27` (no `--synthetic`: AI-assisted editing/TTS of own
script + own program = not YouTube-disclosable; flag reserved for realistic
synthetic scenes only).

Channel: youtube.com/@Thetradercockpit · Proven demand: Revelio format,
211k views @ 12.9k subs = 16:1 · CTA: https://javin23863.github.io/soical/

**Every number below is verified against on-disk artifacts (fact sheet 2026-07-13).
Do not round up, do not improve. The honesty IS the hook.**

## Title candidates (A/B)

1. **I Tried to Code ICT. It's Not Even Possible. (So I Tested What Is)**
2. I Built a Machine to Test ICT. It Refused.
3. 349,914 Trading Strategies Entered My Machine. Zero Are "Validated" — On Purpose.

Thumbnail: your face + cockpit deck behind, big text "ICT: NOT CODABLE",
crimson on near-black (match landing page palette). No O-face.

## Cold open (A-roll, ≤30s — memorize this one verbatim)

> "This week, 349,914 trading strategies were bred inside my machine.
> 111,966 made it to the starting line. And the number that have earned the
> word 'validated'? Zero. Not because they all failed — because my system
> refuses to say that word until a strategy survives twelve phases of
> statistical torture. But before any of that could happen, I hit a wall
> nobody on trading YouTube talks about: I tried to code ICT… and it turns
> out you literally can't."

## Beat sheet

| # | Time | Beat | A-roll (you) | B-roll (OpenMontage/capture) |
|---|------|------|--------------|------------------------------|
| 1 | 0:00 | Cold open above | talking head, energy | odometer counter animating 349,914 → 111,966 → 0 |
| 2 | 0:35 | Promise: why ICT can't be coded, what CAN be, and the machine that tests it honestly | talking head | cockpit deck pan (JARVIS core) |
| 3 | 1:30 | **Act 1 — the wall.** A strategy must be written as falsifiable rules before it can be tested. ICT, Wyckoff, Elliott, Order Blocks need "swing/structure" definitions so vague that ten traders draw them ten ways. | talking head + screen | show the actual yaml on screen: *"Deliberately absent: Wyckoff, Elliott Wave, Order Blocks, ICT — structural concepts NOT expressible in this vocabulary… Approximating them and keeping the famous name would be a mislabel."* |
| 4 | 3:00 | The line that cuts: "If it can't be written as code, it can't be tested. If it can't be tested, it can't be disproven. And a method that can't be disproven isn't a method — it's a horoscope with a Discord." | punch line to camera | text card |
| 5 | 4:00 | Fairness beat: this isn't "ICT traders are dumb." It's that the *famous name* can't be pinned down honestly. Anyone who says "I backtested ICT" tested *their own interpretation* — a different strategy wearing the name. | talking head | split-screen: 3 different "order block" drawings on same chart |
| 6 | 5:30 | **Act 2 — what IS codable.** Tour the 10 textbook concepts in the library: Donchian breakout/breakdown, golden cross, EMA momentum, RSI mean-reversion, RSI momentum, volatility squeeze, ATR expansion, inside bar, Bollinger mean-reversion. | voice over cards | one motion-graphic card per concept (OpenMontage explainer pipeline), 10–15s each |
| 7 | 8:30 | **Act 3 — the breeding floor.** Each concept × each market × thousands of parameter variants = 8,042 candidates per scope. Funnel: parse → causality check → fixture eval → duplicate-signal kill → replay-twice determinism. 349,914 bred → 225,996 unique survivors → 111,966 admitted. | talking head | cockpit funnel capture + ledger census odometers |
| 8 | 10:30 | Key honesty beat: **"admitted" does not mean "works."** Admitted means "honest enough to be worth torturing." My system calls them UNTESTED until proven otherwise. Compare: every backtest site on earth calls one green equity curve "profitable." | to camera, slow | UNTESTED badge captures from vault |
| 9 | 11:30 | **Act 4 — the gauntlet waiting for them.** 12-phase battery: intake baseline → out-of-sample retest → session-timing stress → cost stress at 2–3× slippage → Monte-Carlo parameter perturbation (200 sims) → Monte-Carlo trade shuffle → walk-forward with frozen params → walk-forward correlation gate → final out-of-sample → governance battery (deflated Sharpe, PBO, CPCV). | energetic walkthrough | landing-page gauntlet animation OR cockpit phase strip; one lower-third per phase |
| 10 | 14:00 | **Act 5 — proof the machine says no.** Real receipt: the sizing gate ran on real Dow data. One config: +129% net improvement, stable across subperiods → ADOPTED. Another: identical +130% headline — REFUSED, because the gains concentrated in too few periods. A third: grading made results 41% WORSE, and the system said so. "A machine that can't say no is a marketing department." | talking head | receipt doc on screen (receipt-sizing-gate-real-run-1.md numbers) |
| 11 | 16:00 | Close + series hook: "The battery starts running on all ten concepts next. Whatever survives, survives. Whatever dies, dies on camera. If someone's charging you $997 for a strategy in my next video's kill list… maybe wait a week." | to camera | subscribe + landing page URL card |
| 12 | 17:00 | CTA: "The landing page runs a mini version of the gauntlet in your browser — link below. And the app itself is paper-only by design. It will never place a trade. It exists to tell the truth." | talking head | gauntlet demo screen capture |

## A-roll cue card (bullets, don't read word-for-word)

1. 349,914 bred / 111,966 admitted / 0 validated — on purpose
2. Tried to code ICT → not expressible → yaml receipt
3. Can't code it → can't test it → can't disprove it → horoscope
4. Fair beat: every "ICT backtest" = someone's private interpretation
5. The 10 that ARE codable (just name 3–4, cards carry the rest)
6. 8,042 per scope; funnel kills dupes + non-determinism; admitted ≠ works
7. 12 phases, name your favorites: cost ×3, MC shuffle, walk-forward, deflated Sharpe
8. Sizing receipts: +129% adopted / +130% refused / −41% confessed
9. Series promise + paper-only line + link

## Shot list (captures needed before edit)

- [ ] Cockpit deck overview (JARVIS core) — 20s slow pan, 1080p+
- [ ] Funnel/pipeline zone with real counts — 30s
- [ ] Vault: strategy cards + UNTESTED badges + odometers — 30s
- [ ] `concept_library.yaml` in editor, scrolled to "Deliberately absent" block — 15s
- [ ] Landing page gauntlet run (full: pick chip → verdict) — 60s screen rec
- [ ] Sizing receipt doc scroll — 15s
- [ ] A-roll: cold open + beats, phone/webcam, plain wall or desk, 3 takes

## Assembly (OpenMontage)

Pipeline: explainer/documentary hybrid. Kokoro VO ONLY for the 10 concept cards
(B-roll narration insert); everything else = your voice. faster-whisper word-level
captions. Master 16:9; shorts cuts: (a) cold open 0:00–0:35, (b) horoscope line,
(c) +130% refused receipt — each 9:16 via `publish.py` to YT/IG/FB when Meta live.

## Description draft

> I built a machine that breeds trading strategies by the hundred thousand and
> tortures them through 12 statistical phases before it will say a single kind
> word. First problem: the internet's favorite strategy can't even enter.
> ICT, Wyckoff, Elliott Wave, Order Blocks — not expressible as falsifiable
> rules, and my system refuses to test a mislabel.
> What CAN be coded: 10 textbook concepts, 349,914 bred variants, 111,966
> admitted to the start line. Validated so far: zero — the battery runs next,
> on camera.
> ⚙️ Try the mini-gauntlet: https://javin23863.github.io/soical/
> 📄 Research instrument, paper-only by design. Not financial advice. No
> performance promised or implied.

Tags: ICT trading, backtest, quant trading, trading strategy tested, ICT strategy,
smart money concepts, algorithmic trading, monte carlo, walk-forward

## Honesty checklist (block release if any fail)

- [ ] "0 validated" always framed as *battery not yet complete*, never "all died"
- [ ] No profit claims, no PnL screenshots, no "edge" promises
- [ ] All counts match fact sheet (349,914 / 225,996 / 111,966 / 46 scopes / 8,042)
- [ ] yaml quote shown verbatim, not paraphrased on screen
- [ ] Paper-only + not-financial-advice in video AND description
- [ ] Sizing numbers exact: +129% adopted, +130% refused (concentration), −41% stated
