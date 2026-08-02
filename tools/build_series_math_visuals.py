#!/usr/bin/env python
"""Build factual 16:9 math visuals for Into the Laboratory episodes 1-4.

The run artifact is read-only. Every generated SVG says whether it is run data,
derived arithmetic, or illustrative geometry. A JSON receipt binds outputs to
the exact source files and hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "rb-20260725T133803-b44bd92c"
GOLDEN_RUN_ID = "rb-20260715T094910-d0d18d9a"
FUTURES = Path(r"C:\Users\MSI\repos\futures")
PHASES = FUTURES / "runtime" / "validation" / "robustness" / RUN_ID / "phases"
GOLDEN_PHASES = (
    FUTURES / "runtime" / "validation" / "robustness" / GOLDEN_RUN_ID / "phases"
)
CODE_GRAPH = Path(r"C:\Users\MSI\.graphify\futures\graphify-out\graph.json")
OPS_GRAPH = Path(
    r"C:\Users\MSI\Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit"
    r"\graphify-out\graph.json"
)
CODE_GRAPH_RECEIPT = Path(
    r"C:\Users\MSI\Documents\Manager\vault"
    r"\2026-07-29-code-graph-rebuild-receipt.md"
)
PREVIEW = ROOT / "productions" / "_series" / "visual-rebuild-previews"
EVIDENCE_SNAPSHOT = ROOT / "productions" / "_series" / "academic-evidence-snapshot.json"
PROJECTS = ROOT / "OpenMontage" / "projects"

W, H = 1920, 1080
BG = "#08030a"
PANEL = "#0a0407"
GRID = "#3a0d1a"
TEXT = "#f5e8ea"
MUTED = "#c89aa3"
GOLD = "#ff9100"
GREEN = "#00e676"
RED = "#ff1744"
BLUE = "#f5e8ea"
FONT_REGULAR = Path(r"C:\Windows\Fonts\CascadiaMono.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\consolab.ttf")


def _phase(name: str) -> tuple[dict, Path]:
    path = PHASES / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")), path


def _golden_phase(name: str) -> tuple[dict, Path]:
    path = GOLDEN_PHASES / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8")), path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _q(values: list[float], p: float) -> float:
    """NumPy's default linear sample-quantile convention."""
    xs = sorted(values)
    h = (len(xs) - 1) * p
    lo = math.floor(h)
    hi = math.ceil(h)
    return xs[lo] if lo == hi else xs[lo] + (h - lo) * (xs[hi] - xs[lo])


def _t(x: float, y: float, value: str, size: int = 32, color: str = TEXT,
       anchor: str = "start", weight: int = 500) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{color}" '
        f'font-family="Cascadia Mono,Cascadia Code,Consolas,monospace" '
        f'font-size="{size}" font-weight="{weight}" text-anchor="{anchor}">'
        f"{html.escape(value)}</text>"
    )


def _line(x1: float, y1: float, x2: float, y2: float, color: str = GRID,
          width: float = 2, dash: str = "") -> str:
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{color}" stroke-width="{width}"{d}/>'
    )


def _rect(x: float, y: float, w: float, h: float, fill: str = PANEL,
          stroke: str = GRID, radius: float = 18, opacity: float = 1) -> str:
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="{radius}" fill="{fill}" fill-opacity="{opacity}" stroke="{stroke}"/>'
    )


def _poly(points: list[tuple[float, float]], color: str, width: float = 4,
          fill: str = "none", opacity: float = 1) -> str:
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return (
        f'<polyline points="{pts}" fill="{fill}" stroke="{color}" '
        f'stroke-width="{width}" stroke-linejoin="round" stroke-linecap="round" '
        f'opacity="{opacity}"/>'
    )


