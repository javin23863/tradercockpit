#!/usr/bin/env python3
"""Create and feed the operator's Professional Voice Clone.

The account has ONE professional slot. Training it on the wrong audio burns it, so the
sample set is vetted here rather than trusted: every file must be a real microphone
recording. TTS output is refused outright -- a clone of a clone is how the slot gets wasted.

    python tools/pvc_clone.py --create --samples productions/_voice/pvc
    python tools/pvc_clone.py --status
    python tools/pvc_clone.py --train <voice_id>

The captcha step is the operator's: ElevenLabs requires a live recording of displayed text
to prove consent, and no stored file can satisfy it.

NOTE: eleven_v3 reports can_be_finetuned=false, so the finished PVC cannot run on it. Using
the PVC means the daily lane moves to a v2-family model.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from tts_elevenlabs import load_env  # noqa: E402

API = "https://api.elevenlabs.io/v1"
MIN_MINUTES = 30
BATCH_BYTES = 45_000_000          # keep each multipart request comfortably under the limit
# Any of these in a path means the audio is synthetic or already processed by a clone.
BANNED = ("vo-", "narration-clean", "EP02", "sample-", "apollo")


def headers():
    load_env()
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY missing")
    return {"xi-api-key": key}


def vet(sample_dir: Path):
    files, total = [], 0.0
    import subprocess
    for path in sorted(sample_dir.glob("*.wav")):
        if any(token.lower() in path.name.lower() for token in BANNED):
            sys.exit(f"refused: {path.name} looks like TTS output, not a microphone recording")
        dur = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
             str(path)], capture_output=True, text=True).stdout.strip() or 0)
        files.append((path, dur))
        total += dur
    if not files:
        sys.exit(f"no .wav samples in {sample_dir}")
    print(f"  {len(files)} samples, {total/60:.1f} min")
    if total / 60 < MIN_MINUTES:
        sys.exit(f"refused: {total/60:.1f} min is under the {MIN_MINUTES} min PVC floor")
    return files


def create(name, sample_dir, language="en"):
    h = headers()
    files = vet(Path(sample_dir))
    r = requests.post(f"{API}/voices/pvc", headers={**h, "Content-Type": "application/json"},
                      json={"name": name, "language": language,
                            "description": "TraderCockpit host voice, operator's own recordings"},
                      timeout=60)
    if r.status_code >= 400:
        sys.exit(f"create failed {r.status_code}: {r.text[:400]}")
    voice_id = r.json()["voice_id"]
    print(f"  voice_id {voice_id}")

    batch, size = [], 0
    def flush(batch):
        if not batch:
            return
        payload = [("files", (p.name, open(p, "rb"), "audio/wav")) for p in batch]
        resp = requests.post(f"{API}/voices/pvc/{voice_id}/samples", headers=h,
                             files=payload, timeout=900)
        for _, (_, handle, _) in payload:
            handle.close()
        if resp.status_code >= 400:
            sys.exit(f"sample upload failed {resp.status_code}: {resp.text[:400]}")
        print(f"    uploaded {len(batch)} sample(s)")

    for path, _ in files:
        if size + path.stat().st_size > BATCH_BYTES and batch:
            flush(batch); batch, size = [], 0
        batch.append(path); size += path.stat().st_size
    flush(batch)
    return voice_id


def status():
    h = headers()
    data = requests.get(f"{API}/v2/voices?page_size=100".replace("/v1/v2", "/v2"),
                        headers=h, timeout=30)
    if data.status_code >= 400:
        data = requests.get("https://api.elevenlabs.io/v2/voices?page_size=100",
                            headers=h, timeout=30)
    for v in data.json().get("voices", []):
        if v.get("category") == "professional" or "pvc" in str(v.get("voice_id", "")):
            print(f"  {v['voice_id']}  {v.get('name')}  category={v.get('category')} "
                  f"state={v.get('fine_tuning', {}).get('state')}")
    sub = requests.get(f"{API}/user/subscription", headers=h, timeout=20).json()
    print(f"  professional slots used {sub.get('professional_voice_slots_used')}"
          f"/{sub.get('professional_voice_limit')}")


def train(voice_id):
    h = headers()
    r = requests.post(f"{API}/voices/pvc/{voice_id}/train", headers=h,
                      json={"model_id": "eleven_multilingual_v2"}, timeout=60)
    print(f"  train -> {r.status_code} {r.text[:300]}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--samples", default="productions/_voice/pvc")
    ap.add_argument("--name", default="Operator (TraderCockpit)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--train", metavar="VOICE_ID")
    a = ap.parse_args()
    if a.status:
        status(); return 0
    if a.train:
        train(a.train); return 0
    if a.create:
        vid = create(a.name, a.samples)
        print(f"\nNEXT: the operator must pass the ElevenLabs consent captcha for {vid} "
              f"(a live reading of displayed text; no stored file can satisfy it), then:\n"
              f"  python tools/pvc_clone.py --train {vid}")
        return 0
    ap.error("choose --create, --status or --train")


if __name__ == "__main__":
    raise SystemExit(main())
