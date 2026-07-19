# TraderCockpit Trust-Recovery and Release-Gate Plan (v2)

## Summary

- Quarantine Video 04 as operator-rejected. Preserve it only as failure evidence; reconcile its package, publish log, and vault receipts to show no publication authority.
- Pause automated content production and publishing. Read-only analytics may continue.
- The next five runs use the human-gated workflow below. Agent identity is irrelevant as a control: Sol and Luna share the same codebase and model, so renaming the pilot changes nothing. The trust boundary is operator vs. automation, and only the gates below constitute that boundary. "Sol-led" survives only as a workflow label. Delegated (non-human-gated) operation cannot resume until all five runs pass consecutively and the operator explicitly re-enables delegation.
- Apply the same evidence-based release discipline before any consumer-facing product is publicly released.

## Enforcement model (what actually stops a bypass)

Every gate in this plan lives in the same agent-editable codebase that Video 04 bypassed. Code-level gates are therefore **procedure, not security**: an agent that can edit `tools/publish.py` can delete its gates. The plan is honest about this and rests on one structural control:

**Credential custody.** Live-publish credentials (YouTube OAuth token, TikTok session) move out of any agent-readable path. Live publishing becomes an operator-run step: the operator either executes the publish command themselves or supplies the credential/unlock at the moment of publication, per run. The agent can prepare everything; it cannot publish anything. This is the wall. All other gates exist to make the operator's decision at that wall well-informed and auditable.

**Approval-record integrity.** Approval records are agent-readable but operator-authored: the operator pastes the exact hash themselves (in chat or into the approval file); the validator only compares. Residual risk stated plainly: an agent could still forge an approval file it can write to. The forgery does not matter at the publish step — publication requires the operator-held credential regardless — but it could waste a run. Forged or agent-authored approval records discovered at any point reset the five-run count.

## Enforced workflow

### Topic and source approval
- Prepare the analysis brief and source receipt before writing narration.
- State the lead story, why it matters now, market transmission, bounded secondary stories, platform, and target length.
- Bloomberg supplies market-news framing; Al Jazeera supplies foreign/conflict framing. Official releases, exchanges, and TradingView remain evidence sources, not substitutes for the requested news framing.
- While the Iran war dominates the market regime, it leads unless the operator explicitly approves another lead. China may appear only as a bounded secondary story unless separately approved.
- Operator approval binds to exact SHA-256 hashes of the analysis brief and source receipt. The operator pastes the hashes into the approval record themselves.

### Script approval
- Draft from the operator-approved Video 01/02 voice corpus and frozen claims.
- Treat the automated style audit as advisory only.
- Present the complete script to the operator. The operator records its exact SHA-256, reviewer, and timestamp in the approval record.
- Block TTS, captions, visual assembly, and rendering if approval is absent or the script changes afterward.

### Artifact approval
- YouTube long-form uses a caption-free master. YouTube handles captions.
- Block TikTok/Reels until a separate short-form caption treatment, vertical asset, and account path are approved.
- Final-artifact review covers editorial quality, source use, narration, chart/subject alignment, audio, pacing, and platform fit — performed on the actual final export.
- Operator publication approval binds the exact asset, title, copy, claims receipt, production approval, caption mode, disclosure state, and privacy setting.

### Publication
- Live publishing is operator-executed or operator-unlocked (credential custody above). No credential ever resides where the agent can read it.
- Live publishing accepts only an approved batch item; arbitrary file/title command-line publishing is disabled.
- Require explicit platform publication authority in addition to script and asset approvals.
- Report success only after the platform returns — and a read-back confirms — a live platform ID/URL.
- A clean uploader exit without a verifiable post remains uploaded-unverified, never published.

## Minimal implementation changes

- Add one standard-library production-approval validator with exact-hash topic and script records. The validator compares operator-pasted hashes against computed hashes; it authors nothing.
- Relocate YouTube OAuth token and TikTok session files to an operator-only path outside the repo and agent working directories; `tools/publish.py` live mode reads credentials only from that path, so live publishing fails closed when run by the agent.
- Gate every downstream stage in `tools/produce.py`; generate/select the caption-free master for YouTube and do not require caption generation for that lane.
- Introduce social-batch/v2 in `tools/social_batch.py`. Bind the production approval, caption policy, privacy, title, copy, claims receipt, asset, disclosure, and their hashes into the final approval fingerprint. Keep v1 readable only as historical evidence, never live-publishable.
- Change `tools/publish.py` live mode to require `--batch` and `--item`. Perform real authentication probes:
  - YouTube: refresh OAuth if possible and confirm the authenticated channel.
  - TikTok: require a valid session and read-back capability; otherwise keep publishing disabled.
- Make the publisher write `publish_log.json` from actual platform responses. Failures retain null URL/ID and never receive published status.
- Update existing canonical runbooks and vault notes instead of creating parallel documentation. Record the Video 04 failures: gate bypass, wrong lead/source hierarchy, generic voice, inaccurate burned captions, and false credential readiness.

## Tests and acceptance

- Missing, stale, or modified topic/script approvals block TTS and assembly.
- NBS-only framing fails; official NBS evidence paired with the required Bloomberg/Al Jazeera framing passes.
- A YouTube item referencing a burned-caption master fails.
- Any post-approval change to title, copy, asset, script, claims, caption mode, privacy, or disclosure invalidates approval.
- Live publish attempted from the agent environment (no operator credential present) fails closed — this is the primary acceptance test for credential custody.
- YouTube readiness distinguishes absent, refreshable-expired, revoked, and valid credentials and confirms the expected channel.
- Live publishing rejects v1 batches, drafts, rejected items, hash mismatches, platform mismatches, and unverified TikTok sessions.
- Simulated publisher success must produce a platform ID/URL and matching publish-log entry; uploader-only success remains unverified.
- The current Video 04 fixture stays rejected and cannot become ready.
- Complete five consecutive human-gated runs with:
  - operator topic/source approval (operator-pasted hashes);
  - operator script approval;
  - final-artifact acceptance;
  - operator exact-hash publication approval;
  - operator-executed or operator-unlocked publication;
  - verified live platform receipts.
- Any bypass, forged or agent-authored approval record, false readiness result, editorial rejection, or unverifiable publication resets the five-run count.

## Assumptions

- Automated publishing remains paused during recovery; Sunday read-only analytics may continue.
- YouTube uses platform-native captions. Short-form publishing remains blocked until separately approved.
- External provider spend stays at $0.
- Existing uploads remain untouched.
- Consumer-product public release remains blocked until its own repository implements equivalent exact-input, human-approval, final-artifact, and verified-deployment gates.
