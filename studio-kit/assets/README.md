# Assets — Sample Arsenal + Full Free Library

This folder ships a small **curated sample** so you have working examples the moment you
open the kit, plus the fetcher that pulls the **complete free CC0 library** on demand.

## What's here
- `samples/hdris/` — 2 HDRI environment maps (2K, .hdr) for image-based lighting in the
  Three.js / Hyperframes compositions.
- `samples/textures/` — 2 PBR texture SETS (Diffuse / Normal / Roughness / AO / Displacement).
- `samples/props/` — 2 ready-to-use 3D props (glTF + textures) for set dressing.
- `arsenal-fetch.cjs` — downloader for the full library.
- `00-INDEX.json` — manifest of every asset the fetcher can pull.
- `arsenal-README.md` — the arsenal's own reference notes.

## Licensing
All bundled samples are **CC0 (public domain)** from [Poly Haven](https://polyhaven.com) —
free to use in personal and commercial work, no attribution required.

## Get the full library (free)
```bash
node arsenal-fetch.cjs
```
This fetches more CC0 **HDRIs, textures, and 3D props** from Poly Haven and builds a standalone,
license-clean asset library under `samples/` for you to draw from. It's a library you pull assets
*from* by hand — it doesn't auto-wire anything into the compositions. Drop the HDRIs/textures/props
you want into your Three.js / Hyperframes or Unreal scenes as needed.
