#!/usr/bin/env python3
"""Fail closed unless every narration beat names its exact visual."""
import argparse
import json
import re
import sys
from pathlib import Path


SCHEMA = "tradercockpit-scene-plan/v1"
DEFAULT_GAP_S = 0.45
GODSEYE_USES = {"geography", "observed-layer", "attributable-replay"}
GENERIC_PURPOSES = {"b-roll", "generic b-roll", "atmosphere", "establishing shot"}


def _norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def validate_scene_plan(plan, sections, production=None, require_files=True):
    errors = []
    if plan.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    beats = plan.get("beats")
    if not isinstance(beats, list) or not beats:
        return errors + ["beats must be a non-empty list"]

    section_map = {str(section["num"]): section for section in sections}
    grouped = {num: [] for num in section_map}
    seen_ids = set()
    root = Path(production) if production else None

    for index, beat in enumerate(beats):
        label = f"beats[{index}]"
        beat_id = _norm(beat.get("id"))
        section = str(beat.get("section", ""))
        narration = _norm(beat.get("narration"))
        visual = beat.get("visual") or {}
        if not re.fullmatch(r"[A-Za-z0-9_-]+", beat_id):
            errors.append(f"{label}: id must use letters, numbers, underscore, or hyphen")
        elif beat_id in seen_ids:
            errors.append(f"{label}: duplicate id {beat_id}")
        seen_ids.add(beat_id)
        if section not in section_map:
            errors.append(f"{label}: unknown section {section}")
        else:
            grouped[section].append(beat)
        if not narration:
            errors.append(f"{label}: narration is required")

        spoken = {_norm(value).lower() for value in beat.get("spokenSubjects", []) if _norm(value)}
        visible = {_norm(value).lower() for value in visual.get("visibleSubjects", []) if _norm(value)}
        if not spoken or not visible or not spoken.intersection(visible):
            errors.append(f"{label}: spokenSubjects and visual.visibleSubjects have no subject overlap")

        path = _norm(visual.get("path"))
        kind = _norm(visual.get("kind")).lower()
        fit = _norm(visual.get("fit")).lower()
        purpose = _norm(visual.get("purpose"))
        if not path:
            errors.append(f"{label}: visual.path is required")
        elif require_files and root and not (root / path).is_file():
            errors.append(f"{label}: visual does not exist: {path}")
        if fit not in {"contain", "cover"}:
            errors.append(f"{label}: visual.fit must be contain or cover")
        if not purpose:
            errors.append(f"{label}: visual.purpose is required")
        if kind == "news" and fit != "contain":
            errors.append(f"{label}: news visual must use fit=contain; source cards may not be cropped")
        if kind == "godseye":
            evidence_use = _norm(visual.get("evidenceUse")).lower()
            if purpose.lower() in GENERIC_PURPOSES or evidence_use not in GODSEYE_USES:
                errors.append(
                    f"{label}: Godseye needs a specific explanatory purpose and evidenceUse in "
                    f"{sorted(GODSEYE_USES)}"
                )
            if evidence_use in {"observed-layer", "attributable-replay"} and not visual.get("evidencePacket"):
                errors.append(f"{label}: Godseye {evidence_use} requires an evidencePacket")

    for num, section in section_map.items():
        planned = _norm(" ".join(_norm(beat.get("narration")) for beat in grouped[num]))
        scripted = _norm(section.get("text"))
        if planned != scripted:
            errors.append(f"section {num}: beat narration must cover the script exactly and in order")
    return errors


def compile_timeline(plan, sections, gap_s=0.0):
    errors = validate_scene_plan(plan, sections, require_files=False)
    if errors:
        raise ValueError("\n".join(errors))
    grouped = {}
    for beat in plan["beats"]:
        grouped.setdefault(str(beat["section"]), []).append(beat)

    timeline = []
    start = 0.0
    for section_index, section in enumerate(sections):
        beats = grouped[str(section["num"])]
        weights = [max(len(_norm(beat["narration"])), 1) for beat in beats]
        section_duration = float(section["duration"])
        if section_index < len(sections) - 1:
            section_duration += gap_s
        used = 0.0
        for beat_index, (beat, weight) in enumerate(zip(beats, weights)):
            duration = (section_duration - used if beat_index == len(beats) - 1
                        else round(section_duration * weight / sum(weights), 3))
            compiled = dict(beat)
            compiled.update({"start": round(start, 3), "duration": round(duration, 3)})
            timeline.append(compiled)
            start += duration
            used += duration
    return timeline


def load_timeline(production, gap_s=DEFAULT_GAP_S):
    production = Path(production)
    plan_path = production / "scene-plan.json"
    sections_path = production / "build" / "sections.json"
    if not plan_path.is_file():
        raise ValueError(f"missing {plan_path}; section-order auto-cutting is disabled")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    sections = json.loads(sections_path.read_text(encoding="utf-8"))
    errors = validate_scene_plan(plan, sections, production=production, require_files=True)
    if errors:
        raise ValueError("\n".join(errors))
    timeline = compile_timeline(plan, sections, gap_s=gap_s)
    build = production / "build"
    (build / "timeline.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    receipt = {
        "status": "PASS",
        "schema": SCHEMA,
        "beats": len(timeline),
        "checks": [
            "exact narration coverage",
            "declared spoken/visible subject overlap",
            "contain-only news policy",
            "purpose-gated Godseye policy",
        ],
        "doesNotProve": [
            "the visual declaration matches the pixels",
            "full-size text legibility",
            "editorial quality",
        ],
    }
    (build / "editorial-gate.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return timeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("production")
    args = parser.parse_args()
    try:
        timeline = load_timeline(args.production)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"EDITORIAL GATE BLOCK\n{exc}", file=sys.stderr)
        return 1
    print(f"EDITORIAL GATE PASS — {len(timeline)} explicit beats")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
