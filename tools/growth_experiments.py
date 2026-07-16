#!/usr/bin/env python
"""Validate and summarize TraderCockpit's file-backed growth experiments."""

import argparse
import csv
import json
import math
import statistics
from datetime import datetime
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "social-ops" / "growth-experiments.v1.json"
METRICS = ROOT / "social-ops" / "metrics.csv"

LIBRARIES = {
    "audiences": ("audience", "audience/"),
    "angles": ("angle", "angle/"),
    "hooks": ("hook", "hook/"),
    "formats": ("format", "format/"),
    "offers": ("offer", "offer/"),
}
LIBRARY_STATES = {"active", "hypothesis", "blocked"}
LANES = {"new", "reuse"}
EXPERIMENT_STATES = {"proposed", "running", "measured", "decided", "blocked"}
SURFACES = {"youtube", "instagram", "facebook", "tiktok", "email", "landing"}
DECISIONS = {"pending", "kill", "iterate", "reuse"}
GUARDRAILS = {"claims_gate_pass", "corrections_zero"}
DIRECT_METRICS = {
    "three_second_hold_percent",
    "completion_percent",
    "average_percentage_viewed",
    "ctr_percent",
    "qualified_comments",
}
DERIVED_METRICS = {
    "shares_per_1000_views": ("shares", "views", 1000),
    "saves_per_1000_views": ("saves", "views", 1000),
    "cta_click_rate_percent": ("cta_clicks", "landing_visits", 100),
    "confirmed_signup_rate_percent": ("confirmed_signups", "landing_visits", 100),
}
SUPPORTED_METRICS = DIRECT_METRICS | set(DERIVED_METRICS)
REQUIRED_METRIC_COLUMNS = {
    "batch_id", "item_id", "channel", "claims_gate", "corrections", "views", "shares",
    "saves", "landing_visits", "cta_clicks", "confirmed_signups", *DIRECT_METRICS,
}


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _timezone(value, field):
    text = _text(value, field)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from error
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return text


def _inside(root, value, field, must_exist=True):
    text = _text(value, field)
    relative = Path(text)
    if PurePosixPath(text).is_absolute() or PureWindowsPath(text).is_absolute():
        raise ValueError(f"{field} must be repo-relative")
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{field} must stay inside TraderCockpit") from error
    if must_exist and not path.is_file():
        raise ValueError(f"{field} does not exist")
    return path


def _read_json(path, field):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as error:
        raise ValueError(f"{field} is not readable") from error
    except json.JSONDecodeError as error:
        raise ValueError(f"{field} is not valid JSON") from error


def _number(row, field, tag):
    value = row.get(field)
    if value is None or not str(value).strip():
        return None
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{tag}.{field} must be numeric or blank") from error
    if not math.isfinite(number):
        raise ValueError(f"{tag}.{field} must be finite")
    if number < 0:
        raise ValueError(f"{tag}.{field} must not be negative")
    return number


def _metric_value(row, metric, tag):
    if row is None:
        return None
    if metric in DIRECT_METRICS:
        return _number(row, metric, tag)
    numerator, denominator, scale = DERIVED_METRICS[metric]
    top, bottom = _number(row, numerator, tag), _number(row, denominator, tag)
    return None if top is None or bottom is None or bottom <= 0 else top / bottom * scale


def _read_metrics(path):
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            missing = sorted(REQUIRED_METRIC_COLUMNS - fields)
            if missing:
                raise ValueError(f"metrics.csv is missing columns: {', '.join(missing)}")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as error:
        raise ValueError("metrics.csv is not readable") from error

    by_key = {}
    for index, row in enumerate(rows, 2):
        batch_id, item_id = row.get("batch_id", "").strip(), row.get("item_id", "").strip()
        if not batch_id and not item_id:
            continue
        if not batch_id or not item_id:
            raise ValueError(f"metrics.csv row {index} must include batch_id and item_id")
        key = (batch_id, item_id)
        if key in by_key:
            raise ValueError(f"metrics.csv has duplicate row for {batch_id}/{item_id}")
        by_key[key] = (index, row)
    return by_key


