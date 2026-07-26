# daily-2026-07-23 — what the content step owes

The runner (`tools/daily_postclose.py`) will not publish without these. It fails closed and pings rather than shipping a partial production.

- [ ] `vo.txt` (agent) — script_style_gate + the exact-hash approval bind to it
- [ ] `claims.yaml` (agent) — claims_gate maps every number-bearing region to a receipt
- [ ] `scene-plan.json` (agent) — editorial_gate validates beats against visible subjects
- [ ] `analysis-brief.md` (agent) — script_approval binds the production to its brief
- [ ] `news-sources.json` (agent) — source provenance for the claims ledger
- [ ] `social-batch.json` (agent) — publish.py publishes exactly one approved v2 item
- [ ] `vo-receipts.yaml` (agent, optional) — per-claim receipt detail

Editorial frame is the **post-close recap**: what the session did, on settled closing prints, never pre-open positioning. See the daily-news-video skill.
