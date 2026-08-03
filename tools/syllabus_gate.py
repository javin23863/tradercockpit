#!/usr/bin/env python3
"""Fail-closed E03 syllabus contract gate.

The repository previously named this gate without shipping it.  This narrow implementation
reads the live syllabus and phase sources, then checks the E03 candidate against both.  It is
not a replacement for creative approval; it prevents a missing syllabus contract or a stale
phase mapping from reading as green.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Keep the documented ``py tools/syllabus_gate.py ...`` invocation importable even though
# ``tools`` is a source directory rather than an installed package.
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.build_e03_timing_session_rebuild import (
    EXPECTED_PHASE_SHA256,
    PHASE_CODE,
    PHASE_SOURCE,
    SYLLABUS_SOURCE,
    assert_phase03_truth,
    derive_phase03_facts,
    sha256,
)


REQUIRED_TERMS = ("fill", "slippage", "latency", "split sample", "session half", "regime", "profit factor")
FORBIDDEN_LATER_RESULT = re.compile(
    r"53\s*(?:→|->|to)\s*46|\b7\s*/\s*2\b|\b7\s+(?:fail|failed|failures)\b|\b46\s+(?:clear|pass|passed)\b",
    re.I,
)


def syllabus_section(text: str) -> str:
    match = re.search(r"^##\s*Ep03\b.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not match:
        raise SystemExit("BLOCK: live syllabus has no Ep03 section")
    return match.group(1)


def term_contract(section: str) -> list[str]:
    match = re.search(r"\*\*Terms defined\.?\*\*(.*?)(?:\n\s*\n)", section, re.S)
    if not match:
        raise SystemExit("BLOCK: Ep03 has no Terms defined contract")
    terms = [part.strip(" .") for part in re.sub(r"[*`]", "", match.group(1)).replace("\n", " ").split("·") if part.strip(" .")]
    return terms


def spoken(vo: str) -> str:
    return " ".join(
        line.strip()
        for line in vo.splitlines()
        if line.strip() and not line.lstrip().startswith("#") and not line.startswith("===") and not line.startswith("##")
    )


def run(episode: Path, phase_source: Path, syllabus: Path) -> int:
    for path in (episode / "vo.txt", episode / "packaging.json", phase_source, PHASE_CODE, syllabus):
        if not path.is_file():
            raise SystemExit(f"BLOCK: syllabus gate input missing: {path}")

    phase_sha = sha256(phase_source)
    if phase_sha != EXPECTED_PHASE_SHA256:
        raise SystemExit(f"BLOCK: phase03 source hash {phase_sha} != {EXPECTED_PHASE_SHA256}")
    facts = derive_phase03_facts(json.loads(phase_source.read_text(encoding="utf-8")))
    assert_phase03_truth(facts)

    syllabus_text = syllabus.read_text(encoding="utf-8")
    section = syllabus_section(syllabus_text)
    terms = term_contract(section)
    missing_contract_terms = [term for term in REQUIRED_TERMS if not any(term in item.lower() for item in terms)]
    if missing_contract_terms:
        raise SystemExit(f"BLOCK: live Ep03 syllabus dropped terms: {missing_contract_terms}")

    body = spoken((episode / "vo.txt").read_text(encoding="utf-8"))
    missing_terms = [term for term in REQUIRED_TERMS if not re.search(rf"\b{re.escape(term)}\b", body, re.I)]
    if missing_terms:
        raise SystemExit(f"BLOCK: E03 VO misses syllabus terms: {missing_terms}")
    if FORBIDDEN_LATER_RESULT.search(body) or FORBIDDEN_LATER_RESULT.search((episode / "packaging.json").read_text(encoding="utf-8")):
        raise SystemExit("BLOCK: E03 contains a later phase04 payoff/result")
    code = PHASE_CODE.read_text(encoding="utf-8")
    code_checks = {
        "one-bar delay": "entry decisions delayed by one extra bar" in code,
        "median-hour split": "median entry hour" in code,
        "three PF gates": "pf_entry_delay_1bar" in code and "pf_session_half_1" in code and "pf_session_half_2" in code,
    }
    if not all(code_checks.values()):
        raise SystemExit(f"BLOCK: phase03 methodology contract drifted: {code_checks}")

    package = json.loads((episode / "packaging.json").read_text(encoding="utf-8"))
    checks = {
        "syllabus_episode": package.get("syllabus_episode") == "03",
        "title": package.get("title") == "154 Entered. 101 Failed. 53 Cleared Every Check.",
        "phase_source_sha256": package.get("evidence", {}).get("phase03_source_sha256") == EXPECTED_PHASE_SHA256,
        "validated_false": package.get("evidence", {}).get("validation_status") is False,
        "real_data": package.get("evidence", {}).get("real_data") is True,
        "wiring_proof": package.get("evidence", {}).get("wiring_proof") is True,
    }
    if not all(checks.values()):
        raise SystemExit(f"BLOCK: package does not carry the live E03 contract: {checks}")
    print(json.dumps({
        "verdict": "PASS",
        "phase03_sha256": phase_sha,
        "terms": terms,
        "counts": {"entering": len(facts["candidate_ids"]), "unique_failures": facts["unique_failures"], "surviving": facts["surviving"]},
        "mapping": facts["failure_counts"],
        "methodology": code_checks,
        "package": checks,
    }, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", type=Path)
    parser.add_argument("--phase-source", type=Path, default=PHASE_SOURCE)
    parser.add_argument("--syllabus", type=Path, default=SYLLABUS_SOURCE)
    args = parser.parse_args()
    return run(args.episode.resolve(), args.phase_source, args.syllabus)


if __name__ == "__main__":
    raise SystemExit(main())
