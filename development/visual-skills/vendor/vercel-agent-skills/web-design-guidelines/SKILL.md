---
name: web-design-guidelines
description: Review UI code for Web Interface Guidelines compliance using the repository-pinned guideline snapshot.
metadata:
  author: vercel
  version: "1.0.0"
  argument-hint: <file-or-pattern>
---

# Web Interface Guidelines

Review files for compliance with the pinned Web Interface Guidelines checked into this repository.

## How It Works

1. Read `../../vercel-web-interface-guidelines/command.md` from this vendored bundle.
2. Read the specified files or product surface under review.
3. Check against all applicable rules in the pinned guideline snapshot.
4. Output findings in the terse `file:line` format defined by that snapshot.

## Pinned-source rule

Do not fetch or apply mutable `main` content during ordinary implementation or review. The exact upstream skill is preserved as `UPSTREAM-SKILL.md`; this local wrapper intentionally replaces its network-fetch step so the review standard is reproducible and works offline.

Only an explicit visual-skill refresh may consult upstream. A refresh must review the changed upstream content, update the pinned `vercel-web-interface-guidelines/command.md`, update `UPSTREAMS.json`, preserve license/source notices, and commit those changes together.
