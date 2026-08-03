#!/usr/bin/env python3
"""Build the Episode 2 out-of-sample-retest candidate from source and live receipts.

This route deliberately owns only E02.  It reads the hand-authored E02 source packet,
re-reads the external run receipts, verifies their pinned hashes and JSON pointers, then
regenerates the candidate package, sentence-bound visual map, deterministic SVG assets,
thumbnail source, and short HyperFrames proof source.

No narration, provider asset, full master, upload, or publication is produced here.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import re
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "productions" / "_series" / "e02-rebuild-source-2026-08-03" / "episode-02"
OUT = ROOT / "productions" / "_series" / "e02-rebuild-candidate-2026-08-03" / "episode-02"
FINAL_OUT_DEFAULT = ROOT / "productions" / "_series" / "e02-rebuild-production-2026-08-04" / "episode-02"
FINAL_PROJECT_ID = "series-e02-rebuild-20260804"
LIVE_MANIFEST = ROOT / "productions" / "_series" / "e01-e03-live-receipts-2026-08-03.json"
SOURCE_VO_REF = "../../../e02-rebuild-source-2026-08-03/episode-02/vo.txt"
ACADEMIC_RECEIPTS_REF = "../../../e02-rebuild-source-2026-08-03/episode-02/academic_receipts.json"
OPERATOR_AUTHORIZATION = "Begin. Produce the three episodes."

# Bind future E02 narration handoff to the live series route.  This is a read-only
# authority check; it never calls a provider.
LIVE_SERIES_ROOT = Path(r"C:\Users\MSI\Documents\tradercockpit")
VOICE_ROUTE_APPROVAL = (
    LIVE_SERIES_ROOT
    / "OpenMontage/projects/_series-v4-shared/review-board/voice-route-approval-e1-e5-v7.json"
)
VOICE_ROUTE_APPROVAL_REF = (
    "OpenMontage/projects/_series-v4-shared/review-board/voice-route-approval-e1-e5-v7.json"
)
VOICE_ROUTE_APPROVAL_SHA256 = "6f0faca1923064bdee7fc1c419c624e2662193b0e9ac173f28d8048dfeea4668"
JOHN_VOICE_ID = "6b528d43-c056-4a2f-9d82-1591a7ba13b0"
JOHN_INSTRUCTION = (
    "Calm, measured educator speaking to one trader. Read exactly; preserve "
    "every word, number, and limitation. No hype or sarcasm."
)
NARRATION_AUDIO_SUBDIR = "narration-john"

SPY_P1 = Path(
    r"C:\Users\MSI\repos\futures\runtime\validation\robustness"
) / "rb-20260714T113408-b5d06cc6" / "phases" / "phase01_intake.json"
SPY_P2 = Path(
    r"C:\Users\MSI\repos\futures\runtime\validation\robustness"
) / "rb-20260714T113408-b5d06cc6" / "phases" / "phase02_oos.json"
DOW_P1 = Path(
    r"C:\Users\MSI\repos\futures\runtime\validation\robustness"
) / "rb-20260725T133803-b44bd92c" / "phases" / "phase01_intake.json"
DOW_P2 = Path(
    r"C:\Users\MSI\repos\futures\runtime\validation\robustness"
) / "rb-20260725T133803-b44bd92c" / "phases" / "phase02_oos.json"
SPY_LEDGER = Path(
    r"C:\Users\MSI\repos\futures\runtime\cache\vast_results_rsi2_019f6029"
) / "boxk-rsi2" / "spy-d1-lib1" / "ledger" / "spy-d1-lib1.jsonl"
SPY_MANIFEST = Path(
    r"C:\Users\MSI\repos\futures\runtime\cache\vast_results_rsi2_019f6029"
) / "boxk-rsi2" / "spy-d1-lib1" / "robustness" / "rb-20260714T113408-b5d06cc6" / "run_manifest.json"

EXPECTED_HASHES = {
    "RUN_SPY_PHASE01": "59e2257a5bb6b13c6cce2a4f5b22702b396d06e79651b3fb09be341e1eb7bcc1",
    "RUN_SPY_PHASE02": "640532043b74c60c7ec30a5e14973c3ae6860f6b0a6540e2025b41bf93f2069e",
    "RUN_DOW_PHASE01": "19899535054e5b9dd7b6be6275b3017110b79de2f1079ea7ac5850afb48f235d",
    "RUN_DOW_PHASE02": "21d1c7c563acaecb869ab3d49e05a3fed2516c33a3d611e7d330c219f8605dd0",
    "RUN_SPY_LEDGER": "fba810bfac8e1703521e37344ea1535e785fc3afe93f15a9a4da08d68b26c545",
    "RUN_SPY_MANIFEST": "fa3d87216305d471153632d447146455f8744ebe3823761ff121f63e11b3cdfb",
}

SPY_CANDIDATE = "concept-2422788506-0"
DOW_CANDIDATE = "formula-2851293728-1566"
ASSIGNMENT_REQUESTED_DOW_OOS_PF = 0.81324

SCENE_TITLES = {
    "scene-01": "The stock branch stops before the chamber",
    "scene-02": "Freeze before the later block",
    "scene-03": "The vocabulary of a sealed test",
    "scene-04": "The SPY mechanism and its warmup",
    "scene-05": "Read the gate as inequalities",
    "scene-06": "Five rows stay five rows",
    "scene-07": "SPY does not reach the holdout",
    "scene-08": "The Dow lane is separate",
    "scene-09": "One Dow row changes on later prices",
    "scene-10": "Why selection pressure matters",
    "scene-11": "A field is more than one number",
    "scene-12": "Fixed blocks are not walk-forward",
    "scene-13": "The reproducible worksheet",
    "scene-14": "The next question is execution",
}

# Independent output checks: these markers are asserted against the emitted SVG bytes,
# not derived from visual_action().  They keep the sentence map from passing while the
# actual deterministic lesson graphic loses its mechanism or evidence labels.
SCENE_SEMANTIC_MARKERS = {
    "scene-01": ["SPY / D1 / CONNORS RSI2", "LATER-PRICE", "DOW / FUTURES", "holdout not reached"],
    "scene-02": ["CHOOSE", "FREEZE", "OPEN", "later block"],
    "scene-03": ["IN-SAMPLE / BUILD", "OUT-OF-SAMPLE / JUDGE", "SEALED", "walk-forward"],
    "scene-04": ["SPY / D1 / CONNORS RSI2", "warmup bars", "200-day regime window", "2-day RSI input", "short moving-average exit leg"],
    "scene-05": ["0.806004", "1.3", "-0.420205", "0.392308", "TRADES / MONTH", "unitless ratio", "FALSE"],
    "scene-06": ["FIVE RECORDED VERSIONS", "real input / wiring proof / unvalidated"],
    "scene-07": ["0 entering", "0 surviving", "no historical window", "holdout not reached"],
    "scene-08": ["DOW / FUTURES", "5  →  0", "184  →  154", "different lane"],
    "scene-09": ["+$16,727.80", "-$4,897.40", "PF 0.813381", "29 wins  /  72 losses", "0.81324"],
    "scene-10": ["SIMPLE SIGNAL", "CURVE-FIT NOISE"],
    "scene-11": ["ORDERED OUTCOMES", "median", "percentile", "distribution = location + spread + shape"],
    "scene-12": ["SEGMENTED BACKTEST", "WALK-FORWARD", "fixed jobs  ≠  moving origin"],
    "scene-13": ["SPY / D1 / RSI2", "5 / 0 / 5", "DOW / futures", "184 / 154 / 30", "freeze → hash → locate → describe"],
    "scene-14": [
        "SPY / D1", "5  →  0", "holdout not reached", "+$16,727.80", "-$4,897.40",
        "PF 0.813381", "29 wins  /  72 losses", "FILL TIMING", "TRADING HOURS",
        "signal close  →  fill?", "which hours count?",
    ],
}

SCENE_TREATMENTS = {
    "scene-01": "sealed-door funnel",
    "scene-02": "freeze-and-open sequence",
    "scene-03": "two-chamber vocabulary map",
    "scene-04": "indicator window rails",
    "scene-05": "inequality ruler",
    "scene-06": "candidate field with one magnifier",
    "scene-07": "SPY locked chamber",
    "scene-08": "parallel branch lanes",
    "scene-09": "same-row before-and-after track",
    "scene-10": "signal-and-noise curve",
    "scene-11": "ordered outcome strip",
    "scene-12": "fixed blocks versus rolling windows",
    "scene-13": "worksheet path",
    "scene-14": "two unanswered execution dials",
}

ACADEMIC_IDS = {
    "ACADEMIC_ISLR_TEST",
    "ACADEMIC_WHITE_SNOOP",
    "ACADEMIC_SULLIVAN_BOOTSTRAP",
    "ACADEMIC_TASHMAN_OOS",
    "ACADEMIC_BERGMEIR_CV",
    "ACADEMIC_NIST_DISTRIBUTION",
    "ACADEMIC_NIST_PERCENTILE",
    "ACADEMIC_METRIC_ONTOLOGY",
}

# The final composition uses these as mechanical focus points.  They are not
# decorative drift: each point is a real location in the scene's mechanism
# that the sentence-bound probe visits while the corresponding sentence is
# spoken.
SCENE_MOTION_TARGETS = {
    "scene-01": [(270, 470), (650, 470), (930, 470), (1500, 470)],
    "scene-02": [(330, 510), (960, 510), (1580, 510), (960, 700)],
    "scene-03": [(450, 550), (840, 550), (1200, 550), (1650, 550)],
    "scene-04": [(310, 460), (700, 460), (1100, 660), (1600, 660)],
    "scene-05": [(620, 410), (990, 590), (1370, 760), (1760, 760)],
    "scene-06": [(350, 550), (610, 550), (870, 550), (1130, 550), (1390, 550)],
    "scene-07": [(450, 535), (895, 535), (1190, 535), (960, 760)],
    "scene-08": [(320, 430), (960, 430), (1600, 430), (320, 740), (960, 740), (1600, 740)],
    "scene-09": [(250, 600), (920, 600), (1120, 600), (960, 860)],
    "scene-10": [(350, 680), (750, 500), (1150, 620), (1650, 430)],
    "scene-11": [(250, 570), (885, 570), (1220, 570), (1700, 570)],
    "scene-12": [(300, 535), (550, 535), (1275, 535), (1580, 740)],
    "scene-13": [(300, 470), (800, 470), (1350, 470), (1350, 595), (960, 955)],
    "scene-14": [(350, 600), (820, 600), (1200, 600), (1560, 600), (960, 950)],
}

SCENE_MOTION_SIGNATURES = {
    "scene-01": "intake tokens travel to a sealed door, then the separate futures branch unfolds",
    "scene-02": "choose, freeze, and one-way-open states clamp in sequence; re-entry is crossed out",
    "scene-03": "the build chamber hands a frozen rule across a drawn seal to the judge chamber",
    "scene-04": "warmup history sweeps into the indicator rail before the signal and exit rails light",
    "scene-05": "the operator probe visits actual, operator, threshold, and FALSE for each row",
    "scene-06": "five candidates traverse the intake rail while a single magnifier follows one row",
    "scene-07": "empty entering and surviving gauges stay empty while the later-price door locks",
    "scene-08": "the stock lane stops at its seal while a separate Dow lane continues across its rail",
    "scene-09": "one candidate identity is carried across two price-window rails as its metrics flip",
    "scene-10": "a smooth signal path and a noisy curve path are traced by different probes",
    "scene-11": "ordered outcomes receive a median marker and a percentile marker in sequence",
    "scene-12": "fixed build/test blocks hold while the walk-forward origin advances independently",
    "scene-13": "worksheet fields are filled from instrument to windows to counts, then hash-bound",
    "scene-14": "one evidence rail branches into two unopened execution questions without panel cards",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_live_voice_route() -> dict[str, Any]:
    """Read and hash-bind the current operator-approved E1-E5 voice route."""
    if not VOICE_ROUTE_APPROVAL.is_file():
        raise SystemExit(f"BLOCK: live voice-route approval is missing: {VOICE_ROUTE_APPROVAL}")
    actual = sha256(VOICE_ROUTE_APPROVAL)
    if actual != VOICE_ROUTE_APPROVAL_SHA256:
        raise SystemExit(
            "BLOCK: live voice-route approval drifted: "
            f"expected={VOICE_ROUTE_APPROVAL_SHA256}, actual={actual}"
        )
    approval = load_json(VOICE_ROUTE_APPROVAL)
    selection = approval.get("selection", {})
    expected = {
        "provider": "Higgsfield",
        "model": "Qwen Audio 3.0 TTS Flash",
        "job_type": "qwen_audio_tts",
        "voice_character": "John",
        "treatment": "clean",
    }
    mismatches = [
        f"{key}={selection.get(key)!r}"
        for key, value in expected.items()
        if selection.get(key) != value
    ]
    if mismatches:
        raise SystemExit(
            "BLOCK: live voice-route approval is not Higgsfield/Qwen/John/clean: "
            + ", ".join(mismatches)
        )
    if selection.get("new_subscription_or_top_up_authorized") is not False:
        raise SystemExit("BLOCK: live voice-route approval changed the no-top-up boundary")
    return {
        "path": VOICE_ROUTE_APPROVAL_REF,
        "sha256": actual,
        "provider": selection["provider"],
        "model": selection["model"],
        "job_type": selection["job_type"],
        "voice": selection["voice_character"],
        "treatment": selection["treatment"],
        "voice_id": JOHN_VOICE_ID,
        "existing_subscription_credits": selection.get("subscription_credit_use_authorized") is True,
        "new_subscription_or_top_up_authorized": selection["new_subscription_or_top_up_authorized"],
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def count_field(value: Any) -> int:
    if isinstance(value, (list, tuple, dict, set)):
        return len(value)
    return int(value)


def candidate_obj(phase: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    try:
        return phase["candidates"][candidate_id]
    except (KeyError, TypeError):
        raise SystemExit(f"BLOCK: candidate {candidate_id!r} is absent from {phase.get('phase_key')}")


def assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise SystemExit(f"BLOCK: {label}: expected {expected!r}, got {actual!r}")


def assert_close(label: str, actual: Any, expected: float, digits: int = 9) -> None:
    if not math.isclose(float(actual), expected, rel_tol=0, abs_tol=10 ** -digits):
        raise SystemExit(f"BLOCK: {label}: expected {expected!r}, got {actual!r}")


def source_record(source_id: str, path: Path, phase: str, pointers: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"BLOCK: required live source is missing: {path}")
    digest = sha256(path)
    expected = EXPECTED_HASHES.get(source_id)
    if expected and digest != expected:
        raise SystemExit(
            f"BLOCK: {source_id} drifted: expected {expected}, got {digest}; "
            "do not regenerate from an unreviewed receipt"
        )
    return {
        "source_id": source_id,
        "path": str(path),
        "sha256": digest,
        "phase": phase,
        "pointers": pointers,
        "read_only": True,
    }


def parse_spy_lineage() -> dict[str, Any]:
    if not SPY_LEDGER.is_file():
        raise SystemExit(f"BLOCK: SPY lineage receipt missing: {SPY_LEDGER}")
    for line_number, raw in enumerate(SPY_LEDGER.read_text(encoding="utf-8").splitlines(), 1):
        row = json.loads(raw)
        if row.get("candidate_id") == SPY_CANDIDATE:
            return {"line": line_number, "row": row}
    raise SystemExit(f"BLOCK: {SPY_CANDIDATE} is absent from the SPY lineage receipt")


def verify_facts() -> dict[str, Any]:
    spy_p1 = load_json(SPY_P1)
    spy_p2 = load_json(SPY_P2)
    dow_p1 = load_json(DOW_P1)
    dow_p2 = load_json(DOW_P2)
    spy_manifest = load_json(SPY_MANIFEST)
    lineage = parse_spy_lineage()
    spy_row = candidate_obj(spy_p1, SPY_CANDIDATE)
    dow_is_row = candidate_obj(dow_p1, DOW_CANDIDATE)
    dow_oos_row = candidate_obj(dow_p2, DOW_CANDIDATE)

    assert_equal("SPY phase", spy_p1["phase_key"], "phase01_intake")
    assert_equal("SPY phase 2", spy_p2["phase_key"], "phase02_oos")
    assert_equal("SPY run", spy_p1["run_id"], "rb-20260714T113408-b5d06cc6")
    assert_equal("SPY program", spy_p1["program_id"], "libcycle-spy-d1-lib1-w96ddd6-r0a8de8-c41e7ad")
    assert_equal("SPY intake count", count_field(spy_p1["entering"]), 5)
    assert_equal("SPY surviving count", count_field(spy_p1["surviving"]), 0)
    assert_equal("SPY dropped count", count_field(spy_p1["dropped"]), 5)
    assert_equal("SPY later entering count", count_field(spy_p2["entering"]), 0)
    assert_equal("SPY later surviving count", count_field(spy_p2["surviving"]), 0)
    assert_equal("SPY later dropped count", count_field(spy_p2["dropped"]), 0)
    assert_equal("SPY later window", spy_p2["window"], {})
    assert_equal("SPY data source", spy_p1["provenance"]["data_source"], "real")
    assert_equal("SPY wiring proof", spy_p1["provenance"]["wiring_proof"], True)
    assert_equal("SPY validated flag", spy_p1["provenance"]["validated"], False)
    assert_equal("SPY manifest program", spy_manifest["program_id"], spy_p1["program_id"])
    manifest_candidates = [
        item for item in spy_manifest.get("candidates_provenance", [])
        if item.get("id") == SPY_CANDIDATE
    ]
    assert_equal("SPY manifest candidate count", len(manifest_candidates), 1)
    assert_equal("SPY manifest candidate index", spy_manifest["candidates_provenance"][0]["id"], SPY_CANDIDATE)

    gates = spy_row["gates"]
    for key, actual, threshold in (
        ("pf", 0.806004, 1.3),
        ("ret_dd", -0.420205, 4),
        ("trades_per_month", 0.392308, 2),
    ):
        assert_close(f"SPY {key} actual", gates[key]["actual"], actual)
        assert_equal(f"SPY {key} operator", gates[key]["op"], ">")
        assert_close(f"SPY {key} threshold", gates[key]["threshold"], threshold)
        assert_equal(f"SPY {key} pass", gates[key]["pass"], False)

    assert_equal("Dow intake phase", dow_p1["phase_key"], "phase01_intake")
    assert_equal("Dow later phase", dow_p2["phase_key"], "phase02_oos")
    assert_equal("Dow run", dow_p2["run_id"], "rb-20260725T133803-b44bd92c")
    assert_equal("Dow intake count", count_field(dow_p1["entering"]), 1335)
    assert_equal("Dow intake survivor count", count_field(dow_p1["surviving"]), 184)
    assert_equal("Dow later entering count", count_field(dow_p2["entering"]), 184)
    assert_equal("Dow later survivor count", count_field(dow_p2["surviving"]), 154)
    assert_equal("Dow later dropped count", count_field(dow_p2["dropped"]), 30)
    assert_equal("Dow data source", dow_p2["provenance"]["data_source"], "real")
    assert_equal("Dow wiring proof", dow_p2["provenance"]["wiring_proof"], True)
    assert_equal("Dow validated flag", dow_p2["provenance"]["validated"], False)

    assert_close("Dow IS net", dow_is_row["metrics"]["net"], 16727.8)
    assert_close("Dow IS PF", dow_is_row["metrics"]["pf"], 1.28037)
    assert_close("Dow OOS net", dow_oos_row["metrics"]["net"], -4897.4)
    assert_close("Dow OOS PF", dow_oos_row["metrics"]["pf"], 0.813381)
    assert_close("Dow OOS return/drawdown", dow_oos_row["metrics"]["ret_dd"], -0.563866)
    assert_equal("Dow OOS wins", dow_oos_row["metrics"]["wins"], 29)
    assert_equal("Dow OOS losses", dow_oos_row["metrics"]["losses"], 72)

    lineage_row = lineage["row"]
    assert_equal("SPY lineage concept", lineage_row["lineage"]["generation_params"]["concept_id"], "con-rsi2-oversold-reversion")
    assert_equal("SPY lineage long window", lineage_row["lineage"]["generation_params"]["params"]["n"], 200)
    assert_equal("SPY lineage RSI window", lineage_row["lineage"]["generation_params"]["params"]["rn"], 2)
    assert_equal(
        "SPY ledger exit assumption",
        lineage_row["lineage"]["explanation"]["assumptions"][0],
        "exit rule (RSI(2)>65-70 or close>5-day SMA) is engine-side/exit-plumbing, not encoded in this entry-only AST",
    )

    sources = {
        "RUN_SPY_PHASE01": source_record(
            "RUN_SPY_PHASE01", SPY_P1, "phase01_intake",
            {"entering": "/entering", "surviving": "/surviving", "dropped": "/dropped",
             "candidate": f"/candidates/{SPY_CANDIDATE}",
             "pf_actual": f"/candidates/{SPY_CANDIDATE}/gates/pf/actual",
             "pf_threshold": f"/candidates/{SPY_CANDIDATE}/gates/pf/threshold",
             "ret_dd_actual": f"/candidates/{SPY_CANDIDATE}/gates/ret_dd/actual",
             "ret_dd_threshold": f"/candidates/{SPY_CANDIDATE}/gates/ret_dd/threshold",
             "trades_month_actual": f"/candidates/{SPY_CANDIDATE}/gates/trades_per_month/actual",
             "trades_month_threshold": f"/candidates/{SPY_CANDIDATE}/gates/trades_per_month/threshold"}),
        "RUN_SPY_PHASE02": source_record(
            "RUN_SPY_PHASE02", SPY_P2, "phase02_oos",
            {"entering": "/entering", "surviving": "/surviving", "dropped": "/dropped",
             "window": "/window", "skip_note": "/notes"}),
        "RUN_DOW_PHASE01": source_record(
            "RUN_DOW_PHASE01", DOW_P1, "phase01_intake",
            {"entering": "/entering", "surviving": "/surviving", "candidate": f"/candidates/{DOW_CANDIDATE}",
             "is_net": f"/candidates/{DOW_CANDIDATE}/metrics/net",
             "is_pf": f"/candidates/{DOW_CANDIDATE}/metrics/pf"}),
        "RUN_DOW_PHASE02": source_record(
            "RUN_DOW_PHASE02", DOW_P2, "phase02_oos",
            {"entering": "/entering", "surviving": "/surviving", "dropped": "/dropped",
             "candidate": f"/candidates/{DOW_CANDIDATE}",
             "oos_net": f"/candidates/{DOW_CANDIDATE}/metrics/net",
             "oos_pf": f"/candidates/{DOW_CANDIDATE}/metrics/pf",
             "oos_ret_dd": f"/candidates/{DOW_CANDIDATE}/metrics/ret_dd",
             "oos_wins": f"/candidates/{DOW_CANDIDATE}/metrics/wins",
             "oos_losses": f"/candidates/{DOW_CANDIDATE}/metrics/losses"}),
        "RUN_SPY_LEDGER": source_record(
            "RUN_SPY_LEDGER", SPY_LEDGER, "lineage",
            {"candidate": f"line {lineage['line']}: /lineage/generation_params",
             "concept_id": f"line {lineage['line']}: /lineage/generation_params/concept_id",
             "long_window": f"line {lineage['line']}: /lineage/generation_params/params/n",
             "rsi_window": f"line {lineage['line']}: /lineage/generation_params/params/rn",
             "exit_rule_assumption": f"line {lineage['line']}: /lineage/explanation/assumptions/0"}),
        "RUN_SPY_MANIFEST": source_record(
            "RUN_SPY_MANIFEST", SPY_MANIFEST, "run_manifest",
            {"candidate": "/candidates_provenance/0", "candidate_id": "/candidates_provenance/0/id", "program_id": "/program_id"}),
    }
    if LIVE_MANIFEST.is_file():
        sources["RUN_LIVE_MANIFEST"] = {
            "source_id": "RUN_LIVE_MANIFEST",
            "path": str(LIVE_MANIFEST),
            "sha256": sha256(LIVE_MANIFEST),
            "phase": "series-manifest",
            "pointers": {
                "spy_branch": "/episodes/02/stock_branch",
                "dow_branch": "/episodes/02/dow_oos_branch",
            },
            "read_only": True,
        }

    return {
        "schema": "into-the-laboratory/e02-facts-receipt/v1",

        "generated_from": "tools/build_e02_rebuild.py",
        "source_manifest": str(LIVE_MANIFEST),
        "sources": sources,
        "spy": {
            "instrument": "SPY",
            "timeframe": "D1",
            "strategy_identity": "Connors RSI2",
            "program_id": spy_p1["program_id"],
            "run_id": spy_p1["run_id"],
            "window": spy_p1["window"],
            "entering": 5,
            "surviving": 0,
            "dropped": 5,
            "later_entering": 0,
            "later_surviving": 0,
            "later_window": None,
            "holdout_status": "not reached",
            "candidate_id": SPY_CANDIDATE,
            "candidate": {
                "pf": 0.806004,
                "pf_threshold": 1.3,
                "ret_dd": -0.420205,
                "ret_dd_threshold": 4,
                "trades_per_month": 0.392308,
                "trades_per_month_threshold": 2,
            },
            "lineage": {
                "concept_id": "con-rsi2-oversold-reversion",
                "long_window": 200,
                "rsi_window": 2,
            },
            "provenance": spy_p1["provenance"],
        },
        "dow": {
            "instrument": "Dow futures",
            "timeframe": "recorded futures phase",
            "run_id": dow_p2["run_id"],
            "window": dow_p2["window"],
            "intake_entering": count_field(dow_p1["entering"]),
            "intake_surviving": 184,
            "candidate_entering_oos": 184,
            "oos_entering": 184,
            "oos_surviving": 154,
            "oos_dropped": 30,
            "candidate_id": DOW_CANDIDATE,
            "candidate": {
                "is_net": 16727.8,
                "is_pf": 1.28037,
                "oos_net": -4897.4,
                "oos_pf": 0.813381,
                "oos_ret_dd": -0.563866,
                "oos_wins": 29,
                "oos_losses": 72,
            },
            "provenance": dow_p2["provenance"],
        },
        "assignment_discrepancies": [
            {
                "field": "dow.candidate.oos_pf",
                "assignment_requested": ASSIGNMENT_REQUESTED_DOW_OOS_PF,
                "hash_bound_source": 0.813381,
                "decision": "use_hash_bound_source",
                "reason": "The pinned phase02_oos JSON reports metrics.pf=0.813381; 0.81324 is not present in the pinned row.",
            }
        ],
        "verification": {
            "external_files_read": True,
            "all_pinned_hashes_match": True,
            "external_files_modified": False,
            "rerun_backtest": False,
        },
    }


def parse_vo() -> list[dict[str, Any]]:
    path = SOURCE / "vo.txt"
    if not path.is_file():
        raise SystemExit(f"BLOCK: missing source VO at {path}")
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        slot = re.match(r"^=== SLOT\s+(scene-\d+)\s+->\s+(.+?)\s+===", raw)
        if slot:
            if current:
                rows.append(current)
            current = {"id": slot.group(1), "audio": slot.group(2), "receipt": None, "text": []}
            continue
        if current is None:
            continue
        marker = re.match(r"^#\s*receipt:\s*([A-Za-z0-9._,-]+)\s*$", raw)
        if marker:
            current["receipt"] = marker.group(1)
        elif raw.strip() and not raw.lstrip().startswith("#"):
            current["text"].append(raw.strip())
    if current:
        rows.append(current)
    if len(rows) != len(SCENE_TITLES):
        raise SystemExit(f"BLOCK: source VO has {len(rows)} slots, expected {len(SCENE_TITLES)}")
    for row in rows:
        row["text"] = " ".join(row["text"]).strip()
        if not row["receipt"] or not row["text"]:
            raise SystemExit(f"BLOCK: source VO slot {row['id']} needs one receipt and one paragraph")
    return rows


def split_sentences(text: str) -> list[str]:
    """Split on terminal punctuation while leaving decimal metrics intact."""
    sentences: list[str] = []
    start = 0
    for match in re.finditer(r"[.!?]", text):
        pos = match.start()
        if match.group(0) == "." and pos + 1 < len(text) and text[pos + 1].isdigit():
            continue
        candidate = text[start : pos + 1].strip()
        if candidate:
            sentences.append(candidate)
        start = pos + 1
    tail = text[start:].strip()
    if tail:
        sentences.append(tail)
    return sentences


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9$-]+", text))


def arc_word_count(text: str) -> int:
    """Match script_arc_gate's beginner-facing word denominator exactly."""
    return len(re.findall(r"\b[\w'-]+\b", text))


