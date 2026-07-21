#!/usr/bin/env python3
"""Capture REAL TradingView candlestick charts for the video's finance sections.

Replaces the old custom-drawn line charts (and the abstract bulb/corridor cards) with
actual candlestick screenshots from TradingView Desktop, driven through the tradingview-mcp
`tv` CLI (same CDP bridge the broker import uses). Each chart gets a slow Ken-Burns
zoom so it reads as motion, not a static slide.

Sections it produces (into productions/<prod>/visuals/):
  04-chart  Brent crude       06-chart  S&P 500 (+ VIX beat)   08-chart  gold
  07-card   energy sector      09-card   Brent w/ scenario context

Prereqs (like docs/BROKERS.md): TradingView Desktop running with
--remote-debugging-port=9222, and repos/tradingview-mcp present (npm installed).

    python tools/visuals/fetch_tv_charts.py productions/video-02-hormuz
    python tools/visuals/fetch_tv_charts.py productions/video-02-hormuz --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
HUB = HERE.parents[1]
TV_CLI = Path(r"C:\Users\MSI\repos\tradingview-mcp\src\cli\index.js")

# section -> TradingView symbol + timeframe. Symbols chosen for clean TradingView
# coverage; timeframe "6M"/"12M" = the chart's visible range button equivalent.
CHARTS = [
    {"out": "04-chart", "symbol": "TVC:UKOIL", "tf": "1D", "label": "BRENT CRUDE"},
    {"out": "06-chart", "symbol": "SP:SPX", "tf": "1D", "label": "S&P 500"},
    {"out": "08-chart", "symbol": "TVC:GOLD", "tf": "1D", "label": "GOLD"},
    {"out": "07-card", "symbol": "AMEX:XLE", "tf": "1D", "label": "ENERGY SECTOR (XLE)"},
    {"out": "09-card", "symbol": "TVC:UKOIL", "tf": "1W", "label": "BRENT — SCENARIO RANGE"},
]
DEFAULT_DUR = 30.0  # assemble trims/boomerangs each to its VO section length
CAPTURE_RECEIPT_SCHEMA = "tradercockpit-chart-capture-receipts/v1"


def record_chart_capture(prod: Path, artifact: Path, captured_at: datetime) -> dict:
    """Record the final chart artifact once, at the shared production-output boundary."""
    prod, artifact = prod.resolve(), artifact.resolve()
    if captured_at.tzinfo is None:
        raise ValueError("captured_at must include a timezone")
    try:
        relative = artifact.relative_to(prod).as_posix()
    except ValueError as error:
        raise ValueError(f"chart artifact must stay inside production: {artifact}") from error
    if not artifact.is_file():
        raise FileNotFoundError(artifact)

    receipt_path = prod / "chart-capture-receipts.json"
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if receipt.get("schema") != CAPTURE_RECEIPT_SCHEMA or not isinstance(receipt.get("captures"), list):
            raise ValueError(f"invalid chart capture receipt: {receipt_path}")
        if any(not isinstance(item, dict) or not item.get("path") for item in receipt["captures"]):
            raise ValueError(f"invalid chart capture entries: {receipt_path}")
    else:
        receipt = {"schema": CAPTURE_RECEIPT_SCHEMA, "captures": []}

    with artifact.open("rb") as handle:
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
    entry = {
        "path": relative,
        "capturedAt": captured_at.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "sha256": digest,
    }
    receipt["captures"] = sorted(
        [item for item in receipt["captures"] if item.get("path") != relative] + [entry],
        key=lambda item: str(item.get("path", "")),
    )
    # ponytail: capture jobs are local and serial; add a file lock only if parallel capture is introduced.
    temporary = receipt_path.with_name(f"{receipt_path.name}.tmp")
    temporary.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    temporary.replace(receipt_path)
    return entry


def tv(args: list[str], dry: bool) -> dict:
    """Run a `tv` CLI command, return parsed JSON. Raises on failure."""
    if dry:
        print(f"  [dry] tv {' '.join(args)}")
        return {}
    if not TV_CLI.exists():
        sys.exit(f"tradingview-mcp not found at {TV_CLI} — clone + npm install it")
    proc = subprocess.run(["node", str(TV_CLI), *args], capture_output=True, text=True, timeout=90)
    if proc.returncode != 0:
        hint = " — is TradingView Desktop running with --remote-debugging-port=9222?" if proc.returncode == 2 else ""
        sys.exit(f"tv {' '.join(args)} exited {proc.returncode}: {(proc.stderr or proc.stdout).strip()[:200]}{hint}")
    try:
        return json.loads(proc.stdout)
    except ValueError:
        return {}


def ken_burns(png: Path, out: Path, dur: float, dry: bool) -> None:
    """Slow zoom-in on the chart PNG so it has motion (not a static slide)."""
    frames = int(dur * 30)
    # zoompan zooms from 1.0 to ~1.12 across the clip, centered; scale up first so the
    # zoom stays crisp, then output 1920x1080 CFR30. Fit-and-pad to 16:9 BEFORE zoompan —
    # zoompan maps its window to s= exactly, so non-16:9 input (windowed TV chart region)
    # came out squashed (video-02 defect, fixed 2026-07-14).
    vf = (f"scale=3840:2160:force_original_aspect_ratio=decrease,"
          f"pad=3840:2160:(ow-iw)/2:(oh-ih)/2:black,"
          f"zoompan=z='min(zoom+0.0008,1.12)':d={frames}"
          f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps=30,format=yuv420p")
    if dry:
        print(f"  [dry] ffmpeg ken-burns {png.name} -> {out.name} ({dur:.0f}s)")
        return
    subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(png), "-t", f"{dur:.2f}",
                    "-vf", vf, "-c:v", "h264_nvenc", "-cq", "19", "-preset", "p5",
                    str(out)], check=True, capture_output=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prod", help="production folder, e.g. productions/video-02-hormuz")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--dur", type=float, default=DEFAULT_DUR)
    a = ap.parse_args()

    prod = (HUB / a.prod) if not Path(a.prod).is_absolute() else Path(a.prod)
    visuals = prod / "visuals"
    visuals.mkdir(parents=True, exist_ok=True)

    for c in CHARTS:
        print(f"[{c['out']}] {c['label']} ({c['symbol']} {c['tf']})")
        tv(["symbol", c["symbol"]], a.dry_run)
        tv(["timeframe", c["tf"]], a.dry_run)
        tv(["type", "Candles"], a.dry_run)   # ensure candlesticks, not line
        shot = tv(["screenshot", "--region", "chart", "--output", c["out"]], a.dry_run)
        captured_at = datetime.now(timezone.utc)
        png = Path(shot.get("file_path")) if shot.get("file_path") else \
            TV_CLI.parents[1] / "screenshots" / f"{c['out']}.png"
        out = visuals / f"{c['out']}.mp4"
        ken_burns(png, out, a.dur, a.dry_run)
        if not a.dry_run:
            record_chart_capture(prod, out, captured_at)
            print(f"  -> {out}")

    print("\nDONE" if not a.dry_run else "\nDRY RUN OK — no TradingView driven, no render.")
    print("note: sections 07/09 are now real charts (energy sector, Brent scenario) — the")
    print("bulb/corridor cards are retired. News-headline B-roll can layer over 07/09 later.")
    return 0


def selftest() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        prod = Path(tmp) / "productions" / "test"
        artifact = prod / "visuals" / "chart.mp4"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"chart")
        captured_at = datetime(2026, 7, 20, tzinfo=timezone.utc)
        entry = record_chart_capture(prod, artifact, captured_at)
        receipt = json.loads((prod / "chart-capture-receipts.json").read_text(encoding="utf-8"))
        assert receipt["schema"] == CAPTURE_RECEIPT_SCHEMA
        assert receipt["captures"] == [entry]
        assert entry["sha256"] == hashlib.sha256(b"chart").hexdigest()
    print("CHART CAPTURE RECEIPT SELFTEST PASS")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    else:
        raise SystemExit(main())
