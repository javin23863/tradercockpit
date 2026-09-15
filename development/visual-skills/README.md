# Mandatory visual-development skills

This directory is a checked-in development authority for every customer-visible change in the TraderCockpit public website: HTML/CSS/JS UI, screenshots, WebGL/VTK scenes, motion, marketing and commerce surfaces, documentation visuals, responsive behavior, and visual states. The separate desktop-product repository carries its own copy of the same mandatory skill authority.

The material is vendored so an agent cannot silently skip it because an external URL changed or was unavailable. `UPSTREAMS.json` records the exact source commit for each snapshot.

## Requirement

Before planning or implementing a visible change, read this file, `CHECKLIST.md`, the relevant TraderCockpit local visual authority, and the applicable vendored skills. A visual change is not complete from source review alone; it requires rendered appraisal evidence.

For website work the minimum required reading is:

- `vendor/vercel-agent-skills/web-design-guidelines/SKILL.md` (local offline wrapper; exact upstream copy is `UPSTREAM-SKILL.md`)
- `vendor/vercel-web-interface-guidelines/command.md`
- `vendor/taste-skill/skills/redesign-skill/SKILL.md`
- `vendor/taste-skill/skills/image-to-code-skill/SKILL.md`
- `vendor/taste-skill/skills/gpt-tasteskill/SKILL.md`
- relevant references under `vendor/awesome-design-md/design-md/`

For TraderCockpit, the most useful Design.md benchmarks include `linear.app`, `stripe`, `binance`, and `nvidia`; they are references for hierarchy, financial/product density, restraint, and depth. They are not permission to copy those brands.
## Precedence

When authorities conflict, use this order:

1. Product truth, safety, accessibility, licensing, and public-claim boundaries.
2. TraderCockpit local authorities: `DESIGN.md`, measured visual specs, approved screenshots, product manifests, and existing renderer/data contracts.
3. This mandatory visual-development policy and checklist.
4. Vendored third-party skills and design references.

Third-party instructions that require a different framework, invented content, external stock imagery, fake measurements, or an unsupported dependency do not override TraderCockpit truth. Translate the design principle into the existing stack instead.

The Taste skills sometimes prescribe GSAP, generated imagery, randomization, or placeholder image services. Those are inspiration/process defaults, not permission to add a dependency, leak a network target, invent visual evidence, or replace owner-approved imagery. If image generation is unavailable, use the checked-in owner visual authority and produce fresh rendered implementation evidence.

## Visual parity standard

"Looks consistent" is not acceptance. Compare rendered pages against the owner-approved visual authority for composition, density, dimensional hierarchy, materials, semantic market colors, typography, responsive behavior, and motion. Do not claim parity from CSS tokens, source inspection, or a contact sheet alone.

Every page family must have a distinct visual job. Repeating the same left-copy/right-diagram hero and the same equal-card grid across unrelated pages is a failure even if colors and spacing are correct. Depth must express real structure or clearly decorative atmosphere; it must never imply analytical dimensions that do not exist.
