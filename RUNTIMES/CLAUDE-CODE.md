# OpenMontage on Claude Code

**Install (done on this machine):** skill copied to `~/.claude/skills/openmontage/` — trigger registered in `~/.claude/CLAUDE.md`. Any Claude Code session can invoke it via the Skill tool or `/openmontage`.

## Play to Claude Code's strengths

- **Skill system**: `openmontage/SKILL.md` auto-loads on video requests; it defers to the engine's `AGENT_GUIDE.md`.
- **Subagents / workflows**: fan out per-scene asset generation (research, image gen, stock search) as parallel agents; keep the render serial (one GPU).
- **see-video skill** (installed here): analyze a reference YouTube/TikTok video frame-by-frame before producing in its style — pairs with OpenMontage's "Start from Reference Video" flow.
- **Long-running renders**: run via Bash `run_in_background`, monitor the backlot dashboard (`python -m backlot open`).
- **GPU**: this box's RTX 3080 (8 GB) — obey the GPU pins in SKILL.md (`wan2.1-1.3b` only).

## Project skills & agents (2026-07-13, news-first pivot)

Repo-local, auto-discovered from `.claude/`:
- **skill `daily-news-video`** — end-to-end daily runbook: fact pass → script → God's Eye
  b-roll → chart cards → assemble/shorts → publish gate. Start here for "today's video".
- **skill `godseye-footage`** — CDP capture of the God's Eye globe app (shot JSON,
  cinematography rules, frame verification).
- **agent `fact-pack`** (sonnet) — sourced, dated, PIT-safe fact pack with an explicit
  UNVERIFIED-banned list; run before scripting anything.

Knowledge base: `C:\Users\MSI\Desktop\TraderCockpit-Vault` — read `_meta/hot.md` first,
then `_meta/index.md`. Strategy source of truth: `CONTENT-STRATEGY-TRADER-COCKPIT.md`
(news-first pivot section at top).

## Quick start

```
cd C:\Users\MSI\Desktop\OpenMontage-Skill\OpenMontage
# describe the video in natural language; Claude reads AGENT_GUIDE.md and drives the pipeline
```