def _rule(rule, root, tag):
    if not isinstance(rule, dict):
        raise ValueError(f"{tag}.decisionRule must be an object")
    status = rule.get("status")
    if status not in {"pending_baseline", "locked"}:
        raise ValueError(f"{tag}.decisionRule.status must be pending_baseline or locked")
    if rule.get("aggregation") != "median":
        raise ValueError(f"{tag}.decisionRule.aggregation must be median")
    values = [rule.get(name) for name in ("minimumObservations", "killBelow", "reuseAtOrAbove", "baselineReceipt")]
    if status == "pending_baseline":
        if any(value is not None for value in values):
            raise ValueError(f"{tag}.decisionRule pending baseline fields must be null")
        return rule

    minimum, kill, reuse, receipt = values
    if isinstance(minimum, bool) or not isinstance(minimum, int) or minimum < 1:
        raise ValueError(f"{tag}.decisionRule.minimumObservations must be a positive integer")
    if isinstance(kill, bool) or not isinstance(kill, (int, float)):
        raise ValueError(f"{tag}.decisionRule.killBelow must be numeric")
    if isinstance(reuse, bool) or not isinstance(reuse, (int, float)):
        raise ValueError(f"{tag}.decisionRule.reuseAtOrAbove must be numeric")
    if not math.isfinite(kill) or not math.isfinite(reuse):
        raise ValueError(f"{tag}.decisionRule thresholds must be finite")
    if kill >= reuse:
        raise ValueError(f"{tag}.decisionRule.killBelow must be less than reuseAtOrAbove")
    _inside(root, receipt, f"{tag}.decisionRule.baselineReceipt")
    return rule


def _operator_decision(experiment, tag):
    decision = experiment.get("decision")
    if not isinstance(decision, dict) or decision.get("verdict") not in DECISIONS:
        raise ValueError(f"{tag}.decision.verdict must be pending, kill, iterate, or reuse")
    verdict = decision["verdict"]
    if verdict == "pending":
        if decision.get("reason") is not None or decision.get("decidedAt") is not None:
            raise ValueError(f"{tag}.decision pending fields must be null")
        if experiment["state"] == "decided":
            raise ValueError(f"{tag}.state decided requires an operator verdict")
    else:
        if experiment["state"] != "decided":
            raise ValueError(f"{tag}.operator verdict requires state decided")
        _text(decision.get("reason"), f"{tag}.decision.reason")
        _timezone(decision.get("decidedAt"), f"{tag}.decision.decidedAt")
    return decision


def _advisory(state, rule, primary_values, observation_count, guardrail_missing, guardrail_failure):
    if state == "blocked":
        return {"verdict": "blocked", "reason": "Experiment has unresolved blockers."}
    if rule["status"] == "pending_baseline":
        return {"verdict": "insufficient_evidence", "reason": "Decision thresholds are pending the reviewed baseline."}
    if len(primary_values) < observation_count:
        return {"verdict": "insufficient_evidence", "reason": "At least one observation is missing the primary metric."}
    if len(primary_values) < rule["minimumObservations"]:
        return {"verdict": "insufficient_evidence", "reason": f"{len(primary_values)}/{rule['minimumObservations']} required observations have a primary metric."}
    if guardrail_missing:
        return {"verdict": "insufficient_evidence", "reason": "At least one observation is missing a hard guardrail result."}
    if guardrail_failure:
        return {"verdict": "kill", "reason": "A hard claims or corrections guardrail failed."}
    median = statistics.median(primary_values)
    if median < rule["killBelow"]:
        return {"verdict": "kill", "reason": "Median primary metric is below the locked kill threshold."}
    if median >= rule["reuseAtOrAbove"]:
        return {"verdict": "reuse", "reason": "Median primary metric meets the locked reuse threshold."}
    return {"verdict": "iterate", "reason": "Median primary metric falls between the locked thresholds."}


