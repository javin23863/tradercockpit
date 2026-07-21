#!/usr/bin/env python3
"""visual_qa.py -- geometry gate on the RENDERED pixels of the vertical cuts.

Why this exists: editorial-gate.json says in its own doesNotProve list that the
gate chain cannot prove "the visual declaration matches the pixels". Nothing
looked at a frame before posting, and captions shipped sitting on top of the
chart. This gate looks.

What it does, per vertical clip:
  1. reads the clip's sidecar .srt (already rebased to 0 by the clipper) and
     samples a frame at each CAPTION ONSET, plus a few evenly-spaced frames.
  2. measures the caption bounding box from the pixels by differencing the
     burned clip against its caption-free twin (*.vertical.clean.mp4, produced
     by CLIP_CLEAN_VERTICAL=1). Same -ss/-t/-vf on both, so every pixel that
     differs is caption ink. No OCR, no assumed style constants.
  3. hard-fails on objective geometry: safe-zone breach, out-of-frame, and
     caption sitting on a high-detail (chart/graphic) region.
  4. tiles the sampled frames into one contact sheet for the morning review.
  5. hard-fails if ffprobe finds no audio stream or FFmpeg finds the whole track silent.
  6. warns on persistent corner edge clusters that may be a foreign watermark.

It also checks TikTok assets declared in productions/*/social-batch*.json are
native, manifest-backed 9:16 vertical renders. That checks the selection input;
it cannot prove the later uploader used that same file.

Usage:
    python tools/visual_qa.py productions/<vid>
    python tools/visual_qa.py productions/<vid> --clips <dir>   # default studio-kit/clipper/output
    python tools/visual_qa.py --selftest
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
HUB = HERE.parent
FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"
CLIPS_DEFAULT = HUB / "studio-kit" / "clipper" / "output"

# Analysis is done on a downscaled grayscale plane; 1/4 of 1080x1920 keeps caption
# strokes visible in the difference while staying cheap in pure Python (no numpy).
AW, AH = 270, 480
# 8-bit delta that counts as caption ink. Burning subtitles changes x264's rate
# control for the WHOLE frame, so the two encodes differ slightly everywhere; a low
# threshold picks that codec noise up in detailed regions and inflates the bbox to
# the full frame. Caption ink is white-with-black-outline over the plate, i.e. a
# very large delta, so a high threshold separates it cleanly from re-encode drift.
DIFF_THRESHOLD = 70
MIN_INK_PER_LINE = 2     # a row/column needs this many ink pixels to enter the bbox
CELL = 15                # edge-density cell size on the analysis plane (=60px full-res)
# Cell is a "graphic region" at this multiple of the lower-quartile baseline.
# 1.6 was inert: on a white TradingView plate the lower quartile is ~0.88, so quiet*1.6 = 1.4
# and the absolute floor below (6.0) was what actually bound. Measured on the clip-001 crop
# probe, the ratios under the caption are sharply bimodal:
#   ~12.2 - 14.1  faint chart furniture (gridlines, the dotted level line) — nothing occluded
#   ~40.1 - 40.8  real candle bodies under the text — a genuine collision
#   ~51.7         densest chart core anywhere in the frame (the sensitivity ceiling)
# 22 sits in that gap: 1.56x above the furniture cluster, 1.85x below real candles. What it
# costs: any graphic quieter than ~22x baseline no longer trips the gate, so a caption over
# sparse detail (a lone trendline, thin axis labels, a faint watermark) now passes unflagged.
# Candles, dense text and news cards all sit at 30x+ and are still caught. Do NOT raise past
# ~30 — that is where real candle bodies start slipping through.
BUSY_FACTOR = 22.0
MAX_FRAMES = 24          # contact-sheet ceiling; onsets are sampled first

# Watermark detection deliberately runs below BUSY_FACTOR and only WARNs. It
# looks for a compact two-dimensional edge cluster repeated across frames, while
# masking the native TraderCockpit header (top-left) and handle (bottom-right).
# ponytail: this is not logo recognition. A foreign mark over either native-brand
# mask can be missed; remove the masks and accept noisy warnings if layouts change.
WATERMARK_CELL = 10
WATERMARK_FACTOR = 4.0
WATERMARK_FLOOR = 6.0
WATERMARK_SAMPLES = 5
NATIVE_BRAND_ZONES = (
    (0.0, 0.0, 0.58, 0.12),   # TRADERCOCKPIT header + red descriptor
    (0.0, 0.16, 1.0, 0.21),   # fixed chart-frame top border
    (0.65, 0.90, 1.0, 1.0),   # @thetradercockpit handle
)

# Safe zones. Source: GTM/Social-Media-Library/Platform Publishing Manual.md, "TikTok"
# section: "keep text/faces out of the top ~15% (nav), bottom ~20% (caption + metadata),
# right ~15% (like/comment rail). Center is safe." TikTok is the tightest of the three
# vertical surfaces, so its numbers govern the shared 1080x1920 export (the manual's
# Cross-Platform Conversion section says to design for the union of all three).
SAFE_ZONES = {
    "vertical": {"top": 0.15, "bottom": 0.20, "right": 0.15, "left": 0.0},
    # 16:9 long-form has no platform chrome over the frame. The manual gives no
    # numbers for it, so nothing is hard-failed there beyond frame bounds.
    "landscape": {"top": 0.0, "bottom": 0.0, "right": 0.0, "left": 0.0},
}


def log(msg):
    print(f"[visual_qa] {msg}", flush=True)


# --- pure geometry (self-tested) ---------------------------------------------

def safe_zone_breaches(box, size, zones):
    """box=(x0,y0,x1,y1) exclusive-right/bottom, size=(w,h). -> list of breach strings."""
    x0, y0, x1, y1 = box
    w, h = size
    out = []
    if x0 < 0 or y0 < 0 or x1 > w or y1 > h:
        out.append(f"caption extends outside frame bounds {box} vs {w}x{h}")
    if zones["top"] and y0 < zones["top"] * h:
        out.append(f"caption top y={y0} breaches top {zones['top']:.0%} safe zone (y<{int(zones['top'] * h)})")
    if zones["bottom"] and y1 > (1 - zones["bottom"]) * h:
        out.append(f"caption bottom y={y1} breaches bottom {zones['bottom']:.0%} safe zone (y>{int((1 - zones['bottom']) * h)})")
    if zones["right"] and x1 > (1 - zones["right"]) * w:
        out.append(f"caption right x={x1} breaches right {zones['right']:.0%} safe zone (x>{int((1 - zones['right']) * w)})")
    if zones["left"] and x0 < zones["left"] * w:
        out.append(f"caption left x={x0} breaches left {zones['left']:.0%} safe zone")
    return out


def boxes_overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def edge_cells(gray, w, h, cell):
    """Return [((x0,y0,x1,y1), mean forward-difference gradient), ...]."""
    cells = []
    for cy in range(0, h - 1, cell):
        for cx in range(0, w - 1, cell):
            total = n = 0
            for y in range(cy, min(cy + cell, h - 1)):
                row = y * w
                for x in range(cx, min(cx + cell, w - 1)):
                    p = gray[row + x]
                    total += abs(p - gray[row + x + 1]) + abs(p - gray[row + w + x])
                    n += 1
            if n:
                cells.append(((cx, cy, min(cx + cell, w), min(cy + cell, h)), total / n))
    return cells


def busy_cells(gray, w, h, cell=CELL, factor=BUSY_FACTOR):
    """Edge density per cell -> list of (x0,y0,x1,y1) cells above `factor` x baseline.

    ponytail: forward-difference gradient against a lower-quartile baseline, not a
    real Sobel with a trained threshold. It only has to separate "dense
    chart/candles/text" from "flat or blurred background", and it runs in pure
    Python on a 270x480 plane. It cannot tell a chart from any other detailed
    thing (a busy news card, film grain, a dense logo) — it flags detail, and the
    contact sheet is what settles whether the detail mattered. Upgrade to
    numpy+Sobel, or to scene-plan-declared graphic rects, if false positives bite.
    """
    cells = edge_cells(gray, w, h, cell)
    if not cells:
        return []
    scores = [score for _, score in cells]
    ordered = sorted(scores)
    # lower-quartile baseline, not median: a chart-dominant frame can be busy over
    # half its area, and a median baseline would then call the chart "normal".
    quiet = ordered[len(ordered) // 4]
    floor = max(quiet * factor, 6.0)  # a flat frame must not make noise "busy"
    return [box for box, score in cells if score > floor]


def _inside_normalized(box, normalized, w, h):
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    x0, y0, x1, y1 = normalized
    return x0 * w <= cx <= x1 * w and y0 * h <= cy <= y1 * h


def _two_dimensional_cluster(boxes, cell):
    points = {(box[0] // cell, box[1] // cell) for box in boxes}
    for x, y in points:
        horizontal = (x - 1, y) in points or (x + 1, y) in points
        vertical = (x, y - 1) in points or (x, y + 1) in points
        if horizontal and vertical:
            return True
    return False


def corner_watermark_regions(gray, w, h, cell=WATERMARK_CELL):
    """Return corner names with compact low-threshold edge clusters.

    This is intentionally a heuristic and never a hard failure. Native brand
    zones are masked to avoid warning on every current TraderCockpit render.
    """
    cells = edge_cells(gray, w, h, cell)
    if not cells:
        return []
    ordered = sorted(score for _, score in cells)
    floor = max(ordered[len(ordered) // 4] * WATERMARK_FACTOR, WATERMARK_FLOOR)
    corners = {
        "top-left": (0.03, 0.03, 0.30, 0.20),
        "top-right": (0.70, 0.03, 0.97, 0.20),
        "bottom-left": (0.03, 0.80, 0.30, 0.97),
        "bottom-right": (0.70, 0.80, 0.97, 0.97),
    }
    found = []
    for name, region in corners.items():
        candidates = [
            box for box, score in cells
            if score > floor and _inside_normalized(box, region, w, h)
            and not any(_inside_normalized(box, native, w, h) for native in NATIVE_BRAND_ZONES)
        ]
        if _two_dimensional_cluster(candidates, cell):
            found.append(name)
    return found


def audio_stream_present(probe):
    return any(stream.get("codec_type") == "audio" for stream in probe.get("streams", []))


def entirely_silent(silencedetect_log, duration, tolerance=0.1):
    """True only when one silence interval spans the complete media duration."""
    start = None
    for line in silencedetect_log.splitlines():
        match = re.search(r"silence_start:\s*([0-9.]+)", line)
        if match:
            start = float(match.group(1))
        match = re.search(r"silence_end:\s*([0-9.]+)", line)
        if match and start is not None:
            if start <= tolerance and float(match.group(1)) >= duration - tolerance:
                return True
            start = None
    return False


def ink_bbox(diff, w, h, threshold=DIFF_THRESHOLD, min_per_line=MIN_INK_PER_LINE):
    """Bounding box of pixels where the burned frame differs from the clean twin.

    A row or column needs `min_per_line` ink pixels to count, so a single stray
    macroblock cannot stretch the box across the frame.
    """
    rows, cols = [0] * h, [0] * w
    for y in range(h):
        base = y * w
        for x in range(w):
            if diff[base + x] >= threshold:
                rows[y] += 1
                cols[x] += 1
    ys = [y for y, n in enumerate(rows) if n >= min_per_line]
    xs = [x for x, n in enumerate(cols) if n >= min_per_line]
    return (xs[0], ys[0], xs[-1] + 1, ys[-1] + 1) if xs and ys else None


def scale_box(box, from_size, to_size):
    fw, fh = from_size
    tw, th = to_size
    return (int(box[0] * tw / fw), int(box[1] * th / fh),
            min(tw, -(-box[2] * tw // fw)), min(th, -(-box[3] * th // fh)))


# --- ffmpeg ------------------------------------------------------------------

def probe_size(video):
    out = subprocess.run(
        [FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0:s=x", str(video)],
        check=True, capture_output=True, text=True).stdout.strip()
    w, h = out.split("x")[:2]
    return int(w), int(h)


def gray_frame(video, t):
    """One frame at time t as a raw AW x AH grayscale plane (bytes)."""
    proc = subprocess.run(
        [FFMPEG, "-v", "error", "-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1",
         "-vf", f"scale={AW}:{AH}", "-c:v", "png", "-f", "image2pipe", "-"],
        check=True, capture_output=True)
    if not proc.stdout:
        return None
    with Image.open(io.BytesIO(proc.stdout)) as image:
        return image.convert("L").tobytes()


def contact_sheet(video, times, out_path, columns=4):
    """Tile the sampled frames into one reviewable PNG (ffmpeg tile filter)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.parent / "_frames"
    tmp.mkdir(exist_ok=True)
    for old in tmp.glob("f-*.png"):
        old.unlink()
    for i, t in enumerate(times):
        subprocess.run(
            [FFMPEG, "-y", "-v", "error", "-ss", f"{t:.3f}", "-i", str(video),
             "-frames:v", "1", "-vf", "scale=270:-2", str(tmp / f"f-{i:03}.png")],
            check=True, capture_output=True)
    rows = -(-len(times) // columns)
    subprocess.run(
        [FFMPEG, "-y", "-v", "error", "-framerate", "1", "-i", str(tmp / "f-%03d.png"),
         "-vf", f"tile={columns}x{rows}:padding=6:margin=6:color=0x202020",
         "-frames:v", "1", str(out_path)],
        check=True, capture_output=True)
    for old in tmp.glob("f-*.png"):
        old.unlink()
    tmp.rmdir()
    return out_path


# --- srt ---------------------------------------------------------------------

TS_RE = re.compile(r"(\d\d):(\d\d):(\d\d)[,.](\d\d\d)\s*-->")


def caption_onsets(srt_path):
    out = []
    for line in Path(srt_path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = TS_RE.match(line.strip())
        if m:
            h, mi, s, ms = (int(g) for g in m.groups())
            out.append(h * 3600 + mi * 60 + s + ms / 1000)
    return out


def sample_times(onsets, duration, extra=4):
    """Caption onsets first (+0.15s so the cue is actually drawn), then filler."""
    times = [min(t + 0.15, max(duration - 0.05, 0)) for t in onsets]
    times += [duration * (i + 1) / (extra + 1) for i in range(extra)]
    times = sorted({round(t, 2) for t in times if 0 <= t < duration})
    return times[:MAX_FRAMES]


# --- gate --------------------------------------------------------------------

def check_audio(video):
    """-> (hard_failures, warnings, result) for stream presence and full-track silence."""
    hard, warns = [], []
    result = {"clip": Path(video).name, "audioStream": False, "pureSilence": None}
    try:
        probe = json.loads(subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "stream=codec_type:format=duration",
             "-of", "json", str(video)],
            check=True, capture_output=True, text=True).stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as error:
        hard.append({"clip": Path(video).name, "problem": f"audio stream could not be verified: {error}"})
        return hard, warns, result

    result["audioStream"] = audio_stream_present(probe)
    if not result["audioStream"]:
        hard.append({"clip": Path(video).name, "problem": "no audio stream"})
        return hard, warns, result

    try:
        duration = float(probe.get("format", {}).get("duration") or 0)
    except (TypeError, ValueError) as error:
        hard.append({"clip": Path(video).name, "problem": f"audio duration could not be verified: {error}"})
        return hard, warns, result
    try:
        scan = subprocess.run(
            [FFMPEG, "-hide_banner", "-nostats", "-i", str(video), "-map", "0:a:0",
             "-af", "silencedetect=noise=-50dB:d=0.1", "-f", "null", "-"],
            check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as error:
        hard.append({"clip": Path(video).name,
                     "problem": f"audio silence could not be verified: {error}"})
        return hard, warns, result

    result["pureSilence"] = entirely_silent(scan.stderr, duration)
    if result["pureSilence"]:
        hard.append({"clip": Path(video).name, "problem": "audio stream is pure silence (-50dB threshold)"})
    return hard, warns, result


def scan_corner_watermarks(video, duration):
    times = sample_times([], duration, extra=WATERMARK_SAMPLES)
    frames = []
    errors = []
    for t in times:
        try:
            gray = gray_frame(video, t)
        except subprocess.CalledProcessError as error:
            errors.append(f"{t:.2f}s: {error}")
            continue
        if gray:
            regions = corner_watermark_regions(gray, AW, AH)
            if regions:
                frames.append({"t": t, "corners": regions})
    return {
        "clip": Path(video).name,
        "source": str(video),
        "framesSampled": len(times) - len(errors),
        "framesFlagged": len(frames),
        "flagged": bool(times) and len(frames) >= min(2, len(times)),
        "detections": frames,
        "errors": errors,
        "risk": "HEURISTIC WARN only: corner edge density can false-positive on graphics and miss faint, moving, or native-brand-overlapping watermarks",
    }


def _render_manifest_for(asset):
    manifest = asset.parent / "manifest.json"
    return manifest if manifest.is_file() else None


def check_tiktok_selections(production):
    """Audit social-batch TikTok inputs without claiming uploader-time enforcement."""
    hard, warns, results = [], [], []
    batches = sorted(Path(production).glob("social-batch*.json"))
    for batch in batches:
        try:
            items = json.loads(batch.read_text(encoding="utf-8")).get("items", [])
        except (OSError, json.JSONDecodeError) as error:
            warns.append(f"{batch.name}: TikTok selection manifest unreadable: {error}")
            continue
        for item in items:
            if item.get("channel") != "tiktok":
                continue
            selected = {"batch": batch.name, "id": item.get("id"), "asset": item.get("asset"),
                        "status": "PASS", "renderManifest": None}
            problems = []
            value = item.get("asset")
            if not isinstance(value, str) or not value:
                problems.append("TikTok asset path is missing")
                asset = None
            else:
                asset = (HUB / value).resolve()
                try:
                    asset.relative_to(HUB)
                except ValueError:
                    problems.append("TikTok asset is outside the repository")
                    asset = None
            if asset:
                if not asset.is_file():
                    problems.append("TikTok asset does not exist")

            manifest = _render_manifest_for(asset) if asset and asset.is_file() else None
            if asset and asset.is_file():
                if not re.fullmatch(r"clip-\d+-.+\.vertical\.mp4", asset.name):
                    problems.append("TikTok asset is not a native *.vertical.mp4 render")
                width, height = probe_size(asset)
                selected["size"] = f"{width}x{height}"
                if width * 16 != height * 9:
                    problems.append(f"TikTok asset is not exact 9:16 ({width}x{height})")
            if not manifest:
                problems.append("TikTok asset has no adjacent clipper manifest; native-render provenance is unproved")
            else:
                selected["renderManifest"] = str(manifest.relative_to(HUB))
                try:
                    provenance = json.loads(manifest.read_text(encoding="utf-8"))
                    match = re.fullmatch(r"clip-\d+-(.+)\.vertical\.mp4", asset.name)
                    labels = {segment.get("label") for segment in provenance.get("segments", [])}
                    if not match or match.group(1) not in labels:
                        problems.append("TikTok asset name is not present in its clipper manifest")
                    source = Path(provenance.get("source", ""))
                    if source and not source.is_absolute():
                        source = HUB / source
                    if not source.is_file():
                        problems.append("TikTok clipper manifest source is missing")
                except (OSError, TypeError, json.JSONDecodeError) as error:
                    problems.append(f"TikTok clipper manifest unreadable: {error}")

            if problems:
                selected["status"] = "BLOCK"
                for problem in problems:
                    hard.append({"clip": value or "n/a", "problem": problem})
            results.append(selected)
    if not results:
        warns.append("no TikTok item found in social-batch*.json; clean-master selection was not checked")
    return hard, warns, results


def check_clip(burned, clean, srt, zones):
    """-> (hard_failures, warnings, sampled_times)"""
    hard, warns = [], []
    w, h = probe_size(burned)
    duration = float(subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
         str(burned)], check=True, capture_output=True, text=True).stdout.strip())
    onsets = caption_onsets(srt) if Path(srt).is_file() else []
    if not onsets:
        warns.append(f"{burned.name}: no caption timings found ({Path(srt).name}); "
                     "sampled evenly instead of at caption onsets")
    times = sample_times(onsets, duration)

    if not clean or not Path(clean).is_file():
        warns.append(f"{burned.name}: no caption-free twin ({Path(clean).name if clean else 'n/a'}); "
                     "caption geometry NOT measured. Re-render with CLIP_CLEAN_VERTICAL=1.")
        return hard, warns, times

    for t in times:
        burn = gray_frame(burned, t)
        base = gray_frame(clean, t)
        if not burn or not base:
            warns.append(f"{burned.name} @{t:.2f}s: frame extraction returned no data")
            continue
        diff = bytes(abs(a - b) for a, b in zip(burn, base))
        box = ink_bbox(diff, AW, AH)
        if box is None:
            continue  # no caption drawn at this instant
        full = scale_box(box, (AW, AH), (w, h))
        for breach in safe_zone_breaches(full, (w, h), zones):
            hard.append({"clip": burned.name, "t": t, "box": full, "problem": breach})
        hit = [c for c in busy_cells(base, AW, AH) if boxes_overlap(box, c)]
        if hit:
            hard.append({
                "clip": burned.name, "t": t, "box": full,
                "problem": f"caption overlaps {len(hit)} high-detail cell(s) "
                           f"(chart/graphic region) in the caption-free plate",
            })
    return hard, warns, times


