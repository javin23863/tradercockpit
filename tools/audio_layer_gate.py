#!/usr/bin/env python3
"""Fail-closed gate on the delivered sound layer.

Why this exists: produce.py degrades silently. `pick_music()` returns None on an
empty music_library/ (one log line), and missing SFX files are skipped with no log
at all, so build_sound_filter() returns None and the master ships as bare narration
with every other gate green. That is exactly how the series-01 master shipped silent
(Series 01 - Master Review 2026-07-25, Finding 3).

The rules this enforces are already rulings, not new policy:
  - Video Editing Craft: "A narration-only master with no SFX and no music bed is an
    unfinished edit by this playbook, whatever its loudness measurements say."
  - Content Machine Team Brief: "Any reduction from an approved brief - audio layer,
    runtime, density - is an operator decision, not a pipeline one."

So a drop is not forbidden; an UNDECLARED drop is. Record the operator's call in
build/audio-layer-override.json to pass with a reduced layer:

    {"music": "approved absent for this cut", "sfx": "no section SFX this cut"}

Usage:
    python tools/audio_layer_gate.py productions/<vid>
    python tools/audio_layer_gate.py --selftest
"""
import json
import sys
from pathlib import Path

RECEIPT = "audio-layer-receipt.json"
OVERRIDE = "audio-layer-override.json"
VERDICT = "audio-layer-gate.json"


def evaluate(receipt: dict, override: dict | None = None) -> tuple[str, list[str]]:
    """Return (PASS|BLOCK, failures). Absent receipt is a BLOCK, never a pass."""
    override = override or {}
    failures = []

    if not receipt:
        return "BLOCK", [f"{RECEIPT} missing - produce.py did not record a sound layer"]

    if not receipt.get("music") and not override.get("music"):
        failures.append(
            "music bed absent (music_library/ empty or unreadable) and no operator override")

    # SFX only apply when the cut actually has section transitions to land them on.
    if receipt.get("sectionBoundaries", 0) > 0 and not override.get("sfx"):
        if not receipt.get("sfxDirPresent"):
            failures.append(
                f"SFX dir absent ({receipt.get('sfxDir')}) - whoosh/impact silently skipped")
        else:
            for name in ("whoosh", "impact"):
                if not receipt.get(name):
                    failures.append(f"{name} SFX not layered and no operator override")

    if not receipt.get("layered") and not (override.get("music") and override.get("sfx")):
        failures.append("master carries bare narration - no layer reached the mix")

    return ("BLOCK" if failures else "PASS"), failures


def _read(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def selftest() -> None:
    full = {"music": "bed.mp3", "whoosh": True, "impact": True, "sfxDirPresent": True,
            "sectionBoundaries": 5, "layered": True}
    assert evaluate(full)[0] == "PASS"

    # the series-01 failure: everything else green, nothing in the mix
    silent = {"music": None, "whoosh": False, "impact": False, "sfxDirPresent": False,
              "sectionBoundaries": 5, "layered": False}
    verdict, fails = evaluate(silent)
    assert verdict == "BLOCK" and len(fails) == 3, fails

    # a declared reduction is allowed to ship
    assert evaluate(silent, {"music": "none this cut", "sfx": "none this cut"})[0] == "PASS"

    # missing receipt must never read as approval
    assert evaluate({})[0] == "BLOCK"
    assert evaluate(None)[0] == "BLOCK"

    # a cut with no section transitions owes no SFX, but still owes a bed
    no_sections = {"music": "bed.mp3", "whoosh": False, "impact": False,
                   "sfxDirPresent": False, "sectionBoundaries": 0, "layered": True}
    assert evaluate(no_sections)[0] == "PASS"

    print("audio_layer_gate self-test: OK")


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        selftest()
        return 0
    if not argv:
        print(__doc__)
        return 2

    build = Path(argv[0]) / "build"
    verdict, failures = evaluate(_read(build / RECEIPT), _read(build / OVERRIDE))
    build.mkdir(parents=True, exist_ok=True)
    (build / VERDICT).write_text(
        json.dumps({"verdict": verdict, "failures": failures}, indent=2), encoding="utf-8")
    for line in failures:
        print(f"[audio-layer] {line}")
    print(f"[audio-layer] {verdict}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
