#!/usr/bin/env python3
"""Faceless production runner: vo.txt + visuals/ -> published video.

Production folder layout (productions/<name>/):
  vo.txt            sections: "## NN visual-slug" header + narration paragraph
  visuals/          one file per section, named NN-*.mp4 or NN-*.png
  build/            generated: per-section wav, sections.json, master.mp4 ...

Stages (each idempotent, resumable):
  python produce.py productions/video-01 --stage vo         # Kokoro TTS per section
  python produce.py productions/video-01 --stage captions   # faster-whisper -> srt
  python produce.py productions/video-01 --stage assemble   # visuals x durations + vo + subs
  python produce.py productions/video-01 --stage shorts     # studio-kit clipper
  python produce.py productions/video-01 --stage all

Run with the OpenMontage venv python (has kokoro + faster-whisper + soundfile).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
HUB = HERE.parent
FFMPEG = "ffmpeg"
VOICE = "bm_george"  # kokoro JARVIS-style British male (the machine narrator); swap with --voice
GAP_S = 0.45        # silence between sections


def log(msg):
    print(f"[produce] {msg}", flush=True)


def parse_sections(prod: Path):
    text = (prod / "vo.txt").read_text(encoding="utf-8")
    sections = []
    cur = None
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


def stage_vo(prod: Path, voice: str):
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    build = prod / "build"
    build.mkdir(exist_ok=True)
    sections = parse_sections(prod)
    pipe = KPipeline(lang_code="a")
    meta = []
    for s in sections:
        out = build / f"vo-{s['num']}.wav"
        if not out.exists():
            log(f"TTS section {s['num']} ({s['slug']}) — {len(s['text'])} chars")
            chunks = [audio for _, _, audio in pipe(s["text"], voice=voice)]
            audio = np.concatenate(chunks)
            sf.write(out, audio, 24000)
        dur = sf.info(out).duration
        meta.append({**s, "wav": out.name, "duration": round(dur, 3)})
    # concat with gaps
    gap = np.zeros(int(GAP_S * 24000), dtype="float32")
    full = []
    for m in meta:
        data, _ = sf.read(build / m["wav"], dtype="float32")
        full.extend([data, gap])
    sf.write(build / "vo-full.wav", np.concatenate(full[:-1]), 24000)
    (build / "sections.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    total = sum(m["duration"] for m in meta) + GAP_S * (len(meta) - 1)
    log(f"VO done: {len(meta)} sections, {total/60:.1f} min -> build/vo-full.wav")


def stage_captions(prod: Path):
    from faster_whisper import WhisperModel

    build = prod / "build"
    wav = build / "vo-full.wav"
    if not wav.exists():
        sys.exit("run --stage vo first")
    log("transcribing for word-level captions (faster-whisper small)...")
    model = WhisperModel("small", device="auto", compute_type="int8")
    segments, _ = model.transcribe(str(wav), word_timestamps=True)

    def ts(t):
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h):02}:{int(m):02}:{int(s):02},{int((s % 1) * 1000):03}"

    lines, i = [], 1
    for seg in segments:
        words = seg.words or []
        # group words into <=5-word caption chunks (platform norm)
        for j in range(0, len(words), 5):
            grp = words[j:j + 5]
            lines += [str(i), f"{ts(grp[0].start)} --> {ts(grp[-1].end)}",
                      " ".join(w.word.strip() for w in grp), ""]
            i += 1
    (build / "captions.srt").write_text("\n".join(lines), encoding="utf-8")
    log(f"captions.srt written ({i - 1} cues)")


def stage_assemble(prod: Path):
    build = prod / "build"
    meta = json.loads((build / "sections.json").read_text(encoding="utf-8"))
    visdir = prod / "visuals"
    parts = []
    for k, m in enumerate(meta):
        matches = sorted(visdir.glob(f"{m['num']}-*")) if visdir.exists() else []
        if not matches:
            sys.exit(f"missing visual for section {m['num']} ({m['slug']}) in {visdir}")
        vis = matches[0]
        dur = m["duration"] + (GAP_S if k < len(meta) - 1 else 0)
        part = build / f"part-{m['num']}.mp4"
        if not part.exists():
            log(f"section {m['num']}: {vis.name} -> {dur:.1f}s")
            scale_vf = ("scale=1920:1080:force_original_aspect_ratio=decrease,"
                        "pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p")
            enc = ["-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20", str(part)]
            if vis.suffix.lower() == ".png":
                cmd = [FFMPEG, "-y", "-loop", "1", "-t", f"{dur:.3f}", "-i", str(vis),
                       "-vf", scale_vf, *enc]
            else:
                vd = float(subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", str(vis)],
                    check=True, capture_output=True, text=True).stdout.strip())
                if vd >= dur or dur > 2 * vd:
                    # long enough (trim), or too short for one bounce (loop restart,
                    # least-bad fallback — log it so the gap is a known cut, not a surprise)
                    if dur > 2 * vd:
                        log(f"  WARN {vis.name} {vd:.1f}s < half of {dur:.1f}s -> loop restart visible")
                    cmd = [FFMPEG, "-y", "-stream_loop", "-1", "-t", f"{dur:.3f}",
                           "-i", str(vis), "-vf", scale_vf, *enc]
                else:
                    # shorter than the VO: append the reversed tail (boomerang) —
                    # seamless direction flip instead of a jump-cut loop restart
                    tail = min(dur - vd + 0.5, vd)
                    cmd = [FFMPEG, "-y", "-i", str(vis), "-sseof", f"-{tail:.3f}",
                           "-i", str(vis), "-filter_complex",
                           f"[1:v]reverse[r];[0:v][r]concat=n=2:v=1,{scale_vf}[v]",
                           "-map", "[v]", "-t", f"{dur:.3f}", *enc]
            subprocess.run(cmd, check=True, capture_output=True)
        parts.append(part)
    concat = build / "concat.txt"
    concat.write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
    log("concatenating + muxing VO + burning captions...")
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-i", str(build / "vo-full.wav"),
                    "-vf", "subtitles=captions.srt:force_style="
                    "'FontName=Cascadia Mono,FontSize=13,PrimaryColour=&HEAE8F5,"
                    "OutlineColour=&H0A0308,Outline=2,Bold=1,MarginV=40'",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-c:a", "aac", "-b:a", "192k", "-shortest",
                    str(build / "master.mp4")], check=True, cwd=build, capture_output=True)
    # caption-free copy for the shorts lane (clipper burns its own 9:16-sized captions)
    subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                    "-i", str(build / "vo-full.wav"),
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    str(build / "master-clean.mp4")], check=True, cwd=build, capture_output=True)
    log(f"master: {build / 'master.mp4'}")


def stage_shorts(prod: Path):
    clipper = HUB / "studio-kit" / "clipper"
    master = prod / "build" / "master-clean.mp4"  # caption-free; clipper burns its own
    if not master.exists():
        master = prod / "build" / "master.mp4"
    if not master.exists():
        sys.exit("run --stage assemble first")
    if not (clipper / "node_modules").exists():
        log("installing clipper deps (one-time)...")
        subprocess.run(["npm", "install"], cwd=clipper, check=True, shell=True)
    log("clipper: highlight pick + 9:16 reframe...")
    subprocess.run(["node", "clip.js", str(master), "--reframe",
                    "--srt", str(prod / "build" / "captions.srt")],
                   cwd=clipper, check=True, shell=True)
    log(f"shorts in {clipper / 'output'}")


STAGES = {"vo": stage_vo, "captions": stage_captions, "assemble": stage_assemble, "shorts": stage_shorts}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("production", help="production folder (contains vo.txt)")
    p.add_argument("--stage", default="all", choices=[*STAGES, "all"])
    p.add_argument("--voice", default=VOICE)
    args = p.parse_args()
    prod = Path(args.production).resolve()
    if not (prod / "vo.txt").exists():
        sys.exit(f"no vo.txt in {prod}")
    order = list(STAGES) if args.stage == "all" else [args.stage]
    for name in order:
        log(f"=== stage: {name} ===")
        STAGES[name](prod, args.voice) if name == "vo" else STAGES[name](prod)


if __name__ == "__main__":
    main()
