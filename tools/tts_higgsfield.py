#!/usr/bin/env python3
"""Daily-lane VO via Higgsfield Qwen (Marcus) — drop-in replacement for tts_elevenlabs.py.

Emits the SAME build/ artifacts as produce.stage_vo, tts_chatterbox and tts_elevenlabs
(vo-NN.wav, vo-full.wav, sections.json), so `--stage captions` and `--stage assemble`
run downstream unchanged.

  python tools/tts_higgsfield.py productions/daily-2026-08-04
  python tools/tts_higgsfield.py productions/daily-2026-08-04 --dry-run   # credits only

Why this exists: the ElevenLabs Creator tier ran to 18,051 of 130,984 characters with a
reset 23 days out — one more night, then the lane blocks. Marcus is already the operator's
proven voice on the Into the Laboratory series and bills against included Higgsfield Max
credits at roughly a credit a night, so the monthly wall disappears.

The provider route (model, voice id, instruction, and every generation parameter) is
IMPORTED from generate_series_higgsfield_narration, not restated here. That module's
sha256 is bound into the series approval receipts, so it is read-only from this side: a
copy of its constants would be a second source of truth that drifts silently.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path

try:
    from tools.generate_series_higgsfield_narration import (
        JOB_TYPE, MARCUS_INSTRUCTION, MARCUS_VOICE_ID, MODEL,
        _recover_provider_job, account_status, loudnorm_measure, run_json,
    )
    from tools.produce import parse_sections, require_production_approval
    from tools.tts_chatterbox import force_daily_operator_voice, section_wav_name
    from tools.tts_elevenlabs import (
        WPM_TOLERANCE, concat, duration, section_text, word_count,
    )
except ImportError:  # direct `python tools/tts_higgsfield.py` execution
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from generate_series_higgsfield_narration import (  # noqa: E402
        JOB_TYPE, MARCUS_INSTRUCTION, MARCUS_VOICE_ID, MODEL,
        _recover_provider_job, account_status, loudnorm_measure, run_json,
    )
    from produce import parse_sections, require_production_approval  # noqa: E402
    from tts_chatterbox import force_daily_operator_voice, section_wav_name  # noqa: E402
    from tts_elevenlabs import (  # noqa: E402
        WPM_TOLERANCE, concat, duration, section_text, word_count,
    )

# Measured on the series: ~0.09 included credits per section, so a 13-section daily is
# about one credit. Kept as a floor for the dry run, not as a billing authority.
CREDITS_PER_SECTION = 0.09
SAMPLE_RATE_HZ = 44100  # the daily contract; the series masters at 48k for its own render
# Marcus's own rate — NOT tts_elevenlabs.TARGET_WPM. Speaking rate is a property of the
# voice: importing the clone's 145 here would flag every correct Marcus render as off target
# and push the script budget to a length that ships an 8-minute video. Measured 198 on the
# 2026-08-04 route smoke, and the shipped 202 wpm masters (2026-07-20/21) are the precedent
# this restores: 2,029-2,202 words landed 10.0-10.9 min.
TARGET_WPM = 198
WORD_BAND = (2_000, 2_350)   # the 10-12 min ad floor at this rate


def provider_task(text: str) -> dict:
    """The exact approved Marcus submission, shaped for _recover_provider_job's matcher."""
    return {"text": text, "instruction": MARCUS_INSTRUCTION}


