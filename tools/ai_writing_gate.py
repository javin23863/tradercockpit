#!/usr/bin/env python3
"""Fail-closed AI-writing gate. Wraps the vendored conorbronsdon/avoid-ai-writing detector.

    python tools/ai_writing_gate.py <file-or-production> [--json]
    python tools/ai_writing_gate.py --survey productions/*/vo.txt   # re-calibrate BLOCK_TYPES

Why a wrapper and not a port: the detector is 1,754 lines of regex, stylometry and
AI-tool fingerprints under MIT, vendored verbatim at tools/vendor/avoid-ai-writing (see
VERSION for the pinned commit). Porting it to Python would fork it on day one. It runs as
a node subprocess; `npm --prefix tools/vendor/avoid-ai-writing test` runs upstream's own
suite against the vendored copy.

This is a SECOND gate, not a replacement. `script_style_gate` enforces TraderCockpit
doctrine (no predictions, no vague authority, no backstage narration). This one enforces
generic AI-ism -- the words and shapes in `.claude/skills/no-ai-slop/SKILL.md`, which until
now were prose an agent reads rather than code that blocks.

BLOCK vs WARN is a CATEGORY list, not a score threshold. The detector's 0-100 score is
normalised by log2(words/50) and has no meaning against our copy until it is baselined on a
corpus of ours; a made-up cutoff would be a number with no evidence behind it. Categories
are falsifiable one at a time: each entry in BLOCK_TYPES below fired zero times across
every shipped vo.txt and every approved social batch (see --survey), so a hit is new
information rather than the standing state of correct copy.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "vendor" / "avoid-ai-writing" / "runner.js"

# Near-dispositive tells: a single hit is evidence the text came out of a chatbot, or is
# unpublishable regardless of who wrote it. Measured against every shipped vo.txt and every
# approved social-batch item -- zero hits, so these do not red the lane on correct copy.
BLOCK_TYPES = {
    "chatbot": "chatbot pleasantry left in the copy",
    "sycophantic": "assistant-flattery register",
    "reasoning-artifact": "chain-of-thought narration left in the copy",
    "cutoff-disclaimer": "model self-identification or knowledge-cutoff text",
    "ai-placeholder": "unfilled [PLACEHOLDER] slot",
    "ai-citation-markup": "chatbot citation markup leaked through copy-paste",
    "ai-utm-source": "AI-tool tracking parameter on a URL",
    "normalization-flag": "zero-width or homoglyph chars typical of humanizer bypass tools",
    "vague-attribution": "unnamed source ('experts say', 'studies show')",
    "tier1": "always-flag AI vocabulary",
    "acknowledgment-loop": "restates the prompt back at the reader",
    "generic-conclusion": "closer with no falsifiable content",
    "future-narrative": "vague future-significance closer",
    "speculative-opener": "'imagine a world where' opener",
    "formulaic-opener": "LLM-default essay opener",
    "social-cta-closer": "engagement-bait sign-off",
    "hedge-stack": "modal stacked on a hedge adverb",
}

# Everything the detector can report that is NOT in BLOCK_TYPES warns instead. Two of them
# are demoted deliberately rather than by omission, because they DO fire on correct copy:
#
#   em-dash             -- every shipped daily script uses em dashes; TTS scripts are
#                          written for breath, and no-ai-slop allows 1-2 in longer drafts.
#   transition          -- "that said" and "notably" appear in shipped market copy.
#   confidence-calibration -- "significantly" is a legitimate market word ("volume was
#                          significantly above the 20-day average").
#   hollow-intensifier  -- overlaps script_style_gate's own editorial-marker rules.
#   filler / template-phrase / rhetorical-question / false-concession / tier2 / tier3 /
#   punct-distribution / cross-para-burstiness / fnword-trigram-entropy / low-ttr /
#   smart-punct-signature / uniformity / formatting / title-case-header /
#   parenthetical-hedge / emotional-flatline / novelty-inflation / significance-inflation /
#   lets-construction / real-actual-inflation / hashtag-stuff / bullet-np-list /
#   tier3-phrase*      -- density and stylometry signals. Real, but they are judgments about
#                          rhythm, and blocking on rhythm trains people to bypass the gate
#                          (the failure script_style_gate.py:445 already documents).
#
# Promote a WARN to BLOCK only after --survey shows it silent on shipped copy.

# Words `.claude/skills/no-ai-slop/SKILL.md:44` bans OUTRIGHT that the vendored detector only
# flags in clusters (its Tier 2) or does not carry at all. Without this the import would be a
# net LOOSENING of house doctrine on those words -- the ep02 failure, where a borrowed lexicon
# approved words the operator bans. Reconciled, not stacked: anything the detector already
# always-flags (delve, tapestry, robust, realm, beacon, meticulous, intricate, ever-evolving,
# leverage, utilize, embark) is left to the detector so there is one owner per word.
#
# `elevated` is deliberately NOT here. It fires in 4 of 109 known-good documents and every one
# is market vocabulary -- "volatility is elevated and still contained". The tell is the
# transitive verb ("elevate the experience"), so only the verb forms are banned.
HOUSE_BANNED = {
    "foster": "encourage, support, build",
    "fosters": "encourages, supports, builds",
    "fostering": "encouraging, supporting, building",
    "facilitate": "enable, help, allow",
    "facilitates": "enables, helps, allows",
    "empower": "enable, let, allow",
    "empowers": "enables, lets, allows",
    "streamline": "simplify, speed up",
    "streamlines": "simplifies, speeds up",
    "multifaceted": "describe the actual facets",
    "paramount": "most important, top priority",
    "transformative": "describe what changed",
    "elevate": "improve, raise, strengthen",
    "elevates": "improves, raises, strengthens",
    "elevating": "improving, raising, strengthening",
    "supercharge": "speed up, strengthen",
    "harness": "use, take advantage of",
    "harnesses": "uses, takes advantage of",
    "harnessing": "using, taking advantage of",
}
HOUSE_BANNED_PHRASES = {
    "paradigm shift": "describe what changed",
    "game changer": "describe what changed",
    "this is huge": "say what it does to a position",
    "this changes everything": "say what it changes",
}
_HOUSE_WORD_RE = re.compile(r"[a-z][a-z'-]*")


def _fail(detail: str) -> dict:
    """A gate that cannot inspect its input BLOCKS. Silence is never a pass."""
    return {
        "verdict": "BLOCK",
        "blocked": [{"type": "gate input", "count": 1, "detail": detail}],
        "warns": [],
        "metrics": {},
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def analyze(text: str, context_mode: str = "general") -> dict:
    """Raw detector output, or None if node could not run it."""
    node = shutil.which("node")
    if not node or not RUNNER.is_file():
        return None
    try:
        proc = subprocess.run([node, str(RUNNER), context_mode], input=text.encode("utf-8"),
                              capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def audit_text(text: str, context_mode: str = "general") -> dict:
    """Audit audience-facing copy. Same {verdict, blocked, warns} shape as script_style_gate."""
    if not text or not text.strip():
        return _fail("No audience-facing text was provided.")
    result = analyze(text, context_mode)
    if result is None:
        return _fail(f"Unable to run the vendored detector via node ({RUNNER}).")
    # 'Too short' (<10 words) is a real refusal to score, not a pass. Captions and hooks are
    # routinely under 10 words, so it must not BLOCK -- but it must be visible in the receipt
    # rather than reported as a clean scan.
    unscored = bool(result.get("tooShort") or result.get("tooLong"))

    blocked: list[dict] = []
    warns: list[dict] = []
    for issue_type, hits in _group(result.get("issues", [])).items():
        bucket, detail = (blocked, BLOCK_TYPES[issue_type]) if issue_type in BLOCK_TYPES \
            else (warns, "AI-writing pattern")
        bucket.append({
            "type": issue_type,
            "count": len(hits),
            "detail": detail,
            "examples": sorted({h.get("text", "") for h in hits})[:8],
            "suggestion": next((h["suggestion"] for h in hits if h.get("suggestion")), None),
        })
    house = _house_hits(text)
    if house:
        blocked.append({
            "type": "house-banned",
            "count": sum(house.values()),
            "detail": "words no-ai-slop bans outright that the detector only flags in clusters",
            "examples": sorted(house),
            "suggestion": "; ".join(f"{word} -> {HOUSE_BANNED.get(word) or HOUSE_BANNED_PHRASES[word]}"
                                    for word in sorted(house)),
        })
    blocked.sort(key=lambda item: -item["count"])
    warns.sort(key=lambda item: -item["count"])
    return {
        "verdict": "BLOCK" if blocked else "PASS",
        "blocked": blocked,
        "warns": warns,
        "metrics": {
            "words": result.get("stats", {}).get("wordCount", 0),
            "detectorScore": result.get("score", 0),
            "detectorLabel": result.get("label", ""),
            "classification": result.get("document_classification", "UNSCORED"),
            "unscored": unscored,
        },
        "detector": {"vendor": "conorbronsdon/avoid-ai-writing",
                     "version": (ROOT / "tools/vendor/avoid-ai-writing/VERSION")
                     .read_text(encoding="utf-8").split()[-1]},
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def _house_hits(text: str) -> dict[str, int]:
    """Occurrences of the outright-banned house words the detector would let through."""
    lowered = text.lower()
    hits = {word: count for word, count in
            ((word, sum(1 for token in _HOUSE_WORD_RE.findall(lowered) if token == word))
             for word in HOUSE_BANNED) if count}
    hits.update({phrase: lowered.count(phrase) for phrase in HOUSE_BANNED_PHRASES
                 if phrase in lowered})
    return hits


def _group(issues: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for issue in issues:
        grouped.setdefault(issue.get("type", "unknown"), []).append(issue)
    return grouped


def _read(target: Path) -> str:
    path = target / "vo.txt" if target.is_dir() else target
    text = path.read_text(encoding="utf-8")
    if path.name == "vo.txt":  # strip section headers, as script_style_gate does
        text = "\n".join(line for line in text.splitlines() if not line.startswith("## "))
    return text


def survey(paths: list[str]) -> int:
    """Tally every issue category the detector reports across known-good copy.

    This is the calibration instrument: a category that fires here is one the corpus says is
    normal in correct TraderCockpit copy, so it CANNOT be a BLOCK. Re-run it after any
    vendored-detector bump, and move anything new out of BLOCK_TYPES before shipping.
    """
    import collections
    tally: collections.Counter = collections.Counter()
    docs = 0
    for raw in paths:
        target = Path(raw)
        if not target.exists():
            continue
        try:
            text = _read(target)
        except (OSError, UnicodeDecodeError):
            continue
        result = analyze(text)
        if result is None:
            sys.exit("node could not run the vendored detector; cannot survey")
        docs += 1
        for issue_type in {issue.get("type") for issue in result.get("issues", [])}:
            tally[issue_type] += 1
        if _house_hits(text):  # the house list is part of the gate, so it is part of the survey
            tally["house-banned"] += 1
    print(f"surveyed {docs} known-good documents")
    for issue_type, count in tally.most_common():
        flag = "  <-- IN BLOCK_TYPES, would red the lane" if issue_type in BLOCK_TYPES else ""
        print(f"  {issue_type:26} fires in {count}/{docs}{flag}")
    armed = set(BLOCK_TYPES) | {"house-banned"}
    noisy = sorted(armed & set(tally))
    print(f"  BLOCK categories silent on all {docs}: {len(armed) - len(noisy)}/{len(armed)}")
    if noisy:
        print(f"  WOULD RED THE LANE: {', '.join(noisy)} -- demote or exempt before arming")
    return 1 if noisy else 0


def _selftest() -> None:
    """One runnable check: a known tell BLOCKS, real shipped copy does not."""
    slop = ("Certainly! Let me think step by step. In the rapidly evolving world of markets, "
            "experts say we must delve into the intricate tapestry of price action. "
            "I hope this helps! As of my last update, only time will tell.")
    report = audit_text(slop)
    assert report["verdict"] == "BLOCK", report
    types = {item["type"] for item in report["blocked"]}
    assert {"chatbot", "cutoff-disclaimer", "vague-attribution", "tier1"} <= types, types

    # The house list must catch what the detector alone would wave through: a SINGLE
    # outright-banned word, with no second Tier 2 word in the paragraph to form a cluster.
    single = ("Our research tools empower you to read the tape. The S&P closed at 6,340, "
              "down 0.8%. I care about 6,300 into Thursday's CPI print.")
    assert not any(issue["type"] in ("tier1", "tier2") for issue in analyze(single)["issues"]), \
        "detector is expected to miss a lone Tier 2 word -- that is why HOUSE_BANNED exists"
    house = audit_text(single)
    assert house["verdict"] == "BLOCK", house
    assert [item for item in house["blocked"] if item["type"] == "house-banned"], house

    clean = ("The S&P 500 closed at 6,340, down 0.8% on the day. Breadth was the tell: "
             "only 140 names finished green. I care about 6,300 -- lose it and the "
             "July trend line is gone. Watch Thursday's CPI print at 8:30 Eastern.")
    assert audit_text(clean)["verdict"] == "PASS", audit_text(clean)
    print("ai_writing_gate selftest: ok")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", nargs="*", help="file, or production dir containing vo.txt")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--survey", action="store_true", help="tally categories over known-good copy")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--out", type=Path, help="optional JSON receipt path")
    args = parser.parse_args()
    if args.selftest:
        _selftest()
        return 0
    if args.survey:
        return survey(args.target)
    if not args.target:
        parser.error("target is required")
    target = Path(args.target[0])
    try:
        report = audit_text(_read(target))
    except (OSError, UnicodeDecodeError) as exc:
        report = _fail(f"Unable to read {target}: {exc}")
    out_path = args.out or (target if target.is_dir() else target.parent) / "build" / "ai-writing-gate.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        metrics = report["metrics"]
        print(f"ai_writing_gate: {report['verdict']} -- {metrics.get('words', 0)} words, "
              f"detector score {metrics.get('detectorScore', 0)} "
              f"({metrics.get('detectorLabel', 'n/a')})")
        if metrics.get("unscored"):
            print("  detector declined to score this length; category rules still applied")
        for item in report["blocked"]:
            print(f"  BLOCK {item['type']}: x{item['count']} -- {item['detail']}")
            if item["examples"]:
                print(f"      {', '.join(item['examples'])}")
        for item in report["warns"]:
            print(f"  warn  {item['type']}: x{item['count']}")
        print(f"  report: {out_path}")
    return 1 if report["verdict"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
