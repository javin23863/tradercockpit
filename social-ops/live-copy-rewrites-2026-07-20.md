# Live copy rewrites — 2026-07-20

Every published title/caption audited against the doctrine that did not exist when they shipped:
[[Channel SEO]] (keyword in first ~60 chars, ≤100 total, front-loaded, one dominant number),
[[Script Voice Guide]] (no slogans, no corrective contrast, concrete over abstract), and the
rebuilt `tools/script_style_gate.py`.

**Two of these are live defects, not polish.** Ranked by that first.

---

## P0 — TikTok published a FILENAME as the caption

| | |
|---|---|
| **Live now** | `clip-002-do-not-trade-the-siren.vertical` |
| **Views** | 0 |
| **Cause** | The exact documented failure in `tools/handoff/tiktok_post_cdp.cjs`: *"TikTok prefills the FILENAME, and does it LATE… clearing once races the prefill."* The clear-verify-retry guard exists in that script precisely because this happens — this post predates or bypassed it. |
| **Fix** | Replace the caption. Content is the "don't trade the siren" clip. |

**Replacement caption:**
> Oil ripped 10% on a 20% Hormuz toll. The move that mattered wasn't the headline — it was $83 crude landing in producer earnings. Exxon +4%, Chevron +3% same day. #oil #hormuz #energystocks #stockmarket #FinTok

*Note: uses its one permitted corrective contrast. If the style gate flags it, drop "wasn't the headline — it was" and lead with the number.*

---

## P1 — Pre-playbook slogan titles still live on YouTube

The old style gate hardcoded exactly two slogans: **"pressure chain"** and **"siren"**. Both are in
a live title. This is the single clearest piece of pre-doctrine verbiage on the channel.

| Live title | Views | Problem | Rewrite |
|---|---|---|---|
| `Don't Trade the Siren. Trade the Pressure Chain. #Shorts` | 44 | Both banned slogans; abstract slogan substituting for a mechanism; no number; no asset named | `Oil +10%, Energy +4%: What Actually Moved #Shorts` |
| `The market is pricing the Strait, not the end of the world #Shorts` | 21 | Corrective contrast in a title; no number; "the market is pricing" is vague authority-adjacent | `5 Tankers vs 130 a Day: What Hormuz Actually Closed #Shorts` |
| `The Nasdaq Broke. The S&P Held.` | 14 | No number in the first 60 chars; no level; reads as a headline with no evidence | `Nasdaq Broke 7431, S&P Held Its Band — The Divergence` |
| `Iran Oil Deadline Day Meets a Cracking AI Trade` | 18 | No number; "cracking AI trade" is unsupported characterisation | `Iran Deadline Day and TSMC's $403.50 Floor` |
| `Iran War Widens as Oil Holds $84` | 5 | Number present and front-ish, but "war widens" is characterisation we cannot source | `Oil Holds $84 as the Risk Premium Sticks` |

**Already compliant — do not touch:**
- `Trump's 20% Hormuz Toll Sent Oil +10% 🛢️ #Shorts` (89 views — the best performer, and the most
  number-forward title on the channel. That correlation is worth noting.)
- `TSM's 403.50 Floor Is Being Tested` (ticker + level, front-loaded)

---

## P2 — Descriptions and pinned comments

Unverified from cached artifacts — needs a live read. Doctrine ([[Channel SEO]]) wants: ≤5,000
chars, dated source links, the landing/profile link, chapters matching accepted master timing, and
**no product pitch** on the news/education lane. Pinned comments are a free surface currently
unused across all 14 YouTube posts.

---

## What the data says, separate from the copy

**TikTok is the working channel and is being under-served.** Its top clip has **568 views** against
**89** for the best YouTube video — 6×, from 6 posts vs 14. [[Creator Career — Modern Millie]] names
TikTok→YouTube as the strongest pairing and warns Instagram→YouTube converts poorly. Current effort
allocation is inverted relative to observed results.

**Instagram captions are already the strongest copy on any surface** — concrete levels, real
numbers, a stated read. They post-date the playbooks. Facebook mirrors them at 0–3 views, which is
the "reframe natively, never blind-crosspost" rule being violated in practice.

---

## Application constraints

- Video title/description edits are **recoverable** and doctrine encourages repackaging
  ("repackage don't repost", "never erase weak-but-factual uploads") — these are edits, never
  deletions.
- **Profile edits** (name, avatar, bio, category) require exact-copy approval plus interactive
  platform authorization per [[Channel SEO]] — those are prepared separately, not applied here.
- Every rewrite above must pass `tools/script_style_gate.py` before it is applied.
