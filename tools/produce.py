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
sys.path.insert(0, str(Path(__file__).resolve().parent))
from encoder import encoder_args  # noqa: E402

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

# Sound layer (operator-approved on daily-2026-07-20 A/B, 2026-07-21): music bed
# ~21.5 dB under the voice ("subtle ambiance"), whoosh on each section transition,
# one bass impact under the final (closing-thesis) section.
MUSIC_DIR = HUB / "music_library"     # operator-curated royalty-free tracks; first file (sorted) is the bed
SFX_DIR = HUB / "OpenMontage" / ".agents" / "skills" / "hyperframes-media" / "assets" / "sfx"
MUSIC_UNDER_VO_DB = 21.5
WHOOSH_DB = -12.0
IMPACT_DB = -14.0
SFX_LEAD_S = 0.2                      # whoosh starts just before the cut so it peaks on it
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}

# Voice mastering — the chain studio-kit/pipeline/MONTAGE-CRAFT.md documented and nothing ran.
# Chatterbox emits ~-17 LUFS raw with no EQ or dynamics; stage_assemble has always preferred
# build/vo-full-mastered.wav, but until now no tool wrote it.
VO_MASTER_LUFS = -16.0    # under DELIVERY so the bed lands the MIX on target, not over it
DELIVERY_LUFS = -14.0     # YouTube/IG playback target: quieter and they turn us up, noise and all
VO_MASTER_FILTER = (
    "highpass=f=80,"
    "equalizer=f=500:t=q:w=1.2:g=-2,"       # pull the mud
    "equalizer=f=3500:t=q:w=1.0:g=2.5,"     # presence, so consonants survive a phone speaker
    "deesser=i=0.35,"
    "acompressor=threshold=-18dB:ratio=3:attack=5:release=15,"
    f"loudnorm=I={VO_MASTER_LUFS}:TP=-1.5:LRA=11"
)
DELIVERY_LOUDNORM = f"loudnorm=I={DELIVERY_LUFS}:TP=-1.5:LRA=11"
# Delivery audio spec. Chatterbox runs at 24 kHz; without this the master inherits it and
# `-b:a 192k` silently collapses to ~100 kbps behind a 12 kHz ceiling (measured on
# daily-2026-07-23). The bed and SFX get downsampled into the same ceiling.
MASTER_AR = "48000"
MASTER_AC = "2"


def log(msg):
    print(f"[produce] {msg}", flush=True)


def measure_lufs(path):
    """Integrated LUFS via ffmpeg ebur128 (last summary 'I:' line)."""
    err = subprocess.run(
        [FFMPEG, "-i", str(path), "-af", "ebur128", "-f", "null", os.devnull],
        capture_output=True, text=True).stderr
    return float(re.findall(r"I:\s+(-?[\d.]+)\s+LUFS", err)[-1])


def probe_duration(path):
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True).stdout.strip())


def pick_music():
    if not MUSIC_DIR.is_dir():
        return None
    tracks = sorted(p for p in MUSIC_DIR.iterdir()
                    if p.is_file() and p.suffix.lower() in AUDIO_EXTS)
    return tracks[0] if tracks else None


def section_starts(timeline):
    """Start time of every section after the first (beat ids are '<NN><letter>')."""
    starts, prev = [], None
    for beat in timeline:
        num = re.match(r"\d+", beat["id"]).group(0)
        if prev is not None and num != prev:
            starts.append(float(beat["start"]))
        prev = num
    return starts


