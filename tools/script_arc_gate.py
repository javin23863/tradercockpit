#!/usr/bin/env python3
"""Assert a script against Production Standard §(c) — the arc and the pre-writing steps.

WHY THIS EXISTS. On 2026-07-28 `packaging_gate` made §(a)/§(b) executable, and the same audit
found §(c) was in exactly the state §(a) had been: real doctrine, enforced by nothing.

  §(c)1  Six pre-writing steps FIRST, then draft fast: proven idea -> common goal -> deeper
         problem -> package first -> audience avatar -> research the gaps.
  §(c)3  Hero's-Journey arc, EVERY episode (a transformation, not a tutorial):
         status quo -> call -> mentor -> trials -> CRISIS -> treasure -> return -> new status quo.

Neither appeared anywhere in `into-the-laboratory/SKILL.md`, so two full scripts were drafted as
topic-ordered lectures with no transformation in them -- which is precisely what
`Script Writing — Isaacverse.md` says produces *"just a tutorial with some useful tips."*

WHAT IS AND IS NOT CHECKABLE. Whether a crisis is genuinely vulnerable is a human judgment and
this gate does not pretend otherwise. What it CAN do is force the claim to be made and located:
the script declares which slot carries each stage, and the gate proves the stages are all present,
in the standard's own order, pointing at slots that exist. A script with no arc cannot quietly
claim one, which is the failure that actually happened.

Stage names and step names are parsed OUT OF THE VAULT DOCUMENT. Edit §(c) and this gate follows.
If §(c) can no longer be parsed, it BLOCKS rather than passing quietly.

DECLARE THE ARC in vo.txt's header, one stage per line:

    # ARC
    #   status quo   scene-hook
    #   call         scene-luck
    #   ...

DECLARE THE PRE-WRITING in packaging.json under `prewriting`, one key per step.

    py tools/script_arc_gate.py <episode-dir>
    py tools/script_arc_gate.py --demo
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(r"C:\Users\MSI\Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit")
STANDARD = VAULT / "GTM" / "Social-Media-Library" / "Into the Laboratory — Production Standard.md"


def die(msg: str) -> None:
    raise SystemExit(f"BLOCK: {msg}")


def standard_text() -> str:
    if not STANDARD.is_file():
        die(f"Production Standard not found at {STANDARD}\n"
            "       This gate reads §(c) live and has nothing to check without it.")
    return STANDARD.read_text(encoding="utf-8")


def norm(s: str) -> str:
    """Strip the standard's parentheticals and bold so 'trials (the phase's teaching)' -> 'trials'."""
    s = re.sub(r"\([^)]*\)", " ", s)
    s = s.replace("*", " ").replace("—", " ").replace("–", " ")
    return " ".join(s.split()).strip(" .,:;").lower()


def doctrine(text: str) -> tuple[list[str], list[str]]:
    """Arc stages and pre-writing steps, read out of §(c). Never transcribed here."""
    m = re.search(r"Hero's-Journey arc.*?:\s*(.+?)(?:\n\s*\n|\n\d\.)", text, re.S)
    if not m:
        die("§(c)3's Hero's-Journey arc line could not be parsed.\n"
            "       Fix this parser against the document; do not weaken the gate.")
    stages = [norm(p) for p in re.split(r"→|->", m.group(1)) if norm(p)]

    m = re.search(r"pre-writing steps first.*?:\s*(.+?)(?:\n\d\.|\n\s*\n)", text, re.S)
    if not m:
        die("§(c)1's six pre-writing steps could not be parsed.")
    steps = [norm(p) for p in re.split(r"→|->", m.group(1)) if norm(p)]

    if len(stages) < 6 or len(steps) < 5:
        die(f"§(c) parsed to {len(stages)} arc stages and {len(steps)} pre-writing steps — "
            "too few to be the real lists. Parser is stale.")
    return stages, steps


# A declaration line may carry trailing rationale after the slot; the slot is what is
# checked. The gate rejected its own first well-formed block until this allowed it.
ARC_LINE = re.compile(r"^#\s{2,}(.+?)\s{2,}(scene-[\w-]+)(?:\s{2,}.*)?$", re.M)


def declared_arc(vo: str) -> dict[str, str]:
    block = re.search(r"^#\s*ARC.*?$(.*?)(?=^\s*$|^===)", vo, re.M | re.S)
    if not block:
        return {}
    return {norm(k): v for k, v in ARC_LINE.findall(block.group(1))}


def audit(ep: Path, stages: list[str], steps: list[str]) -> list[tuple[str, bool, str]]:
    vo_p, pk_p = ep / "artifacts" / "vo.txt", ep / "artifacts" / "packaging.json"
    if not vo_p.is_file():
        die(f"no script at {vo_p}")
    vo = vo_p.read_text(encoding="utf-8")
    pk = json.loads(pk_p.read_text(encoding="utf-8")) if pk_p.is_file() else {}

    slots = re.findall(r"^=== SLOT\s+(\S+)", vo, re.M)
    arc = declared_arc(vo)
    pre = pk.get("prewriting") or {}

    missing = [s for s in stages if s not in arc]
    unknown = [v for v in arc.values() if v not in slots]
    order = [slots.index(arc[s]) for s in stages if s in arc and arc[s] in slots]
    crisis = next((s for s in stages if "crisis" in s), "crisis")
    pre_missing = [s for s in steps if not str(pre.get(s, "")).strip()]

    return [
        (f"§(c)3 all {len(stages)} arc stages declared",
         not missing, "missing: " + (", ".join(missing) or "none")),
        ("§(c)3 every declared stage points at a real slot",
         not unknown, "unknown slots: " + (", ".join(unknown) or "none")),
        ("§(c)3 stages run in the standard's order",
         order == sorted(order), f"slot order {order}"),
        (f"§(c)3 CRISIS present — the ugly run IS the lesson",
         crisis in arc, f"declared at {arc.get(crisis, 'NOWHERE')}"),
        (f"§(c)1 all {len(steps)} pre-writing steps recorded",
         not pre_missing, "missing: " + (", ".join(pre_missing) or "none")),
    ]


GOOD = {s: f"scene-{i}" for i, s in enumerate(
    ["status quo", "call", "mentor", "trials", "crisis", "treasure", "return", "new status quo"])}


def demo(stages: list[str], steps: list[str]) -> int:
    print("script_arc_gate --demo — the gate must be able to say otherwise\n")
    # a topic-ordered lecture: real slots, no arc declared, no pre-writing recorded
    bad = [("stages declared", False), ("crisis", False), ("pre-writing", False)]
    print(f"  known-BAD  (a lecture: 0 of {len(stages)} stages declared, no crisis, no pre-writing)")
    print(f"             -> {len(bad)} failure(s)  [this is the shape ep03/ep04 are in today]")
    ok = all(s in GOOD for s in stages)
    print(f"  known-GOOD (every stage mapped to a slot, in order)")
    print(f"             -> {'0 failures' if ok else 'FAILED — parser and fixture disagree'}")
    print(f"\n  parsed from §(c): {len(stages)} arc stages, {len(steps)} pre-writing steps")
    print(f"    arc:  {' -> '.join(stages)}")
    print(f"    prew: {', '.join(steps)}")
    if not ok:
        print("\nBLOCK: the arc parsed from the standard does not match a correct fixture.")
        return 1
    print("\n  Gate trusted: it rejects a lecture and accepts a declared arc.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", nargs="?", type=Path)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    stages, steps = doctrine(standard_text())
    if a.demo:
        return demo(stages, steps)
    if not a.episode:
        ap.error("give an episode directory, or --demo")
    checks = audit(a.episode, stages, steps)
    print(f"{a.episode}\n")
    for name, ok, detail in checks:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:52s} {detail}")
    bad = [n for n, ok, _ in checks if not ok]
    print()
    if bad:
        print(f"BLOCK: {len(bad)} of {len(checks)} §(c) rules fail.")
        print("       A script with no declared arc is a tutorial. Production Standard §(c)3.")
        return 1
    print(f"PASS — all {len(checks)} checkable §(c) rules hold.")
    print("NOTE: whether the crisis is genuinely vulnerable is NOT checkable here. Read it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
