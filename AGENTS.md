# Repository scope

- TraderCockpit owns the media, marketing, social, and public concept surface.
- Apollo is an assistant/interface concept. The consumer runtime belongs in a separate future repository.
- Godseye is a separate geospatial evidence product. Use only its versioned automation and evidence contracts.
- Futures and Register are context-only unless the operator explicitly opens a task in those repositories. Do not edit, test, generate files in, stage, or clean them from this repository task.
- Do not borrow dependencies or installations from another repository.

# ponytail

The `ponytail:ponytail` plugin skill is mandatory for every task in this repository. Reuse existing code and native platform features, avoid speculative abstractions, and leave the smallest verified change that satisfies the request.

# recurring social operations

After Sol proves a TraderCockpit social workflow with a real end-to-end acceptance receipt, use
`.agents/skills/social-ops-luna/SKILL.md` for recurring execution. Project-scoped schedules run on
`gpt-5.6-luna` at `max`; first-time setup, workflow changes, credentials, terms, and failed gates
remain with Sol.

Sol always owns consumer-facing quality control and pipeline implementation. Luna output is a
candidate until Sol reviews the actual final artifact and receipts; delegation never lowers a gate
or transfers accountability. Sol acceptance and operator exact-hash publication approval are both
required. Quality regressions return to Sol for root-cause pipeline repair.

The publishing calendar is Monday–Friday daily market news, Saturday weekly recap through
`.agents/skills/weekly-market-recap/SKILL.md`, and no Sunday post. Sunday is the analytics and
process-improvement review.

# teaching series lane (on-camera playlist)

A third content lane is at concept stage: a separate YouTube playlist, operator on camera, teaching
retail traders what they are doing wrong. Read `handoffs/SERIES-LANE-HANDOFF-2026-07-24.md` before
any work on it, and use `.agents/skills/series-script/SKILL.md` for episode scripting. It is NOT
the Show (the Show needs monetization the channel does not have and stays parked) and NOT the daily
news video. Nothing in this lane is ratified — no episode is approved, scheduled, or started.

# zero-cost generative media

- Use the project skill `.agents/skills/tradercockpit-free-media/SKILL.md` for every request to create, edit, generate, repurpose, or package social media assets, alongside any more specific production skill.
- External provider spend is fixed at `$0`. Reject MuAPI, credits, subscriptions, paid model APIs, hosted generation, hosted MCP gateways, and paid fallbacks. Do not offer to configure them.
- Codex image generation is allowed under the operator's existing Codex access. Offline still generation uses only `Open-Generative-AI/` with `stable-diffusion.cpp` and DreamShaper 8.
- Video work may read the installed `openmontage` skill for its pipeline contract, but must execute only in this repository's `OpenMontage/` checkout. Never use another repository's engine, venv, models, or credentials.
- Generated media is creative material, never a factual chart, news screenshot, geospatial observation, product proof, or evidence. Preserve source/model/seed/license provenance and existing synthetic-disclosure gates.
- Do not create accounts, enter provider keys, top up balances, publish, schedule, or upload unless the operator explicitly authorizes that separate action.

# deploy

When the operator gives `deploy` as a direct instruction, the current task must not stage, commit, push, mutate a pull request, merge, release, or perform post-merge deployment actions.

Instead, immediately create one separate project-scoped Codex task for this repository:

- Resolve the saved Codex project whose canonical folder exactly matches the active repository.
- Use model `gpt-5.6-luna` with reasoning effort `max`.
- Target that exact project and repository folder, using the current checkout or a worktree starting from the current branch.
- Never create a projectless deployment task.
- If the exact project, model, or reasoning effort is unavailable, fail closed and ask the operator to correct the project configuration. Do not substitute another model or location.

Pass Luna a deployment packet containing:

- Repository and canonical worktree paths.
- Current branch, base branch, and commit.
- Pull-request URL and state, if one exists.
- Requested deployment outcome and approved acceptance criteria.
- Changed-file inventory and intentionally excluded files.
- Tests, builds, claims checks, and review evidence already completed.
- Known risks, required approvals, secrets boundaries, and rollback notes.

Luna owns the repeatable deployment workflow:

1. Reconfirm repository, worktree, branch, and diff state.
2. Stage only files already reviewed by the primary task.
3. Commit intentionally and push the intended branch.
4. Create or update the pull request.
5. Monitor CI and review status.
6. Return substantive product, architecture, contract, dependency, claim, migration, credential, or scope changes to the primary task for review.
7. Merge only after the primary task approves the final diff and evidence.
8. Verify the default branch and the explicitly requested post-merge target.

The primary task remains responsible for implementation, full-diff review, test adequacy, and merge approval. Luna performs deployment actions after that approval. One Luna task handles one repository and one pull request. Cross-repository releases require separate Luna tasks and an explicit merge order. Production publication occurs only when the operator explicitly includes it in the deployment instruction.

