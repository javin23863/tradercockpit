# daily-2026-07-20 — what the content step owes

The runner (`tools/daily_postclose.py`) will not publish without these. It fails closed and pings rather than shipping a partial production.

- [x] `vo.txt` (agent) — script_style_gate PASS (1,494 words, 12 sections; 3 warns accepted editorially)
- [x] `claims.yaml` (agent) — claims_gate PASS (20 claims, 46 receipts)
- [x] `scene-plan.json` (agent) — 16 beats, editorial_gate clean in the 2026-07-21 dry run; chart captures receipted and predate vo.txt
- [x] `analysis-brief.md` (agent) — post-close brief, divergence-promoted lead
- [x] `news-sources.json` (agent) — 2 pages rendered+captured (US News/Reuters, NPR); Baghaei line dropped as unverifiable
- [x] `social-batch.json` (agent) — one draft YouTube item, disclaimer string included
- [x] `vo-receipts.yaml` (agent) — 46 section-keyed receipts
- Dry run 2026-07-21 ~03:00Z: decision publish-private (4 single_source claims, 3 style warns; zero hard fails)

Editorial frame is the **post-close recap**: what the session did, on settled closing prints, never pre-open positioning. See the daily-news-video skill.
