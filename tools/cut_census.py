#!/usr/bin/env python3
"""Rendered pacing gate: scene-change rate plus actual static-frame holds."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

MIN_PER_MIN = 4.0
MAX_HOLD_S = 15.0
EARLY_MAX_HOLD_S = 10.0
EARLY_WINDOW_S = 90.0
SCENE_THRESHOLD = 0.12

# Shared calibration with the episode motion census: at 480x270 grayscale, fewer
# than 1% of pixels changing by more than 8/255 reads as a held frame.
W, H, FPS = 480, 270, 2.0
PIX_DELTA = 8
STATIC_PCT = 1.0

PROFILES = ("film-motion", "board-led-explainer")
# Calibrated against the exact operator-approved Episode 01 board treatment:
# midpoint lit area 6.05% minimum, adjacent-board difference 8.76% minimum,
# and encoded/planned duration delta 0.026s. These leave roughly 2x margin.
BOARD_MIN_LIT_PCT = 3.0
BOARD_MIN_ADJACENT_DIFF_PCT = 4.0
BOARD_DURATION_TOLERANCE_S = 0.10
BOARD_W, BOARD_H = 160, 90


def scene_changes(video: Path, threshold: float) -> list[float]:
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
            "-vf", f"select='gt(scene,{threshold})',metadata=print",
            "-an", "-f", "null", "-",
        ],
        capture_output=True, text=True, errors="replace",
    )
    if proc.returncode:
        raise SystemExit(f"BLOCK: ffmpeg scene detection failed for {video}")
    return sorted(float(x) for x in re.findall(r"pts_time:([\d.]+)", proc.stderr))


def duration(video: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "csv=p=0", str(video),
        ],
        capture_output=True, text=True, errors="replace",
    )
    try:
        return float(proc.stdout.strip())
    except ValueError:
        raise SystemExit(f"BLOCK: ffprobe gave no duration for {video}") from None


def motion(video: Path) -> np.ndarray:
    proc = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", str(video),
            "-vf", f"fps={FPS},scale={W}:{H}", "-pix_fmt", "gray",
            "-f", "rawvideo", "-",
        ],
        stdout=subprocess.PIPE,
    )
    assert proc.stdout is not None
    frame_bytes = W * H
    previous, changes = None, []
    while True:
        raw = proc.stdout.read(frame_bytes)
        if len(raw) < frame_bytes:
            break
        current = np.frombuffer(raw, dtype=np.uint8).astype(np.int16)
        if previous is not None:
            changes.append(float((np.abs(current - previous) > PIX_DELTA).mean() * 100.0))
        previous = current
    proc.stdout.close()
    if proc.wait():
        raise SystemExit(f"BLOCK: ffmpeg motion sampling failed for {video}")
    return np.asarray(changes)


def static_holds(changes: np.ndarray) -> list[tuple[float, float]]:
    """Return (start, duration) for contiguous samples that read as still."""
    holds, start = [], None
    for index, changed_pct in enumerate(changes):
        at = (index + 1) / FPS
        if changed_pct < STATIC_PCT and start is None:
            start = at
        elif changed_pct >= STATIC_PCT and start is not None:
            holds.append((start, at - start))
            start = None
    if start is not None:
        holds.append((start, len(changes) / FPS - start))
    return holds


def visual_refresh_rate(changes: np.ndarray, total_seconds: float) -> float:
    """Meaningful changed samples per minute; supports cuts and continuous animation."""
    if total_seconds <= 0:
        return 0.0
    return float((changes >= STATIC_PCT).sum() / (total_seconds / 60.0))


def _board_frame(video: Path, at: float) -> np.ndarray:
    proc = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-ss", str(at), "-i", str(video),
            "-frames:v", "1", "-vf", f"scale={BOARD_W}:{BOARD_H},format=gray",
            "-f", "rawvideo", "-",
        ],
        capture_output=True,
    )
    expected = BOARD_W * BOARD_H
    if proc.returncode or len(proc.stdout) != expected:
        raise SystemExit(f"BLOCK: could not read encoded board frame at {at:.3f}s")
    return np.frombuffer(proc.stdout, dtype=np.uint8)


def board_metrics(video: Path, total: float, timing_path: Path | None) -> dict:
    if timing_path is None or not timing_path.is_file():
        raise SystemExit("BLOCK: board-led-explainer requires --timing with declared scene windows")
    try:
        data = json.loads(timing_path.read_text(encoding="utf-8"))
        scenes = data["scenes"]
        planned = float(data["duration_seconds"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"BLOCK: invalid board timing artifact {timing_path}: {exc}") from None
    if not scenes:
        raise SystemExit(f"BLOCK: {timing_path} declares zero scenes")

    windows, expected_start = [], 0.0
    for scene in scenes:
        try:
            scene_id = str(scene["scene_id"])
            start = float(scene["start_seconds"])
            end = float(scene["end_seconds"])
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit(f"BLOCK: invalid scene window in {timing_path}: {exc}") from None
        if end <= start or abs(start - expected_start) > BOARD_DURATION_TOLERANCE_S:
            raise SystemExit(
                f"BLOCK: non-contiguous board window {scene_id}: {start:.3f}-{end:.3f}, "
                f"expected start {expected_start:.3f}"
            )
        windows.append((scene_id, start, end))
        expected_start = end

    frames, lit = [], []
    for _, start, end in windows:
        frame = _board_frame(video, (start + end) / 2)
        frames.append(frame)
        lit.append(float((frame > PIX_DELTA).mean() * 100.0))
    diffs = [
        float((np.abs(curr.astype(np.int16) - prev.astype(np.int16)) > PIX_DELTA).mean() * 100.0)
        for prev, curr in zip(frames, frames[1:])
    ]
    return {
        "scene_count": len(windows),
        "duration_delta_s": abs(total - planned),
        "lit_pct": lit,
        "adjacent_diff_pct": diffs,
    }


def board_failures(metrics: dict) -> list[str]:
    failures = []
    if metrics["duration_delta_s"] > BOARD_DURATION_TOLERANCE_S:
        failures.append(
            f"encoded/planned duration delta {metrics['duration_delta_s']:.3f}s "
            f"(cap {BOARD_DURATION_TOLERANCE_S:.2f}s)"
        )
    for index, lit in enumerate(metrics["lit_pct"], 1):
        if lit < BOARD_MIN_LIT_PCT:
            failures.append(
                f"scene {index:02d} midpoint is effectively black ({lit:.2f}% lit)"
            )
    for index, diff in enumerate(metrics["adjacent_diff_pct"], 2):
        if diff < BOARD_MIN_ADJACENT_DIFF_PCT:
            failures.append(
                f"scene {index - 1:02d}->{index:02d} boards are not visually distinct "
                f"({diff:.2f}% changed)"
            )
    return failures


def board_gate(video: Path, total: float, timing_path: Path | None) -> int:
    metrics = board_metrics(video, total, timing_path)
    failures = board_failures(metrics)
    print(video.name)
    print("profile              board-led-explainer")
    print(f"duration             {total:.1f}s  ({total / 60:.2f} min)")
    print(f"declared boards      {metrics['scene_count']}")
    print(f"duration delta       {metrics['duration_delta_s']:.3f}s")
    print(f"minimum lit area     {min(metrics['lit_pct']):.2f}%")
    print(f"minimum board change {min(metrics['adjacent_diff_pct'], default=100.0):.2f}%")
    print("\nGATE  every declared board must be present, non-black, distinct, and duration-bound")
    for finding in failures:
        print(f"  FAIL {finding}")
    if failures:
        print(f"GATE  FAIL  {len(failures)} board coverage finding(s)")
        return 1
    print("GATE  PASS")
    print("NOTE  intentional static holds are not motion failures in this profile")
    return 0


def self_check() -> int:
    changes = np.array([0.2] * 22 + [8.0] + [0.1] * 32)
    holds = static_holds(changes)
    assert holds == [(0.5, 11.0), (12.0, 15.5)], holds
    failures = [
        (start, span)
        for start, span in holds
        if span > (EARLY_MAX_HOLD_S if start < EARLY_WINDOW_S else MAX_HOLD_S)
    ]
    assert failures == holds
    assert visual_refresh_rate(np.array([8.0] * 8), 60.0) == 8.0
    assert visual_refresh_rate(np.array([0.2] * 8), 60.0) == 0.0
    good_board = {
        "duration_delta_s": 0.026,
        "lit_pct": [6.05, 11.2],
        "adjacent_diff_pct": [8.76],
    }
    assert not board_failures(good_board)
    assert len(board_failures({**good_board, "lit_pct": [0.0, 11.2]})) == 1
    assert len(board_failures({**good_board, "adjacent_diff_pct": [0.0]})) == 1
    print("cut_census self-check ok: film motion and board coverage profiles both block defects")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", nargs="?")
    parser.add_argument("--threshold", type=float, default=SCENE_THRESHOLD)
    parser.add_argument("--profile", choices=PROFILES, default="film-motion")
    parser.add_argument("--timing", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()
    if args.self_check:
        return self_check()
    if not args.video:
        raise SystemExit("usage: cut_census.py <master.mp4>")

    video = Path(args.video)
    if not video.is_file():
        raise SystemExit(f"BLOCK: {video} does not exist")
    total = duration(video)
    if args.profile == "board-led-explainer":
        return board_gate(video, total, args.timing)
    cuts = scene_changes(video, args.threshold)
    changes = motion(video)
    holds = sorted(static_holds(changes), key=lambda item: item[1], reverse=True)

    marks = [0.0, *cuts, total]
    scene_gaps = sorted(
        ((marks[i + 1] - marks[i], marks[i]) for i in range(len(marks) - 1)),
        reverse=True,
    )
    rate = len(cuts) / (total / 60)
    refresh_rate = visual_refresh_rate(changes, total)
    still_pct = float((changes < STATIC_PCT).mean() * 100) if len(changes) else 100.0
    failures = [
        (start, span)
        for start, span in holds
        if span > (EARLY_MAX_HOLD_S if start < EARLY_WINDOW_S else MAX_HOLD_S)
    ]

    print(video.name)
    print(f"duration             {total:.1f}s  ({total / 60:.2f} min)")
    print(f"scene changes        {len(cuts)}   ({rate:.2f}/min at threshold {args.threshold})")
    print(f"visual refreshes     {refresh_rate:.2f}/min (>= {STATIC_PCT:.1f}% pixels changed)")
    print(f"longest scene gap    {scene_gaps[0][0]:.2f}s at {scene_gaps[0][1]:.1f}s "
          "(diagnostic; motion can continue)")
    print(f"static picture       {still_pct:.1f}% of sampled frames")
    if holds:
        print(f"longest actual hold  {holds[0][1]:.2f}s at {holds[0][0]:.1f}s")
        print("\nworst 10 actual holds:")
        for start, span in holds[:10]:
            print(f"  {span:6.2f}s   {start:7.1f}s -> {start + span:7.1f}s")
    else:
        print("longest actual hold  0.00s")

    print(f"\nGATE  visual refreshes >= {MIN_PER_MIN:.0f}/min; actual hold <= "
          f"{EARLY_MAX_HOLD_S:.0f}s before {EARLY_WINDOW_S:.0f}s, "
          f"<= {MAX_HOLD_S:.0f}s after")
    if refresh_rate < MIN_PER_MIN:
        print(f"  FAIL visual-refresh rate {refresh_rate:.2f}/min")
    for start, span in sorted(failures):
        cap = EARLY_MAX_HOLD_S if start < EARLY_WINDOW_S else MAX_HOLD_S
        print(f"  FAIL {span:6.2f}s actual hold at {start:7.1f}s (cap {cap:.0f}s)")
    if refresh_rate >= MIN_PER_MIN and not failures:
        print("GATE  PASS")
        return 0
    print(f"GATE  FAIL  {len(failures)} actual hold(s)"
          f"{'' if refresh_rate >= MIN_PER_MIN else ' + visual-refresh rate'}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
