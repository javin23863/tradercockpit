# TraderCockpit Public Design Authority

This file is the product-facing UX authority for every public TraderCockpit page. The process is adapted from the DesignMotionHQ UX Engine methodology; it is a review method, not a visual-style donor. The canonical TraderCockpit website visual authority is `.github/WEBSITE-CURRENT.md`; its measured geometry, product truth, and data provenance remain controlling.

## Shipping rule

A public page is not complete because it renders. Before release it must pass all eight review dimensions below, desktop and mobile browser acceptance, public-claims checks, and the repository's visual/data integrity gates. Every public HTML page has a corresponding record in `docs/ux-page-contracts.v1.json`.

## Mandatory visual-development skills

Visible work must use the checked-in authorities under `development/visual-skills/`. At minimum, reviewers read the vendored Vercel web-design guidance, Taste redesign/image-to-code guidance, relevant `awesome-design-md` references, and `development/visual-skills/CHECKLIST.md`. Exact upstream revisions are recorded in `development/visual-skills/UPSTREAMS.json`.

These external skills are mandatory review inputs, not a substitute for TraderCockpit truth. Product manifests, owner-approved screenshots, measured geometry, accessibility, data provenance, and this document take precedence when guidance conflicts. A visual PASS requires fresh rendered desktop and mobile evidence from the reviewed commit; source review or inherited audit metadata alone cannot close parity.
## 1. Intent discovery

Name the audience, the single job the page should help them complete, and the worst mistake the page could cause. A page may educate, sell, route, explain, or resolve a state, but it must not attempt all of those at equal priority.

For marketing surfaces, lead with the concrete product or outcome rather than adjectives about the product. For research education, lead with the question or decision the evidence supports. Internal architecture, release machinery, implementation detail, and developer-roadmap language never belong in the public hierarchy.

## 2. Information hierarchy

Every page has one focal point. Marketing and commerce surfaces have one primary action; secondary actions must be visually subordinate. Article and research pages may use reading/interaction rather than a conversion CTA as the primary task.

Product proof follows product claims as early as practical. Repeated cards, badges, pills, gradients, and icon rows are not hierarchy by themselves. Density is deliberate: information-rich pages may be dense, but priority must remain legible through size, weight, contrast, and spacing.

## 3. State completeness

Dynamic features define loading, success/content, empty, error, and blocked/unavailable states whenever those states can occur. Empty states explain what happened and the next useful action. Errors state what the user can do next. Missing evidence remains missing; no renderer, copy, or fallback invents a value.

Disabled or unavailable actions must be either hidden until relevant or paired with an accessible explanation. Loading is not represented as disabled.

## 4. Form UX

Inputs use persistent labels; placeholder text is an example, never the label. Required, optional, focus, error, success, disabled, and submitting states are distinct when applicable. Validation copy names the problem and recovery. Sensitive inputs and third-party submission boundaries remain explicit.

## 5. Feedback and affordance

Primary actions are visible without hover. Touch interaction never depends on hover state. Interactive targets are at least 44px on coarse pointers/mobile layouts unless the element is purely inline text. Keyboard focus remains visible and distinct from selected/active state.

Use immediate local feedback for direct manipulation, progress for longer work, and confirmation only when the outcome cannot be inferred from the changed surface. Motion supports causality; it does not replace status or meaning.

## 6. UX audit

Release review checks blocker, major, and minor findings. Blockers include unreachable actions, false claims, broken links, inaccessible essential controls, data invention, privacy/security mistakes, and layouts that hide required information. Major findings include unclear hierarchy, unexplained state, poor mobile operation, or contradictory copy.

All 41 public HTML pages are browser-audited at desktop and mobile widths. New public pages must be added to the page-contract authority before CI can pass.

## 7. Design system discipline

Use semantic tokens rather than page-local visual inventions. Theme 2 keeps a 4px-derived spacing rhythm, bounded type hierarchy, warm near-black layered surfaces, ivory typography, and one champagne/brass interface accent. Red and green remain semantic research/risk colors where data requires them; cyan/teal may remain inside truthful product captures or analytical graphics but is no longer the generic public-site action language. State variants are designed, not inferred from opacity alone.

Core interaction tokens are declared in shared CSS, including `--ux-touch-target`, spacing tokens, focus treatment, and motion timing. Page-specific styling may refine composition but must not create a second visual language.

## 8. Visual character

Each page is reviewed on four explicit axes:

- **Type:** hierarchy must read before decoration; long-form text prioritizes legibility.
- **Color:** champagne/brass carries public-site action and controlled illumination; red/green carry negative/positive research semantics when data warrants them; color is never the sole carrier of meaning.
- **Space:** dense research material uses grouping and rhythm instead of arbitrary panels; marketing uses breathing room around the focal proof.
- **Finish:** depth, glass, 3D, shadows, and motion must reinforce real structure. Decorative effects cannot imply analytical dimensions that do not exist.

## Anti-slop requirements

Avoid abstract adjective-first headlines, generic feature-icon rows, equal-weight CTA pairs, fabricated social proof, decorative gradients without information, repetitive panel grids, and copy that narrates how the website was constructed. Name the product, task, evidence, limitation, or consequence directly.

Screenshots and demonstrations must be real/current or explicitly labeled synthetic. Research graphics use the dimensionality warranted by their data contracts: VTK 3D where spatial dimensions are meaningful, production 2D where time/price or two-variable structure is the truth, and no reconstruction where the producer does not expose sufficient data.

## Navigation and mobile

Primary destinations remain visible in ordinary navigation; search is an accelerator, not the only route. Tabs and segmented controls require visible active and focus states. Mobile layouts may reflow or stack but may not hide the only path to an action. Coarse-pointer controls use the shared 44px minimum target contract.

## Release evidence

Current rendered acceptance is recorded only under `.github/evidence/current-website/` and `.github/site-appraisal-current.md`. The machine-readable page authority is `docs/ux-page-contracts.v1.json`, enforced by `.github/scripts/check_public_ux.py` in the `website-integrity` workflow.
