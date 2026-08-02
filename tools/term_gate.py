#!/usr/bin/env python3
"""Require every syllabus term to appear in the selected episode's spoken VO."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYLLABUS = (
    ROOT / "OpenMontage" / "projects" / "series-01-backtest-is-not-a-strategy"
    / "docs" / "syllabus.md"
)
ALIASES = {
    "gross win/loss": [r"\bgross wins?\b.*?\bgross losses?\b"],
    "frozen parameters": [r"frozen\b", r"\bfreeze the parameters?\b"],
    "warmup bars": [r"warm-?up\s+bars?\b", r"\bwarm-?up\b"],
    "curve-fitting": [r"curve[\s-]?fit(?:ting|ted)?\b"],
    "in-sample (repeat)": [r"in-sample\b"],
    "profit factor (repeat)": [r"profit factor\b"],
    "walk-forward (named, deferred to ep07 by *definition only*, not by content)":
        [r"walk-?forward\b"],
}
DEFINITIONAL = re.compile(
    r"(?:is called|are called|that's|that is|which means|which is|is when|means\b|"
    r"\bha(?:s|ve) a name\b|\bwhen I say\b|\bcomes down to\b|"
    r"\bcall (?:it|this|that)\b|\bis the\b|\bis a\b|\bare the\b|"
    r"[—:]\s+(?:the|a|an)\b)", re.I)


def episode_terms(syllabus: Path, episode: str) -> list[str]:
    if not syllabus.is_file():
        raise SystemExit(f"BLOCK: syllabus not found at {syllabus}")
    text = syllabus.read_text(encoding="utf-8")
    section = re.search(rf"^##\s*Ep{episode}\b.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not section:
        raise SystemExit(f"BLOCK: no '## Ep{episode}' section in {syllabus.name}")
    terms = re.search(r"\*\*Terms defined\.?\*\*(.*?)(?:\n\s*\n)", section.group(1), re.S)
    if not terms:
        raise SystemExit(f"BLOCK: Ep{episode} has no '**Terms defined.**' contract")
    raw = re.sub(r"[*`]", "", terms.group(1)).replace("\n", " ")
    return [part.strip(" .") for part in raw.split("·") if part.strip(" .")]


def spoken(vo: Path) -> str:
    if not vo.is_file():
        raise SystemExit(f"BLOCK: {vo} missing")
    keep, on = [], False
    for line in vo.read_text(encoding="utf-8").splitlines():
        if re.match(r"===\s*SLOT", line):
            on = True
            continue
        if on and not line.strip().startswith("#"):
            keep.append(re.sub(r"\[[^\]]*\]", " ", line))
    return " ".join(keep)


def patterns_for(term: str) -> list[str]:
    if term in ALIASES:
        return ALIASES[term]
    core = re.sub(r"\s*\(.*?\)\s*", "", term).strip()
    words = [re.escape(word) for word in re.split(r"[\s-]+", core) if word]
    return [r"\b" + r"[\s-]+".join(words) + r"\b"]


def check(text: str, terms: list[str]) -> list[tuple[str, bool, bool]]:
    rows = []
    for term in terms:
        hits = [match for pattern in patterns_for(term)
                for match in re.finditer(pattern, text, re.I | re.S)]
        defined = any(
            DEFINITIONAL.search(text[max(0, hit.start() - 120):hit.end() + 120])
            for hit in hits
        )
        rows.append((term, bool(hits), defined))
    return rows


def demo() -> int:
    text = ("Gross wins are every winner added together. Gross losses are every loser added "
            "together. Max drawdown is the largest peak-to-trough fall. The strategy was "
            "tested in-sample.")
    rows = check(text, ["gross win/loss", "max drawdown", "in-sample", "profit factor"])
    assert [(term, present) for term, present, _ in rows] == [
        ("gross win/loss", True),
        ("max drawdown", True),
        ("in-sample", True),
        ("profit factor", False),
    ]
    named = check(
        "Moving a setting has a name: perturbation. "
        "A grid edge — the highest or lowest setting tested — is a search boundary.",
        ["perturbation", "grid edge"],
    )
    assert all(present and defined for _, present, defined in named), named
    explained = check(
        "When I say the parameters are frozen, it comes down to every number being saved. "
        "Those first bars have a name of their own: warmup bars.",
        ["frozen parameters", "warmup bars"],
    )
    assert all(present and defined for _, present, defined in explained), explained
    print("term_gate self-check ok")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--production", type=Path)
    ap.add_argument("--episode", required=False, default="01")
    ap.add_argument("--syllabus", type=Path, default=DEFAULT_SYLLABUS)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--demo", action="store_true")
    args = ap.parse_args()
    if args.demo:
        return demo()
    if args.production is None:
        ap.error("--production is required")
    vo = args.production / "artifacts" / "vo.txt"
    terms = episode_terms(args.syllabus, args.episode)
    rows = check(spoken(vo), terms)
    print(f"ep{args.episode} teaching contract: {len(terms)} term(s)")
    for term, present, defined in rows:
        note = "" if not present or defined else " (mentioned, no definitional cue)"
        print(f"  {'ok  ' if present else 'MISS'}  {term}{note}")
    missing = [term for term, present, _ in rows if not present]
    undefined = [term for term, present, defined in rows if present and not defined]
    if missing:
        print(f"BLOCK — {len(missing)} required term(s) are never spoken: "
              + ", ".join(missing))
        return 1
    if args.strict and undefined:
        print(f"BLOCK (--strict) — {len(undefined)} term(s) lack a definitional cue: "
              + ", ".join(undefined))
        return 1
    print(f"PASS — all {len(terms)} contract terms are spoken.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
