#!/usr/bin/env python3
"""Post-approval derivative lane: cut verticals from the APPROVED long-form master,
gate them, scaffold the social batch, and (with --upload) publish where auth allows.

Deterministic contract (operator 2026-07-21: repeatable, LLM-agnostic, own gates):
  1. Preconditions HARD-FAIL: build/master.mp4 + build/captions.srt + build/sections.json
     present, and publish_log.json carries a published YouTube long-form. Derivatives are
     cut ONLY downstream of the operator-approved long-form — never from an unreviewed master.
  2. Editorial input = derivatives-plan.json in the production dir (writer-authored, like
     vo.txt; selection is editorial, execution is deterministic):
       {"segments": [{"section": "01", "offset": 0, "duration": 35,
                      "label": "hook-bounce-failed", "anchor": "right", "layout": "crop",
                      "title": "<=100 chars, no '>'", "copy": "hook ... exact disclaimer"}]}
     Max 2 segments (YouTube 6-uploads/day quota discipline). Segment start is DERIVED:
     the captions.srt cue whose text opens the named section, plus offset — no whisper
     re-pick, no hand timestamps.
  3. Cut via studio-kit clipper --mode script into productions/<vid>/shorts — NEVER the
     shared studio-kit/clipper/output (2026-07-21 stale-clip collision). One clipper run
     per segment so CLIP_ANCHOR/CLIP_LAYOUT apply per segment; CLIP_CLEAN_VERTICAL=1
     renders the caption-free twin visual_qa needs for bbox diffing.
  4. Gates, fail-closed: visual_qa (safe zones, caption geometry, native-render provenance)
     + copy gate (script_style_gate.audit_text PASS + exact REQUIRED_DISCLAIMER).
  5. Batch: social-batch-verticals.json (social-batch/v2, containsSyntheticMedia false —
     operator ruling 2026-07-21: own voice, own charts, no AI-generated platform labels).
     Items are machine-approved ONLY because the parent long-form carries operator approval
     — reviewedBy records that chain; approvalSha256 = social_batch.approval_fingerprint.
  6. --upload publishes each item through tools/publish.py (auth probes fail closed,
     read-back verified). Without --upload everything stages and the exact publish
     commands are printed. Meta (IG/FB) and TikTok items stage but report their standing
     auth blockers instead of pretending.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
HUB = HERE.parent
CLIPPER = HUB / "studio-kit" / "clipper" / "clip.js"
MAX_SEGMENTS = 2

sys.path.insert(0, str(HERE))
from script_style_gate import audit_text  # noqa: E402
from social_batch import REQUIRED_DISCLAIMER, approval_fingerprint  # noqa: E402


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def parse_srt(path: Path) -> list[tuple[float, str]]:
    cues = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")):
        match = re.search(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->", block)
        if not match:
            continue
        h, m, s, ms = (int(g) for g in match.groups())
        text = " ".join(line.strip() for line in block.splitlines()
                        if "-->" not in line and not line.strip().isdigit())
        cues.append((h * 3600 + m * 60 + s + ms / 1000, text))
    return cues


def section_start(cues: list[tuple[float, str]], section_text: str, section_num: str) -> float:
    """First cue whose words open the section. Both artifacts are machine-written from the
    same vo.txt, so a 5-word prefix match is exact, not fuzzy."""
    prefix = _words(section_text)[:5]
    for start, text in cues:
        if _words(text)[: len(prefix)] == prefix:
            return start
    sys.exit(f"section {section_num}: opening words {prefix} not found in captions.srt — "
             "captions and sections.json disagree; re-run produce before cutting derivatives")


def run(cmd: list[str], env_extra: dict | None = None) -> None:
    env = {**os.environ, **(env_extra or {})}
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        sys.exit(f"command failed ({result.returncode}): {' '.join(str(part) for part in cmd)}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("prod")
    parser.add_argument("--upload", action="store_true",
                        help="publish gated items via tools/publish.py (default: stage only)")
    parser.add_argument("--platform", default="youtube",
                        help="channel for the batch items (default youtube = Shorts)")
    args = parser.parse_args()

    prod = (HUB / args.prod) if not Path(args.prod).is_absolute() else Path(args.prod)
    build = prod / "build"
    shorts = prod / "shorts"

    # 1. preconditions — derivatives exist only downstream of the approved long-form
    master = build / "master.mp4"
    captions = build / "captions.srt"
    sections_path = build / "sections.json"
    for required in (master, captions, sections_path):
        if not required.is_file():
            sys.exit(f"precondition missing: {required}")
    publish_log = prod / "publish_log.json"
    if not publish_log.is_file():
        sys.exit("publish_log.json missing — the long-form was never published; nothing to derive from")
    log_entries = json.loads(publish_log.read_text(encoding="utf-8"))
    entries = log_entries if isinstance(log_entries, list) else log_entries.get("entries", [])
    parent = next((e for e in reversed(entries)
                   if e.get("platform") == "youtube" and e.get("status") == "published"), None)
    if not parent:
        sys.exit("no published YouTube long-form in publish_log.json — approve and publish it first")

    plan_path = prod / "derivatives-plan.json"
    if not plan_path.is_file():
        sys.exit(f"{plan_path} missing — write the segment plan (editorial step; see module docstring)")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    segments = plan.get("segments", [])
    if not 1 <= len(segments) <= MAX_SEGMENTS:
        sys.exit(f"plan must carry 1-{MAX_SEGMENTS} segments (quota discipline), got {len(segments)}")

    sections = {s["num"]: s for s in json.loads(sections_path.read_text(encoding="utf-8"))}
    cues = parse_srt(captions)

    # 2. copy gate BEFORE any rendering — cheapest gate first
    for seg in segments:
        for key in ("section", "duration", "label", "title", "copy"):
            if not seg.get(key):
                sys.exit(f"segment missing '{key}': {seg}")
        if REQUIRED_DISCLAIMER not in seg["copy"]:
            sys.exit(f"segment {seg['label']}: copy lacks the exact disclaimer")
        report = audit_text(seg["copy"])
        if report["verdict"] != "PASS":
            sys.exit(f"segment {seg['label']}: copy BLOCKED by style gate: "
                     + "; ".join(b["type"] for b in report["blocked"]))
        if ">" in seg["title"]:
            sys.exit(f"segment {seg['label']}: YouTube rejects '>' in titles (invalidTitle scar)")

    # 3. cut — one clipper run per segment, per-production output dir
    shorts.mkdir(exist_ok=True)
    scratch = build / "derivative-segs"
    scratch.mkdir(exist_ok=True)
    assets = []
    for index, seg in enumerate(segments, start=1):
        section = sections.get(seg["section"]) or sys.exit(f"unknown section {seg['section']}")
        start = section_start(cues, section["text"], seg["section"]) + float(seg.get("offset", 0))
        seg_file = scratch / f"seg-{index}.json"
        seg_file.write_text(json.dumps({"segments": [
            {"start": round(start, 2), "duration": float(seg["duration"]), "label": seg["label"]}
        ]}), encoding="utf-8")
        run(["node", str(CLIPPER), str(master), "--mode", "script", "--script", str(seg_file),
             "--srt", str(captions), "--output", str(shorts), "--clips", "1", "--reframe"],
            env_extra={"CLIP_ANCHOR": seg.get("anchor", "right"),
                       "CLIP_LAYOUT": seg.get("layout", "crop"),
                       "CLIP_CLEAN_VERTICAL": "1"})
        rendered = sorted(shorts.glob(f"clip-001-{seg['label']}.vertical.mp4"))
        if not rendered:
            sys.exit(f"clipper produced no vertical for {seg['label']}")
        target = shorts / f"clip-{index:03d}-{seg['label']}.vertical.mp4"
        if rendered[0] != target:  # clipper numbers per-run; renumber to per-plan
            for suffix in (".vertical.mp4", ".vertical.clean.mp4", ".srt", ".mp4"):
                src = shorts / f"clip-001-{seg['label']}{suffix}"
                if src.exists():
                    src.replace(shorts / f"clip-{index:03d}-{seg['label']}{suffix}")
        assets.append((seg, target.relative_to(HUB).as_posix()))

    # renumbered files invalidate the per-run manifest; rewrite it so visual_qa provenance holds
    manifest = shorts / "manifest.json"
    manifest.write_text(json.dumps({
        "source": str(master), "mode": "script", "clips_count": len(assets),
        "segments": [{"start": None, "duration": s["duration"], "label": s["label"]}
                     for s, _ in assets],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parent_video": parent.get("url") or parent.get("videoId"),
    }, indent=2), encoding="utf-8")

    # 4. visual gate on the rendered pixels
    run([sys.executable, str(HERE / "visual_qa.py"), str(prod), "--clips", str(shorts)])

    # 5. batch scaffold — machine approval rides on the operator-approved parent
    batch_path = prod / "social-batch-verticals.json"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    batch = {"schema": "social-batch/v2",
             "batchId": f"{prod.name}-verticals",
             # Operator ruling 2026-07-21: no AI-generated platform labels — the narration is
             # the operator's OWN cloned voice reading operator-approved scripts, visuals are
             # real TradingView/news captures (scene-plan kinds validate the false declaration).
             # Platform-policy risk of unlabeled synthetic audio was stated and operator-owned.
             "containsSyntheticMedia": False,
             "items": []}
    for seg, asset in assets:
        # YouTube's batch contract rejects burned captions: it takes the caption-free twin
        # and platform-native captions. Burned stays for IG/FB/TikTok.
        if args.platform == "youtube":
            asset = asset.replace(".vertical.mp4", ".vertical.clean.mp4")
            caption_mode = "native"
        else:
            caption_mode = "burned"
        item = {
            "id": f"{args.platform}-{seg['label']}",
            "channel": args.platform,
            "status": "approved",
            "asset": asset,
            "claimsGate": (build / "claims-gate.json").relative_to(HUB).as_posix(),
            "productionApproval": (prod / "production-approval.json").relative_to(HUB).as_posix(),
            "title": seg["title"],
            "captionMode": caption_mode,
            "privacy": "public",
            "publicationAuthorized": True,
            "reviewedBy": f"machine: cut_derivatives downstream of operator-approved long-form "
                          f"{parent.get('url') or parent.get('videoId')}",
            "reviewedAt": now,
            "copy": seg["copy"],
        }
        item["approvalSha256"] = approval_fingerprint(
            batch["batchId"], item, contains_synthetic_media=True, schema="social-batch/v2")
        batch["items"].append(item)
    batch_path.write_text(json.dumps(batch, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[derivatives] batch staged: {batch_path} ({len(batch['items'])} items)")

    # 6. publish (or print the exact commands)
    for item in batch["items"]:
        cmd = [sys.executable, str(HERE / "publish.py"),
               "--batch", str(batch_path), "--item", item["id"]]
        if args.upload:
            run(cmd)
        else:
            print("[derivatives] to publish:", " ".join(cmd))
    print("[derivatives] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
