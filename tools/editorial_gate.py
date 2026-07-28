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

import yaml


SCHEMA = "tradercockpit-scene-plan/v1"
# Predicates a viewer can see as a horizontal line. Mirrors the price entries of
# claims_gate.FEED_PREDICATES, kept local so this gate carries no import-order dependency.
LEVEL_PREDICATES = {"prior_open", "prior_high", "prior_low", "prior_close",
                    "session_open", "session_high", "session_low", "session_close"}
# Proper names only. "technology" is deliberately absent: it is a sector concept, not a
# ticker, and aliasing it to XLK fires on nearly every section.
INSTRUMENT_ALIASES = {
    "SP:SPX": ["s&p 500", "s&p", "spx"],
    "NASDAQ:IXIC": ["nasdaq composite", "nasdaq"],
    "NASDAQ:NVDA": ["nvidia", "nvda"],
    "AMEX:XLK": ["xlk"],
    "CBOE:VIX": ["vix", "volatility index"],
    "TVC:UKOIL": ["brent"],
    "TVC:US10Y": ["10-year", "ten-year", "10 year"],
    "TVC:GOLD": ["gold"],
    "TVC:DXY": ["dollar index", "dxy"],
}
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


def _price(value):
    try:
        return round(float(str(value).replace(",", "")), 4)
    except (TypeError, ValueError):
        return None


def load_chart_plans(root):
    """Every chart-plan*.json, merged by `out`. A day's charts are split across files
    (chart-plan-cash.json, chart-plan-vix.json); reading only chart-plan.json silently
    skipped the VIX chart from both level binding and the spoken/visible check."""
    charts, errors = {}, []
    for path in sorted(Path(root).glob("chart-plan*.json")):
        for chart in json.loads(path.read_text(encoding="utf-8")):
            out, symbol = _norm(chart.get("out")), _norm(chart.get("symbol"))
            if out in charts and charts[out].get("symbol") != symbol:
                errors.append(f"{out}: chart plans disagree on symbol "
                              f"({charts[out].get('symbol')} vs {symbol})")
            charts[out] = chart
    return charts, errors


def beat_chart_sections(scene):
    """{chart `out`: sections whose beats show it}. The stem of visuals/03-spx.mp4 is the
    chart's `out`, which is how a beat binds to the plan that drew it."""
    owners = {}
    for beat in scene.get("beats", []):
        stem = Path(_norm((beat.get("visual") or {}).get("path"))).stem
        if stem:
            owners.setdefault(stem, set()).add(str(beat.get("section")))
    return owners


def check_level_binding(production):
    """Every level drawn is spoken, and every level spoken is drawn.

    Only horizontal lines count as levels: a trendline's anchors are swing pivots, not
    figures the script quotes. This is the gate for "you don't speak in levels" -- on
    daily-2026-07-27 each chart drew the prior close and the session low while the script
    spoke five levels of that same instrument, so three were named and never shown."""
    root = Path(production)
    blocked = []
    charts, plan_errors = load_chart_plans(root)
    blocked.extend({"type": "level_binding", "detail": detail} for detail in plan_errors)
    if not charts:
        return {"status": "BLOCK" if blocked else "PASS", "charts": 0, "blocked": blocked}
    missing = [name for name in ("scene-plan.json", "claims.yaml", "vo-receipts.yaml")
               if not (root / name).is_file()]
    if missing:
        blocked.append({"type": "level_binding",
                        "detail": f"chart plans are present but {missing} missing; levels unprovable"})
        return {"status": "BLOCK", "charts": len(charts), "blocked": blocked}
    scene = json.loads((root / "scene-plan.json").read_text(encoding="utf-8"))
    claims = {c["id"]: c for c in (yaml.safe_load((root / "claims.yaml").read_text(encoding="utf-8")) or [])}
    receipts = yaml.safe_load((root / "vo-receipts.yaml").read_text(encoding="utf-8")) or {}
    owners = beat_chart_sections(scene)

    for out, chart in sorted(charts.items()):
        symbol = _norm(chart.get("symbol"))
        sections = owners.get(out, set())
        if not sections:
            continue  # captured but never cut in: nothing is asserted on screen
        drawn = {}
        for stage in chart.get("stages", []):
            for shape in stage.get("draw", []):
                if "horizontal" not in _norm(shape.get("type")).lower():
                    continue
                price = _price(shape.get("price"))
                if price is not None:
                    drawn[price] = _norm(shape.get("type"))
        spoken = {}
        for section in sections:
            for receipt in receipts.get(section, []):
                claim = claims.get(receipt.get("claim")) or {}
                if not symbol or symbol not in str(claim.get("source", "")):
                    continue
                if claim.get("predicate") not in LEVEL_PREDICATES:
                    continue
                price = _price(claim.get("value"))
                if price is not None:
                    spoken[price] = f"{claim['id']} ({claim['predicate']})"
        for price, kind in sorted(drawn.items()):
            if price not in spoken:
                blocked.append({"type": "level_binding", "path": out,
                                "detail": f"{out}: {kind} drawn at {price} is spoken in none of "
                                          f"sections {sorted(sections)}"})
        for price, who in sorted(spoken.items()):
            if price not in drawn:
                blocked.append({"type": "level_binding", "path": out,
                                "detail": f"{out}: {who} is spoken at {price} but not drawn on "
                                          f"the {symbol} chart"})
    return {"status": "BLOCK" if blocked else "PASS", "charts": len(charts), "blocked": blocked}


