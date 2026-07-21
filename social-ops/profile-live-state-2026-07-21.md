# Social profile live state — verified by API/CDP read — 2026-07-21

**Why this exists:** the 2026-07-20 approval sheets (`profile-copy-2026-07-20.md`,
`pre-doctrine-verbiage-defects-2026-07-20.md`) were written and gate-checked but **never applied**,
and they admit the live IG/TikTok/FB bios were *never read* ("exact live bio was not captured").
That is how "all pages fixed" was reported while the live YouTube description was still the old
awkward copy. This file records the **actual live state**, read from the API (YouTube) and CDP
(IG/TikTok/FB), not from cache.

## APPLIED this session (YouTube — the one real defect)

Channel description rewritten live via `tools/channel_seo.py` and verified by API read-back
(channel `UCBc6RR49Qk5vtDQaw8BjH3A`). Style gate: **PASS, 0 blocks**.

Removed: `12 phases of statistical torture`, `No lambo`, `publishes the kill list`, and the dead
`https://javin23863.github.io/soical/` link (its trailing raw URL was what tangled into the Share
button). Added the operator-approved retained line **"You are the market."** Kept the exact mandatory
disclaimer.

Live description now (421 chars):

```text
TraderCockpit — evidence-first market analysis. Oil, equities, rates, currencies, and the geopolitics that move them.

The strategies the internet sells you, coded honestly and put through the tests a real desk runs before risking a dollar. What holds up, holds up. What breaks, breaks on camera.

You are the market.

No signals. No courses. Research tooling, not financial advice. No performance is promised or implied.
```

`tools/channel_seo.py` `DESCRIPTION` constant updated to match live (was a different, unapplied
market-news draft). `KEYWORDS` unchanged.

## Live-read state of the other three surfaces (CDP, 2026-07-21)

**None carried the awkward gauntlet-slop or the dead `soical` link.** All three already have a clean
market-news bio. The operator's concern that the same bad copy was everywhere was unfounded — proven
by live read, not assumed.

| Surface | Handle | Live bio (read 2026-07-21) | Link | State |
|---|---|---|---|---|
| Instagram | `@tradercockpit` (14 followers) | `📊 Markets, read plainly. Oil, stocks, rates & geopolitics → your portfolio. News & education, not advice. ▶️ Daily on YouTube 👇` | YouTube | clean |
| TikTok | `@trader.cockpit` (0 followers, 28 likes) | `Markets, read plainly. Oil • equities • rates → your portfolio. Not advice.` | none (no clickable field) | clean, name-casing nit |
| Facebook | `Tradercockpit` (page id 61591774715570) | Intro: `Markets, read plainly. Oil, equities, rates, and the geopolitics moving them, translated into what it means for your portfolio. News & education only. Not financial advice.` | `youtube.com/@Thetradercockpit` | clean, logged out |

Screenshots: `scratchpad/social-shots/{instagram,tiktok,facebook}.png` (session-local).

## Nits — ALL RESOLVED 2026-07-21 (operator "fix all"; every write verified by live read-back)

1. **TikTok** — name `trader cockpit` → **`TraderCockpit`**, bio → **`You are the market. Not
   financial advice; no performance promised.`** (66/80). Verified live. Scar repeated: the run that
   "failed" (immediate read-back showed old values) had actually saved — TikTok read-after-write lag,
   same as YouTube. Native-React-setter alone does NOT commit on TikTok; a real save needs the field
   values in React state (keystroke or Input.insertText path).
2. **Facebook** — operator logged the CDP Chrome into FB. Bio → **"You are the market. Oil, equities,
   rates, and the geopolitics moving them — read plainly, mapped to your portfolio. Research tooling,
   not financial advice. No performance is promised or implied."** (verified live). **Username set:
   `facebook.com/tradercockpit`** (was never set; operator chose it 2026-07-14, applied now). **Name
   `Tradercockpit` → `TraderCockpit` submitted** — FB requires the account password (operator typed
   it) and up to 3 days review + 60-day lock; pending FB's review, not ours.
3. **Instagram** — session restored after the debug-Chrome relaunch (no SSO needed). Bio →
   **"You are the market. / Daily market news on YouTube ↓ / Research tooling, not financial advice.
   No performance is promised or implied."** (129/150, full mandatory disclaimer now fits). Name was
   already `TraderCockpit`; link stays YouTube. Verified live. Followers 14 → 27 at read time.
4. **Voice unified.** All four surfaces now carry "You are the market." + the full mandatory
   disclaimer (TikTok carries the closest 80-char honest equivalent).

### CDP driving lessons (cost ~6 iterations, keep)
- **FB settings content lives in an IFRAME** — top-document queries see nothing; search `p.frames()`.
- **Per-keystroke `elementHandle.type()` stalls CDP on slow Meta pages** (`Runtime.callFunctionOn
  timed out`); use ONE `keyboard.sendCharacter(text)` (Input.insertText) after focus+select.
- **A one-shot detector races the SPA render** — poll up to ~24s for content, never single-check.
- **FB save buttons are sometimes `a`/leaf-div, not `button`** — match leaf text, click closest
  actionable ancestor.
- **Closing all tabs in the debug Chrome EXITS it** — sessions survive on disk; relaunch with the
  same `--user-data-dir=C:\Users\MSI\.chrome-cdp --remote-debugging-port=9333`.
- **Page-admin context is per-click-path**, not per-URL: direct `settings/?tab=profile` lands in
  PERSONAL settings; page rail → Page setup → Name keeps PAGE context.

## Scar reinforced
`social-surface-audit` rule zero held again: cache said "profile SEO already good / all pages fixed";
live read said YouTube was still broken and the other bios had never been captured at all. **Read the
surface. Never report a profile fixed from a cache or an unapplied approval sheet.**
