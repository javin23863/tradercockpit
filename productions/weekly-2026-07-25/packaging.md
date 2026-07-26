# Packaging — weekly 2026-07-25

Built against the First Impression System contract: thumbnail promises, title contextualises,
hook confirms — **three layers, zero shared words.**

## Title (published)

> **The Oil Shock Nobody Bought**

Claim-led, not label-led. The restored weekly spec is explicit that
`Stock Market Weekly Review: …` took 3 views while the same week's claim-led short took 58 at
50.9% — so the label form is banned. No word here appears in the thumbnail.

## Thumbnail — `thumb.png`, 1280×720

| field | value |
|---|---|
| eyebrow | `THE WEEK` |
| num | `+11.8%` |
| phrase | `ENERGY GOT *3.36%*` |
| dir | up |

Spec gate **PASS**: 4 words against the 5-word ceiling, leads with a number, 3-colour palette,
contrast and logo corner all within rule.

**Both numbers are receipted.** `+11.8%` is `clm-chart-brent-weekly-2026-07-24`; `3.36%` is
`clm-chart-xle-weekly-2026-07-24`. Neither is rounded press copy — both come off the weekly bar
and appear in the captures.

**Small-size test passed** at 150 px wide: `+11.8%` and `ENERGY GOT 3.36%` both survive; the
eyebrow and the logo drop out, which is the correct outcome — the number and the verdict are
what must read in the feed.

## Why this pairing

The thumbnail is the whole thesis in two numbers with nothing to explain: the barrel did
eleven point eight, the producers got three point three six. A viewer who reads only those two
figures has already understood the video. The title then supplies the interpretation the
numbers do not state — that the market declined to buy the move — and the spoken hook confirms
it in different words again.

## The contract, checked

1. Thumbnail passes the canonical design rules — **yes**, gate PASS at 4 words.
2. Thumbnail, title and spoken hook each say something different about one promise — **yes**:
   numbers / interpretation / consequence, no shared vocabulary.
3. Seconds 0–3 deliver the thumbnail's promise — **yes**, the open now leads with
   *"Brent crude went up almost twelve percent this week and closed at 98.69, and the market
   decided it didn't believe a word of it."*
4. Pattern interrupt, best material front-loaded — **yes**, the four-instrument disagreement
   is stated in the first fifteen seconds rather than held back.
5. Would a viewer who clicked feel the promise was kept? — **yes**. The video's body is that
   divergence measured across six charts. Nothing in the packaging overstates it.

## Derivatives

Not built. `cut_derivatives.py` hard-requires `build/master.mp4`, so verticals wait on the
render. Contract when they are cut: **at most two pre-approval verticals**, more only after the
master is accepted. Shorts covers are skipped by doctrine — in-feed the first frame is the cover.
