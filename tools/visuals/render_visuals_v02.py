#!/usr/bin/env python3
"""Render video-02-hormuz visuals: 3 tc-chart cards (04/06/08) + 2 tc-card cards (07/09).

Durations come from productions/video-02-hormuz/build/sections.json (VO stage output) when
present; otherwise every section falls back to --dur-default so charts can be rendered before
the VO stage completes.

Run (any python3; rendering shells out to node + studio-kit renderer):
  python render_visuals_v02.py [--only NN] [--dur-default 40]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
HUB = HERE.parent.parent
PROD = HUB / "productions" / "video-02-hormuz"
VIS = PROD / "visuals"
CHART_DATA = PROD / "build" / "chart-data.json"
RENDERER = HUB / "studio-kit" / "pipeline" / "generators" / "html3d-render.cjs"
COMP_CARD = HUB / "studio-kit" / "pipeline" / "generators" / "compositions" / "tc-card.html"
COMP_CHART = HUB / "studio-kit" / "pipeline" / "generators" / "compositions" / "tc-chart.html"
PAD_S = 1.0

# All numbers verified against FACTS-2026-07-13.md — copy exactly, do not invent or extend.
CARDS = {
    "07": {"kicker": "rotation — wednesday jul 8 spike day (last clean read)",
           "title": "The **war-premium** rotation",
           "lines": ["<span class='ok'>energy up</span>: Diamondback +3% · Occidental +2.5% · Chevron +2%",
                     "<span class='bad'>fuel burners down</span>: Carnival −3.5% · United −3% · Delta −2%",
                     "utilities held · tech lagged"],
           "bg": "corridor"},
    "09": {"kicker": "scenarios — explicitly NOT predictions",
           "title": "If the strait stays **broken**",
           "lines": ["JPMorgan: Brent 120–130, overshoot risk 150",
                     "model: one-quarter Gulf halt → WTI ≈ 110",
                     "conditional models from banks — <b>I do not predict</b>"],
           "bg": "bulb"},
}


def build_charts(static):
    """CHARTS dict (04/06/08) -- built from build/chart-data.json so numbers trace to one source."""
    return {
        "04": {
            "kicker": "the oil tape — 2026-07-13",
            "title": "",
            "series_key": "brent", "series_label": "BRENT",
            "markers": [
                {"date": "2026-03-10", "value": static["brent_mar_peak"], "label": "march peak ~126", "style": "peak"},
                {"value": static["brent_fri_close"], "label": "friday close 76.56", "style": "level"},
                {"date": None, "value": static["brent_sun_reopen"], "label": "sun reopen 78.67", "style": "now"},
            ],
            "bignum": {"value": "78.67", "delta": "+3.5%", "label": "brent — sunday futures reopen"},
            "lines": ["friday close 76.56 · +5% on week", "march precedent: 126 peak"],
        },
        "06": {
            "kicker": "friday's market never saw the weekend",
            "title": "S&P 7,575 · VIX 15 — a quiet-summer number",
            "series_key": "spx", "series_label": "S&P 500", "inset_key": "vix", "inset_label": "VIX",
            "markers": [
                {"date": None, "value": static["spx_fri"], "label": "spx 7,575.39", "style": "now"},
            ],
            "bignum": {"value": "15.03", "delta": "-5.1%", "label": "VIX friday close"},
            "lines": ["S&P +1% on week · Nasdaq 26,281", "fear gauge closed BEFORE the strait closed"],
        },
        "08": {
            "kicker": "the hedge that isn't hedging",
            "title": "",
            "series_key": "gold", "series_label": "GOLD",
            "markers": [
                {"date": "2026-01-28", "value": static["gold_ath"], "label": "jan 28 ATH 5,595", "style": "peak"},
                {"date": None, "value": static["gold_now"], "label": "now ~4,100", "style": "now"},
            ],
            "bignum": {"value": "4,100", "delta": "-13%", "label": "from January high"},
            "lines": ["DXY 100.94 · 10-year 4.56%", "dollar + yields outweigh the fear trade"],
        },
    }


def load_durations(dur_default):
    sec_path = PROD / "build" / "sections.json"
    if sec_path.exists():
        sections = {s["num"]: s for s in json.loads(sec_path.read_text(encoding="utf-8"))}
        return {num: sections[num]["duration"] for num in sections}, sections
    print(f"[warn] no sections.json -- using --dur-default {dur_default}s for all sections")
    return {}, {}


def run_render(comp, out, dur, label):
    print(f"[render] {label} {dur:.1f}s -> {out.name}")
    r = subprocess.run(["node", str(RENDERER), "--html", str(comp),
                        "--out", str(out), "--fps", "30", "--dur", f"{dur:.2f}",
                        "--w", "1920", "--h", "1080", "--nopost"], shell=True)
    if r.returncode:
        sys.exit(f"render failed on {label}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--only")
    p.add_argument("--dur-default", type=float, default=40.0)
    args = p.parse_args()

    durations, sections = load_durations(args.dur_default)
    VIS.mkdir(parents=True, exist_ok=True)

    if not CHART_DATA.exists():
        sys.exit(f"missing {CHART_DATA} -- run fetch_chart_data.py first")
    chart_data = json.loads(CHART_DATA.read_text(encoding="utf-8"))
    CHARTS = build_charts(chart_data["static"])

    for num, card in CARDS.items():
        if args.only and num != args.only:
            continue
        out = VIS / f"{num}-card.mp4"
        if out.exists():
            print(f"[skip] {out.name}")
            continue
        dur = durations.get(num, args.dur_default) + PAD_S
        (COMP_CARD.parent / "cfg.json").write_text(json.dumps(card), encoding="utf-8")
        run_render(COMP_CARD, out, dur, f"{num} ({sections.get(num, {}).get('slug', 'card')})")

    for num, chart in CHARTS.items():
        if args.only and num != args.only:
            continue
        out = VIS / f"{num}-chart.mp4"
        if out.exists():
            print(f"[skip] {out.name}")
            continue
        dur = durations.get(num, args.dur_default) + PAD_S
        main_data = chart_data[chart["series_key"]]
        series = [{"label": chart["series_label"], "dates": main_data["dates"], "closes": main_data["closes"]}]
        if "inset_key" in chart:
            inset_data = chart_data[chart["inset_key"]]
            series.append({"label": chart["inset_label"], "dates": inset_data["dates"], "closes": inset_data["closes"]})
        cfg = {"kicker": chart["kicker"], "title": chart["title"], "series": series,
               "markers": chart["markers"], "bignum": chart["bignum"], "lines": chart["lines"],
               "dur": dur}
        (COMP_CHART.parent / "cfg.json").write_text(json.dumps(cfg), encoding="utf-8")
        run_render(COMP_CHART, out, dur, f"{num} ({sections.get(num, {}).get('slug', 'chart')})")

    print("video-02 visuals done.")


if __name__ == "__main__":
    main()
