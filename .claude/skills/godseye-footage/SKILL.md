---
name: godseye-footage
description: Capture purposeful Godseye geospatial footage for TraderCockpit through its versioned automation and evidence contract. Use for a location flyover, chokepoint map, geopolitical geography, attributable replay, or verified geospatial b-roll.
---

# Godseye footage

Godseye is a separate product. TraderCockpit may use only `window.godseyeAutomationV1(request)`
through `tools/visuals/godseye_capture.mjs`; never inspect or depend on Godseye DOM, Cesium internals,
selectors, presets, layers, basemaps, or source paths.

Before each capture, read the current vault `[[God's Eye Footage Engine]]` receipt and verify the
exact approved source commit, runnable package commit, `godseye-automation/v1` readiness, and
returned `evidence-packet/v1`. Forward capture requires package/source parity. The current package
is `release-main-c9d040e`, built from exact merged source commit
`c9d040e2f0dd998148c509f7417503b1acbddee0`; its `Godseye.exe` SHA-256 is
`011b6ce911adb586dc8d49c0c1d7c8dfe1600e4f70e29eb6984caabc7b6f0977`. The package passed 179
tests, the production build, Windows packaging, and a live `godseye-automation/v1` readiness probe
on 2026-07-16. The preserved `release-final-92a00ae` package is historical only. Never substitute
an unversioned desktop/repo build.

## Purpose gate

Use 0–1 Godseye shot in a normal flagship. Include it only when the shot does one of these:

- teaches geography that explains the market mechanism;
- shows an observed layer supported by the returned evidence packet; or
- replays an attributable event supported by the contract.

Generic globe motion, atmosphere, or “because we have it” fails. Godseye never proves live ships,
satellites, force posture, attacks, or attribution unless the exact evidence packet does.

## Workflow

1. Write the narration beat first and state the shot's explanatory purpose.
2. Write a minimal shot JSON using the schema documented in `[[God's Eye Footage Engine]]`.
3. Run `node tools/visuals/godseye_capture.mjs --dry-run <shots.json>`.
4. Start the approved versioned package with CDP, confirm contract readiness, then capture.
5. Preserve the returned evidence packet beside the clip.
6. Inspect a full-resolution midpoint and the in/out boundaries. Reject blank, clipped,
   overexposed, underground, generic, or unsupported footage.
7. Add only the accepted clip to `scene-plan.json`; visible subject and narration must agree.

If the approved package or contract is unavailable, omit Godseye and continue with sourced charts
or news. Do not edit, rebuild, or borrow from the separate repository in a TraderCockpit task.
