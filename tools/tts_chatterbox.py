#!/usr/bin/env python3
"""Voice-cloned VO stage — drop-in replacement for produce.py --stage vo.

Uses Chatterbox (Resemble AI, MIT) zero-shot cloning from per-speaker reference
audio. Untagged narration uses the operator voice. Emits the SAME build/ artifacts
as produce.stage_vo
(vo-NN.wav, vo-full.wav, sections.json), so `produce.py --stage captions` and
`--stage assemble` run downstream unchanged.

Run with the repository's isolated Chatterbox venv:
  OpenMontage/.venv-chatterbox/Scripts/python.exe tools/tts_chatterbox.py \
      productions/sample-hormuz --operator-ref productions/_voice/operator-clean.wav \
      --apollo-ref productions/_voice/apollo-candidates/<approved-file>.wav

--exaggeration/--cfg are Chatterbox's delivery knobs (0.5/0.5 = natural; raise
exaggeration for more energy, lower cfg for slower/steadier). Restore defaults
if a render sounds off — the physical voice needs tuning a fixed model can't see.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from tools.produce import parse_sections, require_production_approval
except ModuleNotFoundError:  # direct `python tools/tts_chatterbox.py` execution
    from produce import parse_sections, require_production_approval

GAP_S = 0.45          # silence between sections — matches produce.GAP_S
CHUNK_CHARS = 280     # Chatterbox degrades past ~40s/one breath; split long sections
DEFAULT_OPERATOR_REF = Path(__file__).resolve().parents[1] / "productions" / "_voice" / "operator-clean.wav"


def chunk(text: str, limit: int = CHUNK_CHARS) -> list[str]:
    """Group sentences into <=limit-char chunks so each generate() is one clean
    breath. Split on sentence enders only — keeps '76.56' / 'A.M.D.' intact."""
    sents = re.split(r"(?<=[.!?])\s+", text.strip())
    out, buf = [], ""
    for s in sents:
        if not s:
            continue
        if buf and len(buf) + 1 + len(s) > limit:
            out.append(buf)
            buf = s
        else:
            buf = f"{buf} {s}".strip()
    if buf:
        out.append(buf)
    return out or [text]


def section_wav_name(section, apollo_key=None):
    speakers = {block["speaker"] for block in section["blocks"]}
    if speakers == {"OPERATOR"}:
        return f"vo-{section['num']}.wav"
    label = "apollo" if speakers == {"APOLLO"} else "duo"
    return f"vo-{section['num']}-{label}-{apollo_key[:8]}.wav"


def _selftest() -> None:
    # the only non-trivial logic here is the chunker — assert it splits + never drops text
    long = "One. Two two two. " * 40
    cs = chunk(long, limit=80)
    assert all(len(c) <= 80 for c in cs), [len(c) for c in cs]       # never exceeds limit here
    assert " ".join(cs).split() == long.split(), "chunker dropped/reordered words"
    assert chunk("No enders here just words") == ["No enders here just words"]
    assert len(chunk("a. " * 200, limit=50)) > 1, "long text must split"
    assert section_wav_name({"num": "01", "blocks": [{"speaker": "OPERATOR"}]}) == "vo-01.wav"
    assert section_wav_name({"num": "02", "blocks": [{"speaker": "APOLLO"}]}, "abcdef1234") == \
        "vo-02-apollo-abcdef12.wav"
    print("selftest OK")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prod", nargs="?", help="production folder (contains vo.txt)")
    ap.add_argument("--ref", "--operator-ref", dest="operator_ref", default=str(DEFAULT_OPERATOR_REF),
                    help="operator reference audio (default: productions/_voice/operator-clean.wav)")
    ap.add_argument("--apollo-ref", help="operator-approved Apollo reference audio")
    ap.add_argument("--exaggeration", type=float, default=0.5)
    ap.add_argument("--cfg", type=float, default=0.5)
    ap.add_argument("--selftest", action="store_true", help="check the chunker, no model")
    a = ap.parse_args()

    if a.selftest:
        _selftest()
        return 0
    if not a.prod:
        sys.exit("usage: tts_chatterbox.py <prod> [--apollo-ref <approved-voice.wav>]")

    prod = Path(a.prod).resolve()
    operator_ref = Path(a.operator_ref).resolve()
    if not operator_ref.exists():
        sys.exit(f"operator reference audio not found: {operator_ref}")
    try:
        require_production_approval(prod)
    except ValueError as error:
        sys.exit(f"production approval gate blocked TTS: {error}")

    sections = parse_sections(prod)
    needs_apollo = any(block["speaker"] == "APOLLO"
                       for section in sections for block in section["blocks"])
    if needs_apollo and not a.apollo_ref:
        sys.exit("Apollo narration requires --apollo-ref with the exact operator-approved sample")
    refs = {"OPERATOR": operator_ref}
    if a.apollo_ref:
        refs["APOLLO"] = Path(a.apollo_ref).resolve()
        if not refs["APOLLO"].exists():
            sys.exit(f"Apollo reference audio not found: {refs['APOLLO']}")
    apollo_key = (hashlib.sha256(refs["APOLLO"].read_bytes()).hexdigest()
                  if "APOLLO" in refs else None)

    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS

    build = prod / "build"
    build.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[clone] loading Chatterbox on {device}", flush=True)
    model = ChatterboxTTS.from_pretrained(device=device)
    sr = model.sr
    gap = torch.zeros(1, int(GAP_S * sr))

    meta, full = [], []
    for s in sections:
        out = build / section_wav_name(s, apollo_key)
        if out.exists():  # same skip-existing contract as produce.stage_vo —
            audio, file_sr = ta.load(str(out))  # delete a wav to regenerate that section
            if file_sr != sr:
                audio = ta.functional.resample(audio, file_sr, sr)
            print(f"[clone] section {s['num']} ({s['slug']}) exists, skip", flush=True)
        else:
            pieces = []
            for block in s["blocks"]:
                for c in chunk(block["text"]):
                    wav = model.generate(c, audio_prompt_path=str(refs[block["speaker"]]),
                                         exaggeration=a.exaggeration, cfg_weight=a.cfg)
                    pieces.append(wav if wav.dim() == 2 else wav.unsqueeze(0))
            audio = torch.cat(pieces, dim=1)
            ta.save(str(out), audio, sr)
            voices = "+".join(block["speaker"] for block in s["blocks"])
            print(f"[clone] section {s['num']} ({s['slug']}, {voices}) "
                  f"-> {audio.shape[1]/sr:.1f}s", flush=True)
        dur = audio.shape[1] / sr
        meta.append({**s, "wav": out.name, "duration": round(dur, 3)})
        full.extend([audio, gap])

    full_wav = torch.cat(full[:-1], dim=1)
    ta.save(str(build / "vo-full.wav"), full_wav, sr)
    (build / "sections.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    total = full_wav.shape[1] / sr
    print(f"[clone] DONE: {len(meta)} sections, {total/60:.1f} min -> build/vo-full.wav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
