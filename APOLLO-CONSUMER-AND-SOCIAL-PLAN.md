# Apollo Consumer Experience and Social Operations Plan

- **Status:** Proposed
- **Owner:** javin23863
- **Repository:** `javin23863/tradercockpit`
- **Last updated:** 2026-07-15
- **Canonical landing page:** <https://javin23863.github.io/tradercockpit/>
- **Related implementation branch:** `agent/apollo-manifest-godseye-bridge`

## Purpose

TraderCockpit is the media, marketing, and social operation around a future consumer product. Its public message is simple: test whether a creator's strategy claim survives a robustness pipeline before paying for it.

TraderCockpit is not the consumer runtime, the private robustness engine, or proof that an unfinished capability exists. Apollo is the assistant/interface name. The consumer-product name remains a separate decision.

## Repository boundaries

| Repository | Ownership | Boundary |
|---|---|---|
| TraderCockpit | Public landing experience, simulated Apollo preview, content production, claims review, social operations | Reads only allowlisted public product data from `product-manifest/v1` |
| Future consumer repository | Apollo runtime, customer-safe workflow, authentication, product API client | Does not contain the private robustness implementation |
| Futures | Private robustness and verdict-producing engine | Read-only for this program until a separately approved service-boundary task |
| Godseye | Real-time geospatial evidence and social-video capture | Supplies sanitized `evidence-packet/v1` data only through a verified capability |
| Register | Context only | No edits, generated files, tests, staging, or cleanup |

Code, installations, credentials, node modules, and UI components do not cross repository boundaries. Integration happens through versioned contracts.

## Public product state

The landing page fetches same-origin `product-manifest/v1` and fails closed. Until a valid manifest verifies a capability, TraderCockpit presents a static, non-transactional waitlist state.

TraderCockpit must not infer missing identity, capability, platform, offer, checkout, support, or refund fields. Arbitrary creator-strategy ingestion and Apollo remain clearly labeled concepts until a consumer manifest verifies them. Copy must not promise to find alpha, guarantee performance, or imply that a strategy failing one battery can never work.

## Apollo experience

### Visual direction

Apollo should feel alive without turning evidence into decoration. Replace the current solar/CRT treatment with a fluid, bioluminescent neural-cellular system:

- **Listening:** speech energy pulls nearby filaments toward the core.
- **Thinking:** temporary branches form, test connections, and reorganize.
- **Previewing:** the proposed strategy and battery stages become visible around the core.
- **Confirming:** motion quiets and one exact consequential action receives visual priority.
- **Running:** signals propagate through the real stages reported by the consumer backend.
- **Speaking/completing:** movement resolves into a stable evidence receipt.
- **Waiting:** a restrained breathing rhythm replaces constant noise.

The living core is a navigator, not an avatar pasted onto a dashboard. Configuration, warnings, comparisons, and evidence appear as contextual workbench surfaces around it. Canvas provides atmosphere; controls and meaningful information remain semantic DOM content.

The first prototype reuses native Canvas and CSS. No rendering dependency is added unless the native prototype fails a measured requirement.

### Evidence layer

The organic shell hands technical results to a sober, undistorted evidence layer. It must show:

- Strategy rules and unresolved assumptions.
- Data range, market, timeframe, costs, and exclusions.
- Battery stages actually requested and completed.
- Distributions and failure modes, not only a headline verdict.
- Warnings, source timestamps, and reproducibility metadata.
- A durable verdict receipt suitable for later comparison.

Color or motion cannot be the only carrier of meaning. Keyboard access, readable contrast, reduced motion, and screen-reader labels are baseline requirements.

### Voice

Launch with push-to-talk. The target is local-first speech capture with explicit microphone state and a visible transcript before consequential action. Continuous wake-word listening is deferred until privacy, false-trigger, battery, and reliability measurements justify it.

Voice may navigate, clarify, compose, and preview. It cannot bypass the confirmation gate.

## Consumer journey

