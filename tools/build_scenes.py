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
import json
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# The master scales each .scene-slot to 1.105 with 52px of lateral travel, so usable half-width is
# (960 - 52) / 1.105 ~= 821px. Content must live inside x 139..1781, not the full 1920.
SAFE_W = 1642


def dur(wav: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(wav)], capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(f"BLOCK: ffprobe failed on {wav}")
    return round(float(out.stdout.strip()), 3)


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


CSS = """
    *{margin:0;padding:0;box-sizing:border-box}
    #root{position:absolute;inset:0;background:#0a0a0b;overflow:hidden;
          font-family:'Inter','Helvetica Neue',Arial,sans-serif;color:#e8e6e2}
    .wrap{position:absolute;left:50%%;transform:translateX(-50%%);width:%(w)dpx}
    /* every rule that sets a large size sets a line-height with it. */
    .title{top:96px;font:700 74px/1.14 inherit;letter-spacing:-.015em;color:#f2efe9;opacity:0}
    .sub{top:196px;font:500 34px/1.32 inherit;letter-spacing:.10em;color:#8c8781;opacity:0}
    .band{top:300px}
    .row{display:flex;gap:34px;justify-content:center;align-items:stretch}
    .card{flex:1;background:#131315;border:1px solid #24242a;border-radius:10px;
          padding:34px 32px 30px;opacity:0}
    .lab{font:600 24px/1.3 inherit;letter-spacing:.13em;color:#8f8a84;margin-bottom:18px}
    .val{font:700 92px/1.06 inherit;letter-spacing:-.02em;color:#f2efe9}
    .val.sm{font:700 62px/1.1 inherit}
    .note{font:400 25px/1.42 inherit;color:#9a938c;margin-top:18px}
    .kick{bottom:104px;font:600 40px/1.3 inherit;letter-spacing:.02em;color:#c8b98a;
          text-align:center;opacity:0}
    .rule{position:absolute;left:50%%;transform:translateX(-50%%);width:%(w)dpx;height:1px;
          background:#26262c;opacity:0}
    /* Kling returns 1280x720; without this a clip lays out at intrinsic size in the corner. */
    #root > video{position:absolute;inset:0;width:1920px;height:1080px;object-fit:cover}
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
                          f'{{opacity:1, y:0, duration:.55}}, DUR * {nxt(0.20 + i * 0.16):.3f});')
                for part, sel in (("l", "lab"), ("v", "val"), ("n", "note")):
                    if part == "n" and not cards[i].get("note"):
                        continue
                    tw.append(f'    tl.fromTo("#s-c{i} .{sel}", {{opacity:0}}, '
                              f'{{opacity:1, duration:.4}}, DUR * {nxt(0.24 + i * 0.16):.3f});')
        else:
            for i in range(len(cards)):
                tw.append(f'    tl.fromTo("#s-c{i}", {{opacity:0, y:26}}, '
                          f'{{opacity:1, y:0, duration:.75}}, DUR * {nxt(0.22 + i * 0.14):.3f});')

    # `ticks` are small labelled markers revealed one at a time under the band. They exist so a
    # scene can clear intro_pace with MARGIN using real content rather than decoration: ep02's
    # hook straddled the 16-change bar and which side a render landed on was encoder noise.
    for i, t in enumerate(spec.get("ticks") or []):
        add(f'  <div data-hf-id="{hid}k{i}" id="s-tk{i}" class="wrap clip" '
            f'style="top:{770 + i * 46}px;font:600 27px/1.4 inherit;letter-spacing:.16em;color:#8b8680;'
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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("episode", nargs="?", type=Path)
    ap.add_argument("--demo", action="store_true")
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
        assert re.search(r"font:\s*\d+\s+\d+px/[\d.]+", CSS), "large type needs a line-height"
        assert all(0.0 <= float(x) <= 1.0 for x in lits), "positions must be fractions of DUR"
        print(f"build_scenes selftest ok — {n} tweens, all DUR * <literal>, one window, "
              "line-heights present")
        return 0

    if not a.episode:
        ap.error("give an episode directory, or --demo")
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
            f'      <div data-hf-id="{hid}" class="scene-slot" data-composition-id="{sid}"\n'
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