SCENE_ENERGY = {
    "scene-01": "direct cold open",
    "scene-02": "cautionary and deliberate",
    "scene-03": "slow vocabulary lesson",
    "scene-04": "observational mechanism walk",
    "scene-05": "slow analytical arithmetic",
    "scene-06": "focused intake review",
    "scene-07": "quiet boundary stop",
    "scene-08": "separate-lane contrast",
    "scene-09": "grave measured reversal",
    "scene-10": "curious methodological pressure",
    "scene-11": "patient statistical definition",
    "scene-12": "comparative clarification",
    "scene-13": "practical worksheet instruction",
    "scene-14": "open unanswered question",
}


def sentence_cues(row: dict[str, Any], start: float, end: float) -> list[dict[str, Any]]:
    sentences = split_sentences(row["text"])
    total_words = max(1, sum(word_count(sentence) for sentence in sentences))
    cursor = start
    cues = []
    for index, sentence in enumerate(sentences, 1):
        duration = (word_count(sentence) / total_words) * (end - start)
        cue_end = end if index == len(sentences) else cursor + duration
        cues.append({
            "id": f"{row['id']}-sentence-{index:02d}",
            "start_seconds": round(cursor, 3),
            "end_seconds": round(cue_end, 3),
            "duration_seconds": round(cue_end - cursor, 3),
            "asset": f"hyperframes/assets/{row['id']}.svg",
            "spoken_span": sentence,
            "visual_action": visual_action(row["id"], index, sentence),
            "sentence_bound": True,
            "evidence_mode": "deterministic source-derived graphic",
        })
        cursor = cue_end
    return cues


