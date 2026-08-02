#!/usr/bin/env python3
"""Assert an episode's packaging against the VAULT Production Standard, read live.

WHY THIS EXISTS. On 2026-07-28 the operator rejected four consecutive titles and named the cause:
"you not following the skills in the playbook in the obsidian vault... whatever is inside your MD
files that are causing you to skip these skills". It was measurable, not attitudinal.

`GTM/Social-Media-Library/Into the Laboratory - Production Standard.md` section (a) carries SEVEN
title rules, led by a formula:

    [famous beginner strategy] x [what this phase reveals], as a curiosity-gap debunk
    reference: "I Optimised the Golden Cross. That Was the Mistake."
    (a)1 Phase labels are the syllabus, NOT titles.

`~/.claude/skills/into-the-laboratory/SKILL.md` stage 3 -- the whole packaging stage -- carried ONE
of them: "Title and thumbnail share zero words." That is (a)3. The formula, the phase-label ban and
the char limit were absent. The skill is auto-loaded into context and the vault document is not, so
the lossy copy won every time. Ep01 was written against the vault and follows the formula; ep02,
ep03 and ep04 do not.

THE FIX IS THE PATTERN THAT ALREADY WORKS HERE. `term_gate.py` parses the syllabus LIVE and asserts
the script against it, which is why the teaching contract holds while the packaging doctrine did
not. This does the same for the Production Standard: every threshold below is READ OUT OF THE VAULT
DOCUMENT, never transcribed. If the standard moves, this gate moves with it. If the document is
missing or unparseable, this BLOCKS -- a gate that cannot find its own source is not a pass.

WHAT IT DELIBERATELY DOES NOT DO. It cannot judge whether a curiosity gap is any good, and it must
not pretend to. Section (b)3 says the same of `thumb_gate`: it renders the squint image and tells
you to look at it rather than claiming a file-size check can see a promise. The checkable half is
length, overlap, vocabulary, ordering and the phase-label ban.

    py tools/packaging_gate.py <path/to/packaging.json>
    py tools/packaging_gate.py --demo        # must REJECT the known-bad fixture
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(r"C:\Users\MSI\Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit")
STANDARD = VAULT / "GTM" / "Social-Media-Library" / "Into the Laboratory — Production Standard.md"

# Phase labels are the syllabus, never titles -- (a)1. Sourced from the pipeline's own phase
# labels rather than invented here.
PHASE_LABELS = ("out-of-sample", "out of sample", "in-sample", "intake", "cost stress",
                "timing", "session stress", "monte carlo", "walk-forward", "walk forward",
                "governance", "mc param", "mc trade", "final oos", "oos retest", "perturbation")

# (a)1's carve-out, AMENDED 2026-07-30. These are the method names a beginner actually types into
# search, so they may lead a title -- but only alongside a concrete result. The rest of
# PHASE_LABELS stay syllabus language whatever else the title says.
PUBLIC_METHODS = ("monte carlo", "walk-forward", "walk forward", "out-of-sample",
                  "out of sample", "in-sample", "in sample")

# An internal phase code never qualifies for the carve-out, with or without a number attached:
# `phase06_mc_param`, "Phase 6". The amendment is a search-intent exception, not permission to
# title an episode with its pipeline label.
INTERNAL_CODE = re.compile(r"phase[\s_-]*\d", re.I)

STOPWORDS = {"a", "an", "the", "and", "or", "but", "of", "to", "in", "on", "at", "for", "with",
             "is", "was", "it", "its", "this", "that", "my", "i", "you", "your", "me", "we",
             "he", "she", "they", "them", "from", "by", "as", "so", "then", "than", "next",
             "not", "no", "did", "do", "does", "had", "has", "have", "be", "been", "am", "are"}


TOKEN = r"[\w$%,.-]+"     # one on-screen word; keeps $78,420 and -$9,229 whole


def die(msg: str) -> None:
    raise SystemExit(f"BLOCK: {msg}")


def standard_text() -> str:
    if not STANDARD.is_file():
        die(f"Production Standard not found at {STANDARD}\n"
            "       This gate reads the vault document live and has nothing to check without it.")
    return STANDARD.read_text(encoding="utf-8")


def rules(text: str) -> dict:
    """Pull the numeric rules OUT OF THE DOCUMENT. Never transcribe a threshold."""
    out = {}
    m = re.search(r"≤\s*(\d+)\s*chars", text)
    out["max_title_chars"] = int(m.group(1)) if m else None

    m = re.search(r"\*\*(\d+)[–-](\d+)\s*visual elements max", text)
    out["thumb_elements"] = (int(m.group(1)), int(m.group(2))) if m else None

    m = re.search(r"Text\s+(\d+)[–-](\d+)\s*words", text)
    out["thumb_words"] = (int(m.group(1)), int(m.group(2))) if m else None

    out["zero_shared"] = bool(re.search(r"zero shared words", text, re.I))
    out["formula"] = bool(re.search(r"famous beginner strategy", text, re.I))
    # AMENDED 2026-07-28: the left side may be a BELIEF when the phase tests a field rather than a
    # named strategy. Detected from the document, so the gate follows the standard rather than a
    # constant here -- revert the amendment and this check tightens again by itself.
    out["belief_allowed"] = bool(re.search(r"famous beginner belief", text, re.I))
    # AMENDED 2026-07-30: a searched public method name may lead a title when that same title
    # states a concrete, receipt-backed result. Detected from the document like the 07-28 belief
    # amendment, so reverting the amendment tightens (a)1 back by itself.
    out["method_needs_result"] = bool(re.search(r"[Ss]earched public method names?", text))
    out["phase_labels_banned"] = bool(re.search(r"Phase labels are the syllabus, NOT titles", text))
    out["package_before_script"] = bool(re.search(r"Package BEFORE the script", text, re.I))

    optional = {"belief_allowed", "method_needs_result"}
    missing = [k for k, v in out.items()
               if k not in optional and (v is None or v is False)]
    if missing:
        die("the Production Standard no longer states: " + ", ".join(missing) +
            "\n       Either section (a)/(b) was edited or this parser is stale. "
            "Fix the parser against the document; do not weaken the gate.")
    return out


def strategy_vocab() -> set[str]:
    """The formula's left-hand side, sourced from the series docs rather than invented here.

    Grows with the series: add a strategy to the syllabus and it becomes a legal title subject.
    """
    docs = (Path(__file__).resolve().parents[1] / "OpenMontage" / "projects" /
            "series-01-backtest-is-not-a-strategy" / "docs")
    names = {"golden cross", "death cross", "moving average", "crossover", "rsi", "macd",
             "bollinger", "breakout", "donchian", "mean reversion", "turtle", "ichimoku",
             "stochastic", "ema", "sma", "pivot", "支"}
    found = set()
    if docs.is_dir():
        blob = " ".join(p.read_text(encoding="utf-8", errors="ignore").lower()
                        for p in docs.glob("*.md"))
        found = {n for n in names if n in blob}
    return found or names


def words(s: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9']+", s.lower()) if w not in STOPWORDS}


def has_result(title: str) -> bool:
    """(a)'s 2026-07-30 carve-out wants a concrete result alongside the method name.

    The checkable half is that a number is present at all, and that it is not merely the digits
    of an internal phase code. Whether the number is receipt-backed is (a)4's earned-claim gate
    and the claims gates -- not something a string check can have.
    """
    return bool(re.search(r"\d", INTERNAL_CODE.sub(" ", title)))


def audit(pk: dict, proj: Path | None, r: dict, vocab: set[str]) -> list[tuple[str, bool, str]]:
    title = str(pk.get("title", ""))
    thumb = pk.get("thumbnail", {}) or {}
    elements = [str(e) for e in (thumb.get("elements") or [])]
    tw = words(title)
    thw = set().union(*[words(e) for e in elements]) if elements else set()
    lo, hi = r["thumb_elements"]
    wlo, whi = r["thumb_words"]
    status = str(pk.get("STATUS", ""))

    # AMENDED 2026-07-30. A searched public method name may lead the title when the title also
    # states a concrete result -- that is what makes it a search-intent exception rather than a
    # bare topic label ("Monte Carlo explained"). An internal phase code is never exempt.
    internal = INTERNAL_CODE.search(title)
    label_hits = [p for p in PHASE_LABELS if p in title.lower()]
    method_hits = [p for p in PUBLIC_METHODS if p in title.lower()]
    method_exempt = (r["method_needs_result"] and bool(method_hits)
                     and has_result(title) and not internal)
    strategy_hits = sorted(v for v in vocab if v in title.lower())
    belief = r["belief_allowed"] and bool(pk.get("beginner_belief"))

    checks = [
        (f"(a)6 title max {r['max_title_chars']} chars",
         0 < len(title) <= r["max_title_chars"],
         f"{len(title)} chars"),

        ("(a) FORMULA — strategy, belief, or searched method + result",
         bool(strategy_hits) or belief or method_exempt,
         ("strategy: " + ", ".join(strategy_hits)) if strategy_hits else
         (f"belief: {pk['beginner_belief']!r}" if belief else
          ("searched method + result: " + ", ".join(method_hits)) if method_exempt else
          "NONE — name a beginner strategy in the title, or (amended 2026-07-28) declare the "
          "beginner belief this title debunks in a `beginner_belief` field, or (amended "
          "2026-07-30) lead with a searched public method name AND a concrete result")),

        ("(a)1 title is not a phase label",
         not label_hits and not internal if not method_exempt else not internal,
         (f"internal phase code: {internal.group(0)!r} — never exempt, (a)1 stands") if internal
         else ("searched method + result, exempt 2026-07-30: " + ", ".join(method_hits))
         if method_exempt
         else ("bare topic label: " + ", ".join(method_hits) + " — the 2026-07-30 carve-out "
               "needs a concrete result in the same title") if method_hits
         else "hits: " + (", ".join(label_hits) or "none")),

        ("(a)3 title and thumbnail share zero words",
         not (tw & thw),
         "shared: " + (", ".join(sorted(tw & thw)) or "none")),

        (f"(b)2 thumbnail has {lo}-{hi} elements",
         lo <= len(elements) <= hi,
         f"{len(elements)}"),

        # (b)6 is the thumbnail's TOTAL text, not a per-element budget. The --demo caught this:
        # the standard's own ep01 example is two 2-word elements, which a per-element floor of 3
        # rejects. A gate that fails the document's own reference is measuring the wrong thing.
        (f"(b)6 thumbnail text {wlo}-{whi} words TOTAL",
         wlo <= sum(len(re.findall(TOKEN, e)) for e in elements) <= whi,
         f"{sum(len(re.findall(TOKEN, e)) for e in elements)} words across "
         f"{len(elements)} element(s)"),

        ("(c)2 first sentence matches the title",
         bool(pk.get("first_spoken_sentence")) and
         len(words(str(pk["first_spoken_sentence"])) & tw) >= max(1, len(tw) // 3),
         "overlap " + str(len(words(str(pk.get("first_spoken_sentence", ""))) & tw)) +
         f" of {len(tw)} title words"),
    ]

    # (b)1 / (c)1 -- package BEFORE the script, checked mechanically rather than trusted.
    if proj is not None:
        vo = proj / "artifacts" / "vo.txt"
        checks.append((
            "(b)1 package BEFORE the script",
            not (vo.is_file() and "PROPOSED" in status.upper()),
            "vo.txt exists while STATUS is still PROPOSED" if
            (vo.is_file() and "PROPOSED" in status.upper()) else "ok"))
    return checks


BAD_FIXTURE = {
    "STATUS": "PROPOSED 2026-07-27 — awaiting operator approval",
    "title": "Out-of-Sample Retest: The Cost Stress Phase Explained In Detail For Beginners Who Want To Learn",
    "first_spoken_sentence": "Today we discuss something completely different.",
    "thumbnail": {"elements": ["OUT-OF-SAMPLE", "RETEST", "THE COST STRESS PHASE", "AND MORE"]},
}
GOOD_FIXTURE = {   # ep01, quoted by the standard itself at (a) and (b)2
    "STATUS": "APPROVED",
    "title": "I Optimised the Golden Cross. That Was the Mistake.",
    "first_spoken_sentence": "I optimised the golden cross, and that was the mistake.",
    "thumbnail": {"elements": ["$78,420 → −$9,229", "SAME STRATEGY"]},
}
# ep05, operator-approved 2026-07-30. The amendment exists so that this can pass; before it was
# implemented here the gate BLOCKED this title on (a)1 and (a) FORMULA. A ruling that only the
# document knows about is prose, and prose does not gate.
METHOD_FIXTURE = {
    "STATUS": "APPROVED",
    "title": "Monte Carlo Backtest: We Moved the Exits. 28 of 46 Failed.",
    "first_spoken_sentence": "We moved the exits on 46 strategies, and 28 of them failed.",
    "thumbnail": {"elements": ["200 EACH", "18 LEFT"]},
}
# Same method name, no result. This is the "Monte Carlo explained" shape the amendment still bans,
# and it is what stops the carve-out from being read as "phase labels are fine now".
BARE_TOPIC_FIXTURE = {
    "STATUS": "APPROVED",
    "title": "Monte Carlo Backtest Explained",
    "first_spoken_sentence": "Monte carlo backtest, explained.",
    "thumbnail": {"elements": ["200 EACH", "18 LEFT"]},
}
# A number does not launder an internal phase code -- the exception is search intent, not digits.
PHASE_CODE_FIXTURE = {
    "STATUS": "APPROVED",
    "title": "Phase 6: We Moved the Exits. 28 of 46 Failed.",
    "first_spoken_sentence": "We moved the exits on 46 strategies, and 28 of them failed.",
    "thumbnail": {"elements": ["200 EACH", "18 LEFT"]},
}


def run(pk: dict, proj: Path | None, label: str) -> int:
    r = rules(standard_text())
    checks = audit(pk, proj, r, strategy_vocab())
    print(f"{label}\n  title: {pk.get('title','')!r}\n")
    for name, ok, detail in checks:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name:44s} {detail}")
    bad = [n for n, ok, _ in checks if not ok]
    print()
    if bad:
        print(f"BLOCK: {len(bad)} of {len(checks)} packaging rules fail.")
        print(f"       Source: {STANDARD.name} (a)/(b) - read it, do not guess.")
        return 1
    print(f"PASS — all {len(checks)} checkable packaging rules hold.")
    print("NOTE: whether the curiosity gap actually works is NOT checkable here. "
          "Squint-test the thumbnail and read (a)2 yourself.")
    return 0


def demo() -> int:
    print("packaging_gate --demo — the gate must be able to say otherwise\n")
    r = rules(standard_text())
    vocab = strategy_vocab()

    def fails(fx: dict) -> list[str]:
        return [n for n, ok, _ in audit(fx, None, r, vocab) if not ok]

    # (fixture, must_fail, why it is in here)
    cases = (
        (BAD_FIXTURE, True, "known-BAD — violates (a) wholesale"),
        (GOOD_FIXTURE, False, "ep01 — the standard's own reference at (a) and (b)2"),
        (METHOD_FIXTURE, False, "ep05 — operator-approved under the 2026-07-30 amendment"),
        (BARE_TOPIC_FIXTURE, True, "same method name, NO result — still a bare topic label"),
        (PHASE_CODE_FIXTURE, True, "internal phase code + a result — still banned"),
    )
    verdicts = []
    for fx, must_fail, why in cases:
        f = fails(fx)
        agreed = bool(f) == must_fail
        verdicts.append(agreed)
        print(f"  {'ok  ' if agreed else 'VOID'}  {'must FAIL' if must_fail else 'must PASS'}  "
              f"{fx['title'][:52]!r}\n        {why}\n        -> {len(f)} failure(s): "
              f"{', '.join(f) or 'NONE'}")

    if not all(verdicts):
        print("\nBLOCK: the gate disagreed with a fixture whose verdict is already settled. "
              "A gate that cannot separate these is not measuring the rule.")
        return 1
    print("\n  Gate trusted: it rejects bad packaging, accepts the standard's own example, and "
          "\n  separates the 2026-07-30 method-name carve-out from a bare topic label and a "
          "phase code.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("packaging", nargs="?", type=Path)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        return demo()
    if not a.packaging:
        ap.error("give a packaging.json, or --demo")
    if not a.packaging.is_file():
        die(f"{a.packaging} not found")
    pk = json.loads(a.packaging.read_text(encoding="utf-8"))
    proj = a.packaging.resolve().parents[1]
    return run(pk, proj, str(a.packaging))


if __name__ == "__main__":
    sys.exit(main())
