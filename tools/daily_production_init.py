#!/usr/bin/env python3
"""Scaffold the day's production folder and report what the content step still owes.

The post-close lane has two halves and only one of them is a script:

    AGENT STEP   research -> analysis brief -> chart capture -> vo.txt -> claims.yaml
                 -> scene-plan.json -> draft social-batch.json      (needs an LLM)
    RUNNER STEP  render -> gates -> machine approval -> publish     (tools/daily_postclose.py)

`produce.py` never creates the folder and no script writes `vo.txt` — the
daily-news-video skill does, and that is an agent action. So arming the runner alone
gives an unattended PUBLISH of whatever an agent wrote earlier, not an unattended lane.

This module is the contract between the halves: it mints the folder with a deterministic
name so the scheduler does not have to be told a path, and it answers one question
honestly — is this production ready for the runner, and if not, exactly what is missing.

    python tools/daily_production_init.py --init          # mint today's folder
    python tools/daily_production_init.py --check         # readiness, exit 1 if not ready
    python tools/daily_production_init.py --check --json  # machine-readable
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRODUCTIONS = ROOT / "productions"

# What the runner reads. Each entry is (filename, who owes it, why the runner needs it).
REQUIRED = (
    ("vo.txt", "agent", "script_style_gate + the exact-hash approval bind to it"),
    ("claims.yaml", "agent", "claims_gate maps every number-bearing region to a receipt"),
    ("scene-plan.json", "agent", "editorial_gate validates beats against visible subjects"),
    ("analysis-brief.md", "agent", "script_approval binds the production to its brief"),
    ("news-sources.json", "agent", "source provenance for the claims ledger"),
    ("social-batch.json", "agent", "publish.py publishes exactly one approved v2 item"),
)
OPTIONAL = (("vo-receipts.yaml", "agent", "per-claim receipt detail"),)


def eastern_now(utc: datetime | None = None) -> datetime:
    """US/Eastern without tzdata — this box has no system tz database (verified 2026-07-20).

    Second Sunday in March 02:00 -> first Sunday in November 02:00 is EDT (-4), else EST (-5).
    """
    utc = utc or datetime.now(timezone.utc)
    year = utc.year

    def nth_sunday(month: int, nth: int) -> datetime:
        day = datetime(year, month, 1, tzinfo=timezone.utc)
        day += timedelta(days=(6 - day.weekday()) % 7)  # first Sunday
        return day + timedelta(weeks=nth - 1)

    dst_start = nth_sunday(3, 2) + timedelta(hours=7)   # 02:00 EST == 07:00 UTC
    dst_end = nth_sunday(11, 1) + timedelta(hours=6)    # 02:00 EDT == 06:00 UTC
    offset = -4 if dst_start <= utc < dst_end else -5
    return utc + timedelta(hours=offset)


def slug_for(day: datetime | None = None) -> str:
    """Deterministic folder name so the scheduler never needs a path argument."""
    day = day or eastern_now()
    return f"daily-{day:%Y-%m-%d}"


def production_path(day: datetime | None = None) -> Path:
    return PRODUCTIONS / slug_for(day)


def init(day: datetime | None = None) -> dict:
    """Mint the folder. Idempotent: never overwrites an existing file."""
    path = production_path(day)
    path.mkdir(parents=True, exist_ok=True)
    (path / "build").mkdir(exist_ok=True)
    (path / "visuals").mkdir(exist_ok=True)

    manifest = path / "OWED.md"
    if not manifest.exists():
        lines = [
            f"# {path.name} — what the content step owes\n",
            "\nThe runner (`tools/daily_postclose.py`) will not publish without these. "
            "It fails closed and pings rather than shipping a partial production.\n\n",
        ]
        for name, owner, why in REQUIRED:
            lines.append(f"- [ ] `{name}` ({owner}) — {why}\n")
        for name, owner, why in OPTIONAL:
            lines.append(f"- [ ] `{name}` ({owner}, optional) — {why}\n")
        lines.append(
            "\nEditorial frame is the **post-close recap**: what the session did, on settled "
            "closing prints, never pre-open positioning. See the daily-news-video skill.\n"
        )
        manifest.write_text("".join(lines), encoding="utf-8")
    return check(day)


def check(day: datetime | None = None) -> dict:
    """Readiness. `ready` is true only when every required artifact exists and is non-empty."""
    path = production_path(day)
    missing, present = [], []
    for name, owner, why in REQUIRED:
        target = path / name
        if target.is_file() and target.stat().st_size > 0:
            present.append(name)
        else:
            missing.append({"file": name, "owedBy": owner, "why": why})
    return {
        "schema": "tradercockpit-production-readiness/v1",
        "production": str(path),
        "slug": path.name,
        "exists": path.is_dir(),
        "ready": path.is_dir() and not missing,
        "present": present,
        "missing": missing,
        "checkedAt": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "note": "ready=false means the AGENT step has not run or did not finish. The runner "
                "must notify, never silently no-op — a missing folder and a missing video look "
                "identical from outside.",
    }


def selftest() -> None:
    from datetime import datetime as dt

    # DST boundaries: the stdlib rule must agree with US/Eastern on all four sides.
    assert eastern_now(dt(2026, 1, 15, 12, 0, tzinfo=timezone.utc)).hour == 7, "EST"
    assert eastern_now(dt(2026, 7, 15, 12, 0, tzinfo=timezone.utc)).hour == 8, "EDT"
    assert eastern_now(dt(2026, 3, 8, 6, 0, tzinfo=timezone.utc)).hour == 1, "pre-spring-forward"
    assert eastern_now(dt(2026, 3, 8, 8, 0, tzinfo=timezone.utc)).hour == 4, "post-spring-forward"

    assert slug_for(dt(2026, 7, 20)) == "daily-2026-07-20"

    # A folder that does not exist is never ready, and says so without raising.
    result = check(dt(1999, 1, 1))
    assert result["exists"] is False and result["ready"] is False
    assert len(result["missing"]) == len(REQUIRED), result

    print(f"daily_production_init self-test: OK ({len(REQUIRED)} required artifacts tracked)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--init", action="store_true", help="mint today's production folder")
    parser.add_argument("--check", action="store_true", help="readiness only; exit 1 if not ready")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        selftest()
        return 0
    if not (args.init or args.check):
        parser.error("pass --init or --check")

    result = init() if args.init else check()
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['slug']}: {'READY' if result['ready'] else 'NOT READY'}")
        for item in result["missing"]:
            print(f"  missing {item['file']} ({item['owedBy']}) — {item['why']}")
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
