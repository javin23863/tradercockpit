# TraderCockpit — Growth Authority Playbook

**Purpose.** One governing doctrine for the channel, per platform, grounded in *the* recognized
authority for that platform — not blog-spam. Each authority is confirmed by ≥2 independent sources
that point at the same reference. The **distilled rules** at the end of each section are the
checklist the `daily-news-video` skill treats as mandatory input for every video and every post.

Updated 2026-07-14. Niche: trust-first finance news (oil, equities, rates, geopolitics → portfolio).
Unified handle everywhere: **@thetradercockpit**.

---

## 1. YouTube — authority: **Paddy Galloway**

The most-sought YouTube strategist working today; clients include MrBeast, Ryan Trahan, Jesser,
Noah Kagan; ~10B views generated. His thesis: **packaging (idea + thumbnail + title) and retention
are the load-bearing variables** — most channels under-invest in the idea and its packaging and
over-invest in production.

**Cross-references converging on Galloway (multiple entities, one reference):**
- CNBC, "Meet the YouTube whisperers … behind MrBeast and other million-dollar channels" (May 2026).
- Creator Science podcast #152 and #209 (two separate deep-dives naming him "most sought-after").
- Colin & Samir, "The New Rules of YouTube From Paddy Galloway."
- Storyboard18, "YouTube strategists emerge as creators' secret weapon."

**Official corroboration:** YouTube Creator Insider / Liaison emphasizes viewer satisfaction over
raw watch time.

### Distilled rules (enforce)
- **Package before you produce.** Decide the ONE idea, draft the thumbnail, write the title —
  *before* cutting the video. If the thumbnail+title don't make you want to click, re-do the idea.
- **Retention is front-loaded.** Earn the first 30 seconds; open on the payoff/stakes, not a ramp.
- **One clear subject per video.** No second topic competing for the click.
- **Niche consistency.** Stay in the markets-news lane; the algorithm rewards a predictable promise.
- **Title SEO:** put the primary keyword early. Ship custom captions for accessibility and search.
- **Length serves retention, never pads.** 8+ min only because retention holds (mid-roll ads).

---

## 2. Instagram + Facebook Reels (Meta) — authority: **Adam Mosseri, Head of Instagram**

Mosseri publishes ranking-signal confirmations directly (Reels/@mosseri posts, Jan-2025 series,
Dec-2025 year-end memo). Because Meta runs Instagram and Facebook Reels off the same recommendation
philosophy, his guidance governs **both** our Meta surfaces.

**Cross-references converging on Mosseri (multiple entities, one reference):**
- dataslayer, "Instagram Algorithm — 5 Ranking Signals Mosseri Confirmed."
- torro.io, "Instagram Algorithm 2025 (Explained by Adam Mosseri)."
- exchange4media, "How Instagram ranks posts: Adam Mosseri explains the algorithm."
- Fanpage Karma, "Instagram Reels Algorithm — Key Ranking Factors."

### Distilled rules (enforce)
- **#1 signal = watch time.** Then **sends-per-reach** (DM shares) and **likes-per-reach**. Sends
  drive *new-audience* reach; likes weigh more with existing followers. → make it worth sending.
- **Win the first 3 seconds.** Instagram heavily weighs whether viewers pass the 3s mark.
- **No cross-platform watermark.** A TikTok/CapCut logo makes a Reel ineligible for recommendation.
  → Our verticals must ship clean (they already do; TikTok's own logo is only added on TikTok).
- **Original content only.** Accounts posting ≥10 reposts in 30 days are excluded from
  recommendations — every Reel is our own cut.
- **Add audio/voiceover** (we already have cloned VO) — required for eligibility + ranking.
- **"Raw, real human" priority (Dec-2025 memo):** favor authentic, non-AI-looking content in 2026.
  Our human-VO + live-chart format fits; avoid obviously synthetic visuals as the main lane.

---

## 3. TikTok — authority: **TikTok Creator Portal / Newsroom (official "How TikTok recommends content")**

TikTok is the rare platform whose *own* published documentation is the definitive authority; the
For-You ranking is officially described and every credible third party just restates it.

**Cross-references restating the same official signal stack (multiple entities, one reference):**
- Hootsuite, "How the TikTok algorithm works."
- socialboostdigital, "TikTok's Signal Stack … For-You Page ranking."
- strategia-x, "TikTok Algorithm — what the For You Page actually rewards."

### Distilled rules (enforce)
- **Completion rate matters.** Cut tight; every second must earn the next. Short, loopable edits
  beat long ones.
- **Comment velocity in the first 30 min > total comments over 24h.** Open with a question or a
  claim that invites a reply; be ready to reply fast in the first half hour.
- **Relevant sound + on-screen captions** help categorize the video — use an allowed sound layer
  and keep burned word-captions.
- **Distribution expands from an initial audience when response is strong.** Judge posts by
  retention and engagement quality, not day-one raw views.
- **Post-native.** TikTok gets the clean 9:16 master (no other platform's watermark).

---

## 4. Thumbnails & visual design — authority: **Graham Stephan finance model + VidIQ/1of10 CTR research**

For the *finance* niche specifically, the recognized best-in-class is Graham Stephan's thumbnail
system: a dominant dollar figure or percentage plus a short, bold phrase — text does the work.
General CTR mechanics come from VidIQ and 1of10's A/B research.

**Cross-references converging (multiple entities):**
- VidIQ — emotional, legible thumbnails with one clear subject.
- 1of10 and ampifire — "one dominant subject, 2–3 colors, 3–5 words" is the modern high-CTR shape.
- Multiple finance-thumbnail breakdowns cite Graham Stephan's number-forward style as the template.

### Distilled rules (enforce)
- **≤5 words of text**, one dominant subject, 2–3 colors.
- **Lead with the number** (a price, a %, a dollar figure) — finance viewers click specifics.
- **4.5:1 contrast at mobile size**; test legibility at ~120px wide.
- **Use the brand palette:** red `#FF1744` on black `#08030a`; reserve green and amber for
  semantic market data only.
- **Logo in a fixed corner every time** for recognition and consistency.
- **Consistent template across all uploads** (this is what `tools/visuals/thumbnail.html` enforces).

---

## How this binds production

`.claude/skills/daily-news-video/SKILL.md` links this file as a mandatory input. Concretely:
1. **Package first (Galloway):** write the thumbnail + title before the cut; thumbnail via the
   template in Deliverable 3.
2. **Verticals ship clean + hook-first (Mosseri/TikTok):** first 3s hook, no foreign watermark,
   burned captions, our own VO, trending sound on the TikTok cut.
3. **One brand, one handle (design authority):** every surface uses `BRAND.md` art + @thetradercockpit.
4. **Caption/first-comment discipline (TikTok):** invite replies; be present in the first 30 min.

Sources are named inline above so the "multiple independent entities → one authority" requirement is
auditable rather than asserted.
