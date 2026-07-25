#!/usr/bin/env python3
"""Voice-cloned VO stage — drop-in replacement for produce.py --stage vo.

Uses Chatterbox (Resemble AI, MIT) zero-shot cloning from per-speaker reference
audio. Untagged narration uses the operator voice. Emits the SAME build/ artifacts
as produce.stage_vo
(vo-NN.wav, vo-full.wav, sections.json), so `produce.py --stage captions` and
`--stage assemble` run downstream unchanged.

Daily productions are operator-only. Stale speaker tags in a `daily-*` script are
normalized to OPERATOR, and `--apollo-ref` is rejected. Hybrid narration remains
available to the separate Show lane.

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
JOIN_PAUSE_S = 0.15   # breath at a chunk join; chunks used to be welded with zero gap
TRIM_FLOOR_DB = -45.0 # head/tail below this (relative to the chunk's own peak) is not speech
SEED_DEFAULT = 4242
COMMIT_NEEDED_GB = 8.0
DEFAULT_OPERATOR_REF = Path(__file__).resolve().parents[1] / "productions" / "_voice" / "operator-clean.wav"


def commit_headroom_gb():
    """Windows commit-charge headroom in GB, or None off Windows.

    The 2026-07-20 incident (reproduced 3x) is a COMMIT ceiling, not free RAM: this box is
    16 GB RAM + a fixed 16 GB pagefile, so commit caps at 32 GB and Chatterbox needs ~8 GB of
    it. Failure faces are OSError 1455 at safetensors load, 0xC0000005 at model load, or a
    tiny numpy allocation failing mid-sampling — all the same cause.
    """
    if sys.platform != "win32":
        return None
    import ctypes

    class MemoryStatusEx(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

    status = MemoryStatusEx()
    status.dwLength = ctypes.sizeof(MemoryStatusEx)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
        return None
    return status.ullAvailPageFile / 1024 ** 3


def trim_silence(wav, sr, floor_db=TRIM_FLOOR_DB):
    """Drop head/tail near-silence from one generated chunk.

    Chunks are concatenated, so without this one chunk's trailing breath gets welded straight
    onto the next chunk's leading silence ~45 times a video.
    """
    amp = wav.abs().max(dim=0).values
    peak = float(amp.max())
    if peak <= 0:
        return wav
    loud = (amp > peak * (10 ** (floor_db / 20))).nonzero()
    if loud.numel() == 0:
        return wav
    keep = int(0.02 * sr)      # leave 20ms so consonant onsets and tails survive the trim
    first = max(int(loud[0]) - keep, 0)
    last = min(int(loud[-1]) + keep, wav.shape[1])
    return wav[:, first:last]


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


def force_daily_operator_voice(prod: Path, sections: list[dict]) -> list[dict]:
    if not prod.name.startswith("daily-"):
        return sections
    for section in sections:
        section["speaker"] = "OPERATOR"
        for block in section["blocks"]:
            block["speaker"] = "OPERATOR"
    return sections


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
    daily = [{"speaker": "APOLLO", "blocks": [{"speaker": "APOLLO", "text": "News."}]}]
    assert force_daily_operator_voice(Path("daily-2026-07-22"), daily)[0]["blocks"][0][
        "speaker"] == "OPERATOR"
    show = [{"speaker": "APOLLO", "blocks": [{"speaker": "APOLLO", "text": "Analysis."}]}]
    assert force_daily_operator_voice(Path("show-s1e1"), show)[0]["blocks"][0][
        "speaker"] == "APOLLO"
    headroom = commit_headroom_gb()
    assert headroom is None or headroom > 0, headroom
    try:
        import torch
    except ModuleNotFoundError:
        print("selftest OK (trim_silence skipped: torch absent)")
        return
    sr, keep = 24000, int(0.02 * 24000)
    padded = torch.cat([torch.zeros(1, sr // 2), torch.ones(1, sr) * 0.5,
                        torch.zeros(1, sr // 2)], dim=1)
    trimmed = trim_silence(padded, sr)
    assert abs(trimmed.shape[1] - (sr + 2 * keep)) <= 2, trimmed.shape   # keeps 20ms each side
    assert trim_silence(torch.zeros(1, 100), sr).shape[1] == 100         # all-silent: untouched
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
    ap.add_argument("--seed", type=int, default=SEED_DEFAULT,
                    help="per-chunk sampling seed; keeps a re-rendered section identical")
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

    if prod.name.startswith("daily-") and a.apollo_ref:
        sys.exit("daily narration is operator-only; --apollo-ref is not allowed")
    sections = force_daily_operator_voice(prod, parse_sections(prod))
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

    headroom = commit_headroom_gb()
    if headroom is not None and headroom < COMMIT_NEEDED_GB:
        sys.exit(
            f"commit headroom {headroom:.1f} GB < {COMMIT_NEEDED_GB} GB needed by Chatterbox.\n"
            "This is commit charge, not free RAM. Close TradingView, Chromium/Firefox apps and\n"
            "orphan codex app-servers; if an esq run holds multi-GB commit, wait it out rather\n"
            "than killing it. Rendering now would fail mid-sampling and waste the whole pass."
        )

    import torch
    import torchaudio as ta
    from chatterbox.tts import ChatterboxTTS

    build = prod / "build"
    build.mkdir(parents=True, exist_ok=True)

    # what the previous render actually spoke, so an edited section cannot ship stale audio
    prior_sha = {}
    meta_path = build / "sections.json"
    if meta_path.is_file():
        try:
            prior_sha = {entry["wav"]: entry.get("textSha256")
                         for entry in json.loads(meta_path.read_text(encoding="utf-8"))}
        except (ValueError, TypeError, KeyError):
            prior_sha = {}

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[clone] loading Chatterbox on {device}", flush=True)
    model = ChatterboxTTS.from_pretrained(device=device)
    sr = model.sr
    gap = torch.zeros(1, int(GAP_S * sr))

    meta, full = [], []
    pause = torch.zeros(1, int(JOIN_PAUSE_S * sr))
    for s in sections:
        out = build / section_wav_name(s, apollo_key)
        text_sha = hashlib.sha256(s["text"].encode("utf-8")).hexdigest()
        recorded = prior_sha.get(out.name)
        # a pre-sha sections.json records nothing, so trust those rather than force a full
        # re-render; only a sha that EXISTS and differs means the script moved under the audio
        stale = out.exists() and recorded is not None and recorded != text_sha
        if out.exists() and not stale:  # same skip-existing contract as produce.stage_vo —
            audio, file_sr = ta.load(str(out))  # delete a wav to regenerate that section
            if file_sr != sr:
                audio = ta.functional.resample(audio, file_sr, sr)
            print(f"[clone] section {s['num']} ({s['slug']}) exists, skip", flush=True)
        else:
            if stale:
                print(f"[clone] section {s['num']} ({s['slug']}) text changed since its wav "
                      "-> re-rendering", flush=True)
            pieces = []
            for block_idx, block in enumerate(s["blocks"]):
                for chunk_idx, c in enumerate(chunk(block["text"])):
                    # seed per chunk, not once per run: re-rendering ONE section has to
                    # reproduce it, and a run-level seed makes that depend on what ran before
                    torch.manual_seed(a.seed + 1_000_000 * int(s["num"])
                                      + 1000 * block_idx + chunk_idx)
                    wav = model.generate(c, audio_prompt_path=str(refs[block["speaker"]]),
                                         exaggeration=a.exaggeration, cfg_weight=a.cfg)
                    pieces.append(trim_silence(wav if wav.dim() == 2 else wav.unsqueeze(0), sr))
            joined = []
            for piece in pieces:
                joined.extend([piece, pause])
            audio = torch.cat(joined[:-1], dim=1)
            ta.save(str(out), audio, sr)
            voices = "+".join(block["speaker"] for block in s["blocks"])
            print(f"[clone] section {s['num']} ({s['slug']}, {voices}) "
                  f"-> {audio.shape[1]/sr:.1f}s", flush=True)
        dur = audio.shape[1] / sr
        meta.append({**s, "wav": out.name, "duration": round(dur, 3),
                     "textSha256": text_sha, "seed": a.seed})
        full.extend([audio, gap])

    full_wav = torch.cat(full[:-1], dim=1)
    ta.save(str(build / "vo-full.wav"), full_wav, sr)
    (build / "sections.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    total = full_wav.shape[1] / sr
    print(f"[clone] DONE: {len(meta)} sections, {total/60:.1f} min -> build/vo-full.wav")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
