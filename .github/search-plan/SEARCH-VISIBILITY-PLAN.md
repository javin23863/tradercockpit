# TraderCockpit: wording and search visibility plan (updated 2026-10-12)

This file updates Codex's 5 October "research-backed wording and search visibility plan" to match the repo as it is now. It applies the fixes from mike's outside review and adds the gaps that review found. It lives under `.github/` so GitHub Pages does not publish it.

Status labels: **DONE**: live on the site once its PR merges. **DRAFT**: written in this folder, for mike or the coordinator to publish. **OWNER**: needs an account, a sign-in or a decision, so no agent does it. **OPEN**: not started.

## What changed since the original plan

| Original plan said | Now |
|---|---|
| Site at `javin23863.github.io/tradercockpit/`, robots file under the project path | The domain is decided: **https://trader-cockpit.com** (PR 56). Every canonical URL, `og:url`, JSON-LD id, sitemap entry and `llms.txt` link uses it. `robots.txt` is at the root and names the sitemap. **DONE** |
| Homepage supporting line "Explore trading strategies, charts, models, and repeatable research workflows." | Dropped: it implies shipped features. The homepage says what is true: guides to backtesting, out-of-sample testing and Monte Carlo analysis, plus a Windows desktop app in development. **DONE** (already live from PR 55; kept) |
| "Join the TraderCockpit waitlist" as the primary action; meta description "…desktop access is on waitlist" | The waitlist was retired in PR 55: there is no email capture and checkout is closed. The primary action is "Read the guides"; the description says "Our Windows desktop app is in development." **DONE** |
| Author or reviewer "when available" | Byline **"By the TraderCockpit team"**, an Organization author in Article JSON-LD, an "About the TraderCockpit team" note and an "Educational material, not financial advice" note on the three upgraded guides. Under Google's guidance on "Your Money or Your Life" topics, an organization byline is weaker than a named, credentialed author or reviewer. It can be upgraded later to a named author or reviewer with a bio. **DONE** (team byline); named author **OWNER** (optional) |
| Bing help URL `…/ai-performance-9f8e7d6c` | Removed: the page renders no content without a browser session, so it could not be confirmed. Replaced with Bing's announcement post (confirmed). |
| "Google's Search generative AI inclusion control" | The page's actual title is "Search generative AI control". Kept with that name. |
| Google's generative AI report "is rolling out" | Updated: Search Console says it had rolled out to all sites as of 31 August 2026. |
| Instagram indexing claim (help.instagram.com/147542625391305) | Removed: the help page renders no content without a browser session, so it could not be confirmed. |

## Verified sources (checked 2026-10-12)

