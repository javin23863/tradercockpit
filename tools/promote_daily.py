#!/usr/bin/env python3
"""Operator said "approved" -> this runs the whole post-approval chain, one command:

  1. flip the production's private long-form to PUBLIC (read-back verified)
  2. Telegram confirmation with the public URL
  3. cut + gate + publish the verticals to every requested platform
     (tools/cut_derivatives.py per platform; per-platform failure never stops the rest)

Run ONLY after the operator has approved the private long-form (their message is the gate;
nothing here asks again). Requires derivatives-plan.json to already exist — write it while
the operator is judging. Deletion of superseded private uploads stays an explicit operator
order, never part of this command.

  PYTHONIOENCODING=utf-8 OpenMontage/.venv/Scripts/python.exe tools/promote_daily.py \
      productions/<vid> [--platforms youtube tiktok instagram facebook] [--skip-promote]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HUB = HERE.parent
DEFAULT_PLATFORMS = ["youtube", "tiktok", "instagram", "facebook"]

sys.path.insert(0, str(HERE))


def latest_longform(prod: Path) -> dict:
    log = json.loads((prod / "publish_log.json").read_text(encoding="utf-8"))
    entries = log if isinstance(log, list) else log.get("entries", [])
    for entry in reversed(entries):
        if entry.get("platform") == "youtube" and entry.get("status") == "published" \
                and "long" in (entry.get("itemId") or entry.get("id") or ""):
            return entry
    sys.exit("no published long-form youtube entry in publish_log.json")


def promote(video_id: str) -> None:
    from channel_seo import get_service
    yt = get_service()
    status = yt.videos().list(part="status", id=video_id).execute()["items"][0]["status"]
    if status.get("privacyStatus") == "public":
        print(f"[promote] {video_id} already public")
        return
    status["privacyStatus"] = "public"
    yt.videos().update(part="status", body={"id": video_id, "status": status}).execute()
    after = yt.videos().list(part="status", id=video_id).execute()["items"][0]["status"]
    if after.get("privacyStatus") != "public":
        sys.exit(f"[promote] read-back is {after.get('privacyStatus')}, not public — stopping")
    print(f"[promote] {video_id} -> public (read-back verified)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prod")
    parser.add_argument("--platforms", nargs="+", default=DEFAULT_PLATFORMS,
                        choices=DEFAULT_PLATFORMS)
    parser.add_argument("--skip-promote", action="store_true",
                        help="long-form is already public; run distribution only")
    args = parser.parse_args()

    prod = (HUB / args.prod) if not Path(args.prod).is_absolute() else Path(args.prod)
    if not (prod / "derivatives-plan.json").is_file():
        sys.exit("derivatives-plan.json missing — write the segment plan first (editorial step)")

    entry = latest_longform(prod)
    url = entry.get("url") or entry.get("videoId")
    video_id = (url or "").rsplit("/", 1)[-1]
    if not args.skip_promote:
        promote(video_id)
        try:
            from notify_telegram import send
            send(f"PROMOTED PUBLIC: {prod.name} {url}")
        except Exception as error:  # noqa: BLE001 - confirmation ping is best-effort
            print(f"[promote] telegram ping failed (non-fatal): {error}")

    results = {}
    for platform in args.platforms:
        print(f"\n[distribute] === {platform} ===")
        proc = subprocess.run([sys.executable, str(HERE / "cut_derivatives.py"), str(prod),
                               "--platform", platform, "--upload"])
        results[platform] = "ok" if proc.returncode == 0 else f"FAILED rc={proc.returncode}"

    print("\n[distribute] ledger:")
    for platform, verdict in results.items():
        print(f"  {platform}: {verdict}")
    failed = [p for p, v in results.items() if v != "ok"]
    if failed:
        print(f"[distribute] investigate failures before retrying — TikTok retries double-post: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