def load_growth_summary(manifest_path=MANIFEST, metrics_path=METRICS, root=ROOT):
    """Return a validated, read-only summary; raise ValueError on any contract violation."""
    root = Path(root).resolve()
    data = _read_json(Path(manifest_path), "growth manifest")
    if not isinstance(data, dict) or data.get("schema") != "tradercockpit-growth-experiments/v1":
        raise ValueError("growth manifest schema must be tradercockpit-growth-experiments/v1")
    _timezone(data.get("updatedAt"), "updatedAt")
    if data.get("paidActivation") != "disabled":
        raise ValueError("paidActivation must remain disabled")

    libraries = data.get("libraries")
    if not isinstance(libraries, dict):
        raise ValueError("libraries must be an object")
    library_by_id, library_counts = {}, {}
    for category, (field, prefix) in LIBRARIES.items():
        entries = libraries.get(category)
        if not isinstance(entries, list):
            raise ValueError(f"libraries.{category} must be an array")
        counts = {state: 0 for state in sorted(LIBRARY_STATES)}
        for index, entry in enumerate(entries):
            tag = f"libraries.{category}[{index}]"
            if not isinstance(entry, dict):
                raise ValueError(f"{tag} must be an object")
            item_id = _text(entry.get("id"), f"{tag}.id")
            if not item_id.startswith(prefix):
                raise ValueError(f"{tag}.id must start with {prefix}")
            if item_id in library_by_id:
                raise ValueError(f"duplicate library id {item_id}")
            if entry.get("state") not in LIBRARY_STATES:
                raise ValueError(f"{tag}.state must be active, hypothesis, or blocked")
            _text(entry.get("label"), f"{tag}.label")
            _text(entry.get("description"), f"{tag}.description")
            if entry.get("unlock") is not None:
                _text(entry["unlock"], f"{tag}.unlock")
            library_by_id[item_id] = (field, entry)
            counts[entry["state"]] += 1
        library_counts[category] = counts

    experiments = data.get("experiments")
    if not isinstance(experiments, list):
        raise ValueError("experiments must be an array")
    experiment_by_id = {}
    for index, experiment in enumerate(experiments):
        tag = f"experiments[{index}]"
        if not isinstance(experiment, dict):
            raise ValueError(f"{tag} must be an object")
        experiment_id = _text(experiment.get("id"), f"{tag}.id")
        if not experiment_id.startswith("exp-"):
            raise ValueError(f"{tag}.id must start with exp-")
        if experiment_id in experiment_by_id:
            raise ValueError(f"duplicate experiment id {experiment_id}")
        experiment_by_id[experiment_id] = experiment

    metric_rows = _read_metrics(Path(metrics_path))
    summaries = []
    for index, experiment in enumerate(experiments):
        tag = f"experiments[{index}]"
        experiment_id = experiment["id"]
        if experiment.get("lane") not in LANES:
            raise ValueError(f"{tag}.lane must be new or reuse")
        if experiment.get("state") not in EXPERIMENT_STATES:
            raise ValueError(f"{tag}.state is unsupported")
        if experiment.get("surface") not in SURFACES:
            raise ValueError(f"{tag}.surface is unsupported")
        if experiment["surface"] == "landing" and experiment["state"] != "blocked":
            raise ValueError(f"{tag} landing experiments must remain blocked in v1")
        _text(experiment.get("hypothesis"), f"{tag}.hypothesis")

        assembly = experiment.get("assembly")
        if not isinstance(assembly, dict):
            raise ValueError(f"{tag}.assembly must be an object")
        blocked_library = False
        for category, (field, _) in LIBRARIES.items():
            reference = _text(assembly.get(field), f"{tag}.assembly.{field}")
            found = library_by_id.get(reference)
            if not found or found[0] != field:
                raise ValueError(f"{tag}.assembly.{field} references an unknown {field}")
            blocked_library |= found[1]["state"] == "blocked"
        if blocked_library and experiment["state"] != "blocked":
            raise ValueError(f"{tag} uses a blocked library entry and must remain blocked")
        if experiment.get("changedComponent") not in {value[0] for value in LIBRARIES.values()}:
            raise ValueError(f"{tag}.changedComponent is unsupported")

        comparison = experiment.get("comparison")
        if comparison != "baseline":
            compared = experiment_by_id.get(comparison)
            if not compared or compared is experiment:
                raise ValueError(f"{tag}.comparison references an unknown experiment")
            other = compared.get("assembly", {})
            changed = [field for field, _ in LIBRARIES.values() if assembly.get(field) != other.get(field)]
            if changed != [experiment["changedComponent"]]:
                raise ValueError(f"{tag}.comparison must change exactly {experiment['changedComponent']}")

        metrics = experiment.get("metrics")
        if not isinstance(metrics, dict) or metrics.get("primary") not in SUPPORTED_METRICS:
            raise ValueError(f"{tag}.metrics.primary is unsupported")
        secondary = metrics.get("secondary")
        if not isinstance(secondary, list) or any(metric not in SUPPORTED_METRICS for metric in secondary):
            raise ValueError(f"{tag}.metrics.secondary contains an unsupported metric")
        if len(secondary) != len(set(secondary)) or metrics["primary"] in secondary:
            raise ValueError(f"{tag}.metrics must not repeat metrics")
        guardrails = metrics.get("guardrails")
        if not isinstance(guardrails, list) or set(guardrails) != GUARDRAILS or len(guardrails) != len(GUARDRAILS):
            raise ValueError(f"{tag}.metrics.guardrails must contain claims_gate_pass and corrections_zero")

        rule = _rule(experiment.get("decisionRule"), root, tag)
        decision = _operator_decision(experiment, tag)
        blockers = experiment.get("blockers")
        if not isinstance(blockers, list) or any(not isinstance(value, str) or not value.strip() for value in blockers):
            raise ValueError(f"{tag}.blockers must be an array of non-empty strings")
        if experiment["state"] == "blocked" and not blockers:
            raise ValueError(f"{tag}.state blocked requires blockers")
        if experiment["state"] != "blocked" and blockers:
            raise ValueError(f"{tag}.blockers require state blocked")

        observations = experiment.get("observations")
        if not isinstance(observations, list):
            raise ValueError(f"{tag}.observations must be an array")
        if experiment["state"] in {"running", "measured", "decided"} and not observations:
            raise ValueError(f"{tag}.state {experiment['state']} requires observations")
        seen_observations, joined = set(), []
        for observation_index, observation in enumerate(observations):
            observation_tag = f"{tag}.observations[{observation_index}]"
            if not isinstance(observation, dict):
                raise ValueError(f"{observation_tag} must be an object")
            batch_path = _inside(root, observation.get("batch"), f"{observation_tag}.batch")
            item_id = _text(observation.get("itemId"), f"{observation_tag}.itemId")
            key = (str(batch_path), item_id)
            if key in seen_observations:
                raise ValueError(f"{tag}.observations contains a duplicate")
            seen_observations.add(key)
            batch = _read_json(batch_path, f"{observation_tag}.batch")
            if not isinstance(batch, dict) or batch.get("schema") != "social-batch/v1":
                raise ValueError(f"{observation_tag}.batch must use social-batch/v1")
            batch_id = _text(batch.get("batchId"), f"{observation_tag}.batch.batchId")
            items = batch.get("items")
            matches = [item for item in items if isinstance(item, dict) and item.get("id") == item_id] if isinstance(items, list) else []
            if len(matches) != 1:
                raise ValueError(f"{observation_tag}.itemId must identify one batch item")
            if matches[0].get("channel") != experiment["surface"]:
                raise ValueError(f"{observation_tag}.itemId channel must match experiment surface")
            metric_entry = metric_rows.get((batch_id, item_id))
            if metric_entry and metric_entry[1].get("channel", "").strip() != experiment["surface"]:
                raise ValueError(f"metrics.csv channel must match {experiment_id} surface")
            row_number, row = metric_entry if metric_entry else (None, None)
            row_tag = f"metrics.csv row {row_number}" if row_number else "missing metrics row"
            values = {name: _metric_value(row, name, row_tag) for name in [metrics["primary"], *secondary]}
            claims_gate = None if row is None else row.get("claims_gate", "").strip().upper()
            corrections = None if row is None else _number(row, "corrections", row_tag)
            row_guardrails = {
                "claims_gate_pass": None if not claims_gate else claims_gate == "PASS",
                "corrections_zero": None if corrections is None else corrections == 0,
            }
            joined.append({
                "batchId": batch_id,
                "itemId": item_id,
                "hasMetrics": row is not None,
                "metrics": values,
                "guardrails": row_guardrails,
            })

        primary_values = [item["metrics"][metrics["primary"]] for item in joined if item["metrics"][metrics["primary"]] is not None]
        guardrails = [value for item in joined for value in item["guardrails"].values()]
        guardrail_missing = any(value is None for value in guardrails)
        guardrail_failure = any(value is False for value in guardrails)
        advisory = _advisory(
            experiment["state"], rule, primary_values, len(joined), guardrail_missing, guardrail_failure,
        )
        if experiment["state"] in {"measured", "decided"} and not primary_values:
            raise ValueError(f"{tag}.state {experiment['state']} requires a primary metric observation")
        if experiment["state"] == "decided":
            if rule["status"] != "locked" or advisory["verdict"] in {"blocked", "insufficient_evidence"}:
                raise ValueError(f"{tag}.state decided requires sufficient evidence and a locked rule")
            if guardrail_failure and decision["verdict"] == "reuse":
                raise ValueError(f"{tag}.decision cannot reuse after a hard guardrail failure")

        summaries.append({
            "id": experiment_id,
            "lane": experiment["lane"],
            "state": experiment["state"],
            "surface": experiment["surface"],
            "hypothesis": experiment["hypothesis"],
            "assembly": assembly,
            "changedComponent": experiment["changedComponent"],
            "comparison": comparison,
            "observationCount": len(joined),
            "primaryMetric": metrics["primary"],
            "primaryValues": primary_values,
            "primaryMedian": statistics.median(primary_values) if primary_values else None,
            "advisory": advisory,
            "decision": decision,
            "blockers": blockers,
            "observations": joined,
        })

    state_counts = {state: sum(item["state"] == state for item in summaries) for state in sorted(EXPERIMENT_STATES)}
    return {
        "schema": data["schema"],
        "valid": True,
        "updatedAt": data["updatedAt"],
        "paidActivation": data["paidActivation"],
        "libraryCounts": library_counts,
        "experimentStateCounts": state_counts,
        "experiments": summaries,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "report"))
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        summary = load_growth_summary()
    except ValueError as error:
        raise SystemExit(f"BLOCK: {error}") from error
    if args.command == "validate":
        print(f"growth-experiments: PASS — {len(summary['experiments'])} experiments, paid disabled")
    elif args.as_json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        for experiment in summary["experiments"]:
            print(f"{experiment['id']}: {experiment['state']} / {experiment['advisory']['verdict']}")


if __name__ == "__main__":
    main()