def build_sound_filter(vo_idx, total_s, boundaries, music_idx=None, music_gain_db=None,
                       whoosh_idx=None, impact_idx=None):
    """Audio filter_complex mixing VO + music bed + section SFX into [aout].

    Always returns a chain: with nothing to layer this is VO -> limiter -> delivery loudnorm.
    It used to return None there, which routed bare VO straight to the encoder and skipped
    the limiter and any loudness target at all.
    Whoosh lands on every section transition except the last, which gets the impact.
    """
    chains, mix = [], [f"[{vo_idx}:a]"]
    if music_idx is not None:
        chains.append(
            f"[{music_idx}:a]atrim=0:{total_s:.3f},volume={music_gain_db:.1f}dB,"
            f"afade=t=in:d=2,afade=t=out:st={max(total_s - 4, 0):.3f}:d=4[mus]")
        mix.append("[mus]")
    whooshes = boundaries[:-1] if impact_idx is not None else boundaries
    if whoosh_idx is not None and whooshes:
        split = "".join(f"[wsp{i}]" for i in range(len(whooshes)))
        chains.append(f"[{whoosh_idx}:a]volume={WHOOSH_DB:.1f}dB,asplit={len(whooshes)}{split}")
        for i, t in enumerate(whooshes):
            ms = max(round((t - SFX_LEAD_S) * 1000), 0)
            chains.append(f"[wsp{i}]adelay={ms}|{ms}[w{i}]")
            mix.append(f"[w{i}]")
    if impact_idx is not None and boundaries:
        ms = round(boundaries[-1] * 1000)
        chains.append(f"[{impact_idx}:a]volume={IMPACT_DB:.1f}dB,adelay={ms}|{ms}[imp]")
        mix.append("[imp]")
    # amix only when there is something to mix — amix=inputs=1 is a no-op that still costs a pass
    head = (f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0," if len(mix) > 1
            else f"{mix[0]}")
    chains.append(f"{head}alimiter=limit=0.97,{DELIVERY_LOUDNORM}[aout]")
    return ";".join(chains)


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
    except (ImportError, RuntimeError, OSError) as exc:
        # Windows Application Control can block PyAV's native DLL, and a CUDA-built
        # faster-whisper raises RuntimeError (not ImportError) when cuBLAS is absent —
        # "Library cublas64_12.dll is not found", which crashed the 2026-07-26 render
        # AFTER the GPU narration had already succeeded. Catch the whole family: the
        # narration is generated from the exact approved script, so script-locked cues
        # are the better artifact anyway. Free ASR can burn words on screen that the
        # operator never approved; vo.txt is the exact-hash-approved text.
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