def synth(text: str, out_raw: Path, speech_rate: float = 1.0) -> dict:
    """One section, provider-native. Returns the completed job."""
    command = [
        "higgsfield", "generate", "create", JOB_TYPE,
        "--prompt", text,
        "--instruction", MARCUS_INSTRUCTION,
        "--voice_type", "preset",
        "--voice_id", MARCUS_VOICE_ID,
        "--format", "wav",
        "--sample_rate", "24000",
        "--language", "en",
        "--seed", "0",
        "--speech_rate", str(speech_rate),
        "--pitch_rate", "1",
        "--volume", "50",
        "--wait",
        "--json",
    ]
    try:
        job = run_json(command, attempts=1)[0]
    except RuntimeError:
        # Read the queue before retrying: an ambiguous submission that actually landed
        # would otherwise be paid for twice (series scar, encoded in _recover_provider_job).
        # That matcher pins speech_rate == 1, so an off-default rate never recovers and
        # simply re-submits — at ~0.09 credits a section that is the cheap side to be on.
        job = _recover_provider_job(provider_task(text), MARCUS_VOICE_ID)
        if job is None:
            job = run_json(command, attempts=1)[0]
    out_raw.parent.mkdir(parents=True, exist_ok=True)
    temporary = out_raw.with_suffix(".wav.tmp")
    urllib.request.urlretrieve(job["result_url"], temporary)
    temporary.replace(out_raw)
    return job


def clean(raw: Path, out: Path) -> None:
    """Same two-pass EBU R128 chain the series approved, at the daily lane's 44.1 kHz.

    Not generate_series_higgsfield_narration.clean_audio: that one pins 48 kHz 24-bit for
    the series render, and its module's hash is bound into the Episode 4 approval receipts,
    so it must not grow a parameter. Only the measurement pass is shared.
    """
    measured = loudnorm_measure(raw)
    filt = (
        "highpass=f=70,"
        "loudnorm=I=-16:LRA=11:TP=-1.5:"
        f"measured_I={measured['input_i']}:"
        f"measured_TP={measured['input_tp']}:"
        f"measured_LRA={measured['input_lra']}:"
        f"measured_thresh={measured['input_thresh']}:"
        f"offset={measured['target_offset']}:linear=true"
    )
    result = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-nostats", "-i", str(raw), "-af", filt,
         "-ar", str(SAMPLE_RATE_HZ), "-ac", "1", str(out)],
        capture_output=True, text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)


