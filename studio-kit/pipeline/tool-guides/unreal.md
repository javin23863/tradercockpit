# Unreal Engine 5.8 + UnrealClaude

**What it is:** A real, photoreal 3D film studio inside your computer — Unreal Engine 5.8 — that the agent can build and shoot inside automatically through the "UnrealClaude" bridge.

## Why it's in the pipeline / what job it does

This is the **top visual tier**. When a shot needs to look genuinely real — actual 3D worlds with real depth, cinematic film cameras, and Lumen lighting (true light bounce, reflections, shadows) — this is where it's made. Other tools fake depth and lighting; Unreal *has* them. Think real sets and a real camera, not a flat picture pretending to be 3D. The agent builds the scene, points a camera, and renders out a clean MP4.

## Setting it up (external install — you provide Unreal)

Unreal is the one heavyweight tool the kit doesn't bundle — it's a free, multi-gigabyte install you get from Epic:

1. Install **Unreal Engine 5.8** via the [Epic Games Launcher](https://www.unrealengine.com/download).
2. Create (or open) a project to shoot in — call it `StudioProject`, anywhere you like on disk.
3. Add the **UnrealClaude** MCP bridge plugin to that project's `Plugins/` folder and enable it in the editor.

Once the project is open, a small server wakes up inside the editor at `localhost:3000`. That server is the "phone line" an agent uses to drive the scene.

## How to use it

Once the project is open, the agent talks to it over that local connection — sending plain instructions like build, move, and "take a picture." For example, to grab the current frame and actually look at it:

```
POST http://localhost:3000/mcp/tool/capture_viewport
```

That returns the frame as an image the agent can decode and inspect. There are **28 tools** in all — placing objects (`spawn_actor`), moving/rotating/scaling them (`move_actor`), changing materials, running engine commands, opening different scenes, and more.

The rhythm is simple: **build the scene → capture a frame to check it → adjust → repeat.** When it looks right, it goes through Unreal's Sequencer and Movie Render Queue to produce the final **MP4**.

## Complements

Pairs with **Hyperframes** (abstract 3D motion-graphics) and **Remotion** (for assembling, captioning, and finishing the clip for social) — photoreal atmosphere from Unreal, words and polish from the others.