def _svg(title: str, subtitle: str, body: list[str], provenance: str) -> str:
    header = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
        f'<rect width="{W}" height="{H}" fill="{BG}"/>',
        _t(110, 115, title, 58, TEXT, weight=750),
        _t(110, 165, subtitle, 25, MUTED, weight=500),
        _line(110, 198, 1810, 198, GRID, 2),
    ]
    footer = [
        _line(110, 1002, 1810, 1002, GRID, 2),
        _t(110, 1040, provenance, 20, MUTED),
        "</svg>",
    ]
    return "\n".join(header + body + footer) + "\n"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _mix_hex(left: str, right: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    a = tuple(int(left[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(right[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x + (y - x) * amount):02x}" for x, y in zip(a, b))


def _response_value(dx: int, dy: int, stable: bool) -> float:
    radius = math.hypot(dx, dy)
    width = 3.15 if stable else 0.85
    return 0.92 * math.exp(-((radius / width) ** (8 if stable else 2)))


def _response_color(value: float) -> str:
    if value < 0.45:
        return _mix_hex(GRID, RED, value / 0.45)
    if value < 0.75:
        return _mix_hex(RED, GOLD, (value - 0.45) / 0.30)
    return _mix_hex(GOLD, GREEN, (value - 0.75) / 0.17)


def _pil_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REGULAR), size)


def _brand_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    draw.text((88, 50), "TRADERCOCKPIT / INTO THE LABORATORY / EP04",
              font=_pil_font(22, True), fill=RED)
    draw.text((88, 102), title, font=_pil_font(48, True), fill=TEXT)
    draw.text((88, 168), subtitle, font=_pil_font(25), fill=MUTED)
    draw.line((88, 220, 1832, 220), fill=GRID, width=2)


def _ep01_backtest_vs_strategy() -> str:
    body = [
        _rect(110, 245, 1700, 680),
        _rect(180, 360, 500, 350, "#0d121b", GRID, 18),
        _t(430, 435, "BACKTEST", 42, BLUE, "middle", 800),
        _t(430, 505, "written rules", 27, TEXT, "middle", 650),
        _t(430, 555, "+ historical prices", 27, TEXT, "middle", 650),
        _t(430, 605, "+ stated costs", 27, TEXT, "middle", 650),
        _t(790, 545, "≠", 72, RED, "middle", 800),
        _rect(900, 315, 820, 520, "#0d121b", GRID, 18),
        _t(1310, 390, "TRADING STRATEGY", 42, GOLD, "middle", 800),
        _t(1030, 475, "exact entry and exit rules", 25, TEXT),
        _t(1030, 530, "risk and position-size rules", 25, TEXT),
        _t(1030, 585, "realistic costs and fills", 25, TEXT),
        _t(1030, 640, "out-of-sample tests", 25, TEXT),
        _t(1030, 695, "a rule for when to stop", 25, TEXT),
        _t(960, 900, "A backtest is one measurement inside the strategy-building process.", 30, MUTED, "middle", 700),
    ]
    return _svg(
        "A BACKTEST IS NOT THE WHOLE STRATEGY",
        "HISTORICAL-PRICE REPLAY VERSUS A COMPLETE, TESTABLE TRADING PLAN",
        body,
        "TEACHING DIAGRAM · A HISTORICAL RESULT IS NOT A FORECAST",
    )


def _ep01_golden_arithmetic(phase: dict) -> str:
    cand = phase["candidates"]["concept_library-0-2"]
    metrics = cand["metrics"]
    wins = float(metrics["gross_win"])
    losses = float(metrics["gross_loss"])
    net = float(metrics["net"])
    max_value = max(wins, losses)
    body = [_rect(110, 245, 1700, 680), _line(225, 780, 1695, 780, MUTED, 3)]
    bars = [
        (500, wins, "GROSS WINS", GREEN),
        (960, losses, "GROSS LOSSES", RED),
    ]
    for x, value, label, color in bars:
        height = 390 * value / max_value
        body += [
            f'<rect x="{x-125}" y="{780-height:.1f}" width="250" height="{height:.1f}" '
            f'rx="16" fill="{color}" opacity=".84"/>',
            _t(x, 835, label, 25, MUTED, "middle", 700),
            _t(x, 885, f"${value:,.0f}", 38, color, "middle", 800),
        ]
    body += [
        _t(1450, 430, "PROFIT FACTOR", 25, MUTED, "middle", 700),
        _t(1450, 500, f"{metrics['pf']:.3f}", 58, GOLD, "middle", 850),
        _t(1450, 555, "wins ÷ losses", 23, MUTED, "middle"),
        _t(1450, 665, "NET", 25, MUTED, "middle", 700),
        _t(1450, 735, f"−${abs(net):,.0f}", 54, RED, "middle", 850),
        _t(250, 305, "Golden Cross · separate historical test", 27, TEXT, weight=700),
        _t(250, 347, f"{metrics['n']} closed trades · {phase['window']['start']} → {phase['window']['end']}", 23, MUTED),
    ]
    return _svg(
        "THE GREEN LINE DID NOT SURVIVE THE ARITHMETIC",
        "ALL WINNING DOLLARS VERSUS ALL LOSING DOLLARS UNDER THE RECORDED COST MODEL",
        body,
        "RECORDED HISTORICAL TEST · VALUES ROUNDED FOR DISPLAY",
    )


def _ep01_win_rate_payoff(phase: dict) -> str:
    metrics = phase["candidates"]["concept_library-0-2"]["metrics"]
    avg_win = float(metrics["gross_win"]) / int(metrics["wins"])
    avg_loss = float(metrics["gross_loss"]) / int(metrics["losses"])
    body = [
        _rect(110, 245, 1700, 680),
        _t(255, 315, "ONE PERCENTAGE", 24, MUTED, weight=700),
        _t(255, 405, f"{float(metrics['win_rate']):.1%}", 72, GOLD, weight=850),
        _t(255, 458, "win rate", 26, MUTED),
        _t(790, 410, "×", 70, RED, "middle", 800),
        _t(1070, 315, "PAYOFF SIZE", 24, MUTED, weight=700),
        _t(1070, 395, f"${avg_win:,.0f}", 50, GREEN, "middle", 850),
        _t(1070, 438, f"average win · {int(metrics['wins'])} wins", 22, MUTED, "middle"),
        _t(1460, 395, f"−${avg_loss:,.0f}", 50, RED, "middle", 850),
        _t(1460, 438, f"average loss · {int(metrics['losses'])} losses", 22, MUTED, "middle"),
        _line(255, 540, 1660, 540, GRID, 3),
        _t(255, 620, "GROSS WINS", 23, MUTED, weight=700),
        _t(255, 680, f"${float(metrics['gross_win']):,.0f}", 42, GREEN, weight=850),
        _t(780, 620, "GROSS LOSSES", 23, MUTED, weight=700),
        _t(780, 680, f"−${float(metrics['gross_loss']):,.0f}", 42, RED, weight=850),
        _t(1320, 620, "FINAL NET", 23, MUTED, weight=700),
        _t(1320, 680, f"−${abs(float(metrics['net'])):,.0f}", 42, RED, weight=850),
        _t(960, 845, "Win rate is one input. The full payoff arithmetic is the verdict.", 30, TEXT, "middle", 750),
    ]
    return _svg(
        "A WIN RATE CANNOT JUDGE THE STRATEGY ALONE",
        "GOLDEN CROSS · 733 CLOSED TRADES · SAME RECORDED HISTORICAL TEST",
        body,
        "RECORDED RUN · AVERAGES DERIVED FROM GROSS RESULTS AND TRADE COUNTS",
    )


def _ep01_drawdown(phase: dict) -> str:
    cand = phase["candidates"]["concept_library-0-2"]
    metrics = cand["metrics"]
    daily = [float(value) for value in metrics["daily_returns"]]
    recorded_max_drawdown = float(metrics["max_dd"])
    equity = [0.0]
    for value in daily:
        equity.append(equity[-1] + value)
    running_peak = equity[0]
    peak_index = 0
    best_peak_index = 0
    trough_index = 0
    max_drawdown = 0.0
    for index, value in enumerate(equity):
        if value > running_peak:
            running_peak = value
            peak_index = index
        drawdown = running_peak - value
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            best_peak_index = peak_index
            trough_index = index
    lo, hi = min(equity), max(equity)
    x0, y0, pw, ph = 210, 855, 1490, 520
    points = [
        (
            x0 + index / (len(equity) - 1) * pw,
            y0 - (value - lo) / (hi - lo) * ph,
        )
        for index, value in enumerate(equity)
    ]
    px, py = points[best_peak_index]
    tx, ty = points[trough_index]
    body = [
        _rect(110, 245, 1700, 680),
        _poly(points, BLUE, 5),
        _line(px, py, tx, ty, RED, 5, "12 9"),
        f'<circle cx="{px:.1f}" cy="{py:.1f}" r="14" fill="{GOLD}"/>',
        f'<circle cx="{tx:.1f}" cy="{ty:.1f}" r="14" fill="{RED}"/>',
        _t(px, py - 25, "account high", 23, GOLD, "middle", 700),
        _t(tx, ty + 48, "later low", 23, RED, "middle", 700),
        _t(1190, 310, f"recorded maximum drawdown  ${recorded_max_drawdown:,.0f}", 33, RED, "middle", 800),
        _t(1190, 355, "largest peak-to-later-trough fall reported by the historical test", 24, MUTED, "middle"),
        _t(960, 925, "Drawdown describes the path, not only the final profit or loss.", 27, TEXT, "middle", 700),
    ]
    return _svg(
        "MAXIMUM DRAWDOWN IS A PEAK-TO-TROUGH FALL",
        "THE DEEPEST DROP CAN BE LARGE EVEN WHEN A FINAL NUMBER LOOKS ACCEPTABLE",
        body,
        "RECORDED KPI IS AUTHORITATIVE · PATH RECONSTRUCTED FROM ROUNDED DAILY RETURNS",
    )


def _gate_kills(phase: dict, gate_name: str) -> list[dict]:
    return [
        result["gates"][gate_name]
        for result in phase["candidates"].values()
        if result["gates"][gate_name].get("pass") is False
    ]


def _ep01_intake_funnel(phase: dict) -> str:
    entering = len(phase["entering"])
    surviving = len(phase["surviving"])
    dropped = entering - surviving
    pf_kills = len(_gate_kills(phase, "pf"))
    retdd_kills = len(_gate_kills(phase, "ret_dd"))
    activity_kills = len(_gate_kills(phase, "trades_per_month"))
    body = [
        _rect(110, 245, 1700, 680),
        f'<polygon points="230,350 1690,350 1320,815 600,815" fill="{BLUE}" opacity=".22" stroke="{BLUE}" stroke-width="4"/>',
        _t(960, 430, f"{entering:,} STRATEGIES ENTERED", 48, TEXT, "middle", 850),
        _t(960, 760, f"{surviving} SURVIVED THE FIRST SCREEN", 43, GREEN, "middle", 850),
        _t(960, 855, f"{dropped:,} failed at least one rule", 29, RED, "middle", 750),
        _t(350, 535, f"{pf_kills:,}", 43, GOLD, "middle", 850),
        _t(350, 580, "profit-factor failures", 23, MUTED, "middle"),
        _t(960, 535, f"{retdd_kills:,}", 43, GOLD, "middle", 850),
        _t(960, 580, "return/drawdown failures", 23, MUTED, "middle"),
        _t(1570, 535, f"{activity_kills}", 43, GOLD, "middle", 850),
        _t(1570, 580, "too few trades per month", 23, MUTED, "middle"),
        _t(960, 935, "Gate counts overlap: one strategy can fail more than one rule.", 24, MUTED, "middle"),
    ]
    return _svg(
        "THE FIRST SCREEN REMOVED 1,151 OF 1,335 STRATEGIES",
        "PROFITABILITY · RETURN VERSUS DRAWDOWN · MINIMUM ACTIVITY",
        body,
        "RECORDED RUN · FAILURE COUNTS OVERLAP",
    )


def _ep01_profit_factor_near_misses(phase: dict) -> str:
    threshold = 1.05
    band_low = threshold - 0.10 * abs(threshold)
    values = [
        float(gate["actual"])
        for gate in _gate_kills(phase, "pf")
        if isinstance(gate.get("actual"), (int, float))
        and not isinstance(gate.get("actual"), bool)
    ]
    near = [value for value in values if 0 <= threshold - value < 0.10 * abs(threshold)]
    lo, hi = 0.60, 1.08
    bins = 24
    counts = [0] * bins
    for value in values:
        index = min(bins - 1, max(0, int((value - lo) / (hi - lo) * bins)))
        counts[index] += 1
    x0, y0, pw, ph = 190, 855, 1540, 520
    max_count = max(counts)
    body = [_rect(110, 245, 1700, 680)]
    for index, count in enumerate(counts):
        left = lo + index / bins * (hi - lo)
        right = lo + (index + 1) / bins * (hi - lo)
        color = GOLD if right > band_low else BLUE
        bx = x0 + index / bins * pw
        height = ph * count / max_count
        body.append(
            f'<rect x="{bx:.1f}" y="{y0-height:.1f}" width="{pw/bins-5:.1f}" '
            f'height="{height:.1f}" fill="{color}" opacity=".84"/>'
        )
    band_x = x0 + (band_low - lo) / (hi - lo) * pw
    threshold_x = x0 + (threshold - lo) / (hi - lo) * pw
    body += [
        _line(x0, y0, x0 + pw, y0, MUTED, 3),
        f'<rect x="{band_x:.1f}" y="320" width="{threshold_x-band_x:.1f}" height="{y0-320:.1f}" '
        f'fill="{GOLD}" opacity=".10"/>',
        _line(threshold_x, 300, threshold_x, y0, RED, 4, "12 9"),
        _t(threshold_x, 895, "1.05 rule", 24, RED, "middle", 700),
        _t(230, 310, f"{len(near)} of {len(_gate_kills(phase, 'pf')):,} profit-factor failures fell in 0.945–1.05", 31, TEXT, weight=750),
        _t(230, 355, "That band is clustered around break-even—not around a large positive margin.", 25, MUTED),
        _t(960, 935, "“Within 10% of the rule” does not mean “within 10% of a durable trading edge.”", 27, GOLD, "middle", 750),
    ]
    return _svg(
        "THE LARGE “NEAR-MISS” COUNT WAS BREAKEVEN NOISE",
        "FAILED PROFIT FACTOR VALUES · NULL MEASUREMENTS EXCLUDED",
        body,
        "RECORDED RUN · DECLARED 10% BAND · NULL VALUES EXCLUDED",
    )


def _ep01_threshold_motion(phase: dict) -> str:
    failures = [
        float(gate["actual"])
        for gate in _gate_kills(phase, "pf")
        if isinstance(gate.get("actual"), (int, float))
        and not isinstance(gate.get("actual"), bool)
    ]
    reclassified = sum(1 for value in failures if 1.00 <= value < 1.05)
    x0, x1, y = 240, 1680, 575
    scale = lambda value: x0 + (value - 0.90) / 0.20 * (x1 - x0)
    body = [
        _rect(110, 245, 1700, 680),
        _t(960, 335, "THE MEASURED VALUES DO NOT MOVE", 34, TEXT, "middle", 800),
        _line(x0, y, x1, y, MUTED, 8),
    ]
    for value in (0.90, 0.95, 1.00, 1.05, 1.10):
        x = scale(value)
        body += [_line(x, y - 18, x, y + 18, MUTED, 3), _t(x, y + 62, f"{value:.2f}", 23, MUTED, "middle")]
    for index, value in enumerate(sorted(v for v in failures if 0.90 <= v <= 1.10)):
        x = scale(value)
        cy = 475 - (index % 5) * 18
        body.append(f'<circle cx="{x:.1f}" cy="{cy:.1f}" r="5" fill="{BLUE}" opacity=".55"/>')
    rule_105 = scale(1.05)
    rule_100 = scale(1.00)
    body += [
        _line(rule_105, 300, rule_105, 760, RED, 5, "13 9"),
        _t(rule_105, 805, "DECLARED RULE 1.05", 25, RED, "middle", 800),
        _line(rule_100, 390, rule_100, 760, GOLD, 5, "13 9"),
        _t(rule_100, 850, "LOWERED RULE 1.00", 25, GOLD, "middle", 800),
        _t(960, 905, f"{reclassified} recorded failures would be reclassified; no result improved.", 29, TEXT, "middle", 750),
    ]
    return _svg(
        "MOVING THE RULE CHANGES ADMISSION—NOT PERFORMANCE",
        "SAME PROFIT-FACTOR MEASUREMENTS · TWO DIFFERENT DECISION LINES",
        body,
        "RECORDED RUN · NULL VALUES EXCLUDED · THRESHOLD COMPARISON DERIVED",
    )


def _ep01_survivor_status(phase: dict) -> str:
    surviving = len(phase["surviving"])
    body = [
        _rect(110, 245, 1700, 680),
        _t(360, 315, f"{surviving} FIRST-SCREEN SURVIVORS", 29, TEXT, "middle", 800),
    ]
    for index in range(surviving):
        col, row = index % 16, index // 16
        body.append(f'<circle cx="{205 + col * 22}" cy="{365 + row * 35}" r="7" fill="{GOLD}" opacity=".78"/>')
    body += [
        _t(790, 560, "→", 74, RED, "middle", 800),
        _t(790, 625, "NOT A WINNER BADGE", 23, RED, "middle", 800),
    ]
    questions = [
        "LATER HISTORICAL PRICES",
        "HIGHER TRADING COSTS",
        "NEARBY RULE SETTINGS",
        "CONCENTRATION IN HISTORY",
    ]
    for index, label in enumerate(questions):
        y = 315 + index * 142
        body += [
            _rect(960, y, 680, 104, "#0d121b", GRID, 14),
            _t(1300, y + 64, label, 27, TEXT, "middle", 750),
        ]
    body.append(_t(960, 910, "Passing the first screen only earns the next question.", 30, GOLD, "middle", 750))
    return _svg(
        "THE 184 SURVIVORS ARE CANDIDATES—NOT WINNERS",
        "FIRST SCREEN COMPLETE · ROBUSTNESS QUESTIONS STILL OPEN",
        body,
        "RECORDED RUN · SURVIVOR COUNT 184 · QUESTION LIST IS THE DECLARED PIPELINE",
    )


def _ep02_timeline(phase: dict) -> str:
    start, end = phase["window"]["start"], phase["window"]["end"]
    x0, x1, y = 165, 1755, 520
    split = 1110
    body = [
        _rect(110, 255, 1700, 650),
        _line(x0, y, x1, y, MUTED, 6),
        f'<rect x="{x0}" y="{y-68}" width="{split-x0}" height="136" rx="16" fill="{BLUE}" opacity=".35"/>',
        f'<rect x="{split}" y="{y-68}" width="{x1-split}" height="136" rx="16" fill="{GOLD}" opacity=".38"/>',
        _t((x0 + split) / 2, y - 95, "DEVELOPMENT DATA", 36, BLUE, "middle", 700),
        _t((split + x1) / 2, y - 95, "LOCKED OUT-OF-SAMPLE TEST", 36, GOLD, "middle", 700),
        _t((x0 + split) / 2, y + 18, "choose rules and parameters here", 28, TEXT, "middle"),
        _t((split + x1) / 2, y + 18, "evaluate the frozen strategy here", 28, TEXT, "middle"),
        _line(split, 325, split, 705, RED, 4, "16 12"),
        _t(split, 755, f"actual test window  {start} → {end}", 30, TEXT, "middle", 650),
        _t(960, 835, "The percentage is a design choice—not a universal 20–30% rule.", 31, MUTED, "middle"),
    ]
    return _svg(
        "TIME-ORDERED DEVELOPMENT AND HOLDOUT WINDOWS",
        "TRAIN FIRST · FREEZE THE STRATEGY · THEN OPEN OUT-OF-SAMPLE DATA",
        body,
        "RECORDED WINDOWS · STRATEGY FROZEN BEFORE OUT-OF-SAMPLE TEST",
    )


def _ep02_distribution(phase: dict) -> str:
    nets = [float(c["metrics"]["net"]) for c in phase["candidates"].values()]
    lo, hi = min(nets), max(nets)
    bins = 22
    counts = [0] * bins
    for value in nets:
        idx = min(bins - 1, int((value - lo) / (hi - lo) * bins))
        counts[idx] += 1
    x0, y0, pw, ph = 180, 870, 1530, 560
    maxc = max(counts)
    body = [_rect(110, 245, 1700, 680)]
    for i, count in enumerate(counts):
        bx = x0 + i * pw / bins
        bw = pw / bins - 6
        bh = ph * count / maxc
        center = lo + (i + 0.5) / bins * (hi - lo)
        color = RED if center < 0 else GREEN
        body.append(f'<rect x="{bx:.1f}" y="{y0-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" '
                    f'fill="{color}" opacity=".82"/>')
    zx = x0 + (0 - lo) / (hi - lo) * pw
    body += [
        _line(x0, y0, x0 + pw, y0, MUTED, 3),
        _line(zx, y0 - ph, zx, y0 + 22, GOLD, 4, "12 10"),
        _t(zx, y0 + 58, "$0 net", 25, GOLD, "middle", 700),
        _t(x0, y0 + 58, f"${lo:,.0f}", 24, MUTED, "middle"),
        _t(x0 + pw, y0 + 58, f"${hi:,.0f}", 24, MUTED, "middle"),
        _t(185, 300, f"{len(nets)} candidates", 30, TEXT, weight=700),
        _t(185, 342, f"{sum(v > 0 for v in nets)} above $0 net", 27, GREEN),
        _t(1810 - 100, 300, "Distribution, not a winner card", 27, GOLD, "end", 700),
        _t(1810 - 100, 342, "Each bar is a range of held-out net results.", 24, MUTED, "end"),
    ]
    return _svg(
        "DISTRIBUTION OF HELD-OUT NET RESULTS",
        "NET RESULT ACROSS ALL 184 CANDIDATES · SAME OUT-OF-SAMPLE WINDOW",
        body,
        "RECORDED RUN · ALL 184 LATER-PERIOD RESULTS",
    )


def _ep02_concentration(phase: dict) -> str:
    key, cand = max(phase["candidates"].items(), key=lambda kv: kv[1]["metrics"]["net"])
    daily = [float(v) for v in cand["metrics"]["daily_returns"]]
    total = sum(daily)
    top10 = sum(sorted(daily, reverse=True)[:10])
    remainder = total - top10
    vals = [total, top10, remainder]
    labels = ["TOTAL", "10 BEST DAYS", "REMAINDER"]
    colors = [BLUE, GOLD, GREEN if remainder >= 0 else RED]
    maxabs = max(abs(v) for v in vals)
    body = [_rect(110, 245, 1700, 680), _line(220, 665, 1700, 665, MUTED, 3)]
    for i, (value, label, color) in enumerate(zip(vals, labels, colors)):
        cx = 460 + i * 500
        height = 310 * abs(value) / maxabs
        y = 665 - height if value >= 0 else 665
        body += [
            f'<rect x="{cx-105}" y="{y:.1f}" width="210" height="{height:.1f}" rx="12" fill="{color}" opacity=".85"/>',
            _t(cx, 780, label, 25, MUTED, "middle", 700),
            _t(cx, 830, f"${value:,.0f}", 38, color, "middle", 750),
        ]
    body += [
        _t(185, 300, f"Candidate {key.rsplit('-', 1)[-1]}", 28, TEXT, weight=700),
        _t(185, 342, f"{len(daily)} daily observations", 24, MUTED),
        _t(1720, 315, "If the remainder is negative, profit was concentrated.", 26, GOLD, "end", 650),
        _t(1720, 353, "That does not prove the other days were noise.", 24, MUTED, "end"),
    ]
    return _svg(
        "CONCENTRATION STRESS: REMOVE THE 10 BEST DAYS",
        "A WATERFALL ANSWERS A NARROW QUESTION—WHERE DID THIS SAMPLE'S PROFIT COME FROM?",
        body,
        "RECORDED RUN · TEN-DAY REMOVAL CALCULATED FROM DAILY RESULTS",
    )


def _ep02_selected_maximum(phase: dict) -> str:
    rows = sorted((float(c["metrics"]["net"]), key) for key, c in phase["candidates"].items())
    lo, hi = rows[0][0], rows[-1][0]
    x0, y0, pw, ph = 210, 840, 1490, 500
    body = [_rect(110, 245, 1700, 680), _line(x0, y0, x0 + pw, y0, MUTED, 3)]
    for i, (net, key) in enumerate(rows):
        x = x0 + i / (len(rows) - 1) * pw
        y = y0 - (net - lo) / (hi - lo) * ph
        selected = i == len(rows) - 1
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{15 if selected else 5}" '
                    f'fill="{GOLD if selected else BLUE}" opacity="{1 if selected else .5}"/>')
        if selected:
            body += [
                _line(x, y + 22, x, y + 120, GOLD, 3, "8 7"),
                _t(x - 20, y + 152, "raw maximum", 25, GOLD, "end", 700),
                _t(x - 20, y + 188, "selected after comparison", 23, MUTED, "end"),
            ]
    body += [
        _t(210, 310, "184 held-out results, ordered from low to high", 28, TEXT, weight=700),
        _t(210, 352, "Each dot is one candidate on the same out-of-sample window.", 24, MUTED),
        _t(960, 930, "The highlighted maximum is selected evidence—not a pre-specified single test.", 26, TEXT, "middle", 700),
    ]
    return _svg(
        "SELECTION AFTER COMPARING 184 HELD-OUT RESULTS",
        "THE RAW MAXIMUM ANSWERS A DIFFERENT QUESTION FROM ONE PRE-SPECIFIED TEST",
        body,
        "RECORDED RUN · SELECTING AFTER COMPARISON CHANGES THE QUESTION",
    )


def _ep02_walk_forward() -> str:
    body = [_rect(110, 245, 1700, 680)]
    for i in range(3):
        y = 360 + i * 175
        train_x = 230 + i * 190
        train_w = 820 if i < 2 else 630
        test_x = train_x + train_w
        body += [
            _t(180, y + 50, f"FOLD {i + 1}", 25, MUTED, "start", 700),
            f'<rect x="{train_x}" y="{y}" width="{train_w}" height="96" rx="12" fill="{BLUE}" opacity=".42"/>',
            f'<rect x="{test_x}" y="{y}" width="260" height="96" rx="12" fill="{GOLD}" opacity=".56"/>',
            _t(train_x + train_w / 2, y + 60, "DEVELOP / REFIT", 24, TEXT, "middle", 700),
            _t(test_x + 130, y + 60, "TEST NEXT", 24, TEXT, "middle", 700),
        ]
    body += [
        _t(960, 900, "Expanding and rolling windows are different designs. State which one you used.", 27, TEXT, "middle", 700),
    ]
    return _svg(
        "WALK-FORWARD EVALUATION USES ORDERED FOLDS",
        "DEVELOP ON EARLIER DATA · EVALUATE ON THE NEXT BLOCK · THEN ADVANCE",
        body,
        "TEACHING DIAGRAM · ROLL THE BUILD-AND-TEST WINDOWS FORWARD",
    )


def _ep02_sample_uncertainty() -> str:
    intervals = [(12, 0.254, 0.746), (100, 0.404, 0.596)]
    x0, pw = 330, 1250
    body = [_rect(110, 245, 1700, 680)]
    for i, (n, lo, hi) in enumerate(intervals):
        y = 470 + i * 260
        lx, hx, mx = x0 + lo * pw, x0 + hi * pw, x0 + .5 * pw
        body += [
            _t(250, y + 10, f"n = {n}", 31, TEXT, "end", 700),
            _line(x0, y, x0 + pw, y, GRID, 3),
            _line(lx, y, hx, y, BLUE if n == 100 else RED, 14),
            _line(lx, y - 28, lx, y + 28, TEXT, 4),
            _line(hx, y - 28, hx, y + 28, TEXT, 4),
            f'<circle cx="{mx:.1f}" cy="{y}" r="14" fill="{GOLD}"/>',
            _t(lx, y + 64, f"{lo:.1%}", 23, MUTED, "middle"),
            _t(hx, y + 64, f"{hi:.1%}", 23, MUTED, "middle"),
        ]
    body += [
        _t(x0, 330, "0%", 22, MUTED, "middle"),
        _t(x0 + pw / 2, 330, "50% observed win rate", 24, GOLD, "middle", 700),
        _t(x0 + pw, 330, "100%", 22, MUTED, "middle"),
        _t(960, 900, "Illustrative 95% Wilson intervals under an independent Bernoulli model.", 26, TEXT, "middle", 700),
        _t(960, 940, "Real P&L also depends on payoff size, tails, and serial dependence.", 23, MUTED, "middle"),
    ]
    return _svg(
        "SAMPLE SIZE CHANGES UNCERTAINTY",
        "THE SAME 50% OBSERVED WIN RATE CAN SUPPORT VERY DIFFERENT INTERVALS",
        body,
        "DERIVED EXAMPLE · UNCERTAINTY DEPENDS ON SAMPLE SIZE AND THE QUESTION",
    )


def _ep03_cost_anatomy() -> str:
    body = [
        _rect(110, 245, 1700, 680),
        _t(960, 320, "decision / arrival benchmark", 30, BLUE, "middle", 700),
        _line(270, 450, 1650, 450, MUTED, 5),
        _line(570, 390, 570, 510, BLUE, 5),
        _line(1110, 390, 1110, 510, GOLD, 5),
        _t(570, 370, "REFERENCE PRICE", 25, BLUE, "middle", 700),
        _t(1110, 370, "EXECUTION PRICE", 25, GOLD, "middle", 700),
        f'<path d="M590 540 C760 650 920 650 1090 540" fill="none" stroke="{RED}" stroke-width="5"/>',
        _t(840, 690, "price shortfall against the declared benchmark", 29, RED, "middle", 650),
        _t(420, 820, "commission", 28, TEXT, "middle", 700),
        _t(960, 820, "spread / impact / price movement while waiting", 25, TEXT, "middle", 700),
        _t(1500, 820, "missed or partial execution", 28, TEXT, "middle", 700),
        _t(960, 885, "Name the benchmark and inclusions before calling any number “slippage.”", 31, GOLD, "middle", 700),
    ]
    return _svg(
        "EXECUTION COST NEEDS A BENCHMARK",
        "COMMISSION IS EXPLICIT · IMPLEMENTATION SHORTFALL IS MEASURED FROM A DECLARED REFERENCE",
        body,
        "TEACHING DIAGRAM · DEFINE THE PRICE BENCHMARK BEFORE THE COST",
    )


def _ep03_transitions(phase: dict) -> str:
    rows = []
    for key, cand in phase["candidates"].items():
        d2 = cand["detail"]["slippage_2x"]
        d3 = cand["detail"]["slippage_3x"]
        rows.append((key, d2["pf"] > 1.0, d3["net"] > 0))
    rows.sort(key=lambda r: (not r[1], not r[2], r[0]))
    body = [_rect(110, 245, 1700, 680)]
    x2, x3 = 540, 1380
    body += [
        _t(x2, 315, "2× SLIPPAGE ASSUMPTION", 30, BLUE, "middle", 750),
        _t(x3, 315, "3× SLIPPAGE ASSUMPTION", 30, GOLD, "middle", 750),
        _t(x2, 358, "profit factor > 1.0", 23, MUTED, "middle"),
        _t(x3, 358, "net dollars > 0", 23, MUTED, "middle"),
    ]
    cols = 9
    for i, (_, pass2, pass3) in enumerate(rows):
        row, col = divmod(i, cols)
        y = 430 + row * 78
        xa = x2 - 280 + col * 70
        xb = x3 - 280 + col * 70
        body += [
            f'<circle cx="{xa}" cy="{y}" r="21" fill="{GREEN if pass2 else RED}"/>',
            f'<circle cx="{xb}" cy="{y}" r="21" fill="{GREEN if pass3 else RED}"/>',
            _line(xa + 25, y, xb - 25, y, GRID, 2),
        ]
    fail2 = sum(not r[1] for r in rows)
    fail3 = sum(not r[2] for r in rows)
    body += [
        _t(x2, 905, f"{fail2} failed · {len(rows)-fail2} passed", 29, TEXT, "middle", 700),
        _t(x3, 905, f"{fail3} failed · {len(rows)-fail3} passed", 29, TEXT, "middle", 700),
        _t(960, 955, "On one fixed net-trade ledger, PF > 1 and net > 0 have the same sign; the stress level changed.", 24, MUTED, "middle"),
    ]
    return _svg(
        "PASS/FAIL RESULTS UNDER TWO SLIPPAGE ASSUMPTIONS",
        "EACH DOT IS ONE OF THE SAME 53 STRATEGIES · GREEN PASSED THAT SPECIFIC BAR",
        body,
        "RECORDED RUN · SAME 53 STRATEGIES UNDER EACH COST ASSUMPTION",
    )


def _ep03_response_curves(phase: dict) -> str:
    rows = []
    for key, cand in phase["candidates"].items():
        d2 = cand["detail"]["slippage_2x"]
        d3 = cand["detail"]["slippage_3x"]
        rows.append((key.rsplit("-", 1)[-1], d2["net"], d3["net"], d2["pf"], d3["pf"]))
    rows.sort(key=lambda r: r[2])
    chosen = [rows[0], rows[len(rows)//2], rows[-1]]
    x2, x3, y0, ph = 560, 1370, 800, 430
    net_values = [v for r in chosen for v in (r[1], r[2])]
    lo, hi = min(net_values), max(net_values)
    scale = lambda v: y0 - (v - lo) / (hi - lo) * ph
    body = [_rect(110, 245, 1700, 680), _line(250, scale(0), 1680, scale(0), GOLD, 3, "12 9")]
    palette = [RED, BLUE, GREEN]
    for row, color in zip(chosen, palette):
        sid, n2, n3, pf2, pf3 = row
        y2, y3 = scale(n2), scale(n3)
        body += [
            _line(x2, y2, x3, y3, color, 6),
            f'<circle cx="{x2}" cy="{y2:.1f}" r="13" fill="{color}"/>',
            f'<circle cx="{x3}" cy="{y3:.1f}" r="13" fill="{color}"/>',
            _t(x2 - 28, y2 + 9, f"{sid}  ${n2:,.0f}", 24, color, "end", 650),
            _t(x3 + 28, y3 + 9, f"${n3:,.0f}  PF {pf3:.2f}", 24, color, "start", 650),
        ]
    body += [
        _t(x2, 330, "2×", 36, BLUE, "middle", 750),
        _t(x3, 330, "3×", 36, GOLD, "middle", 750),
        _t(280, scale(0) - 16, "$0 NET", 22, GOLD),
        _t(960, 900, "Worst · median · best at 3× shown. The full field is retained privately.", 24, MUTED, "middle"),
    ]
    return _svg(
        "NET RESULT UNDER 2× AND 3× SLIPPAGE ASSUMPTIONS",
        "NET RESULT AT 2× AND 3× FOR 3 ACTUAL STRATEGIES",
        body,
        "RECORDED RUN · THREE EXAMPLES FROM THE FULL 53-STRATEGY FIELD",
    )


def _ep03_fixed_ledger_formula() -> str:
    body = [
        _rect(110, 245, 1700, 680),
        _t(960, 360, "stressed net = baseline net − added execution cost", 38, TEXT, "middle", 700),
        _t(960, 500, "added cost = completed trades × extra cost per trade × position size", 34, BLUE, "middle", 700),
        _line(270, 590, 1650, 590, GRID, 3),
        _t(420, 680, "TRADE LIST", 25, MUTED, "middle", 700),
        _t(420, 735, "fixed", 42, GREEN, "middle", 750),
        _t(960, 680, "FILLS AND QUEUE", 25, MUTED, "middle", 700),
        _t(960, 735, "not re-simulated", 38, RED, "middle", 750),
        _t(1500, 680, "SLIPPAGE INPUT", 25, MUTED, "middle", 700),
        _t(1500, 735, "2× and 3×", 42, GOLD, "middle", 750),
        _t(960, 875, "A linear repricing check is useful only inside these fixed assumptions.", 28, TEXT, "middle", 700),
    ]
    return _svg(
        "FIXED-TRADE REPRICING",
        "ONE COST INPUT CHANGED · EXECUTION WAS NOT REPLAYED",
        body,
        "RECORDED METHOD · SAME SAVED TRADES, DIFFERENT ASSUMED COST",
    )


def _ep03_order_tradeoff() -> str:
    body = [_rect(110, 245, 1700, 680)]
    panels = [
        (190, "MARKET ORDER", BLUE, "prioritizes immediate execution",
         ["accepts available price", "can cross spread", "price can move while it waits"]),
        (1010, "LIMIT ORDER", GOLD, "controls worst acceptable price",
         ["may not fill", "may fill partly", "can face adverse selection"]),
    ]
    for x, title, color, lead, bullets in panels:
        body += [
            _rect(x, 330, 720, 500, "#0d121b", GRID, 16),
            _t(x + 360, 410, title, 34, color, "middle", 750),
            _t(x + 360, 480, lead, 26, TEXT, "middle", 650),
        ]
        for i, bullet in enumerate(bullets):
            body.append(_t(x + 95, 585 + i * 70, f"• {bullet}", 25, MUTED))
    body += [_t(960, 900, "Order type exchanges price risk and execution risk; neither removes cost.", 28, TEXT, "middle", 700)]
    return _svg(
        "MARKET AND LIMIT ORDERS TRADE DIFFERENT RISKS",
        "PRICE CONTROL · EXECUTION PROBABILITY · OPPORTUNITY COST",
        body,
        "TEACHING DIAGRAM · EXECUTION PRICE AND FILL RISK TRADE OFF",
    )


def _ep03_cost_drivers() -> str:
    factors = [
        ("ORDER SIZE", 320, 390), ("URGENCY", 760, 315), ("BOOK DEPTH", 1210, 315),
        ("VOLATILITY", 1570, 420), ("TIME / VENUE", 1420, 760), ("ORDER TYPE", 780, 800),
        ("INSTRUMENT", 330, 700),
    ]
    body = [_rect(110, 245, 1700, 680)]
    for label, x, y in factors:
        body += [_line(960, 575, x, y, GRID, 3), f'<circle cx="{x}" cy="{y}" r="82" fill="#131b29" stroke="{BLUE}" stroke-width="2"/>',
                 _t(x, y + 8, label, 20, TEXT, "middle", 700)]
    body += [
        f'<circle cx="960" cy="575" r="150" fill="{BLUE}" opacity=".72"/>',
        _t(960, 560, "EXECUTION", 31, TEXT, "middle", 750),
        _t(960, 605, "COST", 44, GOLD, "middle", 800),
        _t(960, 900, "A multiplier is meaningful only relative to a declared baseline and uncertainty set.", 25, MUTED, "middle"),
    ]
    return _svg(
        "EXECUTION COST IS CONDITIONAL",
        "THE SAME TRADE CAN FACE DIFFERENT COSTS UNDER DIFFERENT CONDITIONS",
        body,
        "TEACHING DIAGRAM · COST CHANGES WITH HOW AND WHERE AN ORDER TRADES",
    )


def _ep04_mcse() -> str:
    x0, y0, pw, ph = 230, 850, 1420, 500
    points = []
    for n in range(10, 10001, 10):
        lx = math.log10(n)
        x = x0 + (lx - 1) / 3 * pw
        y = y0 - (1 / math.sqrt(n) - 0.01) / (1 / math.sqrt(10) - 0.01) * ph
        points.append((x, y))
    n200x = x0 + (math.log10(200) - 1) / 3 * pw
    n200y = y0 - (1 / math.sqrt(200) - 0.01) / (1 / math.sqrt(10) - 0.01) * ph
    body = [
        _rect(110, 245, 1700, 680),
        _poly(points, BLUE, 6),
        _line(x0, y0, x0 + pw, y0, MUTED, 3),
        _line(x0, y0 - ph, x0, y0, MUTED, 3),
        _line(n200x, 330, n200x, y0, GOLD, 3, "11 9"),
        f'<circle cx="{n200x:.1f}" cy="{n200y:.1f}" r="16" fill="{GOLD}"/>',
        _t(n200x + 24, n200y - 12, "200 runs in this experiment", 26, GOLD, weight=700),
        _t(260, 330, "relative Monte Carlo error ∝ 1 / √N", 31, TEXT, weight=700),
        _t(260, 378, "4× as many independent runs → about ½ the sampling error", 27, MUTED),
        _t(x0, 895, "10", 23, MUTED, "middle"),
        _t(x0 + pw/3, 895, "100", 23, MUTED, "middle"),
        _t(x0 + 2*pw/3, 895, "1,000", 23, MUTED, "middle"),
        _t(x0 + pw, 895, "10,000 runs", 23, MUTED, "middle"),
        _t(960, 950, "No universal maximum. Choose N from the statistic and precision required.", 27, RED, "middle", 700),
    ]
    return _svg(
        "MONTE CARLO SAMPLING ERROR VERSUS NUMBER OF RUNS",
        "THE SQUARE-ROOT LAW EXPLAINS WHY PRECISION IMPROVES SLOWLY",
        body,
        "DERIVED MATH · INDEPENDENT-RUN AVERAGE EXAMPLE",
    )


def _ep04_field(phase: dict) -> str:
    rows = []
    for key, cand in phase["candidates"].items():
        m = cand["metrics"]
        rows.append((key.rsplit("-", 1)[-1], float(m["baseline_ret_dd"]),
                     float(m["ret_dd_p95_frac_of_phase02"]), cand["verdict"]))
    x0, y0, pw, ph = 220, 870, 1430, 540
    maxb = max(r[1] for r in rows)
    maxr = max(r[2] for r in rows)
    body = [_rect(110, 245, 1700, 680)]
    threshold_y = y0 - 0.5 / maxr * ph
    body += [_line(x0, threshold_y, x0 + pw, threshold_y, GOLD, 4, "12 9"),
             _t(x0 + pw, threshold_y - 16, "0.50 gate", 24, GOLD, "end", 700)]
    for sid, baseline, ratio, verdict in rows:
        x = x0 + baseline / maxb * pw
        y = y0 - ratio / maxr * ph
        color = GREEN if verdict.lower() == "pass" else RED
        body.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="{color}" opacity=".82"/>')
    body += [
        _t(250, 310, f"{len(rows)} strategies", 29, TEXT, weight=700),
        _t(250, 352, f"{sum(r[3].lower() == 'pass' for r in rows)} passed · {sum(r[3].lower() != 'pass' for r in rows)} failed", 26, MUTED),
        _t(1700, 310, "x: baseline return ÷ drawdown", 24, BLUE, "end"),
        _t(1700, 352, "y: 5th-percentile result ÷ baseline", 24, GOLD, "end"),
        _t(960, 950, "A strong baseline did not guarantee a stable lower-tail result.", 27, MUTED, "middle"),
    ]
    return _svg(
        "BASELINE PERFORMANCE AND LOWER-TAIL RETENTION",
        "BASELINE STRENGTH VERSUS LOWER-TAIL RETENTION",
        body,
        "RECORDED RUN · ALL 46 STRATEGIES SHOWN",
    )


def _ep04_fan_data(phase: dict) -> tuple:
    target = next((item for item in phase["candidates"].items()
                   if item[0].endswith("-3106")), next(iter(phase["candidates"].items())))
    key, cand = target
    paths = [[float(v) for v in row] for row in cand["display"]["param_paths"]]
    n = min(map(len, paths))
    paths = [row[:n] for row in paths]
    bands = {p: [_q([row[i] for row in paths], p) for i in range(n)]
             for p in (0.05, 0.25, 0.50, 0.75, 0.95)}
    profitable = [row for row in paths if row[-1] > 0]
    losing = [row for row in paths if row[-1] <= 0]
    representative = None
    if profitable:
        median_end = _q([row[-1] for row in profitable], 0.50)
        representative = min(profitable, key=lambda row: abs(row[-1] - median_end))
    return key, cand, paths, bands, profitable, losing, representative


def _ep04_fan(phase: dict) -> str:
    key, cand, paths, bands, profitable, losing, representative = _ep04_fan_data(phase)
    n = len(paths[0])
    allv = [v for row in paths for v in row]
    lo, hi = min(min(allv), 0), max(max(allv), 0)
    x0, y0, pw, ph = 210, 885, 1490, 570
    xy = lambda seq: [
        (x0 + i / (n - 1) * pw, y0 - (v - lo) / (hi - lo) * ph)
        for i, v in enumerate(seq)
    ]
    p05, p25, p50, p75, p95 = (xy(bands[p]) for p in (0.05, 0.25, 0.50, 0.75, 0.95))
    outer = p05 + list(reversed(p95))
    inner = p25 + list(reversed(p75))
    body = [
        _rect(110, 245, 1700, 700),
        f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in outer)}" fill="{MUTED}" opacity=".13"/>',
        f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x,y in inner)}" fill="{MUTED}" opacity=".24"/>',
    ]
    for row in paths:
        body.append(_poly(xy(row), GREEN if row[-1] > 0 else RED, 1, opacity=.14))
    if representative is not None:
        body.append(_poly(xy(representative), GREEN, 4))
    zero_y = xy([0] * n)[0][1]
    body += [
        _line(x0, zero_y, x0 + pw, zero_y, GOLD, 3, "10 8"),
        _t(x0 + pw, zero_y - 12, "$0", 22, GOLD, "end", 700),
        _poly(p50, TEXT, 5),
        _line(x0, y0, x0 + pw, y0, MUTED, 3),
        _t(250, 310, f"Strategy {key.rsplit('-', 1)[-1]}", 30, TEXT, weight=700),
        _t(250, 352, f"{len(profitable)} green profitable endings · {len(losing)} red losing or flat endings", 25, MUTED),
        _t(1660, 315, "green = finishes above $0", 24, GREEN, "end", 700),
        _t(1660, 355, "red = finishes at or below $0", 24, RED, "end", 700),
        _t(1660, 395, "white = pointwise median", 24, TEXT, "end", 700),
        _t(960, 925, "Path color reports terminal P&L. Neutral shading reports pointwise quantile bands.", 24, MUTED, "middle"),
    ]
    return _svg(
        "SIMULATED EQUITY PATHS AND QUANTILE BANDS",
        "GREEN PATHS FINISH PROFITABLE · RED PATHS FINISH LOSING OR FLAT",
        body,
        "RECORDED DISPLAY PATHS · POINT-BY-POINT PERCENTILE BANDS",
    )


