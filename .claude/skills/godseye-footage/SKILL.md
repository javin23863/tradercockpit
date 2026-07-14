---
name: godseye-footage
description: >
  Capture God's Eye globe b-roll for videos: write a shot list, drive the app over CDP,
  record, verify frames. Use when the user asks for globe footage, God's Eye shots,
  geopolitical b-roll, or a location flyover/night-lights/military-flights shot.
---

# godseye-footage

> Operator ruling 2026-07-14: on TraderCockpit videos GE is **b-roll used SPARINGLY**
> (~15% runtime — cold open / one flyover / outro), NOT the main visual. Live TradingView
> TA charts dominate. Overusing GE got video-02 rejected. See daily-news-video visual doctrine.

Tool: `tools/visuals/godseye_capture.mjs` (this repo). App:
`C:\Users\MSI\repos\godseye\release\win-unpacked\GodsEye.exe` — separate repo, read-only.

## Run
```powershell
Start-Process "C:\Users\MSI\repos\godseye\release\win-unpacked\GodsEye.exe" -ArgumentList "--remote-debugging-port=9222"
# wait ~15s, verify: Invoke-WebRequest http://127.0.0.1:9222/json/version
node tools\visuals\godseye_capture.mjs --dry-run <shots.json>       # schema check
node tools\visuals\godseye_capture.mjs <shots.json> <outdir>        # capture
```
Skip-existing by mp4 name; failed shot auto-reloads app + retries once.

## Shot JSON
`{name, lon, lat, height, headingDeg, pitchDeg, holdSec, settleSec?, orbitDegPerSec?,
fromHeight?, flyDurationSec?, preset?, caption?, clickIds?[], scanAfter?[], scanWaitSec?}`
- `fromHeight` (e.g. 18000000) records the descent — use for cold opens.
- `clickIds`: `"layer:NIGHT LIGHTS"` (row-text match), `"basemap:aerial"`, or element ids.
  `layer:` is IDEMPOTENT — ensures ON (`layer:NAME:off` for off). Never assume toggle:
  default-on layers (MILITARY, CRITICAL INFRA, FLIGHTS, SHIPS) got silently hidden by
  blind toggle clicks in ge-raw4 (2026-07-13).
- `scanAfter`: view-bboxed scan buttons clicked after camera arrives; `scanWaitSec` (default 5).
- `caption` = burned lower-third (DOM HUD is not in the canvas capture).
- Harness auto-applies quality: `viewer.resolutionScale = 2` + 3D-tiles SSE 16→8
  (re-applied after crash-reload). Raise SSE back if capture stutters.

## Cinematography rules (frame-review learned — follow these)
- Frame south/top-down (pitch -70…-85) or along-feature; heading 0 from a coast shows
  boring interior.
- Night lights ONLY render on `basemap:aerial`; put night shots LAST (basemap stays switched).
- NEVER set the viewer clock — `utcHour` killed the ge-raw3 run (Cesium fatal on the final
  shot, 2026-07-13). Region must be naturally dark (Gulf ≈ 22-02 UTC) or fake it with DUSK preset.
- AIS (aisstream.io) has NO Persian Gulf receiver coverage (src/ships.ts:29 comment); a wide
  view falls back to the NW-Europe default bbox, so "ships in the strait" captions are
  unfulfillable — never caption-promise live AIS in the Gulf. Verify overlay data EXISTS
  (probe entity counts over CDP) before captioning any live layer.
- No low-altitude orbits (blur smear) — use fromHeight zoom instead.
- Keep the in-app FRED oil dock out of frame (stale prices).
- ALWAYS verify: extract 1 frame per clip (`ffmpeg -ss <mid> -frames:v 1`) and Read it
  before accepting a shot. Reshoot bad framing — cheap.

Full rules + best-shot examples: vault note "God's Eye Footage Engine"
(C:\Users\MSI\Desktop\TraderCockpit-Vault).
