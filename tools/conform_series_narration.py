#!/usr/bin/env python3
"""Apply the smallest deterministic timing/pitch conform to approved Higgsfield John takes."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import statistics
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from generate_series_higgsfield_narration import clean_audio, probe

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "OpenMontage" / "projects"
RECEIPT = ROOT / "productions" / "_series" / "higgsfield-john-post-conform-v1-receipt.json"
CONFORMS = (
    ("series-v4-e03-timing-session", "scene-05", 0.97, 0.0),
    ("series-04-mc-param", "scene-hook", 1.0, -0.5),
    ("series-04-mc-param", "scene-close", 1.0, -1.0),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pitch_factor(semitones: float) -> float:
    return 2 ** (semitones / 12)


def cadence_report(transcript: dict, tempo_factor: float) -> dict:
    rows = []
    for segment in transcript.get("segments", []):
        words = [
            word for word in segment.get("words", [])
            if word.get("word", "").strip()
        ]
        duration = float(segment["end"]) - float(segment["start"])
        if len(words) < 4 or duration <= 0:
            continue
        rows.append({
            "segment_id": segment.get("id"),
            "words": len(words),
            "duration_seconds": round(duration, 3),
            "words_per_second": round(len(words) / duration, 3),
            "text": segment.get("text", "").strip(),
        })
    if len(rows) < 3:
        raise ValueError("cadence gate needs at least three four-word ASR segments")
    median_wps = statistics.median(row["words_per_second"] for row in rows)
    for row in rows:
        row["median_ratio"] = round(row["words_per_second"] / median_wps, 3)
        row["pass"] = 0.70 <= row["median_ratio"] <= 1.40
    violations = [row for row in rows if not row["pass"]]
    transform_pass = 0.95 <= tempo_factor <= 1.05
    return {
        "schema": "tradercockpit.narration-cadence-gate/v2",
        "screen_scope": "Screens timing outliers and tempo-transform provenance; it does not certify naturalness or prosody.",
        "thresholds": {
            "minimum_median_ratio": 0.70,
            "maximum_median_ratio": 1.40,
            "minimum_tempo_factor": 0.95,
            "maximum_tempo_factor": 1.05,
        },
        "applied_tempo_factor": tempo_factor,
        "transform_pass": transform_pass,
        "median_words_per_second": round(median_wps, 3),
        "segments": rows,
        "violations": violations,
        "timing_pass": not violations,
        "human_listening_review": "required",
        "pass": not violations and transform_pass,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--check-transcript", type=Path)
    parser.add_argument("--tempo-factor", type=float)
    args = parser.parse_args()
    if args.demo:
        assert abs(pitch_factor(-12) - 0.5) < 1e-12
        assert len({(project, scene) for project, scene, _, _ in CONFORMS}) == len(CONFORMS)
        steady_transcript = {"segments": [
            {"id": 1, "start": 0, "end": 1, "text": "one two three four", "words": [{"word": str(i)} for i in range(4)]},
            {"id": 2, "start": 1, "end": 2, "text": "one two three four", "words": [{"word": str(i)} for i in range(4)]},
            {"id": 3, "start": 2, "end": 3, "text": "one two three four", "words": [{"word": str(i)} for i in range(4)]},
        ]}
        steady = cadence_report(steady_transcript, 1.0)
        assert steady["pass"]
        transformed = cadence_report(steady_transcript, 1.9)
        assert transformed["timing_pass"] and not transformed["transform_pass"] and not transformed["pass"]
        slowdown = cadence_report({"segments": [
            {"id": 1, "start": 0, "end": 1, "text": "one two three four", "words": [{"word": str(i)} for i in range(4)]},
            {"id": 2, "start": 1, "end": 2, "text": "one two three four", "words": [{"word": str(i)} for i in range(4)]},
            {"id": 3, "start": 2, "end": 4.5, "text": "one two three four", "words": [{"word": str(i)} for i in range(4)]},
        ]}, 1.0)
        assert not slowdown["pass"] and slowdown["violations"][0]["segment_id"] == 3
        print("conform_series_narration selftest: PASS")
        return 0
    if args.check_transcript:
        if args.tempo_factor is None:
            parser.error("--tempo-factor is required with --check-transcript")
        report = cadence_report(
            json.loads(args.check_transcript.read_text(encoding="utf-8")),
            args.tempo_factor,
        )
        print(json.dumps(report, indent=2))
        return 0 if report["pass"] else 1

    rows = []
    for project_id, scene_id, tempo, semitones in CONFORMS:
        project = PROJECTS / project_id
        canonical = project / "assets" / "audio" / "narration" / f"{scene_id}.wav"
        provider_clean = (
            project / "assets" / "audio" / "narration" / "provider-clean" / f"{scene_id}.wav"
        )
        provider_clean.parent.mkdir(parents=True, exist_ok=True)
        if not provider_clean.is_file():
            shutil.copyfile(canonical, provider_clean)

        with tempfile.TemporaryDirectory(dir=project / "artifacts") as temp_dir:
            temp_dir = Path(temp_dir)
            conformed = temp_dir / "conformed.wav"
            mastered = temp_dir / "mastered.wav"
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-hide_banner", "-nostats", "-i", str(provider_clean),
                    "-af", f"rubberband=tempo={tempo}:pitch={pitch_factor(semitones):.9f}",
                    "-ar", "48000", "-ac", "1", "-c:a", "pcm_s24le", str(conformed),
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode:
                raise SystemExit(result.stderr)
            clean_audio(conformed, mastered)
            shutil.copyfile(mastered, canonical)

        info = probe(canonical)
        manifest_path = project / "artifacts" / "asset_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry = next(
            item for item in manifest["assets"]
            if item.get("type") == "narration" and item.get("scene_id") == scene_id
        )
        entry["duration_seconds"] = info["duration_seconds"]
        entry["source_tool"] = (
            "Higgsfield Qwen Audio 3.0 TTS Flash plus FFmpeg clean mastering "
            "and rubberband conform"
        )
        entry["post_conform"] = {
            "tempo": tempo,
            "pitch_semitones": semitones,
            "provider_clean_sha256": sha256(provider_clean),
            "final_sha256": sha256(canonical),
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        rows.append({
            "project_id": project_id,
            "scene_id": scene_id,
            "tempo": tempo,
            "pitch_semitones": semitones,
            "provider_clean_path": str(provider_clean.relative_to(ROOT)),
            "provider_clean_sha256": sha256(provider_clean),
            "final_path": str(canonical.relative_to(ROOT)),
            "final_sha256": sha256(canonical),
            **info,
        })
        print(f"{project_id} {scene_id} {info['duration_seconds']:.3f}s {sha256(canonical)}")

    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps({
        "schema": "tradercockpit.higgsfield-john-post-conform/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": "Higgsfield",
        "voice": "John",
        "external_credits_used": 0,
        "processing": "FFmpeg rubberband conform, then 70 Hz high-pass and two-pass EBU R128 normalization",
        "entries": rows,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(rows)} approved Higgsfield takes conformed -> {RECEIPT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
