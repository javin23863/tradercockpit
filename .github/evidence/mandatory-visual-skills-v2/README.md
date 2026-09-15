# Mandatory visual-skills v2 rendered acceptance

Reviewed visible implementation: `f6cf4cc1a8b0a6a2f4ef842135f3be53481051a3`.

- 41 public pages rendered at 1440 px desktop and 390 px mobile: 82/82 HTTP 200.
- No captured console errors, page errors, horizontal overflow, or hidden reveal targets.
- Reduced-motion appraisal covers Home, Pricing, Docs, a generated Concept page, and Research Lab; all five remain readable.
- Keyboard-only appraisal on Pricing confirms visible focus through the skip link and primary navigation.
- Home continues to render the approved Three.js/WebGL Quant Universe; Research Lab continues to render the VTK/WebGL analytical surfaces.
- `desktop-contact-sheet.jpg` and `mobile-contact-sheet.jpg` provide all-page first-viewport appraisal; `fullpage/` covers the major page families.
- `render-receipt.json` binds browser version, route geometry, renderer state, errors, overflow, reduced motion, keyboard focus, and evidence paths to the reviewed commit.

This pass also closes the mechanical web-design findings that remained after v1: every public HTML document now declares the dark browser theme color, the shared CSS declares `color-scheme: dark`, viewport-height rules use `dvh`, touch actions are explicit, the search result scroller contains overscroll, and the Pricing product capture carries intrinsic dimensions plus lazy/async loading.

The route-specific depth treatment was separated into `docs/assets/site-visual-depth.css`, so the homepage no longer downloads the article/page-family visual rules it does not use. The local hardening gate now passes without raising its payload budgets.

Visual appraisal disposition: PASS for this implementation slice. The split stylesheet preserved the approved compositions and subject-specific scenes across the public surface while reducing the homepage text payload.