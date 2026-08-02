#!/usr/bin/env python3
"""Generate HyperFrames scene compositions from a per-episode spec.

WHY A GENERATOR AND NOT 15 HAND-WRITTEN FILES. Every composition defect that has cost this series
a re-render was a property of how the HTML was written, not of what it said:

  * `}, DUR * 0.632)` was invisible to the beat parser while only bare literals were matched, and
    `tl.set(c[0], ..., DUR * c[1])` from a forEach was invisible after that. BOTH TIMES the gate
    "passed" by detecting nothing and place_cutaways saw one enormous empty gap.
  * `retime.py` rescales numeric literals only, so `2.6 + i * 2.6` or `var C3 = 95.0` keeps its
    authored time on a scene whose length changed — that is how scene-windows' third card vanished
    from a master through four clean gates.
  * `font: 700 168px` with no line-height silently overlaps whatever sits below it. Most common
    composition error in the project.
  * Staggered `data-start` values produce dead screen the timeline cannot fix.

Generating removes all four BY CONSTRUCTION. Every tween position is emitted as `DUR * <literal>`
inline at the call site, every clip gets the same full-scene window, and every type rule carries a
line-height. A defect class you cannot express is better than one you check for.

    py tools/build_scenes.py <episode-dir>          # reads artifacts/scenes.json
    py tools/build_scenes.py --demo                 # self-check on a pinned spec
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Keep content away from the canvas edge so typography and charts have a stable safe area.
SAFE_W = 1642

# How long the thumbnail plate is held at full before it drops back to a backdrop. Five seconds
# is the vault's number, not a taste call: `GTM/Social-Media-Library/YouTube Intro & Hook --
# House Reference.md` Step 2 makes "first shot matches the thumbnail" and "inside 5.0s" two
# BLOCKERS, not notes.
PLATE_HOLD_S = 5.0

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "OpenMontage" / "projects"
ACADEMIC_GSAP = (
    ROOT
    / "OpenMontage"
    / ".agents"
    / "skills"
    / "music-to-video"
    / "references"
    / "motion-primitives"
    / "assets"
    / "gsap.min.js"
)


def dur(wav: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(wav)], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f"BLOCK: ffprobe failed on {wav}")
    return round(float(out.stdout.strip()), 3)


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


# NEVER use the `font:` shorthand here. `font: 700 74px/1.14 inherit` is INVALID CSS -- the
# shorthand requires a real font-family as its last component and `inherit` is not one -- so the
# browser drops the WHOLE declaration, size and weight with it, and every element falls back to
# the 16px default. Two full episodes rendered that way on 2026-07-28 before anyone looked at a
# frame: ep03's 74px title measured 16px on the master, `intro_pace` read 2 visual changes in
# 25s instead of 18 because 16px text barely moves a pixel histogram, and the self-check below
# "passed" the whole time because it only looked for the `<size>/<line-height>` pattern.
# Longhand, always. It cannot be silently invalid.
CSS = """
    *{margin:0;padding:0;box-sizing:border-box}
    #root{position:absolute;inset:0;background:#0a0a0b;overflow:hidden;
          font-family:'Inter','Helvetica Neue',Arial,sans-serif;color:#e8e6e2}
    .wrap{position:absolute;left:50%%;transform:translateX(-50%%);width:%(w)dpx}
    /* every rule that sets a large size sets a line-height with it. */
    .title{top:96px;font-weight:700;font-size:74px;line-height:1.14;
           letter-spacing:-.015em;color:#f2efe9;opacity:0}
    .sub{top:196px;font-weight:500;font-size:34px;line-height:1.32;
         letter-spacing:.10em;color:#8c8781;opacity:0}
    .band{top:300px}
    .row{display:flex;gap:34px;justify-content:center;align-items:stretch}
    /* #131315 on a #0a0a0b field is a box you cannot see: the card's own reveal was an
       invisible event and only its text registered, which is why three of the hook's
       beats produced nothing measurable and nothing visible. Lifted enough to read as
       a panel arriving, still dark. */
    /* intro_pace counts a pixel as moved only if it shifts >= 40 grey levels, and needs 26
       such pixels in a 320x180 frame. #0a0a0b -> #1a1a1f is 16 levels, so a card panel's
       arrival qualifies ZERO pixels no matter how large the panel is -- which is why all
       three card bodies were invisible to the meter and nearly so to the eye. This accent
       rule is #c8b98a on near-black: 180 levels, and 180x8px downsamples to ~39 qualifying
       pixels. It is also just a better card -- the panel now announces itself. */
    .card{flex:1;background:#1a1a1f;border:1px solid #3a3a45;border-radius:10px;
          padding:34px 32px 30px;opacity:0}
    .cbar{height:8px;width:180px;background:#c8b98a;border-radius:2px;margin-bottom:26px}
    .lab{font-weight:600;font-size:24px;line-height:1.3;letter-spacing:.13em;
         color:#8f8a84;margin-bottom:18px}
    .val{font-weight:700;font-size:92px;line-height:1.06;letter-spacing:-.02em;color:#f2efe9}
    .val.sm{font-weight:700;font-size:62px;line-height:1.1}
    .note{font-weight:400;font-size:25px;line-height:1.42;color:#9a938c;margin-top:18px}
    .kick{bottom:104px;font-weight:600;font-size:40px;line-height:1.3;letter-spacing:.02em;
          color:#c8b98a;text-align:center;opacity:0}
    .rule{position:absolute;left:50%%;transform:translateX(-50%%);width:%(w)dpx;height:2px;
          background:#3a3a44;opacity:0}
    /* Kling returns 1280x720; without this a clip lays out at intrinsic size in the corner. */
    #root > video{position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover}
    /* THE THUMBNAIL PLATE, ON FRAME ONE. Every other element in this file starts at opacity 0
       and fades in on a beat, so frame 0 of a generated scene is a BLACK FIELD by construction.
       ep03 measured 4.667s and ep04 4.333s before a non-black frame against presentation_gate's
       0.1s bar -- five seconds of nothing at the exact point the vault calls "the biggest
       drop-off in the video" (Intro & Hook House Reference, Step 2). It also silently broke the
       other half of that rule: the first shot is supposed to match the thumbnail in subject,
       composition and primary colours, and black matches nothing.
       So this one is opaque from frame 0 and never fades IN -- it fades DOWN, after the match
       has been held. Same treatment as the thumbnail's own plate so the two read as one image.

       THE GRADE IS BAKED INTO THE PNG, NOT APPLIED IN CSS. The first cut used
       `filter:saturate(.32) contrast(1.18) brightness(.80)` plus a full-frame ::after vignette.
       That is two full-screen compositing layers recomputed every frame in every worker, and
       the render died at 30%% with all five Chrome workers returning "Protocol error
       (Page.captureScreenshot): Unable to capture screenshot". Same look, none of the cost:
         ffmpeg -i plate.png -vf "scale=1920:1080:force_original_aspect_ratio=increase,
                crop=1920:1080,eq=saturation=0.32:contrast=1.18:brightness=-0.09,vignette=a=1.1" */
    .plate{position:absolute;inset:0;background-position:center;background-size:cover;
           background-repeat:no-repeat}
"""

SCENE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>%(id)s</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>
<style>%(css)s</style>
</head>
<body>
<div data-hf-id="%(hid)s" id="root" data-composition-id="%(id)s"
     data-width="1920" data-height="1080" data-duration="%(dur).3f"%(nodrift)s>

%(body)s

<script>
  (function () {
    // DUR is the scene length. Every position below is written DUR * <numeric literal> INLINE at
    // the call site: that is the only form retime.py can rescale and broll_conflicts.py can see.
    var DUR = %(dur).3f;
    var tl = gsap.timeline({ paused: true });
%(tweens)s
    window.__timelines = window.__timelines || {};
    window.__timelines["%(id)s"] = tl;
  })();
</script>
</div>
</body>
</html>
"""


def build_scene(sid: str, spec: dict, d: float) -> tuple[str, int]:
    hid = "hf-" + re.sub(r"[^a-z0-9]", "", sid)[-6:]
    els, tw, idx = [], [], 1
    full = f'class="clip" data-start="0.0" data-duration="{d:.3f}"'

    def add(html: str, sel: str, at: float, kind: str = "fade"):
        nonlocal idx
        els.append(html)
        if kind == "rise":
            tw.append(f'    tl.fromTo("{sel}", {{opacity:0, y:26}}, '
                      f'{{opacity:1, y:0, duration:.75}}, DUR * {at:.3f});')
        elif kind == "wipe":
            tw.append(f'    tl.fromTo("{sel}", {{opacity:0, scaleX:.2}}, '
                      f'{{opacity:1, scaleX:1, duration:.6}}, DUR * {at:.3f});')
        else:
            tw.append(f'    tl.fromTo("{sel}", {{opacity:0, x:-22}}, '
                      f'{{opacity:.96, x:0, duration:.8}}, DUR * {at:.3f});')
        idx += 1

    beats = list(spec.get("beats") or [])
    b = iter(beats)

    def nxt(default: float) -> float:
        try:
            return float(next(b))
        except StopIteration:
            return default

    # Track 0, ahead of everything, and NOT routed through add() -- add() fades an element in
    # from opacity 0, which is precisely the behaviour that made frame 0 black.
    if spec.get("plate"):
        els.append(f'  <div data-hf-id="{hid}p" id="s-plate" class="plate clip" '
                   # Root-relative, NOT "../assets/...". Compositions are served with the
                   # project root as base URL; a "../" path renders fine and 404s in preview,
                   # which npm run check calls invalid_parent_traversal_in_asset_path.
                   f"style=\"background-image:url('assets/images/{spec['plate']}')\" "
                   f'data-start="0.0" data-duration="{d:.3f}" data-track-index="0"></div>')
        # Held at full for PLATE_HOLD_S, then down to a backdrop. The hold is the thumbnail
        # match and the vault gives it five seconds; the fade is also a real visual event, which
        # is why the 4.067s freeze that sat 0.067s over the cap goes away with it.
        hold = min(PLATE_HOLD_S, d * 0.5) / d
        tw.append(f'    tl.fromTo("#s-plate", {{opacity:1}}, '
                  f'{{opacity:.15, duration:1.1, ease:"none"}}, DUR * {hold:.3f});')

    add(f'  <div data-hf-id="{hid}t" id="s-title" class="wrap title clip" '
        f'data-start="0.0" data-duration="{d:.3f}" data-track-index="{idx}">{esc(spec["title"])}</div>',
        "#s-title", nxt(0.03))
    if spec.get("sub"):
        add(f'  <div data-hf-id="{hid}s" id="s-sub" class="wrap sub clip" '
            f'data-start="0.0" data-duration="{d:.3f}" data-track-index="{idx}">{esc(spec["sub"])}</div>',
            "#s-sub", nxt(0.09))
    add(f'  <div data-hf-id="{hid}r" id="s-rule" class="rule clip" style="top:262px" '
        f'data-start="0.0" data-duration="{d:.3f}" data-track-index="{idx}"></div>',
        "#s-rule", nxt(0.13), "wipe")

    cards = spec.get("cards") or []
    if cards:
        inner = []
        for i, c in enumerate(cards):
            vcls = "val sm" if len(str(c["value"])) > 9 else "val"
            inner.append(
                f'      <div data-hf-id="{hid}c{i}" id="s-c{i}" class="card">\n'
                f'        <div data-hf-id="{hid}a{i}" class="cbar"></div>\n'
                f'        <div data-hf-id="{hid}l{i}" class="lab">{esc(c["label"])}</div>\n'
                f'        <div data-hf-id="{hid}v{i}" class="{vcls}">{esc(str(c["value"]))}</div>\n'
                + (f'        <div data-hf-id="{hid}n{i}" class="note">{esc(c["note"])}</div>\n'
                   if c.get("note") else "")
                + "      </div>")
        els.append(f'  <div data-hf-id="{hid}b" class="wrap band clip" data-start="0.0" '
                   f'data-duration="{d:.3f}" data-track-index="{idx}">\n'
                   f'    <div data-hf-id="{hid}rw" class="row">\n' + "\n".join(inner) +
                   "\n    </div>\n  </div>")
        idx += 1
        # `stagger_parts` reveals a card's label, value and note as three separate changes rather
        # than one. intro_pace wants >= 1 visual change per 1.6s across the opening, and a scene
        # built from whole-card fades cannot reach 16 changes in 25s no matter how many beat
        # fractions the spec declares -- there are only as many changes as there are elements.
        if spec.get("stagger_parts"):
            for i in range(len(cards)):
                tw.append(f'    tl.fromTo("#s-c{i}", {{opacity:0, y:26}}, '
                          f'{{opacity:1, y:0, duration:.3}}, DUR * {nxt(0.20 + i * 0.16):.3f});')
                for part, sel in (("l", "lab"), ("v", "val"), ("n", "note")):
                    if part == "n" and not cards[i].get("note"):
                        continue
                    # A pure opacity fade on a 24px label is a change nobody sees and nothing
                    # measures: ep03's hook authored 19 beats and intro_pace found 12, and the
                    # seven it missed were all part-fades. The parts RISE now, same as the cards
                    # do -- a small block that moves reads as a reveal, a small block that
                    # brightens reads as nothing.
                    tw.append(f'    tl.fromTo("#s-c{i} .{sel}", {{opacity:0, y:28}}, '
                              f'{{opacity:1, y:0, duration:.28}}, DUR * {nxt(0.24 + i * 0.16):.3f});')
        else:
            for i in range(len(cards)):
                tw.append(f'    tl.fromTo("#s-c{i}", {{opacity:0, y:26}}, '
                          f'{{opacity:1, y:0, duration:.75}}, DUR * {nxt(0.22 + i * 0.14):.3f});')

    # `ticks` are small labelled markers revealed one at a time under the band. They exist so a
    # scene can clear intro_pace with MARGIN using real content rather than decoration: ep02's
    # hook straddled the 16-change bar and which side a render landed on was encoder noise.
    for i, t in enumerate(spec.get("ticks") or []):
        add(f'  <div data-hf-id="{hid}k{i}" id="s-tk{i}" class="wrap clip" '
            # Ticks stack under the card band and above the kicker, which starts at 924
            # (bottom:104 + a 52px line box). A fourth tick at 700+3*54 ran to 910 and the
            # layout checker called the overlap on ep04. 636 + i*52 puts a fourth tick's
            # box at 792..840 -- 84px clear of the kicker, 71px below the card band.
            f'style="top:{636 + i * 52}px;font-weight:600;font-size:34px;line-height:1.4;'
            f'letter-spacing:.16em;color:#a9a29a;'
            f'text-align:center" data-start="0.0" data-duration="{d:.3f}" '
            f'data-track-index="{idx}">{esc(t)}</div>', f"#s-tk{i}", nxt(0.50 + i * 0.04), "rise")

    if spec.get("kicker"):
        add(f'  <div data-hf-id="{hid}k" id="s-kick" class="wrap kick clip" '
            f'data-start="0.0" data-duration="{d:.3f}" data-track-index="{idx}">{esc(spec["kicker"])}</div>',
            "#s-kick", nxt(0.78), "rise")

    nodrift = ' data-no-drift="1"' if spec.get("no_drift") else ""
    html = SCENE % dict(id=sid, hid=hid, dur=d, css=CSS % {"w": SAFE_W},
                        body="\n".join(els), tweens="\n".join(tw), nodrift=nodrift)
    return html, len(tw)


ACADEMIC_COPY = {
    ("01", "scene-01"): (
        "HISTORICAL REPLAY",
        "Rules · costs · holdout · stop condition",
    ),
    ("01", "scene-03"): (
        "RULES BEFORE RESULTS",
        "Write the idea before you see the test.",
    ),
    ("01", "scene-13"): (
        "WRITE THE PROCESS",
        "The curve is a measurement, not the strategy.",
    ),
    ("02", "scene-twins"): (
        "OUT-OF-SAMPLE ≠ CERTIFIED",
        "Data quality, execution, dependence, regime coverage, and search count remain open.",
    ),
    ("03", "scene-cliff"): (
        "DESCRIPTIVE SHAPE",
        "A sharp response is evidence from this field, not a universal theorem.",
    ),
    ("03", "scene-scar"): (
        "WIRING PROOF ≠ CALIBRATION",
        "External fills and live execution still have to be measured.",
    ),
    ("04", "scene-casualty"): (
        "LOCATION ≠ CAUSATION",
        "A two-dimensional projection can locate failures without proving the cause of each failure.",
    ),
}

ACADEMIC_EPISODES = {
    "01": "BACKTEST IS NOT A STRATEGY",
    "02": "OUT-OF-SAMPLE",
    "03": "SLIPPAGE",
    "04": "MONTE CARLO + PARAMETER ROBUSTNESS",
}

V4_EPISODES = {
    "01": "SELECTION + INTAKE",
    "02": "OUT-OF-SAMPLE",
    "03": "FILL + SESSION STRESS",
    "04": "FUTURES COST STRESS",
}

V4_INTRO_AUDIT = {
    "01": (
        ("SETTINGS SEARCHED", "9,971", "warn"),
        ("WINNER FROZEN", "60 / 66", "good"),
        ("IN-SAMPLE NET", "+$78,420", "good"),
        ("OUT-OF-SAMPLE NET", "MINUS $9,229", "bad"),
        ("SEARCH RECORDED", "CHECK", "good"),
        ("FUTURE PROFIT GUARANTEED", "NO", "bad"),
    ),
    "02": (
        ("RULE FROZEN FIRST", "CHECK", "good"),
        ("IN-SAMPLE INTAKE", "1 PASSED", "good"),
        ("NEXT DATA HIDDEN", "UNTIL TEST", "good"),
        ("OUT-OF-SAMPLE", "0 LEFT", "bad"),
        ("FAILURE CAUSE KNOWN", "NO", "warn"),
        ("FUTURE PROFIT GUARANTEED", "NO", "bad"),
    ),
    "03": (
        ("CANDIDATES IN", "154", "warn"),
        ("FILL ONE BAR LATER", "TEST", "warn"),
        ("EARLIER SESSION HALF", "TEST", "warn"),
        ("LATER SESSION HALF", "TEST", "warn"),
        ("PASSED ALL THREE", "53", "good"),
        ("FAILED A VIEW", "101", "bad"),
    ),
    "04": (
        ("CANDIDATES IN", "53", "warn"),
        ("TRADE LEDGER FROZEN", "CHECK", "good"),
        ("2X SLIPPAGE FAILS", "2", "bad"),
        ("3X SLIPPAGE FAILS", "7", "bad"),
        ("PASSED BOTH GATES", "46", "good"),
        ("BASELINE COST KNOWN", "NO", "warn"),
    ),
}

ACADEMIC_CONTEXT_STEPS = {
    ("01", "scene-13"): ("RULES", "COSTS", "HOLDOUT", "STOP RULE"),
    ("03", "scene-scar"): ("WIRING", "CALIBRATION", "LIVE FILLS", "LIMITS"),
}

ACADEMIC_INTRO_AUDIT = {
    "01": (
        ("HISTORICAL PRICES REPLAYED", "YES", "good"),
        ("RULES FROZEN FIRST", "CHECK", "good"),
        ("COSTS WRITTEN IN", "CHECK", "good"),
        ("SEARCH RECORDED", "CHECK", "good"),
        ("HOLDOUT UNTOUCHED", "NEXT", "warn"),
        ("TOMORROW PREDICTED", "NO", "bad"),
    ),
    "02": (
        ("BUILT ON EARLIER DATA", "YES", "good"),
        ("RULES FROZEN", "CHECK", "good"),
        ("LATER BLOCK HIDDEN", "UNTIL TEST", "good"),
        ("RESULT SURVIVES", "MEASURE", "warn"),
        ("CHANGED AFTER LOOKING", "CONTAMINATED", "bad"),
        ("FINAL PROOF", "NO", "bad"),
    ),
    "03": (
        ("COMMISSION INCLUDED", "CHECK", "good"),
        ("SLIPPAGE STRESSED", "CHECK", "good"),
        ("TURNOVER COUNTED", "CHECK", "good"),
        ("FILL MODEL NAMED", "CHECK", "good"),
        ("STILL PROFITABLE", "TEST", "warn"),
        ("ZERO-COST RESULT", "INCOMPLETE", "bad"),
    ),
    "04": (
        ("ONE BEST SETTING", "FRAGILE?", "bad"),
        ("NEIGHBORS TESTED", "CHECK", "good"),
        ("PLATEAU WIDTH", "MEASURE", "warn"),
        ("RANDOM PATHS", "TEST", "warn"),
        ("EDGE PEAK", "WARNING", "bad"),
        ("STABLE REGION", "PREFER", "good"),
    ),
}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _srt_timestamp(seconds: float) -> str:
    millis = max(0, round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _caption_cues(text: str, start: float, end: float) -> list[tuple[float, float, str]]:
    """Distribute sentence captions across the measured narration window."""
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    if not sentences:
        return []
    weights = [max(1, len(re.findall(r"\w+", sentence))) for sentence in sentences]
    total_weight = sum(weights)
    cursor = start
    cues = []
    for index, (sentence, weight) in enumerate(zip(sentences, weights)):
        cue_end = end if index == len(sentences) - 1 else cursor + (end - start) * weight / total_weight
        cues.append((cursor, cue_end, sentence))
        cursor = cue_end
    return cues


def _install_file(source: Path, target: Path, *, hardlink: bool = False) -> None:
    """Install one render dependency without rewriting an identical file."""
    if not source.is_file():
        raise SystemExit(f"BLOCK: missing approved asset {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_file() and _sha(source) == _sha(target):
        return
    if target.exists():
        target.unlink()
    if hardlink:
        try:
            target.hardlink_to(source)
            return
        except OSError:
            pass
    shutil.copyfile(source, target)


def _academic_scene_html(
    *,
    composition_id: str,
    scene_id: str,
    episode: str,
    duration: float,
    route: str,
    visual_src: str | None,
    copy: tuple[str, str] | None,
    provenance: str,
    is_intro: bool,
    episode_label: str | None = None,
    intro_audit: tuple[tuple[str, str, str], ...] | None = None,
) -> str:
    prefix = re.sub(r"[^a-z0-9]", "", composition_id.lower())
    is_trader = route == "trader_context"
    art_class = "art-stage"
    if route == "real_chart":
        art_class += " chart-stage"
    elif route == "chalkboard_draw_on":
        art_class += " chalk-stage"
    elif route == "card":
        art_class += " card-stage"
    else:
        art_class += " math-stage"
    if is_intro:
        art_class += " intro-art-stage"

    art = ""
    shutters = ""
    shutter_tweens = ""
    if visual_src:
        art = (
            f'    <div id="{prefix}-art-stage" class="clip {art_class}" '
            f'data-start="0" data-duration="{duration:.3f}" data-track-index="1">\n'
            f'      <img id="{prefix}-art" src="{visual_src}" alt="" '
            f'data-layout-allow-overflow="true" />\n'
            "    </div>\n"
        )
        shutter_count = 3
        for i in range(shutter_count):
            top = i * 33.333
            height = 33.5
            shutters += (
                f'    <div id="{prefix}-shutter-{i}" class="clip shutter" '
                f'style="top:{top:.3f}%;height:{height:.3f}%;" '
                f'data-layout-allow-overflow="true" '
                f'data-start="0" data-duration="{duration:.3f}" '
                f'data-track-index="{20 + i}"></div>\n'
            )
            at = i * 0.03
            shutter_tweens += (
                f'    tl.fromTo("#{prefix}-shutter-{i}", {{xPercent:0}}, '
                f'{{xPercent:102, duration:.05, ease:"power2.out"}}, '
                f"{at:.3f});\n"
            )

    callout = ""
    callout_tween = ""
    if copy:
        callout = (
            f'    <div id="{prefix}-callout" class="clip callout" data-start="0" '
            f'data-duration="{duration:.3f}" data-track-index="10">\n'
            f'      <div class="callout-kicker">{esc(copy[0])}</div>\n'
            f'      <div class="callout-copy">{esc(copy[1])}</div>\n'
            "    </div>\n"
        )
        callout_at = 3.48 if (episode, scene_id) == ("01", "scene-03") else min(5.0, duration * 0.18)
        callout_tween = (
            f'    tl.fromTo("#{prefix}-callout", {{opacity:0, y:34}}, '
            f'{{opacity:1, y:0, duration:.8, ease:"power3.out"}}, '
            f"{callout_at:.3f});\n"
        )

    context_board = ""
    context_tween = ""
    if is_trader:
        steps = ACADEMIC_CONTEXT_STEPS[(episode, scene_id)]
        context_board = (
            f'    <div id="{prefix}-context-board" class="clip context-board" '
            f'data-start="0" data-duration="{duration:.3f}" data-track-index="2">\n'
            '      <div class="context-heading">PROCESS RECORD</div>\n'
            '      <div class="context-steps">\n'
            + "\n".join(
                f'        <div class="context-step"><span>{i + 1:02d}</span>{esc(step)}</div>'
                for i, step in enumerate(steps)
            )
            + "\n      </div>\n"
            "    </div>\n"
        )
        context_tween = (
            f'    tl.fromTo("#{prefix}-context-board", {{opacity:0, y:42}}, '
            f'{{opacity:1, y:0, duration:.85, ease:"power3.out"}}, 4.20);\n'
        )

    intro_board = ""
    intro_tweens = ""
    if is_intro:
        audit_rows = intro_audit or ACADEMIC_INTRO_AUDIT[episode]
        intro_board = (
            f'    <div id="{prefix}-audit" class="clip audit-board" data-start="0" '
            f'data-duration="{duration:.3f}" data-track-index="12">\n'
            '      <div class="audit-heading">INTO THE LABORATORY // QUESTION LEDGER</div>\n'
            '      <div class="audit-rows">\n'
            + "\n".join(
                f'        <div id="{prefix}-audit-{i}" class="audit-row">'
                f'<span class="audit-question">{esc(question)}</span>'
                f'<span class="audit-open">OPEN</span>'
                f'<span class="audit-answer {tone}">{esc(answer)}</span>'
                f'<span class="audit-scan"></span></div>'
                for i, (question, answer, tone) in enumerate(audit_rows)
            )
            + "\n      </div>\n"
            "    </div>\n"
        )
        row_step = min(0.62, max(0.32, (duration - 1.35) / max(1, len(audit_rows) - 1)))
        for i in range(len(audit_rows)):
            reveal_at = 0.45 + i * row_step
            answer_at = reveal_at + .36
            intro_tweens += (
                f'    tl.fromTo("#{prefix}-audit-{i}", {{opacity:0, x:28}}, '
                f'{{opacity:1, x:0, duration:.18, ease:"power2.out"}}, {reveal_at:.2f});\n'
                f'    tl.to("#{prefix}-audit-{i} .audit-open", '
                f'{{background:"#ff9100", color:"#08030a", duration:.12}}, '
                f'{reveal_at + .18:.2f});\n'
                f'    tl.to("#{prefix}-audit-{i} .audit-open", '
                f'{{opacity:0, duration:.12}}, {answer_at:.2f});\n'
                f'    tl.fromTo("#{prefix}-audit-{i} .audit-answer", {{opacity:0, y:7}}, '
                f'{{opacity:1, y:0, duration:.18, ease:"power2.out"}}, {answer_at + .08:.2f});\n'
                f'    tl.fromTo("#{prefix}-audit-{i} .audit-scan", {{scaleX:0}}, '
                f'{{scaleX:1, duration:.18, ease:"power2.out"}}, {reveal_at + .56:.2f});\n'
            )
        heading_at = min(duration - .35, 0.45 + (len(audit_rows) - 1) * row_step + .82)
        intro_tweens += (
            f'    tl.to("#{prefix}-audit .audit-heading", '
            f'{{color:"#ff9100", duration:.16}}, {heading_at:.2f});\n'
        )

    background = "transparent" if is_trader else "#08030a"
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>{composition_id}</title></head>
<body>
<template id="{composition_id}-template">
  <style>
    @font-face {{ font-family:"Cascadia Mono"; src:local("Cascadia Mono"); }}
    @font-face {{ font-family:"Cascadia Code"; src:local("Cascadia Code"); }}
    #root {{
      position:absolute; inset:0; width:1920px; height:1080px; overflow:hidden;
      box-sizing:border-box; background:{background}; color:#f5e8ea;
      font-family:"Cascadia Mono","Cascadia Code",Consolas,monospace;
    }}
    .clip {{ position:absolute; box-sizing:border-box; }}
    .field-grid {{
      inset:0; opacity:.22; pointer-events:none;
      background-image:
        linear-gradient(rgba(255,23,68,.16) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,23,68,.12) 1px, transparent 1px);
      background-size:96px 96px;
    }}
    .art-stage {{
      left:54px; top:36px; width:1812px; height:1008px; overflow:hidden;
      border:1px solid #4b1120; background:#08030a; box-shadow:0 28px 80px rgba(0,0,0,.46);
    }}
    .art-stage img {{ display:block; width:100%; height:100%; object-fit:contain; }}
    .chart-stage {{ left:64px; top:146px; width:1310px; height:760px; transform:perspective(1400px) rotateY(2deg); }}
    .chalk-stage {{ left:74px; top:62px; width:1772px; height:956px; border-color:#493b2b; }}
    .card-stage {{ opacity:.42; transform:scale(1.035); }}
    .intro-art-stage {{ left:64px; top:146px; width:970px; height:760px; }}
    .shutter {{ left:0; width:100%; background:#08030a; z-index:5; transform-origin:left center; }}
    .source-note {{
      left:86px; bottom:38px; z-index:9; max-width:1500px; color:#c89aa3;
      font-size:18px; line-height:1.25; letter-spacing:.06em;
    }}
    .callout {{
      right:88px; bottom:104px; z-index:10; width:640px; padding:30px 34px;
      border:1px solid #ff1744; border-left-width:8px; background:rgba(8,3,10,.94);
      box-shadow:0 24px 70px rgba(0,0,0,.50);
    }}
    .callout-kicker {{ color:#ff9100; font-size:25px; line-height:1.2; font-weight:800; letter-spacing:.08em; }}
    .callout-copy {{ margin-top:15px; color:#f5e8ea; font-size:29px; line-height:1.32; font-weight:650; }}
    .context-board {{
      left:86px; top:174px; width:1748px; height:720px; z-index:4; padding:68px 76px;
      border:1px solid #4b1120; background:#08030a; box-shadow:0 28px 80px rgba(0,0,0,.55);
    }}
    .context-heading {{ color:#f5e8ea; font-size:54px; line-height:1.1; font-weight:850; letter-spacing:.03em; }}
    .context-steps {{ display:grid; grid-template-columns:repeat(4,1fr); gap:24px; margin-top:112px; }}
    .context-step {{
      min-height:180px; padding:34px 26px; border-top:6px solid #ff1744; background:#13060b;
      color:#f5e8ea; font-size:28px; line-height:1.25; font-weight:750;
    }}
    .context-step span {{ display:block; margin-bottom:26px; color:#ff9100; font-size:22px; line-height:1; }}
    .audit-board {{
      right:88px; top:154px; width:690px; z-index:12; padding:24px 26px 28px;
      border:1px solid #5a1a28; border-top:5px solid #ff1744;
      background:rgba(8,3,10,.94); box-shadow:0 28px 80px rgba(0,0,0,.60);
    }}
    .audit-heading {{
      color:#f5e8ea; font-size:19px; line-height:1.2; font-weight:800; letter-spacing:.07em;
    }}
    .audit-rows {{ display:grid; gap:10px; margin-top:20px; }}
    .audit-row {{
      position:relative; min-height:68px; display:flex; align-items:center; padding:0 118px 0 18px;
      border-left:4px solid #ff1744; background:#15070c;
    }}
    .audit-question {{ color:#f5e8ea; font-size:22px; line-height:1.16; font-weight:720; }}
    .audit-open, .audit-answer {{
      position:absolute; right:14px; top:20px; min-width:84px; text-align:center;
      font-size:17px; line-height:1.6; font-weight:850; letter-spacing:.05em;
    }}
    .audit-open {{ color:#ffb1bf; border:1px solid #ff1744; }}
    .audit-answer {{ opacity:0; color:#08030a; }}
    .audit-answer.good {{ background:#00e676; }}
    .audit-answer.warn {{ background:#ff9100; }}
    .audit-answer.bad {{ background:#ff1744; color:#1b191a; }}
    .audit-scan {{
      position:absolute; left:0; bottom:0; width:100%; height:4px; background:#ff9100;
      transform:scaleX(0); transform-origin:left center;
    }}
  </style>
  <div id="root" data-composition-id="{composition_id}" data-width="1920"
       data-height="1080" data-duration="{duration:.3f}">
    <div id="{prefix}-grid" class="clip field-grid" data-start="0"
         data-duration="{duration:.3f}" data-track-index="0"></div>
{art}{shutters}{context_board}{intro_board}
    <div id="{prefix}-source" class="clip source-note" data-start="0"
         data-duration="{duration:.3f}" data-track-index="9">{esc(provenance)}</div>
{callout}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused:true }});
    const DUR = {duration:.3f};
    tl.fromTo("#{prefix}-grid", {{opacity:.08}}, {{opacity:.22, duration:.9, ease:"none"}}, 0);
    tl.fromTo("#{prefix}-source", {{opacity:0, y:16}}, {{opacity:1, y:0, duration:.7, ease:"power2.out"}}, .55);
{f'    tl.fromTo("#{prefix}-art", {{opacity:.38}}, {{opacity:1, duration:1.15, ease:"power2.out"}}, .18);' if visual_src else ''}
{shutter_tweens}{context_tween}{intro_tweens}{callout_tween}
    window.__timelines["{composition_id}"] = tl;
  </script>
</template>
</body>
</html>
"""


def _narration_profile(manifest: dict, narration: dict[str, dict]) -> dict[str, str]:
    """Resolve one manifest-pinned narrator instead of hard-coding John in the render."""
    profiles = {
        (
            asset.get("provider", "Higgsfield"),
            asset.get("model", "Qwen Audio 3.0 TTS Flash"),
            asset.get("voice_performance", {})
            .get("provider_settings", {})
            .get("voice"),
        )
        for asset in narration.values()
    }
    if len(profiles) != 1 or None in next(iter(profiles)):
        raise SystemExit("BLOCK: narration assets do not pin one provider/model/voice")
    provider, model, voice = next(iter(profiles))
    metadata_voice = manifest.get("metadata", {}).get("narration", {}).get("voice")
    if metadata_voice and metadata_voice != voice:
        raise SystemExit("BLOCK: narration metadata conflicts with narration assets")
    slug = re.sub(r"[^a-z0-9]+", "-", voice.lower()).strip("-")
    return {
        "asset_dir": f"qwen-{slug}",
        "basis": f"Measured approved {model} {voice} masters",
        "label": f"{provider} {model} / {voice} preset / clean master",
    }


def build_academic_episode(episode_dir: Path) -> dict:
    """Build the approved meaning-first HyperFrames cut from canonical artifacts."""
    episode_dir = episode_dir.resolve()
    projects_root = PROJECTS.resolve()
    if not episode_dir.is_relative_to(projects_root):
        raise SystemExit(f"BLOCK: episode must live under {projects_root}")
    if not episode_dir.name.startswith(("series-0", "series-v4-e")):
        raise SystemExit(f"BLOCK: not a teaching-series project: {episode_dir}")

    v4_match = re.fullmatch(r"series-v4-e(\d{2})-.+", episode_dir.name)
    episode = v4_match.group(1) if v4_match else episode_dir.name.split("-")[1]
    if episode not in ACADEMIC_EPISODES:
        raise SystemExit(f"BLOCK: unsupported episode {episode}")
    episode_label = V4_EPISODES[episode] if v4_match else ACADEMIC_EPISODES[episode]
    intro_audit = V4_INTRO_AUDIT[episode] if v4_match else ACADEMIC_INTRO_AUDIT[episode]
    packaging = json.loads(
        (episode_dir / "artifacts" / "packaging.json").read_text(encoding="utf-8")
    )
    display_episode = f"{int(packaging.get('episode', episode)):02d}"
    scene_plan_path = episode_dir / "artifacts" / "scene_plan.json"
    manifest_path = episode_dir / "artifacts" / "asset_manifest.json"
    script_path = episode_dir / "artifacts" / "script.json"
    scene_plan = json.loads(scene_plan_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    script = json.loads(script_path.read_text(encoding="utf-8"))
    visuals = {
        item["scene_id"]: item
        for item in manifest["assets"]
        if item["type"] != "narration"
    }
    narration = {
        item["scene_id"]: item
        for item in manifest["assets"]
        if item["type"] == "narration"
    }
    scene_ids = [scene["id"] for scene in scene_plan["scenes"]]
    script_sections = {section["id"]: section for section in script["sections"]}
    if (
        set(scene_ids) != set(visuals)
        or set(scene_ids) != set(narration)
        or set(scene_ids) != set(script_sections)
    ):
        raise SystemExit(f"BLOCK: scene/visual/narration IDs do not align in {episode_dir.name}")
    narration_profile = _narration_profile(manifest, narration)

    hyperframes = episode_dir / "hyperframes"
    compositions = hyperframes / "compositions"
    compositions.mkdir(parents=True, exist_ok=True)
    for old in (*compositions.glob("*.html"), *compositions.glob("*.motion.json")):
        old.unlink()
    _install_file(ACADEMIC_GSAP, hyperframes / "assets" / "vendor" / "gsap.min.js")

    slots: list[str] = []
    audio_tags: list[str] = []
    media_tags: list[str] = []
    timing: list[dict] = []
    total = 0.0
    trader_source = (
        PROJECTS
        / "series-01-backtest-is-not-a-strategy"
        / "hyperframes"
        / "assets"
        / "broll"
        / "lab-desk-monitors.mp4"
    )

    for index, scene in enumerate(scene_plan["scenes"]):
        scene_id = scene["id"]
        visual = visuals[scene_id]
        voice = narration[scene_id]
        route = visual["subtype"]
        voice_duration = round(float(voice["duration_seconds"]), 3)
        head = 0.20 if index == 0 else 0.15
        tail = 0.35
        # Canonical timestamps are planning estimates. Using them after the final take is
        # measured created up to 13 seconds of dead air, so the final voice is the clock.
        scene_duration = round(head + voice_duration + tail, 3)
        composition_id = f"ep{display_episode}-{re.sub(r'[^a-z0-9]+', '-', scene_id.lower()).strip('-')}"
        visual_src: str | None = None

        if route in {"animated_math", "card"}:
            svg_name = Path(visual["path"]).stem + ".svg"
            svg = hyperframes / "assets" / "math" / svg_name
            if not svg.is_file():
                raise SystemExit(f"BLOCK: missing installed mathematical source {svg}")
            visual_src = f"assets/math/{svg_name}"
        elif route == "chalkboard_draw_on":
            source = (episode_dir / visual["path"]).resolve()
            target = hyperframes / "assets" / "chalkboard" / source.name
            _install_file(source, target)
            visual_src = f"assets/chalkboard/{target.name}"
        elif route == "real_chart":
            source = (episode_dir / visual["path"]).resolve()
            target = hyperframes / "assets" / "images" / source.name
            _install_file(source, target)
            visual_src = f"assets/images/{target.name}"
        elif route == "trader_context":
            target = hyperframes / "assets" / "video" / trader_source.name
            _install_file(trader_source, target)
        else:
            raise SystemExit(f"BLOCK: unsupported route {route} for {scene_id}")

        if route == "real_chart":
            provenance = "TRADINGVIEW WORKFLOW CONTEXT // NOT PERFORMANCE EVIDENCE"
        elif route == "trader_context":
            provenance = "TRADERCOCKPIT SYNTHETIC CONTEXT // NON-EVIDENTIARY"
        elif route == "chalkboard_draw_on":
            provenance = "TRADERCOCKPIT ORIGINAL DRAW-ON // EXPLANATORY"
        elif route == "card":
            provenance = "TRADERCOCKPIT DEFINITION CARD // EXPLANATORY"
        else:
            provenance = "TRADERCOCKPIT ORIGINAL GEOMETRY // PROVENANCE INSIDE FRAME"

        html = _academic_scene_html(
            composition_id=composition_id,
            scene_id=scene_id,
            episode=display_episode,
            duration=scene_duration,
            route=route,
            visual_src=visual_src,
            copy=None if index == 0 else ACADEMIC_COPY.get((episode, scene_id)),
            provenance=provenance,
            is_intro=index == 0,
            episode_label=episode_label,
            intro_audit=intro_audit,
        )
        scene_file = compositions / f"{scene_id}.html"
        scene_file.write_text(html, encoding="utf-8")
        (compositions / f"{scene_id}.motion.json").write_text(
            json.dumps(
                {
                    "duration": scene_duration,
                    "assertions": [
                        {
                            "kind": "appearsBy",
                            "selector": f"#{re.sub(r'[^a-z0-9]', '', composition_id.lower())}-source",
                            "bySec": 0.9,
                        },
                        {
                            "kind": "staysInFrame",
                            "selector": f"#{re.sub(r'[^a-z0-9]', '', composition_id.lower())}-source",
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        slot_z = 4 if route == "trader_context" else 2
        slots.append(
            f'    <div id="slot-{index:02d}" class="clip scene-slot" '
            f'style="z-index:{slot_z}" data-composition-id="{composition_id}" '
            f'data-composition-src="compositions/{scene_id}.html" '
            f'data-start="{total:.3f}" data-duration="{scene_duration:.3f}" '
            f'data-track-index="1" data-width="1920" data-height="1080"></div>'
        )
        audio_source = episode_dir / voice["path"]
        audio_target = (
            hyperframes
            / "assets"
            / "audio"
            / narration_profile["asset_dir"]
            / f"{scene_id}.wav"
        )
        _install_file(audio_source, audio_target, hardlink=True)
        narration_start = round(total + head, 3)
        audio_tags.append(
            f'    <audio id="narration-{index:02d}" src="assets/audio/{narration_profile["asset_dir"]}/{scene_id}.wav" '
            f'data-start="{narration_start:.3f}" data-duration="{voice_duration:.3f}" '
            # Qwen takes are mono at -16 LUFS. HyperFrames duplicates mono into stereo,
            # adding 3.01 LU unless each channel is reduced by sqrt(1/2).
            f'data-track-index="10" data-volume="0.707945"></audio>'
        )

        if route == "trader_context":
            context_duration = min(5.0, scene_duration)
            media_tags.append(
                f'    <video id="context-{index:02d}" class="clip context-video" '
                f'src="assets/video/{trader_source.name}" data-start="{total:.3f}" '
                f'data-duration="{context_duration:.3f}" data-track-index="2" muted playsinline></video>'
            )

        timing.append(
            {
                "scene_id": scene_id,
                "composition_id": composition_id,
                "route": route,
                "start_seconds": total,
                "end_seconds": round(total + scene_duration, 3),
                "duration_seconds": scene_duration,
                "narration_start_seconds": narration_start,
                "narration_end_seconds": round(narration_start + voice_duration, 3),
                "narration_duration_seconds": voice_duration,
                "visual_source": visual_src or f"assets/video/{trader_source.name}",
            }
        )
        total = round(total + scene_duration, 3)

    index_html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Into the Laboratory — Episode {display_episode}</title>
  <script src="assets/vendor/gsap.min.js"></script>
  <style>
    @font-face {{ font-family:"Cascadia Mono"; src:local("Cascadia Mono"); }}
    @font-face {{ font-family:"Cascadia Code"; src:local("Cascadia Code"); }}
    * {{ margin:0; padding:0; box-sizing:border-box; }}
    body {{ background:#08030a; }}
    #root {{ position:absolute; inset:0; width:1920px; height:1080px; overflow:hidden; background:#08030a; }}
    .scene-slot {{ position:absolute; inset:0; transform-origin:center; }}
    .context-video {{ position:absolute; inset:0; width:1920px; height:1080px; object-fit:cover; z-index:3; opacity:.82; }}
  </style>
</head>
<body>
  <div id="root" data-composition-id="main" data-start="0" data-duration="{total:.3f}"
       data-width="1920" data-height="1080" data-fps="30">
{chr(10).join(slots)}
{chr(10).join(media_tags)}
{chr(10).join(audio_tags)}
  </div>
  <script>
    window.__timelines = window.__timelines || {{}};
    const main = gsap.timeline({{ paused:true }});
    window.__timelines["main"] = main;
  </script>
</body>
</html>
"""
    (hyperframes / "index.html").write_text(index_html, encoding="utf-8")

    timing_artifact = {
        "version": "1.0",
        "episode": display_episode,
        "basis": f"{narration_profile['basis']}; narration begins 0.20s into the opening scene and 0.15s into later scenes, with a 0.35s resolve hold after every narration asset.",
        "duration_seconds": total,
        "scene_count": len(timing),
        "scenes": timing,
    }
    timing_path = episode_dir / "artifacts" / "academic_edit_timing.json"
    timing_path.write_text(json.dumps(timing_artifact, indent=2) + "\n", encoding="utf-8")

    caption_dir = episode_dir / "artifacts" / "captions"
    caption_dir.mkdir(parents=True, exist_ok=True)
    caption_path = caption_dir / "youtube-native.srt"
    caption_rows: list[str] = []
    caption_index = 1
    for item in timing:
        section = script_sections[item["scene_id"]]
        for cue_start, cue_end, cue_text in _caption_cues(
            section["text"],
            item["narration_start_seconds"],
            item["narration_end_seconds"],
        ):
            caption_rows.extend(
                [
                    str(caption_index),
                    f"{_srt_timestamp(cue_start)} --> {_srt_timestamp(cue_end)}",
                    cue_text,
                    "",
                ]
            )
            caption_index += 1
    caption_path.write_text("\n".join(caption_rows), encoding="utf-8")

    cuts = []
    narration_segments = []
    scenes_by_id = {scene["id"]: scene for scene in scene_plan["scenes"]}
    for item in timing:
        scene = scenes_by_id[item["scene_id"]]
        cuts.append(
            {
                "id": item["scene_id"],
                "source": item["composition_id"],
                "in_seconds": item["start_seconds"],
                "out_seconds": item["end_seconds"],
                "speed": 1.0,
                "layer": "primary",
                "transition_in": "cut",
                "transition_out": "cut",
                "reason": scene["information_role"],
            }
        )
        narration_segments.append(
            {
                "asset_id": f"narration-{item['scene_id']}",
                "start_seconds": item["narration_start_seconds"],
                "end_seconds": item["narration_end_seconds"],
            }
        )
    sys.path.insert(0, str(ROOT / "OpenMontage"))
    from lib.slideshow_risk import score_slideshow_risk

    risk_scenes = json.loads(json.dumps(scene_plan["scenes"]))
    for risk_scene in risk_scenes:
        risk_scene.setdefault("shot_language", {})["camera_movement"] = "static"
    risk = score_slideshow_risk(
        risk_scenes,
        {"cuts": cuts},
        renderer_family="explainer-data",
        render_runtime="hyperframes",
    )
    edit_decisions = {
        "version": "1.0",
        "cuts": cuts,
        "audio": {
            "narration": {"segments": narration_segments},
            "sfx": [],
        },
        "subtitles": {
            "enabled": False,
            "style": "sentence",
            "source": "artifacts/captions/youtube-native.srt",
            "position": "bottom-center",
            "max_words_per_line": 10,
        },
        "renderer_family": "explainer-data",
        "render_runtime": "hyperframes",
        "composition_mode": "atelier",
        "bespoke": {
            "entry": "hyperframes/index.html",
            "composition_id": "main",
            "art_direction": "artifacts/art-direction.md",
        },
        "slideshow_risk_score": risk,
        "metadata": {
            "creative_grammar": "board_led_explainer",
            "gate_profile": "board-led-explainer",
            "music": "none",
            "caption_delivery": "youtube_native_sidecar_only",
            "measured_timing": "artifacts/academic_edit_timing.json",
            "voice": narration_profile["label"],
            "audio_mastering_target": "-16 LUFS, -1.5 dBTP, 48 kHz mono 24-bit PCM",
            "audio_processing": [
                "70 Hz high-pass",
                "two-pass EBU R128 normalization",
                "no denoise",
            ],
            "provider_spend_after_asset_approval_usd": 0,
            "visual_routes": {
                route: sum(1 for item in timing if item["route"] == route)
                for route in sorted({item["route"] for item in timing})
            },
            "rejected_visuals_excluded": True,
            "publish_authorized": False,
        },
    }
    edit_path = episode_dir / "artifacts" / "edit_decisions.json"
    edit_path.write_text(json.dumps(edit_decisions, indent=2) + "\n", encoding="utf-8")

    art_direction = f"""# TraderCockpit Academic Instrument — Episode {display_episode}

The composition uses the operator-approved meaning-first routing: original deterministic SVG
geometry for mathematical claims, original chalkboards for draw-on explanations, narrow cards
for definitions and limitations, the TradingView capture only for workflow context, and the
existing seated-trader footage only for non-evidentiary human context.

Palette: `#08030a` field, `#f5e8ea` primary type, `#ff1744` active trace, `#00e676`
profitable outcome, and `#ff9100` caution or boundary. Red and green retain trading meaning.
Every displayed chart keeps its own recorded-run, derived, illustrative, or limitation label.

The camera remains fixed. Staged masks, source-specific draw-ons, and deliberate holds expose the
actual relationship without decorative movement. The edit never substitutes laboratory objects, abstract physics,
or generated atmosphere for axes, points, bands, arithmetic, or labels.
"""
    (episode_dir / "artifacts" / "art-direction.md").write_text(
        art_direction, encoding="utf-8"
    )
    scene_rows = "\n".join(
        f"| {item['scene_id']} | {item['route']} | {item['start_seconds']:.3f}–{item['end_seconds']:.3f} | {item['visual_source']} |"
        for item in timing
    )
    (episode_dir / "artifacts" / "scenes.md").write_text(
        f"# Episode {display_episode} measured edit map\n\n"
        "| Scene | Route | Time (s) | Render source |\n"
        "|---|---|---:|---|\n"
        f"{scene_rows}\n",
        encoding="utf-8",
    )
    (hyperframes / "frame.md").write_text(
        f"# Episode {display_episode} frame contract\n\n"
        "Binding direction: TraderCockpit Academic Instrument. The approved SVG geometry is "
        "revealed as the explanatory subject on a fixed camera; review PNGs are not final plates. Original "
        "chalkboards draw on, real chart and trader footage remain context-only, and no "
        "rejected laboratory imagery may appear. 1920x1080, 30 fps, no music, native captions "
        "only.\n",
        encoding="utf-8",
    )
    return {
        "episode": display_episode,
        "scenes": len(timing),
        "duration_seconds": total,
        "index": str(hyperframes / "index.html"),
        "timing": str(timing_path),
        "edit_decisions": str(edit_path),
        "captions": str(caption_path),
        "index_sha256": _sha(hyperframes / "index.html"),
        "timing_sha256": _sha(timing_path),
        "edit_decisions_sha256": _sha(edit_path),
        "captions_sha256": _sha(caption_path),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", nargs="?", type=Path)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument(
        "--academic",
        action="store_true",
        help="build the approved meaning-first teaching-series composition",
    )
    a = ap.parse_args()

    if a.demo:
        spec = {"title": "DEMO", "sub": "SELF CHECK",
                "cards": [{"label": "A", "value": "1.43"}, {"label": "B", "value": "0.97"}],
                "kicker": "KICKER", "beats": [0.05, 0.10, 0.14, 0.30, 0.50, 0.80]}
        html, n = build_scene("scene-demo", spec, 40.0)
        lits = re.findall(r"DUR \* (\d+\.\d+)", html)
        assert len(lits) == n == 6, (len(lits), n)
        assert "DUR * c[" not in html and "DUR *" in html
        assert html.count('data-start="0.0"') >= 4, "clips must share one full-scene window"
        # This used to look for `font: <weight> <size>px/<lh>` and passed on a shorthand ending
        # in `inherit`, which no browser applies. Assert what actually has to be true: no `font:`
        # shorthand at all, and every font-size carries a line-height.
        assert "font:" not in CSS and "font:" not in html, "use longhand -- see the note on CSS"
        sizes = re.findall(r"font-size:\s*(\d+)px", CSS)
        assert len(sizes) >= 6 and CSS.count("line-height:") >= len(sizes),             "every font-size needs a line-height beside it"
        assert max(int(x) for x in sizes) >= 74, "the title must be a headline, not body copy"
        assert all(0.0 <= float(x) <= 1.0 for x in lits), "positions must be fractions of DUR"
        academic = _academic_scene_html(
            composition_id="ep04-scene-fan",
            scene_id="scene-fan",
            episode="04",
            duration=32.0,
            route="animated_math",
            visual_src="assets/math/ep04-fan-chart.svg",
            copy=None,
            provenance="RECORDED RUN",
            is_intro=True,
            intro_audit=V4_INTRO_AUDIT["04"],
        )
        assert academic.index("<template") < academic.index("<style") < academic.index('id="root"')
        assert "http://" not in academic and "https://" not in academic
        assert academic.count('data-track-index="9"') == 1
        assert 'window.__timelines["ep04-scene-fan"] = tl' in academic
        assert "focus-rail" not in academic and "progress-track" not in academic
        assert "-rail" not in academic and "-progress" not in academic
        assert '-grid", {opacity:.08}' in academic
        assert "episode-tag" not in academic and "route-tag" not in academic
        assert "ANIMATED MATH" not in academic
        assert "scale:1.025" not in academic and '-art", {x:' not in academic
        assert academic.count('background:"#ff9100"') == len(V4_INTRO_AUDIT["04"])
        assert academic.count('class="audit-scan"') == len(V4_INTRO_AUDIT["04"])
        assert academic.count('audit-scan", {scaleX:0}') == len(V4_INTRO_AUDIT["04"])
        assert all("PROVEN" not in question and not answer.startswith("-")
                   for rows in V4_INTRO_AUDIT.values() for question, answer, _ in rows)
        profile = _narration_profile(
            {"metadata": {"narration": {"voice": "Marcus"}}},
            {
                "scene-01": {
                    "provider": "Higgsfield",
                    "model": "Qwen Audio 3.0 TTS Flash",
                    "voice_performance": {
                        "provider_settings": {"voice": "Marcus"}
                    },
                }
            },
        )
        assert profile["asset_dir"] == "qwen-marcus"
        assert "Marcus" in profile["basis"] and "Marcus" in profile["label"]
        print(f"build_scenes selftest ok — {n} tweens, all DUR * <literal>, one window, "
              "line-heights present; academic template contract ok")
        return 0

    if not a.episode:
        ap.error("give an episode directory, or --demo")
    if a.academic:
        result = build_academic_episode(a.episode)
        print(
            f"EP{result['episode']} {result['scenes']} scenes "
            f"{result['duration_seconds']:.3f}s {result['index_sha256']}"
        )
        return 0
    spec_p = a.episode / "artifacts" / "scenes.json"
    if not spec_p.is_file():
        raise SystemExit(f"BLOCK: no spec at {spec_p}")
    specs = json.loads(spec_p.read_text(encoding="utf-8"))
    out = a.episode / "hyperframes" / "compositions"
    out.mkdir(parents=True, exist_ok=True)
    audio = a.episode / "hyperframes" / "assets" / "audio" / "v1"

    total, n, slots, auds = 0.0, 0, [], []
    HEAD = 0.6      # must match retime.py / wire_narration.py
    for sid, spec in specs.items():
        wav = audio / f"{sid}.wav"
        if not wav.is_file():
            raise SystemExit(f"BLOCK: {sid} has a spec but no VO at {wav}")
        raw = dur(wav)
        d = round(raw + 1.5, 3)     # head/tail pad, matches retime
        html, beats = build_scene(sid, spec, d)
        (out / f"{sid}.html").write_text(html, encoding="utf-8")
        print(f"  {sid:24s} {d:6.2f}s  {beats:2d} beats")
        hid = "hf-sl" + re.sub(r"[^a-z0-9]", "", sid)[-4:]
        slots.append(
            f'      <div data-hf-id="{hid}" id="slot-{n:02d}" class="scene-slot" data-composition-id="{sid}"\n'
            f'           data-composition-src="compositions/{sid}.html"\n'
            f'           data-start="{total:.3f}" data-duration="{d:.3f}"\n'
            f'           data-width="1920" data-height="1080" data-track-index="1"></div>')
        auds.append(
            f'      <audio data-hf-id="hf-na{n:02d}" id="narration-{n:02d}" class="clip" '
            f'src="assets/audio/v1/{sid}.wav" data-start="{total + HEAD:.3f}" '
            f'data-duration="{raw:.3f}" data-track-index="10"></audio>')
        total = round(total + d, 3)
        n += 1

    # Generated whole, so a slot and its narration cannot drift apart. wire_narration.py is
    # anchored to an ep02-specific "TODO(ep02)" comment and is deliberately not used here.
    idx = (out.parent / "index.html")
    idx.write_text(
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f'<title>{out.parent.parent.name}</title>\n<style>\n'
        '  *{margin:0;padding:0;box-sizing:border-box}\n'
        '  body{background:#000}\n'
        '  #root{position:absolute;inset:0;background:#0a0a0b;overflow:hidden}\n'
        '  .scene-slot{position:absolute;inset:0}\n'
        # Cutaways are 1344x768 or 1280x720; without this a clip lays out at its intrinsic
        # size in the top-left corner and the render looks like a bug rather than a cut.
        '  #root > video{position:absolute;inset:0;width:1920px;height:1080px;'
        'object-fit:cover}\n</style>\n</head>\n<body>\n'
        f'    <div data-hf-id="hf-root" id="root" data-composition-id="main" data-start="0" '
        f'data-duration="{total:.3f}" data-width="1920" data-height="1080" data-fps="30">\n'
        + "\n".join(slots) + "\n\n"
        + "      <!-- NARRATION (generated by tools/build_scenes.py) -->\n"
        + "\n".join(auds) + "\n      <!-- /NARRATION -->\n\n"
        # EMPTY ON PURPOSE. place_cutaways.py rewrites whatever sits between these two markers,
        # and when it finds neither them nor its ep02 anchor its regex fell through to a
        # str.replace() that matched nothing -- it wrote the file back unchanged and printed
        # "written." 35 cutaways were reported placed into a file with zero <video> tags, and
        # broll_conflicts then "passed" by finding no B-roll to conflict. The markers are part
        # of the generated file so that path cannot recur.
        + "      <!-- CUTAWAYS (generated by tools/place_cutaways.py) -->\n"
        + "      <!-- /CUTAWAYS -->\n"
        + "    </div>\n"
        # The master composition needs its own registration or the checker errors with
        # missing_timeline_registry -- the per-scene timelines do not satisfy it.
        + '<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js"></script>\n'
        + "<script>\n"
        + "  window.__timelines = window.__timelines || {};\n"
        + "  window.__timelines.main = gsap.timeline({ paused: true });\n"
        + "</script>\n</body>\n</html>\n", encoding="utf-8")

    print(f"\n{n} scenes, {total:.1f}s = {int(total//60)}:{int(total%60):02d}")
    print(f"index.html written with {n} slots and {n} narration clips")
    return 0


if __name__ == "__main__":
    sys.exit(main())
