#!/usr/bin/env python3
"""Keep scene-plan.json narrations verbatim-synced to vo.txt after script edits.

Single-beat sections get their narration replaced with the section text. Multi-beat
sections are validated: the beats' narrations, joined in order, must equal the section
text — if not, this exits non-zero and names the section (the author re-splits by hand,
because only a human/model knows where the visual cut belongs).

    python tools/scene_sync.py productions/<video>          # fix + validate
    python tools/scene_sync.py productions/<video> --check  # validate only, no writes
"""
import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prod")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    prod = Path(a.prod)

    text = (prod / "vo.txt").read_text(encoding="utf-8")
    sections = {m.group(1): norm(m.group(2)) for m in re.finditer(
        r"^## (\d+)[^\n]*\n(.+?)(?=\n## |\Z)", text, re.M | re.S)}

    plan_path = prod / "scene-plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    by_section = defaultdict(list)
    for beat in plan["beats"]:
        by_section[beat["section"]].append(beat)

    changed, failures = 0, []
    for sec, beats in by_section.items():
        if sec not in sections:
            failures.append(f"section {sec}: in scene-plan but not in vo.txt")
            continue
        if len(beats) == 1:
            if norm(beats[0]["narration"]) != sections[sec]:
                beats[0]["narration"] = sections[sec]
                changed += 1
        elif norm(" ".join(b["narration"] for b in beats)) != sections[sec]:
            failures.append(f"section {sec}: {len(beats)} beats no longer tile the section "
                            "text — re-split narrations by hand")
    for sec in sections:
        if sec not in by_section:
            failures.append(f"section {sec}: in vo.txt but has no beat")

    if changed and not a.check:
        plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
    print(f"scene_sync: {changed} beat(s) resynced, {len(failures)} failure(s)")
    for failure in failures:
        print(f"  - {failure}")
    return 1 if failures or (changed and a.check) else 0


if __name__ == "__main__":
    sys.exit(main())
