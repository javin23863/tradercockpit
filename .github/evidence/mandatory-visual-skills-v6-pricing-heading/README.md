# Mandatory visual-skills v6 Pricing heading acceptance

Reviewed visible implementation: `28beaeb5395af1e07a880a1c45d529328bf83552`.

A fresh Pricing appraisal found the narrow Availability rail clipping its heading at the 1440 px desktop viewport. The fix scopes supporting-rail heading typography to the available width without changing the page hierarchy.

- Before (`6b6a1f8`): 64 px heading; 305 px scroll width in a 266 px content box.
- After (`28beaeb`): 36 px heading; 266 px scroll width in a 266 px content box.
- Fresh all-page acceptance: 41 pages × desktop/mobile = 82/82 HTTP 200.
- No page errors, horizontal overflow, or hidden reveal targets were found.
- Reduced-motion acceptance: 5/5 PASS.
- Pricing keyboard-focus journey: PASS.
- Desktop Pricing full-page evidence confirms the Availability heading is no longer cropped.
- Mobile Pricing remains within the existing responsive composition.

`render-receipt.json` binds the full browser run to the source commit; `pricing-heading-measurement.json` records the focused before/after geometry.
