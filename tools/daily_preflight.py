#!/usr/bin/env python3
"""Preflight or refuse. Everything the night needs, probed live, before anything renders.

The 2026-07-27 stall looked like a mystery from the outside: the lane started, ran for
hours, and produced nothing. Every one of these conditions fails that way -- silently,
late, after tokens and GPU minutes are already spent. Probe them first and say which one.

    python tools/daily_preflight.py [--json] [--require-pvc]

Exit 1 on any BLOCK. WARN never blocks; it is the state the lane is knowingly in.
"""
from __future__ import annotations

import argparse
import json
import shutil
import socket
import subprocess
import sys
from pathlib import Path

try:
    from tools.tts_elevenlabs import load_env
except ImportError:  # direct `python tools/daily_preflight.py` execution
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tts_elevenlabs import load_env

ROOT = Path(__file__).resolve().parents[1]
TV_CDP_PORT = 9222
# Upper bound of one night at the shipped 1,450-1,700 word budget and the measured 5.90
# chars/word (docs/DAILY-LANE-OVERHAUL-PLAN.md B4). A night that cannot be paid for must
# not start: mid-render exhaustion leaves a half-narrated production and a stalled lane.
NIGHT_CHARS = 10_332
DISK_FLOOR_GB = 20


def check(name, status, detail):
    return {"check": name, "status": status, "detail": detail}


def tradingview():
    with socket.socket() as probe:
        probe.settimeout(1)
        up = probe.connect_ex(("127.0.0.1", TV_CDP_PORT)) == 0
    return check("tradingview", "PASS" if up else "BLOCK",
                 f"CDP :{TV_CDP_PORT} {'reachable' if up else 'unreachable'}; "
                 "charts-before-script cannot run without it")


def elevenlabs(require_pvc=False):
    """Key, remaining quota, and whether the voice is still the instant clone."""
    import os

    import requests

    key, voice = os.environ.get("ELEVENLABS_API_KEY"), os.environ.get("ELEVEN_VOICE_ID")
    if not key or not voice:
        return [check("elevenlabs-key", "BLOCK", "ELEVENLABS_API_KEY / ELEVEN_VOICE_ID absent "
                                                 "from the environment and repo .env")]
    rows = [check("elevenlabs-key", "PASS", "key and voice id present")]
    headers = {"xi-api-key": key}
    try:
        sub = requests.get("https://api.elevenlabs.io/v1/user/subscription",
                           headers=headers, timeout=20).json()
        used, limit = int(sub["character_count"]), int(sub["character_limit"])
        left = limit - used
        rows.append(check(
            "elevenlabs-quota", "PASS" if left >= NIGHT_CHARS else "BLOCK",
            f"{left:,} of {limit:,} chars left on tier {sub.get('tier')}; "
            f"one night costs up to {NIGHT_CHARS:,}"))
    except (requests.RequestException, KeyError, ValueError, TypeError) as error:
        rows.append(check("elevenlabs-quota", "BLOCK", f"subscription probe failed: {error}"))
    try:
        category = requests.get(f"https://api.elevenlabs.io/v1/voices/{voice}",
                                headers=headers, timeout=20).json().get("category")
        professional = category == "professional"
        rows.append(check(
            "elevenlabs-voice",
            "PASS" if professional else ("BLOCK" if require_pvc else "WARN"),
            f"voice category is {category!r}; the operator paid for a professional clone "
            "and the lane is still rendering the instant one"))
    except (requests.RequestException, ValueError) as error:
        rows.append(check("elevenlabs-voice", "BLOCK", f"voice probe failed: {error}"))
    return rows


def youtube():
    try:
        from publish import youtube_readiness
    except ModuleNotFoundError:
        from tools.publish import youtube_readiness
    try:
        probe = youtube_readiness()
    except Exception as error:  # any transport/credential shape counts as not ready
        return check("youtube", "BLOCK", f"readiness probe failed: {type(error).__name__}: {error}")
    return check("youtube", "PASS" if probe.get("ready") else "BLOCK",
                 f"status={probe.get('status')}; the private upload is the deliverable")


def disk():
    free_gb = shutil.disk_usage(ROOT).free / 1024 ** 3
    return check("disk", "PASS" if free_gb >= DISK_FLOOR_GB else "BLOCK",
                 f"{free_gb:.1f} GB free on the repo volume, floor {DISK_FLOOR_GB} GB")


def pagefile():
    """A pinned pagefile kills TTS with OSError 1455 while the GPU sits at 4% idle."""
    try:
        probe = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-CimInstance Win32_ComputerSystem).AutomaticManagedPagefile"],
            capture_output=True, text=True, timeout=60,
        )
        managed = probe.stdout.strip().lower() == "true"
    except (OSError, subprocess.SubprocessError) as error:
        return check("pagefile", "WARN", f"could not read the pagefile setting: {error}")
    return check("pagefile", "PASS" if managed else "WARN",
                 f"AutomaticManagedPagefile={managed}; a pinned pagefile fails TTS with "
                 "OSError 1455 midway through the render")


def verdict(rows):
    """PASS / WARN / BLOCK for the whole night. Pure, so the branches are self-testable."""
    if any(row["status"] == "BLOCK" for row in rows):
        return "BLOCK"
    return "WARN" if any(row["status"] == "WARN" for row in rows) else "PASS"


def run(require_pvc=False):
    load_env()
    rows = [tradingview(), *elevenlabs(require_pvc), youtube(), disk(), pagefile()]
    return {"verdict": verdict(rows), "checks": rows}


def selftest():
    assert verdict([check("a", "PASS", "")]) == "PASS"
    assert verdict([check("a", "PASS", ""), check("b", "WARN", "")]) == "WARN"
    assert verdict([check("a", "WARN", ""), check("b", "BLOCK", "")]) == "BLOCK"
    # the instant clone warns by default and blocks only once the PVC is meant to be live
    assert check("elevenlabs-voice", "WARN", "")["status"] == "WARN"
    print("daily-preflight selftest: 4/4 PASS")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--require-pvc", action="store_true",
                        help="promote the instant-clone WARN to a BLOCK (re-arm criterion 3)")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        selftest()
        return 0
    report = run(args.require_pvc)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"DAILY PREFLIGHT {report['verdict']}")
        for row in report["checks"]:
            print(f"  {row['status']:5} {row['check']}: {row['detail']}")
    return 1 if report["verdict"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
