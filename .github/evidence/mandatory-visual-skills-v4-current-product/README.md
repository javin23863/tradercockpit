# Current product capture follow-up

Reviewed implementation: `ed06c6256611c0b5903ee13d43957390ffa1f2fc`.

This follow-up corrects a material visual-truth defect found during appraisal: the public site still showed the retired dashboard capture after Guided Home became the current product authority.

- Replaced `docs/assets/desktop-current.png` with a fresh 1440×960 actual-app capture from the current TraderCockpit Guided Home.
- The capture shows the three resumable journeys: Try a sample, Connect my data, and Build my first strategy.
- Home and Pricing now expose Models in the current product-route description, and Home reports eight primary desktop destinations.
- Home and Pricing were rendered at 1440px desktop and 390px mobile after the replacement.
- All four renders returned HTTP 200 with no page errors or horizontal overflow.
- Browser-decoded image dimensions match the declared 1440×960 intrinsic size.
- `render-receipt.json` records the browser checks for this exact source commit.

The broader 41-page evidence remains under `mandatory-visual-skills-v1`; this directory is the exact follow-up proof for the corrected current-product capture.