#!/usr/bin/env python3
"""Voice-cloned VO stage — drop-in replacement for produce.py --stage vo.

Uses Chatterbox (Resemble AI, MIT) zero-shot cloning from ONE reference wav of
the operator's voice. Emits the SAME build/ artifacts as produce.stage_vo
(vo-NN.wav, vo-full.wav, sections.json), so `produce.py --stage captions` and
`--stage assemble` run downstream unchanged.

Run with the ISOLATED clone venv (chatterbox pins torch==2.6.0, kept out of the
OpenMontage venv):
  productions/_voice/.venv-clone/Scripts/python.exe tools/tts_chatterbox.py \
      productions/sample-hormuz --ref productions/_voice/operator.wav

--exaggeration/--cfg are Chatterbox's delivery knobs (0.5/0.5 = natural; raise
exaggeration for more energy, lower cfg for slower/steadier). Restore defaults
if a render sounds off — the physical voice needs tuning a fixed model can't see.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

GAP_S = 0.45          # silence between sections — matches produce.GAP_S
CHUNK_CHARS = 280     # Chatterbox degrades past ~40s/one breath; split long sections


def parse_sections(prod: Path):
    """Same '## NN slug' parser as produce.parse_sections (kept local to avoid
    importing produce.py, which lives in the OTHER venv)."""
    text = (prod / "vo.txt").read_text(encoding="utf-8")
    sections, cur = [], None
    for line in text.splitlines():
        if line.startswith("## "):
            if cur:
                sections.append(cur)
            num, _, slug = line[3:].strip().partition(" ")
            cur = {"num": num, "slug": slug, "text": ""}
        elif line.startswith("#"):
            continue
        elif cur is not None:
            cur["text"] += line.strip() + " "
    if cur:
        sections.append(cur)
    for s in sections:
        s["text"] = s["text"].strip()
    if not sections:
        sys.exit("no '## NN slug' sections found in vo.txt")
    return sections


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


def _selftest() -> None:
    # the only non-trivial logic here is the chunker — assert it splits + never drops text
    long = "One. Two two two. " * 40
    cs = chunk(long, limit=80)
    assert all(len(c) <= 80 for c in cs), [len(c) for c in cs]       # never exceeds limit here
    assert " ".join(cs).split() == long.split(), "chunker dropped/reordered words"
    assert chunk("No enders here just words") == ["No enders here just words"]
    assert len(chunk("a. " * 200, limit=50)) > 1, "long text must split"
    print("selftest OK")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prod", nargs="?", help="production folder (contains vo.txt)")
    ap.add_argument("--ref", help="reference wav/mp3 of the voice to clone")
    ap.add_argument("--exaggeration", type=float, default=0.5)
    ap.add_argument("--cfg", type=float, default=0.5)
    ap.add_argument("--selftest", action="store_true", help="check the chunker, no model")
    a = ap.parse_args()

    if a.selftest:
        _selftest()
        return 0
    if not a.prod or not a.ref:
        sys.exit("usage: tts_chatterbox.py <prod> --ref <voice.wav>")

    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS

    prod = Path(a.prod).resolve()
    ref = Path(a.ref).resolve()
    if not ref.exists():
        sys.exit(f"reference audio not found: {ref}")
    build = prod / "build"
    build.mkdir(parents=True, exist_ok=True)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[clone] loading Chatterbox on {device}, ref={ref.name}", flush=True)
    model = ChatterboxTTS.from_pretrained(device=device)
    sr = model.sr
    gap = torch.zeros(1, int(GAP_S * sr))

    sections = parse_sections(prod)
    meta, full = [], []
    for s in sections:
        out = build / f"vo-{s['num']}.wav"
        if out.exists():  # same skip-existing contract as produce.stage_vo —
            audio, file_sr = ta.load(str(out))  # delete a wav to regenerate that section
            if file_sr != sr:
                audio = ta.functional.resample(audio, file_sr, sr)
            print(f"[clone] section {s['num']} ({s['slug']}) exists, skip", flush=True)
        else:
            pieces = []
            for c in chunk(s["text"]):
                wav = model.generate(c, audio_prompt_path=str(ref),
                                     exaggeration=a.exaggeration, cfg_weight=a.cfg)
                pieces.append(wav if wav.dim() == 2 else wav.unsqueeze(0))
            audio = torch.cat(pieces, dim=1)
            ta.save(str(out), audio, sr)
            print(f"[clone] section {s['num']} ({s['slug']}) -> {audio.shape[1]/sr:.1f}s", flush=True)
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
