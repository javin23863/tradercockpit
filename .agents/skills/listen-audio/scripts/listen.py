#!/usr/bin/env python3
"""Create a local listening receipt from the actual media bytes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path


def find_bin(name: str, supplied: Path | None) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    suffix = ".exe" if sys.platform == "win32" else ""
    repo = Path(__file__).resolve().parents[4]
    candidates = [supplied / f"{name}{suffix}"] if supplied else []
    candidates.append(
        repo / "OpenMontage" / ".tools" / "ffmpeg" / "bin" / f"{name}{suffix}"
    )
    return next((str(path) for path in candidates if path.is_file()), None)


def run(command: list[str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, timeout=timeout)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def last_number(pattern: str, text: str) -> float | None:
    values = re.findall(pattern, text, flags=re.MULTILINE)
    return float(values[-1]) if values else None


def transcribe(path: Path, model_name: str, language: str | None) -> dict:
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel(
            model_name, device="cpu", compute_type="int8", local_files_only=True
        )
        segments, info = model.transcribe(
            str(path), language=language, vad_filter=True, word_timestamps=True
        )
        rows = []
        for segment in segments:
            probabilities = [word.probability for word in (segment.words or [])]
            rows.append({
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "text": segment.text.strip(),
                "mean_word_probability": (
                    round(sum(probabilities) / len(probabilities), 3)
                    if probabilities else None
                ),
            })
        return {
            "status": "ok",
            "language": language or info.language,
            "duration_seconds": round(info.duration, 3),
            "text": " ".join(row["text"] for row in rows),
            "segments": rows,
        }
    except Exception as exc:
        return {"status": "unavailable", "error": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--speech-required", action="store_true")
    parser.add_argument("--expected-script", type=Path)
    parser.add_argument("--model", default="small.en")
    parser.add_argument("--language", default="en")
    parser.add_argument("--ffmpeg-dir", type=Path)
    parser.add_argument("--target-lufs", type=float)
    parser.add_argument("--lufs-tolerance", type=float, default=2.0)
    parser.add_argument("--true-peak-ceiling", type=float)
    parser.add_argument("--min-script-similarity", type=float, default=0.9)
    args = parser.parse_args()

    source = args.input.resolve()
    if not source.is_file():
        parser.error(f"input does not exist: {source}")
    args.out.mkdir(parents=True, exist_ok=True)

    ffmpeg = find_bin("ffmpeg", args.ffmpeg_dir)
    ffprobe = find_bin("ffprobe", args.ffmpeg_dir)
    if not ffmpeg or not ffprobe:
        parser.error("ffmpeg and ffprobe are required")

    probe = run([
        ffprobe, "-v", "error", "-show_format", "-show_streams",
        "-of", "json", str(source),
    ])
    metadata = json.loads(probe.stdout) if probe.returncode == 0 else {}
    audio_streams = [
        stream for stream in metadata.get("streams", [])
        if stream.get("codec_type") == "audio"
    ]
    decode = run([ffmpeg, "-v", "error", "-i", str(source), "-f", "null", "-"])
    loudness = run([
        ffmpeg, "-hide_banner", "-i", str(source),
        "-af", "ebur128=peak=true", "-f", "null", "-",
    ])
    silence = run([
        ffmpeg, "-hide_banner", "-i", str(source),
        "-af", "silencedetect=noise=-50dB:d=0.5", "-f", "null", "-",
    ])

    waveform = args.out / "waveform.png"
    spectrogram = args.out / "spectrogram.png"
    wave = run([
        ffmpeg, "-y", "-v", "error", "-i", str(source),
        "-filter_complex", "showwavespic=s=1600x400:colors=#e31b23",
        "-frames:v", "1", str(waveform),
    ])
    spec = run([
        ffmpeg, "-y", "-v", "error", "-i", str(source),
        "-lavfi", "showspectrumpic=s=1600x800:legend=1:color=fiery",
        "-frames:v", "1", str(spectrogram),
    ])

    transcript = transcribe(source, args.model, args.language or None)
    comparison = None
    if args.expected_script:
        expected_words = words(args.expected_script.read_text(encoding="utf-8"))
        actual_words = words(transcript.get("text", ""))
        ending_size = min(8, len(expected_words))
        matcher = SequenceMatcher(None, expected_words, actual_words)
        comparison = {
            "expected_path": str(args.expected_script.resolve()),
            "expected_word_count": len(expected_words),
            "transcribed_word_count": len(actual_words),
            "word_sequence_similarity": round(matcher.ratio(), 4),
            "minimum_similarity": args.min_script_similarity,
            "expected_ending_present": bool(ending_size)
            and expected_words[-ending_size:] == actual_words[-ending_size:],
            "differences": [
                {
                    "operation": operation,
                    "expected": expected_words[i1:i2],
                    "transcribed": actual_words[j1:j2],
                }
                for operation, i1, i2, j1, j2 in matcher.get_opcodes()
                if operation != "equal"
            ],
        }

    starts = [
        float(value) for value in re.findall(r"silence_start:\s*([\d.]+)", silence.stderr)
    ]
    ends = [
        float(value) for value in re.findall(r"silence_end:\s*([\d.]+)", silence.stderr)
    ]
    integrated_lufs = last_number(
        r"^\s*I:\s*(-?[\d.]+)\s+LUFS", loudness.stderr
    )
    true_peak_dbfs = last_number(
        r"^\s*Peak:\s*(-?[\d.]+)\s+dBFS", loudness.stderr
    )
    blockers = []
    if not audio_streams:
        blockers.append("no audio stream")
    if decode.returncode:
        blockers.append("full-file decode failed")
    if args.speech_required and transcript["status"] != "ok":
        blockers.append("required speech transcription unavailable")
    if args.speech_required and not words(transcript.get("text", "")):
        blockers.append("required speech was not detected")
    if wave.returncode or spec.returncode:
        blockers.append("waveform or spectrogram generation failed")
    if comparison and not comparison["expected_ending_present"]:
        blockers.append("expected script ending was not found")
    if (
        comparison
        and comparison["word_sequence_similarity"] < args.min_script_similarity
    ):
        blockers.append("transcript similarity is below the declared floor")
    if args.target_lufs is not None and (
        integrated_lufs is None
        or abs(integrated_lufs - args.target_lufs) > args.lufs_tolerance
    ):
        blockers.append("integrated loudness is outside the production limit")
    if (
        args.true_peak_ceiling is not None
        and (true_peak_dbfs is None or true_peak_dbfs > args.true_peak_ceiling)
    ):
        blockers.append("true peak exceeds the production ceiling")

    receipt = {
        "schema": "tradercockpit-listening-receipt/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "fail" if blockers else "pass",
        "machine_checks_only": True,
        "operator_playback_required_for_subjective_approval": True,
        "input": {
            "path": str(source), "sha256": file_hash(source),
            "size_bytes": source.stat().st_size,
        },
        "probe": {"format": metadata.get("format", {}), "audio_streams": audio_streams},
        "decode": {"status": "pass" if decode.returncode == 0 else "fail"},
        "signal": {
            "integrated_lufs": integrated_lufs,
            "target_lufs": args.target_lufs,
            "lufs_tolerance": args.lufs_tolerance if args.target_lufs is not None else None,
            "loudness_range_lu": last_number(
                r"^\s*LRA:\s*(-?[\d.]+)\s+LU", loudness.stderr
            ),
            "true_peak_dbfs": true_peak_dbfs,
            "true_peak_ceiling": args.true_peak_ceiling,
            "silence_segments_over_0_5s": [
                {
                    "start": round(start, 3), "end": round(end, 3),
                    "duration": round(end - start, 3),
                }
                for start, end in zip(starts, ends)
            ],
        },
        "transcript": transcript,
        "script_comparison": comparison,
        "review_images": {
            "waveform": str(waveform.resolve()),
            "spectrogram": str(spectrogram.resolve()),
        },
        "blockers": blockers,
    }
    receipt_path = args.out / "listening-receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "receipt": str(receipt_path.resolve()),
        "transcript": transcript.get("text", ""),
        "blockers": blockers,
    }, indent=2))
    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
