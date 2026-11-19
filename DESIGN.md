# Trader Cockpit website design

The design rules for every public page. One stylesheet (`docs/assets/site.css`), one header and footer (`.github/scripts/site_chrome.py`), one data file for product facts (`.github/product/capabilities.v1.json`). A page that needs something these do not give gets it added there, never in the page.

## Shipping rule

A page ships when it has been looked at in a real browser at 1440 and 390 pixels wide, every check in `website-integrity` passes, and it holds to the eight sections and the anti-slop list below. Every public HTML page has a row in `.github/product/ux-page-contracts.v1.json`.

## 1. Intent discovery

Name the reader, the one job the page does for them, and the worst mistake it could cause. Product pages lead with what the trader gets. Guides lead with the question they answer. How the site, the app or the company works inside never appears on a page.

## 2. Information hierarchy

One focal point and one filled button per view: the download once the app is out, the early access list until then (`site_chrome.cta()` follows `docs/product-manifest.v1.json`). The product is shown as early as it is claimed. Hierarchy comes from size, weight and space; cards, pills and labels are not hierarchy.

## 3. State completeness

Everything is visible with JavaScript off and with motion reduced. A script that fills a status line has a plain default. An empty or failed state says what happened and what to do next. A missing fact stays missing: nothing invents a value.

## 4. Form UX

Inputs have a visible label; a placeholder is never the label. Errors name the problem and the fix and keep what was typed. The early access form is the site's only form, and it posts only to the approved list.

## 5. Feedback and affordance

Actions are visible without hover. Touch targets are 44px on a phone. Keyboard focus is a 2px gold ring. Hover and focus answer within 150ms, with colour only: no entrance animations, parallax or scroll effects.

## 6. UX audit

Blockers: a false claim, a broken link, an action that cannot be reached, text under 4.5:1 contrast, sideways scroll, an invented figure, a private or internal detail. Major: unclear hierarchy, copy about the site itself, a picture that is not a real screen of the current app.

## 7. Design system discipline

Tokens live at the top of `site.css`.

- **Colour.** The app's own dark ground and gold: `--ground`, `--panel` (raised bands), `--raised` (behind app screens), `--line`, `--ink`, `--ink-2` (secondary text, still above 10:1), `--gold` (links, the current page, the one filled button). No other accent, no gradients, no glows.
- **Type.** Headings in Bahnschrift, the DIN face Windows ships, with DIN and condensed fallbacks elsewhere; text in Segoe UI. Read text is 17px; nothing is under 13.5px. One scale: `--t1`, `--t2`, `--t3`, `--lead`, `--body`, `--small`.
- **Space.** One scale, `--s1` to `--s10` (4 to 128px). One container, 1240px with a fluid gutter. Text starts on the container's left line.
- **Components.** `btn` (and `btn primary`), `more` (a bold text link), `shot` (an app screen on a raised panel), `band`, `split`, `stack`, `cols-2`, `ticks`, `guide-list`, `plans`, `kv`, `prose`, `details.qa`, `note`. Radii are 4, 6 and 10px.

## 8. Visual character

- **Type** carries the look: large condensed headings, plain sentence case.
- **Colour** is the app's: a visitor who opens the app after the site sees the same ground and the same gold.
- **Space** is generous around app screens and tight inside lists.
- **Finish** is flat. Elevation is a lighter surface and a 1px line. No shadows, glass, 3D or motion.

## Anti-slop requirements

- Every picture of the product is a real screen of the current app on a real market. No renderings, room scenes, synthetic plots or mock charts.
- No kicker or eyebrow above a heading, no 01/02/03 markers unless the order is the information, no meta chips, no arrows after links, no middle-dot strings.
- No grid of identical icon cards, no cards inside cards, no strip of big numbers over one-word labels, no testimonials or logo walls.
- Copy says what the trader gets in plain words: short, concrete, present tense. No competitor's strengths, no dates, no supplier or internal names, no "not open yet" lists, no text about how the site is organised.
- Banned words and constructions are listed in the standard this file was written from; `check_public_ux.py` refuses the worst of them.
- A capability the app does not back is left out. A capability the app has is on Features, and every paid tier on Pricing lists all of them.

## Navigation and mobile

The header is the same on every page: Features, Pricing, Community, Learn, Support, Search and the one button. The footer lists Product, Guides and Company links and carries the one legal line. On a phone the header wraps to two rows and stops being sticky.

## How pages are built

Run, in this order: `generate_product_pages.py` (Home, Features, Pricing), `generate_concept_pages.py`, `generate_community_pages.py`, `site_chrome.py` (header, footer, stylesheet, titles and the Learn, How-to and Examples lists on every page), `search_metadata.py`, then `record_reading_pages.py "reason"`. Each has `--check`. Page titles, descriptions and h1s are in `.github/product/page-meta.v1.json`.
