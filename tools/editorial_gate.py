#!/usr/bin/env python3
"""Fail closed unless every narration beat names its exact visual."""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


SCHEMA = "tradercockpit-scene-plan/v1"
DEFAULT_GAP_S = 0.45
GODSEYE_USES = {"geography", "observed-layer", "attributable-replay"}
GENERIC_PURPOSES = {"b-roll", "generic b-roll", "atmosphere", "establishing shot"}
CAPTURE_RECEIPT_SCHEMA = "tradercockpit-chart-capture-receipts/v1"
# Conservative audit cutover: older files cannot be back-filled; captures from this local date must receipt.
CAPTURE_RECEIPT_REQUIRED_AT = datetime.fromisoformat("2026-07-20T00:00:00+07:00")


def _norm(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _capture_time(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed


def check_chart_ordering(production, plan=None):
    """Prove receipted chart captures predate vo.txt; isolate unprovable history as WARN."""
    root = Path(production).resolve()
    blocked, warnings = [], []
    if plan is None:
        plan_path = root / "scene-plan.json"
        if not plan_path.is_file():
            warnings.append({
                "type": "chart_ordering",
                "detail": "no scene plan; no chart references can be checked, ordering unprovable",
            })
            return {"status": "WARN", "charts": 0, "blocked": blocked, "warnings": warnings}
        try:
            plan = json.loads(plan_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            blocked.append({"type": "chart_ordering", "detail": f"scene plan is unreadable: {error}"})
            return {"status": "BLOCK", "charts": 0, "blocked": blocked, "warnings": warnings}

    charts = sorted({
        _norm((beat.get("visual") or {}).get("path")).replace("\\", "/")
        for beat in plan.get("beats", []) if isinstance(beat, dict)
        and ("chart" in _norm((beat.get("visual") or {}).get("kind")).lower()
             or "tradingview" in _norm((beat.get("visual") or {}).get("kind")).lower())
        and _norm((beat.get("visual") or {}).get("path"))
    })
    vo_path = root / "vo.txt"
    if not vo_path.is_file():
        blocked.append({"type": "chart_ordering", "detail": "vo.txt is missing; ordering cannot be checked"})
        return {"status": "BLOCK", "charts": len(charts), "blocked": blocked, "warnings": warnings}
    vo_mtime = datetime.fromtimestamp(vo_path.stat().st_mtime, timezone.utc)

    receipt_path = root / "chart-capture-receipts.json"
    captures = {}
    if receipt_path.is_file():
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            if receipt.get("schema") != CAPTURE_RECEIPT_SCHEMA or not isinstance(receipt.get("captures"), list):
                raise ValueError(f"schema must be {CAPTURE_RECEIPT_SCHEMA} with a captures array")
            for entry in receipt["captures"]:
                if not isinstance(entry, dict) or not all(entry.get(field) for field in ("path", "capturedAt", "sha256")):
                    raise ValueError("each capture must contain path, capturedAt, and sha256")
                path = str(entry["path"]).replace("\\", "/")
                if path in captures:
                    raise ValueError(f"duplicate capture path: {path}")
                captures[path] = entry
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            blocked.append({"type": "chart_ordering", "detail": f"invalid capture receipt: {error}"})
            return {"status": "BLOCK", "charts": len(charts), "blocked": blocked, "warnings": warnings}

    for relative in charts:
        artifact = (root / relative).resolve()
        try:
            artifact.relative_to(root)
        except ValueError:
            blocked.append({"type": "chart_ordering", "path": relative, "detail": f"{relative}: chart path leaves production"})
            continue
        if not artifact.is_file():
            blocked.append({"type": "chart_ordering", "path": relative, "detail": f"{relative}: chart artifact is missing"})
            continue
        entry = captures.get(relative)
        if entry is None:
            detail = f"{relative}: no receipt, ordering unprovable"
            target = blocked if artifact.stat().st_mtime >= CAPTURE_RECEIPT_REQUIRED_AT.timestamp() else warnings
            if target is blocked:
                detail += " (new capture on or after 2026-07-20 Asia/Bangkok)"
            else:
                detail += " (historical asset predates receipt enforcement)"
            target.append({"type": "chart_ordering", "path": relative, "detail": detail})
            continue
        try:
            captured_at = _capture_time(entry["capturedAt"])
        except (TypeError, ValueError) as error:
            blocked.append({"type": "chart_ordering", "path": relative, "detail": f"{relative}: invalid capturedAt: {error}"})
            continue
        digest = str(entry["sha256"]).lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            blocked.append({"type": "chart_ordering", "path": relative, "detail": f"{relative}: invalid artifact sha256"})
            continue
        with artifact.open("rb") as handle:
            actual = hashlib.file_digest(handle, "sha256").hexdigest()
        if actual != digest:
            blocked.append({"type": "chart_ordering", "path": relative, "detail": f"{relative}: artifact hash does not match capture receipt"})
        if captured_at >= vo_mtime:
            blocked.append({
                "type": "chart_ordering", "path": relative,
                "detail": f"{relative}: capturedAt {entry['capturedAt']} does not precede vo.txt mtime {vo_mtime.isoformat()}",
            })

    status = "BLOCK" if blocked else "WARN" if warnings else "PASS"
    return {"status": status, "charts": len(charts), "blocked": blocked, "warnings": warnings}


def validate_scene_plan(plan, sections, production=None, require_files=True, warnings=None):
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
    if root and require_files:
        ordering = check_chart_ordering(root, plan)
        errors.extend(item["detail"] for item in ordering["blocked"])
        if warnings is not None:
            warnings.extend(ordering["warnings"])
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
    warnings = []
    errors = validate_scene_plan(plan, sections, production=production, require_files=True, warnings=warnings)
    if errors:
        raise ValueError("\n".join(errors))
    timeline = compile_timeline(plan, sections, gap_s=gap_s)
    build = production / "build"
    (build / "timeline.json").write_text(json.dumps(timeline, indent=2), encoding="utf-8")
    receipt = {
        "status": "WARN" if warnings else "PASS",
        "schema": SCHEMA,
        "beats": len(timeline),
        "checks": [
            "exact narration coverage",
            "declared spoken/visible subject overlap",
            "contain-only news policy",
            "purpose-gated Godseye policy",
            "receipted chart captures precede vo.txt",
        ],
        "warnings": warnings,
        "doesNotProve": [
            "the visual declaration matches the pixels",
            "full-size text legibility",
            "editorial quality",
        ],
    }
    (build / "editorial-gate.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return timeline


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        production = Path(tmp)
        visual = production / "visuals" / "chart.mp4"
        visual.parent.mkdir()
        visual.write_bytes(b"chart")
        vo = production / "vo.txt"
        vo.write_text("script", encoding="utf-8")
        plan = {"beats": [{"visual": {"path": "visuals/chart.mp4", "kind": "tradingview"}}]}
        cutover = CAPTURE_RECEIPT_REQUIRED_AT.timestamp()
        os.utime(visual, (cutover - 10, cutover - 10))
        os.utime(vo, (cutover + 20, cutover + 20))
        historical = check_chart_ordering(production, plan)
        assert historical["status"] == "WARN" and "no receipt, ordering unprovable" in historical["warnings"][0]["detail"]

        os.utime(visual, (cutover + 10, cutover + 10))
        assert check_chart_ordering(production, plan)["status"] == "BLOCK"
        receipt = {
            "schema": CAPTURE_RECEIPT_SCHEMA,
            "captures": [{
                "path": "visuals/chart.mp4",
                "capturedAt": datetime.fromtimestamp(cutover + 10, timezone.utc).isoformat(),
                "sha256": hashlib.sha256(b"chart").hexdigest(),
            }],
        }
        (production / "chart-capture-receipts.json").write_text(json.dumps(receipt), encoding="utf-8")
        assert check_chart_ordering(production, plan)["status"] == "PASS"
        receipt["captures"][0]["capturedAt"] = datetime.fromtimestamp(cutover + 30, timezone.utc).isoformat()
        (production / "chart-capture-receipts.json").write_text(json.dumps(receipt), encoding="utf-8")
        assert check_chart_ordering(production, plan)["status"] == "BLOCK"
    print("EDITORIAL ORDERING SELFTEST PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("production", nargs="?")
    parser.add_argument("--ordering-only", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        selftest()
        return 0
    if not args.production:
        parser.error("production is required")
    if args.ordering_only:
        report = check_chart_ordering(args.production)
        print(f"EDITORIAL ORDERING {report['status']} — {report['charts']} chart artifact(s)")
        for item in [*report["warnings"], *report["blocked"]]:
            print(f"  - {item['detail']}")
        return 1 if report["blocked"] else 0
    try:
        timeline = load_timeline(args.production)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"EDITORIAL GATE BLOCK\n{exc}", file=sys.stderr)
        return 1
    receipt = json.loads((Path(args.production) / "build" / "editorial-gate.json").read_text(encoding="utf-8"))
    print(f"EDITORIAL GATE {receipt['status']} — {len(timeline)} explicit beats")
    for warning in receipt.get("warnings", []):
        print(f"  - {warning['detail']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