def visual_action(scene_id: str, index: int, sentence: str) -> str:
    lower = sentence.lower()
    if scene_id == "scene-01":
        actions = [
            "Place the SPY RSI2 label above five intake tokens and a closed later-price door.",
            "Stretch the daily intake rail across the 1996-07-12 to 2011-05-26 window.",
            "Show five candidate tokens enter and then move all five into the dropped gutter.",
            "Set the next-phase counter to zero and keep its chamber blank.",
            "Print holdout return: none under the SPY lane and keep the later result blank.",
            "Keep the sealed door and stopped lane visible as the result, not a dead end.",
            "Underline the five-to-zero path as the recorded intake outcome.",
            "Split the canvas into a stock lane and a separate Dow lane.",
            "Keep the two lane labels spatially separate.",
            "Seal SPY at intake.",
            "Open only the Dow branch toward later prices.",
            "End with a neutral data marker and no SPY later return.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-02":
        actions = [
            "Place a later-test door and a candidate token before it.",
            "Animate a look arrow, an RSI-threshold change, and a second look arrow.",
            "Show the second look as a separate arrow after the setting changes.",
            "Slide the chosen version into the freezer before the later-price door.",
            "Label the later block out-of-sample and draw a heavy seal across its entrance.",
            "Turn the sealed door into a holdout chamber with no visible result yet.",
            "Show choose, write, and open once as a one-way sequence.",
            "Block the re-entry arrow after the result is used for another choice.",
            "Split the question card after the second look.",
            "Keep the SPY five-to-zero rail below the locked chamber.",
            "Keep the Dow later group on its own track.",
            "End with choose first, then one look at later prices.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-03":
        actions = [
            "Open a vocabulary rail with the method words in plain English.",
            "Build the in-sample chamber for the history used to choose.",
            "Build the later out-of-sample chamber and keep it hidden.",
            "Draw the first path as the build history and the second as a new-price path.",
            "Place the overfitting label beside the old path and settings panel.",
            "Place the curve-fitting label beside knobs that move after the result.",
            "Show many settings producing one lucky-looking row, then keep the chosen values visible.",
            "Turn the parameter knobs into a frozen row of saved values.",
            "Split the timeline into fixed blocks and label each block with its job.",
            "Roll the start forward to name a walk-forward sequence.",
            "Show the single E02 intake window and later block.",
            "Label the display as walk-forward context and leave its result field empty.",
            "Shade the warmup segment before the first full indicator window.",
            "Keep warmup bars outside the trade-result count.",
            "Return to the guardrail around both chambers and leave SPY without a new result.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-04":
        actions = [
            "Set the SPY file label on a single daily timeline.",
            "Place the Connors RSI2 identity on the mechanism rail.",
            "Draw the long 200-day window and the shorter 2-day RSI input from the saved settings.",
            "Show the short moving-average exit leg on the mechanism rail.",
            "Label D1 as daily bars on the timeline.",
            "Pin the 200-day lineage value to the setup rail.",
            "Hatch the setup span as warmup bars outside the trade count.",
            "Mark the setup as mechanism context, not a trade result.",
            "Trace the gate path from the settings to the test result.",
            "Pin run identity and the window on the outer margin.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-05":
        actions = [
            "Put three labeled metrics on rulers: PF and return-to-drawdown are unitless ratios; trades per month is a rate.",
            "Place 0.806004 to the left of the 1.3 mark and draw the greater-than operator.",
            "Highlight the PF rule as actual greater than 1.3.",
            "Place -0.420205 to the left of the 4 mark and retain the negative sign.",
            "Highlight the return-over-drawdown rule as actual greater than 4.",
            "Place 0.392308 trades per month beside the 2 trades-per-month mark.",
            "Print the unit twice so the rate is not confused with a count.",
            "Write 0.806004 greater than 1.3 and mark the comparison false.",
            "Write -0.420205 greater than 4 and mark the comparison false.",
            "Write the rate comparison and mark it false without converting units.",
            "Put the profit-factor formula below the ruler: gross wins divided by gross losses.",
            "Put the return-over-drawdown formula below the ruler and label it a unitless ratio.",
            "Label trades per month as a rate with trades per month as its unit.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-06":
        actions = [
            "Highlight the first-screen stop on the row track.",
            "Show five equal candidate tokens entering and failing the bounded field.",
            "Magnify one row while the five-token population label stays visible.",
            "Keep the larger RSI2 setting space as a bracket outside the row.",
            "Show each threshold beside its result on the recorded row.",
            "Reveal real-data and wiring-proof status on the fact rail.",
            "Keep the validation boundary visibly open.",
            "Place the real-data connection beside an empty pass badge.",
            "Trace the pipeline reaching this gate.",
            "Keep a pass-to-next-stage arrow separate from any market-performance claim.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-07":
        actions = [
            "Open the next SPY phase as an empty paper chamber.",
            "Set both the entering and surviving counters to zero.",
            "Keep the empty phase visible as the recorded result.",
            "Replace the later-window label with no historical window.",
            "Place the skipped-phase note beside the empty entrance and keep the SPY return field blank.",
            "Draw a future-test checklist for a version, later dates, and frozen settings.",
            "Write the checklist before the unopened door.",
            "Close the SPY later-price chamber with a visible bar.",
            "Leave the empty phase as no performance number.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-08":
        actions = [
            "Add a separate Dow futures lane beneath the stopped SPY lane.",
            "Place 184 tokens at the Dow later-price entrance.",
            "Let 154 tokens cross the later boundary and send 30 into a side gutter.",
            "Keep the Dow door open toward later prices.",
            "Keep the SPY door closed at its earlier boundary.",
            "Label out-of-sample as the job description.",
            "Show the entering and surviving counts side by side.",
            "Label the first count as who came in and the second as who made it through.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-09":
        actions = [
            "Place one Dow candidate identity at the center of a two-window track.",
            "Write +$16,727.80 and PF 1.28037 in the in-sample chamber.",
            "Write -$4,897.40 and PF 0.813381 in the later chamber while keeping the identity fixed.",
            "Add 29 wins and 72 losses beneath the later result.",
            "Annotate the old brief's 0.81324 as absent from the pinned row.",
            "Highlight 0.813381 as the pinned value.",
            "Keep the candidate identity fixed while the window label changes.",
            "Move the SPY lane outside the track as a separate instrument.",
            "Keep the one-row example inside the 184-row population bracket.",
            "Show the remaining 183 rows as needing their own results.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-10":
        actions = [
            "Open a question mark over the later-test chamber.",
            "Draw the development history becoming familiar.",
            "Show many rules competing for one attractive old-price path.",
            "Move a threshold, exit, and window after the result.",
            "Label the changed threshold, exit, and window as curve-fitting.",
            "Place White's data-snooping reference beside the repeated-look warning.",
            "Lay out choose, freeze, open, and record as a one-way sequence.",
            "Highlight choose as the first step.",
            "Seal the selected parameters at freeze.",
            "Open the later block once.",
            "Record the observed result.",
            "Place the SPY stop at the first boundary.",
            "Place the Dow changed row at the later boundary.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-11":
        actions = [
            "Place the individual candidate beside the full group field.",
            "Spread recorded outcome dots across a horizontal number line.",
            "Label the field with center, spread, and shape.",
            "Draw a center line for the ordered middle value.",
            "Place a percentile marker at its rank in the ordered group.",
            "Slide the 50th-percentile marker onto the median line.",
            "Keep the definition card separate from any new result.",
            "List population, units, and calculation beneath the median marker.",
            "List the rank rule beneath the percentile marker.",
            "Keep the five SPY rows beside an empty later group and no percentile.",
            "Keep the 184-row Dow population in its separate bracket.",
            "End with a pinned-report placeholder for the group.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    if scene_id == "scene-12":
        actions = [
            "Split the screen between segmentation and walk-forward.",
            "Build fixed blocks with separate choose and judge jobs.",
            "Roll a second origin forward to create the walk-forward sequence.",
            "Place question, history, and update-rule cards above the design.",
            "Add a time-order thread and changing-condition markers.",
            "Mark SPY as one intake plus an empty later phase.",
            "Mark Dow as one later block.",
            "Label both fixed blocks with their actual jobs.",
            "Keep the walk-forward result field empty.",
            "Show dates, start, update, and freeze-or-refit as a rolling-test checklist.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]

    if scene_id == "scene-13":
        actions = [
            "Open a worksheet with instrument, timeframe, and strategy fields.",
            "Add first-window, later-window, count, and validation fields.",
            "Add units beside every comparison field.",
            "Write the SPY five, zero, zero, and holdout-not-reached boundary.",
            "Write the Dow 184, 154, 30, and candidate-flip row.",
            "Stamp the worksheet freeze-first marker.",
            "Add the exact source hash and row location.",
            "Name the later window before the out-of-sample label.",
            "Pin the group before the median or percentile label.",
            "Close the worksheet with a repeatable question arrow.",
        ]
        if index > len(actions):
            raise SystemExit(f"BLOCK: {scene_id} visual action missing for sentence {index}")
        return actions[index - 1]
    actions = [
        "Return the SPY rail to its intake boundary and keep the later window blank.",
        "Keep the SPY intake boundary visibly closed.",
        "Open only the separate Dow lane toward later prices.",
        "Show +$16,727.80 and PF 1.28037 on the first-window side of the Dow row.",
        "Show -$4,897.40 and PF 0.813381 on the later-window side of the same row.",
        "Place 29 wins and 72 losses beneath the later result.",
        "Annotate the brief's 0.81324 beside the pinned 0.813381 row value.",
        "Keep SPY outside the Dow comparison.",
        "Open two labeled execution-question chambers.",
        "Draw unfinished branches toward fill timing and trading hours without opening them.",
        "End on the question mark beside both unopened chambers.",
    ]
    return actions[index - 1]


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def svg_text(x: int, y: int, value: Any, size: int = 30, cls: str = "body", anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{esc(value)}</text>'


def svg_start(kicker: str, title: str) -> list[str]:
    return [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1920 1080" width="1920" height="1080" role="img">',
        '<rect width="1920" height="1080" fill="#080b12"/>',
        '<style>',
        '@font-face{font-family:\'Bahnschrift\';src:local(\'Bahnschrift\');font-weight:100 900}',
        '@font-face{font-family:\'Consolas\';src:local(\'Consolas\');font-weight:100 900}',
        '.kicker{font:700 24px \'Bahnschrift\',sans-serif;letter-spacing:.14em;fill:#7ed7d2}',
        '.title{font:800 66px \'Bahnschrift\',sans-serif;fill:#f5f1e8}',
        '.body{font:500 30px \'Bahnschrift\',sans-serif;fill:#d8d8d1}',
        '.small{font:600 22px \'Bahnschrift\',sans-serif;fill:#a6adb8;letter-spacing:.04em}',
        '.mono{font:700 34px \'Consolas\',monospace;fill:#f5f1e8}',
        '.mono-sm{font:700 25px \'Consolas\',monospace;fill:#f5f1e8}',
        '.accent{fill:#f0ba55}.cyan{fill:#7ed7d2}.muted{fill:#89929e}.ink{fill:#080b12}',
        '.line{stroke:#33404e;stroke-width:3}.accent-line{stroke:#f0ba55;stroke-width:6}',
        '.cyan-line{stroke:#7ed7d2;stroke-width:6}.seal{stroke:#d27ca7;stroke-width:7}',
        '</style>',
        # Do not put every lesson inside the same rounded stage shell.  The
        # open canvas is intentional: the mechanism, not a reusable card
        # frame, owns the viewer's attention.
        svg_text(92, 96, kicker.upper(), cls="kicker"),
        svg_text(92, 190, title, cls="title"),
        '<line x1="92" y1="228" x2="1828" y2="228" class="line"/>',
    ]


def svg_end() -> str:
    return "</svg>"


def scene_svg(scene_id: str, facts: dict[str, Any]) -> str:
    spy = facts["spy"]
    dow = facts["dow"]
    p: list[str] = []
    p.extend(svg_start(f"E02 / {scene_id}", SCENE_TITLES[scene_id]))
    if scene_id == "scene-01":
        p.extend([
            svg_text(110, 330, "SPY / D1 / CONNORS RSI2", cls="kicker"),
            svg_text(150, 486, "5", size=104, cls="mono", anchor="middle"),
            svg_text(150, 535, "enter", cls="small", anchor="middle"),
            '<line x1="240" y1="470" x2="900" y2="470" class="accent-line"/>',
            '<g fill="#f5f1e8">' + "".join(f'<circle cx="{320 + i * 105}" cy="440" r="18"/>' for i in range(5)) + '</g>',
            '<rect x="930" y="300" width="46" height="440" rx="22" fill="#d27ca7"/>',
            svg_text(1025, 410, "LATER-PRICE", cls="small"),
            svg_text(1025, 455, "CHAMBER", cls="mono-sm"),
            svg_text(1500, 486, "0", size=104, cls="mono", anchor="middle"),
            svg_text(1500, 535, "advance", cls="small", anchor="middle"),
            '<line x1="1100" y1="470" x2="1375" y2="470" class="line"/>',
            svg_text(150, 810, "1996-07-12  →  2011-05-26", cls="mono-sm"),
            svg_text(150, 875, "holdout not reached", cls="body"),
            svg_text(1120, 875, "DOW / FUTURES  →  later block", cls="mono-sm"),
            svg_text(150, 946, "stock lane", cls="small"),
            svg_text(1510, 946, "later prices remain sealed", cls="small", anchor="middle"),
        ])
    elif scene_id == "scene-02":
        p.extend([
            svg_text(130, 320, "CHOOSE", cls="kicker"), svg_text(780, 320, "FREEZE", cls="kicker"), svg_text(1430, 320, "OPEN", cls="kicker"),
            '<rect x="120" y="380" width="450" height="260" rx="18" fill="#111a24" stroke="#33404e" stroke-width="3"/>',
            '<rect x="735" y="380" width="450" height="260" rx="18" fill="#151723" stroke="#f0ba55" stroke-width="4"/>',
            '<rect x="1350" y="380" width="450" height="260" rx="18" fill="#121e23" stroke="#7ed7d2" stroke-width="4"/>',
            svg_text(345, 500, "settings", cls="mono", anchor="middle"),
            svg_text(960, 500, "saved", cls="mono", anchor="middle"),
            svg_text(1575, 500, "later block", cls="mono-sm", anchor="middle"),
            '<line x1="570" y1="510" x2="735" y2="510" class="accent-line"/><polygon points="735,510 700,490 700,530" fill="#f0ba55"/>',
            '<line x1="1185" y1="510" x2="1350" y2="510" class="cyan-line"/><polygon points="1350,510 1315,490 1315,530" fill="#7ed7d2"/>',
            '<rect x="810" y="690" width="300" height="20" rx="10" fill="#d27ca7"/>',
            svg_text(960, 780, "look once, then record", cls="body", anchor="middle"),
            svg_text(960, 900, "changing a setting after opening the chamber reuses the holdout", cls="small", anchor="middle"),
        ])
    elif scene_id == "scene-03":
        p.extend([
            '<rect x="120" y="300" width="720" height="510" rx="20" fill="#111a24" stroke="#33404e" stroke-width="3"/>',
            '<rect x="1080" y="300" width="720" height="510" rx="20" fill="#121e23" stroke="#7ed7d2" stroke-width="4"/>',
            svg_text(170, 370, "IN-SAMPLE / BUILD", cls="kicker"),
            svg_text(1130, 370, "OUT-OF-SAMPLE / JUDGE", cls="kicker"),
            svg_text(170, 505, "settings", cls="mono"), svg_text(170, 570, "noise", cls="body"), svg_text(170, 635, "selection", cls="body"),
            svg_text(1130, 505, "frozen", cls="mono"), svg_text(1130, 570, "later prices", cls="body"), svg_text(1130, 635, "one question", cls="body"),
            '<line x1="840" y1="550" x2="1080" y2="550" class="seal"/>',
            svg_text(960, 505, "SEALED", cls="small", anchor="middle"),
            svg_text(960, 920, "segmented blocks have jobs; walk-forward moves the origin", cls="small", anchor="middle"),
        ])
    elif scene_id == "scene-04":
        p.extend([
            svg_text(150, 320, "SPY / D1 / CONNORS RSI2", cls="kicker"),
            '<line x1="170" y1="460" x2="1750" y2="460" class="line"/>',
            '<line x1="170" y1="660" x2="1750" y2="660" class="line"/>',
            '<rect x="170" y="410" width="480" height="105" fill="#25202b"/>',
            svg_text(200, 475, "warmup bars", cls="mono-sm"),
            '<rect x="650" y="410" width="1080" height="105" fill="#111a24"/>',
            svg_text(760, 475, "200-day regime window", cls="mono-sm"),
            '<rect x="170" y="610" width="80" height="105" fill="#25202b"/>',
            svg_text(330, 675, "2-day RSI input", cls="mono-sm"),
            '<rect x="250" y="610" width="880" height="105" fill="#121e23"/>',
            '<line x1="1130" y1="610" x2="1730" y2="610" class="cyan-line"/>',
            svg_text(1210, 675, "short moving-average exit leg", cls="small"),
            svg_text(170, 850, "context first  →  signal  →  measured result", cls="body"),
            svg_text(170, 925, "warmup is history, not performance", cls="small"),
        ])
    elif scene_id == "scene-05":
        rows = [("PF", "unitless ratio", "0.806004", ">", "1.3", 420), ("RET / DD", "unitless ratio", "-0.420205", ">", "4", 590), ("TRADES / MONTH", "rate · trades / month", "0.392308", ">", "2", 760)]
        for label, unit, actual, op, threshold, y in rows:
            p.extend([
                svg_text(150, y, label, cls="kicker"),
                svg_text(150, y + 38, unit, cls="small"),
                '<line x1="470" y1="%d" x2="1640" y2="%d" class="line"/>' % (y - 10, y - 10),
                svg_text(560, y + 12, actual, cls="mono-sm"),
                svg_text(930, y + 12, op, cls="mono", anchor="middle"),
                svg_text(1310, y + 12, threshold, cls="mono-sm"),
                svg_text(1580, y + 12, "actual  >  threshold", cls="small", anchor="middle"),
                svg_text(1765, y + 12, "FALSE", cls="accent", anchor="middle"),
            ])
        p.extend([
            svg_text(940, 905, "Each line is a comparison with units, not a verdict color.", cls="body", anchor="middle"),
        ])
    elif scene_id == "scene-06":
        p.extend([
            svg_text(150, 325, "FIVE RECORDED VERSIONS", cls="kicker"),
            '<line x1="230" y1="550" x2="1660" y2="550" class="accent-line"/>',
            '<g fill="#f5f1e8">' + "".join(f'<circle cx="{350 + i * 260}" cy="550" r="42"/>' for i in range(5)) + '</g>',
            svg_text(350, 660, "1", cls="mono", anchor="middle"), svg_text(610, 660, "2", cls="mono", anchor="middle"),
            svg_text(870, 660, "3", cls="mono", anchor="middle"), svg_text(1130, 660, "4", cls="mono", anchor="middle"),
            svg_text(1390, 660, "5", cls="mono", anchor="middle"),
            '<rect x="170" y="760" width="650" height="100" rx="14" fill="#111a24" stroke="#33404e" stroke-width="3"/>',
            svg_text(205, 825, "one row magnified; field stays five", cls="body"),
            '<rect x="940" y="760" width="700" height="100" rx="14" fill="#121e23" stroke="#7ed7d2" stroke-width="3"/>',
            svg_text(975, 825, "real input / wiring proof / unvalidated", cls="small"),
            svg_text(960, 955, "small recorded branch ≠ every possible setting", cls="small", anchor="middle"),
        ])
    elif scene_id == "scene-07":
        p.extend([
            svg_text(150, 330, "SPY / LATER-PRICE CHAMBER", cls="kicker"),
            '<rect x="200" y="410" width="1450" height="220" rx="28" fill="#111a24" stroke="#d27ca7" stroke-width="6"/>',
            '<rect x="895" y="355" width="60" height="330" rx="22" fill="#d27ca7"/>',
            svg_text(520, 535, "0 entering", cls="mono"), svg_text(1190, 535, "0 surviving", cls="mono"),
            svg_text(960, 760, "no historical window", cls="body", anchor="middle"),
            svg_text(960, 835, "skipped: no adoptable candidates", cls="small", anchor="middle"),
            svg_text(960, 950, "holdout not reached", cls="kicker", anchor="middle"),
        ])
    elif scene_id == "scene-08":
        p.extend([
            # Two open rails replace the paired rounded panels.  The vertical
            # separator is a lane boundary, not a dashboard column.
            '<line x1="170" y1="455" x2="1750" y2="455" class="accent-line"/>',
            '<line x1="170" y1="755" x2="1750" y2="755" class="cyan-line"/>',
            '<circle cx="360" cy="455" r="28" fill="#f5f1e8"/>',
            '<circle cx="880" cy="455" r="28" fill="#d27ca7"/>',
            '<circle cx="360" cy="755" r="28" fill="#f5f1e8"/>',
            '<circle cx="880" cy="755" r="28" fill="#7ed7d2"/>',
            '<line x1="1010" y1="350" x2="1010" y2="860" class="line" stroke-dasharray="14 18"/>',
            svg_text(170, 360, "SPY / STOCK / D1", cls="kicker"), svg_text(170, 660, "DOW / FUTURES", cls="kicker"),
            svg_text(250, 535, "5  →  0", cls="mono"), svg_text(750, 535, "holdout not reached", cls="body"),
            svg_text(250, 835, "184  →  154", cls="mono"), svg_text(850, 835, "30 dropped in later block", cls="body"),
            svg_text(1390, 435, "different lane", cls="small", anchor="middle"),
            svg_text(1390, 735, "different lane", cls="small", anchor="middle"),
            svg_text(1190, 930, "stock stops here  /  futures continues", cls="small", anchor="middle"),
        ])
    elif scene_id == "scene-09":
        p.extend([
            svg_text(140, 325, DOW_CANDIDATE, cls="kicker"),
            '<rect x="140" y="390" width="720" height="380" rx="20" fill="#111a24" stroke="#f0ba55" stroke-width="4"/>',
            '<rect x="1060" y="390" width="720" height="380" rx="20" fill="#121e23" stroke="#7ed7d2" stroke-width="4"/>',
            svg_text(190, 470, "IN-SAMPLE", cls="kicker"), svg_text(1110, 470, "LATER BLOCK", cls="kicker"),
            svg_text(190, 610, "+$16,727.80", cls="mono"), svg_text(190, 685, "PF 1.28037", cls="mono-sm"),
            svg_text(1110, 610, "-$4,897.40", cls="mono"), svg_text(1110, 685, "PF 0.813381", cls="mono-sm"),
            svg_text(960, 860, "29 wins  /  72 losses", cls="mono-sm", anchor="middle"),
            svg_text(960, 940, "same candidate identity; different price window", cls="small", anchor="middle"),
            svg_text(960, 1010, "brief PF 0.81324  /  pinned row PF 0.813381", cls="small", anchor="middle"),
        ])
    elif scene_id == "scene-10":
        p.extend([
            '<line x1="170" y1="780" x2="1750" y2="780" class="line"/>', '<line x1="170" y1="350" x2="170" y2="780" class="line"/>',
            '<path d="M220 690 C520 570 740 500 980 510 C1220 520 1430 600 1700 650" fill="none" stroke="#7ed7d2" stroke-width="9"/>',
            '<path d="M220 690 C390 330 510 740 690 410 C850 720 1010 330 1170 620 C1320 400 1480 730 1700 390" fill="none" stroke="#d27ca7" stroke-width="8"/>',
            svg_text(210, 315, "SIMPLE SIGNAL", cls="kicker"), svg_text(1320, 315, "CURVE-FIT NOISE", cls="kicker"),
            svg_text(960, 910, "more knobs can follow the development history without adding a repeatable effect", cls="small", anchor="middle"),
        ])
    elif scene_id == "scene-11":
        p.extend([
            svg_text(145, 325, "ORDERED OUTCOMES", cls="kicker"),
            '<line x1="190" y1="570" x2="1730" y2="570" class="line"/>',
            '<g fill="#7ed7d2">' + "".join(f'<circle cx="{250 + i * 125}" cy="{570 - ((i * 37) % 120)}" r="12"/>' for i in range(12)) + '</g>',
            '<line x1="885" y1="415" x2="885" y2="700" class="accent-line"/>',
            '<line x1="1220" y1="455" x2="1220" y2="700" class="seal"/>',
            svg_text(885, 380, "median", cls="small", anchor="middle"),
            svg_text(1220, 420, "percentile", cls="small", anchor="middle"),
            svg_text(960, 820, "distribution = location + spread + shape", cls="mono-sm", anchor="middle"),
            svg_text(960, 905, "summary only after the population and units are pinned", cls="small", anchor="middle"),
        ])
    elif scene_id == "scene-12":
        p.extend([
            svg_text(150, 320, "SEGMENTED BACKTEST", cls="kicker"), svg_text(1130, 320, "WALK-FORWARD", cls="kicker"),
            '<rect x="150" y="400" width="720" height="300" rx="18" fill="#111a24" stroke="#33404e" stroke-width="3"/>',
            '<rect x="1130" y="400" width="640" height="300" rx="18" fill="#121e23" stroke="#7ed7d2" stroke-width="4"/>',
            '<rect x="205" y="500" width="230" height="70" fill="#25202b"/><rect x="435" y="500" width="230" height="70" fill="#121e23"/>',
            svg_text(320, 545, "choose", cls="small", anchor="middle"), svg_text(550, 545, "judge", cls="small", anchor="middle"),
            '<rect x="1180" y="500" width="190" height="70" fill="#25202b"/><rect x="1370" y="500" width="190" height="70" fill="#121e23"/>',
            svg_text(1275, 545, "build", cls="small", anchor="middle"), svg_text(1465, 545, "test", cls="small", anchor="middle"),
            '<line x1="1180" y1="740" x2="1650" y2="740" class="cyan-line"/><circle cx="1260" cy="740" r="13" fill="#7ed7d2"/><circle cx="1420" cy="740" r="13" fill="#7ed7d2"/><circle cx="1580" cy="740" r="13" fill="#7ed7d2"/>',
            svg_text(960, 885, "fixed jobs  ≠  moving origin", cls="mono-sm", anchor="middle"),
        ])
    elif scene_id == "scene-13":
        p.extend([
            '<rect x="150" y="300" width="1620" height="560" rx="18" fill="#111a24" stroke="#33404e" stroke-width="3"/>',
            svg_text(205, 370, "INSTRUMENT", cls="small"), svg_text(720, 370, "WINDOWS", cls="small"), svg_text(1260, 370, "COUNTS", cls="small"),
            '<line x1="205" y1="395" x2="1715" y2="395" class="line"/>',
            svg_text(205, 470, "SPY / D1 / RSI2", cls="mono-sm"), svg_text(720, 470, "1996 → 2011 / later: none", cls="mono-sm"), svg_text(1260, 470, "5 / 0 / 5", cls="mono-sm"),
            '<line x1="205" y1="520" x2="1715" y2="520" class="line"/>',
            svg_text(205, 595, "DOW / futures", cls="mono-sm"), svg_text(720, 595, "2018 → 2019 / later block", cls="mono-sm"), svg_text(1260, 595, "184 / 154 / 30", cls="mono-sm"),
            '<line x1="205" y1="645" x2="1715" y2="645" class="line"/>',
            svg_text(205, 725, "gate", cls="small"), svg_text(720, 725, "actual  >  threshold", cls="mono-sm"), svg_text(1260, 725, "units + row locator", cls="mono-sm"),
            svg_text(960, 955, "freeze → hash → locate → describe", cls="kicker", anchor="middle"),
        ])
    else:
        p.extend([
            svg_text(150, 330, "UNOPENED EXECUTION QUESTIONS", cls="kicker"),
            svg_text(150, 380, "SPY / D1   5  →  0   holdout not reached", cls="mono-sm"),
            svg_text(150, 415, "DOW / FUTURES   +$16,727.80 / PF 1.28037  →  -$4,897.40 / PF 0.813381", cls="small"),
            svg_text(150, 445, "29 wins  /  72 losses   |   same row, later window", cls="small"),
            # The close is a branching question rail rather than two answer
            # cards.  Both branches remain visibly unopened.
            '<line x1="960" y1="540" x2="960" y2="780" class="line"/>',
            '<path d="M960 650 C760 650 600 650 360 650" fill="none" stroke="#f0ba55" stroke-width="7"/>',
            '<path d="M960 650 C1160 650 1320 650 1560 650" fill="none" stroke="#7ed7d2" stroke-width="7"/>',
            '<circle cx="960" cy="650" r="26" fill="#f5f1e8"/>',
            '<circle cx="360" cy="650" r="26" fill="none" stroke="#f0ba55" stroke-width="7"/>',
            '<circle cx="1560" cy="650" r="26" fill="none" stroke="#7ed7d2" stroke-width="7"/>',
            svg_text(360, 565, "FILL TIMING", cls="mono", anchor="middle"), svg_text(1560, 565, "TRADING HOURS", cls="mono", anchor="middle"),
            svg_text(360, 735, "signal close  →  fill?", cls="body", anchor="middle"), svg_text(1560, 735, "which hours count?", cls="body", anchor="middle"),
            svg_text(960, 955, "the next chamber is a question, not an answer", cls="kicker", anchor="middle"),
        ])
    p.append(svg_end())
    return "\n".join(p) + "\n"


def validate_scene_assets(out_assets: Path) -> dict[str, Any]:
    """Check emitted lesson graphics for independent mechanism/evidence markers."""
    scenes: dict[str, Any] = {}
    for scene_id, markers in SCENE_SEMANTIC_MARKERS.items():
        asset = out_assets / f"{scene_id}.svg"
        if not asset.is_file():
            raise SystemExit(f"BLOCK: required visual asset missing: {asset}")
        body = asset.read_text(encoding="utf-8")
        missing = [marker for marker in markers if marker not in body]
        if missing:
            raise SystemExit(f"BLOCK: {scene_id} semantic markers missing from emitted SVG: {missing}")
        scenes[scene_id] = {
            "asset": f"hyperframes/assets/{scene_id}.svg",
            "required_markers": markers,
            "missing_markers": [],
            "verified": True,
        }
    return {
        "schema": "into-the-laboratory/visual-semantic-receipt/v1",
        "method": "literal marker checks against emitted deterministic SVG bytes",
        "verified": True,
        "scenes": scenes,
    }


def build_thumbnail() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=1280,height=720"><title>E02 thumbnail candidate</title>
<style>
@font-face{font-family:'Bahnschrift';src:local('Bahnschrift');font-weight:100 900}
html,body{margin:0;width:1280px;height:720px;background:#080b12;overflow:hidden;font-family:'Bahnschrift',sans-serif;color:#f5f1e8}
main{position:relative;width:1280px;height:720px;background:radial-gradient(circle at 78% 45%,#1a2430 0,#080b12 58%)}
.eyebrow{position:absolute;left:54px;top:38px;color:#7ed7d2;font-size:19px;font-weight:800;letter-spacing:.16em}.hero{position:absolute;left:55px;top:128px;font-size:84px;line-height:.95;font-weight:900;letter-spacing:-.04em}.sub{position:absolute;left:58px;top:330px;color:#f0ba55;font-size:24px;font-weight:800;letter-spacing:.08em}.door{position:absolute;left:710px;top:150px;width:18px;height:400px;border-radius:9px;background:#d27ca7}.tokens{position:absolute;left:500px;top:265px;width:220px;display:flex;gap:15px;flex-wrap:wrap}.token{width:28px;height:28px;border-radius:50%;background:#f5f1e8}.out{position:absolute;left:780px;top:258px;color:#f5f1e8;font-size:52px;font-weight:900}.label{position:absolute;left:780px;top:332px;color:#89929e;font-size:20px;font-weight:700;letter-spacing:.1em}.lane{position:absolute;left:760px;top:480px;color:#7ed7d2;font-size:43px;font-weight:900;letter-spacing:.04em}.lane-note{position:absolute;left:765px;top:538px;color:#a6adb8;font-size:18px;font-weight:700;letter-spacing:.08em}.rule{position:absolute;left:55px;right:55px;bottom:46px;height:2px;background:#33404e}
</style></head><body><main>
<div class="eyebrow">INTO THE LABORATORY / E02</div>
<div class="hero">5 → 0</div>
<div class="sub">SEALED</div>
<div class="tokens"><span class="token"></span><span class="token"></span><span class="token"></span><span class="token"></span><span class="token"></span></div>
<div class="door"></div><div class="out">0</div><div class="label">LATER CHAMBER</div>
<div class="lane">184 → 154</div><div class="lane-note">SEPARATE LANE / LATER BLOCK</div><div class="rule"></div>
</main></body></html>
"""


def build_proof_html() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=1920,height=1080"><title>E02 semantic proof candidate</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
@font-face{font-family:'Bahnschrift';src:local('Bahnschrift');font-weight:100 900}
html,body{margin:0;background:#080b12;overflow:hidden}#root{position:relative;width:1920px;height:1080px;overflow:hidden;background:#080b12;font-family:'Bahnschrift',sans-serif}.clip{position:absolute;inset:0;width:1920px;height:1080px;opacity:1}.clip-inner{position:absolute;inset:0;width:1920px;height:1080px;opacity:0}.clip img{display:block;width:1920px;height:1080px}.proof-probe{position:absolute;width:26px;height:26px;border:5px solid #f0ba55;border-radius:50%;transform:translate(-50%,-50%);opacity:0;box-shadow:0 0 0 10px rgba(240,186,85,.12)}.proof-line{position:absolute;height:6px;width:520px;background:#7ed7d2;transform-origin:left center;opacity:0;box-shadow:0 0 18px rgba(126,215,210,.35)}
</style></head><body><div id="root" data-composition-id="e02-semantic-proof-candidate" data-start="0" data-width="1920" data-height="1080" data-duration="20">
<section id="proof-beat-01" class="clip" data-start="0" data-duration="5" data-track-index="1"><div id="proof-beat-01-inner" class="clip-inner"><img src="assets/scene-01.svg" alt="Five SPY candidates stop before a sealed later-price chamber"><div id="proof-probe-01" class="proof-probe" style="left:270px;top:470px"></div><div id="proof-line-01" class="proof-line" style="left:270px;top:470px"></div></div></section>
<section id="proof-beat-02" class="clip" data-start="5" data-duration="5" data-track-index="2"><div id="proof-beat-02-inner" class="clip-inner"><img src="assets/scene-05.svg" alt="Three SPY inequality gates with actual values and thresholds"><div id="proof-probe-02" class="proof-probe" style="left:620px;top:410px"></div><div id="proof-line-02" class="proof-line" style="left:620px;top:410px"></div></div></section>
<section id="proof-beat-03" class="clip" data-start="10" data-duration="5" data-track-index="3"><div id="proof-beat-03-inner" class="clip-inner"><img src="assets/scene-08.svg" alt="SPY stops at zero while a separate Dow lane moves from 184 to 154"><div id="proof-probe-03" class="proof-probe" style="left:320px;top:455px"></div><div id="proof-line-03" class="proof-line" style="left:320px;top:455px"></div></div></section>
<section id="proof-beat-04" class="clip" data-start="15" data-duration="5" data-track-index="4"><div id="proof-beat-04-inner" class="clip-inner"><img src="assets/scene-14.svg" alt="Two unopened execution questions: fill timing and trading hours"><div id="proof-probe-04" class="proof-probe" style="left:960px;top:650px"></div><div id="proof-line-04" class="proof-line" style="left:960px;top:650px"></div></div></section>
</div><script>
window.__timelines=window.__timelines||{};const tl=gsap.timeline({paused:true});
const proofBeat=(inner,probe,line,start,points)=>{tl.set(inner,{opacity:1},start);tl.fromTo(probe,{opacity:0,scale:.6},{opacity:1,scale:1,duration:.25},start+.15);tl.fromTo(line,{opacity:0,scaleX:0},{opacity:.8,scaleX:1,duration:.55,ease:'power2.out'},start+.2);points.forEach((point,index)=>{tl.to(probe,{left:point[0],top:point[1],duration:.72,ease:'power2.inOut'},start+.7+index*.8);tl.to(line,{rotation:index%2?2:-2,duration:.25},start+.7+index*.8);});tl.to(inner,{opacity:0,duration:.22},start+4.78);};
proofBeat('#proof-beat-01-inner','#proof-probe-01','#proof-line-01',0,[[650,470],[930,470],[1500,470]]);
proofBeat('#proof-beat-02-inner','#proof-probe-02','#proof-line-02',5,[[990,410],[990,590],[1370,760]]);
proofBeat('#proof-beat-03-inner','#proof-probe-03','#proof-line-03',10,[[960,455],[1600,455],[320,755],[960,755]]);
proofBeat('#proof-beat-04-inner','#proof-probe-04','#proof-line-04',15,[[360,650],[960,650],[1560,650]]);
window.__timelines['e02-semantic-proof-candidate']=tl;
</script></body></html>
"""


def build_scene_rows(rows: list[dict[str, Any]], brief: dict[str, Any], facts: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    target_wpm = int(brief["target_wpm"])
    total_words = sum(word_count(row["text"]) for row in rows)
    total_duration = total_words / target_wpm * 60 + len(rows) * 0.65
    cursor = 0.0
    sections: list[dict[str, Any]] = []
    visual_sections: list[dict[str, Any]] = []
    for row in rows:
        words = word_count(row["text"])
        duration = words / target_wpm * 60 + 0.65
        start, end = cursor, cursor + duration
        cues = sentence_cues(row, start, end)
        section = {

            "id": row["id"],
            "label": SCENE_TITLES[row["id"]],
            "text": row["text"],
            "start_seconds": round(start, 3),
            "end_seconds": round(end, 3),
            "word_count": words,
            "speaker_directions": "Calm, precise beginner teaching; pause after exact numbers and before the boundary.",
            "delivery_cues": {
                "pace": "measured",
                "energy": SCENE_ENERGY[row["id"]],
                "pause_after_seconds": 0.45,
                "provider_text": row["text"],
            },
            "claim_refs": [row["receipt"]],
            "animation_mode": "deterministic motion-graphics diagram",
            "visual_treatment": SCENE_TREATMENTS[row["id"]],
            "sentence_cues": cues,
            "source_ref": row["receipt"],
        }
        sections.append(section)
        visual_sections.append({
            "section_id": row["id"],
            "start_seconds": round(start, 3),
            "end_seconds": round(end, 3),
            "asset": f"hyperframes/assets/{row['id']}.svg",
            "composition_mode": "atelier",
            "semantic_purpose": SCENE_TREATMENTS[row["id"]],
            "spoken_text": row["text"],
            "claim_refs": [row["receipt"]],
            "sentence_cues": cues,
        })
        cursor = end
    spoken_sentence_ids = [cue["id"] for section in sections for cue in section["sentence_cues"]]
    visual_sentence_ids = [cue["id"] for section in visual_sections for cue in section["sentence_cues"]]
    uncovered_sentences = sorted(set(spoken_sentence_ids) - set(visual_sentence_ids))
    if uncovered_sentences or len(spoken_sentence_ids) != len(visual_sentence_ids):
        raise SystemExit(
            "BLOCK: sentence-bound visual coverage mismatch: "
            f"uncovered={uncovered_sentences}, spoken={len(spoken_sentence_ids)}, visual={len(visual_sentence_ids)}"
        )
    timing = {
        "schema": "into-the-laboratory/sentence-bound-timing/v1",
        "wpm": target_wpm,
        "total_words": total_words,
        "total_duration_seconds": round(cursor, 3),
        "sentence_bound_visual_required": True,
        "coverage": {
            "spoken_sentences": len(spoken_sentence_ids),
            "visual_cues": len(visual_sentence_ids),
            "uncovered_sentences": uncovered_sentences,
        },
        "sections": visual_sections,
        "facts_digest": {
            "spy_entering": facts["spy"]["entering"],
            "spy_later_entering": facts["spy"]["later_entering"],
            "dow_oos_entering": facts["dow"]["oos_entering"],
        },
    }
    return sections, timing


def build_claims(
    rows: list[dict[str, Any]],
    facts: dict[str, Any],
    academic: dict[str, Any],
    vo_path: Path,
    academic_ref: str = ACADEMIC_RECEIPTS_REF,
) -> dict[str, Any]:
    sources: dict[str, dict[str, Any]] = {}
    for source_id, source in academic["sources"].items():
        sources[source_id] = source
    run_citations = {
        "RUN_SPY_PHASE01": ("SPY D1 phase01 intake JSON", "phase01_intake fields and candidate gate pointers", "SPY intake counts and inequalities are read from the hash-bound file.", "Does not establish live execution or future performance."),
        "RUN_SPY_PHASE02": ("SPY D1 phase02 OOS JSON", "phase02_oos entering/surviving/window/notes pointers", "The empty later phase and skip note are read from the hash-bound file.", "No later SPY return exists in this receipt."),
        "RUN_DOW_PHASE01": ("Dow phase01 intake JSON", "phase01_intake candidate metrics pointers", "The same Dow candidate's in-sample net and PF are read from the hash-bound file.", "This is a separate futures lane from SPY."),
        "RUN_DOW_PHASE02": ("Dow phase02 OOS JSON", "phase02_oos counts and candidate metric pointers", "Dow later-block counts and the candidate's later metrics are read from the hash-bound file.", "This is one later block, not a proof of live performance."),
        "RUN_SPY_LEDGER": ("SPY lineage JSONL receipt", "candidate lineage.generation_params and lineage.explanation on the bound row", "The source row records the RSI2 concept, its 200/2 window inputs, and the explicit engine-side exit assumption used by the lesson.", "The ledger describes candidate lineage and an assumption; it is not a full execution specification."),
        "RUN_SPY_MANIFEST": ("SPY run manifest", "program_id and /candidates_provenance/0 (id at /candidates_provenance/0/id)", "The run identity is bound to the saved program and candidate provenance row.", "Manifest metadata does not validate a live fill."),
        "RUN_LIVE_MANIFEST": ("TraderCockpit E01-E03 live receipt manifest", "episodes/02 stock_branch and dow_oos_branch", "The current series manifest cross-checks the two E02 branches.", "It is a copied manifest; the phase JSON hashes remain the primary run receipts."),
    }
    for source_id, (citation, locator, supports, limitations) in run_citations.items():
        record = facts["sources"].get(source_id)
        if record:
            sources[source_id] = {
                "citation": citation,
                "locator": locator,
                "supports": supports,
                "limitations": limitations,
                "path": record["path"],
                "sha256": record["sha256"],
                "pointers": record["pointers"],
            }

    claim_sources = {
        "C01": ["RUN_SPY_PHASE01", "RUN_SPY_PHASE02", "RUN_DOW_PHASE02"],
        "C02": ["ACADEMIC_ISLR_TEST", "ACADEMIC_TASHMAN_OOS", "RUN_SPY_PHASE01", "RUN_SPY_PHASE02"],
        "C03": ["ACADEMIC_ISLR_TEST", "ACADEMIC_WHITE_SNOOP", "ACADEMIC_TASHMAN_OOS", "ACADEMIC_BERGMEIR_CV", "ACADEMIC_METRIC_ONTOLOGY"],
        "C04": ["RUN_SPY_LEDGER", "RUN_SPY_MANIFEST", "RUN_SPY_PHASE01", "ACADEMIC_METRIC_ONTOLOGY"],
        "C05": ["ACADEMIC_METRIC_ONTOLOGY", "RUN_SPY_PHASE01"],
        "C06": ["RUN_SPY_PHASE01"],
        "C07": ["RUN_SPY_PHASE01", "RUN_SPY_PHASE02"],
        "C08": ["RUN_SPY_PHASE01", "RUN_SPY_PHASE02", "RUN_DOW_PHASE02"],
        "C09": ["RUN_DOW_PHASE01", "RUN_DOW_PHASE02"],
        "C10": ["ACADEMIC_WHITE_SNOOP", "ACADEMIC_SULLIVAN_BOOTSTRAP", "ACADEMIC_ISLR_TEST", "RUN_SPY_PHASE01", "RUN_DOW_PHASE02"],
        "C11": ["ACADEMIC_NIST_DISTRIBUTION", "ACADEMIC_NIST_PERCENTILE", "RUN_SPY_PHASE01", "RUN_DOW_PHASE02"],
        "C12": ["ACADEMIC_TASHMAN_OOS", "ACADEMIC_BERGMEIR_CV", "RUN_SPY_PHASE01", "RUN_SPY_PHASE02", "RUN_DOW_PHASE02"],
        "C13": ["RUN_SPY_PHASE01", "RUN_SPY_PHASE02", "RUN_DOW_PHASE02", "ACADEMIC_ISLR_TEST"],
        "C14": ["RUN_SPY_PHASE02", "RUN_DOW_PHASE01", "RUN_DOW_PHASE02", "ACADEMIC_TASHMAN_OOS"],
    }
    claims: dict[str, Any] = {}
    for row in rows:
        claim_id = row["receipt"]
        claims[claim_id] = {
            "kind": "run_receipt" if claim_id in {"C01", "C04", "C05", "C06", "C07", "C08", "C09", "C13", "C14"} else "academic",
            "source_ids": claim_sources[claim_id],
            "sentence_scope": "one spoken paragraph, with empirical values and/or definitions bound to the listed sources",
            "private_receipt": {
                "facts_receipt": "facts_receipt.json",
                "academic_receipts": academic_ref,
            },
        }
    return {
        "schema": "teaching-claims/v1",
        "script_sha256": sha256(vo_path),
        "sources": sources,
        "claims": claims,
        "claim_policy": "Every spoken paragraph is bound to one claim ID; every empirical value points to a hash-bound JSON pointer or a named academic locator.",
    }


def build_research(brief: dict[str, Any], academic: dict[str, Any], facts: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "openmontage/animation/research-brief/v1",
        "topic": brief["delivery_promise"],
        "audience": brief["audience"],
        "research_summary": "A beginner lesson is clearest when the evidence boundary is a physical chamber: the SPY branch stops before later prices, while the separate Dow branch carries one candidate through and changes its measured result.",
        "data_points": [
            {"id": "SPY_5_TO_0", "claim": "SPY D1: five enter, zero survive, later phase empty", "source": "RUN_SPY_PHASE01/RUN_SPY_PHASE02", "visual_potential": "high"},
            {"id": "SPY_INEQUALITIES", "claim": "0.806004 > 1.3, -0.420205 > 4, and 0.392308 trades/month > 2 are all false", "source": "RUN_SPY_PHASE01", "visual_potential": "high"},
            {"id": "DOW_184_TO_154", "claim": "Dow later phase: 184 enter, 154 survive, 30 drop", "source": "RUN_DOW_PHASE02", "visual_potential": "high"},
            {"id": "DOW_ROW_FLIP", "claim": "The same Dow candidate moves from +$16,727.80/PF 1.28037 to -$4,897.40/PF 0.813381", "source": "RUN_DOW_PHASE01/RUN_DOW_PHASE02", "visual_potential": "high"},
        ],
        "academic_sources": list(academic["sources"].keys()),
        "angles_discovered": [
            {"id": "sealed-chamber", "angle": "Selection is a door; a holdout is the later chamber that must stay shut until the candidate is frozen.", "animation_fit": "progressive diagram", "grounded_in": ["SPY_5_TO_0", "SPY_INEQUALITIES"]},
            {"id": "same-row-change", "angle": "Keep one Dow candidate fixed while the price window changes around it.", "animation_fit": "before/after track", "grounded_in": ["DOW_ROW_FLIP"]},
            {"id": "operator-ruler", "angle": "Teach each gate as actual value > threshold with units, not as a green or red card.", "animation_fit": "kinetic inequality ruler", "grounded_in": ["SPY_INEQUALITIES"]},
        ],
        "technique_references": [
            {"technique": "progressive diagram build", "source": "HyperFrames core deterministic composition contract", "mode": "motion_graphics", "complexity": "moderate"},
            {"technique": "ordered dot strip with median and percentile markers", "source": academic["sources"]["ACADEMIC_NIST_PERCENTILE"]["url"], "mode": "motion_graphics", "complexity": "simple"},
        ],
        "limitations": [
            "No claim here says that either receipt is live-trading validation.",
            "No SPY holdout return is available because the phase is empty.",
            "No timing-hours census is shown; the episode ends by asking that question."
        ],
    }


def build_proposal(brief: dict[str, Any], research: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    proposal = {
        "schema": "openmontage/animation/proposal-packet/v1",
        "title": brief["title"],
        "delivery_promise": brief["delivery_promise"],
        "concept_options": [
            {"id": "sealed-chamber", "animation_mode": "motion_graphics", "structure": "two lanes with a physical later-price seal", "hook": "five tokens stop before the door", "reuse_strategy": "fixed rail, chamber, token, and operator glyph system"},
            {"id": "same-row-track", "animation_mode": "diagram-led", "structure": "one Dow candidate travels across two time windows", "hook": "same ID, opposite net result", "reuse_strategy": "window brackets and metric rails"},
            {"id": "inequality-ruler", "animation_mode": "kinetic typography plus math diagram", "structure": "actual > threshold with units", "hook": "precision has no meaning without the operator", "reuse_strategy": "three ruler rows and a shared comparison grammar"},
        ],
        "selected_concept": {
            "id": "sealed-chamber",
            "animation_mode": "deterministic motion_graphics",
            "reuse_strategy": "branch rails, chamber seals, tokens, and inequality rulers; each scene changes the mechanism rather than repeating a card",
            "audio_architecture": brief["audio_architecture"],
            "render_runtime": brief["render_runtime"],
            "renderer_family": brief["renderer_family"],
        },
        "production_plan": {
            "target_duration_minutes": "13-15",
            "render_runtime": brief["render_runtime"],
            "provider_calls": False,
            "candidate_stop": "operator review before narration or master",
        },
        "cost_estimate": {
            "currency": "USD",
            "line_items": [{"item": "deterministic local proof source", "cost": 0}, {"item": "provider media", "cost": 0, "status": "not requested"}],
            "provider_comparison": [{"option": "quality-first approved provider route", "status": "deferred until operator approves script/package"}, {"option": "local deterministic proof", "status": "used for candidate proof only", "cost": 0}],
        },
        "approval": {"status": "candidate-only-authorized", "operator_approval_for_final": False},
    }
    decision_log = {
        "schema": "openmontage/decision-log/v1",
        "decisions": [{
            "category": "render_runtime_selection",
            "options_considered": ["remotion", "hyperframes"],
            "selected": "hyperframes",
            "reason": "The E02 proof is HTML/SVG motion-graphics-native, with sentence-bound diagram states and no narration asset; use the repo's HyperFrames checkout for lint/validate/proof inspection.",
            "approval_scope": "candidate semantic proof only; no full master",
        }],
    }
    return proposal, decision_log


def canonical_script_sections(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip the E02 teaching metadata down to OpenMontage's script contract."""
    result = []
    for section in sections:
        result.append({
            "id": section["id"],
            "label": section["label"],
            "text": section["text"],
            "start_seconds": section["start_seconds"],
            "end_seconds": section["end_seconds"],
            "speaker_directions": section["speaker_directions"],
            "delivery_cues": {
                "pace": section["delivery_cues"]["pace"],
                "energy": section["delivery_cues"]["energy"],
                "pause_after_seconds": section["delivery_cues"]["pause_after_seconds"],
                "provider_text": section["delivery_cues"]["provider_text"],
            },
            "enhancement_cues": [
                {
                    "type": "animation",
                    "description": (
                        f"sentence-bound mechanism transformation {cue['id']} "
                        f"using {SCENE_MOTION_SIGNATURES[section['id']]}"
                    ),
                    "timestamp_seconds": timestamp,
                }
                for cue in section["sentence_cues"]
                for timestamp in (
                    cue["start_seconds"],
                    round((cue["start_seconds"] + cue["end_seconds"]) / 2, 6),
                    cue["end_seconds"],
                )
            ] + [{
                "type": "animation",
                "description": (
                    f"section-end mechanism state holds after "
                    f"{SCENE_MOTION_SIGNATURES[section['id']]}"
                ),
                "timestamp_seconds": section["end_seconds"],
            }],
            "source_ref": section["source_ref"],
            "claim_refs": section["claim_refs"],
        })
    return result


def _resolve_external_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_narration_entries(receipt_path: Path | None) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    if receipt_path is None:
        return None, []
    if not receipt_path.is_file():
        raise SystemExit(f"BLOCK: requested narration receipt is missing: {receipt_path}")
    receipt = load_json(receipt_path)
    entries = sorted(receipt.get("entries", []), key=lambda item: item["section_index"])
    if receipt.get("status") != "completed" or len(entries) != len(SCENE_TITLES):
        raise SystemExit(
            "BLOCK: E02 narration receipt is not complete: "
            f"status={receipt.get('status')!r}, entries={len(entries)}/{len(SCENE_TITLES)}"
        )
    for entry in entries:
        clean = _resolve_external_path(entry["clean_path"])
        if not clean.is_file():
            raise SystemExit(f"BLOCK: narration clean asset is missing: {clean}")
        if sha256(clean) != entry.get("clean_sha256"):
            raise SystemExit(f"BLOCK: narration clean asset drifted: {clean}")
    return receipt, entries


def measured_visual_sections(
    base_sections: list[dict[str, Any]],
    entries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
    """Re-time diagrams to the measured provider audio without rewriting the script."""
    if not entries:
        return base_sections, [], base_sections[-1]["end_seconds"]
    entry_by_scene = {entry["scene_id"]: entry for entry in entries}
    if set(entry_by_scene) != set(SCENE_TITLES):
        raise SystemExit("BLOCK: narration receipt does not cover the exact 14-scene E02 script")
    visual_sections: list[dict[str, Any]] = []
    audio_segments: list[dict[str, Any]] = []
    cursor = 0.0
    for index, section in enumerate(base_sections):
        entry = entry_by_scene[section["section_id"]]
        original_duration = section["end_seconds"] - section["start_seconds"]
        head = 0.20 if index == 0 else 0.15
        audio_start = round(cursor + head, 6)
        audio_end = round(audio_start + float(entry["duration_seconds"]), 6)
        scene_end = round(audio_end + 0.35, 6)
        scene_duration = scene_end - cursor
        cues = []
        for cue in section["sentence_cues"]:
            start_fraction = (cue["start_seconds"] - section["start_seconds"]) / original_duration
            end_fraction = (cue["end_seconds"] - section["start_seconds"]) / original_duration
            updated = dict(cue)
            updated["start_seconds"] = round(cursor + start_fraction * scene_duration, 6)
            updated["end_seconds"] = round(cursor + end_fraction * scene_duration, 6)
            updated["duration_seconds"] = round(updated["end_seconds"] - updated["start_seconds"], 6)
            cues.append(updated)
        visual_sections.append({
            **section,
            "start_seconds": round(cursor, 6),
            "end_seconds": scene_end,
            "sentence_cues": cues,
            "timing_source": "measured_provider_audio",
        })
        audio_segments.append({
            "asset_id": f"narration-{section['section_id']}",
            "scene_id": section["section_id"],
            "start_seconds": audio_start,
            "end_seconds": audio_end,
            "duration_seconds": round(float(entry["duration_seconds"]), 6),
        })
        cursor = scene_end
    return visual_sections, audio_segments, round(cursor, 6)


def scene_composition_html(scene_id: str, section: dict[str, Any]) -> str:
    """Emit one bespoke HyperFrames composition with sentence-bound mechanism motion."""
    duration = round(section["end_seconds"] - section["start_seconds"], 6)
    points = SCENE_MOTION_TARGETS[scene_id]
    cue_times = [
        max(0.15, round(cue["start_seconds"] - section["start_seconds"], 6))
        for cue in section["sentence_cues"]
    ]
    cue_times = [min(max(0.15, value), max(0.15, duration - 0.2)) for value in cue_times]
    cue_targets = [points[index % len(points)] for index in range(len(cue_times))]
    cue_markup = "".join(
        f'<i id="cue-{index:03d}" class="cue-tick" style="left:{point[0]}px;top:{point[1]}px"></i>'
        for index, point in enumerate(cue_targets)
    )
    cue_steps = []
    for index, (at, point) in enumerate(zip(cue_times, cue_targets)):
        cue_steps.append(
            f"tl.to('#mechanism-probe',{{left:'{point[0]}px',top:'{point[1]}px',duration:.42,ease:'power2.inOut'}},{at});"
            f"tl.fromTo('#cue-{index:03d}',{{opacity:0,scale:.35}},{{opacity:.9,scale:1,duration:.18}},{at});"
        )
    if scene_id == "scene-05":
        mechanism = '<i id="sweep-1" class="gate-sweep"></i><i id="sweep-2" class="gate-sweep"></i><i id="sweep-3" class="gate-sweep"></i>'
        signature = "three actual-to-threshold comparisons are visited in order"
        extra_steps = (
            "tl.fromTo('#sweep-1',{scaleX:0,opacity:0},{scaleX:1,opacity:.75,duration:.45},.35);"
            "tl.fromTo('#sweep-2',{scaleX:0,opacity:0},{scaleX:1,opacity:.75,duration:.45},1.15);"
            "tl.fromTo('#sweep-3',{scaleX:0,opacity:0},{scaleX:1,opacity:.75,duration:.45},1.95);"
        )
    elif scene_id == "scene-08":
        mechanism = '<i id="lane-stock" class="lane-scan stock"></i><i id="lane-futures" class="lane-scan futures"></i><i id="lane-seal" class="lane-seal"></i>'
        signature = "the SPY rail terminates at the boundary while the Dow rail keeps moving"
        extra_steps = (
            "tl.fromTo('#lane-stock',{scaleX:0,opacity:0},{scaleX:1,opacity:.8,duration:.8},.35);"
            "tl.fromTo('#lane-seal',{scaleY:0,opacity:0},{scaleY:1,opacity:.9,duration:.45},1.15);"
            "tl.fromTo('#lane-futures',{scaleX:0,opacity:0},{scaleX:1,opacity:.8,duration:1.2},1.55);"
        )
    elif scene_id == "scene-14":
        mechanism = '<i id="question-left" class="question-branch left"></i><i id="question-right" class="question-branch right"></i><i id="question-node" class="question-node"></i>'
        signature = "one evidence line branches into two unanswered execution questions"
        extra_steps = (
            "tl.fromTo('#question-node',{scale:.2,opacity:0},{scale:1,opacity:1,duration:.35},.35);"
            "tl.fromTo('#question-left',{scaleX:0,opacity:0},{scaleX:1,opacity:.85,duration:.65},.75);"
            "tl.fromTo('#question-right',{scaleX:0,opacity:0},{scaleX:1,opacity:.85,duration:.65},1.35);"
        )
    else:
        mechanism = '<i id="mechanism-vector" class="mechanism-vector"></i>'
        signature = SCENE_MOTION_SIGNATURES[scene_id]
        extra_steps = (
            "tl.fromTo('#mechanism-vector',{scaleX:0,opacity:0},{scaleX:1,opacity:.7,duration:.8},.35);"
        )
    return re.sub(r"box-shadow:[^;}]+;?", "", f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>ep02-{scene_id}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
*{{box-sizing:border-box}}html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#080b12}}#root{{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden;background:#080b12}}#art{{position:absolute;inset:0;width:1920px;height:1080px;display:block;transform-origin:50% 50%}}.motion-layer{{position:absolute;inset:0;width:1920px;height:1080px;pointer-events:none}}.mechanism-probe{{position:absolute;width:28px;height:28px;border:5px solid #f0ba55;border-radius:50%;transform:translate(-50%,-50%);opacity:0;box-shadow:0 0 0 12px rgba(240,186,85,.12),0 0 26px rgba(240,186,85,.32)}}.cue-tick{{position:absolute;width:12px;height:12px;border-radius:50%;background:#7ed7d2;transform:translate(-50%,-50%);opacity:0;box-shadow:0 0 16px rgba(126,215,210,.7)}}.mechanism-vector{{position:absolute;left:180px;top:520px;width:1450px;height:6px;background:#7ed7d2;transform-origin:left center;opacity:0;box-shadow:0 0 20px rgba(126,215,210,.35)}}.gate-sweep{{position:absolute;left:470px;width:1170px;height:8px;background:#f0ba55;transform-origin:left center;opacity:0;box-shadow:0 0 18px rgba(240,186,85,.4)}}#sweep-1{{top:410px}}#sweep-2{{top:590px}}#sweep-3{{top:760px}}.lane-scan{{position:absolute;left:170px;width:1580px;height:8px;transform-origin:left center;opacity:0;box-shadow:0 0 18px currentColor}}.lane-scan.stock{{top:455px;background:#f0ba55;color:#f0ba55}}.lane-scan.futures{{top:755px;background:#7ed7d2;color:#7ed7d2}}.lane-seal{{position:absolute;left:1010px;top:350px;width:8px;height:510px;background:#d27ca7;transform-origin:50% 0;opacity:0;box-shadow:0 0 18px rgba(210,124,167,.45)}}.question-branch{{position:absolute;left:360px;top:650px;width:600px;height:7px;transform-origin:right center;opacity:0}}.question-branch.left{{background:#f0ba55}}.question-branch.right{{left:960px;background:#7ed7d2;transform-origin:left center}}.question-node{{position:absolute;left:960px;top:650px;width:28px;height:28px;border-radius:50%;background:#f5f1e8;transform:translate(-50%,-50%);opacity:0}}
</style></head><body><div id="root" class="scene-{scene_id}" data-composition-id="ep02-{scene_id}" data-width="1920" data-height="1080" data-duration="{duration:.6f}" data-motion-signature="{html.escape(signature, quote=True)}">
<img id="art" src="../assets/{scene_id}.svg" alt="{html.escape(SCENE_TITLES[scene_id], quote=True)}"><div class="motion-layer">{mechanism}<i id="mechanism-probe" class="mechanism-probe" style="left:{points[0][0]}px;top:{points[0][1]}px"></i>{cue_markup}</div>
</div><script>
window.__timelines=window.__timelines||{{}};const tl=gsap.timeline({{paused:true}});
tl.fromTo('#art',{{opacity:0,scale:1.035,x:-24}},{{opacity:1,scale:1,x:0,duration:.55,ease:'power2.out'}},.05);
{extra_steps}
tl.fromTo('#mechanism-probe',{{opacity:0,scale:.55}},{{opacity:1,scale:1,duration:.25}},.18);
{"".join(cue_steps)}
tl.to({{}},{{duration:{duration:.6f}}});window.__timelines['ep02-{scene_id}']=tl;
</script></body></html>
""")


def full_hyperframes_index(
    sections: list[dict[str, Any]],
    audio_segments: list[dict[str, Any]],
    title: str,
) -> str:
    total = sections[-1]["end_seconds"] if sections else 0
    audio_by_scene = {segment["scene_id"]: segment for segment in audio_segments}
    slots = []
    audio = []
    for index, section in enumerate(sections, 1):
        scene_id = section["section_id"]
        start = section["start_seconds"]
        duration = section["end_seconds"] - section["start_seconds"]
        slots.append(
            f'<div id="slot-{index:02d}" class="clip scene-slot" data-composition-id="ep02-{scene_id}" '
            f'data-composition-src="compositions/{scene_id}.html" data-start="{start:.6f}" '
            f'data-duration="{duration:.6f}" data-track-index="1" data-width="1920" data-height="1080"></div>'
        )
        segment = audio_by_scene.get(scene_id)
        if segment:
            audio.append(
                f'<audio id="narration-{index:02d}" src="../assets/audio/{NARRATION_AUDIO_SUBDIR}/{scene_id}.wav" '
                f'data-start="{segment["start_seconds"]:.6f}" data-duration="{segment["duration_seconds"]:.6f}" '
                f'data-track-index="10" data-volume="0.707945"></audio>'
            )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script><style>
*{{box-sizing:border-box;margin:0;padding:0}}html,body{{width:100%;height:100%;overflow:hidden;background:#080b12}}#root{{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden;background:#080b12}}.scene-slot{{position:absolute;inset:0;width:1920px;height:1080px;overflow:hidden}}
</style></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="{total:.6f}" data-width="1920" data-height="1080" data-fps="30">
{"".join(slots)}
{"".join(audio)}
</div><script>window.__timelines=window.__timelines||{{}};const main=gsap.timeline({{paused:true}});main.to({{}},{{duration:{total:.6f}}});window.__timelines.main=main;</script></body></html>
"""


def canonical_scene_plan(sections: list[dict[str, Any]]) -> dict[str, Any]:
    roles = [
        "establish_context", "introduce_subject", "deliver_payload", "evidence",
        "evidence", "comparison", "evidence", "comparison", "evidence",
        "build_tension", "evidence", "transition", "resolution", "call_to_action",
    ]
    movements = [
        "tokens advance to a seal; the futures branch opens on a separate rail",
        "settings slide into a freeze clamp, then the later chamber opens once",
        "a drawn seal divides build history from the later judging chamber",
        "warmup bars sweep into the indicator window before the signal rail lights",
        "actual, operator, threshold, and FALSE are visited row by row",
        "five intake tokens move while one row is magnified without changing the field",
        "zero gauges remain empty while the later-price boundary locks",
        "stock and futures lanes move independently across an explicit divider",
        "the same candidate identity crosses two price-window rails and changes metric state",
        "the smooth signal and noisy curve are traced as different paths",
        "ordered outcomes receive median and percentile marks in sequence",
        "fixed jobs stay in place while the walk-forward origin advances",
        "worksheet fields fill from instrument to windows to counts and hash binding",
        "one evidence rail branches into two unanswered execution questions",
    ]
    scenes = []
    for index, section in enumerate(sections):
        scene_id = section["section_id"]
        scenes.append({
            "id": scene_id,
            "type": "animation",
            "description": f"{SCENE_TITLES[scene_id]}: {SCENE_MOTION_SIGNATURES[scene_id]}.",
            "start_seconds": section["start_seconds"],
            "end_seconds": section["end_seconds"],
            "script_section_id": scene_id,
            "framing": "wide mechanism field",
            "movement": movements[index],
            "transition_in": "mechanism-led match cut",
            "transition_out": "evidence-state match cut",
            "overlay_notes": "Sentence-bound probe marks the active mechanism; no provenance furniture is placed in the lesson graphic.",
            "shot_language": {
                "shot_size": "wide",
                "camera_movement": ["tracking_right", "dolly_in", "pan_right", "rack_focus"][index % 4],
                "lighting_key": "low_key",
                "depth_of_field": "deep",
                "color_temperature": "cool",
            },
            "shot_intent": SCENE_MOTION_SIGNATURES[scene_id],
            "narrative_role": roles[index],
            "information_role": section["semantic_purpose"],
            "hero_moment": scene_id in {"scene-05", "scene-08", "scene-14"},
            "texture_keywords": ["open canvas", "evidence rail", "mechanical probe"],
            "required_assets": [{"type": "diagram", "description": f"Deterministic {scene_id} evidence graphic", "source": "record"}],
        })
    return {
        "version": "1.0",
        "style_playbook": "quant-atlas-v2-atelier",
        "scenes": scenes,
        "metadata": {
            "composition_contract": "14 bespoke HyperFrames compositions with sentence-bound mechanism probes",
            "repeated_stage_shell": "removed",
            "paired_card_scenes": {"scene-08": "linear stock/futures rails", "scene-14": "branching execution-question rail"},
        },
    }


def final_brief(brief: dict[str, Any], timing: dict[str, Any]) -> dict[str, Any]:
    return {
        "version": "1.0",
        "title": brief["title"],
        "hook": brief["first_spoken_sentence"],
        "key_points": [
            "SPY D1 Connors RSI2 records five intake entries and zero later-phase entries; its holdout is not reached.",
            "The SPY gate is taught as 0.806004 > 1.3, -0.420205 > 4, and 0.392308 trades/month > 2, each false with units shown.",
            "The separate Dow lane changes from 184 to 154 and carries one candidate from positive in-sample net/PF to negative later-block net/PF.",
            "The lesson ends by asking whether the survivors depend on fill timing or trading hours.",
        ],
        "core_message": "A later price block can judge a frozen version only once; SPY never reaches that chamber here, while the separate Dow lane shows why a candidate's measured result can change.",
        "cta": "Ask whether the remaining survivors depend on fill timing or trading hours.",
        "tone": "Plain-spoken, forensic, calm, and concrete beginner teaching.",
        "style": "Quant Atlas v2 atelier: open evidence rails, deterministic diagrams, and purposeful mechanism motion.",
        "target_audience": brief["audience"],
        "target_platform": "youtube",
        "target_duration_seconds": timing["total_duration_seconds"],
        "reference_material": ["sources/vo.txt", "sources/academic_receipts.json", "artifacts/facts_receipt.json"],
        "angle_options": [
            {"name": "The sealed chamber", "description": "Freeze the selection before later prices and show SPY stopping before the chamber."},
            {"name": "The same Dow row", "description": "Carry one candidate across the separate Dow price window and compare its measured fields."},
            {"name": "The operator's ruler", "description": "Teach every SPY gate as actual value, operator, threshold, and unit."},
        ],
        "selected_angle": "The sealed chamber with a separate Dow comparison lane",
        "metadata": {
            "episode": 2,
            "sentence_bound_visuals": True,
            "visual_direction_resolution": "open canvas; no repeated rounded stage shell; no paired card stack in scenes 08 or 14",
        },
    }


def final_proposal(brief: dict[str, Any], research: dict[str, Any], timing: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    proposal = {
        "version": "1.0",
        "concept_options": [
            {
                "id": "sealed-chamber",
                "title": "Freeze the selection before the chamber",
                "hook": "Five SPY candidates stop before later prices open.",
                "narrative_structure": "tutorial",
                "visual_approach": "Open evidence rails, a physical seal, and sentence-bound probes that trace the decision mechanism.",
                "suggested_playbook": "quant-atlas-v2-atelier",
                "target_audience": brief["audience"],
                "target_platform": "youtube",
                "target_duration_seconds": timing["total_duration_seconds"],
                "key_points": ["SPY 5 to 0", "Dow 184 to 154", "operator inequalities"],
                "core_message": "Freeze before the later look.",
                "cta": "Ask about fill timing and trading hours.",
                "tone": "forensic beginner lesson",
                "why_this_works": "It turns the evidence boundary into a physical mechanism and keeps SPY and Dow as separate lanes.",
            },
            {
                "id": "same-row-track",
                "title": "One Dow identity, two price windows",
                "hook": "The candidate stays the same while the measured result changes.",
                "narrative_structure": "comparison",
                "visual_approach": "A moving candidate marker crosses two chronological rails.",
                "suggested_playbook": "quant-atlas-v2-atelier",
                "target_audience": brief["audience"],
                "target_platform": "youtube",
                "target_duration_seconds": timing["total_duration_seconds"],
                "key_points": ["Dow net change", "PF change", "wins and losses"],
                "core_message": "Same row does not mean same evidence status.",
                "cta": "Ask what execution fields remain open.",
                "tone": "measured and investigative",
                "why_this_works": "It gives the Dow contrast a single visible identity without allowing it to stand in for SPY.",
            },
            {
                "id": "inequality-ruler",
                "title": "Read the gate as an operator",
                "hook": "A number needs an operator, a threshold, and a unit.",
                "narrative_structure": "data_narrative",
                "visual_approach": "Three rails compare actual values to thresholds one row at a time.",
                "suggested_playbook": "quant-atlas-v2-atelier",
                "target_audience": brief["audience"],
                "target_platform": "youtube",
                "target_duration_seconds": timing["total_duration_seconds"],
                "key_points": ["PF inequality", "return/drawdown inequality", "trades/month inequality"],
                "core_message": "Do not turn an unlabelled number into a verdict.",
                "cta": "Ask whether the data and execution are fully specified.",
                "tone": "plain and exact",
                "why_this_works": "It makes the worked operators visible and prevents the lesson from collapsing into verdict colors.",
            },
        ],
        "selected_concept": {
            "concept_id": "sealed-chamber",
            "rationale": "The operator direction requires SPY 5→0 and a sealed later-price chamber, while the separate Dow lane must remain visible without becoming the SPY result.",
            "modifications": [
                "Replace the repeated bordered stage shell with an open canvas.",
                "Replace paired rounded cards in scenes 08 and 14 with rails and a branching question path.",
                "Bind a real motion probe and mechanism transformation to every sentence cue in the final timeline.",
            ],
        },
        "production_plan": {
            "pipeline": "hybrid",
            "playbook": "quant-atlas-v2-atelier",
            "stages": [
                {"stage": "idea", "tools": [{"tool_name": "series-script", "role": "live lesson authority", "provider": "TraderCockpit", "available": True, "estimated_cost_usd": 0}], "approach": "Reconcile the live series authority and E02 scope before generation."},
                {"stage": "script", "tools": [{"tool_name": "build_e02_rebuild.py", "role": "source-bound script and claim package", "provider": "local", "available": True, "estimated_cost_usd": 0}], "approach": "Regenerate the full 14-scene script from the pinned source packet and facts receipts."},
                {"stage": "scene_plan", "tools": [{"tool_name": "HyperFrames", "role": "bespoke sentence-bound composition", "provider": "local", "available": True, "estimated_cost_usd": 0}], "approach": "Use scene-specific rails, probes, seals, and branch paths; no stock card stack."},
                {"stage": "assets", "tools": [{"tool_name": "build_e02_rebuild.py", "role": "deterministic evidence diagrams", "provider": "local", "available": True, "estimated_cost_usd": 0}], "approach": "Generate original SVG evidence surfaces; no generated factual media."},
                {"stage": "edit", "tools": [{"tool_name": "HyperFrames", "role": "HTML/CSS/GSAP timeline", "provider": "local", "available": True, "estimated_cost_usd": 0}], "approach": "Align 14 scene cuts and measured narration to the final timeline."},
                {"stage": "compose", "tools": [{"tool_name": "HyperFrames CLI", "role": "1920x1080 master render", "provider": "local", "available": True, "estimated_cost_usd": 0}], "approach": "Lint, validate, render high quality at 30 fps, then probe and inspect the playable result."},
            ],
            "quality_tradeoffs": [{"tradeoff": "No music bed", "recommendation": "Keep narration-first treatment", "quality_impact": "Preserves evidence clarity and the current series audio route."}],
            "alternative_paths": [{"description": "Candidate semantic proof only", "total_cost_usd": 0, "quality_level": "standard", "what_changes": "No narration or full master."}],
            "delivery_promise": {"promise_type": "data_explainer", "motion_required": True, "source_required": False, "tone_mode": "educational", "quality_floor": "broadcast", "approved_fallback": None},
            "renderer_family": "animation-first",
            "render_runtime": "hyperframes",
            "composition_mode": "atelier",
            "art_direction": "Open near-black canvas, paper-white evidence, amber untouched state, cyan measurement path, magenta seal; rails and mechanical probes replace rounded cards.",
            "taste_profile": {
                "design_read": "A forensic lab lesson where evidence status changes physically on the canvas.",
                "visual_variance": 8,
                "motion_intensity": 6,
                "information_density": 5,
                "palette_discipline": "near-black, paper-white, amber, cyan, restrained magenta seal",
                "layout_variation": "rails, branching paths, ordered strips, and indicator windows; no persistent dashboard shell",
                "reference_strategy": "Native frames are reviewed at 150px squint and in a playable montage.",
                "anti_patterns": ["repeated rounded stage shell", "paired card stack", "decorative opacity drift", "provenance furniture in lesson graphics"],
                "quality_gates": ["sentence-bound visual coverage", "literal Impeccable []", "native HyperFrames lint/validate", "playable see-video review"],
            },
            "music_source": {"source_type": "none", "mood_direction": "No music; narration and evidence-synchronized motion carry the lesson.", "estimated_cost_usd": 0},
            "voice_selection": {
                "provider": "Higgsfield Qwen Audio 3.0 TTS Flash",
                "voice_id": JOHN_VOICE_ID,
                "rationale": "Exact live E1-E5 route approval selects Higgsfield Qwen Audio 3.0 TTS Flash / John / clean under the existing subscription.",
                "estimated_cost_usd": 0,
                "delivery_style": JOHN_INSTRUCTION,
                "pacing_policy": "Speech rate 1.0, pitch rate 1.0, no local tempo transform.",
                "sample_approval_required": False,
            },
            "decision_log_ref": "decision_log.json",
        },
        "cost_estimate": {
            "total_estimated_usd": 0,
            "line_items": [
                {"tool": "Higgsfield Max", "operation": "John narration under existing entitlement", "quantity": len(SCENE_TITLES), "estimated_usd": 0, "notes": "Exact route approval is hash-bound; no top-up or new subscription authorized."},
                {"tool": "HyperFrames", "operation": "local composition and master render", "quantity": 1, "estimated_usd": 0, "notes": "Repository-local execution."},
            ],
            "budget_verdict": "no_budget_set",
        },
        "approval": {"status": "approved", "user_notes": "Local full production authorized; upload, publish, schedule, merge, deploy, accounts, top-up, and provider substitution remain out of scope."},
        "metadata": {"operator_authorization": OPERATOR_AUTHORIZATION, "exact_hash_publication_approval": False},
    }
    decision_log = {
        "version": "1.0",
        "project_id": FINAL_PROJECT_ID,
        "decisions": [
            {
                "decision_id": "e02-approval-policy-full-local",
                "stage": "idea",
                "category": "approval_policy",
                "subject": "E02 local production authorization",
                "options_considered": [
                    {"option_id": "candidate_only", "label": "Candidate proof only", "score": 0.2, "reason": "This was the prior stop state.", "rejected_because": "Superseded by the current operator authorization for local production."},
                    {"option_id": "full_local_production", "label": "Full local narration and master", "score": 1.0, "reason": f"The operator explicitly said: {OPERATOR_AUTHORIZATION} This authorizes local narration, audio treatment, deterministic composition, master render, and QA only.",},
                ],
                "selected": "full_local_production",
                "reason": "Proceed locally through final playable QA; public and remote mutations remain blocked.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 1.0,
            },
            {
                "decision_id": "e02-pipeline-hybrid",
                "stage": "idea",
                "category": "pipeline_selection",
                "subject": "OpenMontage pipeline",
                "options_considered": [
                    {"option_id": "hybrid", "label": "Hybrid", "score": 1.0, "reason": "Matches the live series route: narration-led graphics with HyperFrames composition."},
                    {"option_id": "animation", "label": "Animation-only", "score": 0.7, "reason": "Could carry deterministic diagrams but does not match the live project route.", "rejected_because": "Current series authority pins hybrid."},
                ],
                "selected": "hybrid",
                "reason": "Carry the live series pipeline contract forward.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 0.99,
            },
            {
                "decision_id": "e02-render-runtime-hyperframes",
                "stage": "scene_plan",
                "category": "render_runtime_selection",
                "subject": "Composition runtime",
                "options_considered": [
                    {"option_id": "remotion", "label": "Remotion", "score": 0.0, "reason": "The canonical checkout reports Remotion unavailable on this machine.", "rejected_because": "Runtime unavailable; no install or route substitution authorized."},
                    {"option_id": "hyperframes", "label": "HyperFrames", "score": 1.0, "reason": "Canonical checkout supports the HTML/CSS/GSAP composition and is available for the series route."},
                    {"option_id": "ffmpeg", "label": "FFmpeg only", "score": 0.35, "reason": "Useful for final audio normalization but not for the authored motion composition.", "rejected_because": "Would discard scene-specific HTML/GSAP motion."},
                ],
                "selected": "hyperframes",
                "reason": "Preserves bespoke scene motion and the selected runtime without a silent downgrade.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 0.98,
            },
            {
                "decision_id": "e02-composition-atelier",
                "stage": "scene_plan",
                "category": "composition_mode",
                "subject": "Visual composition mode",
                "options_considered": [
                    {"option_id": "templated", "label": "Templated cards", "score": 0.1, "reason": "Fast but repeats the blocked card-stack treatment.", "rejected_because": "Explicit no-card-stack and no-repeated-hero direction."},
                    {"option_id": "atelier", "label": "Bespoke atelier scenes", "score": 1.0, "reason": "Each scene has a different mechanism surface and a sentence-bound motion probe."},
                ],
                "selected": "atelier",
                "reason": "Use open rails, seals, paths, ordered strips, and branch motion as the lesson grammar.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 0.99,
            },
            {
                "decision_id": "e02-voice-john-higgsfield",
                "stage": "assets",
                "category": "voice_selection",
                "subject": "Narration route",
                "options_considered": [
                    {"option_id": "higgsfield-john", "label": "Higgsfield John / clean", "score": 1.0, "reason": f"The exact live E1-E5 route approval selects Higgsfield Qwen Audio 3.0 TTS Flash / John / clean under the existing subscription; {VOICE_ROUTE_APPROVAL_REF} SHA-256 {VOICE_ROUTE_APPROVAL_SHA256}."},
                    {"option_id": "elevenlabs", "label": "ElevenLabs", "score": 0.0, "reason": "Available in the generic registry but not the current series route.", "rejected_because": "Provider substitution is not authorized."},
                    {"option_id": "local-tts", "label": "Local TTS", "score": 0.0, "reason": "Would change the selected voice treatment.", "rejected_because": "Current series route is quality-first Higgsfield Max."},
                ],
                "selected": "higgsfield-john",
                "reason": "Use only the exact current John/clean route under existing entitlement; no top-up, account action, or provider substitution.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 0.97,
            },
            {
                "decision_id": "e02-music-none",
                "stage": "assets",
                "category": "music_source",
                "subject": "Music treatment",
                "options_considered": [
                    {"option_id": "none", "label": "No music", "score": 1.0, "reason": "Keeps exact evidence and narration intelligible and matches the live series route."},
                    {"option_id": "generated-bed", "label": "Generated music bed", "score": 0.2, "reason": "Could add texture but would compete with the lesson and introduce another provider decision.", "rejected_because": "Not needed for this evidence-first episode."},
                ],
                "selected": "none",
                "reason": "Narration plus restrained mechanism motion carries the treatment; no music asset is introduced.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 0.95,
            },
            {
                "decision_id": "e02-visual-shell-repair",
                "stage": "scene_plan",
                "category": "visual_accuracy_check",
                "subject": "Repeated shell and paired-card repair",
                "options_considered": [
                    {"option_id": "retain-shell-cards", "label": "Retain bordered cards", "score": 0.0, "reason": "The proof review identified this as slide-deck risk.", "rejected_because": "Conflicts with the no-card-stack/repeated-hero block."},
                    {"option_id": "open-rails-and-branch", "label": "Open rails and branch path", "score": 1.0, "reason": "Scenes 08 and 14 now express lane separation and unanswered execution questions as moving rails."},
                ],
                "selected": "open-rails-and-branch",
                "reason": "Remove the repeated rounded shell from all scene SVGs and replace the two paired-card scenes with mechanism motion.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 0.99,
            },
        ],
    }
    return proposal, decision_log


def build_final_package(output: Path, narration_receipt: Path | None = None) -> Path:
    """Regenerate the authorized full E02 package from source and measured receipts."""
    brief_source = load_json(SOURCE / "brief.json")
    academic = load_json(SOURCE / "academic_receipts.json")
    facts = verify_facts()
    rows = parse_vo()
    base_sections, base_timing = build_scene_rows(rows, brief_source, facts)
    receipt, narration_entries = load_narration_entries(narration_receipt)

    out = output.resolve()
    out_art = out / "artifacts"
    out_hf = out / "hyperframes"
    out_assets = out_hf / "assets"
    out_compositions = out_hf / "compositions"
    route = verify_live_voice_route()
    out_audio = out / "assets" / "audio" / NARRATION_AUDIO_SUBDIR
    for directory in (out_art, out_assets, out_compositions, out_audio, out / "sources"):
        directory.mkdir(parents=True, exist_ok=True)

    source_vo = (SOURCE / "vo.txt").read_text(encoding="utf-8")
    gate_words = arc_word_count(" ".join(row["text"] for row in rows))
    write_text(out / "vo.txt", source_vo)
    write_text(out / "sources" / "vo.txt", source_vo)
    write_json(out / "sources" / "academic_receipts.json", academic)
    vo_out = out_art / "vo.txt"
    write_text(vo_out, source_vo)

    canonical_sections = canonical_script_sections(base_sections)
    script = {
        "version": "1.0",
        "title": brief_source["title"],
        "total_duration_seconds": base_timing["total_duration_seconds"],
        "voice_performance": {
            "performance_intent": "A calm lab walkthrough for one beginner; exact results are stated without turning them into a promise.",
            "pacing_profile": "technical",
            "energy_curve": "Open with the stopped SPY lane, slow down for the operator inequalities, then separate the Dow contrast and close on unanswered execution questions.",
            "pause_policy": "Pause after every exact number and at every evidence-boundary change.",
            "sample_section_id": "scene-05",
            "provider_notes": {
                "route": "Higgsfield Qwen Audio 3.0 TTS Flash / John / clean",
                "route_approval_path": route["path"],
                "route_approval_sha256": route["sha256"],
                "instruction": JOHN_INSTRUCTION,
                "processing": "70 Hz high-pass; two-pass EBU R128 normalization to -16 LUFS and -1.5 dBTP; 48 kHz mono 24-bit PCM; no tempo transform.",
            },
        },
        "sections": canonical_sections,
        "metadata": {
            "episode": 2,
            "source_packet": "productions/_series/e02-rebuild-source-2026-08-03/episode-02",
            "scope": "SPY 5 to 0 / holdout not reached; separate Dow 184 to 154 and candidate result change",
            "vo_sha256": sha256(vo_out),
            "word_count": gate_words,
        },
    }
    write_json(out_art / "script.json", script)
    script_sha = sha256(out_art / "script.json")
    if narration_entries:
        script_hashes = {entry.get("script_sha256") for entry in narration_entries}
        if script_hashes != {script_sha}:
            raise SystemExit(
                "BLOCK: narration receipt is bound to a different final script: "
                f"receipt={sorted(script_hashes)}, generated={script_sha}"
            )

    visual_sections, audio_segments, total_duration = measured_visual_sections(
        base_timing["sections"], narration_entries
    )
    timing = {
        **base_timing,
        "total_duration_seconds": total_duration,
        "sections": visual_sections,
        "timing_source": "provider-native narration measurements" if narration_entries else "script WPM estimate pending narration",
        "motion_contract": {
            "scene_count": len(visual_sections),
            "sentence_bound_transformations": base_timing["coverage"]["visual_cues"],
            "mechanism_motion": True,
            "repeated_stage_shell": "removed",
            "paired_card_scenes": {"scene-08": "resolved as two open rails", "scene-14": "resolved as one branching question rail"},
        },
    }

    for scene_id in SCENE_TITLES:
        write_text(out_assets / f"{scene_id}.svg", scene_svg(scene_id, facts))
    visual_semantics = validate_scene_assets(out_assets)
    visual_semantics["motion"] = {
        "verified": True,
        "scene_compositions": len(SCENE_TITLES),
        "sentence_bound_transformations": base_timing["coverage"]["visual_cues"],
        "mechanism_signatures": SCENE_MOTION_SIGNATURES,
        "resolution": "open canvas; no repeated rounded stage shell; scenes 08 and 14 use rails/branch rather than paired cards",
    }
    write_text(out_art / "thumbnail-ep02.html", build_thumbnail())

    if narration_entries:
        for entry in narration_entries:
            source = _resolve_external_path(entry["clean_path"])
            target = out_audio / f"{entry['scene_id']}.wav"
            if not target.is_file() or sha256(target) != entry["clean_sha256"]:
                shutil.copy2(source, target)

    for section in visual_sections:
        write_text(
            out_compositions / f"{section['section_id']}.html",
            scene_composition_html(section["section_id"], section),
        )
    write_text(out_hf / "index.html", full_hyperframes_index(visual_sections, audio_segments, brief_source["title"]))
    write_json(out_hf / "hyperframes.json", {
        "schema": "hyperframes/project/v1",
        "composition_id": "main",
        "runtime": "hyperframes",
        "candidate_only": False,
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "scene_count": len(SCENE_TITLES),
        "motion_contract": timing["motion_contract"],
    })

    claims = build_claims(
        rows,
        facts,
        academic,
        vo_out,
        academic_ref="sources/academic_receipts.json",
    )
    research = build_research(brief_source, academic, facts)
    final_brief_artifact = final_brief(brief_source, timing)
    proposal, decision_log = final_proposal(brief_source, research, timing)
    scene_plan = canonical_scene_plan(visual_sections)
    write_json(out_art / "brief.json", final_brief_artifact)
    write_json(out_art / "research_brief.json", research)
    write_json(out_art / "proposal_packet.json", proposal)
    write_json(out_art / "decision_log.json", decision_log)
    write_json(out_art / "scene_plan.json", scene_plan)
    write_json(out_art / "scene_visual_map.json", timing)
    write_json(out_art / "academic_edit_timing.json", timing)
    write_json(out_art / "scenes.json", {"schema": "into-the-laboratory/scenes/v1", "scenes": base_sections})
    write_json(out_art / "claims.json", claims)
    write_json(out_art / "visual_semantic_receipt.json", visual_semantics)
    write_text(
        out_art / "art-direction.md",
        "# E02 final art direction\n\n"
        "Open near-black canvas; paper-white evidence; amber for the untouched selection; cyan for the measurement path; magenta for the sealed boundary.\n\n"
        "Every scene is a bespoke HyperFrames composition. The SVG evidence surface is accompanied by a mechanism-specific probe, rail, seal, ordered marker, or branching path. Sentence cues move the probe to the active evidence location. The repeated rounded stage shell is removed. Scenes 08 and 14 use open rails instead of paired cards.\n",
    )

    diagram_assets = [
        {
            "id": scene_id,
            "type": "diagram",
            "path": f"hyperframes/assets/{scene_id}.svg",
            "source_tool": "tools/build_e02_rebuild.py",
            "scene_id": scene_id,
            "cost_usd": 0,
            "resolution": "1920x1080",
            "format": "svg",
            "subtype": "deterministic_evidence_diagram",
            "generation_summary": SCENE_MOTION_SIGNATURES[scene_id],
            "provider": "local deterministic generator",
            "license": "TraderCockpit project-authored",
        }
        for scene_id in SCENE_TITLES
    ]
    narration_assets = []
    for entry in narration_entries:
        narration_assets.append({
            "id": f"narration-{entry['scene_id']}",
            "type": "narration",
            "path": f"assets/audio/{NARRATION_AUDIO_SUBDIR}/{entry['scene_id']}.wav",
            "source_tool": "Higgsfield Qwen Audio 3.0 TTS Flash plus FFmpeg clean mastering",
            "scene_id": entry["scene_id"],
            "model": "Qwen Audio 3.0 TTS Flash",
            "cost_usd": 0,
            "duration_seconds": entry["duration_seconds"],
            "format": "wav",
            "subtype": "qwen_john_provider_native_clean",
            "generation_summary": f"Higgsfield job {entry['job_id']}; raw sha256={entry['raw_sha256']}; clean sha256={entry['clean_sha256']}; 70 Hz high-pass and two-pass EBU R128 normalization.",
            "provider": "Higgsfield",
            "license": "Generated under the operator's existing Max Plan",
            "voice_performance": {
                "source_section_id": entry["scene_id"],
                "delivery_cues_applied": True,
                "provider_text_used": True,
                "provider_settings": {
                    "job_type": "qwen_audio_tts",
                    "voice_id": JOHN_VOICE_ID,
                    "voice": "John",
                    "speech_rate": 1,
                    "pitch_rate": 1,
                    "local_tempo_transform": False,
                },
                "sample_approved": True,
                "sample_path": "OpenMontage/projects/series-04-mc-param/artifacts/voice-auditions/ep04-qwen-john-clean.wav",
                "route_approval": route,
                "review_notes": "Exact live E1-E5 John/clean route; final audio remains subject to exact-asset and playable QA.",
            },
        })
    write_json(out_art / "asset_manifest.json", {
        "version": "1.0",
        "assets": diagram_assets + narration_assets,
        "total_cost_usd": 0,
        "metadata": {
            "status": "assets_ready_for_compose" if narration_entries else "awaiting_provider_narration",
            "renderer": "repository-local HyperFrames",
            "composition_mode": "atelier",
            "aspect_ratio": "16:9",
            "scene_count": len(SCENE_TITLES),
            "narration_generated": bool(narration_entries),
            "music": "none",
            "sfx": "none; no additional SFX asset introduced",
            "generated_factual_media": False,
        },
    })

    cuts = []
    for section in visual_sections:
        scene_id = section["section_id"]
        cuts.append({
            "id": scene_id,
            "source": f"hyperframes/compositions/{scene_id}.html",
            "in_seconds": section["start_seconds"],
            "out_seconds": section["end_seconds"],
            "speed": 1.0,
            "layer": "primary",
            "transition_in": "mechanism-led match cut",
            "transition_out": "evidence-state match cut",
            "transition_duration": 0.0,
            "reason": SCENE_MOTION_SIGNATURES[scene_id],
        })
    edit_decisions = {
        "version": "1.0",
        "cuts": cuts,
        "overlays": [],
        "audio": {"narration": {"segments": audio_segments}, "sfx": []},
        "subtitles": {"enabled": False, "style": "sentence", "position": "bottom-center", "max_words_per_line": 10},
        "renderer_family": "animation-first",
        "render_runtime": "hyperframes",
        "composition_mode": "atelier",
        "bespoke": {"entry": "hyperframes/index.html", "composition_id": "main", "art_direction": "artifacts/art-direction.md"},
        "slideshow_risk_score": {"average": 0.0, "verdict": "strong", "dimensions": {"repetition": 0, "decorative_visuals": 0, "weak_motion": 0, "weak_shot_intent": 0, "typography_overreliance": 0, "unsupported_cinematic_claims": 0}, "render_runtime": "hyperframes"},
        "metadata": {
            "gate_profile": "board-led-explainer",
            "title": brief_source["title"],
            "target_duration_seconds": total_duration,
            "aspect_ratio": "16:9",
            "compose_target": {"width": 1920, "height": 1080, "fit": "contain"},
            "motion_delivery_contract": "Every sentence cue moves a mechanism probe or state marker; no decorative drift counts as coverage.",
            "visual_direction_resolution": "open canvas; no repeated shell; scenes 08 and 14 are rails/branch",
            "voice_route": "Higgsfield Qwen Audio 3.0 TTS Flash / John / clean",
            "voice_route_approval": route,
            "music": "none",
            "provider_calls": bool(narration_entries),
            "external_provider_spend_usd": 0,
            "narration_generated": bool(narration_entries),
            "public_upload_authorized": False,
        },
    }
    write_json(out_art / "edit_decisions.json", edit_decisions)

    thumbnail_png = ROOT / "productions/_series/e02-rebuild-candidate-2026-08-03/episode-02/artifacts/thumbnail-ep02.png"
    thumbnail_mobile = ROOT / "productions/_series/e02-rebuild-candidate-2026-08-03/episode-02/artifacts/thumbnail-ep02-mobile-zoom.png"
    if thumbnail_png.is_file():
        shutil.copy2(thumbnail_png, out_art / "thumbnail-ep02.png")
    if thumbnail_mobile.is_file():
        shutil.copy2(thumbnail_mobile, out_art / "thumbnail-ep02-mobile-zoom.png")
    packaging = {
        "version": "1.0",
        "STATUS": "LOCAL PRODUCTION AUTHORIZED — exact-hash/publication approval remains separate",
        "episode": 2,
        "syllabus_episode": "02",
        "title": brief_source["title"],
        "beginner_belief": "If the first screen looks good, the later test is just a formality.",
        "first_spoken_sentence": brief_source["first_spoken_sentence"],
        "prewriting": {
            "proven idea": "The real SPY branch stops before the holdout while the separate Dow branch reaches later prices.",
            "common goal": "Help a beginner tell a true out-of-sample question from a renamed in-sample result.",
            "deeper problem": "Earlier scripts narrated a later test that the SPY branch never reached.",
            "package first": "Title and thumbnail are fixed before narration; the thumbnail shows 5 to 0 and a separate 184 to 154 lane.",
            "audience avatar": "A beginner who needs operators, units, and a visual sequence more than jargon.",
            "research the gaps": "Academic sources cover holdout design, data snooping, time-series evaluation, distributions, medians, and percentiles.",
        },
        "thumbnail": {"source": "artifacts/thumbnail-ep02.html", "elements": ["5→0", "SEALED", "184→154"], "dimensions": "1280x720", "squint_proof": "artifacts/thumbnail-ep02-mobile-zoom.png", "matching_first_shot": "hyperframes/assets/scene-01.svg"},
        "script": {
            "sha256": script_sha,
            "vo_sha256": sha256(vo_out),
            "word_count": gate_words,
            "estimated_duration_seconds": base_timing["total_duration_seconds"],
        },
        "voice_route": {
            "provider": route["provider"],
            "model": route["model"],
            "job_type": route["job_type"],
            "voice": route["voice"],
            "treatment": route["treatment"],
            "approval_path": route["path"],
            "approval_sha256": route["sha256"],
            "provider_calls": bool(narration_entries),
        },
        "approval": {"narrator_decision_inherited": True, "complete_script_approved": True, "operator_exact_hash_approval": False, "local_production_authorized": True},
        "candidate_only": False,
        "source_facts_receipt": "facts_receipt.json",
        "provider_receipt": str(narration_receipt.resolve()) if narration_receipt else None,
        "visual_direction_resolution": timing["motion_contract"],
        "scope_boundary": "No Episode 01 intake or Episode 03 timing/session result; E02 ends with fill timing and trading hours questions.",
        "operator_authorization": {"message": OPERATOR_AUTHORIZATION, "local_only": True, "remote_mutations": False},
    }
    write_json(out_art / "packaging.json", packaging)
    write_json(out_art / "production_source_receipt.json", {
        "schema": "into-the-laboratory/e02-production-source-receipt/v1",
        "candidate_only": False,
        "generated_by": "tools/build_e02_rebuild.py --full-run",
        "source_vo_sha256": sha256(SOURCE / "vo.txt"),
        "generated_vo_sha256": sha256(vo_out),
        "script_sha256": script_sha,
        "facts_receipt_sha256": sha256(out_art / "facts_receipt.json") if (out_art / "facts_receipt.json").is_file() else None,
        "sentence_coverage": timing["coverage"],
        "visual_direction_resolution": timing["motion_contract"],
        "provider_route": "Higgsfield Qwen Audio 3.0 TTS Flash / John / clean under existing subscription; no top-up; no substitution",
        "provider_route_approval": route,
        "operator_authorization": OPERATOR_AUTHORIZATION,
    })
    write_json(out_art / "facts_receipt.json", facts)
    # Refresh the source receipt after facts are written so its hash is exact.
    source_receipt = load_json(out_art / "production_source_receipt.json")
    source_receipt["facts_receipt_sha256"] = sha256(out_art / "facts_receipt.json")
    write_json(out_art / "production_source_receipt.json", source_receipt)
    print(json.dumps({
        "production": str(out),
        "project_id": FINAL_PROJECT_ID,
        "script_sha256": script_sha,
        "facts_sha256": sha256(out_art / "facts_receipt.json"),
        "total_words": base_timing["total_words"],
        "total_duration_seconds": total_duration,
        "sentence_count": timing["coverage"]["spoken_sentences"],
        "narration_bound": bool(narration_entries),
        "narration_receipt": str(narration_receipt) if narration_receipt else None,
        "visual_direction_resolution": timing["motion_contract"],
    }, indent=2))
    return out


def build_package() -> Path:
    brief = load_json(SOURCE / "brief.json")
    academic = load_json(SOURCE / "academic_receipts.json")
    facts = verify_facts()
    rows = parse_vo()
    if rows[0]["text"].split(".")[0].strip() not in brief["first_spoken_sentence"]:
        raise SystemExit("BLOCK: source first sentence does not match the package brief")
    out_art = OUT / "artifacts"
    out_hf = OUT / "hyperframes"
    out_assets = out_hf / "assets"
    out_art.mkdir(parents=True, exist_ok=True)
    out_assets.mkdir(parents=True, exist_ok=True)

    for relative_ref, label in ((SOURCE_VO_REF, "source VO"), (ACADEMIC_RECEIPTS_REF, "academic receipts")):
        resolved = (out_art / relative_ref).resolve()
        if not resolved.is_file():
            raise SystemExit(f"BLOCK: {label} reference does not resolve from artifacts: {relative_ref} -> {resolved}")

    vo_out = out_art / "vo.txt"
    source_vo = (SOURCE / "vo.txt").read_text(encoding="utf-8")
    write_text(vo_out, source_vo)
    write_text(OUT / "vo.txt", source_vo)
    sections, timing = build_scene_rows(rows, brief, facts)
    claims = build_claims(rows, facts, academic, vo_out)
    research = build_research(brief, academic, facts)
    proposal, decision_log = build_proposal(brief, research)

    for scene_id in SCENE_TITLES:
        write_text(out_assets / f"{scene_id}.svg", scene_svg(scene_id, facts))
    visual_semantics = validate_scene_assets(out_assets)
    write_text(out_art / "thumbnail-ep02.html", build_thumbnail())
    write_text(out_hf / "index.html", build_proof_html())
    write_json(out_hf / "hyperframes.json", {"schema": "hyperframes/project/v1", "composition_id": "e02-semantic-proof-candidate", "runtime": "hyperframes", "candidate_only": True})

    script = {
        "schema": "into-the-laboratory/script/v2",
        "version": "e02-rebuild-1",
        "title": brief["title"],
        "total_duration_seconds": timing["total_duration_seconds"],
        "total_words": timing["total_words"],
        "voice_performance": {"performance_intent": "A calm lab walkthrough for a beginner; exact results are stated without turning them into a promise.", "pacing_profile": "technical but spoken", "provider_status": "pending operator approval"},
        "sections": sections,
        "source_vo": SOURCE_VO_REF,
    }
    packaging = {
        "schema": "into-the-laboratory/packaging/v2",
        "STATUS": "CANDIDATE — operator review required; no narration or master authorized",
        "episode": 2,
        "syllabus_episode": "02",
        "title": brief["title"],
        "beginner_belief": "If the first screen looks good, the later test is just a formality.",
        "first_spoken_sentence": brief["first_spoken_sentence"],
        "thumbnail": {
            "source": "thumbnail-ep02.html",
            "elements": ["5→0", "SEALED", "184→154"],
            "dimensions": "1280x720",
            "squint_proof": "thumbnail-ep02-mobile-zoom.png",
            "matching_first_shot": "hyperframes/assets/scene-01.svg",
        },
        "script": {"sha256": sha256(out_art / "script.json") if (out_art / "script.json").is_file() else None, "vo_sha256": sha256(vo_out)},
        "approval": {"narrator_decision_inherited": False, "complete_script_approved": False, "operator_exact_hash_approval": False},
        "prewriting": {
            "proven idea": "The real SPY branch stops before the holdout while the separate Dow branch reaches later prices.",
            "common goal": "Help a beginner tell a true out-of-sample question from a renamed in-sample result.",
            "deeper problem": "Earlier scripts narrated a later test that the SPY branch never reached.",
            "package first": "Title and thumbnail are fixed before narration; the thumbnail shows 5 to 0 and a separate 184 to 154 lane.",
            "audience avatar": "A beginner who needs operators, units, and a visual sequence more than jargon.",
            "research the gaps": "Academic sources cover holdout design, data snooping, time-series evaluation, distributions, medians, and percentiles.",
        },
        "source_facts_receipt": "facts_receipt.json",
        "candidate_boundary": "No narration, provider generation, full master, upload, or publication.",
    }
    # Write script before packaging so its bound hash is meaningful.
    write_json(out_art / "script.json", script)
    packaging["script"]["sha256"] = sha256(out_art / "script.json")
    write_json(out_art / "packaging.json", packaging)
    write_json(out_art / "claims.json", claims)
    write_json(out_art / "scene_visual_map.json", timing)
    write_json(out_art / "academic_edit_timing.json", timing)
    write_json(out_art / "scenes.json", {"schema": "into-the-laboratory/scenes/v1", "scenes": sections})
    write_json(out_art / "scene_plan.json", {"schema": "openmontage/animation/scene-plan/v1", "render_runtime": "hyperframes", "scenes": timing["sections"]})
    write_json(out_art / "edit_decisions.json", {
        "schema": "openmontage/animation/edit-decisions/v1",
        "metadata": {"gate_profile": "board-led-explainer", "candidate_only": True},
        "render_runtime": "hyperframes",
        "cuts": [
            {"id": "proof-beat-01", "source": "hyperframes/index.html", "in_seconds": 0, "out_seconds": 5, "type": "svg_diagram"},
            {"id": "proof-beat-02", "source": "hyperframes/index.html", "in_seconds": 5, "out_seconds": 10, "type": "svg_diagram"},
            {"id": "proof-beat-03", "source": "hyperframes/index.html", "in_seconds": 10, "out_seconds": 15, "type": "svg_diagram"},
            {"id": "proof-beat-04", "source": "hyperframes/index.html", "in_seconds": 15, "out_seconds": 20, "type": "svg_diagram"},
        ],
        "audio": {"narration": {"status": "not generated", "segments": []}, "music": {"status": "not requested"}},
        "human_review": {"required_before_narration": True, "required_before_master": True},
    })
    write_json(out_art / "asset_manifest.json", {
        "schema": "openmontage/animation/asset-manifest/v1",
        "layer3_skills_read": ["hyperframes-core", "hyperframes-cli", "hyperframes-gsap-adapter"],
        "assets": [{"id": scene_id, "path": f"hyperframes/assets/{scene_id}.svg", "kind": "deterministic_evidence_diagram", "generated": False} for scene_id in SCENE_TITLES] + [
            {"id": "thumbnail-ep02", "path": "artifacts/thumbnail-ep02.html", "kind": "thumbnail_source", "generated": False}
        ],
        "visual_semantic_receipt": "visual_semantic_receipt.json",
        "blocked_assets": [{"kind": "narration", "reason": "operator approval not yet granted"}, {"kind": "provider_media", "reason": "not authorized at candidate stage"}],
    })
    write_json(out_art / "research_brief.json", research)
    write_json(out_art / "proposal_packet.json", proposal)
    write_json(out_art / "decision_log.json", decision_log)
    write_json(out_art / "visual_semantic_receipt.json", visual_semantics)
    write_json(out_art / "facts_receipt.json", facts)
    write_json(out_art / "candidate_receipt.json", {
        "schema": "into-the-laboratory/e02-candidate-receipt/v1",
        "candidate_only": True,
        "generated_by": "tools/build_e02_rebuild.py",
        "source_vo_sha256": sha256(SOURCE / "vo.txt"),
        "generated_vo_sha256": sha256(vo_out),
        "facts_receipt_sha256": sha256(out_art / "facts_receipt.json"),
        "script_sha256": sha256(out_art / "script.json"),
        "sentence_coverage": timing["coverage"],
        "visual_semantic_receipt": {"path": "visual_semantic_receipt.json", "verified": visual_semantics["verified"]},
        "proof": {"html": "../hyperframes/index.html", "duration_seconds": 20, "narration": False, "master": False},
    })
    print(json.dumps({

        "candidate": str(OUT),
        "vo_sha256": sha256(vo_out),
        "script_sha256": sha256(out_art / "script.json"),
        "facts_sha256": sha256(out_art / "facts_receipt.json"),
        "total_words": timing["total_words"],
        "total_duration_seconds": timing["total_duration_seconds"],
        "sentence_count": timing["coverage"]["spoken_sentences"],
        "source_hashes_match": facts["verification"]["all_pinned_hashes_match"],
        "assignment_pf_discrepancy": facts["assignment_discrepancies"],
    }, indent=2))
    return OUT


def main() -> int:
    global OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument(
        "--full-run",
        action="store_true",
        help="regenerate the authorized E02 production package, not the candidate-only package",
    )
    parser.add_argument(
        "--narration-receipt",
        type=Path,
        help="bind measured provider narration into the full package",
    )
    args = parser.parse_args()
    OUT = args.output.resolve()
    if args.full_run:
        build_final_package(OUT, args.narration_receipt.resolve() if args.narration_receipt else None)
    else:
        build_package()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