def _ep04_geometry() -> str:
    body = []
    for x, label, stable, color, verdict in (
        (120, "BROAD PLATEAU", True, GREEN, "NEIGHBORS CONFIRM THE RESULT"),
        (1000, "NARROW SPIKE", False, RED, "NEIGHBORS COLLAPSE"),
    ):
        body += [
            _rect(x, 270, 800, 650, PANEL, GRID, 16),
            _t(x + 400, 335, label, 31, color, "middle", 800),
            _t(x + 400, 372, "same selected score at the center", 21, MUTED, "middle"),
        ]
        gx, gy, cell = x + 175, 395, 50
        for row in range(9):
            for col in range(9):
                value = _response_value(col - 4, row - 4, stable)
                body.append(
                    f'<rect x="{gx + col * cell}" y="{gy + row * cell}" '
                    f'width="{cell - 3}" height="{cell - 3}" rx="5" '
                    f'fill="{_response_color(value)}" stroke="{BG}" stroke-width="2"/>'
                )
        selected_x, selected_y = gx + 4 * cell, gy + 4 * cell
        body += [
            f'<rect x="{selected_x - 4}" y="{selected_y - 4}" width="{cell + 5}" '
            f'height="{cell + 5}" rx="8" fill="none" stroke="{TEXT}" stroke-width="4"/>',
            f'<circle cx="{selected_x + (cell - 3) / 2:.1f}" '
            f'cy="{selected_y + (cell - 3) / 2:.1f}" r="7" fill="{TEXT}"/>',
            _t(x + 400, 885, verdict, 23, color, "middle", 800),
            _t(x + 400, 912, "parameter A →    parameter B ↑", 18, MUTED, "middle"),
        ]
    body.append(
        _t(960, 968, "Move one step in every direction. Stability lives in the neighborhood.",
           25, TEXT, "middle", 750)
    )
    return _svg(
        "ONE GREEN CELL CAN HIDE TWO DIFFERENT STORIES",
        "CHANGE NEARBY SETTINGS · DOES THE RESULT SURVIVE?",
        body,
        "ORIGINAL TEACHING GEOMETRY · ILLUSTRATIVE VALUES · NOT RUN DATA",
    )


