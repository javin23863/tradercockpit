# 🎮 Unreal Engine 5.8 — deep setup (UnrealClaude MCP)

Unreal is the highest detail/depth ceiling in the studio: a UE editor **plugin + MCP server**
(`UnrealClaude`, github.com/Natfii/UnrealClaude) that lets an agent drive the editor (actors, Blueprints,
levels, materials, Sequencer, viewport capture) to build + render cinematic photoreal 3D.

This is the deep companion to `tool-guides/unreal.md` (the overview). Unreal is an **external install you
provide** — it's the one heavyweight tool the kit doesn't bundle.

---

## What you download (the two big installs)

1. **Unreal Engine 5.8** — free, via the [Epic Games Launcher](https://www.unrealengine.com/download).
2. **Visual Studio 2022 (Community, free) + the "Game development with C++" workload.**
   The UnrealClaude plugin is a **C++ editor plugin with no prebuilt binaries**, so UE cannot compile or open
   it without the MSVC toolchain. In the VS installer, check **"Game development with C++"** (it pulls MSVC +
   the Windows SDK). *(Newer VS versions with the C++ workload also work — UE 5.8 accepts the current toolchain.)*

You also need **Node.js** (for the MCP bridge) and an MCP-capable client (e.g. Claude Code / Claude Desktop).

---

## Setup checklist

1. **Create a UE 5.8 C++ project** — Games → Blank → **C++** (not Blueprint-only; the plugin needs a C++ project
   to compile). Call it whatever you like, e.g. `StudioProject`.
   - ⚠ **Put the project on a NON-synced drive** (e.g. `C:\Unreal\` or `D:\Unreal\`), **NOT inside a cloud-synced
     folder** (OneDrive/Dropbox). The plugin's own README warns that sync causes request hangs (a file-on-disk race).
2. **Add the plugin** — copy `UnrealClaude` into `<YourProject>/Plugins/UnrealClaude/`. Make sure its
   `.uplugin` `EngineVersion` is set to `5.8.0`, and fetch its MCP bridge (`Resources/mcp-bridge/`) then
   `npm install` inside that folder.
3. **Build the plugin** (needs VS2022 + UE 5.8):
   ```
   "<UE_5.8>/Engine/Build/BatchFiles/RunUAT.bat" BuildPlugin -Plugin="<YourProject>/Plugins/UnrealClaude/UnrealClaude.uplugin" -Package="<out>" -TargetPlatforms=Win64
   ```
4. **Wire the MCP server** into your MCP client's config (e.g. `claude_desktop_config.json`)
   as a **stdio** entry (snippet below, with the real absolute path).
5. **Verify the live seam:** open the editor → `curl http://localhost:3000/mcp/status` returns project JSON; the
   Output Log shows `MCP Server started on http://localhost:3000` + `Registered N MCP tools`.

### The MCP config entry (stdio, not URL)
```json
"mcpServers": {
  "unrealclaude": {
    "command": "node",
    "args": ["<ABSOLUTE_PATH>/Plugins/UnrealClaude/Resources/mcp-bridge/index.js"],
    "env": { "UNREAL_MCP_URL": "http://localhost:3000" }
  }
}
```

---

## How it works (so the wiring makes sense)

Two cooperating servers:
1. **In-editor C++ HTTP server** — baked into the plugin, **auto-starts when you open the UE editor**, listens on
   **`http://localhost:3000`** (status: `GET http://localhost:3000/mcp/status`). No toggle.
2. **Node.js MCP bridge** — `Resources/mcp-bridge/index.js`. The client spawns it over **stdio**; it relays your
   commands to the editor's HTTP server. This is what makes the UE tools callable.

So the client config entry is a **stdio command** (`node …/index.js`), *not* a URL.

---

## Drive it — two ways

Launch the project (loads the plugin + starts `:3000` ~15s after the project loads), then:

1. **Direct HTTP (works immediately, no client restart):** `POST http://localhost:3000/mcp/tool/<name>` with a
   JSON body of the args. Tools include `spawn_actor, get_level_actors, set_property, move_actor, delete_actors,
   run_console_command, execute_script, capture_viewport, blueprint_query/modify, anim_blueprint_modify,
   material, asset_search, open_level, character, enhanced_input`. `capture_viewport` returns the frame as
   `base64` (JPEG) in the JSON — decode + view it to SEE the editor. Rotation/scale/location = `move_actor`
   (NOT `set_property`, which is for component props like `LightComponent.Intensity`).
2. **Native MCP tools (`mcp__unrealclaude__*`):** the bridge enumerates the editor's tools **at client startup** —
   so if the editor was down when the client started, only `unreal_status` registers. **Gotcha:** to get all the
   tools natively, the editor must be up FIRST, then restart the client so the bridge re-enumerates. Until then,
   use the direct HTTP path (#1).

**The working loop for video:** build scene (spawn/move/material) → `capture_viewport` to check by eye → iterate
→ Sequencer + Movie Render Queue → **MP4** → into the studio assembly (`STUDIO.md`: VO + captions).

---

## ⚠ Honest unknowns (verify at build time — do NOT assume)

- **Compile on 5.8:** UE 5.8 re-typed `FJsonObject::Values` keys (`FString` → `TSharedString`), so a plugin
  written against 5.7 may need a few source fixes (wrap JSON keys in `FString(...)`) before it compiles clean.
  Only the actual build proves it; patch compile errors as they appear.
- **.NET SDK:** UE's UnrealBuildTool normally bundles its own; install **.NET 8 SDK** only if the build complains.
- **Exact VS component pins** for 5.8 — "Game development with C++" is the standard answer; confirm against
  Epic's 5.8 docs if the build errors on a missing component.

Until Unreal is set up, the studio runs great on **Hyperframes + Remotion** (both $0 and local). See `STACK.md`.