def gate(production, clips_dir=None):
    production = Path(production).resolve()
    clips_dir = Path(clips_dir or CLIPS_DEFAULT)
    out_dir = production / "build" / "visual-qa"
    out_dir.mkdir(parents=True, exist_ok=True)

    hard, warns, sheets = [], [], []
    audio_checks, watermark_checks = [], []
    verticals = sorted(p for p in clips_dir.glob("*.vertical.mp4")
                       if not p.name.endswith(".vertical.clean.mp4"))
    if not verticals:
        warns.append(f"no *.vertical.mp4 in {clips_dir}; nothing rendered was inspected")

    for burned in verticals:
        clean = burned.with_name(burned.name.replace(".vertical.mp4", ".vertical.clean.mp4"))
        srt = burned.with_name(burned.name.replace(".vertical.mp4", ".srt"))
        log(f"checking {burned.name}")
        clip_hard, clip_warns, times = check_clip(burned, clean, srt, SAFE_ZONES["vertical"])
        hard += clip_hard
        warns += clip_warns
        audio_hard, audio_warns, audio_result = check_audio(burned)
        hard += audio_hard
        warns += audio_warns
        audio_checks.append(audio_result)
        duration = float(subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
             str(burned)], check=True, capture_output=True, text=True).stdout.strip())
        watermark_source = clean if clean.is_file() else burned
        watermark = scan_corner_watermarks(watermark_source, duration)
        watermark["clip"] = burned.name
        watermark_checks.append(watermark)
        if watermark["flagged"]:
            corners = sorted({corner for frame in watermark["detections"] for corner in frame["corners"]})
            warns.append(
                f"{burned.name}: possible corner watermark/logo in "
                f"{watermark['framesFlagged']}/{watermark['framesSampled']} sampled frame(s) "
                f"({', '.join(corners)}). HEURISTIC WARN; inspect for a foreign TikTok/CapCut mark."
            )
        for error in watermark["errors"]:
            warns.append(f"{burned.name}: watermark frame extraction failed at {error}")
        if times:
            sheet = out_dir / f"{burned.name.replace('.vertical.mp4', '')}-contact-sheet.png"
            try:
                sheets.append(str(contact_sheet(burned, times, sheet)))
            except subprocess.CalledProcessError as error:
                warns.append(f"{burned.name}: contact sheet failed: {error}")

    tiktok_hard, tiktok_warns, tiktok_selections = check_tiktok_selections(production)
    hard += tiktok_hard
    warns += tiktok_warns

    report = {
        "status": "BLOCK" if hard else "PASS",  # fail-closed, same convention as claims_gate
        "clipsChecked": len(verticals),
        "safeZones": {"surface": "vertical 1080x1920 (TikTok governs)", **SAFE_ZONES["vertical"],
                      "source": "GTM/Social-Media-Library/Platform Publishing Manual.md — TikTok safe zones"},
        "hardFail": hard,
        "warnings": warns,
        "contactSheets": sheets,
        "audioChecks": audio_checks,
        "watermarkChecks": watermark_checks,
        "tiktokSelections": tiktok_selections,
        "checks": [
            "caption bbox measured from pixels (burned frame vs caption-free twin)",
            "platform safe-zone breach (top/bottom/right)",
            "caption outside frame bounds",
            "caption over high-edge-density (chart/graphic) region",
            "audio stream exists and complete track is not pure silence",
            "persistent corner watermark/logo edge clusters (HEURISTIC WARN only)",
            "manifest-selected TikTok asset is a local native exact-9:16 vertical render",
        ],
        "doesNotProve": [
            "caption legibility, font size, or blockiness — aesthetic quality is not machine-checked here",
            "that the caption text is correct or well-timed",
            "colour contrast or readability against the plate",
            "editorial quality, framing taste, or whether a human would ship it",
            "anything about clips with no caption-free twin (geometry is unmeasured there)",
            "watermark identity: there is no logo OCR; the corner-edge heuristic can false-positive or miss marks overlapping native brand masks",
            "that tools/publish.py later dispatched the TikTok asset checked here, or that the file was not replaced after this report",
            "audio quality, loudness, intelligibility, synchronization, or whether short silent passages are editorially acceptable",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }
    (production / "build" / "visual-qa.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    log(f"{report['status']} — {len(hard)} hard fail(s), {len(warns)} warning(s)")
    for f in hard[:20]:
        where = f" @{f['t']:.2f}s box={f['box']}" if "t" in f else ""
        log(f"  FAIL {f['clip']}{where}: {f['problem']}")
    for w in warns[:20]:
        log(f"  WARN {w}")
    log(f"  report: {production / 'build' / 'visual-qa.json'}")
    return report


def selftest():
    zones = SAFE_ZONES["vertical"]
    size = (1080, 1920)
    # clean: centered box inside top15/bottom20/right15
    assert safe_zone_breaches((100, 400, 800, 500), size, zones) == []
    # bottom safe-zone breach (this is the real shipped defect: MarginV=24 -> y~1896)
    b = safe_zone_breaches((100, 1850, 900, 1900), size, zones)
    assert any("bottom" in x for x in b), b
    # top and right breaches
    assert any("top" in x for x in safe_zone_breaches((10, 50, 200, 200), size, zones))
    assert any("right" in x for x in safe_zone_breaches((900, 500, 1070, 600), size, zones))
    # out of frame bounds
    assert any("outside frame" in x for x in safe_zone_breaches((-5, 400, 500, 500), size, zones))
    assert any("outside frame" in x for x in safe_zone_breaches((600, 400, 1200, 500), size, zones))
    # landscape zones only police frame bounds
    assert safe_zone_breaches((0, 1000, 1900, 1079), (1920, 1080), SAFE_ZONES["landscape"]) == []

    assert boxes_overlap((0, 0, 10, 10), (5, 5, 15, 15))
    assert not boxes_overlap((0, 0, 10, 10), (10, 0, 20, 10))   # touching edges is not overlap
    assert not boxes_overlap((0, 0, 10, 10), (0, 20, 10, 30))

    # ink bbox on a synthetic plane: a 4x2 blob at (3,1)
    w, h = 12, 8
    plane = bytearray(w * h)
    for y in range(1, 3):
        for x in range(3, 7):
            plane[y * w + x] = 200
    assert ink_bbox(bytes(plane), w, h) == (3, 1, 7, 3)
    assert ink_bbox(bytes(w * h), w, h) is None
    assert scale_box((3, 1, 7, 3), (12, 8), (1080, 1920)) == (270, 240, 630, 720)

    # busy_cells: flat plane has none; a striped half is detected and overlaps a caption there
    flat = bytes(60 * 60)
    assert busy_cells(flat, 60, 60, cell=15) == []
    striped = bytearray(60 * 60)
    for y in range(30):
        for x in range(60):
            striped[y * 60 + x] = 255 * (x % 2)
    cells = busy_cells(bytes(striped), 60, 60, cell=15)
    assert cells and all(c[1] < 30 for c in cells), cells
    assert any(boxes_overlap((0, 0, 60, 20), c) for c in cells)
    assert not any(boxes_overlap((0, 45, 60, 60), c) for c in cells)

    assert sample_times([0.0, 2.0], 10.0, extra=2) == [0.15, 2.15, 3.33, 6.67]
    assert sample_times([], 4.0, extra=1) == [2.0]

    assert audio_stream_present({"streams": [{"codec_type": "video"}, {"codec_type": "audio"}]})
    assert not audio_stream_present({"streams": [{"codec_type": "video"}]})
    assert entirely_silent("silence_start: 0\nsilence_end: 10.0 | silence_duration: 10.0", 10.0)
    assert not entirely_silent("silence_start: 0\nsilence_end: 1.0 | silence_duration: 1.0", 10.0)

    faint = bytearray(60 * 100)
    for y in range(82, 92):
        for x in range(7, 17):
            faint[y * 60 + x] = 20 if (x + y) % 2 else 0
    assert corner_watermark_regions(bytes(faint), 60, 100, cell=5) == ["bottom-left"]
    assert corner_watermark_regions(bytes(60 * 100), 60, 100, cell=5) == []

    print("visual_qa self-test: 25/25 PASS")
    print("audio stream vectors: present=True, missing=False; silence span=True, partial=False")
    print("watermark vectors: faint corner cluster=True, flat frame=False")


def watermark_benchmark(clips_dir=None):
    clips_dir = Path(clips_dir or CLIPS_DEFAULT)
    results = []
    for burned in sorted(p for p in clips_dir.glob("*.vertical.mp4")
                         if not p.name.endswith(".vertical.clean.mp4")):
        clean = burned.with_name(burned.name.replace(".vertical.mp4", ".vertical.clean.mp4"))
        source = clean if clean.is_file() else burned
        duration = float(subprocess.run(
            [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
             str(burned)], check=True, capture_output=True, text=True).stdout.strip())
        result = scan_corner_watermarks(source, duration)
        result["clip"] = burned.name
        results.append(result)
    print(json.dumps(results, indent=2))
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("production", nargs="?")
    parser.add_argument("--clips", help=f"rendered clip folder (default {CLIPS_DEFAULT})")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--watermark-benchmark", action="store_true",
                        help="read-only corner-watermark scan; writes no production artifacts")
    args = parser.parse_args(argv)
    if args.selftest:
        selftest()
        return 0
    if args.watermark_benchmark:
        watermark_benchmark(args.clips)
        return 0
    if not args.production:
        parser.error("production folder is required")
    return 1 if gate(args.production, args.clips)["status"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
