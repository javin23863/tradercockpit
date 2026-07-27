#!/usr/bin/env python3
"""Voice-cloned VO stage via ElevenLabs — drop-in replacement for tts_chatterbox.py.

Emits the SAME build/ artifacts as produce.stage_vo and tts_chatterbox
(vo-NN.wav, vo-full.wav, sections.json), so `--stage captions` and `--stage assemble`
run downstream unchanged. Unlike Chatterbox this needs no torch and no local model,
which is the point: the 4-5 GB local load is what collided with the pinned pagefile
(OSError 1455) on render nights.

  python tools/tts_elevenlabs.py productions/daily-2026-07-27
  python tools/tts_elevenlabs.py productions/daily-2026-07-27 --dry-run   # cost only

Needs ELEVENLABS_API_KEY and ELEVEN_VOICE_ID (repo .env or environment).

--speed is the calibration knob: ElevenLabs has no words-per-minute control, only a
0.7-1.2 multiplier whose real rate depends on the clone. Render, measure the printed
wpm, adjust once. ONE setting for the whole production — the per-scene varispeed that
sank ep02 v29 is exactly what this must never grow.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

try:
    from tools.produce import parse_sections, require_production_approval
    from tools.tts_chatterbox import force_daily_operator_voice, section_wav_name
except ModuleNotFoundError:  # direct `python tools/tts_elevenlabs.py` execution
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from produce import parse_sections, require_production_approval
    from tts_chatterbox import force_daily_operator_voice, section_wav_name

ROOT = Path(__file__).resolve().parents[1]
GAP_S = 0.45              # silence between sections — matches produce.GAP_S
API = "https://api.elevenlabs.io/v1/text-to-speech"
MODEL = "eleven_multilingual_v2"
OUTPUT_FORMAT = "mp3_44100_128"
TARGET_WPM = 145          # operator ruling 2026-07-28: "new clone, medium (145 wpm)"
WPM_TOLERANCE = 12        # flag a render that drifts far enough to hear


def load_env() -> None:
    """Read repo .env without a dependency — real environment always wins."""
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def section_text(section: dict) -> str:
    """One request per section: ElevenLabs keeps prosody across a whole section, so
    the 280-char breath chunking Chatterbox needed would only add seams here."""
    return " ".join(block["text"].strip() for block in section["blocks"]).strip()


def word_count(text: str) -> int:
    """One word per spoken token. Decimals and contractions stay whole — splitting
    '99.40' into two inflates the count and would push --speed the wrong way."""
    return len(re.findall(r"[A-Za-z0-9]+(?:[.'’][A-Za-z0-9]+)*", text))


def synth(text: str, voice: str, key: str, speed: float, out: Path) -> None:
    body = json.dumps({
        "text": text,
        "model_id": MODEL,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "speed": speed},
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{API}/{voice}?output_format={OUTPUT_FORMAT}", data=body,
        headers={"xi-api-key": key, "Content-Type": "application/json"},
    )
    for attempt in (1, 2, 3):
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                out.write_bytes(response.read())
            return
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", "replace")[:300]
            # 4xx other than rate limit is a bad request or a dead key — retrying burns credits
            if error.code not in (429, 500, 502, 503, 504) or attempt == 3:
                sys.exit(f"elevenlabs {error.code}: {detail}")
            time.sleep(5 * attempt)
        except urllib.error.URLError as error:
            if attempt == 3:
                sys.exit(f"elevenlabs unreachable: {error.reason}")
            time.sleep(5 * attempt)


def to_wav(mp3: Path, wav: Path) -> None:
    subprocess.run(["ffmpeg", "-y", "-i", str(mp3), "-ar", "44100", "-ac", "1", str(wav)],
                   check=True, capture_output=True)


def duration(path: Path) -> float:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        check=True, capture_output=True, text=True,
    )
    return float(probe.stdout.strip())


def concat(wavs: list[Path], out: Path) -> None:
    """Join sections with GAP_S of silence, one ffmpeg pass. Each gap is its own
    lavfi input — a filtergraph input pad cannot be consumed twice."""
    args = []
    for wav in wavs:
        args += ["-i", str(wav)]
    for _ in range(len(wavs) - 1):
        args += ["-f", "lavfi", "-t", str(GAP_S), "-i", "anullsrc=r=44100:cl=mono"]
    labels = []
    for index in range(len(wavs)):
        labels.append(f"[{index}:a]")
        if index != len(wavs) - 1:
            labels.append(f"[{len(wavs) + index}:a]")
    graph = "".join(labels) + f"concat=n={len(labels)}:v=0:a=1[out]"
    subprocess.run(["ffmpeg", "-y", *args, "-filter_complex", graph,
                    "-map", "[out]", "-ar", "44100", "-ac", "1", str(out)],
                   check=True, capture_output=True)


def _selftest() -> None:
    sections = [{"num": "01", "slug": "hook", "blocks": [
        {"speaker": "OPERATOR", "text": "Oil fell."}, {"speaker": "OPERATOR", "text": "Yields fell too."}]}]
    assert section_text(sections[0]) == "Oil fell. Yields fell too."
    assert word_count("Brent closed at 99.40, down 2.1%.") == 6
    assert section_wav_name(sections[0]) == "vo-01.wav"
    print("tts-elevenlabs self-test: 3/3 PASS")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prod", nargs="?", help="production folder (contains vo.txt)")
    ap.add_argument("--voice", help="ElevenLabs voice id (default: $ELEVEN_VOICE_ID)")
    ap.add_argument("--speed", type=float, default=1.0, help="0.7-1.2 delivery multiplier")
    ap.add_argument("--dry-run", action="store_true", help="print characters + cost shape, spend nothing")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        _selftest()
        return 0
    if not a.prod:
        sys.exit("usage: tts_elevenlabs.py <prod> [--speed 1.0]")

    load_env()
    prod = Path(a.prod).resolve()
    voice = a.voice or os.environ.get("ELEVEN_VOICE_ID")
    key = os.environ.get("ELEVENLABS_API_KEY")

    try:
        require_production_approval(prod)
    except ValueError as error:
        sys.exit(f"production approval gate blocked TTS: {error}")

    sections = force_daily_operator_voice(prod, parse_sections(prod))
    speakers = {block["speaker"] for section in sections for block in section["blocks"]}
    if speakers != {"OPERATOR"}:
        # ponytail: one cloned voice is wired. Add a speaker->voice map when the Show lane needs Apollo.
        sys.exit(f"ElevenLabs VO is operator-only; script also asks for {sorted(speakers - {'OPERATOR'})}")

    total_chars = sum(len(section_text(section)) for section in sections)
    total_words = sum(word_count(section_text(section)) for section in sections)
    print(f"[eleven] {len(sections)} sections, {total_words} words, {total_chars} characters billable")
    if a.dry_run:
        print(f"[eleven] dry run: nothing sent. voice={voice or 'UNSET'} key={'set' if key else 'MISSING'}")
        return 0
    if not key or not voice:
        sys.exit("ELEVENLABS_API_KEY and ELEVEN_VOICE_ID must be set (repo .env or environment)")

    build = prod / "build"
    build.mkdir(parents=True, exist_ok=True)

    meta, wavs = [], []
    for section in sections:
        wav = build / section_wav_name(section)
        if wav.exists():  # same skip-existing contract as tts_chatterbox — delete a wav to
            print(f"[eleven] section {section['num']} ({section['slug']}) exists, skip")  # regenerate it
        else:
            mp3 = build / f"{wav.stem}.mp3"
            synth(section_text(section), voice, key, a.speed, mp3)
            to_wav(mp3, wav)
            mp3.unlink()
            print(f"[eleven] section {section['num']} ({section['slug']}) -> {duration(wav):.1f}s")
        seconds = duration(wav)
        meta.append({**section, "wav": wav.name, "duration": round(seconds, 3)})
        wavs.append(wav)

    full = build / "vo-full.wav"
    concat(wavs, full)
    (build / "sections.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    total = duration(full)
    wpm = total_words / (total / 60) if total else 0
    print(f"[eleven] DONE: {len(meta)} sections, {total/60:.1f} min -> build/vo-full.wav")
    print(f"[eleven] measured {wpm:.0f} wpm at speed={a.speed} (target {TARGET_WPM})")
    if abs(wpm - TARGET_WPM) > WPM_TOLERANCE:
        print(f"[eleven] WARNING: off target — rerun with --speed {a.speed * wpm / TARGET_WPM:.2f} "
              "after deleting build/vo-*.wav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