def _selftest() -> None:
    task = provider_task("Oil fell.")
    assert task["instruction"] == MARCUS_INSTRUCTION and task["text"] == "Oil fell."
    assert len(MARCUS_INSTRUCTION) <= 128        # provider caps the instruction field
    assert MODEL and JOB_TYPE == "qwen_audio_tts"
    assert SAMPLE_RATE_HZ == 44100               # must match the concat/captions contract
    # the band must actually span the 10-12 min ad floor at this voice's rate, or the
    # budget and the ruling it exists to satisfy have silently drifted apart
    assert WORD_BAND[0] / TARGET_WPM >= 10 and WORD_BAND[1] / TARGET_WPM <= 12
    print("tts-higgsfield self-test: 5/5 PASS")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prod", nargs="?", help="production folder (contains vo.txt)")
    ap.add_argument("--speech-rate", type=float, default=1.0,
                    help="delivery multiplier; measured 198 wpm at 1.0 against a 145 target, "
                         "so this is the calibration knob. ONE setting for the whole "
                         "production — per-scene varispeed is what sank ep02 v29.")
    ap.add_argument("--only", metavar="SECTION",
                    help="generate one approved section as an assets-stage voice sample")
    ap.add_argument("--dry-run", action="store_true",
                    help="print sections + credit shape, spend nothing")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)

    if a.selftest:
        _selftest()
        return 0
    if not a.prod:
        sys.exit("usage: tts_higgsfield.py <prod> [--only SECTION] [--dry-run]")

    prod = Path(a.prod).resolve()
    try:
        require_production_approval(prod)
    except ValueError as error:
        sys.exit(f"production approval gate blocked TTS: {error}")

    sections = force_daily_operator_voice(prod, parse_sections(prod))
    if a.only:
        sections = [section for section in sections if section["num"] == a.only]
        if not sections:
            sys.exit(f"unknown section for --only: {a.only}")
        print(f"[higgs] sample sections: {a.only}")
    speakers = {block["speaker"] for section in sections for block in section["blocks"]}
    if speakers != {"OPERATOR"}:
        # ponytail: one preset voice is wired. Add a speaker->voice map when the Show lane
        # needs Apollo; Higgsfield presets make that a dict, not a second module.
        sys.exit(f"Higgsfield VO is operator-only; script also asks for "
                 f"{sorted(speakers - {'OPERATOR'})}")

    texts = [section_text(section) for section in sections]
    total_words = sum(word_count(text) for text in texts)
    estimate = round(len(sections) * CREDITS_PER_SECTION, 2)
    print(f"[higgs] {len(sections)} sections, {total_words} words, "
          f"voice Marcus on {MODEL}, about {estimate} included credits")
    if a.dry_run:
        print(f"[higgs] dry run: nothing sent. account={account_status()}")
        return 0

    account = account_status()
    if not isinstance(account.get("credits"), (int, float)) or account["credits"] < estimate:
        sys.exit(f"Higgsfield credits {account.get('credits')!r} do not cover the "
                 f"{estimate} this production needs; $0-cash lane refuses to top up")

    build = prod / "build"
    build.mkdir(parents=True, exist_ok=True)
    meta, wavs = [], []
    for index, section in enumerate(sections):
        wav = build / section_wav_name(section)
        if wav.exists():  # same skip-existing contract as the other two TTS paths —
            print(f"[higgs] section {section['num']} ({section['slug']}) exists, skip")
        else:             # delete a wav to regenerate it
            raw = build / "raw" / wav.name
            synth(texts[index], raw, a.speech_rate)
            clean(raw, wav)
            print(f"[higgs] section {section['num']} ({section['slug']}) "
                  f"-> {duration(wav):.1f}s")
        seconds = duration(wav)
        # per-section wpm: a whole-file average hides one section drifting (2026-07-28)
        section_wpm = word_count(texts[index]) / (seconds / 60) if seconds else 0
        drift = "" if abs(section_wpm - TARGET_WPM) <= WPM_TOLERANCE else "  <-- OFF TARGET"
        print(f"[higgs]   section {section['num']}: {section_wpm:.0f} wpm{drift}")
        meta.append({**section, "wav": wav.name, "duration": round(seconds, 3),
                     "wpm": round(section_wpm)})
        wavs.append(wav)

    if a.only:
        print(f"[higgs] SAMPLE DONE: {wavs[0].name}")
        return 0

    full = build / "vo-full.wav"
    concat(wavs, full)
    (build / "sections.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    total = duration(full)
    wpm = total_words / (total / 60) if total else 0
    spread = max(m["wpm"] for m in meta) - min(m["wpm"] for m in meta)
    print(f"[higgs] DONE: {len(meta)} sections, {total/60:.1f} min -> build/vo-full.wav")
    print(f"[higgs] measured {wpm:.0f} wpm (target {TARGET_WPM}), per-section spread {spread}")
    if abs(wpm - TARGET_WPM) > WPM_TOLERANCE:
        print(f"[higgs] WARNING: off target — rerun with --speech-rate "
              f"{a.speech_rate * TARGET_WPM / wpm:.2f} after deleting build/vo-*.wav, or "
              f"re-size the script: at {wpm:.0f} wpm the 10-12 min ad floor needs "
              f"{int(wpm * 10):,}-{int(wpm * 12):,} words.")
    if not WORD_BAND[0] <= total_words <= WORD_BAND[1]:
        print(f"[higgs] WARNING: {total_words:,} words is outside the {WORD_BAND[0]:,}-"
              f"{WORD_BAND[1]:,} band this voice needs for 10-12 min. The master is "
              f"{total/60:.1f} min.")
    if spread > 2 * WPM_TOLERANCE:
        worst = min(meta, key=lambda m: m["wpm"])
        print(f"[higgs] WARNING: pace spread {spread} wpm across sections — slowest is "
              f"{worst['num']} ({worst['wpm']} wpm). Uneven delivery is usually number "
              "density, not the voice.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