# esq-battery-ops

- **esq-battery-ops** (`~/.agents/skills/esq-battery-ops/SKILL.md`) launches, monitors, diagnoses, and recovers ESQ library-cycle battery runs.
- Trigger: `/esq-battery-ops` or a request to monitor, resume, or triage an ESQ battery/backtest run.
- Use the skill before doing anything else for those requests.

# graphify

- **graphify** (`~/.agents/skills/graphify/SKILL.md`) turns project inputs into a knowledge graph.
- Trigger: `/graphify`.
- Use the skill before doing anything else when the operator invokes it.

# openmontage

- **openmontage** (`~/.agents/skills/openmontage/SKILL.md`) produces YouTube videos, Shorts, Reels, and TikToks from a brief.
- Trigger: `/openmontage` or any request to create or edit a video, montage, explainer, Short, or Reel.
- Use the skill for those requests, then execute its pipeline from this repository's `OpenMontage/` checkout only.

# see-video

- **see-video** (`~/.agents/skills/see-video/SKILL.md`) extracts frames from a YouTube URL, direct video URL, or local video so Codex can inspect it.
- Trigger: `/see-video` or a request to inspect what is shown in a shared video.
- Use the skill for those requests.

# tiktok-upload

- **tiktok-upload** (`.agents/skills/tiktok-upload/SKILL.md`) posts an approved 9:16 MP4 through TikTok's official free Content Posting API with refreshable OAuth and provider read-back.
- Trigger: `/tiktok-upload` or any request to post or upload a video to TikTok.
- Use the skill for those requests.

# System hygiene (MANDATORY — disk is shared and exhaustible)

Standing rule after the 2026-07-17 disk-zero incident. Full protocol:
the ops vault `Operations\SYSTEM-HYGIENE-PROTOCOL.md`. Enforcer: `tools/janitor.py`.

- **Start scoped:** temp/scratch in the session scratchpad or `C:\tmp\<task>`, never scattered in
  `~/repos` / `~/Documents` / `~/Desktop`. Bulk data (>~1 GB) is cloud-first to B2; local keeps GOLD
  slices only. New worktrees go under `C:\tmp\`, named for their task.
- **No dated archive clones.** A git tag/branch is the snapshot — never copy a tree into
  `_preserved-*` or `<repo>-pre-cloud-<sha>`. That copy pattern is what filled the disk.
- **Close out every task:** commit+push source, send bulk to B2, `git worktree remove` your
  worktree, drop regenerable intermediates (build/, ta-work/, clipper output, __pycache__), then
  `py tools/janitor.py --reclaim caches build --yes`. Receipt GB freed in the vault log.
- **Audit before any multi-GB job:** `py tools/janitor.py` (read-only) — know the headroom first.
- Anything neither in a remote nor in B2 must be backed up before deletion, never trashed blind.

Portfolio/ops/GTM notes → the ops vault: `C:\Users\MSI\Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit` (repo doctrine stays here; never create another vault). `Desktop\TraderCockpit-Vault` is RETIRED read-only.

# Model-agnostic production principle (operator directive, 2026-07-21)

Outcome quality must not depend on which LLM runs the lane. Every production decision traces to
one of four writer-independent surfaces:

1. **Written doctrine** — `MARKET-ANALYSIS-DOCTRINE.md` (same 7 questions, same watchlist, same
   confirmation table for every writer), `BRAND.md`, `GROWTH-AUTHORITY-PLAYBOOK.md`, the skills.
2. **Deterministic gates** — claims, style, editorial, visual QA, and the fail-closed
   `daily_postclose.py` decision. A gate that documents without blocking reads as approval;
   silence is never a pass.
3. **Pinned exemplars** — the newest operator-approved scripts and builds are the quality floor
   a draft is compared against, not the writer's taste.
4. **Independent critic pass** — a second model critiques every script against the brief and the
   exemplars; the writer triages findings against receipts (receipts win over both models).

Corollary: when a run needs model judgment the process didn't specify (a capture looked wrong, a
number idiom didn't reduce to bar arithmetic, a source couldn't be pinned), the fix is encoded
into a gate, tool flag, or skill checklist IN THE SAME WAVE — next run, a different model hits a
rule instead of a judgment call. That is how the process stays reproducible across models.

# Control-plane handoff

- This repository owns implementation artifacts and source receipts. It never writes `Manager\.manager\manager.db` or generated ops-vault pages.
- At every handoff, return exact branch, commit, tests, artifacts, blockers, and next action to the Manager coordinator. Manager alone applies portfolio intents and runs `vault_sync.py`.
- Read handwritten operator decisions and current generated status from the ops vault. Edit repository doctrine here; edit operator decisions through the vault Inbox; never edit a page marked `generated:`.
