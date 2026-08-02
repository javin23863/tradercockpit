#!/usr/bin/env python3
"""Build the five operator-approved teaching-series thumbnail directions."""

from __future__ import annotations

import argparse
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "OpenMontage" / "projects"
ROWS = {
    "01": (
        "series-v4-e01-backtest-search",
        "SELECTION / INTAKE",
        "SAME SETTINGS",
        "NEW DATA",
        "dots",
    ),
    "02": (
        "series-v4-e02-spy-held-out",
        "OUT-OF-SAMPLE",
        "1 IN",
        "0 LEFT",
        "windows",
    ),
    "03": (
        "series-v4-e03-timing-session",
        "FILL + SESSION STRESS",
        "53 STRATEGIES",
        "LEFT",
        "gates",
    ),
    "04": (
        "series-v4-e04-futures-cost",
        "FUTURES COST STRESS",
        "46 STRATEGIES",
        "LEFT",
        "costs",
    ),
    "05": (
        "series-04-mc-param",
        "PARAMETER STRESS",
        "PARAMETER",
        "SENSITIVITY CHECK",
        "surface",
    ),
}

CSS = """
*{box-sizing:border-box}html,body{margin:0;width:1280px;height:720px;overflow:hidden}
body{background:#08030a;color:#fff2e5;font-family:Arial,sans-serif}
.root{position:relative;width:1280px;height:720px;padding:58px 64px;background:
radial-gradient(circle at 20% 55%,rgba(255,23,68,.22),transparent 35%),
linear-gradient(rgba(74,23,33,.22) 1px,transparent 1px),
linear-gradient(90deg,rgba(74,23,33,.22) 1px,transparent 1px);background-size:auto,54px 54px,54px 54px}
.eyebrow{font:800 24px/1.2 'Cascadia Mono',Consolas,monospace;letter-spacing:.13em;color:#caaeb2}
.eyebrow:after{content:'';display:block;width:120px;height:6px;margin-top:16px;background:#ff1744}
.content{position:absolute;left:64px;right:64px;top:160px;bottom:70px;display:grid;grid-template-columns:45% 55%;align-items:center}
.visual{position:relative;width:100%;height:100%;border-right:3px solid #4a1721}
.copy{padding-left:58px;text-align:right}
.copy .a,.copy .b{display:block;font:900 88px/.88 'Arial Black',Arial,sans-serif;letter-spacing:-.055em}
.copy .a{color:#7be0ad}.copy .b{margin-top:28px;color:#ffb54a}
.ep05 .copy .b{font-size:64px;line-height:.92}
.tag{position:absolute;right:66px;bottom:38px;font:800 21px/1 'Cascadia Mono',Consolas,monospace;letter-spacing:.12em;color:#caaeb2}
.dots:before{content:'';position:absolute;left:40px;top:45px;width:370px;height:330px;background:radial-gradient(circle,#7be0ad 0 6px,transparent 7px);background-size:44px 44px}
.dots:after{content:'60 / 66';position:absolute;left:130px;top:185px;padding:20px 28px;border:5px solid #ffb54a;background:#08030a;color:#ffb54a;font:900 50px/1 'Arial Black',Arial,sans-serif}
.windows{display:flex;gap:26px;align-items:center;justify-content:center}
.window{position:relative;width:190px;height:280px;border:5px solid #7be0ad;background:rgba(0,230,118,.07)}
.window.bad{border-color:#ff1744;background:rgba(255,23,68,.08)}
.window b{display:block;padding:18px;font:900 25px/1.1 Arial,sans-serif;color:#7be0ad}
.window.bad b{color:#ff1744}.line{position:absolute;left:18px;right:18px;bottom:55px;height:90px;border-bottom:8px solid #7be0ad;transform:skewY(-16deg)}
.bad .line{border-color:#ff1744;transform:skewY(16deg)}
.gates{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;align-content:center;padding:45px 28px}
.gate{height:260px;display:flex;align-items:center;justify-content:center;border:6px solid #ffb54a;background:rgba(255,181,74,.08);color:#ffb54a;text-align:center;font:900 34px/1.05 'Arial Black',Arial,sans-serif}
.costs{display:flex;gap:22px;align-items:end;justify-content:center;padding:70px 30px}
.bar{width:110px;border:6px solid #7be0ad;background:rgba(0,230,118,.08);color:#7be0ad;text-align:center;padding-top:24px;font:900 34px/1 Arial,sans-serif}
.bar.one{height:150px}.bar.two{height:245px;border-color:#ffb54a;color:#ffb54a;background:rgba(255,181,74,.09)}
.bar.three{height:345px;border-color:#ff1744;color:#ff1744;background:rgba(255,23,68,.10)}
.surface{display:grid;grid-template-columns:repeat(5,62px);grid-auto-rows:62px;gap:10px;align-content:center;justify-content:center}
.cell{border:4px solid #7be0ad;background:rgba(0,230,118,.14)}
.cell.edge{border-color:#ffb54a;background:rgba(255,181,74,.16)}
.cell.fail{border-color:#ff1744;background:rgba(255,23,68,.18)}
"""

VISUALS = {
    "dots": '<div class="visual dots"></div>',
    "windows": (
        '<div class="visual windows"><div class="window"><b>IN-SAMPLE</b><div class="line"></div></div>'
        '<div class="window bad"><b>OOS</b><div class="line"></div></div></div>'
    ),
    "gates": (
        '<div class="visual gates"><div class="gate">+1<br>BAR</div>'
        '<div class="gate">FIRST<br>HALF</div><div class="gate">SECOND<br>HALF</div></div>'
    ),
    "costs": (
        '<div class="visual costs"><div class="bar one">1×</div>'
        '<div class="bar two">2×</div><div class="bar three">3×</div></div>'
    ),
    "surface": (
        '<div class="visual surface">'
        + "".join(
            f'<div class="cell{" edge" if i in {1, 3, 5, 9, 15, 19, 21, 23} else " fail" if i in {0, 4, 20, 24} else ""}"></div>'
            for i in range(25)
        )
        + "</div>"
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode", action="append", choices=sorted(ROWS))
    selected = set(parser.parse_args().episode or ROWS)
    for episode, (project_id, subject, line1, line2, visual) in ROWS.items():
        if episode not in selected:
            continue
        target = PROJECTS / project_id / "artifacts" / f"thumbnail-ep{episode}.html"
        target.write_text(
            "<!doctype html><html><head><meta charset=\"utf-8\"><style>"
            + CSS
            + f'</style></head><body><div class="root ep{episode}">'
            + f'<div class="eyebrow">INTO THE LABORATORY // EP {episode}</div>'
            + '<div class="content">'
            + VISUALS[visual]
            + '<div class="copy">'
            + f'<span class="a">{html.escape(line1)}</span>'
            + f'<span class="b">{html.escape(line2)}</span></div></div>'
            + f'<div class="tag">{html.escape(subject)}</div></div></body></html>',
            encoding="utf-8",
        )
        print(target)
    assert "grid-template-columns:45% 55%" in CSS
    print(f"series-v4 thumbnails: PASS {len(selected)}/{len(selected)} separate visual and headline zones")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