def check_spoken_visible(production):
    """Derive what a beat SPEAKS from its receipts, not from what it declares.

    `spokenSubjects` is written by the same pass that writes the narration, so a beat can
    declare ["nvda"], name the S&P, the Nasdaq and XLK, and still satisfy the declared
    overlap check -- daily-2026-07-27 beat 01-03 did exactly that.

    Primary substrate is receipts: a beat's narration tiles the section text verbatim, and
    every receipt quote is a verbatim substring, so any quoted number resolves claim ->
    instrument regardless of paraphrase or anaphora. The lexicon only supplements number-free
    proper names ("XLK followed it down"). Sector words like "technology" are deliberately
    NOT aliased -- they fire on nearly every section.

    An instrument may be spoken over another instrument's chart when the section shows its
    chart in a neighbouring beat: that is the operator's un-splittable pair clause ("an S&P
    close below X and a VIX close above Y"). News beats are exempt, or attributed sourcing
    ("Micron slumped 2.3%") would demand a chart for every company a wire story names."""
    root = Path(production)
    blocked = []
    charts, plan_errors = load_chart_plans(root)
    blocked.extend({"type": "spoken_visible", "detail": detail} for detail in plan_errors)
    if not (root / "scene-plan.json").is_file():
        return {"status": "BLOCK" if blocked else "PASS", "beats": 0, "blocked": blocked}
    scene = json.loads((root / "scene-plan.json").read_text(encoding="utf-8"))
    claims, receipts = {}, {}
    if (root / "claims.yaml").is_file() and (root / "vo-receipts.yaml").is_file():
        claims = {c["id"]: c for c in (yaml.safe_load((root / "claims.yaml").read_text(encoding="utf-8")) or [])}
        receipts = yaml.safe_load((root / "vo-receipts.yaml").read_text(encoding="utf-8")) or {}
    elif charts:
        blocked.append({"type": "spoken_visible",
                        "detail": "chart plans present but claims.yaml/vo-receipts.yaml missing; "
                                  "spoken instruments cannot be derived"})
        return {"status": "BLOCK", "beats": 0, "blocked": blocked}

    symbol_of = {out: _norm(chart.get("symbol")) for out, chart in charts.items()}
    section_symbols = {}
    for out, sections in beat_chart_sections(scene).items():
        for section in sections:
            if symbol_of.get(out):
                section_symbols.setdefault(section, set()).add(symbol_of[out])

    beats = scene.get("beats", [])
    for beat in beats:
        visual = beat.get("visual") or {}
        if "news" in _norm(visual.get("kind")).lower():
            continue
        section = str(beat.get("section"))
        narration = _norm(beat.get("narration"))
        spoken = set()
        for receipt in receipts.get(section, []):
            quote = _norm(receipt.get("quote"))
            if quote and quote in narration:
                source = str((claims.get(receipt.get("claim")) or {}).get("source", ""))
                if "ohlcv-feed-receipts" in source and "#" in source:
                    spoken.add(source.split("#", 1)[1])
        lowered = narration.lower()
        for symbol, names in INSTRUMENT_ALIASES.items():
            if any(re.search(rf"(?<![\w&]){re.escape(name)}(?![\w&])", lowered) for name in names):
                spoken.add(symbol)
        shown = symbol_of.get(Path(_norm(visual.get("path"))).stem)
        allowed = ({shown} if shown else set()) | section_symbols.get(section, set())
        for symbol in sorted(spoken - allowed):
            blocked.append({
                "type": "spoken_visible", "path": _norm(visual.get("path")),
                "detail": f"beat {_norm(beat.get('id'))}: speaks {symbol} while showing "
                          f"{shown or _norm(visual.get('path'))}, and section {section} never charts it",
            })
    return {"status": "BLOCK" if blocked else "PASS", "beats": len(beats), "blocked": blocked}


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
        errors.extend(item["detail"] for item in check_level_binding(root)["blocked"])
        errors.extend(item["detail"] for item in check_spoken_visible(root)["blocked"])
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
            "every level drawn is spoken and every level spoken is drawn",
            "receipt-derived spoken instruments are charted in their own section",
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

        # level binding, both poles
        def write_levels(drawn, spoken_predicates):
            (production / "chart-plan.json").write_text(json.dumps([{
                "out": "03-spx", "symbol": "SP:SPX",
                "stages": [{"draw": [{"type": "horizontal_line", "price": p} for p in drawn]}],
            }]), encoding="utf-8")
            (production / "scene-plan.json").write_text(json.dumps({"beats": [
                {"section": "03", "visual": {"path": "visuals/03-spx.mp4"}}]}), encoding="utf-8")
            (production / "claims.yaml").write_text(yaml.safe_dump([
                {"id": p, "value": v, "predicate": p, "source": "ohlcv-feed-receipts-x.json#SP:SPX"}
                for p, v in spoken_predicates]), encoding="utf-8")
            (production / "vo-receipts.yaml").write_text(yaml.safe_dump(
                {"03": [{"quote": "q", "claim": p} for p, _ in spoken_predicates]}), encoding="utf-8")

        write_levels([7411.98, 7382.74], [("prior_close", 7411.98), ("session_low", 7382.74)])
        assert check_level_binding(production)["status"] == "PASS"
        # the 07-27 shape: two levels drawn, five spoken -> three named and never shown
        write_levels([7411.98, 7382.74], [("prior_close", 7411.98), ("session_low", 7382.74),
                                          ("session_open", 7464.2), ("session_high", 7480.57),
                                          ("session_close", 7413.18)])
        report = check_level_binding(production)
        assert report["status"] == "BLOCK" and len(report["blocked"]) == 3, report
        # a line drawn at a price the script never says
        write_levels([9999.0], [("prior_close", 9999.0), ("session_low", 1.0)])
        assert check_level_binding(production)["status"] == "BLOCK"
        # non-level predicates are not levels: a return is spoken but must not demand a line
        write_levels([7411.98], [("prior_close", 7411.98), ("session_return", -4.99)])
        assert check_level_binding(production)["status"] == "PASS"

        # spoken/visible, both poles. Two charts exist; what changes is which beats show them.
        (production / "chart-plan.json").write_text(json.dumps([
            {"out": "03-spx", "symbol": "SP:SPX", "stages": []},
            {"out": "07-vix", "symbol": "CBOE:VIX", "stages": []},
        ]), encoding="utf-8")
        (production / "claims.yaml").write_text(yaml.safe_dump([
            {"id": "vix-close", "value": 18.67, "predicate": "session_close",
             "source": "ohlcv-feed-receipts-x.json#CBOE:VIX"}]), encoding="utf-8")
        (production / "vo-receipts.yaml").write_text(yaml.safe_dump(
            {"09": [{"quote": "a close above 18.67", "claim": "vix-close"}]}), encoding="utf-8")

        def write_scene(beats):
            (production / "scene-plan.json").write_text(json.dumps({"beats": beats}), encoding="utf-8")

        # a number quoted from a VIX receipt, spoken over the S&P chart, VIX never charted
        write_scene([{"id": "09-01", "section": "09", "narration": "We want a close above 18.67 next.",
                      "visual": {"path": "visuals/03-spx.mp4", "kind": "tradingview"}}])
        assert check_spoken_visible(production)["status"] == "BLOCK"
        # same clause, but the section shows the VIX chart in a neighbouring beat: the
        # operator's un-splittable pair clause
        write_scene([{"id": "09-01", "section": "09", "narration": "We want a close above 18.67 next.",
                      "visual": {"path": "visuals/03-spx.mp4", "kind": "tradingview"}},
                     {"id": "09-02", "section": "09", "narration": "Here is the volatility side.",
                      "visual": {"path": "visuals/07-vix.mp4", "kind": "tradingview"}}])
        assert check_spoken_visible(production)["status"] == "PASS"
        # lexicon catches a number-free proper name that no receipt covers
        write_scene([{"id": "09-01", "section": "09", "narration": "Nvidia stayed heavy all session.",
                      "visual": {"path": "visuals/03-spx.mp4", "kind": "tradingview"}}])
        assert check_spoken_visible(production)["status"] == "BLOCK"
        # news beats are exempt: a wire story may name companies it does not chart
        write_scene([{"id": "09-01", "section": "09", "narration": "Nvidia stayed heavy all session.",
                      "visual": {"path": "visuals/01-ap.mp4", "kind": "news"}}])
        assert check_spoken_visible(production)["status"] == "PASS"
    print("EDITORIAL ORDERING SELFTEST PASS")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("production", nargs="?")
    parser.add_argument("--ordering-only", action="store_true")
    parser.add_argument("--levels-only", action="store_true")
    parser.add_argument("--spoken-only", action="store_true")
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
    if args.levels_only:
        report = check_level_binding(args.production)
        print(f"LEVEL BINDING {report['status']} — {report['charts']} planned chart(s)")
        for item in report["blocked"]:
            print(f"  - {item['detail']}")
        return 1 if report["blocked"] else 0
    if args.spoken_only:
        report = check_spoken_visible(args.production)
        print(f"SPOKEN/VISIBLE {report['status']} — {report['beats']} beat(s)")
        for item in report["blocked"]:
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
