# China Q2 vertical — proposal decision

Status: operator approved resuming the social-posting workflow on 2026-07-15; exact-asset publication remains fail-closed, and private production is blocked on a narration-provider decision.

Target: one 45–60 second, 9:16 vertical master adaptable to YouTube Shorts, Instagram Reels, Facebook Reels, and TikTok. No public publish is authorized.

## Execution receipt — 2026-07-15

- Reverified the official NBS release and the existing China claims; the U.S. PPI, Bank of Canada,
  and Federal Reserve Beige Book releases remain later-session packages.
- The current batch remains five drafts with no master asset, claims gate, or approval fingerprint.
- OpenMontage preflight: FFmpeg/Remotion/HyperFrames 3/3; local image generation 2/11; local video
  generation 4/19; TTS 0/6; music generation 0/3; Pixabay music search available. The approved
  cloned-voice route is not registered in the selected pipeline, so it cannot be substituted silently.
- Publisher dry-run: Instagram and Facebook ready; YouTube and TikTok missing credentials.
- The reviewed Godseye automation/evidence source is available at commit `92a00ae` in the separate
  checkout, but TraderCockpit's hardcoded packaged capture target predates that contract. Do not claim
  final Godseye capture readiness until an aligned packaged runtime is provided and dry-run verified.

## Concept options

1. **China Is Two Economies** — recommended
   - Hook: “China grew 4.3%—but the number hides two very different economies.”
   - Flow: GDP headline → 13.3% high-tech growth → 1.3% retail growth → -18.0% property investment → portfolio confirmation list.
   - Why: the cleanest primary-source story, strongest visual contrast, and most reusable format for daily authority.

2. **Strong Exports Can Warn**
   - Hook: “Export strength can be a pressure signal—not proof that household demand is healthy.”
   - Flow: industrial/export strength → weak domestic demand → global manufacturing and policy transmission.
   - Tradeoff: more differentiated, but needs more context than a sub-60-second first post comfortably holds.

3. **Five Portfolio Confirmation Checks**
   - Hook: “The GDP print is only step one. Watch these five markets next.”
   - Flow: official release → China equities → CNH → industrial metals → Asian exporters → luxury/consumer proxies.
   - Tradeoff: highly useful, but realized market direction must remain blank until timestamped price data is verified.

## Visual direction

- Dark TraderCockpit field, high-contrast ivory type, warm amber for the production side, cool cyan for demand, red only for negative values.
- Split-screen balance motif: factory/high-tech blocks rise on one side while retail/property blocks lag on the other.
- Every factual card shows “NBS China · 15 Jul 2026”; final card says “Check the reaction. Don’t assume it.”
- Captions stay inside platform-safe zones. No generic stock trading floors, fake charts, or AI presenters.

## Required build decisions

### Render runtime

- **Remotion — recommended:** React scene stack, deterministic stat cards, captions, charts, and easy reuse as a daily bulletin template.
- **HyperFrames:** HTML/GSAP-native kinetic typography and more bespoke motion; stronger for a one-off expressive piece, but less reusable and with weaker caption automation.

Both runtimes passed local availability preflight. A runtime cannot be written into the final proposal packet until the operator explicitly selects it.

### Composition mode

- **Templated — recommended:** fastest repeatable daily authority format; reuse is intentional and values remain data-driven.
- **Atelier:** one-off hand-authored composition; more distinctive but slower and not justified for a same-day bulletin unless this is treated as a hero launch asset.

### Voice

- **TraderCockpit cloned voice — recommended:** the local Chatterbox command and chunker self-test pass; an actual audio sample still requires the approved script and voice gate. This preserves the existing brand sound at zero provider spend.
- Operator-recorded narration: most authentic, but creates a manual production dependency.
- Configure an external TTS provider: automatable, but requires credentials, provider terms, and possibly spend. OpenMontage preflight currently reports no configured TTS provider.

No narration will be generated before script approval.

### Music

- **No music — recommended:** narration, restrained transitions, and one low-volume confirmation tone; best fit for trust-first same-day macro news.
- Pixabay stock bed: available through search, but requires track selection and license/source receipt.

OpenMontage preflight reports no configured music generator and an empty local music library.

## Proposed zero-spend envelope

Research and composition: $0. Asset generation: $0 if the existing local voice route is viable and no stock music is selected. Any provider account, paid operation, or material license acceptance requires a separate operator gate.

## Approval syntax

Reply with either:

`Approve recommended: concept 1, Remotion, templated, cloned voice sample, no music.`

or specify one choice from each section. Approval authorizes private production through a reviewable draft only; it does not authorize public posting.
