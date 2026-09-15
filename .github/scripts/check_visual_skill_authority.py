#!/usr/bin/env python3
"""Enforce checked-in visual-development authorities for public UI work."""
from __future__ import annotations

from pathlib import Path
import json

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "development" / "visual-skills"
UPSTREAMS = ROOT / "UPSTREAMS.json"
AGENTS = REPO / "AGENTS.md"
DESIGN = REPO / "DESIGN.md"

EXPECTED = {
    "awesome-design-md": "8147538b4226ae41e2487a9179e3bcc1f68e8554",
    "vercel-agent-skills/web-design-guidelines": "063bee94c3f4df8453406c830b0a7df0f2860278",
    "vercel-web-interface-guidelines": "e3d624baaf29dc1fc645aff3e38f03e564d2d6b1",
    "taste-skill": "ccbc15639c97057cbfcf32ecebc38ef716e4bb37",
}

REQUIRED_FILES = (
    ROOT / "README.md",
    ROOT / "CHECKLIST.md",
    ROOT / "vendor" / "vercel-agent-skills" / "web-design-guidelines" / "SKILL.md",
    ROOT / "vendor" / "vercel-web-interface-guidelines" / "command.md",
    ROOT / "vendor" / "taste-skill" / "skills" / "redesign-skill" / "SKILL.md",
    ROOT / "vendor" / "taste-skill" / "skills" / "image-to-code-skill" / "SKILL.md",
    ROOT / "vendor" / "taste-skill" / "skills" / "gpt-tasteskill" / "SKILL.md",
    ROOT / "vendor" / "awesome-design-md" / "LICENSE",
    ROOT / "vendor" / "taste-skill" / "LICENSE",
    ROOT / "vendor" / "vercel-web-interface-guidelines" / "LICENSE",
)

def main() -> int:
    problems: list[str] = []
    for path in REQUIRED_FILES:
        if not path.is_file() or path.stat().st_size < 40:
            problems.append(f"missing or empty visual authority: {path.relative_to(REPO)}")

    try:
        data = json.loads(UPSTREAMS.read_text(encoding="utf-8"))
    except Exception as exc:
        problems.append(f"invalid visual upstream manifest: {exc}")
        data = {"sources": []}

    sources = {row.get("name"): row for row in data.get("sources", []) if isinstance(row, dict)}
    for name, commit in EXPECTED.items():
        row = sources.get(name)
        if not row:
            problems.append(f"missing upstream provenance: {name}")
        elif row.get("commit") != commit:
            problems.append(f"unexpected pinned commit for {name}: {row.get('commit')}")

    design_docs = list((ROOT / "vendor" / "awesome-design-md" / "design-md").glob("*/DESIGN.md"))
    if len(design_docs) < 50:
        problems.append(f"awesome-design-md snapshot is incomplete: {len(design_docs)} DESIGN.md files")
    taste_skills = list((ROOT / "vendor" / "taste-skill" / "skills").glob("*/SKILL.md"))
    if len(taste_skills) < 8:
        problems.append(f"taste-skill snapshot is incomplete: {len(taste_skills)} SKILL.md files")

    for authority in (AGENTS, DESIGN):
        if not authority.is_file():
            problems.append(f"missing root visual authority: {authority.name}")
            continue
        text = authority.read_text(encoding="utf-8")
        if "development/visual-skills" not in text:
            problems.append(f"{authority.name} does not require the vendored visual skills")

    checklist = (ROOT / "CHECKLIST.md").read_text(encoding="utf-8") if (ROOT / "CHECKLIST.md").is_file() else ""
    for marker in ("Render every public HTML page", "Generated pages", "reduced-motion", "visual PASS"):
        if marker.lower() not in checklist.lower():
            problems.append(f"visual checklist missing rendered acceptance marker: {marker}")

    if problems:
        print("VISUAL SKILL AUTHORITY: FAIL")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print(
        "VISUAL SKILL AUTHORITY: PASS "
        f"({len(EXPECTED)} pinned upstreams, {len(design_docs)} design references, "
        f"{len(taste_skills)} Taste skills)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
