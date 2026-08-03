#!/usr/bin/env python3
"""Build the deterministic visual companion for the Episode 1-3 rewrite candidate.

The source run files are read-only. This tool only writes new SVGs and a hash-bound receipt under
productions/_series. It deliberately reuses the house SVG primitives from build_series_math_visuals
instead of introducing a second visual system.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_series_math_visuals import (
    GOLD,
    GREEN,
    GRID,
    MUTED,
    PANEL,
    RED,
    TEXT,
    _line,
    _rect,
    _sha,
    _svg,
    _t,
    _write,
)

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "productions" / "_series" / "e01-e03-live-receipts-2026-08-03.json"
OUT = ROOT / "productions" / "_series" / "visual-rebuild-previews"
def _manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _source_check(manifest: dict) -> dict[str, Path]:
    """Check every external source hash before drawing any factual mark."""
    paths: dict[str, Path] = {}
    for episode in manifest["episodes"].values():
        candidates = []
        if isinstance(episode, dict):
            candidates.extend(episode.get("runs", []))
            candidates.extend([episode.get("stock_branch", {}), episode.get("dow_oos_branch", {})])
            if episode.get("source_path"):
                candidates.append(episode)
        for item in candidates:
            if not isinstance(item, dict) or not item.get("source_path"):
                continue
            path = Path(item["source_path"])
            if not path.is_file():
                raise FileNotFoundError(path)
            actual = _sha(path)
            expected = item.get("sha256") or item.get("phase01_sha256") or item.get("phase02_sha256")
            if expected and actual != expected:
                raise ValueError(f"source hash drift: {path} expected {expected}, got {actual}")
            paths[item["source_path"]] = path
        stock = episode.get("stock_branch") if isinstance(episode, dict) else None
        if stock:
            for path_key, hash_key in (("phase01_source_path", "phase01_sha256"),
                                       ("phase02_source_path", "phase02_sha256")):
                path = Path(stock[path_key])
                if not path.is_file():
                    raise FileNotFoundError(path)
                if _sha(path) != stock[hash_key]:
                    raise ValueError(f"source hash drift: {path}")
                paths[str(path)] = path
        shared = episode.get("next_phase") if isinstance(episode, dict) else None
        if shared and shared.get("source_sha256"):
            path = Path(r"C:\Users\MSI\repos\futures\runtime\validation\robustness\rb-20260725T133803-b44bd92c\phases\phase04_cost.json")
            if _sha(path) != shared["source_sha256"]:
                raise ValueError(f"source hash drift: {path}")
            paths[str(path)] = path
    return paths


def _bar(x: float, y: float, width: float, height: float, value: float, maximum: float,
         label: str, value_text: str, color: str) -> list[str]:
    length = max(0.0, width * value / maximum) if maximum else 0.0
    return [
        _t(x, y - 18, label, 24, MUTED, weight=700),
        _rect(x, y, width, height, GRID, GRID, 8),
        _rect(x, y, length, height, color, color, 8, 0.88),
        _t(x + width + 24, y + height - 9, value_text, 30, color, weight=800),
    ]


def _e01_pipeline() -> str:
    body = [_rect(110, 265, 1700, 560), _t(150, 330, "ONE CANDIDATE / ONE COMPLETE RULE SET", 24, GOLD, weight=800)]
    steps = [
        (220, "OBSERVE", "question"),
        (550, "SPECIFY", "entry · exit · fill"),
        (880, "REPLAY", "old prices"),
        (1210, "GATE", "metric + threshold"),
        (1540, "NEXT TEST", "only survivors"),
    ]
    for index, (x, title, sub) in enumerate(steps):
        body += [_rect(x - 115, 420, 230, 150, PANEL, GOLD if title == "GATE" else GRID, 16)]
        body += [_t(x, 480, title, 28, TEXT, "middle", 800), _t(x, 525, sub, 21, MUTED, "middle")]
        if index < len(steps) - 1:
            body += [_line(x + 118, 495, steps[index + 1][0] - 118, 495, GOLD, 4)]
    body += [
        _t(210, 680, "data source", 22, MUTED), _t(410, 680, "REAL", 28, GREEN, weight=800),
        _t(750, 680, "wiring proof", 22, MUTED), _t(930, 680, "TRUE", 28, GREEN, weight=800),
        _t(1260, 680, "validated", 22, MUTED), _t(1430, 680, "FALSE", 28, RED, weight=800),
        _t(960, 775, "pipeline evidence ≠ live-performance proof", 30, TEXT, "middle", 700),
    ]
    return _svg(
        "THE FIRST SCREEN IS A DECISION PIPELINE",
        "COMPLETE RULES → HISTORICAL REPLAY → DECLARED GATE → NEXT TEST",
        body,
        "METHOD DIAGRAM · FLAGS PRESERVED FROM THE RECORDED RUNS",
    )


def _e01_lanes(manifest: dict) -> str:
    runs = manifest["episodes"]["01"]["runs"]
    body = [_rect(110, 245, 1700, 690), _t(160, 315, "ENTERING", 22, MUTED, weight=700),
            _t(1450, 315, "CARRIED FORWARD", 22, MUTED, "middle", 700)]
    y_values = [390, 560, 730]
    max_value = max(row["entering"] for row in runs)
    for row, y in zip(runs, y_values):
        label = row["label"].upper()
        body += [_t(160, y - 28, label, 28, TEXT, weight=800),
                 _t(160, y + 34, f'{row["window"]["start"]} → {row["window"]["end"]}', 20, MUTED)]
        body += [_rect(520, y - 42, 700, 74, GRID, GRID, 10),
                 _rect(520, y - 42, 700 * row["entering"] / max_value, 74, GOLD, GOLD, 10, 0.82),
                 _t(1245, y + 10, f'{row["entering"]:,}', 34, GOLD, weight=800)]
        body += [_line(1420, y - 5, 1650, y - 5, GRID, 12),
                 _line(1420, y - 5, 1420 + 230 * row["surviving"] / max(1, row["entering"]), y - 5,
                       GREEN if row["surviving"] else RED, 12),
                 _t(1700, y + 10, f'{row["surviving"]:,}', 34, GREEN if row["surviving"] else RED, weight=800)]
    body += [_t(960, 875, "5,390 entering across three run-specific libraries", 34, TEXT, "middle", 800),
             _t(960, 915, "184 forward · 0 S&P futures · 0 EURUSD", 26, MUTED, "middle")]
    return _svg(
        "THREE REAL RUNS / ONE NARROW SURVIVOR LANE",
        "THE COUNTS ARE AGGREGATED FOR THE LESSON; WINDOWS AND RUN IDENTITIES STAY SEPARATE",
        body,
        "RUN DATA · DOW 1,335→184 · S&P 500 FUTURES 2,004→0 · EURUSD 2,051→0",
    )


def _e01_gates(manifest: dict) -> str:
    census = manifest["episodes"]["01"]["dow_gate_census"]
    body = [_rect(110, 245, 1700, 690), _t(160, 315, "DOW FIRST SCREEN", 26, GOLD, weight=800),
            _t(160, 365, "1,335 entering", 42, TEXT, weight=800), _line(160, 405, 1760, 405, GRID, 3)]
    for y, label, value, text, color in [
        (490, "RETURN / DRAWDOWN", census["failed_return_to_drawdown"], "1,122", RED),
        (625, "PROFIT FACTOR", census["failed_profit_factor"], "1,065", RED),
        (760, "ACTIVITY", census["failed_activity"], "150", RED),
    ]:
        body += _bar(230, y, 1040, 62, value, 1335, label, text, color)
    body += [_rect(1450, 500, 240, 210, PANEL, GREEN, 18),
             _t(1570, 575, "184", 62, GREEN, "middle", 850),
             _t(1570, 625, "ADVANCE", 24, TEXT, "middle", 800),
             _t(1570, 665, "1,151 dropped", 20, MUTED, "middle"),
             _t(960, 875, "FAILURE COUNTS OVERLAP · DO NOT ADD THE THREE BARS", 28, GOLD, "middle", 800)]
    return _svg(
        "THE DOW GATE HAS OVERLAPPING FAILURE MODES",
        "A CANDIDATE CAN FAIL RETURN/DD, PROFIT FACTOR, ACTIVITY, OR MORE THAN ONE",
        body,
        "RUN DATA · GATE CENSUS FROM DOW PHASE01 · 1,151 DROPPED / 184 ADVANCE",
    )


def _e01_ledger(manifest: dict) -> str:
    candidate = manifest["episodes"]["01"]["dow_candidate_examples"]["is_survivor"]
    body = [_rect(110, 250, 800, 630), _rect(1010, 250, 800, 630),
            _t(160, 320, "ONE RECORDED DOW CANDIDATE", 26, GOLD, weight=800),
            _t(160, 375, candidate["candidate_id"], 22, MUTED),
            _t(160, 470, "NET", 22, MUTED), _t(460, 470, f'${candidate["net"]:,.2f}', 42, GREEN, weight=800),
            _t(160, 550, "PROFIT FACTOR", 22, MUTED), _t(460, 550, f'{candidate["profit_factor"]:.6f}', 42, GREEN, weight=800),
            _t(160, 630, "RETURN / DRAWDOWN", 22, MUTED), _t(460, 630, f'{candidate["return_to_drawdown"]:.6f}', 42, GREEN, weight=800),
            _t(160, 710, "TRADES", 22, MUTED), _t(460, 710, f'{candidate["trades"]:,}', 42, TEXT, weight=800),
            _t(1060, 320, "NEXT PHASE / SAME CANDIDATE", 26, GOLD, weight=800),
            _t(1060, 410, "DEVELOPMENT", 22, MUTED), _t(1450, 410, "OUT-OF-SAMPLE", 22, MUTED),
            _t(1060, 495, "$16,727.80", 42, GREEN, weight=800), _t(1450, 495, "-$4,897.40", 42, RED, weight=800),
            _line(1120, 575, 1690, 575, GOLD, 5), _t(1405, 650, "1,280370 → 0.813381 PF", 30, TEXT, "middle", 800),
            _t(1405, 725, "survivor means passed the previous gate", 22, MUTED, "middle"),
            _t(960, 920, "A GOOD FIRST ROW IS A QUESTION FOR THE NEXT PHASE", 28, GOLD, "middle", 800)]
    return _svg(
        "ONE SURVIVOR / TWO DIFFERENT HISTORICAL ANSWERS",
        "THE FIRST-SCREEN ROW IS REAL; THE LATER STATUS IS ALSO REAL",
        body,
        "RUN DATA · DOW CANDIDATE formula-2851293728-1566 · E01→E02 BRIDGE",
    )


def _e02_spy_boundary(manifest: dict) -> str:
    spy = manifest["episodes"]["02"]["stock_branch"]
    body = [_rect(110, 245, 1700, 690), _t(160, 320, "SPY / D1 / CONNORS RSI2", 30, GOLD, weight=800),
            _t(160, 370, "1996-07-12 → 2011-05-26", 22, MUTED),
            _line(260, 560, 1430, 560, GRID, 16), _line(260, 560, 1430, 560, GOLD, 16),
            _t(260, 500, "5 ENTER", 34, GOLD, weight=800),
            _line(1430, 560, 1650, 560, GRID, 16, "16 14"),
            _t(1500, 500, "0 SURVIVE", 34, RED, weight=800),
            _line(1430, 650, 1650, 650, MUTED, 4, "10 10"),
            _t(1430, 720, "HOLDOUT NOT REACHED", 28, MUTED, weight=800),
            _t(160, 810, "phase02 entering: 0", 26, TEXT, weight=800),
            _t(160, 855, "phase02 surviving: 0", 26, TEXT, weight=800),
            _t(1060, 810, "REAL DATA", 26, GREEN, weight=800),
            _t(1060, 855, "WIRING PROOF TRUE · VALIDATED FALSE", 24, RED, weight=800),
            _t(960, 905, "The empty phase is a recorded boundary, not an unseen-price result.", 24, TEXT, "middle")]
    return _svg(
        "THE SPY BRANCH STOPS BEFORE THE HOLDOUT",
        "5 CANDIDATES ENTERED · 0 WERE ADOPTED · OOS WAS SKIPPED",
        body,
        "RUN DATA · rb-20260714T113408-b5d06cc6 · PHASE02 NOTE: NO ADOPTABLE CANDIDATES",
    )


def _e02_spy_row(manifest: dict) -> str:
    row = manifest["episodes"]["02"]["stock_branch"]["candidate_example"]
    body = [_rect(110, 245, 1700, 690), _t(160, 320, row["candidate_id"], 26, GOLD, weight=800),
            _t(160, 375, "ONE OF FIVE ENTERING CANDIDATE ROWS", 22, MUTED)]
    columns = [
        (300, "PROFIT FACTOR", f'{row["profit_factor"]:.6f}', f'> {row["profit_factor_threshold"]}', RED),
        (850, "RETURN / DRAWDOWN", f'{row["return_to_drawdown"]:.6f}', f'> {row["return_to_drawdown_threshold"]}', RED),
        (1400, "TRADES / MONTH", f'{row["trades_per_month"]:.6f}', f'> {row["trades_per_month_threshold"]}', RED),
    ]
    for x, label, actual, threshold, color in columns:
        body += [_line(x, 475, x, 780, GRID, 4), _t(x, 515, label, 22, MUTED, "middle", 700),
                 _t(x, 650, actual, 42, color, "middle", 850), _t(x, 710, threshold, 26, TEXT, "middle", 800),
                 _t(x, 760, "FAIL", 24, color, "middle", 850)]
    body += [_t(960, 875, "the threshold turns a raw metric into a gate decision", 28, GOLD, "middle", 800)]
    return _svg(
        "ONE ACTUAL SPY ROW / THREE ACTUAL FAILURES",
        "SHOW THE VALUE BESIDE THE THRESHOLD; DO NOT SUBSTITUTE A TEACHING EXAMPLE",
        body,
        "RUN DATA · SPY PHASE01 CANDIDATE ROW · ALL THREE DISPLAYED GATES FAIL",
    )


def _e02_dow_oos(manifest: dict) -> str:
    dow = manifest["episodes"]["02"]["dow_oos_branch"]
    row = dow["candidate_example"]
    body = [_rect(110, 245, 790, 690, PANEL, RED, 18), _rect(1010, 245, 800, 690, PANEL, GREEN, 18),
            _t(160, 330, "SPY BRANCH", 28, RED, weight=800), _t(160, 410, "5 → 0", 72, RED, weight=850),
            _t(160, 500, "holdout not reached", 28, TEXT, weight=800),
            _t(160, 555, "separate stock run", 22, MUTED),
            _t(1060, 330, "DOW OOS BRANCH", 28, GREEN, weight=800), _t(1060, 410, "184 → 154", 72, GREEN, weight=850),
            _t(1060, 500, "30 dropped", 28, TEXT, weight=800),
            _t(1060, 555, f'{row["candidate_id"]}: PF {row["is_profit_factor"]:.6f} → {row["oos_profit_factor"]:.6f}', 22, MUTED),
            _t(960, 785, "TWO BRANCHES / ONE HOLDOUT DEFINITION", 34, GOLD, "middle", 850),
            _t(960, 845, "never blend the stock stop with the futures continuation", 24, TEXT, "middle")]
    return _svg(
        "A HOLDOUT EXAMPLE EXISTS IN THE DOW BRANCH",
        "SPY STOPS AT INTAKE · DOW REACHES A LATER PRICE BLOCK",
        body,
        "RUN DATA · SPY 5→0 AND DOW 184→154 ARE SEPARATE RECEIPTS",
    )


def _e03_three_views(manifest: dict) -> str:
    ep = manifest["episodes"]["03"]
    body = [_rect(110, 245, 1700, 690), _t(160, 315, "154 CANDIDATES ENTER", 28, GOLD, weight=800),
            _line(300, 485, 1620, 485, GRID, 10), _t(300, 440, "ONE BAR LATER", 23, MUTED),
            _t(760, 440, "SESSION HALF 1", 23, MUTED), _t(1220, 440, "SESSION HALF 2", 23, MUTED)]
    for x, label, value in [(390, "DELAY", 66), (850, "HALF 1", 41), (1310, "HALF 2", 23)]:
        body += [_line(x, 485, x, 700, RED, 14), _t(x, 745, f'{value} FAIL', 34, RED, "middle", 850),
                 _t(x, 790, label, 22, MUTED, "middle")]
    body += [_rect(1450, 330, 240, 185, PANEL, GREEN, 18), _t(1570, 405, "53", 58, GREEN, "middle", 850),
             _t(1570, 460, "PASS ALL", 23, TEXT, "middle", 800),
             _t(960, 865, "101 FAIL AT LEAST ONE · FAILURE COUNTS OVERLAP · 53 CLEAR ALL THREE", 27, GOLD, "middle", 850)]
    return _svg(
        "ONE POPULATION / THREE EXPLICIT VIEWS",
        "DELAYED ENTRY + SESSION HALF 1 + SESSION HALF 2",
        body,
        "RUN DATA · DOW PHASE03 · 154→53 · 66/41/23 FAILURE CENSUS",
    )


def _e03_rows(manifest: dict) -> str:
    examples = manifest["episodes"]["03"]["candidate_examples"]
    fail = examples["failed_session_half_1"]
    passed = examples["passes_all_three"]
    body = [_rect(110, 245, 1700, 690), _t(160, 320, "RECORDED CANDIDATE ROWS", 28, GOLD, weight=800),
            _t(160, 375, "same three checks · exact receipt values shown", 22, MUTED),
            _rect(150, 430, 320, 310, PANEL, RED, 16), _rect(150, 760, 320, 125, PANEL, GREEN, 16),
            _t(310, 485, "VETO ROW", 24, RED, "middle", 850),
            _t(310, 545, fail["candidate_id"], 18, TEXT, "middle", 700),
            _t(310, 820, "PASS ROW", 24, GREEN, "middle", 850),
            _t(310, 865, passed["candidate_id"], 18, TEXT, "middle", 700)]
    labels = [("DELAY 1 BAR", "pf_entry_delay_1bar"), ("SESSION HALF 1", "pf_session_half_1"), ("SESSION HALF 2", "pf_session_half_2")]
    for index, (label, key) in enumerate(labels):
        x = 650 + index * 360
        fail_color = RED if key == "pf_session_half_1" else GREEN
        body += [_line(x, 445, x, 890, GRID, 3), _t(x, 500, label, 22, MUTED, "middle", 700),
                 _t(x, 610, f'{fail[key]:.6f}', 34, fail_color, "middle", 850),
                 _t(x, 665, "veto row", 19, RED if fail_color == RED else MUTED, "middle", 700),
                 _t(x, 805, f'{passed[key]:.6f}', 34, GREEN, "middle", 850),
                 _t(x, 860, "pass row", 19, GREEN, "middle", 700),
                 _line(x - 88, 708, x + 88, 708, GOLD, 3),
                 _t(x, 740, "threshold 1.000000", 18, TEXT, "middle")]
    body += [_t(1110, 930, "ONE WEAK VIEW VETOES THE CANDIDATE · COUNTS STAY BOUND TO THE RECEIPT", 24, GOLD, "middle", 850)]
    return _svg(
        "THE NUMBERS ARE RECORDED ROWS, NOT ILLUSTRATIONS",
        "ONE SESSION-HALF VETO CAN STOP A CANDIDATE THAT PASSES THE OTHER TWO VIEWS",
        body,
        "RUN DATA · formula-2309285457-3105 VS formula-2309285457-3088",
    )


def _e03_pf() -> str:
    body = [_rect(110, 245, 1700, 690),
            _t(960, 345, "PROFIT FACTOR", 34, GOLD, "middle", 850),
            _t(960, 485, "gross winning dollars", 44, GREEN, "middle", 800),
            _t(960, 555, "────────────────────────", 34, MUTED, "middle"),
            _t(960, 635, "gross losing dollars", 44, RED, "middle", 800),
            _t(540, 785, "0.986603", 42, RED, "middle", 850), _t(540, 835, "session half 1 / veto", 24, TEXT, "middle"),
            _t(1380, 785, "1.156412", 42, GREEN, "middle", 850), _t(1380, 835, "session half 1 / pass row", 24, TEXT, "middle"),
            _t(960, 900, "threshold = 1.000000", 28, GOLD, "middle", 850)]
    return _svg(
        "THE GATE IS AN ALGEBRAIC COMPARISON",
        "PF > 1 MEANS WINNING DOLLARS EXCEED LOSING DOLLARS ON THAT SPECIFIED LEDGER",
        body,
        "METHOD + RUN ROWS · PROFIT FACTOR DEFINITION WITH RECORDED VALUES",
    )


def _e03_handoff(manifest: dict) -> str:
    next_phase = manifest["episodes"]["03"]["next_phase"]
    body = [_rect(110, 245, 1700, 690), _t(160, 315, "PHASE03 OUTPUT", 26, GOLD, weight=800),
            _line(290, 490, 1560, 490, GOLD, 8), _t(290, 440, "154", 54, TEXT, "middle", 850),
            _t(870, 440, "53", 54, GREEN, "middle", 850), _t(1560, 440, "PHASE04", 38, GOLD, "middle", 850),
            _t(290, 560, "OOS", 24, MUTED, "middle"), _t(870, 560, "PASS ALL THREE", 24, GREEN, "middle", 800),
            _t(1560, 560, "COST STRESS", 24, MUTED, "middle", 800),
            _t(460, 725, "53 ENTER", 32, TEXT, "middle", 800), _t(960, 725, "7 FAIL NET AT 3×", 32, RED, "middle", 800),
            _t(1460, 725, "46 PASS BOTH", 32, GREEN, "middle", 800),
            _t(960, 850, "a survivor is the next question, never the final answer", 30, GOLD, "middle", 850)]
    return _svg(
        "THE 53 ARE A HANDOFF, NOT A FINISH LINE",
        "PHASE03 NARROWS THE POPULATION; PHASE04 TESTS THE SAME LEDGER UNDER COST STRESS",
        body,
        "RUN DATA · PHASE04 BRIDGE · 53→46 WITH 7 NET-PROFIT FAILURES AT 3×",
    )


def build(out: Path) -> dict:
    manifest = _manifest()
    sources = _source_check(manifest)
    visuals = {
        "e01-pipeline-map.svg": _e01_pipeline(),
        "e01-run-lanes.svg": _e01_lanes(manifest),
        "e01-dow-gate-census.svg": _e01_gates(manifest),
        "e01-candidate-ledger.svg": _e01_ledger(manifest),
        "e02-spy-boundary.svg": _e02_spy_boundary(manifest),
        "e02-spy-candidate-row.svg": _e02_spy_row(manifest),
        "e02-dow-oos-bridge.svg": _e02_dow_oos(manifest),
        "e03-three-view-funnel.svg": _e03_three_views(manifest),
        "e03-veto-vs-pass.svg": _e03_rows(manifest),
        "e03-profit-factor.svg": _e03_pf(),
        "e03-cost-handoff.svg": _e03_handoff(manifest),
    }
    for name, svg in visuals.items():
        _write(out / name, svg)
    receipt = {
        "schema": "series-e01-e03-rewrite-visuals/v1",
        "generated_from": str(MANIFEST.relative_to(ROOT)).replace("\\", "/"),
        "manifest_sha256": _sha(MANIFEST),
        "sources": {path: _sha(source) for path, source in sorted(sources.items())},
        "outputs": {name: _sha(out / name) for name in visuals},
        "labels": {
            "run_data": [name for name in visuals if name not in {"e01-pipeline-map.svg", "e03-profit-factor.svg"}],
            "derived_or_method": ["e01-pipeline-map.svg", "e03-profit-factor.svg"],
            "illustrative": [],
        },
        "quality_boundary": "All factual numbers are drawn from the tracked manifest; no generative media or generic card component is used.",
    }
    _write(out / "e01-e03-rewrite-visual-receipt.json", json.dumps(receipt, indent=2) + "\n")
    return receipt


def demo() -> None:
    manifest = _manifest()
    assert manifest["episodes"]["01"]["aggregate"]["rejected"] == 5206
    assert manifest["episodes"]["02"]["stock_branch"]["phase01_surviving"] == 0
    assert manifest["episodes"]["03"]["surviving"] == 53
    assert _e03_pf().startswith("<svg")
    print("PASS: rewrite visual math and provenance fixtures are internally consistent")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        demo()
        return 0
    receipt = build(args.out)
    print(f"wrote {len(receipt['outputs'])} rewrite visuals and receipt to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