| Claim | Source | Checked |
|---|---|---|
| No special markup or wording is needed for Google's AI features; Google Search ignores `llms.txt` for visibility and ranking | [Google: optimizing for generative AI features](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide) | Yes |
| Semrush studied **325,000** prompts (ChatGPT Search, Google AI Mode, Perplexity; Jan–Feb 2026, published 10 Mar 2026); articles were **50–66%** of cited LinkedIn content | [Semrush](https://www.semrush.com/blog/linkedin-ai-visibility-study/) | Yes. Per-engine shares appear only in a chart, so only the range is quoted. |
| Knowatoa analysed **1,139,638** AI responses (published 9 Jun 2026); LinkedIn citations were **56.8%** articles, **15.6%** feed posts, **9.3%** company pages | [Knowatoa](https://knowatoa.com/reports/linkedin-citations) | Yes |
| Bing recommends clear headings, tables, FAQ sections, examples and cited evidence; it announced AI Performance reporting (10 Feb 2026) | [Bing Webmaster blog](https://blogs.bing.com/webmaster/2026/2/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview/) | Yes |
| Search Console has a "Search generative AI control" to include or exclude a site's content from AI Overviews, AI Mode and Discover | [Search Console Help](https://support.google.com/webmasters/answer/16908024) | Yes |
| Search Console's "Generative AI performance report (Search)" covers all sites since 31 Aug 2026 | [Search Console Help](https://support.google.com/webmasters/answer/16984139) | Yes |
| OpenAI's `OAI-SearchBot` (search) is separate from `GPTBot` (training) | [OpenAI crawlers](https://developers.openai.com/api/docs/bots) | Yes |
| Branded web mentions correlate with AI Overview visibility (0.664) more than backlinks (0.218); 75,000 brands; the authors say correlation ≠ causation | [Ahrefs, 26 May 2025](https://ahrefs.com/blog/ai-overview-brand-correlation/) | Yes |
| GEO paper: "up to 40%" visibility in generative-engine responses (an experimental measure, not traffic or ranking) | [arXiv 2311.09735](https://arxiv.org/abs/2311.09735) | Yes |
| C-SEO Bench: most conversational-SEO rewrites perform poorly and often hurt ranking | [NeurIPS 2025](https://proceedings.neurips.cc/paper_files/paper/2025/hash/27aa3aeff0f8460a7b43d30fa6c5c032-Abstract-Datasets_and_Benchmarks_Track.html) | Yes |
| Buying links for ranking and automated link building are link spam | [Google spam policies](https://developers.google.com/search/docs/essentials/spam-policies) | Yes |
| PDFs are indexable | [Google indexable file types](https://developers.google.com/search/docs/crawling-indexing/indexable-file-types) | Yes |
| Titles should be descriptive and concise, without keyword stuffing | [Google title links](https://developers.google.com/search/docs/appearance/title-link) | Yes |
| `sameAs` and `logo` are recommended Organization properties | [Google Organization markup](https://developers.google.com/search/docs/appearance/structured-data/organization) | Yes |
| robots.txt must sit at the host root; a 4xx (except 429) means no restrictions | [Google robots.txt spec](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec) | Yes |
| FAQ rich results no longer appear in Google Search (from 7 May 2026) | [Google FAQPage docs](https://developers.google.com/search/docs/appearance/structured-data/faqpage) | Yes |
| YMYL topics get more weight on trust; Google encourages accurate bylines | [Google: helpful, people-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content) | Yes |
| LinkedIn Product Pages are limited to certain industries (including financial services) | [LinkedIn Help](https://www.linkedin.com/help/linkedin/answer/a552600) | Yes |
| `llms.txt` is Jeremy Howard's proposal for helping agents use a site | [llmstxt.org](https://llmstxt.org/) | Yes |

The Instagram reels, Reddit threads and the Marketing Signals playbook in the original plan are practitioner opinion, not evidence; they are dropped from the reasoning.

## On the site (static GitHub Pages)

| Item | Status |
|---|---|
| Canonical URL on every indexable page; utility pages (`404`, `confirmed`, `thanks`) `noindex` | **DONE** (already present; checked by `check_site_hardening.py`) |
| Open Graph and Twitter cards on every indexable page (title, description, URL, 1200×630 image with alt text) | **DONE**: `.github/scripts/search_metadata.py` writes one managed block per page from the page's own title, description and canonical URL, and `--check` keeps them in sync |
| JSON-LD: Organization (logo, `sameAs` YouTube only, the one verified profile), WebSite and SoftwareApplication (Windows, "in development; not yet released", no offers or prices) on the homepage; BreadcrumbList on inner pages; Article (team author, publisher, published/modified dates) on every guide | **DONE** |
| `sitemap.xml` with `<lastmod>` from the same dates the pages declare; `robots.txt` at the root | **DONE** |
| Titles lead with the specific topic, pattern "Topic — TraderCockpit" (homepage "TraderCockpit \| Backtesting & Strategy Validation Guides"); meta descriptions ≤155 characters, topics first; page URLs unchanged | **DONE** for the pages with vague or long text (Learn, How-to, Research Lab, Docs, Pricing, Updates, Support, Terms, Refunds, two Methods pages, seven concept pages via `seoTitle`). Search volumes are **not** checked, see below. |
| Three upgraded guides: answer first, method, assumptions, limits, descriptive links, byline, date, About note | **DONE**: out-of-sample, Monte Carlo and the backtest checklist. The checklist was rewritten in plain trader language in PR 57. |
| Vary "Explore" | **DONE** on the homepage and pricing buttons |
| FAQ sections | Kept for readers only. No FAQ rich results are expected (Google retired them in May 2026), so no FAQPage markup. |
| `llms.txt` | **DONE** at `/llms.txt`, as an optional aid for agents. Google ignores it; it is not a ranking tactic. |
| Favicon (brand mark) on every page | **DONE** |
| Google verification meta tag and `BingSiteAuth.xml` | Kept unchanged |

## Planned: "free paper trading" as a search topic

The owner decided on 12 Oct 2026 to add a $0 Free plan with Google sign-in. It includes unlimited paper trading, 1 chart layout, 3 indicators per chart, 3 alerts and live market data from free sources. Strategy Builder and backtests, real-broker trading, Apollo and exports stay paid. Once the app side has shipped and the Free card is live, add "free paper trading" (and "paper trading app for Windows") as a search topic: a guide to paper trading well (fills, costs, realistic sizing), linked from the Free card, plus a LinkedIn and Instagram angle. Check search volumes first (owner step 6). **OPEN** for the search topic only. The app side shipped in tradercockpitsq PRs 682 and 688 (12 Oct 2026) and the Free card is published on Pricing and the homepage.

## Drafts for publishing (mike or the coordinator publishes; no agent posts)

- `linkedin-articles.md`: three articles, each a different angle (a worked example, a common mistake, a case study), each linking to the full guide rather than condensing it. **DRAFT**
- `instagram-captions.md`: captions for three short tutorials on the same topics. **DRAFT**
- Every outbound link in the drafts carries UTM tags: `utm_source` (linkedin, instagram, youtube, reddit, …), `utm_medium=social` or `community`, `utm_campaign` (the guide slug), e.g. `https://trader-cockpit.com/learn/concepts/out-of-sample.html?utm_source=linkedin&utm_medium=social&utm_campaign=out-of-sample`.
- There is no signup or contact form on the site today (PR 55 retired email capture). When one is added, it must record `utm_source`, `utm_medium` and `utm_campaign` (the old waitlist form had hidden fields for this; reuse that pattern). **OPEN**
- LinkedIn company tagline: "Trading strategy research and education for systematic traders." About text: the homepage introduction, saying the Windows app is in development. **DRAFT** (in `linkedin-articles.md`)

## Owner steps (accounts and sign-ins; not done by agents)

1. **Google Search Console.** The domain property `trader-cockpit.com` is verified by the existing meta tag (or by DNS TXT at Wix). Submit `https://trader-cockpit.com/sitemap.xml`. Request indexing for the homepage and the three guides. In settings, confirm that the **Search generative AI control** allows inclusion. Record a baseline from the Performance and Generative AI performance reports.
2. **Bing Webmaster Tools.** Add `trader-cockpit.com` (verified by `BingSiteAuth.xml`, or import from Search Console), submit the sitemap and turn on AI Performance reporting.
3. **Analytics.** Plausible is configured but `pending_operator_account` in `docs/prelaunch-config.v1.json`. Without it, referral and UTM results can't be measured. Create the account and set the script URL.
4. **LinkedIn company page.** Create it with the tagline and About text, then publish the three articles. A LinkedIn Product Page waits until the app is released and eligibility is confirmed.
5. **Profiles for `sameAs`.** Only YouTube is verified (`docs/social-links.v1.json`). Add LinkedIn, Instagram and others to that file and to `search_metadata.py`'s `SAME_AS` once their URLs exist.
6. **Search volumes.** Before locking further titles, check monthly volumes for the candidate phrases (e.g. "out of sample testing", "in sample vs out of sample", "monte carlo simulation trading", "walk forward analysis", "backtest checklist"). Use Google Keyword Planner (needs a Google Ads account) or a free tool. Titles that lead with specific topics are in place; retitle only if the numbers favour another phrase.
7. **Optional: a named author or reviewer** with a short bio and credentials. This strengthens the guides under YMYL guidance. Once confirmed, switch the byline and the JSON-LD author from the Organization to a Person.

## Measurement

### Brand search and name collisions

- Track impressions and clicks for "TraderCockpit" and "Trader Cockpit" separately from non-brand queries in Search Console (filter by query). **OWNER**, from the baseline onwards.
- Check for products with similar names: search "Trader Cockpit", "TradeCockpit" and "Trading Cockpit" on Google, Bing, app stores, LinkedIn and Instagram. Note any brokerage or app feature with the same name, and whether results mix them up with us. **OPEN** (first pass at baseline, again at week 8)

### AI answer baseline (week 0, 4 and 8)

Ask each question in ChatGPT (search on), Perplexity, Gemini and Copilot, signed out or in a clean profile. Record the date, engine, the full answer, every cited URL, and whether TraderCockpit is mentioned or cited. Use free tiers only; no paid tracking tools.

1. What is the difference between in-sample and out-of-sample backtesting?
2. How do I know if my trading strategy backtest is overfit?
3. What does a Monte Carlo simulation tell you about a trading strategy?
4. Can Monte Carlo simulation predict the maximum drawdown of my strategy?
5. What is walk-forward analysis in trading?
6. How much data should I hold out for out-of-sample testing?
7. Why does my strategy work in the backtest but fail live?
8. What is selection bias in strategy backtesting?
9. How many trades do I need for a backtest to mean anything?
10. How should I include commissions and slippage in a backtest?
11. What questions should I ask before trusting a trading strategy's backtest results?
12. Is a high profit factor in a backtest a good sign?
13. What does drawdown duration mean, and why does it matter?
14. How do I test whether my strategy's parameters are robust?
15. What is data leakage in trading strategy research?
16. What software can I use to backtest and validate trading strategies on Windows?
17. What is TraderCockpit?
18. Are there free guides that explain strategy validation methods?

### Week-8 decisions per channel (written now)

| Channel | Continue if | Change if | Stop if |
|---|---|---|---|
| Google organic | Non-brand impressions for the three guides rise week over week, and at least one guide ranks on page 1–2 for its topic | Impressions rise but CTR stays under 1%: rewrite titles and descriptions | Still not indexed after Search Console requests: fix crawl or indexing before any content work |
| Bing / Copilot | Pages indexed and any AI Performance citations appear | Indexed but never cited: improve tables, examples and sources on the guides | Not indexed: resubmit; no content changes until indexed |
| AI answers (question set) | TraderCockpit is cited for ≥2 of the 18 questions in any engine | Cited only for the brand questions (17–18): publish one more guide on the most-asked uncovered question | No citation in any engine after 8 weeks, and the LinkedIn articles have no reach: put effort into earned mentions in communities |
| LinkedIn articles | ≥1 article gets measurable referral visits (UTM) or appears in an AI answer's citations | Views but no clicks: put the guide link higher and make the angle more specific | No views or clicks after 3 articles: pause and reuse the material elsewhere |
| Instagram tutorials | Profile visits or link clicks (UTM) from tutorials | Reach but no clicks: change the hook or format | No reach after 6 posts: stop |
| Community answers (Reddit and forums, only where self-links are allowed) | Answers get upvotes or referral visits | — | Any moderation removal: stop on that community |

Evaluate at week 4 (trend check only) and week 8 (decisions). Early changes are observational, not proof that one edit caused them.

## Notes

- Nothing here claims the app is available. Prices appear only as "planned", and checkout is closed.
- No StrategyQuant, SQX or AlgoWizard names appear in any public output.
- Bulk link or PDF-submission packages are out: they count as link spam.
