#!/usr/bin/env python3
"""Fail-closed drift check for the Episode 1 intake evidence contract.

The check deliberately reads the recorded phase artifacts named by the E01
manifest.  It does not rerun Futures, mutate external files, or validate a
trading strategy.  Its job is narrower: prove that the numbers used by the
lesson still describe the same three real, wired, not-yet-validated intake
runs and that the Dow failure census is recomputable from the hash-bound JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "productions/_series/e01-e03-live-receipts-2026-08-03.json"

EXPECTED_RUNS = [
    {
        "label": "Dow futures",
        "run_id": "rb-20260725T133803-b44bd92c",
        "phase": "phase01_intake",
        "window": {"start": "2010-06-06", "end": "2018-02-25"},
        "entering": 1335,
        "surviving": 184,
        "dropped": 1151,
        "provenance": {"data_source": "real", "validated": False, "wiring_proof": True},
    },
    {
        "label": "S&P 500 futures",
        "run_id": "rb-20260715T094910-d0d18d9a",
        "phase": "phase01_intake",
        "window": {"start": "2003-07-06", "end": "2013-06-08"},
        "entering": 2004,
        "surviving": 0,
        "dropped": 2004,
        "provenance": {"data_source": "real", "validated": False, "wiring_proof": True},
    },
    {
        "label": "EURUSD",
        "run_id": "rb-20260715T154557-12660559",
        "phase": "phase01_intake",
        "window": {"start": "2022-01-02", "end": "2023-09-06"},
        "entering": 2051,
        "surviving": 0,
        "dropped": 2051,
        "provenance": {"data_source": "real", "validated": False, "wiring_proof": True},
    },
]

EXPECTED_CENSUS = {
    "entering": 1335,
    "surviving": 184,
    "dropped": 1151,
    "failed_return_to_drawdown": 1122,
    "failed_profit_factor": 1065,
    "failed_activity": 150,
    "overlap_warning": "The three failure counts overlap; they are not additive.",
}

EXPECTED_CANDIDATE = {
    "candidate_id": "formula-2851293728-1566",
    "profit_factor": 1.28037,
    "return_to_drawdown": 4.932417,
    "trades": 553,
    "wins": 210,
    "losses": 343,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _assert(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _same(errors: list[str], label: str, actual: Any, expected: Any) -> None:
    _assert(errors, actual == expected, f"{label}: expected {expected!r}, got {actual!r}")


def _check_phase_artifact(errors: list[str], receipt: dict[str, Any]) -> dict[str, Any]:
    path = Path(receipt["source_path"])
    if not path.exists():
        errors.append(f"{receipt['label']}: source artifact is missing: {path}")
        return {}

    _same(errors, f"{receipt['label']} source sha256", sha256(path), receipt["sha256"])
    data = json.loads(path.read_text(encoding="utf-8"))
    _same(errors, f"{receipt['label']} run_id", data.get("run_id"), receipt["run_id"])
    _same(errors, f"{receipt['label']} phase_key", data.get("phase_key"), receipt["phase"])
    _same(errors, f"{receipt['label']} window", data.get("window"), receipt["window"])
    _same(errors, f"{receipt['label']} entering row count", len(data.get("entering", [])), receipt["entering"])
    _same(errors, f"{receipt['label']} surviving row count from source", len(data.get("surviving", [])), receipt["surviving"])
    _same(errors, f"{receipt['label']} dropped row count from source", len(data.get("dropped", [])), receipt["dropped"])
    _same(errors, f"{receipt['label']} provenance", data.get("provenance"), receipt["provenance"])
    _same(errors, f"{receipt['label']} candidate row count", len(data.get("candidates", {})), receipt["entering"])
    _same(errors, f"{receipt['label']} entering arithmetic", receipt["entering"], receipt["surviving"] + receipt["dropped"])
    if "surviving_real" in data:
        _same(errors, f"{receipt['label']} surviving_real row count", len(data["surviving_real"]), receipt["surviving"])
    return data


def validate_manifest(manifest: dict[str, Any], *, verify_external: bool = True) -> dict[str, Any]:
    """Validate E01 and return the measured values for a concise CLI receipt."""
    errors: list[str] = []
    episode = manifest.get("episodes", {}).get("01", {})
    _same(errors, "E01 aggregate", episode.get("aggregate"), {
        "entering": 5390,
        "surviving": 184,
        "rejected": 5206,
        "calculation": "1335 + 2004 + 2051 = 5390; 184 + 0 + 0 = 184; 5390 - 184 = 5206",
    })

    runs = episode.get("runs", [])
    _same(errors, "E01 run count", len(runs), len(EXPECTED_RUNS))
    for index, expected in enumerate(EXPECTED_RUNS):
        if index >= len(runs):
            continue
        actual = runs[index]
        for key in ("label", "run_id", "phase", "window", "entering", "surviving", "dropped", "provenance"):
            _same(errors, f"E01 run {index + 1} {key}", actual.get(key), expected[key])
        _same(errors, f"E01 run {index + 1} arithmetic", actual.get("entering"), actual.get("surviving", 0) + actual.get("dropped", 0))

    _same(errors, "E01 census", episode.get("dow_gate_census"), EXPECTED_CENSUS)
    candidate = episode.get("dow_candidate_examples", {}).get("is_survivor", {})
    _same(errors, "E01 candidate identity", candidate.get("candidate_id"), EXPECTED_CANDIDATE["candidate_id"])
    for key in ("profit_factor", "return_to_drawdown", "trades", "wins", "losses"):
        _same(errors, f"E01 candidate {key}", candidate.get(key), EXPECTED_CANDIDATE[key])

    measured: dict[str, Any] = {
        "aggregate_entering": episode.get("aggregate", {}).get("entering"),
        "aggregate_surviving": episode.get("aggregate", {}).get("surviving"),
        "aggregate_rejected": episode.get("aggregate", {}).get("rejected"),
        "run_artifacts_verified": 0,
        "census_recomputed": False,
    }

    phase_data: list[dict[str, Any]] = []
    if verify_external:
        for receipt in runs:
            data = _check_phase_artifact(errors, receipt)
            if data:
                measured["run_artifacts_verified"] += 1
                phase_data.append(data)

        if phase_data:
            dow = phase_data[0]
            candidates = dow.get("candidates", {})
            recomputed = {
                "entering": len(candidates),
                "surviving": len(dow.get("surviving", [])),
                "dropped": len(dow.get("dropped", [])),
                "failed_return_to_drawdown": sum(not row["gates"]["ret_dd"]["pass"] for row in candidates.values()),
                "failed_profit_factor": sum(not row["gates"]["pf"]["pass"] for row in candidates.values()),
                "failed_activity": sum(not row["gates"]["trades_per_month"]["pass"] for row in candidates.values()),
            }
            expected_recomputed = {key: EXPECTED_CENSUS[key] for key in recomputed}
            _same(errors, "E01 recomputed Dow census", recomputed, expected_recomputed)
            measured["census_recomputed"] = not errors
            row = candidates.get(EXPECTED_CANDIDATE["candidate_id"])
            _assert(errors, row is not None, "E01 candidate row is absent from the hash-bound Dow phase artifact")
            if row is not None:
                _assert(errors, EXPECTED_CANDIDATE["candidate_id"] in dow.get("surviving", []), "E01 candidate is not in the recorded Dow survivor list")
                metrics = row.get("metrics", {})
                _same(errors, "E01 candidate source profit_factor", metrics.get("pf"), EXPECTED_CANDIDATE["profit_factor"])
                _same(errors, "E01 candidate source return_to_drawdown", metrics.get("ret_dd"), EXPECTED_CANDIDATE["return_to_drawdown"])
                _same(errors, "E01 candidate source trades", metrics.get("n"), EXPECTED_CANDIDATE["trades"])
                _same(errors, "E01 candidate source wins", metrics.get("wins"), EXPECTED_CANDIDATE["wins"])
                _same(errors, "E01 candidate source losses", metrics.get("losses"), EXPECTED_CANDIDATE["losses"])

    if errors:
        raise ValueError("\n".join(f"- {error}" for error in errors))
    return measured


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--skip-external", action="store_true", help="Validate the local manifest contract without opening the external phase artifacts.")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    measured = validate_manifest(manifest, verify_external=not args.skip_external)
    print("E01 intake drift check: PASS")
    print(f"manifest={args.manifest}")
    print(f"aggregate={measured['aggregate_entering']} entering -> {measured['aggregate_surviving']} surviving; {measured['aggregate_rejected']} rejected")
    if args.skip_external:
        print("external_phase_artifacts=SKIPPED")
    else:
        print(f"external_phase_artifacts=VERIFIED ({measured['run_artifacts_verified']}/3)")
        print("dow_failure_census=RECOMPUTED (overlap preserved; counts are not additive)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