def _draw_ep04_neighborhood(out: Path) -> None:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    _brand_header(
        draw,
        "ONE GREEN CELL CAN HIDE TWO DIFFERENT STORIES",
        "Change nearby settings. Does the result survive?",
    )
    for x, label, stable, color, verdict in (
        (88, "BROAD PLATEAU", True, GREEN, "NEIGHBORS CONFIRM THE RESULT"),
        (1000, "NARROW SPIKE", False, RED, "NEIGHBORS COLLAPSE"),
    ):
        draw.rounded_rectangle((x, 260, x + 832, 930), radius=22,
                               fill=PANEL, outline=GRID, width=3)
        draw.text((x + 416, 305), label, font=_pil_font(30, True),
                  fill=color, anchor="mm")
        draw.text((x + 416, 348), "same selected score at the center",
                  font=_pil_font(20), fill=MUTED, anchor="mm")
        gx, gy, cell = x + 173, 390, 54
        for row in range(9):
            for col in range(9):
                value = _response_value(col - 4, row - 4, stable)
                left, top = gx + col * cell, gy + row * cell
                draw.rounded_rectangle(
                    (left, top, left + cell - 4, top + cell - 4),
                    radius=6, fill=_response_color(value), outline=BG, width=2,
                )
        selected_x, selected_y = gx + 4 * cell, gy + 4 * cell
        draw.text((gx, gy - 28), "PARAMETER B ↑", font=_pil_font(16, True),
                  fill=MUTED)
        draw.text((gx + 9 * cell, gy - 28), "PARAMETER A →",
                  font=_pil_font(16, True), fill=MUTED, anchor="ra")
        draw.rounded_rectangle(
            (selected_x - 5, selected_y - 5,
             selected_x + cell + 1, selected_y + cell + 1),
            radius=9, outline=TEXT, width=4,
        )
        draw.ellipse(
            (selected_x + 18, selected_y + 18,
             selected_x + 32, selected_y + 32),
            fill=TEXT,
        )
        draw.text((x + 416, 900), verdict, font=_pil_font(21, True),
                  fill=color, anchor="mm")
    draw.text(
        (960, 985),
        "THE TEST: MOVE ONE STEP IN EVERY DIRECTION. STABILITY LIVES IN THE NEIGHBORHOOD.",
        font=_pil_font(21, True), fill=TEXT, anchor="mm",
    )
    draw.text(
        (88, 1042),
        "ORIGINAL TEACHING GEOMETRY / ILLUSTRATIVE VALUES / NOT RUN DATA",
        font=_pil_font(17), fill=MUTED,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)


def _draw_ep04_fan(out: Path, phase: dict) -> None:
    key, candidate, paths, bands, profitable, losing, representative = _ep04_fan_data(phase)
    count = len(paths[0])
    low = min(min(row) for row in paths)
    high = max(max(row) for row in paths)
    low, high = min(low, 0), max(high, 0)
    x0, y0, width, height = 170, 870, 1580, 560

    def point(index: int, value: float) -> tuple[float, float]:
        x = x0 + index / (count - 1) * width
        y = y0 - (value - low) / (high - low) * height
        return x, y

    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    _brand_header(
        draw,
        "ONE RESULT BECOMES A RANGE OF PATHS",
        "Green paths finish profitable. Red paths finish losing or flat.",
    )
    draw.rounded_rectangle((88, 260, 1832, 950), radius=22,
                           fill=PANEL, outline=GRID, width=3)
    for tick in range(5):
        value = low + tick / 4 * (high - low)
        y = point(0, value)[1]
        draw.line((x0, y, x0 + width, y), fill=GRID, width=2)
        label = f"${value / 1000:.0f}k" if abs(value) >= 1000 else f"${value:.0f}"
        draw.text((x0 - 18, y), label, font=_pil_font(17),
                  fill=MUTED, anchor="rm")

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    rgb = tuple(int(MUTED[index:index + 2], 16) for index in (1, 3, 5))
    outer = [point(i, value) for i, value in enumerate(bands[0.05])]
    outer += [point(i, value) for i, value in reversed(list(enumerate(bands[0.95])))]
    inner = [point(i, value) for i, value in enumerate(bands[0.25])]
    inner += [point(i, value) for i, value in reversed(list(enumerate(bands[0.75])))]
    overlay_draw.polygon(outer, fill=(*rgb, 42))
    overlay_draw.polygon(inner, fill=(*rgb, 92))
    for row in paths:
        path_color = GREEN if row[-1] > 0 else RED
        path_rgb = tuple(int(path_color[index:index + 2], 16) for index in (1, 3, 5))
        overlay_draw.line([point(i, value) for i, value in enumerate(row)],
                          fill=(*path_rgb, 36), width=1)
    image = Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(image)
    if representative is not None:
        draw.line([point(i, value) for i, value in enumerate(representative)],
                  fill=GREEN, width=4)
    draw.line([point(i, value) for i, value in enumerate(bands[0.50])],
              fill=TEXT, width=5)
    zero_y = point(0, 0)[1]
    draw.line((x0, zero_y, x0 + width, zero_y), fill=GOLD, width=3)
    draw.text((x0 + width - 8, zero_y - 10), "$0",
              font=_pil_font(17, True), fill=GOLD, anchor="ra")
    draw.line((x0, y0, x0 + width, y0), fill=MUTED, width=2)
    draw.text((x0, 906), "TRADE 1", font=_pil_font(17), fill=MUTED)
    draw.text((x0 + width, 906), f"TRADE {count}", font=_pil_font(17),
              fill=MUTED, anchor="ra")
    draw.text((126, 286), f"STRATEGY {key.rsplit('-', 1)[-1]}",
              font=_pil_font(20, True), fill=TEXT)
    draw.text((126, 320),
              f"{len(paths)} STORED DISPLAY PATHS / {candidate['metrics']['n_sims']} SIMULATIONS",
              font=_pil_font(17), fill=MUTED)
    legend_x = 1410
    for y, label, fill in (
        (286, f"{len(profitable)} PROFITABLE ENDINGS", GREEN),
        (322, f"{len(losing)} LOSING / FLAT ENDINGS", RED),
        (358, "POINTWISE MEDIAN", TEXT),
        (394, "NEUTRAL BANDS = 50% / 90%", _mix_hex(BG, MUTED, 0.65)),
    ):
        draw.rounded_rectangle((legend_x, y, legend_x + 44, y + 12),
                               radius=6, fill=fill)
        draw.text((legend_x + 60, y - 5), label,
                  font=_pil_font(17, True), fill=MUTED)
    draw.text(
        (960, 985),
        "PATH COLOR REPORTS TERMINAL P&L. NEUTRAL BANDS REPORT POINTWISE QUANTILES.",
        font=_pil_font(20, True), fill=TEXT, anchor="mm",
    )
    draw.text(
        (88, 1042),
        "ORIGINAL TRADERCOCKPIT DATA VISUAL / RECORDED RUN / POINTWISE BANDS",
        font=_pil_font(17), fill=MUTED,
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)


def build_ep04_review_stills(out: Path, phase: dict) -> list[Path]:
    outputs = [
        out / "original-ep04-neighborhood.png",
        out / "original-ep04-fan-chart.png",
    ]
    _draw_ep04_neighborhood(outputs[0])
    _draw_ep04_fan(outputs[1], phase)
    _, candidate, paths, _, profitable, losing, _ = _ep04_fan_data(phase)
    source = PHASES / "phase06_mc_param.json"
    receipt = {
        "schema": "tradercockpit.original-visual-proof/v1",
        "recorded_at": "2026-07-30",
        "tool": "tools/build_series_math_visuals.py + Pillow",
        "external_cost_usd": 0,
        "reference_policy": "supplied screenshots informed the subject only; no screenshot pixels appear",
        "source": {"path": str(source), "sha256": _sha(source)},
        "outputs": {
            path.name: {"sha256": _sha(path), "width": W, "height": H}
            for path in outputs
        },
        "claim_boundary": {
            outputs[0].name: "original illustrative teaching geometry; not run data",
            outputs[1].name: "original visualization of recorded stored display paths and pointwise quantiles",
        },
        "fan_chart_semantics": {
            "stored_display_paths": len(paths),
            "simulations": candidate["metrics"]["n_sims"],
            "profitable_endings_green": len(profitable),
            "losing_or_flat_endings_red": len(losing),
            "bands": "neutral pointwise 5th-95th and 25th-75th percentile bands",
            "zero_line": "explicit",
        },
    }
    _write(out / "original-ep04-review-receipt.json",
           json.dumps(receipt, indent=2) + "\n")
    return outputs


def _chalkboard(out: Path, title: str, subtitle: str, items: list[str],
                layout: str = "checklist") -> None:
    """Draw an owned explainer board that can later animate as chalk-on."""
    image = Image.new("RGB", (W, H), "#06110b")
    draw = ImageDraw.Draw(image)
    for y in range(245, 965, 52):
        draw.line((80, y, 1840, y), fill="#0b2116", width=1)
    draw.text((88, 48), "TRADERCOCKPIT / EXPLAINER BOARD",
              font=_pil_font(22, True), fill=GOLD)
    draw.text((88, 100), title, font=_pil_font(48, True), fill="#f4f0df")
    draw.text((88, 166), subtitle, font=_pil_font(24), fill="#bad0c0")
    draw.line((88, 220, 1832, 220), fill="#315a41", width=2)

    if layout == "formula":
        colors = (GREEN, "#f4f0df", RED, "#f4f0df")
        for index, item in enumerate(items):
            draw.text((960, 345 + index * 135), item,
                      font=_pil_font(50 if index != 2 else 62, True),
                      fill=colors[index], anchor="mm")
    elif layout == "stack":
        colors = (GOLD, GREEN, "#f4f0df", RED)
        for index, item in enumerate(items):
            x = 150 + index * 430
            draw.rounded_rectangle((x, 360, x + 360, 690), radius=24,
                                   fill="#0a1a11", outline=colors[index], width=4)
            lines = textwrap.wrap(item, width=15)
            for line_index, line in enumerate(lines):
                draw.text((x + 180, 470 + line_index * 56), line,
                          font=_pil_font(31, True), fill=colors[index],
                          anchor="mm")
            if index < len(items) - 1:
                draw.text((x + 395, 525), "+", font=_pil_font(52, True),
                          fill="#f4f0df", anchor="mm")
    elif layout == "curve":
        x0, y0, x1, y1 = 230, 780, 1460, 330
        draw.line((x0, y0, x1, y0), fill="#bad0c0", width=3)
        draw.line((x0, y0, x0, y1), fill="#bad0c0", width=3)
        points = []
        for index in range(1, 101):
            x = x0 + (x1 - x0) * (index - 1) / 99
            y = y0 - 390 / math.sqrt(index)
            points.append((x, y))
        draw.line(points, fill=GREEN, width=7)
        draw.text((1540, 420), "error", font=_pil_font(32, True), fill="#f4f0df")
        draw.text((1540, 475), "ABOUT 1 / SQRT(N)",
                  font=_pil_font(34, True), fill=GOLD)
        draw.text((1540, 570), "4× runs", font=_pil_font(30, True), fill="#f4f0df")
        draw.text((1540, 620), "≈ ½ error", font=_pil_font(30, True), fill=GREEN)
        draw.text((x0, 830), "FEWER RUNS", font=_pil_font(22), fill="#bad0c0")
        draw.text((x1, 830), "MORE RUNS", font=_pil_font(22), fill="#bad0c0",
                  anchor="ra")
    else:
        for index, item in enumerate(items):
            y = 315 + index * 105
            draw.rectangle((145, y, 190, y + 45), outline=GREEN, width=4)
            draw.line((154, y + 24, 168, y + 37), fill=GREEN, width=4)
            draw.line((168, y + 37, 185, y + 9), fill=GREEN, width=4)
            draw.text((225, y - 2), item, font=_pil_font(34, True),
                      fill="#f4f0df")

    draw.line((88, 1000, 1832, 1000), fill="#315a41", width=2)
    draw.text((88, 1024),
              "ORIGINAL TRADERCOCKPIT DRAW-ON DESIGN / REVIEW STILL",
              font=_pil_font(17), fill="#bad0c0")
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out)


def build_chalkboard_review_stills(out: Path) -> dict[str, Path]:
    specs = {
        "strategy-checklist.png": (
            "WRITE THE STRATEGY BEFORE TESTING IT",
            "TWO TRADERS SHOULD PLACE THE SAME TRADES FROM THE SAME PLAN",
            ["ENTRY RULE", "EXIT RULE", "POSITION SIZE", "LOSS RULE",
             "COSTS + FILLS", "STOP-USING RULE"], "checklist",
        ),
        "profit-factor-arithmetic.png": (
            "PROFIT FACTOR IS DIVISION",
            "USE THE SAME TRADES AND COSTS IN BOTH PILES",
            ["GROSS WINNING DOLLARS", "÷", "GROSS LOSING DOLLARS",
             "1.0 = BREAK-EVEN"], "formula",
        ),
        "test-plan-checklist.png": (
            "LOCK THE TEST PLAN BEFORE THE ANSWER",
            "THE HOLDOUT STAYS UNTOUCHED UNTIL THE RULES ARE FROZEN",
            ["DATES + UNIVERSE", "DATA FILE HASHES", "WARM-UP + COSTS",
             "VERSIONS SEARCHED", "MEASUREMENTS", "UNCERTAINTY METHOD"],
            "checklist",
        ),
        "transaction-cost-stack.png": (
            "NAME EACH COST COMPONENT",
            "SLIPPAGE WITHOUT A BENCHMARK HAS NO STABLE MEANING",
            ["COMMISSION", "BID-ASK SPREAD", "MARKET IMPACT",
             "MOVEMENT BEFORE FILL"], "stack",
        ),
        "trade-cost-units.png": (
            "MAKE THE UNITS TRAVEL WITH THE COST",
            "CONVERT TO ONE DOLLAR UNIT BEFORE MULTIPLYING",
            ["COST PER SIDE", "×", "2 SIDES", "× ROUND TRIPS / CONTRACTS"],
            "formula",
        ),
        "simulation-error.png": (
            "MORE RUNS MAKE THE CALCULATION STEADIER",
            "THEY DO NOT MAKE THE UNCERTAINTY MODEL TRUER",
            [], "curve",
        ),
    }
    outputs = {}
    for name, (title, subtitle, items, layout) in specs.items():
        path = out / name
        _chalkboard(path, title, subtitle, items, layout)
        outputs[name] = path
    return outputs


def _slot_speech(path: Path) -> dict[str, str]:
    speech: dict[str, list[str]] = {}
    slot = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"=== SLOT\s+(\S+)", raw)
        if match:
            slot = match.group(1)
            speech[slot] = []
        elif slot and raw and not raw.startswith("#"):
            speech[slot].append(raw.strip())
    return {key: " ".join(value) for key, value in speech.items()}


def _fit_lines(draw: ImageDraw.ImageDraw, value: str,
               font: ImageFont.FreeTypeFont, max_width: int,
               max_lines: int) -> list[str]:
    words = value.split()
    lines: list[str] = []
    while words and len(lines) < max_lines:
        line = words.pop(0)
        while words and draw.textbbox((0, 0), line + " " + words[0],
                                      font=font)[2] <= max_width:
            line += " " + words.pop(0)
        lines.append(line)
    if words:
        lines[-1] = lines[-1].rstrip(".,;:") + "…"
    return lines


def _mixed_media_frame(source: Path, episode: str, slot: str, mode: str,
                       speech: str, treatment: str, out: Path) -> None:
    base = ImageOps.fit(Image.open(source).convert("RGB"), (960, 540),
                        method=Image.Resampling.LANCZOS)
    image = base.copy()
    draw = ImageDraw.Draw(image, "RGBA")
    if mode == "CARD":
        image = Image.new("RGB", (960, 540), BG)
        image.paste(ImageOps.fit(base, (410, 540), method=Image.Resampling.LANCZOS),
                    (550, 0))
        draw = ImageDraw.Draw(image, "RGBA")
        draw.rounded_rectangle((30, 90, 530, 475), radius=18,
                               fill=(8, 3, 10, 242), outline=GRID, width=2)
    else:
        draw.rectangle((0, 0, 960, 82), fill=(8, 3, 10, 225))
        draw.rectangle((0, 400, 960, 540), fill=(8, 3, 10, 228))
    draw.text((28, 18), f"EP{episode} / {slot.upper()}",
              font=_pil_font(20, True), fill=TEXT)
    badge_box = draw.textbbox((0, 0), mode, font=_pil_font(16, True))
    badge_width = badge_box[2] - badge_box[0] + 30
    draw.rounded_rectangle((932 - badge_width, 18, 932, 52), radius=10,
                           fill=RED)
    draw.text((917, 35), mode, font=_pil_font(16, True),
              fill=TEXT, anchor="rm")
    draw.text((28, 60), "REVIEW ROUTE / NOT FINAL FRAME",
              font=_pil_font(13, True), fill=GOLD)
    text_x = 55 if mode == "CARD" else 28
    text_y = 125 if mode == "CARD" else 416
    text_width = 440 if mode == "CARD" else 890
    font = _pil_font(19 if mode == "CARD" else 17, True)
    excerpt = speech or treatment
    for index, line in enumerate(_fit_lines(draw, excerpt, font, text_width, 4)):
        draw.text((text_x, text_y + index * 28), line, font=font, fill=TEXT)
    if mode == "CARD":
        treatment_font = _pil_font(14)
        for index, line in enumerate(
                _fit_lines(draw, treatment, treatment_font, 440, 3)):
            draw.text((55, 350 + index * 22), line, font=treatment_font,
                      fill=MUTED)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.save(out, quality=92, subsampling=0)


