#!/usr/bin/env python3
"""Bind the listening evidence and rendered-audio gates to one exact episode master."""

from __future__ import annotations

import argparse
import hashlib
import json
import wave
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    parser.add_argument("master", type=Path)
    args = parser.parse_args()

    project = args.project.resolve()
    master = args.master.resolve()
    artifacts = project / "artifacts"
    transcript_path = artifacts / "whisper-back.json"
    gate_path = artifacts / "build" / "gate-receipt.json"
    voice_path = project / "tools" / "bed" / "voice.wav"
    for path in (master, transcript_path, gate_path, voice_path):
        if not path.is_file():
            raise SystemExit(f"BLOCK: missing {path}")

    master_hash = sha256(master)
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate.get("verdict") != "GREEN" or gate.get("master_sha256") != master_hash:
        raise SystemExit("BLOCK: the full gate receipt does not certify these master bytes")
    required_audio_gates = ("presentation_gate", "check_bed", "voice_consistency")
    failed = [
        name
        for name in required_audio_gates
        if gate.get("gates", {}).get(name, {}).get("verdict") != "PASS"
    ]
    if failed:
        raise SystemExit(f"BLOCK: rendered-audio gate did not pass: {', '.join(failed)}")

    transcript = json.loads(transcript_path.read_text(encoding="utf-8"))
    missing = {
        scene: row.get("missing_tokens", [])
        for scene, row in transcript.items()
        if row.get("missing_tokens")
    }
    if missing:
        raise SystemExit(f"BLOCK: listening review has missing claim tokens: {missing}")

    with wave.open(str(voice_path), "rb") as voice:
        voice_duration = voice.getnframes() / voice.getframerate()
        voice_format = {
            "sample_rate_hz": voice.getframerate(),
            "channels": voice.getnchannels(),
            "sample_width_bits": voice.getsampwidth() * 8,
        }

    receipt = {
        "schema": "tradercockpit-series-audio-review/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS",
        "master": str(master),
        "master_sha256": master_hash,
        "rendered_voice_stem": str(voice_path),
        "rendered_voice_stem_sha256": sha256(voice_path),
        "rendered_voice_duration_seconds": round(voice_duration, 3),
        "rendered_voice_format": voice_format,
        "listening_method": (
            "Local Whisper word-timestamp transcription of every narration take, "
            "with fail-closed number, sign, and direction-token comparison to vo.txt."
        ),
        "listening_transcript": str(transcript_path),
        "listening_transcript_sha256": sha256(transcript_path),
        "scenes_listened": len(transcript),
        "worst_scene_wer": max(row.get("wer", 0.0) for row in transcript.values()),
        "missing_claim_tokens": {},
        "exact_master_audio_gates": {
            name: gate["gates"][name] for name in required_audio_gates
        },
        "gate_receipt": str(gate_path),
        "gate_receipt_sha256": sha256(gate_path),
    }
    output = artifacts / "audio-review-receipt.json"
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(transcript)} scenes listened; exact master audio gates passed -> {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