def stage_master(prod: Path):
    """VO mastering: build/vo-full.wav -> build/vo-full-mastered.wav, which assemble prefers."""
    build = prod / "build"
    raw = build / "vo-full.wav"
    if not raw.is_file():
        sys.exit("run --stage vo first")
    out = build / "vo-full-mastered.wav"
    subprocess.run([FFMPEG, "-y", "-i", str(raw), "-af", VO_MASTER_FILTER,
                    "-ar", MASTER_AR, "-c:a", "pcm_s16le", str(out)],
                   check=True, capture_output=True)
    # nothing in VO_MASTER_FILTER changes length; if an edit ever adds something that does,
    # every beat boundary downstream silently desyncs, so fail here instead of at the render
    drift = abs(probe_duration(out) - probe_duration(raw))
    if drift > 0.05:
        sys.exit(f"mastering moved VO duration by {drift:.3f}s; refusing to desync the timeline")
    log(f"vo mastered: {measure_lufs(raw):.1f} -> {measure_lufs(out):.1f} LUFS "
        f"(target {VO_MASTER_LUFS})")


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
        enc = ["-an", *encoder_args(20, "p4"),
               "-frames:v", str(render_frames), str(part)]
        if vis.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            cmd = [FFMPEG, "-y", "-loop", "1", "-t", f"{dur:.3f}", "-i", str(vis),
                   "-vf", scale_vf, *enc]
        else:
            vd = probe_duration(vis)
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

    total_s = sum(frame_counts) / VIDEO_FPS
    boundaries = section_starts(timeline)
    vo_idx = len(parts)
    next_idx = vo_idx + 1
    music_idx = music_gain = whoosh_idx = impact_idx = None
    music = pick_music()
    if music:
        music_gain = (measure_lufs(vo) - MUSIC_UNDER_VO_DB) - measure_lufs(music)
        cmd += ["-stream_loop", "-1", "-i", str(music)]
        music_idx, next_idx = next_idx, next_idx + 1
        log(f"music bed: {music.name} at {music_gain:+.1f} dB")
    else:
        log("music bed: none (music_library/ empty)")
    whoosh, impact = SFX_DIR / "whoosh-short.mp3", SFX_DIR / "impact-bass-1.mp3"
    if boundaries and whoosh.is_file():
        cmd += ["-i", str(whoosh)]
        whoosh_idx, next_idx = next_idx, next_idx + 1
    if boundaries and impact.is_file():
        cmd += ["-i", str(impact)]
        impact_idx, next_idx = next_idx, next_idx + 1
    sound = build_sound_filter(vo_idx, total_s, boundaries, music_idx, music_gain,
                               whoosh_idx, impact_idx)
    audio_map = "[aout]"      # build_sound_filter always returns a chain

    filters = []
    if len(parts) > 1:
        fade_s = TRANSITION_FRAMES / VIDEO_FPS
        chain, prev, offset = [], "[0:v]", 0.0
        for i in range(1, len(parts)):
            offset += frame_counts[i - 1] / VIDEO_FPS
            chain.append(f"{prev}[{i}:v]xfade=transition=fade:duration={fade_s:.3f}:offset={offset:.3f}[x{i}]")
            prev = f"[x{i}]"
        filters.append(";".join(chain))
        video_map = prev
    else:
        video_map = "0:v"
    filters.append(sound)
    cmd += ["-filter_complex", ";".join(filters)]
    cmd += ["-map", video_map, "-map", audio_map]
    # yuv420p pin: without it the xfade graph promotes to yuv444p, which local
    # players cannot decode (2026-07-21 playback incident)
    cmd += [*encoder_args(19, "p5"), "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ar", MASTER_AR, "-ac", MASTER_AC,
            "-shortest", str(build / "master.mp4")]
    subprocess.run(cmd, check=True, cwd=build, capture_output=True)
    # What actually reached the mix. Written only after ffmpeg returns 0, so the
    # receipt attests to a master that exists rather than to one we intended: a
    # receipt left behind by a failed run would let a later standalone gate call
    # PASS the previous master, which is the failure this gate exists to stop.
    # audio_layer_gate is fail-closed on this file -- no receipt means it cannot
    # tell a full sound layer from a silently dropped one, so it BLOCKs. Every
    # skip above is silent (pick_music logs; a missing SFX file does not).
    (build / "audio-layer-receipt.json").write_text(json.dumps({
        "music": music.name if music else None,
        "musicGainDb": round(music_gain, 1) if music_gain is not None else None,
        "sectionBoundaries": len(boundaries),
        "sfxDir": str(SFX_DIR),
        "sfxDirPresent": SFX_DIR.is_dir(),
        "whoosh": whoosh.name if whoosh_idx is not None else None,
        "impact": impact.name if impact_idx is not None else None,
        "layered": any(i is not None for i in (music_idx, whoosh_idx, impact_idx)),
    }, indent=1), encoding="utf-8")
    log(f"master: {build / 'master.mp4'}")


def stage_shorts(prod: Path):
    if os.environ.get("CLIP_SKIP_SHORTS") == "1":
        # Derivatives are cut AFTER the long-form is accepted (skill step 7); the unattended
        # runner sets this so a shorts-lane defect can never block the long-form publish.
        log("shorts: skipped (CLIP_SKIP_SHORTS=1 - post-acceptance lane cuts derivatives)")
        return
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


STAGES = {"vo": stage_vo, "captions": stage_captions, "master": stage_master,
          "assemble": stage_assemble, "shorts": stage_shorts}


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