def build_mixed_media_review() -> dict:
    coverage_path = ROOT / "productions" / "_series" / "academic-visual-coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    review_root = (
        PROJECTS / "series-01-backtest-is-not-a-strategy" /
        "snapshots" / "math-asset-review"
    )
    support_root = (
        PROJECTS / "series-01-backtest-is-not-a-strategy" /
        "snapshots" / "support-media-review"
    )
    chart = (
        PROJECTS / "series-01-backtest-is-not-a-strategy" /
        "hyperframes" / "assets" / "images" / "tradingview-es1-1h.png"
    )
    chalkboards = build_chalkboard_review_stills(
        PROJECTS / "series-01-backtest-is-not-a-strategy" /
        "snapshots" / "chalkboard-review"
    )
    trader = support_root / "trader-desk-monitors.png"
    projects = {
        "01": "series-01-backtest-is-not-a-strategy",
        "02": "series-02-out-of-sample",
        "03": "series-03-slippage",
        "04": "series-04-mc-param",
    }
    overrides = {
        ("01", "scene-01"): ("REAL CHART", chart),
        ("01", "scene-03"): ("CHALKBOARD DRAW-ON", chalkboards["strategy-checklist.png"]),
        ("01", "scene-04"): ("CHALKBOARD DRAW-ON", chalkboards["profit-factor-arithmetic.png"]),
        ("01", "scene-13"): ("TRADER CONTEXT", trader),
        ("02", "scene-twins"): ("CARD", review_root / "ep02-sample-uncertainty.png"),
        ("02", "scene-406"): ("CHALKBOARD DRAW-ON", chalkboards["simulation-error.png"]),
        ("02", "scene-diy"): ("CHALKBOARD DRAW-ON", chalkboards["test-plan-checklist.png"]),
        ("03", "scene-stack"): ("CHALKBOARD DRAW-ON", chalkboards["transaction-cost-stack.png"]),
        ("03", "scene-formula"): ("CHALKBOARD DRAW-ON", chalkboards["transaction-cost-stack.png"]),
        ("03", "scene-cliff"): ("CARD", review_root / "ep03-response-curves.png"),
        ("03", "scene-count"): ("CHALKBOARD DRAW-ON", chalkboards["trade-cost-units.png"]),
        ("03", "scene-scar"): ("TRADER CONTEXT", trader),
        ("04", "scene-mc"): ("CHALKBOARD DRAW-ON", chalkboards["simulation-error.png"]),
        ("04", "scene-casualty"): ("CARD", review_root / "ep04-field-scatter.png"),
        ("04", "scene-limits"): ("CHALKBOARD DRAW-ON", chalkboards["simulation-error.png"]),
    }
    modes: dict[str, int] = {}
    scenes: list[dict] = []
    filmstrips: dict[str, dict] = {}
    for episode, data in coverage["episodes"].items():
        script = ROOT / data["script"]
        speech = _slot_speech(script)
        frames = []
        for slot, route in data["slots"].items():
            mode, source = overrides.get(
                (episode, slot),
                ("ANIMATED MATH", review_root / Path(route["assets"][0]).with_suffix(".png").name),
            )
            if not source.exists():
                raise FileNotFoundError(source)
            out = (
                PROJECTS / projects[episode] / "snapshots" /
                "academic-mixed-media" / f"{slot}.jpg"
            )
            _mixed_media_frame(
                source, episode, slot, mode, speech.get(slot, ""),
                route["treatment"], out,
            )
            modes[mode] = modes.get(mode, 0) + 1
            frames.append(out)
            scenes.append({
                "episode": episode,
                "slot": slot,
                "mode": mode,
                "source": str(source.relative_to(ROOT)).replace("\\", "/"),
                "source_sha256": _sha(source),
                "review_frame": str(out.relative_to(ROOT)).replace("\\", "/"),
                "review_frame_sha256": _sha(out),
                "receipts": route["receipts"],
                "treatment": route["treatment"],
            })
        columns = 3
        thumb_w, thumb_h, gap = 640, 360, 18
        rows = math.ceil(len(frames) / columns)
        sheet = Image.new("RGB", (columns * thumb_w + (columns + 1) * gap,
                                  rows * thumb_h + (rows + 1) * gap), BG)
        for index, frame in enumerate(frames):
            thumb = ImageOps.fit(Image.open(frame).convert("RGB"), (thumb_w, thumb_h),
                                 method=Image.Resampling.LANCZOS)
            x = gap + (index % columns) * (thumb_w + gap)
            y = gap + (index // columns) * (thumb_h + gap)
            sheet.paste(thumb, (x, y))
        sheet_path = (
            PROJECTS / "series-01-backtest-is-not-a-strategy" /
            "snapshots" / f"original-ep{episode}-mixed-media-filmstrip.jpg"
        )
        sheet.save(sheet_path, quality=92, subsampling=0)
        filmstrips[episode] = {
            "path": str(sheet_path.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha(sheet_path),
            "scene_count": len(frames),
            "width": sheet.width,
            "height": sheet.height,
        }
    receipt = {
        "schema": "tradercockpit.mixed-media-asset-review/v1",
        "recorded_at": "2026-07-30",
        "status": "candidate_asset_review",
        "coverage": {"episodes": 4, "scene_slots": len(scenes), "mode_counts": modes},
        "policy": {
            "full_render_started": False,
            "generated_math": False,
            "supplied_reference_pixels_used": False,
            "trader_context_is_synthetic_non_evidence": True,
            "real_chart_is_context_not_performance_evidence": True,
        },
        "inputs": {
            "coverage": {
                "path": str(coverage_path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": _sha(coverage_path),
            },
            "chalkboards": {
                name: {
                    "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": _sha(path),
                }
                for name, path in chalkboards.items()
            },
        },
        "filmstrips": filmstrips,
        "scenes": scenes,
    }
    receipt_path = ROOT / "productions" / "_series" / "mixed-media-asset-review-receipt.json"
    _write(receipt_path, json.dumps(receipt, indent=2) + "\n")
    return receipt


def build_canonical_idea_artifacts() -> dict[str, dict]:
    """Replace the rejected lab brief with the approved meaning-first series brief."""
    coverage_path = ROOT / "productions" / "_series" / "academic-visual-coverage.json"
    review_path = ROOT / "productions" / "_series" / "mixed-media-asset-review-receipt.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    projects = {
        "01": "series-01-backtest-is-not-a-strategy",
        "02": "series-02-out-of-sample",
        "03": "series-03-slippage",
        "04": "series-04-mc-param",
    }
    core = {
        "01": {
            "message": "A backtest is one historical measurement inside a complete, testable trading process.",
            "points": [
                "A green historical result is not a forecast or a complete strategy.",
                "Written entry, exit, size, loss, cost, and stop rules must come before the verdict.",
                "Profit factor, drawdown, and return-to-drawdown answer different questions.",
                "The recorded intake run reduced 1,335 versions to 184 without turning survivors into winners.",
                "Later untouched prices must remain separate from the choices made on development data.",
            ],
        },
        "02": {
            "message": "A held-out result is stronger evidence only when the strategy was frozen before the later block was opened.",
            "points": [
                "Development, warm-up, frozen-rule, and holdout windows must be named in time order.",
                "All 184 held-out results matter; selecting the best after comparison changes the question.",
                "Out-of-sample status does not repair bad data, fills, dependence, or missing regimes.",
                "Sample uncertainty changes continuously; 100 trades is not a universal magic threshold.",
                "A holdout becomes development information once its result changes the next version.",
            ],
        },
        "03": {
            "message": "A trading-cost stress test is credible only when another person can reproduce exactly what changed and what stayed fixed.",
            "points": [
                "Commission, spread, impact, and movement before the fill are different cost components.",
                "Per-side, round-trip, per-contract, and per-order units must be reconciled before multiplication.",
                "The recorded test re-priced the same saved trades at 2x and 3x slippage assumptions.",
                "All 53 response curves matter more than a single survivor or casualty.",
                "The fixed-ledger calculation is a sensitivity check, not a fill simulator or universal cost rule.",
            ],
        },
        "04": {
            "message": "Monte Carlo run count is meaningful only after one run, the uncertainty model, and the remaining error are defined.",
            "points": [
                "The recorded experiment randomly perturbed exit settings while entry logic stayed fixed.",
                "A plateau and an isolated spike encode different parameter-neighborhood risk.",
                "The 5th percentile is a lower-tail summary, not the worst path or a universal guarantee.",
                "The run stored 100 display paths from 200 simulations; terminal outcome color and pointwise bands encode different facts.",
                "More independent runs reduce simulation error but do not make the model truer.",
            ],
        },
    }
    outputs: dict[str, dict] = {}
    for episode, project_id in projects.items():
        project = PROJECTS / project_id
        marker = json.loads((project / "project.json").read_text(encoding="utf-8"))
        script_path = ROOT / coverage["episodes"][episode]["script"]
        speech = _slot_speech(script_path)
        first_slot = next(iter(coverage["episodes"][episode]["slots"]))
        hook = re.split(r"(?<=[.!?])\s+", speech[first_slot], maxsplit=1)[0]
        word_count = sum(len(value.split()) for value in speech.values())
        estimated_duration = round(3 + word_count * 60 / 145, 1)
        episode_scenes = [
            scene for scene in review["scenes"] if scene["episode"] == episode
        ]
        mode_counts: dict[str, int] = {}
        for scene in episode_scenes:
            mode_counts[scene["mode"]] = mode_counts.get(scene["mode"], 0) + 1
        packaging = project / "artifacts" / "packaging.json"
        packaging_data = json.loads(packaging.read_text(encoding="utf-8"))
        packaging_status = str(
            packaging_data.get("STATUS", packaging_data.get("status", "unknown"))
        )
        brief = {
            "version": "1.0",
            "title": marker["title"],
            "hook": hook,
            "key_points": core[episode]["points"],
            "core_message": core[episode]["message"],
            "cta": "Apply the named test to your own process and record the assumptions before looking at the answer.",
            "tone": "Plain English, calm authority, skeptical of conclusions but never hostile to the trader.",
            "style": "Custom TraderCockpit meaning-first atelier: owned red-on-black mathematical motion, exact chalkboard draw-ons, concise cards, real chart context, and sparse trader-at-desk footage.",
            "target_audience": "Retail traders who use backtests or optimizers and want to understand what each robustness test can and cannot establish.",
            "target_platform": "youtube",
            "target_duration_seconds": estimated_duration,
            "reference_material": [
                str(script_path.relative_to(ROOT)).replace("\\", "/"),
                str(coverage_path.relative_to(ROOT)).replace("\\", "/"),
                str(review_path.relative_to(ROOT)).replace("\\", "/"),
                str(packaging.relative_to(ROOT)).replace("\\", "/"),
            ],
            "angle_options": [
                {
                    "name": "Meaning-first academic explainer",
                    "description": "Recommended and visually approved: every sentence routes to the clearest truthful chart, diagram, chalkboard, card, or real workflow shot.",
                },
                {
                    "name": "Generated laboratory metaphor",
                    "description": "Rejected: attractive physical objects do not preserve the mathematical relationship.",
                },
                {
                    "name": "Reference-picture collage",
                    "description": "Rejected: supplied pictures guide subject accuracy but cannot be pasted into the cut.",
                },
            ],
            "selected_angle": "Meaning-first academic explainer",
            "metadata": {
                "status": "awaiting_human",
                "pipeline": "hybrid",
                "anchor_medium": "narration_led_graphics",
                "delivery_promise": "One private 16:9 academic explainer whose visual changes are driven by meaning: exact mathematics for claims, draw-on boards for relationships, cards for narrow definitions, and real trader/chart context only where it helps.",
                "external_media_cost_usd": 0,
                "packaging_status": packaging_status,
                "packaging_approval_open": "AWAITING OPERATOR APPROVAL" in packaging_status,
                "estimated_timing_basis": "3-second fixed ident plus candidate narration estimated at 145 words per minute; replace with measured approved narration durations.",
                "source_inventory": {
                    "candidate_narration": str(script_path.relative_to(ROOT)).replace("\\", "/"),
                    "candidate_narration_sha256": _sha(script_path),
                    "claim_ontology": coverage["episodes"][episode]["ontology"],
                    "approved_math_assets": len({
                        asset
                        for route in coverage["episodes"][episode]["slots"].values()
                        for asset in route["assets"]
                    }),
                    "mixed_media_scene_routes": len(episode_scenes),
                    "mixed_media_mode_counts": mode_counts,
                },
                "support_layers": [
                    "Owned deterministic mathematical visuals with recorded, derived, method, or illustrative labels.",
                    "Original chalkboard draw-on boards for checklists, arithmetic, units, and uncertainty.",
                    "Concise cards only for definitions or limitations that benefit from text beside geometry.",
                    "A real TradingView chart and the existing premium trader-at-desk clip only for workflow or human context.",
                    "YouTube-native caption sidecar after narration timing is locked.",
                ],
                "deliverable_mix": [
                    "One private 1920x1080 YouTube review master.",
                    "No vertical derivatives, upload, schedule, or publication in this run.",
                ],
                "production_plan": {
                    "renderer_family": "bespoke_motion_graphics",
                    "recommended_render_runtime": "hyperframes",
                    "render_runtime_status": "blocked_preflight: OpenMontage registry reported ffmpeg, Remotion, and HyperFrames unavailable on 2026-07-30; HyperFrames specifically reported ffmpeg missing from PATH.",
                    "runtime_alternatives": {
                        "hyperframes": "Recommended for the approved HTML/GSAP-native draw-on and mathematical motion language; blocked until the local runtime is repaired.",
                        "remotion": "Strong alternative for React-native chart and footage composition; also unavailable in the current registry preflight.",
                        "ffmpeg": "Encoding utility only; unavailable in the current registry and not an acceptable static-slide downgrade.",
                    },
                    "composition_mode": "atelier",
                    "visual_generation": "Reuse the approved local mathematics, chalkboards, real chart, and premium trader context. Use Higgsfield Max only if timed scene planning later exposes a specific non-evidentiary motion gap.",
                    "audio": "Qwen / John is the operator-selected source audition. The clean versus clean-deeper processing choice and full narration batch remain gated.",
                    "music": "No music. Preserve the operator's earlier correction and keep the academic voice and arithmetic unobscured.",
                    "fallback_policy": "Stop if the approved motion runtime remains unavailable. Do not silently switch runtimes or reduce the series to static slides.",
                },
                "taste_profile": {
                    "design_read": "A premium retail-trading explainer that earns trust by making every displayed relationship legible and auditable; high information value, low ornament, no laboratory cosplay.",
                    "visual_variance": 8,
                    "motion_intensity": 6,
                    "information_density": 6,
                    "palette_discipline": "TraderCockpit black #08030a, warm white #f5e8ea, red #ff1744, green #00e676, amber #ff9100. Red and green keep trading semantics.",
                    "layout_variation": "Alternate full-frame charts, draw-on boards, field distributions, timelines, response geometry, concise cards, and sparse human context. Never repeat one primary visual merely with a new label.",
                    "reference_strategy": "Use the four approved mixed-media filmstrips as scene-family references. Supplied screenshots remain reference-only.",
                    "anti_patterns": [
                        "generic laboratory objects or AI atmosphere standing in for mathematics",
                        "pasted reference screenshots",
                        "invented curves or losing paths",
                        "unlabeled axes or ambiguous red and green semantics",
                        "caption text duplicating the scene's designed headline",
                    ],
                    "quality_gates": [
                        "Every scene route names a real narrative job and a source hash.",
                        "Factual mathematics remains deterministic and cannot be generated by an image or video model.",
                        "Terminal P&L controls Monte Carlo path color; neutral bands remain pointwise quantiles.",
                        "Important labels remain readable at phone playback size.",
                        "No full render begins before the assets filmstrip is approved.",
                    ],
                },
                "art_direction": {
                    "name": "TraderCockpit Academic Instrument",
                    "palette": "Red-on-black instrument system with semantic green, amber thresholds, and warm-white explanatory type.",
                    "typography": "Cascadia Mono and Consolas; large exact labels; no decorative pseudo-mathematics.",
                    "motion_character": "Causal and readable: draw the axis, reveal the population, move the threshold, perturb the parameter, then show the measured response.",
                    "signature_device": "The test-specific geometry changes every episode while the palette, typography, provenance footer, and semantic color rules remain constant.",
                },
                "canonical_rebuild": {
                    "supersedes": "The rejected nine-scene laboratory treatment and any decorative physical metaphor.",
                    "current_gate": "idea",
                    "next_gate_after_approval": "script",
                    "full_render_started": False,
                },
            },
        }
        brief_path = project / "artifacts" / "brief.json"
        _write(brief_path, json.dumps(brief, indent=2) + "\n")
        decision_path = project / "artifacts" / "decision_log.json"
        decision_log = (
            json.loads(decision_path.read_text(encoding="utf-8"))
            if decision_path.exists()
            else {"version": "1.0", "project_id": project_id, "decisions": []}
        )
        new_decisions = [
            {
                "decision_id": f"d-academic-{episode}-pipeline",
                "stage": "idea",
                "category": "pipeline_selection",
                "subject": "Production pipeline",
                "options_considered": [
                    {
                        "option_id": "hybrid",
                        "label": "Hybrid",
                        "score": 0.96,
                        "reason": "The approved treatment combines narration-led mathematics, real chart and trader context, and designed support layers.",
                    },
                    {
                        "option_id": "animated_explainer",
                        "label": "Animated explainer",
                        "score": 0.72,
                        "reason": "Fits the mathematical layer but understates the real chart and trader-context sources.",
                        "rejected_because": "Hybrid preserves the source-versus-support boundary explicitly.",
                    },
                ],
                "selected": "hybrid",
                "reason": "Hybrid matches the approved five-mode scene routing without treating real context as generated evidence.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 0.96,
            },
            {
                "decision_id": f"d-academic-{episode}-concept",
                "stage": "idea",
                "category": "concept_selection",
                "subject": "Faceless visual concept",
                "options_considered": [
                    {
                        "option_id": "meaning_first_academic",
                        "label": "Meaning-first academic explainer",
                        "score": 1.0,
                        "reason": "Every sentence uses the clearest truthful chart, diagram, chalkboard, card, or workflow shot.",
                    },
                    {
                        "option_id": "generated_laboratory",
                        "label": "Generated laboratory metaphor",
                        "score": 0.05,
                        "reason": "Can create atmosphere but does not preserve mathematical relationships.",
                        "rejected_because": "The operator explicitly rejected the laboratory direction as AI slop.",
                    },
                    {
                        "option_id": "reference_collage",
                        "label": "Reference-picture collage",
                        "score": 0.1,
                        "reason": "Communicates subject matter but would paste supplied references into the cut.",
                        "rejected_because": "The operator requires every displayed visual to be TraderCockpit's own work.",
                    },
                ],
                "selected": "meaning_first_academic",
                "reason": "The operator approved the four 56-scene mixed-media filmstrips and directed production to continue.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 1.0,
            },
            {
                "decision_id": f"d-academic-{episode}-runtime",
                "stage": "idea",
                "category": "render_runtime_selection",
                "subject": "Composition runtime",
                "options_considered": [
                    {
                        "option_id": "hyperframes",
                        "label": "HyperFrames",
                        "score": 0.86,
                        "reason": "Best fit for the approved HTML/GSAP-native draw-on, vector, and mathematical motion language; currently blocked because ffmpeg is not on PATH.",
                    },
                    {
                        "option_id": "remotion",
                        "label": "Remotion",
                        "score": 0.72,
                        "reason": "Strong React-native alternative for chart and footage composition, but the current registry also reports it unavailable.",
                        "rejected_because": "The approved visual system is more naturally expressed by the existing HyperFrames atelier path.",
                    },
                    {
                        "option_id": "ffmpeg",
                        "label": "FFmpeg only",
                        "score": 0.2,
                        "reason": "Useful for final encoding but not sufficient for the approved bespoke motion treatment.",
                        "rejected_because": "Would be a silent downgrade to static or mechanically limited coverage.",
                    },
                ],
                "selected": "hyperframes",
                "reason": "HyperFrames remains the recommended quality path, but rendering must stop until the local runtime is repaired and re-read by the registry.",
                "user_visible": True,
                "user_approved": False,
                "confidence": 0.82,
            },
            {
                "decision_id": f"d-academic-{episode}-composition",
                "stage": "idea",
                "category": "composition_mode",
                "subject": "Composition authoring mode",
                "options_considered": [
                    {
                        "option_id": "atelier",
                        "label": "Atelier",
                        "score": 0.98,
                        "reason": "Preserves the episode-specific geometry, chalkboard drawings, and scene-level visual variance.",
                    },
                    {
                        "option_id": "templated",
                        "label": "Templated",
                        "score": 0.35,
                        "reason": "Faster, but stock scene types would flatten the approved five-mode visual language.",
                        "rejected_because": "The operator is optimizing for production quality and rejected generic visual sameness.",
                    },
                ],
                "selected": "atelier",
                "reason": "The approved filmstrips require hand-authored scene compositions rather than a reusable card spine.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 0.97,
            },
            {
                "decision_id": f"d-academic-{episode}-music",
                "stage": "idea",
                "category": "music_source",
                "subject": "Background music plan",
                "options_considered": [
                    {
                        "option_id": "no_music",
                        "label": "No music",
                        "score": 1.0,
                        "reason": "Keeps arithmetic, definitions, and the approved narrator fully legible and preserves the operator's earlier correction.",
                    },
                    {
                        "option_id": "sparse_instrumental",
                        "label": "Sparse instrumental bed",
                        "score": 0.48,
                        "reason": "Could add energy but would compete with dense spoken explanation and is not needed to solve a scene gap.",
                        "rejected_because": "The operator previously corrected the production to no music.",
                    },
                ],
                "selected": "no_music",
                "reason": "The series will use voice, causal motion, and restrained sound design without a music bed.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 0.99,
            },
        ]
        existing_ids = {
            decision["decision_id"] for decision in decision_log["decisions"]
        }
        decision_log["decisions"].extend(
            decision for decision in new_decisions
            if decision["decision_id"] not in existing_ids
        )
        _write(decision_path, json.dumps(decision_log, indent=2) + "\n")
        outputs[episode] = {
            "project_id": project_id,
            "brief": brief,
            "brief_path": brief_path,
            "brief_sha256": _sha(brief_path),
            "decision_log": decision_log,
            "decision_log_path": decision_path,
            "decision_log_sha256": _sha(decision_path),
        }
    return outputs


def approve_canonical_idea_artifacts() -> dict[str, dict]:
    """Record the approved runtime repair and close the four idea gates."""
    runtime_receipt = (
        ROOT / "productions" / "_series" / "openmontage-runtime-repair-receipt.json"
    )
    projects = {
        "01": "series-01-backtest-is-not-a-strategy",
        "02": "series-02-out-of-sample",
        "03": "series-03-slippage",
        "04": "series-04-mc-param",
    }
    outputs: dict[str, dict] = {}
    for episode, project_id in projects.items():
        project = PROJECTS / project_id
        brief_path = project / "artifacts" / "brief.json"
        decision_path = project / "artifacts" / "decision_log.json"
        brief = json.loads(brief_path.read_text(encoding="utf-8"))
        decision_log = json.loads(decision_path.read_text(encoding="utf-8"))
        runtime_ref = str(runtime_receipt.relative_to(ROOT)).replace("\\", "/")
        if runtime_ref not in brief["reference_material"]:
            brief["reference_material"].append(runtime_ref)
        metadata = brief["metadata"]
        metadata["status"] = "completed"
        plan = metadata["production_plan"]
        plan["render_runtime_status"] = (
            "passed_preflight: HyperFrames 0.7.82 doctor exit 0 on Node 24; "
            "project-local FFmpeg and ffprobe 8.1.2 resolved by OpenMontage."
        )
        plan["runtime_alternatives"] = {
            "hyperframes": (
                "Selected and available. Best fit for the approved HTML/GSAP-native "
                "draw-on, vector, and mathematical motion language."
            ),
            "remotion": (
                "Not available because remotion-composer/node_modules is not installed; "
                "not selected because the approved visual system is HyperFrames-native."
            ),
            "ffmpeg": (
                "Available for encoding and probing, but not an acceptable replacement "
                "for the approved bespoke motion treatment."
            ),
        }
        metadata["canonical_rebuild"]["current_gate"] = "idea_completed"
        metadata["canonical_rebuild"]["next_gate_after_approval"] = "script"
        decision = {
            "decision_id": f"d-academic-{episode}-runtime-repaired",
            "stage": "idea",
            "category": "render_runtime_selection",
            "subject": "Composition runtime",
            "options_considered": [
                {
                    "option_id": "hyperframes",
                    "label": "HyperFrames",
                    "score": 0.98,
                    "reason": (
                        "Available after the project-local repair: HyperFrames 0.7.82, "
                        "Node 24, FFmpeg 8.1.2, ffprobe 8.1.2, and doctor exit 0."
                    ),
                },
                {
                    "option_id": "remotion",
                    "label": "Remotion",
                    "score": 0.72,
                    "reason": (
                        "Strong React-native alternative, but this checkout does not "
                        "have remotion-composer/node_modules installed."
                    ),
                    "rejected_because": (
                        "The approved scene language is HyperFrames-native and its "
                        "selected runtime is now available."
                    ),
                },
                {
                    "option_id": "ffmpeg",
                    "label": "FFmpeg only",
                    "score": 0.2,
                    "reason": "Available for encoding and probing.",
                    "rejected_because": (
                        "FFmpeg-only would not deliver the approved bespoke motion."
                    ),
                },
            ],
            "selected": "hyperframes",
            "reason": (
                "The operator directed repair then continue. The repaired runtime "
                "passes OpenMontage preflight and the HyperFrames CLI doctor."
            ),
            "user_visible": True,
            "user_approved": True,
            "confidence": 0.99,
        }
        existing_ids = {
            item["decision_id"] for item in decision_log["decisions"]
        }
        if decision["decision_id"] not in existing_ids:
            decision_log["decisions"].append(decision)
        _write(brief_path, json.dumps(brief, indent=2) + "\n")
        _write(decision_path, json.dumps(decision_log, indent=2) + "\n")
        outputs[episode] = {
            "project_id": project_id,
            "brief_path": brief_path,
            "brief_sha256": _sha(brief_path),
            "decision_log_path": decision_path,
            "decision_log_sha256": _sha(decision_path),
        }
    return outputs


def build_canonical_scripts() -> dict[str, dict]:
    """Mirror the four approved candidate narrations into script-stage artifacts."""
    coverage_path = ROOT / "productions" / "_series" / "academic-visual-coverage.json"
    review_path = (
        ROOT / "productions" / "_series" / "mixed-media-asset-review-receipt.json"
    )
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    review = json.loads(review_path.read_text(encoding="utf-8"))
    projects = {
        "01": "series-01-backtest-is-not-a-strategy",
        "02": "series-02-out-of-sample",
        "03": "series-03-slippage",
        "04": "series-04-mc-param",
    }
    cue_types = {
        "ANIMATED MATH": "animation",
        "CHALKBOARD DRAW-ON": "diagram",
        "CARD": "stat_card",
        "REAL CHART": "overlay",
        "TRADER CONTEXT": "broll",
    }
    outputs: dict[str, dict] = {}
    for episode, project_id in projects.items():
        project = PROJECTS / project_id
        title = json.loads(
            (project / "project.json").read_text(encoding="utf-8")
        )["title"]
        source_path = ROOT / coverage["episodes"][episode]["script"]
        source_speech = _slot_speech(source_path)
        scene_routes = {
            scene["slot"]: scene
            for scene in review["scenes"]
            if scene["episode"] == episode
        }
        if set(source_speech) != set(scene_routes):
            raise ValueError(
                f"EP{episode} narration slots do not match mixed-media scene routes"
            )
        current = 3.0
        sections = []
        slots = list(source_speech)
        for index, (slot, text) in enumerate(source_speech.items()):
            route = scene_routes[slot]
            duration = len(text.split()) * 60 / 145
            start = round(current, 3)
            current += duration
            end = round(current, 3)
            if index == 0:
                speaker_directions = (
                    "Cold open. Calm, direct, no greeting. Land the claim before "
                    "expanding it."
                )
                energy = "Firm and immediate, then settle into explanation."
            elif index == len(slots) - 1:
                speaker_directions = (
                    "Resolve calmly. No sales cadence; leave the practical standard "
                    "as the final thought."
                )
                energy = "Resolved and useful, without triumph."
            else:
                speaker_directions = (
                    "Speak to one trader. Clear, measured, conversational; let the "
                    "arithmetic and limitations breathe."
                )
                energy = "Calm analytical authority."
            sections.append(
                {
                    "id": slot,
                    "label": slot.removeprefix("scene-").replace("-", " ").title(),
                    "text": text,
                    "start_seconds": start,
                    "end_seconds": end,
                    "speaker_directions": speaker_directions,
                    "delivery_cues": {
                        "pace": "measured",
                        "energy": energy,
                        "emphasis_words": [],
                        "pause_before_seconds": 0 if index == 0 else 0.15,
                        "pause_after_seconds": 0.35,
                        "delivery_note": (
                            "Keep every number and limitation exact. Do not add hype, "
                            "sarcasm, or a promise of performance."
                        ),
                        "provider_text": text,
                    },
                    "enhancement_cues": [
                        {
                            "type": cue_types[route["mode"]],
                            "description": (
                                f"{route['mode']}: {route['treatment']} "
                                f"Approved review source: {route['source']}."
                            ),
                            "timestamp_seconds": round(start + min(0.5, duration / 4), 3),
                        }
                    ],
                    "source_ref": (
                        coverage["episodes"][episode]["ontology"]
                        + "#"
                        + ",".join(route["receipts"])
                    ),
                }
            )
        script = {
            "version": "1.0",
            "title": title,
            "total_duration_seconds": round(current, 3),
            "voice_performance": {
                "performance_intent": (
                    "Plain English, calm authority, speaking to one trader. Explain "
                    "the evidence and its limits without sounding defensive."
                ),
                "pacing_profile": "custom",
                "energy_curve": (
                    "Direct claim, steady teaching cadence, small stakes resets, "
                    "quietly decisive close."
                ),
                "pause_policy": (
                    "Pause after definitions, arithmetic, and scope limitations; "
                    "never rush a number."
                ),
                "sample_section_id": slots[0],
                "provider_notes": {
                    "selected_source": "Qwen / John operator-selected audition",
                    "processing_choice": (
                        "Clean versus clean-deeper remains open; do not batch narration "
                        "before the script gate is approved."
                    ),
                    "timing": (
                        "Section timings are estimates at 145 words per minute after "
                        "the 3-second fixed ident; replace with measured approved audio."
                    ),
                },
            },
            "sections": sections,
            "metadata": {
                "status": "awaiting_human",
                "pipeline": "hybrid",
                "anchor_medium": "narration_led_graphics",
                "source_led_sections": [],
                "support_led_sections": slots,
                "narration_sections": slots,
                "required_support_assets": [
                    {
                        "section_id": section["id"],
                        "mode": scene_routes[section["id"]]["mode"],
                        "source": scene_routes[section["id"]]["source"],
                        "source_sha256": scene_routes[section["id"]]["source_sha256"],
                    }
                    for section in sections
                ],
                "candidate_narration": str(source_path.relative_to(ROOT)).replace(
                    "\\", "/"
                ),
                "candidate_narration_sha256": _sha(source_path),
                "mixed_media_review": str(review_path.relative_to(ROOT)).replace(
                    "\\", "/"
                ),
                "mixed_media_review_sha256": _sha(review_path),
                "exact_text_mirror": True,
                "timing_basis": (
                    "Estimated at 145 words per minute after a 3-second ident; "
                    "not a measured narration duration."
                ),
                "external_media_cost_usd": 0,
                "render_runtime": "hyperframes",
                "composition_mode": "atelier",
                "full_render_started": False,
            },
        }
        if {
            section["id"]: section["text"] for section in script["sections"]
        } != source_speech:
            raise AssertionError(f"EP{episode} canonical script changed narration text")
        script_path = project / "artifacts" / "script.json"
        _write(script_path, json.dumps(script, indent=2) + "\n")
        outputs[episode] = {
            "project_id": project_id,
            "script_path": script_path,
            "script_sha256": _sha(script_path),
            "sections": len(sections),
            "words": sum(len(text.split()) for text in source_speech.values()),
            "estimated_duration_seconds": script["total_duration_seconds"],
        }
    return outputs


def build_canonical_scene_plans() -> dict[str, dict]:
    """Bind every approved script section to its reviewed mixed-media route."""
    review_path = (
        ROOT / "productions" / "_series" / "mixed-media-asset-review-receipt.json"
    )
    review = json.loads(review_path.read_text(encoding="utf-8"))
    projects = {
        "01": "series-01-backtest-is-not-a-strategy",
        "02": "series-02-out-of-sample",
        "03": "series-03-slippage",
        "04": "series-04-mc-param",
    }
    mode_contracts = {
        "ANIMATED MATH": {
            "type": "animation",
            "framing": "Full-frame deterministic geometry with a ten-percent label-safe margin.",
            "movement": "Reveal axes, marks, and comparisons only when the narration names them.",
            "transition_in": "Axis or data-mark draw-on from black.",
            "transition_out": "Hard cut after the relationship is visually complete.",
            "texture": ["instrument", "vector", "deterministic"],
        },
        "CHALKBOARD DRAW-ON": {
            "type": "diagram",
            "framing": "Original full-frame chalkboard with the active line kept phone-readable.",
            "movement": "Write one rule or arithmetic step at a time; hold after each completed step.",
            "transition_in": "First chalk stroke enters on the spoken definition.",
            "transition_out": "Clean board-edge wipe after the completed explanation.",
            "texture": ["chalk", "hand-drawn", "high-contrast"],
        },
        "CARD": {
            "type": "text_card",
            "framing": "One concise definition or limitation beside the underlying geometry.",
            "movement": "Single restrained instrument-card reveal; no kinetic paragraph text.",
            "transition_in": "Instrument panel snap with no decorative flourish.",
            "transition_out": "Hard cut before the next evidence frame.",
            "texture": ["instrument", "concise", "low-ornament"],
        },
        "REAL CHART": {
            "type": "screen_recording",
            "framing": "Full TradingView chart context with the relevant historical area unobscured.",
            "movement": "Use a restrained crop or cursor trace only to identify the discussed region.",
            "transition_in": "Hard cut from the fixed TraderCockpit ident.",
            "transition_out": "Match cut from chart geometry to the next explanatory geometry.",
            "texture": ["real-chart", "source-led", "clean"],
        },
        "TRADER CONTEXT": {
            "type": "broll",
            "framing": "Seated trader and monitors remain recognizable; no chart claim is inferred.",
            "movement": "Use the existing clip's natural motion with at most one restrained crop.",
            "transition_in": "Hard cut to human context after the preceding evidence beat.",
            "transition_out": "Monitor-glow match cut back to explanatory graphics.",
            "texture": ["human-context", "synthetic-labeled", "non-evidentiary"],
        },
    }
    hero_slots = {
        "01": "scene-02",
        "02": "scene-funnel",
        "03": "scene-numbers",
        "04": "scene-fan",
    }
    sizes = ["wide", "insert", "medium_close", "over_shoulder", "close_up", "medium_wide"]
    movements = ["static", "dolly_in", "tracking_left", "zoom_in", "pan_right", "dolly_out"]
    lighting = ["low_key", "rim_lit", "neon", "tungsten_warm"]
    outputs: dict[str, dict] = {}
    for episode, project_id in projects.items():
        project = PROJECTS / project_id
        script_path = project / "artifacts" / "script.json"
        script = json.loads(script_path.read_text(encoding="utf-8"))
        routes = {
            scene["slot"]: scene
            for scene in review["scenes"]
            if scene["episode"] == episode
        }
        section_ids = [section["id"] for section in script["sections"]]
        if section_ids != list(routes):
            raise ValueError(
                f"EP{episode} approved script order does not match mixed-media routes"
            )
        scenes = []
        distinctness = []
        for index, section in enumerate(script["sections"]):
            route = routes[section["id"]]
            contract = mode_contracts[route["mode"]]
            source_path = ROOT / route["source"]
            review_frame = ROOT / route["review_frame"]
            if _sha(source_path) != route["source_sha256"]:
                raise ValueError(f"EP{episode} source hash drift: {route['slot']}")
            if _sha(review_frame) != route["review_frame_sha256"]:
                raise ValueError(f"EP{episode} review-frame hash drift: {route['slot']}")
            is_hero = section["id"] == hero_slots[episode]
            shot_size = "extreme_wide" if is_hero else sizes[index % len(sizes)]
            camera_movement = "dolly_in" if is_hero else movements[index % len(movements)]
            if route["mode"] == "CHALKBOARD DRAW-ON":
                shot_size = "over_shoulder" if index % 2 else "insert"
            elif route["mode"] == "CARD":
                shot_size, camera_movement = "medium_close", "static"
            elif route["mode"] == "REAL CHART":
                shot_size, camera_movement = "over_shoulder", "dolly_in"
            elif route["mode"] == "TRADER CONTEXT":
                shot_size, camera_movement = "medium_wide", "steadicam"
            if index == 0:
                narrative_role = "introduce_subject"
            elif index == len(section_ids) - 1:
                narrative_role = "resolution"
            elif any(word in route["treatment"].lower() for word in ("compare", "contrast", "versus")):
                narrative_role = "comparison"
            elif any(word in route["treatment"].lower() for word in ("actual", "stored", "recorded", "plot")):
                narrative_role = "evidence"
            else:
                narrative_role = "deliver_payload"
            primary_subject = route["treatment"].rstrip(".")
            scene = {
                "id": section["id"],
                "type": contract["type"],
                "description": (
                    f"{route['mode']}: {primary_subject}. "
                    f"Use the reviewed {Path(route['source']).name} construction, "
                    "not a pasted reference or generated metaphor."
                ),
                "start_seconds": 0 if index == 0 else section["start_seconds"],
                "end_seconds": section["end_seconds"],
                "script_section_id": section["id"],
                "framing": contract["framing"],
                "movement": contract["movement"],
                "transition_in": contract["transition_in"],
                "transition_out": (
                    "One-second resolved hold, then clean fade to black."
                    if index == len(section_ids) - 1
                    else contract["transition_out"]
                ),
                "overlay_notes": (
                    "Show only labels, numbers, units, and source limitations needed "
                    "to understand the visual. Never duplicate the spoken sentence "
                    "as both designed text and captions."
                ),
                "shot_language": {
                    "shot_size": shot_size,
                    "camera_movement": camera_movement,
                    "lens_mm": 35 if is_hero else [24, 50, 85][index % 3],
                    "lighting_key": "rim_lit" if is_hero else lighting[index % len(lighting)],
                    "depth_of_field": "deep",
                    "color_temperature": "neutral",
                },
                "shot_intent": (
                    f"{primary_subject}. This is the exact visual job for "
                    f"{section['id']}; motion exposes the relationship without "
                    "adding evidence that is not in the reviewed source."
                ),
                "narrative_role": narrative_role,
                "information_role": primary_subject + ".",
                "hero_moment": is_hero,
                "texture_keywords": contract["texture"],
                "required_assets": [
                    {
                        "type": route["mode"].lower().replace(" ", "_"),
                        "description": (
                            f"{route['source']} sha256={route['source_sha256']}; "
                            f"review frame {route['review_frame']} "
                            f"sha256={route['review_frame_sha256']}."
                        ),
                        "source": "source",
                    }
                ],
            }
            scenes.append(scene)
            distinctness.append(
                {
                    "scene_id": section["id"],
                    "primary_visual_subject": primary_subject,
                    "review_frame": route["review_frame"],
                    "review_frame_sha256": route["review_frame_sha256"],
                    "shares_primary_subject_with_another_scene": False,
                }
            )
        if len({item["primary_visual_subject"] for item in distinctness}) != len(scenes):
            raise ValueError(f"EP{episode} scene plan repeats a primary visual subject")
        plan = {
            "version": "1.0",
            "style_playbook": "tradercockpit-instrument-atelier",
            "scenes": scenes,
            "metadata": {
                "status": "awaiting_human",
                "pipeline": "hybrid",
                "render_runtime": "hyperframes",
                "composition_mode": "atelier",
                "renderer_family": "bespoke_motion_graphics",
                "approved_script_sha256": _sha(script_path),
                "mixed_media_review": str(review_path.relative_to(ROOT)).replace("\\", "/"),
                "mixed_media_review_sha256": _sha(review_path),
                "anchor_rules": (
                    "Narration leads. Every scene's reviewed visual remains primary; "
                    "support labels explain rather than decorate."
                ),
                "support_rules": (
                    "One primary visual per scene. No laboratory metaphors, pasted "
                    "references, generated mathematics, or constant overlay spine."
                ),
                "safe_zones": (
                    "16:9 1920x1080 master; keep essential labels inside a ten-percent "
                    "margin and readable at phone playback size."
                ),
                "variant_rules": (
                    "This gate plans the 16:9 YouTube master only. Any future 9:16 "
                    "derivative requires a separate crop and layout plan."
                ),
                "overlay_density_limits": (
                    "At most one primary diagram plus two short supporting labels; "
                    "never repeat narration verbatim as designed on-screen text."
                ),
                "timing_basis": (
                    "Estimated script timing at 145 words per minute. The first scene "
                    "includes the fixed 0-3 second ident; replace section timing only "
                    "after the approved narration batch is measured."
                ),
                "scene_distinctness": distinctness,
                "scene_distinctness_question": {
                    "do_any_scenes_share_a_primary_visual_subject": False,
                    "signature_device_used_as_scaffolding": False,
                },
                "mode_counts": {
                    mode: sum(1 for route in routes.values() if route["mode"] == mode)
                    for mode in mode_contracts
                },
                "asset_gap_count": 0,
                "higgsfield_allocation": (
                    "No gap identified at scene-plan time. Higgsfield Max remains "
                    "reserved for a later, specific non-evidentiary motion gap."
                ),
                "external_media_cost_usd": 0,
                "full_render_started": False,
            },
        }
        plan_path = project / "artifacts" / "scene_plan.json"
        _write(plan_path, json.dumps(plan, indent=2) + "\n")
        outputs[episode] = {
            "project_id": project_id,
            "scene_plan_path": plan_path,
            "scene_plan_sha256": _sha(plan_path),
            "scenes": len(scenes),
            "mode_counts": plan["metadata"]["mode_counts"],
            "duration_seconds": scenes[-1]["end_seconds"],
        }
    return outputs


def build_canonical_visual_asset_manifests() -> dict[str, dict]:
    """Inventory the approved source for every scene without promoting review stills."""
    review_path = (
        ROOT / "productions" / "_series" / "mixed-media-asset-review-receipt.json"
    )
    review = json.loads(review_path.read_text(encoding="utf-8"))
    projects = {
        "01": "series-01-backtest-is-not-a-strategy",
        "02": "series-02-out-of-sample",
        "03": "series-03-slippage",
        "04": "series-04-mc-param",
    }
    types = {
        "ANIMATED MATH": "diagram",
        "CHALKBOARD DRAW-ON": "diagram",
        "CARD": "image",
        "REAL CHART": "image",
        "TRADER CONTEXT": "image",
    }
    tools = {
        "ANIMATED MATH": "TraderCockpit deterministic math renderer",
        "CHALKBOARD DRAW-ON": "TraderCockpit original chalkboard renderer",
        "CARD": "TraderCockpit instrument-card renderer",
        "REAL CHART": "TradingView native interface capture",
        "TRADER CONTEXT": "TraderCockpit reviewed trader-context source",
    }
    licenses = {
        "REAL CHART": "TradingView interface context; not performance evidence",
        "TRADER CONTEXT": "TraderCockpit-owned synthetic non-evidence context",
    }
    outputs: dict[str, dict] = {}
    for episode, project_id in projects.items():
        project = PROJECTS / project_id
        script_path = project / "artifacts" / "script.json"
        script = json.loads(script_path.read_text(encoding="utf-8"))
        routes = [
            scene for scene in review["scenes"] if scene["episode"] == episode
        ]
        if [section["id"] for section in script["sections"]] != [
            route["slot"] for route in routes
        ]:
            raise ValueError(f"EP{episode} script order does not match asset routes")
        assets = []
        scene_index = []
        for route in routes:
            source = ROOT / route["source"]
            review_frame = ROOT / route["review_frame"]
            if _sha(source) != route["source_sha256"]:
                raise ValueError(f"EP{episode} source hash drift: {route['slot']}")
            if _sha(review_frame) != route["review_frame_sha256"]:
                raise ValueError(
                    f"EP{episode} review-frame hash drift: {route['slot']}"
                )
            with Image.open(source) as image:
                resolution = f"{image.width}x{image.height}"
            relative_source = os.path.relpath(source, project).replace("\\", "/")
            relative_review = os.path.relpath(review_frame, project).replace("\\", "/")
            mode = route["mode"]
            assets.append({
                "id": f"visual-{route['slot']}",
                "type": types[mode],
                "path": relative_source,
                "source_tool": tools[mode],
                "scene_id": route["slot"],
                "cost_usd": 0,
                "resolution": resolution,
                "format": source.suffix.lstrip(".").lower(),
                "subtype": mode.lower().replace(" ", "_").replace("-", "_"),
                "generation_summary": (
                    f"Operator-approved source sha256={route['source_sha256']}; "
                    f"review route sha256={route['review_frame_sha256']}. "
                    "Animate or compose the source according to the approved scene plan; "
                    "the review still is not a final frame."
                ),
                "provider": (
                    "TradingView" if mode == "REAL CHART" else "TraderCockpit"
                ),
                "license": licenses.get(mode, "TraderCockpit-owned"),
            })
            scene_index.append({
                "scene_id": route["slot"],
                "mode": mode,
                "source_path": relative_source,
                "source_sha256": route["source_sha256"],
                "review_frame_path": relative_review,
                "review_frame_sha256": route["review_frame_sha256"],
                "treatment": route["treatment"],
                "receipts": route["receipts"],
            })
        filmstrip = review["filmstrips"][episode]
        manifest = {
            "version": "1.0",
            "assets": assets,
            "total_cost_usd": 0,
            "metadata": {
                "status": "visual_assets_verified_narration_pending",
                "approved_scene_plan_sha256": _sha(
                    project / "artifacts" / "scene_plan.json"
                ),
                "approved_script_sha256": _sha(script_path),
                "mixed_media_review_sha256": _sha(review_path),
                "scene_asset_index": scene_index,
                "filmstrip": {
                    "path": os.path.relpath(
                        ROOT / filmstrip["path"], project
                    ).replace("\\", "/"),
                    "sha256": filmstrip["sha256"],
                    "scene_count": filmstrip["scene_count"],
                },
                "source_vs_generated_map": {
                    "generated_visual_assets": [],
                    "source_visual_assets": [
                        asset["id"] for asset in assets
                    ],
                    "review_stills_are_final_assets": False,
                },
                "visual_asset_gap_count": 0,
                "visual_external_provider_cost_usd": 0,
                "higgsfield_visual_generation_used": False,
                "narration": {
                    "provider": "Higgsfield Qwen",
                    "voice": "John",
                    "approved_treatment": "clean",
                    "clean_deeper": "rejected_by_operator",
                    "batch_status": "pending",
                    "approved_sample_path": os.path.relpath(
                        PROJECTS / "series-04-mc-param" / "artifacts"
                        / "voice-auditions" / "ep04-qwen-john-clean.wav",
                        project,
                    ).replace("\\", "/"),
                    "approved_sample_sha256": (
                        "6d4fa9e01a2183a973829c166f6c0119a7030b28bf9275a0a2e59aa5aca1dfe7"
                    ),
                },
                "music": "none_planned",
                "render_runtime": "hyperframes",
                "composition_mode": "atelier",
                "full_render_started": False,
            },
        }
        manifest_path = project / "artifacts" / "asset_manifest.json"
        _write(manifest_path, json.dumps(manifest, indent=2) + "\n")
        outputs[episode] = {
            "project_id": project_id,
            "asset_manifest_path": manifest_path,
            "asset_manifest_sha256": _sha(manifest_path),
            "visual_assets": len(assets),
        }
    return outputs


def _ep04_perturbation_mechanism() -> str:
    body = [
        _rect(110, 245, 1700, 680),
        _t(240, 330, "FOR EACH NUMERIC EXIT SETTING", 29, TEXT, weight=700),
        _rect(210, 410, 380, 220, "#0d121b", GRID, 16),
        _t(400, 485, "30% chance", 43, BLUE, "middle", 800),
        _t(400, 545, "selected to change", 25, MUTED, "middle"),
        _t(680, 525, "→", 64, GOLD, "middle", 800),
        _rect(770, 410, 430, 220, "#0d121b", GRID, 16),
        _t(985, 480, "multiply by", 25, MUTED, "middle"),
        _t(985, 545, "1 + U(−30%, +30%)", 37, GOLD, "middle", 800),
        _t(1290, 525, "→", 64, GOLD, "middle", 800),
        _rect(1380, 410, 330, 220, "#0d121b", GRID, 16),
        _t(1545, 480, "REPLAY", 37, GREEN, "middle", 800),
        _t(1545, 540, "same entry logic", 24, MUTED, "middle"),
        _t(400, 730, "70% chance: value stays unchanged", 27, MUTED, "middle"),
        _t(960, 855, "Exits-only v1. This is the implemented uncertainty model—not a universal one.", 27, TEXT, "middle", 700),
    ]
    return _svg(
        "THE PARAMETER-PERTURBATION RULE USED IN THIS RUN",
        "SELECTION PROBABILITY AND CHANGE MAGNITUDE ARE TWO DIFFERENT RANDOM STEPS",
        body,
        "RECORDED METHOD · ENTRY RULES STAY FIXED",
    )


def _ep04_p05_rank() -> str:
    body = [_rect(110, 245, 1700, 680)]
    cols = 25
    for i in range(200):
        row, col = divmod(i, cols)
        x, y = 240 + col * 59, 390 + row * 58
        color = RED if i < 10 else BLUE
        body.append(f'<circle cx="{x}" cy="{y}" r="13" fill="{color}" opacity="{1 if i < 10 else .45}"/>')
    body += [
        _t(240, 325, "200 ordered simulation outcomes", 29, TEXT, weight=700),
        _t(1700, 325, "lowest → highest", 25, MUTED, "end"),
        _t(960, 660, "The 5th percentile lies around the tenth ordered outcome.", 31, GOLD, "middle", 750),
        _t(960, 710, "Software may interpolate between ranks; name the quantile convention.", 25, MUTED, "middle"),
        _t(960, 865, "A lower-tail summary is not the same thing as the worst observed path.", 28, TEXT, "middle", 700),
    ]
    return _svg(
        "WHAT THE 5TH PERCENTILE MEANS AT N = 200",
        "ORDER THE RESULTS · THEN READ THE LOWER TAIL",
        body,
        "METHOD DIAGRAM · HYNDMAN & FAN (1996) · NOT RUN VALUES",
    )


def _ep04_tail_resolution() -> str:
    cases = [(0.05, 10, 0.0154, BLUE), (0.01, 2, 0.0070, RED)]
    body = [_rect(110, 245, 1700, 680)]
    for idx, (p, expected, mcse, color) in enumerate(cases):
        y = 410 + idx * 260
        body += [
            _t(230, y + 25, f"{p:.0%} event", 32, color, weight=750),
            _t(510, y + 25, f"{expected} occurrences expected", 31, TEXT, weight=700),
            _t(1110, y + 25, f"MCSE ≈ {mcse:.2%}", 31, GOLD, weight=700),
        ]
        for i in range(200):
            row, col = divmod(i, 50)
            x = 510 + col * 23
            cy = y + 75 + row * 23
            fill = color if i < expected else GRID
            body.append(f'<circle cx="{x}" cy="{cy}" r="7" fill="{fill}" opacity=".9"/>')
        body.append(_t(960, y + 185, "Each dot is one independent path.", 21, MUTED, "middle"))
    body += [_t(960, 910, "Expected counts and MCSE describe simulation noise conditional on the model.", 26, TEXT, "middle", 700)]
    return _svg(
        "LOW-PROBABILITY EVENTS ARE SPARSE AT 200 PATHS",
        "A SMALL COUNT CAN LEAVE LARGE RELATIVE MONTE CARLO ERROR",
        body,
        "DERIVED MATH · INDEPENDENT YES/NO EVENT EXAMPLE",
    )


def _ep04_determinism() -> str:
    labels = [
        ("BASE SEED", 210), ("CANDIDATE", 480), ("PHASE", 750), ("SIM INDEX", 1020),
        ("SHA-256", 1290), ("RNG", 1560),
    ]
    body = [_rect(110, 245, 1700, 680)]
    for i, (label, x) in enumerate(labels):
        body += [
            _rect(x, 390, 210, 115, "#0d121b", GRID, 12),
            _t(x + 105, 458, label, 22, BLUE if i < 4 else GOLD, "middle", 700),
        ]
        if i < len(labels) - 1:
            body.append(_t(x + 240, 460, "→", 34, MUTED, "middle", 700))
    body += [
        _t(960, 610, "RE-DERIVE + REPLAY SIM 0 AND SIM N−1", 33, TEXT, "middle", 750),
        _line(510, 675, 1410, 675, GREEN, 6),
        _t(960, 735, "compare trade hash and return-to-drawdown value", 27, MUTED, "middle"),
        _t(960, 855, "Matching output proves reproducibility of this path—not correctness of the model.", 27, GOLD, "middle", 700),
    ]
    return _svg(
        "CAN THE SAME RANDOM TEST BE REPRODUCED?",
        "THE SAME DECLARED INPUTS MUST REPRODUCE THE SAME SIMULATION",
        body,
        "REPRODUCIBILITY CHECK · SAME DECLARED INPUTS, SAME RESULT",
    )


def _gate_census(phase: dict) -> list[dict]:
    by_name: dict[str, list[dict]] = {}
    for result in phase["candidates"].values():
        for name, gate in result.get("gates", {}).items():
            by_name.setdefault(name, []).append(gate)
    rows = []
    for name, gates in sorted(by_name.items()):
        failed = [gate for gate in gates if gate.get("pass") is False]
        numeric = [
            float(gate["actual"])
            for gate in failed
            if isinstance(gate.get("actual"), (int, float))
            and not isinstance(gate.get("actual"), bool)
        ]
        op = gates[0]["op"]
        threshold = float(gates[0]["threshold"])
        band = 0.10 * abs(threshold)
        if op in {">", ">="}:
            near = sum(0 <= threshold - value < band for value in numeric)
        elif op in {"<", "<="}:
            near = sum(0 <= value - threshold < band for value in numeric)
        else:
            near = 0
        rows.append({
            "gate": name,
            "evaluated_count": len(gates),
            "kill_count": len(failed),
            "failed_with_numeric_actual_count": len(numeric),
            "failed_with_null_actual_count": len(failed) - len(numeric),
            "median_failed_actual": _q(numeric, 0.5) if numeric else None,
            "op": op,
            "threshold": gates[0]["threshold"],
            "near_miss_lt_10pct_count": near,
        })
    return sorted(rows, key=lambda row: (-row["kill_count"], row["gate"]))


def _evidence_snapshot(sources: dict[str, Path], phases: dict[str, dict]) -> dict:
    code_graph = json.loads(CODE_GRAPH.read_text(encoding="utf-8"))
    ops_graph = json.loads(OPS_GRAPH.read_text(encoding="utf-8"))
    return {
        "schema": "series-academic-evidence-snapshot/v1",
        "captured_date": "2026-07-30",
        "authority_order": [
            "exact run artifacts and implementation at the stamped Futures commit",
            "authoritative Markdown cited by the vault graph",
            "academic literature identified in each episode claims file",
        ],
        "graphs": {
            "futures_code_graph": {
                "path": str(CODE_GRAPH),
                "sha256": _sha(CODE_GRAPH),
                "source_commit": code_graph["graph"]["source_commit"],
                "nodes": len(code_graph["nodes"]),
                "links": len(code_graph["links"]),
                "communities": len({
                    node.get("community") for node in code_graph["nodes"]
                }),
                "hyperedges": len(code_graph.get("hyperedges", [])),
            },
            "ops_vault_graph": {
                "path": str(OPS_GRAPH),
                "sha256": _sha(OPS_GRAPH),
                "revision": ops_graph["graph"]["revision"],
                "source_commit": ops_graph["graph"]["source_commit"],
                "nodes": len(ops_graph["nodes"]),
                "links": len(ops_graph["links"]),
                "purpose": ops_graph["graph"]["purpose"],
            },
            "rebuild_receipt": {
                "path": str(CODE_GRAPH_RECEIPT),
                "sha256": _sha(CODE_GRAPH_RECEIPT),
            },
        },
        "run_artifacts": {
            name: {"path": str(path), "sha256": _sha(path)}
            for name, path in sources.items()
        },
        "funnel": {
            name: {
                "entering": len(phase["entering"]),
                "surviving": len(phase["surviving"]),
                "dropped": len(phase["entering"]) - len(phase["surviving"]),
                "window": phase["window"],
                "gate_census": _gate_census(phase),
            }
            for name, phase in phases.items()
        },
        "interpretation_receipt": {
            "finding": (
                "The high phase01 near-miss count is concentrated around "
                "profit factor 1.0; it is break-even noise in this population, "
                "not evidence that the thresholds rejected a near-winner."
            ),
            "source": (
                r"C:\Users\MSI\repos\futures\docs\vault"
                r"\SESSION-HANDOFF-2026-07-29-gate-margins-and-merge-wave.md"
            ),
            "limitations": (
                "This is a finding about the recorded candidate population and "
                "declared gates. It is not a universal claim about every generator."
            ),
        },
        "implementation_boundary": {
            "gate_margin_recording_repair": (
                "Proven on origin/fix/gate-margins but not present on the "
                "stamped main commit. The videos may use the re-derived census, "
                "but must not claim the recording repair is deployed on main."
            ),
            "run_provenance": (
                "The rb-20260725T133803-b44bd92c artifacts declare "
                "validated=false and wiring_proof=true; they support measured "
                "run facts, not future-performance claims."
            ),
        },
    }


def build(out: Path, install: bool) -> dict:
    ep01, p01 = _phase("phase01_intake")
    ep01_golden, p01_golden = _golden_phase("phase01_intake")
    ep02, p02 = _phase("phase02_oos")
    phase03, p03_parked = _phase("phase03_timing")
    ep03, p03 = _phase("phase04_cost")
    ep04, p04 = _phase("phase06_mc_param")
    visuals = {
        "ep01-backtest-vs-strategy.svg": _ep01_backtest_vs_strategy(),
        "ep01-golden-arithmetic.svg": _ep01_golden_arithmetic(ep01_golden),
        "ep01-win-rate-payoff.svg": _ep01_win_rate_payoff(ep01_golden),
        "ep01-drawdown-path.svg": _ep01_drawdown(ep01_golden),
        "ep01-intake-funnel.svg": _ep01_intake_funnel(ep01),
        "ep01-profit-factor-near-misses.svg": _ep01_profit_factor_near_misses(ep01),
        "ep01-threshold-motion.svg": _ep01_threshold_motion(ep01),
        "ep01-survivor-status.svg": _ep01_survivor_status(ep01),
        "ep01-holdout-boundary.svg": _ep02_timeline(ep02),
        "ep02-ordered-holdout.svg": _ep02_timeline(ep02),
        "ep02-oos-field-distribution.svg": _ep02_distribution(ep02),
        "ep02-concentration-stress.svg": _ep02_concentration(ep02),
        "ep02-selected-maximum.svg": _ep02_selected_maximum(ep02),
        "ep02-walk-forward.svg": _ep02_walk_forward(),
        "ep02-sample-uncertainty.svg": _ep02_sample_uncertainty(),
        "ep03-cost-anatomy.svg": _ep03_cost_anatomy(),
        "ep03-field-transitions.svg": _ep03_transitions(ep03),
        "ep03-response-curves.svg": _ep03_response_curves(ep03),
        "ep03-fixed-ledger-formula.svg": _ep03_fixed_ledger_formula(),
        "ep03-order-type-tradeoff.svg": _ep03_order_tradeoff(),
        "ep03-cost-drivers.svg": _ep03_cost_drivers(),
        "ep04-run-count-error.svg": _ep04_mcse(),
        "ep04-field-scatter.svg": _ep04_field(ep04),
        "ep04-fan-chart.svg": _ep04_fan(ep04),
        "ep04-response-geometry.svg": _ep04_geometry(),
        "ep04-perturbation-mechanism.svg": _ep04_perturbation_mechanism(),
        "ep04-p05-rank.svg": _ep04_p05_rank(),
        "ep04-tail-resolution.svg": _ep04_tail_resolution(),
        "ep04-reproducibility-check.svg": _ep04_determinism(),
    }
    for name, svg in visuals.items():
        _write(out / name, svg)
        if install:
            episode = {"ep01": "series-01-backtest-is-not-a-strategy",
                       "ep02": "series-02-out-of-sample",
                       "ep03": "series-03-slippage",
                       "ep04": "series-04-mc-param"}[name[:4]]
            _write(PROJECTS / episode / "hyperframes" / "assets" / "math" / name, svg)
    receipt = {
        "schema": "series-math-visuals/v2",
        "run_id": RUN_ID,
        "sources": {
            "phase01_intake": {"path": str(p01), "sha256": _sha(p01)},
            "golden_cross_phase01_intake": {
                "run_id": GOLDEN_RUN_ID,
                "path": str(p01_golden),
                "sha256": _sha(p01_golden),
            },
            "phase02_oos": {"path": str(p02), "sha256": _sha(p02)},
            "phase03_parked": {"path": str(p03_parked), "sha256": _sha(p03_parked)},
            "phase04_cost": {"path": str(p03), "sha256": _sha(p03)},
            "phase06_mc_param": {"path": str(p04), "sha256": _sha(p04)},
        },
        "outputs": {name: _sha(out / name) for name in visuals},
        "labels": {
            "run_data": [name for name in visuals if "backtest-vs" not in name
                         and "anatomy" not in name
                         and "run-count" not in name and "geometry" not in name
                         and "sample-uncertainty" not in name
                         and "walk-forward" not in name
                         and "order-type" not in name and "cost-drivers" not in name
                         and "p05-rank" not in name and "tail-resolution" not in name
                         and "fixed-ledger" not in name
                         and "perturbation-mechanism" not in name
                         and "reproducibility-check" not in name],
            "derived_or_method": [
                "ep01-backtest-vs-strategy.svg",
                "ep02-walk-forward.svg",
                "ep02-sample-uncertainty.svg",
                "ep03-cost-anatomy.svg",
                "ep03-order-type-tradeoff.svg",
                "ep03-cost-drivers.svg",
                "ep04-run-count-error.svg",
                "ep04-p05-rank.svg",
                "ep04-tail-resolution.svg"
            ],
            "implementation_receipt": [
                "ep03-fixed-ledger-formula.svg",
                "ep04-perturbation-mechanism.svg",
                "ep04-reproducibility-check.svg"
            ],
            "illustrative": [
                "ep01-backtest-vs-strategy.svg",
                "ep04-response-geometry.svg",
            ],
        },
    }
    evidence_snapshot = _evidence_snapshot(
        {
            "phase01_intake": p01,
            "golden_cross_phase01_intake": p01_golden,
            "phase02_oos": p02,
            "phase03_parked": p03_parked,
            "phase04_cost": p03,
            "phase06_mc_param": p04,
        },
        {
            "phase01_intake": ep01,
            "phase02_oos": ep02,
            "phase03_parked": phase03,
            "phase04_cost": ep03,
            "phase06_mc_param": ep04,
        },
    )
    receipt["evidence_snapshot_sha256"] = hashlib.sha256(
        (json.dumps(evidence_snapshot, indent=2) + "\n").encode()
    ).hexdigest()
    receipt_text = json.dumps(receipt, indent=2) + "\n"
    _write(out / "receipt.json", receipt_text)
    evidence_text = json.dumps(evidence_snapshot, indent=2) + "\n"
    _write(EVIDENCE_SNAPSHOT, evidence_text)
    if install:
        for episode in (
            "series-01-backtest-is-not-a-strategy",
            "series-02-out-of-sample",
            "series-03-slippage",
            "series-04-mc-param",
        ):
            _write(PROJECTS / episode / "hyperframes" / "assets" / "math" / "receipt.json",
                   receipt_text)
            _write(
                PROJECTS / episode / "artifacts" / "academic-evidence-snapshot.json",
                evidence_text,
            )
    return receipt


def demo() -> None:
    assert abs(_q([0, 10, 20], 0.25) - 5) < 1e-9
    sample = _svg("T", "S", [_t(10, 10, "A&B")], "P")
    assert "A&amp;B" in sample and sample.endswith("</svg>\n")
    stable_neighbors = sum(_response_value(dx, dy, True)
                           for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    spike_neighbors = sum(_response_value(dx, dy, False)
                          for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    assert stable_neighbors > spike_neighbors * 3
    synthetic = {
        "candidates": {
            "formula-1-3106": {
                "display": {"param_paths": [[-1, 2], [1, -2], [0, 0]]}
            }
        }
    }
    _, _, _, _, profitable, losing, representative = _ep04_fan_data(synthetic)
    assert len(profitable) == 1 and len(losing) == 2 and representative[-1] == 2
    sample_image = Image.new("RGB", (20, 20), BG)
    sample_draw = ImageDraw.Draw(sample_image)
    lines = _fit_lines(sample_draw, "one two three four", _pil_font(10), 40, 2)
    assert len(lines) == 2 and lines[-1].endswith("…")
    print("PASS: quantiles, SVG escaping, neighborhood contrast, P&L colors, and review text")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=PREVIEW)
    parser.add_argument("--install", action="store_true",
                        help="also copy each visual into its episode assets/math folder")
    parser.add_argument("--review-stills", action="store_true",
                        help="build original Episode 04 asset-gate review stills")
    parser.add_argument("--mixed-media-review", action="store_true",
                        help="build sentence-level mixed-media asset review filmstrips")
    parser.add_argument("--canonical-ideas", action="store_true",
                        help="write the four meaning-first canonical idea briefs")
    parser.add_argument("--approve-canonical-ideas", action="store_true",
                        help="record the repaired runtime and close the four idea gates")
    parser.add_argument("--canonical-scripts", action="store_true",
                        help="write the four exact-text canonical script artifacts")
    parser.add_argument("--canonical-scene-plans", action="store_true",
                        help="bind the approved scripts to the 56 reviewed scene routes")
    parser.add_argument("--canonical-visual-assets", action="store_true",
                        help="write verified visual asset manifests for all four episodes")
    parser.add_argument(
        "--review-out",
        type=Path,
        default=PROJECTS / "series-01-backtest-is-not-a-strategy" / "snapshots",
    )
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    if args.demo:
        demo()
        return 0
    if args.review_stills:
        phase, _ = _phase("phase06_mc_param")
        outputs = build_ep04_review_stills(args.review_out, phase)
        print("wrote " + ", ".join(str(path) for path in outputs))
        return 0
    if args.mixed_media_review:
        receipt = build_mixed_media_review()
        print(
            f"wrote {receipt['coverage']['scene_slots']} review frames "
            f"across {len(receipt['filmstrips'])} episode filmstrips"
        )
        return 0
    if args.canonical_ideas:
        outputs = build_canonical_idea_artifacts()
        for episode, data in outputs.items():
            print(f"EP{episode} {data['brief_sha256']} {data['brief_path']}")
        return 0
    if args.approve_canonical_ideas:
        outputs = approve_canonical_idea_artifacts()
        for episode, data in outputs.items():
            print(f"EP{episode} {data['brief_sha256']} {data['brief_path']}")
        return 0
    if args.canonical_scripts:
        outputs = build_canonical_scripts()
        for episode, data in outputs.items():
            print(
                f"EP{episode} {data['script_sha256']} "
                f"{data['sections']} sections {data['words']} words "
                f"{data['estimated_duration_seconds']}s {data['script_path']}"
            )
        return 0
    if args.canonical_scene_plans:
        outputs = build_canonical_scene_plans()
        for episode, data in outputs.items():
            print(
                f"EP{episode} {data['scene_plan_sha256']} "
                f"{data['scenes']} scenes {data['duration_seconds']}s "
                f"{data['scene_plan_path']}"
            )
        return 0
    if args.canonical_visual_assets:
        outputs = build_canonical_visual_asset_manifests()
        for episode, data in outputs.items():
            print(
                f"EP{episode} {data['asset_manifest_sha256']} "
                f"{data['visual_assets']} visual assets "
                f"{data['asset_manifest_path']}"
            )
        return 0
    receipt = build(args.out, args.install)
    print(f"wrote {len(receipt['outputs'])} visuals and receipt to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
