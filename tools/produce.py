#!/usr/bin/env python3
"""Faceless production runner: vo.txt + visuals/ -> published video.

Production folder layout (productions/<name>/):
  vo.txt            "## NN visual-slug [APOLLO]" sections; optional "### SPEAKER" blocks
  scene-plan.json   exact narration-beat -> visual mapping (required)
  visuals/          visual files referenced by scene-plan.json
  build/            generated: per-section wav, sections.json, master.mp4 ...

Stages (each idempotent, resumable):
  python produce.py productions/video-01 --stage vo         # Chatterbox TTS per speaker
  python produce.py productions/video-01 --stage captions   # faster-whisper -> srt
  python produce.py productions/video-01 --stage assemble   # visuals x durations + vo + subs
  python produce.py productions/video-01 --stage shorts     # studio-kit clipper
  python produce.py productions/video-01 --stage all

The VO stage delegates to the repository-local isolated Chatterbox venv.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    from tools.script_approval import require_production_approval
except ModuleNotFoundError:  # direct `python tools/produce.py` execution
    from script_approval import require_production_approval

HERE = Path(__file__).parent
HUB = HERE.parent
FFMPEG = "ffmpeg"
GAP_S = 0.45        # silence between sections
VIDEO_FPS = 30
TRANSITION_FRAMES = 12   # 0.4s crossfade between beats (operator ruling 2026-07-17: smooth transitions)
PAD_COLOR = "0xFFFFFF"   # contain padding; white world per operator ruling (charts + news share white)
OPERATOR_REF = HUB / "productions" / "_voice" / "operator-clean.wav"
CHATTERBOX_PYTHON = HUB / "OpenMontage" / ".venv-chatterbox" / (
    "Scripts/python.exe" if os.name == "nt" else "bin/python")


def log(msg):
    print(f"[produce] {msg}", flush=True)


def allocate_frame_counts(timeline, fps=VIDEO_FPS):
    """Quantize cumulative beat boundaries once so rounding cannot drift."""
    counts = []
    previous_end = 0
    for beat in timeline:
        start = round(float(beat["start"]) * fps)
        end = round((float(beat["start"]) + float(beat["duration"])) * fps)
        if start != previous_end:
            raise ValueError(f"non-contiguous timeline at {beat.get('id', '?')}")
        counts.append(max(1, end - start))
        previous_end = end
    return counts


def parse_sections(prod: Path):
    text = (prod / "vo.txt").read_text(encoding="utf-8")
    sections = []
    cur = None
    speaker = "OPERATOR"
    block_text = ""

    def add_block():
        nonlocal block_text
        content = block_text.strip()
        if content:
            block = {"speaker": speaker, "text": content}
            if cur["blocks"] and cur["blocks"][-1]["speaker"] == speaker:
                cur["blocks"][-1]["text"] += " " + content
            else:
                cur["blocks"].append(block)
        block_text = ""

    def add_section():
        nonlocal cur
        if cur is None:
            return
        add_block()
        voices = {block["speaker"] for block in cur["blocks"]}
        cur["speaker"] = next(iter(voices)) if len(voices) == 1 else None
        cur["text"] = " ".join(block["text"] for block in cur["blocks"])
        sections.append(cur)
        cur = None

    for line in text.splitlines():
        if line.startswith("## "):
            add_section()
            num, _, slug = line[3:].strip().partition(" ")
            tagged = re.search(r"\s+\[(OPERATOR|APOLLO)\]\s*$", slug, re.IGNORECASE)
            speaker = tagged.group(1).upper() if tagged else "OPERATOR"
            if tagged:
                slug = slug[:tagged.start()].rstrip()
            cur = {"num": num, "slug": slug, "blocks": []}
        elif cur is not None and (tagged := re.fullmatch(
                r"\s*###\s+(OPERATOR|APOLLO)\s*", line, re.IGNORECASE)):
            add_block()
            speaker = tagged.group(1).upper()
        elif line.startswith("#"):
            continue
        elif cur is not None:
            block_text += line.strip() + " "
    add_section()
    if not sections:
        sys.exit("no '## NN slug' sections found in vo.txt")
    return sections


def stage_vo(prod: Path, operator_ref=OPERATOR_REF, apollo_ref=None):
    if not CHATTERBOX_PYTHON.is_file():
        sys.exit(f"Chatterbox Python not found: {CHATTERBOX_PYTHON}")
    cmd = [str(CHATTERBOX_PYTHON), str(HERE / "tts_chatterbox.py"), str(prod),
           "--operator-ref", str(operator_ref)]
    if apollo_ref:
        cmd.extend(["--apollo-ref", str(apollo_ref)])
    subprocess.run(cmd, check=True)


def stage_captions(prod: Path):
    build = prod / "build"
    wav = build / "vo-full.wav"
    if not wav.exists():
        sys.exit("run --stage vo first")

    def ts(t):
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h):02}:{int(m):02}:{int(s):02},{int((s % 1) * 1000):03}"

    lines, i = [], 1
    mode = "faster-whisper"
    try:
        from faster_whisper import WhisperModel

        log("transcribing for word-level captions (faster-whisper small)...")
        model = WhisperModel("small", device="auto", compute_type="int8")
        segments, _ = model.transcribe(str(wav), word_timestamps=True)
        for seg in segments:
            words = seg.words or []
            # group words into <=5-word caption chunks (platform norm)
            for j in range(0, len(words), 5):
                grp = words[j:j + 5]
                lines += [str(i), f"{ts(grp[0].start)} --> {ts(grp[-1].end)}",
                          " ".join(w.word.strip() for w in grp), ""]
                i += 1
    except ImportError as exc:
        # Windows Application Control can block PyAV's native DLL. The narration is
        # generated from the exact script, so fall back to script-locked cues rather
        # than bypassing policy or shipping transcription errors.
        mode = "script-locked-timing"
        log(f"faster-whisper unavailable ({exc}); using script-locked timings")
        meta = json.loads((build / "sections.json").read_text(encoding="utf-8"))
        offset = 0.0
        for section in meta:
            words = section["text"].split()
            groups = [words[j:j + 5] for j in range(0, len(words), 5)]
            weights = [max(len(" ".join(group)), 1) for group in groups]
            total_weight = sum(weights)
            cursor = offset
            section_end = offset + section["duration"]
            for j, (group, weight) in enumerate(zip(groups, weights)):
                end = section_end if j == len(groups) - 1 else cursor + section["duration"] * weight / total_weight
                lines += [str(i), f"{ts(cursor)} --> {ts(end)}", " ".join(group), ""]
                cursor = end
                i += 1
            offset = section_end + GAP_S
    (build / "captions.srt").write_text("\n".join(lines), encoding="utf-8")
    (build / "caption-receipt.json").write_text(
        json.dumps({"mode": mode, "cues": i - 1}, indent=2), encoding="utf-8")
    log(f"captions.srt written ({i - 1} cues; {mode})")


def stage_assemble(prod: Path):
    from editorial_gate import load_timeline

    build = prod / "build"
    try:
        timeline = load_timeline(prod, gap_s=GAP_S)
    except ValueError as exc:
        sys.exit(f"editorial gate blocked assembly:\n{exc}")
    parts = []
    frame_counts = allocate_frame_counts(timeline)
    for index, (beat, frame_count) in enumerate(zip(timeline, frame_counts)):
        vis = prod / beat["visual"]["path"]
        # every part except the last carries extra tail frames that the xfade consumes,
        # so beat slots (and VO sync) keep their exact original durations
        render_frames = frame_count + (TRANSITION_FRAMES if index < len(timeline) - 1 else 0)
        dur = render_frames / VIDEO_FPS
        part = build / f"part-{beat['id']}.mp4"
        log(f"beat {beat['id']}: {vis.name} -> {dur:.3f}s ({render_frames} frames incl transition tail)")
        if beat["visual"]["fit"] == "cover":
            scale_vf = ("scale=1920:1080:force_original_aspect_ratio=increase,"
                        "crop=1920:1080,fps=30,format=yuv420p")
        else:
            scale_vf = ("scale=1920:1080:force_original_aspect_ratio=decrease,"
                        f"pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color={PAD_COLOR},"
                        "fps=30,format=yuv420p")
        enc = ["-an", "-c:v", "h264_nvenc", "-preset", "p4", "-cq", "20",
               "-frames:v", str(render_frames), str(part)]
        if vis.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            cmd = [FFMPEG, "-y", "-loop", "1", "-t", f"{dur:.3f}", "-i", str(vis),
                   "-vf", scale_vf, *enc]
        else:
            vd = float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(vis)],
                check=True, capture_output=True, text=True).stdout.strip())
            if "sequence" in beat["visual"]["kind"] and abs(vd - dur) > 0.25:
                sys.exit(
                    f"sequence visual {vis.name} is {vd:.1f}s for a {dur:.1f}s beat; "
                    "build the sequence to the beat so every declared subject appears"
                )
            if vd >= dur:
                cmd = [FFMPEG, "-y", "-t", f"{dur:.3f}", "-i", str(vis),
                       "-vf", scale_vf, *enc]
            elif beat["visual"]["kind"] == "news":
                sys.exit(
                    f"news visual {vis.name} is {vd:.1f}s for a {dur:.1f}s beat; "
                    "use a still or capture the full beat instead of looping an entrance/exit animation"
                )
            elif dur > 2 * vd:
                log(f"  WARN {vis.name} {vd:.1f}s < half of {dur:.1f}s -> loop restart visible")
                cmd = [FFMPEG, "-y", "-stream_loop", "-1", "-t", f"{dur:.3f}",
                       "-i", str(vis), "-vf", scale_vf, *enc]
            else:
                tail = min(dur - vd + 0.5, vd)
                cmd = [FFMPEG, "-y", "-i", str(vis), "-sseof", f"-{tail:.3f}",
                       "-i", str(vis), "-filter_complex",
                       f"[1:v]reverse[r];[0:v][r]concat=n=2:v=1,{scale_vf}[v]",
                       "-map", "[v]", "-t", f"{dur:.3f}", *enc]
        subprocess.run(cmd, check=True, capture_output=True)
        parts.append(part)
    vo = build / "vo-full-mastered.wav"
    if not vo.is_file():
        vo = build / "vo-full.wav"
    log("crossfading beats + muxing VO; YouTube captions remain platform-generated...")
    cmd = [FFMPEG, "-y"]
    for p in parts:
        cmd += ["-i", str(p)]
    cmd += ["-i", str(vo)]
    if len(parts) > 1:
        fade_s = TRANSITION_FRAMES / VIDEO_FPS
        chain, prev, offset = [], "[0:v]", 0.0
        for i in range(1, len(parts)):
            offset += frame_counts[i - 1] / VIDEO_FPS
            chain.append(f"{prev}[{i}:v]xfade=transition=fade:duration={fade_s:.3f}:offset={offset:.3f}[x{i}]")
            prev = f"[x{i}]"
        cmd += ["-filter_complex", ";".join(chain), "-map", prev, "-map", f"{len(parts)}:a"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "h264_nvenc", "-preset", "p5", "-cq", "19",
            "-c:a", "aac", "-b:a", "192k", "-shortest", str(build / "master.mp4")]
    subprocess.run(cmd, check=True, cwd=build, capture_output=True)
    log(f"master: {build / 'master.mp4'}")


def stage_shorts(prod: Path):
    clipper = HUB / "studio-kit" / "clipper"
    master = prod / "build" / "master.mp4"  # clean long-form; vertical applies its own caption rule
    if not master.exists():
        sys.exit("run --stage assemble first")
    if not (clipper / "node_modules").exists():
        log("installing clipper deps (one-time)...")
        subprocess.run(["npm", "install"], cwd=clipper, check=True, shell=True)
    log("clipper: highlight pick + 9:16 reframe...")
    env = dict(os.environ)
    env.setdefault("CLIP_LAYOUT", "fit")  # chart-dominant masters lose the price axis under center crop
    env.setdefault("CLIP_CLEAN_VERTICAL", "1")  # caption-free twin satisfies YouTube's native-caption gate
    subprocess.run(["node", "clip.js", str(master), "--reframe",
                    "--srt", str(prod / "build" / "captions.srt")],
                   cwd=clipper, check=True, shell=True, env=env)
    log(f"shorts in {clipper / 'output'}")


STAGES = {"vo": stage_vo, "captions": stage_captions, "assemble": stage_assemble, "shorts": stage_shorts}


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("production", help="production folder (contains vo.txt)")
    p.add_argument("--stage", default="all", choices=[*STAGES, "all"])
    p.add_argument("--ref", "--operator-ref", dest="operator_ref", default=str(OPERATOR_REF),
                   help="operator reference audio (default: productions/_voice/operator-clean.wav)")
    p.add_argument("--apollo-ref", help="operator-approved Apollo reference audio")
    args = p.parse_args()
    prod = Path(args.production).resolve()
    if not (prod / "vo.txt").exists():
        sys.exit(f"no vo.txt in {prod}")
    try:
        require_production_approval(prod)
    except ValueError as error:
        sys.exit(f"production approval gate blocked production: {error}")
    order = list(STAGES) if args.stage == "all" else [args.stage]
    for name in order:
        log(f"=== stage: {name} ===")
        STAGES[name](prod, args.operator_ref, args.apollo_ref) if name == "vo" else STAGES[name](prod)


if __name__ == "__main__":
    main()
