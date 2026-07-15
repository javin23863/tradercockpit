---
name: open-generative-ai-local
description: Operate TraderCockpit's project-local Open Generative AI Electron studio using only stable-diffusion.cpp and DreamShaper 8. Use for offline or local-only creative image generation, local model preflight, launching the desktop studio, or exporting a generated still without MuAPI or any paid provider.
---

# Open Generative AI local

Run only the isolated checkout at <repo>/Open-Generative-AI, pinned by the integration documentation.

## Preflight

1. Confirm at least 25 GB free disk and verify the checkout commit.
2. Set OPEN_GENERATIVE_AI_LOCAL_AI_DIR=<repo>/Open-Generative-AI/.local-ai and NEXT_TELEMETRY_DISABLED=1 before launch.
3. Confirm no MuAPI or other provider key is configured.
4. Confirm the local model directory contains only the approved DreamShaper 8 SD 1.5 model and the stable-diffusion.cpp engine.

## Launch and generate

1. Start the Electron development app with npm run electron:dev; never start or expose the Next.js web server. In the Codex desktop app, obtain the required action-time confirmation before the first launch of newly downloaded software.
2. Skip the API-key prompt.
3. In Settings > Local Models, use stable-diffusion.cpp and DreamShaper 8 only.
4. Generate at 512x512 for the first proof. Review the image before increasing size or batch count.
5. Copy an accepted image into the active production's visuals folder and add its prompt, model, seed, CreativeML Open RAIL-M license, synthetic status, and source path to the existing asset manifest.

## Boundaries

- Do not download SDXL, Z-Image, Wan2GP, ComfyUI, or additional checkpoints.
- Do not enter an API key or use any cloud model button. If local inference fails, stop; do not fall back to MuAPI.
- Do not use generated images for charts, price levels, news evidence, geospatial evidence, or product proof.
- Stop the Electron process after testing or generation; leave no public listener running.
