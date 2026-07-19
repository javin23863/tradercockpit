#!/usr/bin/env python3
"""Warn when a voiceover draft drifts into generic AI-script habits."""
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path


PROCESS_PATTERNS = {
    "verification jargon": r"\b(?:verified|confirmed|receipt|claims? gate)\b",
    "edit-room narration": r"\b(?:earns? the cut|makes? the edit|in one frame|spoken copy)\b",
    "source-ownership metaphor": r"\b(?:chart|table|map|source) owns?\b",
}
SIGNPOST_PATTERNS = {
    "stock signposting": r"\b(?:let'?s break (?:it|this) down|here'?s what (?:matters|you need)|the real question is)\b",
    "corrective contrast": r"\b(?:not|isn'?t|is not)\b[^.!?]{0,90}\b(?:but|rather than|it'?s)\b",
}
EDITORIAL_MARKER = re.compile(
    r"\b(?:my read|my view|i think|i care|i want|i am|i can(?:not|'t)|i will|i'?m watching|i look|i see|i would|i refuse|allow me)\b",
    re.IGNORECASE,
)


def parse_voiceover(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    sections: list[str] = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current:
                sections.append(" ".join(current).strip())
            current = []
        elif not line.startswith("#") and line.strip():
            current.append(line.strip())
    if current:
        sections.append(" ".join(current).strip())
    if not sections:
        raise ValueError(f"no voiceover sections found in {path}")
    return sections


def _count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def audit_sections(sections: list[str]) -> dict:
    text = " ".join(sections)
    words = re.findall(r"[A-Za-z0-9']+", text)
    sentences = [
        re.findall(r"[A-Za-z0-9']+", sentence)
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if re.search(r"[A-Za-z]", sentence)
    ]
    lengths = [len(sentence) for sentence in sentences]
    metrics = {
        "words": len(words),
        "sections": len(sections),
        "sentences": len(lengths),
        "sentenceWordsMean": round(statistics.mean(lengths), 2) if lengths else 0,
        "sentenceWordsStdDev": round(statistics.pstdev(lengths), 2) if lengths else 0,
        "firstPersonEditorialMarkers": len(EDITORIAL_MARKER.findall(text)),
        "pressureChainMentions": _count(r"\bpressure chains?\b", text),
        "sirenMentions": _count(r"\bsirens?\b", text),
    }
    warnings: list[dict] = []

    for label, pattern in PROCESS_PATTERNS.items():
        count = _count(pattern, text)
        if count:
            warnings.append({"rule": label, "count": count, "guidance": "Keep production and provenance backstage."})

    stock_count = _count(SIGNPOST_PATTERNS["stock signposting"], text)
    if stock_count > 1:
        warnings.append({"rule": "stock signposting", "count": stock_count, "guidance": "Lead with the fact or take."})

    contrast_count = _count(SIGNPOST_PATTERNS["corrective contrast"], text)
    if contrast_count > 1:
        warnings.append({"rule": "corrective contrast", "count": contrast_count, "guidance": "Use direct positive statements; keep at most one earned correction."})

    if metrics["pressureChainMentions"] > 2 or metrics["sirenMentions"] > 2 or (
        metrics["pressureChainMentions"] + metrics["sirenMentions"] > 3
    ):
        warnings.append({
            "rule": "slogan repetition",
            "count": metrics["pressureChainMentions"] + metrics["sirenMentions"],
            "guidance": "A signature line should land once, not become the script's vocabulary.",
        })

    if len(words) >= 800 and not metrics["firstPersonEditorialMarkers"]:
        warnings.append({"rule": "missing editorial owner", "count": 0, "guidance": "Add a defensible first-person market judgment."})

    if lengths and metrics["sentenceWordsMean"] >= 12 and metrics["sentenceWordsStdDev"] < 6:
        warnings.append({"rule": "uniform sentence rhythm", "count": metrics["sentenceWordsStdDev"], "guidance": "Mix short spoken beats with longer explanations."})

    return {
        "schema": "tradercockpit-script-style-audit/v1",
        "status": "WARN" if warnings else "PASS",
        "metrics": metrics,
        "warnings": warnings,
        "policy": "Advisory only. Never rewrite or mutate facts, numbers, names, quotations, or causal direction.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("voiceover", type=Path, help="vo.txt or a production directory containing vo.txt")
    parser.add_argument("--out", type=Path, help="optional JSON receipt path")
    args = parser.parse_args()
    voiceover = args.voiceover / "vo.txt" if args.voiceover.is_dir() else args.voiceover
    try:
        result = audit_sections(parse_voiceover(voiceover))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
