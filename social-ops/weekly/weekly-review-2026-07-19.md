# Weekly Social Review — Sunday 2026-07-19 18:00 ICT (first automated-data review)

Lane: `tradercockpit-weekly-social-review` / Manager node `social.sunday-review`.
Data: `social-week-2026-07-18.md` report + `analytics-latest.json` (collected 2026-07-19 ~17:55 ICT,
youtube/facebook/instagram ready, tiktok collector unavailable) + `velocity-latest.json` (4 samples,
first day) + `hotdog-backlog.json` (11 channels screened). No-post review per department contract.
Playbook lenses: Grow with Alex, Shane Hummus, Modern Millie, GaryVee, Platform Publishing.

## The week in numbers

| Surface | Followers | Week views | Notes |
|---|---|---|---|
| YouTube | 0 subs gained (0 total change) | 185 | 89 min watched, avg 51.9s/view, **38.7% avg viewed**, 1 like, 0 comments, 0 shares |
| Instagram | 10 | 421 observed | 14 posts live, top reel 91 views |
| Facebook | 1 | 8 observed | every reel 0–3 views |
| TikTok | — | — | auth still blocked (`social.tiktok-auth`); HQ vitals last showed 746 lifetime |

Baseline caveat (collector decision, correct): this is week 1 of scheduled snapshots — treat all
numbers as baseline, not trend. Velocity has one day of samples; 24h rates arrive mid-week.

## Winners — and why, in playbook terms

1. **"Trump's 20% Hormuz Toll Sent Oil +10%" Short — 89 views = 19.8× trailing-20 median (4.5).**
   Clear Hot-Dog-style outlier against our own baseline. Why (Shane/Alex): news-shock + immediate
   portfolio consequence in the title, consequence-first hook, evergreen-adjacent macro fear.
   The same story's long-form ("What It Means For Your Portfolio", 23 views = 5.1×) also broke out —
   the *story family* wins, not one upload.
2. **"Don't Trade the Siren. Trade the Pressure Chain." Short — 40 views = 8.9× median.** Brand
   doctrine line as hook; differentiated voice (Copy Posse lens: stance > information).
3. **IG "Friday to Friday off the weekly bars" — 91 views = 3.0× median, and today's "Good news got
   sold" reel is the only live velocity mover (27.8 views/hr).** Weekend-review derivatives travel
   best on IG right now.

## Losers — suspected cause

- **Duplicate uploads split their own views**: "Hormuz Toll: What It Means For Your Portfolio"
  exists twice (23 + 4 views), "How High Can Oil Actually Go" twice (5 + 1). Same title, same
  packaging, same day — self-cannibalization, and it pollutes our own outlier math.
- **Facebook is a dead surface as operated**: 15 reels, 0–3 views each, 1 follower. GaryVee rule
  says platform-native reframe or it's noise; these are unreframed twins. Zero marginal cost to
  keep auto-twinning, but zero evidence of return.
- **Retention 38.7% avg viewed** — below the 40% comfort line; intros are carrying too much setup
  before the payoff (collector flagged the same at 38.15% last window).
- **0 comments / 0 shares / 0 saves signal**: engagement stage (Stage 5) is not being worked —
  playbooks weight shares/saves over views, and nothing in the pipeline currently optimizes for them.

## The three decisions (contract: one repeat, one stop, one controlled test)

- **REPEAT — the news-shock → portfolio-consequence Short family.** Two of three breakouts share
  the shape: [macro shock] + [number] + [what it does to your money]. Next week, every day's
  strongest news item gets this exact Short treatment first.
- **STOP — duplicate same-title uploads.** One story = one Short + one long + platform twins with
  *different* packaging. Publishing QA (Platform Publishing checklist stage) must reject a second
  upload with a near-identical title inside 7 days.
- **TEST — cold-open restructure on the daily Short.** One variable: payoff line moved into the
  first 3 seconds (hook layering per Millie: visual + text + audio), no other format change,
  full week, judged next Sunday on averageViewPercentage (38.7% baseline → target ≥45%).

## Process improvements shipped this week (review infrastructure)

- Content Machine library installed: 7 playbook skills + vault notes + Operator HQ tiles/buttons.
- Analytics pipeline extended: 3-hourly velocity snapshots (scheduled), breakout detection
  (≥2× trailing-20 median), Hot Dog competitor screen (11-channel watchlist, Sunday + on-demand),
  weekly report generator, HQ one-click buttons for both.
- Competitor landscape vetted and documented (vault `GTM/SEO/Competitor Landscape.md`).
- Meta token data-access expiry (2026-10-12) verified and calendared (reminder 2026-10-05).

## Next week's intake backlog (screened)

1. Hormuz/oil second-order effects — freight, airlines, refiner margins (repeat family, proven).
2. "Pressure chain" doctrine Shorts — one per week (8.9× evidence, brand differentiator).
3. Weekend-review IG derivative — double down (3.0× + only live velocity mover).
4. Hot Dog screen returned 0 finds from 11 established channels — expected; add 3–5 sub-100k
   niche channels to the watchlist this week to raise yield (owner: operator/Claude).
5. Driver discipline starts now: every post next week gets a declared driver
   (money/email/audience/fun) in `social-ops/post-drivers.json` *before* publish; this week 100%
   shipped untagged, so driver scoring stayed empty.

## Post-review hardening (Codex CLI audit, same session)

Codex reviewed the pipeline diff before commit and flagged 10 issues (3 high); all fixed same
session: YouTube velocity now samples lifetime view counters (was mixing reporting-window numbers
— invalidated cross-sample math), velocity log converted to true append-only, hotdog screen now
fails loudly (status ok/partial/failed + per-channel counts) instead of exiting 0 on total failure,
clock-skew rate fabrication guarded, malformed-input tolerance, atomic artifact writes. Velocity
log reset as part of the metric fix — intraday curves restart today, full week by next Sunday.

## For next Sunday's review

Compare: averageViewPercentage (test verdict), subs gained, IG follows-per-reel, velocity
24h curves (full week of samples by then), Hot Dog finds after watchlist expansion, driver
score table populated.