1. Select a provided strategy or enter a creator's claim.
2. Apollo separates explicit rules from missing assumptions and asks only necessary questions.
3. Compose and preview the proposed test without launching the verdict-producing battery.
4. Disclose required data, compute scope, limitations, estimated consequences, and unresolved inputs.
5. Require one explicit confirmation.
6. Display only progress received from the consumer backend.
7. Return an auditable verdict receipt without promising alpha.

Creator-video ingestion remains conceptual until the manifest verifies it. A transcript alone is not an executable strategy; the user must review the extracted rules before testing.

## Godseye connection

Apollo and Godseye remain separate products with separate visual identities. Apollo may receive Godseye information only when `product-manifest/v1` declares a verified `godseye-evidence/v1` capability.

The consumer backend may then return sanitized `evidence-packet/v1` objects. Apollo does not import Godseye code, embed its viewer, inspect its installation, or connect directly to Godseye sources. Evidence claims must remain tied to sources active in the captured scene.

## Social operations

ChatGPT Work owns research and deliverables; Codex owns repository and engineering work. This follows OpenAI's current [Work and Codex role guidance](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex).

### Daily workflow

1. Monitor approved news and market-event sources.
2. Rank candidate stories by audience relevance, evidence quality, and available visual support.
3. Use Godseye only when location, movement, timing, or source relationships materially improve the explanation.
4. Draft the long-form script, vertical variants, captions, thumbnail brief, description, and email copy.
5. Run the claims gate and attach sources before approval.
6. Classify inbound messages and draft replies without sending them.
7. Assemble one daily approval batch.
8. Publish only the items in the approved batch.
9. Record corrections and performance metrics against the originating story.

The initial channels are YouTube, TikTok, and email. Other platforms activate only after their authenticated tooling and platform-specific review exist. Batch approval authorizes only the listed artifacts; edits after approval require another approval.

### Quality measures

Measure the operation with:

- Claims-gate failure and correction rates.
- Draft acceptance and edit distance.
- Approval-to-publication time.
- First-three-second hold, average watch time, completion, saves, and shares.
- Email approval, delivery, reply, and correction rates.
- Apollo task completion, configuration errors, confirmation comprehension, evidence comprehension, and user trust.

Views alone do not establish quality, causality, or a repeatable advantage. No workflow is described as viral without measured evidence.

## Delivery order

1. Review and merge this plan and the repository `AGENTS.md` policy.
2. Review and merge the existing manifest/automation-boundary work.
3. Replace the simulated Apollo visual with the native organic-intelligence prototype.
4. Test responsive, keyboard, screen-reader, and reduced-motion behavior.
5. Validate good, missing, malformed, and unsupported manifests locally.
6. Establish the future consumer repository and its customer-safe API contract in a separate decision.
7. Add Work-based draft preparation and batch-approval records before publisher automation.
8. Activate a publishing adapter only after a real account and review path are verified.

Each implementation slice uses one branch, worktree, reviewable diff, and pull request. A direct `deploy` instruction invokes the Luna workflow in `AGENTS.md`; the primary agent remains responsible for implementation and approval.

## Acceptance criteria

- TraderCockpit consistently describes its media and marketing role.
- The canonical landing URL is `https://javin23863.github.io/tradercockpit/`.
- Static content remains an honest waitlist when the manifest is absent or invalid.
- Apollo is presented as an interface concept until verified.
- The organic preview is visually distinct from Godseye and preserves accessible DOM content.
- One explicit confirmation precedes any verdict-producing full battery.
- No fabricated capabilities, progress, results, history, sources, or performance claims appear.
- Social drafts pass the claims gate and an operator-approved batch before publication.
- Futures and Register remain untouched.

## Explicit deferrals

- Wake-word listening.
- A direct Godseye viewer embed.
- Unsupervised public posting or email sending.
- Additional social-platform adapters.
- A headless Godseye CLI.
- Removal of `studio-kit` or vendored Three/Draco files until live imports are measured in a separate cleanup pass.
