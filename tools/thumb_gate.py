#!/usr/bin/env python3
"""Render a thumbnail, enforce platform dimensions, and emit the mobile squint image."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
MAX_BYTES = 2 * 1024 * 1024
SQUINT_W = 150


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, capture_output=True, text=True, errors="replace")
    if result.returncode:
        raise SystemExit(f"BLOCK: {command[0]} failed\n{result.stderr[-2000:]}")
    return result


def main(html_arg: str) -> int:
    html = Path(html_arg).resolve()
    if not html.is_file():
        raise SystemExit(f"BLOCK: {html} not found")
    if not CHROME.is_file():
        raise SystemExit(f"BLOCK: Chrome not found at {CHROME}")

    stem = html.with_suffix("")
    master = stem.with_suffix(".png")
    mobile = stem.with_name(stem.name + "-mobile").with_suffix(".png")
    zoom = stem.with_name(stem.name + "-mobile-zoom").with_suffix(".png")

    # Chrome's default shared Temp profile races concurrent headless processes.
    with tempfile.TemporaryDirectory(prefix=".thumb-gate-", dir=html.parent) as tmp_name:
        tmp = Path(tmp_name)
        profile, cache, shot = tmp / "profile", tmp / "cache", tmp / "shot.png"
        profile.mkdir()
        cache.mkdir()
        run([
            str(CHROME), "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--no-first-run", "--no-default-browser-check",
            f"--user-data-dir={profile}", f"--disk-cache-dir={cache}",
            "--window-size=1280,720", f"--screenshot={shot}",
            "--virtual-time-budget=3000", html.as_uri(),
        ])
        if not shot.is_file():
            raise SystemExit("BLOCK: Chrome wrote no screenshot")
        # Copy bytes into a newly-created destination so Chrome's restrictive screenshot
        # ACL does not travel with the candidate artifact.  The reviewer must be able to
        # read the actual 1280x720 raster, not only the HTML or derived squint.
        if master.exists():
            master.unlink()
        shutil.copyfile(shot, master)

    run(["ffmpeg", "-v", "error", "-y", "-i", str(master),
         "-vf", f"scale={SQUINT_W}:-1", str(mobile)])
    run(["ffmpeg", "-v", "error", "-y", "-i", str(mobile),
         "-vf", f"scale={SQUINT_W * 4}:-1:flags=neighbor", str(zoom)])
    dims = run([
        "ffprobe", "-v", "error", "-show_entries", "stream=width,height",
        "-of", "csv=p=0", str(master),
    ]).stdout.strip()
    size = master.stat().st_size

    print(f"  {master.name}  {dims}  {size / 1024 / 1024:.2f} MB")
    failures = []
    if dims != "1280,720":
        failures.append(f"master is {dims}, spec is 1280,720")
    if size > MAX_BYTES:
        failures.append(f"master is {size / 1024 / 1024:.2f} MB, spec cap is 2 MB")
    if failures:
        raise SystemExit("BLOCK:\n  " + "\n  ".join(failures))

    print("  automated checks PASS")
    print(f"\n  NOT CHECKED BY THIS GATE -- open and look at:\n    {zoom}")
    print("  The promise must still read at 150 px. Inspect the emitted image.")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: thumb_gate.py <thumbnail.html>")
    raise SystemExit(main(sys.argv[1]))
