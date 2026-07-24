# Handoff — Teaching Series lane (on-camera playlist) — 2026-07-24

> STATUS 2026-07-24: **BRAINSTORM / NOT RATIFIED.** Concept + script machinery built this wave.
> Nothing scheduled, nothing published, no episode started. Operator explicitly halted
> finalization: *"We are not finalizing anything. This is still brainstorming."*
> Doctrine + lane SoT = ops vault `GTM/Teaching Series — Concept Brainstorm 2026-07-24.md`.
> This file is the repo-side implementation view only.

## What this lane is

Third content lane on the existing channel: a **separate YouTube playlist**, **operator on
camera**, teaching retail traders what they are doing wrong, building slowly toward putting Apollo
on camera once the product is ready.

**It is NOT the Show.** The Show (`GTM/Show Bible — Season 1.md`) needs monetization the channel
does not have and stays parked. This lane is a plain playlist — no YPP dependency. An agent
conflated the two earlier in this session; the resulting decision note and launch plan were
deleted. Do not resurrect them.

Daily news lane and weekly recap continue unchanged and remain the floor.

## Shipped this wave

| Artifact | Path |
|---|---|
| Script skill (canonical) | `.claude/skills/series-script/SKILL.md` |
| Codex bridge stub | `.agents/skills/series-script/SKILL.md` |
| Visual reference exemplars (6, operator-supplied) | `productions/_series/visual-refs/` |
| Lane doctrine + topic slate + open calls | ops vault `GTM/Teaching Series — Concept Brainstorm 2026-07-24.md` |

No code was written. No gates were modified. No production directory was created.

## The script process (10 stages, canonical detail in the skill)

thesis → receipt pull → package + demand screen → beat map → **capture operator's words** →
draft two-column SPOKEN|SCREEN → visual spec → gates → approval + delivery mode → measure.

Episode skeleton: known intro (≤5s, fixed) → **promise payoff (first 5s after intro)** → stakes →
teach loops → pre-registered on-camera experiment → the turn → close with open loop.

## Reuse contract — do not rebuild these

- Gates: `tools/claims_gate.py`, `tools/script_style_gate.py`, `tools/visual_qa.py`
- Claims: `claims.yaml` per the Claims Ontology, same shape as the daily lane
- Scene binding: `scene-plan.json`, daily-lane format
- Derivatives: `.claude/skills/post-approval-derivatives` (each teach loop = one natural short)
- Analytics: `tools/social_analytics.py`
- Render: `<repo>/OpenMontage` only; external provider spend `$0`

**Only new code sanctioned, and only when episode 1 actually needs it:** one reusable
`tools/mc_visuals.py` (path fan / distribution / underwater / 3D surface from a trades CSV or
param-grid CSV). Justified because every episode reuses it. Do not write per-episode animation
code. The banned-claims scrub stays a manual grep until a real script exists to test a gate
against (`gate-before-trust`: an unfired gate is untrusted).

## Standing constraints (restated — all bind this lane)

- **No alpha promise, no performance guarantee**, standing disclaimer verbatim — canonical home
  `GTM/Offer Inventory and Claims Constraint.md`.
- **Set 03 claims quarantine:** take register, leave every number. No win rates, no "easiest", no
  urgency frames.
- **No callouts / no mockery / no "X exposed"** formats — the studied channels are on the right
  side of the argument.
- **Machinery never named on camera** — show the artifact, speak the implication
  (`Decisions/2026-07-20 Backstage vs Receipts — Show Artifact, Speak Implication.md`).
- **Reviewer never-say table** — `Series/Reviewer Notes — Series Sets 01-03 — 2026-07-24.md`.
  The `Series/` corrective wave items 1–4 are copy-touching and should land before a script quotes
  the research.
- **The killed-strategy story is UNRECEIPTED operator dictation.** Script only from a receipted
  fact pack, never the bare claim.
- **Compute:** any on-camera experiment run needs operator green-light and a rented box. Never
  local.
- **Publishing:** exact-hash operator approval, unchanged.

## Next step when the operator resumes

Blocked on operator calls, not on tooling. In order:

1. **E1 pick** — arc opener (thesis-pure, low search demand) vs highest-demand concept episode
   (prop-firm math / the Monte Carlo lie) with the doctrine threaded in.
2. Series name + known-intro ident design.
3. Then, and only then: run `series-script` stages 1–4 and hand the operator the capture prompt.

Full open list (cadence, episode length, Pine/MT5 handoff boundary, gate graduation) is in the
vault brainstorm note.

## Coordination

No parallel session owns this lane. Ops-vault `GTM/` is SoT for lane doctrine; this file is SoT for
repo-side implementation state. If both need updating, the vault note wins on doctrine and this
file wins on paths and code.
