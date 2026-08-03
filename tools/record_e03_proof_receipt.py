#!/usr/bin/env python3
"""Bind the reviewed E03 semantic-proof MP4 to its regenerated source package."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


SCHEMA = "into-the-laboratory/e03-timing-session-rebuild/semantic-proof-receipt/v1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def stable_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def ffprobe(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_streams", "-show_format",
            "-of", "json", str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((row for row in streams if row.get("codec_type") == "video"), None)
    if video is None:
        raise SystemExit("BLOCK: proof contains no video stream")
    duration = float(video.get("duration") or data.get("format", {}).get("duration") or 0)
    return {
        "codec": video.get("codec_name"),
        "width": int(video.get("width", 0)),
        "height": int(video.get("height", 0)),
        "fps": video.get("r_frame_rate"),
        "duration_seconds": round(duration, 3),
        "video_streams": sum(1 for row in streams if row.get("codec_type") == "video"),
        "audio_streams": sum(1 for row in streams if row.get("codec_type") == "audio"),
        "format": data.get("format", {}).get("format_name"),
    }


def inspection_files(path: Path) -> dict[str, dict[str, object]]:
    if not path.is_dir():
        raise SystemExit(f"BLOCK: inspection directory not found: {path}")
    names = ["montage_001.png", "montage_002.png"] + [f"frame_{index:02d}.png" for index in range(1, 9)]
    rows: dict[str, dict[str, object]] = {}
    for name in names:
        file = path / name
        if not file.is_file():
            raise SystemExit(f"BLOCK: missing inspected frame: {file}")
        rows[name] = {"sha256": sha256(file), "bytes": file.stat().st_size}
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--inspection-dir", type=Path, required=True)
    args = parser.parse_args()

    proof = args.proof.resolve()
    package = args.package.resolve()
    project = args.project.resolve()
    rebuild_receipt = package / "e03-rebuild-receipt.json"
    for required in (proof, rebuild_receipt, args.inspection_dir.resolve()):
        if not required.exists():
            raise SystemExit(f"BLOCK: required proof input is missing: {required}")

    media = ffprobe(proof)
    if (media["width"], media["height"]) != (1280, 720):
        raise SystemExit(f"BLOCK: proof dimensions are {media['width']}x{media['height']}, expected 1280x720")
    if abs(media["duration_seconds"] - 30.0) > 0.1:
        raise SystemExit(f"BLOCK: proof duration is {media['duration_seconds']}, expected 30.0 seconds")
    if media["audio_streams"] != 0:
        raise SystemExit("BLOCK: semantic proof unexpectedly contains audio")

    build_receipt = json.loads(rebuild_receipt.read_text(encoding="utf-8"))
    receipt = {
        "schema": SCHEMA,
        "episode": 3,
        "status": "operator_review_candidate_only",
        "operator_approval": False,
        "narrated": False,
        "master": False,
        "source_bindings": {
            "phase03_source_sha256": build_receipt["phase03_source_sha256"],
            "gsap_sha256": build_receipt["gsap_sha256"],
            "derived_receipt_sha256": build_receipt["derived_receipt_sha256"],
            "vo_sha256": build_receipt["vo_sha256"],
            "visual_map_sha256": build_receipt["visual_map_sha256"],
            "source_html_sha256": build_receipt["source_html_sha256"],
            "thumbnail_html_sha256": build_receipt["thumbnail_html_sha256"],
        },
        "proof": {
            "path": str(proof),
            "sha256": sha256(proof),
            "bytes": proof.stat().st_size,
            "media": media,
            "project": str(project),
            "composition": build_receipt["semantic_proof"]["composition"],
        },
        "inspection": {
            "method": "see-video",
            "directory": str(args.inspection_dir.resolve()),
            "frames": inspection_files(args.inspection_dir.resolve()),
            "beats": [
                "opening matches thumbnail opening_group",
                "aligned failure strips show 41, 66, and 23",
                "union geometry shows 24 and 5 overlaps and 101 unique failures",
                "3105 visibly vetoes on session half 1 at 0.986603",
                "close ends at 154 minus 101 equals 53 and names cost stress only as next question",
            ],
        },
        "render_contract": {
            "duration_seconds": 30.0,
            "width": 1280,
            "height": 720,
            "audio": "none",
            "full_master_rendered": False,
            "provider_narration_generated": False,
        },
    }
    output = package / "semantic-proof-receipt.json"
    stable_json(output, receipt)
    artifact_copy = project / "artifacts" / output.name
    stable_json(artifact_copy, receipt)
    print(json.dumps({
        "receipt": str(output),
        "receipt_sha256": sha256(output),
        "artifact_copy": str(artifact_copy),
        "proof_sha256": receipt["proof"]["sha256"],
        "media": media,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
