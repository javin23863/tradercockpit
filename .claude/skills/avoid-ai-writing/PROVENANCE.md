# Provenance

Source: https://github.com/conorbronsdon/avoid-ai-writing (SKILL.md)
Installed: 2026-07-28, project-scoped under Documents/tradercockpit/.
Commit: 27156c7ae69fade80f2a3410e6899b780248709d
License: MIT — see tools/vendor/avoid-ai-writing/LICENSE.

## Relationship to the other two surfaces

Three surfaces now cover AI-writing. They are reconciled, not stacked:

| Surface | Kind | Owns |
|---|---|---|
| `.claude/skills/no-ai-slop/` | prose an agent reads | house voice, editing principles, the outright-ban word list |
| this skill | prose an agent reads | the wider 45-category catalog, tiers, context profiles, rewrite/detect/edit modes |
| `tools/ai_writing_gate.py` | code that BLOCKS | the deterministic subset, at the social-batch boundary |

The gate is the enforcement point; both skills are drafting aids. Where the two skills
disagree on a word, **no-ai-slop wins** — it is the operator's list. `HOUSE_BANNED` in
`tools/ai_writing_gate.py` exists precisely for that case: it hard-blocks the words
no-ai-slop bans outright which the vendored detector only flags in clusters. Without it,
importing this skill would have LOOSENED house doctrine on nine words.
