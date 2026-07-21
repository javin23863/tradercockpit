#!/usr/bin/env python3
"""Fail-closed deterministic style gate for voiceover and social copy."""
from __future__ import annotations

import argparse
import itertools
import json
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path


PROCESS_PATTERNS = {
    "verification jargon": r"\b(?:verified|confirmed|receipt|claims? gate)\b",
    "edit-room narration": r"\b(?:earns? the cut|makes? the edit|in one frame|spoken copy"
                           r"|on (?:the )?screen|as you can see|you can see (?:it|the)"
                           r"|the (?:headline|chart|page) you'?re looking at"
                           r"|straight (?:from|off) the chart|charts? you (?:just )?saw"
                           r"|pull up [a-z]|showing you the)\b",
    "source-ownership metaphor": r"\b(?:chart|table|map|source) owns?\b",
    # Operator 2026-07-21: "The S&P 500 is the S&P 500. It's not the referee." Instruments keep
    # their names — no assigned personas/nicknames. Extend this list when a new one ships.
    "instrument persona": r"\b(?:referee|umpire|fear gauge|honesty check|quiet number)\b",
}
STOCK_SIGNPOST_RE = re.compile(
    r"\b(?:let'?s break (?:it|this) down|here'?s what (?:matters|you need)|the real question is)\b",
    re.IGNORECASE,
)
CORRECTIVE_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"\bless about\b[^.!?]{1,90}\bthan\b",
    r"\bnot merely\b[^.!?]{1,90}\b(?:but|rather|instead)\b",
    # Contractions matter: the shipped 2026-07-20 violation was "That's not an edge, that's a
    # rounding error" — an apostrophe-s, not the literal "that is". Without this the counter
    # returned 1 on copy containing three corrective contrasts, and the cluster rule below
    # never fired because it needs two detected contrasts to see a cluster.
    r"\b(?:isn'?t|is not|are not|was not|were not|not)\b[^.!?]{0,90}"
    r"(?:\bbut\b|\brather than\b|\binstead\b|--|—|,\s*(?:that|this|it)(?:'s|\s+(?:is|are|was|were))\b)",
    r"\b(?:isn'?t|is not|are not|was not|were not)\b[^.!?]{0,90}[.!?]\s+"
    r"[A-Z][^.!?]{0,70}\b(?:is|are|was|were)\b(?:[.!?]|$)",
    # Operator 2026-07-21 second review: "if it's not this, it's that" — the negate-then-replace
    # template is an AI-tell. Trailing appositive ("priced, not panicked."), cross-sentence
    # replace ("that is not X. That is Y"), and dash-replace ("isn't X anymore — it's Y").
    # (?!financial) exempts the mandated disclaimer "Research tooling, not financial advice."
    r",\s*not\s+(?!financial\b)[a-z][^.!?]{0,40}[.!?]",
    r"\b(?:is|are|was|were)\s+not\b[^.!?]{0,60}[.!?]\s+(?:That|This|It)\s+(?:is|was)\b",
    r"\bisn'?t\b[^.!?]{0,60}[—-]\s*it'?s\b",
    r"\bwasn'?t\b[^.!?]{0,60},\s*it\s+was\b",
))
VAGUE_AUTHORITY_PATTERNS = {
    "analysts say": r"\banalysts? (?:say|said|believe|expect)\b",
    "experts believe": r"\bexperts? (?:say|believe|expect)\b",
    "markets are watching": r"\bmarkets? (?:are|is) watching\b",
    "many observers": r"\bmany observers?\b",
    "widely expected": r"\b(?:it is|it'?s) widely expected\b",
}
PREDICTIVE_PATTERNS = {
    "will go to": re.compile(r"\bwill\s+go\s+to\b", re.IGNORECASE),
    "will hit": re.compile(r"\bwill\s+hit\b", re.IGNORECASE),
    "will reach": re.compile(r"\bwill\s+reach\b", re.IGNORECASE),
    "expect X by": re.compile(r"\bexpect\b[^.!?\n]{1,80}\bby\b", re.IGNORECASE),
    "is going to": re.compile(r"\bis\s+going\s+to\b", re.IGNORECASE),
    "target of": re.compile(r"\btarget\s+of\b", re.IGNORECASE),
    "should reach": re.compile(r"\bshould\s+reach\b", re.IGNORECASE),
    "my target is": re.compile(r"\bmy\s+target\s+is\b", re.IGNORECASE),
}
SUMMARY_RE = re.compile(r"\b(?:in summary|to sum up|the bottom line is)\b", re.IGNORECASE)
ANNOUNCEMENT_RE = re.compile(
    r"^\s*(?:in this (?:video|episode)|today (?:we|i)(?:'re| are|'m| am)?|welcome back|"
    r"let'?s break (?:it|this) down|here'?s what (?:matters|you need)|we need to talk about)\b",
    re.IGNORECASE,
)
CTA_RE = re.compile(
    r"^\s*(?:follow|subscribe|watch|read|visit|download|join|sign up|learn more|full breakdown|"
    r"link\b|https?://|#)",
    re.IGNORECASE,
)
DISCLAIMER_RE = re.compile(
    r"^\s*Research\s+tooling,\s*not\s+financial\s+advice\.\s*"
    r"No\s+performance\s+is\s+promised\s+or\s+implied\.\s*$",
    re.IGNORECASE,
)
EDITORIAL_MARKER = re.compile(
    r"\b(?:my read|my view|i think|i care|i want|i am|i can(?:not|'t)|i will|i'?m watching|"
    r"i look|i see|i would|i refuse|allow me)\b",
    re.IGNORECASE,
)
TRIPLET_RE = re.compile(
    r"\b([A-Za-z][A-Za-z'-]*(?:\s+[a-z][A-Za-z'-]*)?),\s+"
    r"([a-z][A-Za-z'-]*(?:\s+[a-z][A-Za-z'-]*)?)(?:,\s*|\s+)"
    r"(?:and|or)\s+([a-z][A-Za-z'-]*(?:\s+[a-z][A-Za-z'-]*)?)\b"
)
DATE_CATALYST_RE = re.compile(
    r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|today|tomorrow|"
    r"next (?:week|month|quarter)|january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\b|\b20\d{2}[-/]\d{1,2}(?:[-/]\d{1,2})?\b",
    re.IGNORECASE,
)
NUMBER_WORDS = set("""zero one two three four five six seven eight nine ten eleven twelve thirteen
fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty
ninety hundred thousand million billion trillion half quarter""".split())
NON_ACTORS = NUMBER_WORDS | {
    "a", "an", "and", "because", "but", "in", "it", "my", "no", "not", "on", "our",
    "research", "so", "that", "the", "this", "to", "watch", "we",
}
NEGATION_CLUSTER_WINDOW = 3


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


def audit_text(text: str) -> dict:
    """Audit arbitrary audience-facing copy, treating blank-line paragraphs as sections."""
    sections = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    return audit_sections(sections)


def _count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def _words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text)


def _sentences(text: str) -> list[tuple[int, int, str]]:
    return [
        (match.start(), match.end(), match.group(0).strip())
        for match in re.finditer(r"[^.!?]+(?:[.!?]+|$)", text)
        if re.search(r"[A-Za-z]", match.group(0))
    ]


def _corrective_matches(text: str) -> list[tuple[int, int]]:
    spans = sorted((match.start(), match.end()) for pattern in CORRECTIVE_PATTERNS for match in pattern.finditer(text))
    unique: list[tuple[int, int]] = []
    for span in spans:
        if not any(span[0] < end and start < span[1] for start, end in unique):
            unique.append(span)
    return unique


def _predictive_matches(sentences: list[tuple[int, int, str]]) -> list[str]:
    matches = []
    for _, _, sentence in sentences:
        # Only an explicit if...then construction scopes a prediction-shaped phrase as a scenario.
        conditional = re.search(r"\bif\b[^.!?\n]{1,160}\bthen\b", sentence, re.IGNORECASE)
        for label, pattern in PREDICTIVE_PATTERNS.items():
            matches.extend(
                label for match in pattern.finditer(sentence)
                if not conditional or match.start() < conditional.end()
            )
    return matches


def _has_number(text: str) -> bool:
    return bool(re.search(r"\d", text)) or any(word.lower() in NUMBER_WORDS for word in _words(text))


def _has_named_actor(text: str) -> bool:
    if re.search(r"\b[A-Z]{2,5}\b", text):
        return True
    return any(
        match.group(0).lower() not in NON_ACTORS
        for match in re.finditer(r"\b[A-Z][a-z]{2,}\b", text)
    )


def _has_concrete_noun(text: str) -> bool:
    return bool(re.search(r"\d", text)) or _has_named_actor(text)


def _is_backmatter(section: str) -> bool:
    return bool(DISCLAIMER_RE.fullmatch(section.strip()) or CTA_RE.match(section))


def _is_market_vocabulary(phrase: str) -> bool:
    """A repeated phrase that is price/instrument talk, not a slogan.

    VO scripts spell numbers out for TTS, so a script that quotes one level twice
    legitimately repeats 'eighty seven fifty five'. Instrument names recur for the same
    reason ('the s and p', 'the nasdaq one hundred'). Measured 2026-07-20 against all
    eight shipped scripts: without this, every one of them blocked, video-04 firing 55
    times on price strings alone. A gate that reds the daily lane on correct copy trains
    people to ignore it, which is worse than no gate.
    """
    tokens = phrase.split()
    # ANY number word or digit disqualifies the phrase. The doctrine's rule is that a
    # SIGNATURE LINE lands once — a rhetorical flourish. Restating a price level, a date or
    # a percentage across sections is what a market script is FOR, and the guide separately
    # requires a concrete level in every paragraph, so penalising it here would have the gate
    # contradict itself. Only number-free, ticker-free phrasing can be a slogan.
    if any(token in NUMBER_WORDS or any(ch.isdigit() for ch in token) for token in tokens):
        return True
    if any(token in MONTH_WORDS for token in tokens):
        return True
    # Ticker/index names read as repetition because they are spelled letter-by-letter for TTS.
    if re.search(r"(?:\b[a-z]\s+){2,}\b[a-z]\b", phrase) or phrase in INSTRUMENT_PHRASES:
        return True
    # Generic connective scaffolding is not a signature line either.
    return all(token in NON_ACTORS or token in FILLER_TOKENS for token in tokens)


MONTH_WORDS = set("""january february march april may june july august september october november
december monday tuesday wednesday thursday friday saturday sunday""".split())
FILLER_TOKENS = {
    "is", "are", "was", "were", "be", "been", "at", "of", "for", "with", "from", "by",
    "as", "into", "out", "up", "down", "over", "under", "about", "percent", "point",
    "close", "closed", "closes", "open", "opens", "high", "low", "week", "weekly",
    "day", "daily", "month", "year", "market", "index", "yield", "bar", "same", "first",
    "last", "next", "prior", "above", "below", "back", "one", "can", "no", "than",
}


INSTRUMENT_PHRASES = {
    "the s and p", "s and p", "the nasdaq one hundred", "nasdaq one hundred",
    "the ten year", "ten year yield", "the dow jones", "the russell two thousand",
}


def _repeated_ngrams(sections: list[str]) -> list[str]:
    by_phrase: dict[str, set[int]] = {}
    for section_index, section in enumerate(sections):
        tokens = [token.lower() for token in _words(section)]
        for size in range(3, 7):
            for start in range(len(tokens) - size + 1):
                by_phrase.setdefault(" ".join(tokens[start:start + size]), set()).add(section_index)
    repeated = {
        phrase: indexes for phrase, indexes in by_phrase.items()
        if len(indexes) >= 2 and not _is_market_vocabulary(phrase)
    }
    long_phrases = [phrase for phrase in repeated if len(phrase.split()) >= 4]
    if long_phrases:
        selected: list[str] = []
        for phrase in sorted(long_phrases, key=lambda value: (-len(value.split()), value)):
            if not any(phrase in longer for longer in selected):
                selected.append(phrase)
        return selected

    # ponytail: two shared trigrams are enough to catch repeated quip templates without a semantic model.
    for left, right in itertools.combinations(range(len(sections)), 2):
        shared = sorted(
            phrase for phrase, indexes in repeated.items()
            if len(phrase.split()) == 3 and {left, right}.issubset(indexes)
        )
        if len(shared) >= 2:
            return shared
    return []


def _add(target: list[dict], rule: str, count: int | float, detail: str, **extra) -> None:
    target.append({"type": rule, "count": count, "detail": detail, **extra})


# Below this word count the copy is a caption/hook/title, not a script. Two rules are
# script-shaped and must not apply: "end on an invalidation level" (a caption has no closing
# section to land) and "concrete noun per paragraph" (a legitimate caption like "Three banks
# report before the bell. I care about net interest income." carries no digit or ticker and is
# still correct). Measured 2026-07-20: without this scoping, real captions were rejected.
# Everything else — corrective contrast, vague authority, backstage jargon, parallelism
# clusters — applies at every length and stays on.
SCRIPT_LENGTH_WORDS = 120


def audit_sections(sections: list[str]) -> dict:
    sections = [section.strip() for section in sections if isinstance(section, str) and section.strip()]
    text = " ".join(sections)
    words = _words(text)
    sentences = _sentences(text)
    is_script = len(words) >= SCRIPT_LENGTH_WORDS
    lengths = [len(_words(sentence)) for _, _, sentence in sentences]
    section_lengths = [len(_words(section)) for section in sections]
    corrective_matches = _corrective_matches(text)
    predictive_matches = _predictive_matches(sentences)
    repeated_ngrams = _repeated_ngrams(sections)
    content_sections = [section for section in sections if not _is_backmatter(section)]
    metrics = {
        "words": len(words),
        "sections": len(sections),
        "sentences": len(lengths),
        "sentenceWordsMean": round(statistics.mean(lengths), 2) if lengths else 0,
        "sentenceWordsStdDev": round(statistics.pstdev(lengths), 2) if lengths else 0,
        "sectionWordsStdDev": round(statistics.pstdev(section_lengths), 2) if section_lengths else 0,
        "firstPersonEditorialMarkers": len(EDITORIAL_MARKER.findall(text)),
        "correctiveContrastCount": len(corrective_matches),
        "repeatedSloganNgrams": repeated_ngrams,
    }
    blocked: list[dict] = []
    warns: list[dict] = []

    if not sections:
        # BLOCK: absent input is unexamined, never a default PASS.
        _add(blocked, "gate input", 1, "No non-empty audience-facing sections were provided.")
    else:
        if predictive_matches:
            # BLOCK: these unconditioned future-price forms are deterministic violations.
            _add(blocked, "prediction language", len(predictive_matches),
                 "Replace unconditional targets with falsifiable conditions and invalidation levels.",
                 forms=sorted(set(predictive_matches)))

        for label, pattern in PROCESS_PATTERNS.items():
            count = _count(pattern, text)
            if count:
                # BLOCK: the doctrine says these production details must never be narrated.
                _add(blocked, label, count, "Keep production and provenance backstage.")

        stock_count = len(STOCK_SIGNPOST_RE.findall(text))
        if stock_count > 0:
            # WARN: one phrase is deterministic, but whether it is earned needs editorial judgment.
            _add(warns, "stock signposting", stock_count, "Lead with the fact or take.")

        contrast_count = len(corrective_matches)
        if contrast_count > 1:
            # BLOCK: the guide permits at most one earned correction; the count is objective.
            _add(blocked, "corrective contrast", contrast_count,
                 "Use direct positive statements; at most one earned correction is allowed.", limit=1)
        elif contrast_count > 0:
            # WARN: the first occurrence no longer passes free, but a human may keep one earned contrast.
            _add(warns, "corrective contrast", contrast_count,
                 "Confirm that the single correction earns its place.", limit=1)

        vague = sum(_count(pattern, text) for pattern in VAGUE_AUTHORITY_PATTERNS.values())
        if vague:
            # BLOCK: vague attribution obscures who owns a factual claim.
            _add(blocked, "vague authority", vague, "Name the analyst, institution, desk, or source.")

        triplets = len(TRIPLET_RE.findall(text))
        if triplets:
            # WARN: comma syntax is detectable; whether a three-item list is ornamental is heuristic.
            _add(warns, "ornamental group of three", triplets, "Use the natural number of items.")

        if content_sections:
            final_section = content_sections[-1]
            final_sentences = [sentence for _, _, sentence in _sentences(final_section)][-2:]
            final_text = " ".join(final_sentences)
            summary_count = len(SUMMARY_RE.findall(final_text))
            no_final_level = not (_has_number(final_text) or DATE_CATALYST_RE.search(final_text))
            if summary_count or no_final_level:
                # WARN: canned wording is exact, while a prose-only ending may still be intentionally concise.
                reasons = []
                if summary_count:
                    reasons.append("canned summary phrase")
                if no_final_level:
                    reasons.append("no number, level, or dated catalyst in the final two sentences")
                _add(warns, "automatic summary ending", max(summary_count, int(no_final_level)), "; ".join(reasons))
            if is_script and not (_has_number(final_section) or DATE_CATALYST_RE.search(final_section)):
                # BLOCK: the generation rule requires the final non-CTA section to end on falsifiable evidence.
                # Script-length copy only — a caption has no closing section to land.
                _add(blocked, "missing invalidation level", 1,
                     "Final non-CTA section needs a numeric level or dated catalyst.")
        elif is_script:
            # BLOCK: backmatter alone cannot establish a publishable ending.
            _add(blocked, "missing invalidation level", 1, "No non-CTA section was available to inspect.")

        missing_concrete = [index + 1 for index, section in enumerate(sections)
                            if not _is_backmatter(section) and not _has_concrete_noun(section)]
        if is_script and missing_concrete:
            # BLOCK: concrete nouns are mechanically testable and required in every content section.
            # Script-length copy only — see SCRIPT_LENGTH_WORDS.
            _add(blocked, "missing concrete noun", len(missing_concrete),
                 "Each section needs a digit, ticker-shaped token, or capitalized proper noun.",
                 sections=missing_concrete)

        sentence_indexes = []
        for start, _ in corrective_matches:
            sentence_indexes.append(next(
                (index for index, (sentence_start, sentence_end, _) in enumerate(sentences)
                 if sentence_start <= start < sentence_end),
                -1,
            ))
        clusters = sum(
            1 for start in range(len(sentences))
            if len({index for index in sentence_indexes if start <= index < start + NEGATION_CLUSTER_WINDOW}) >= 2
            and (start == 0 or len({index for index in sentence_indexes
                                   if start - 1 <= index < start - 1 + NEGATION_CLUSTER_WINDOW}) < 2)
        )
        if clusters:
            # WARN: clusters are objective; whether the parallelism is rhetorically earned is editorial.
            _add(warns, "negative parallelism cluster", clusters,
                 f"CLUSTER: at least two negation-contrasts occur within {NEGATION_CLUSTER_WINDOW} sentences.",
                 windowSentences=NEGATION_CLUSTER_WINDOW)

        # An ABSOLUTE stdev threshold is wrong: 4 words of spread is metronomic across 200-word
        # sections and perfectly varied across 15-word ones. Measured 2026-07-20 — the compliant
        # fixture (18/16/13 words, stdev 2.05) tripped this, and warnings route to publish-private
        # in daily_postclose, so a false warning silently downgrades every good script. Use a
        # RELATIVE threshold (coefficient of variation) and require enough length for the shape to
        # mean anything.
        # Threshold is the COEFFICIENT OF VARIATION, not raw stdev. Measured 2026-07-20:
        # genuinely metronomic sections (4/4/4 words) sit at CV 0.00, while the compliant
        # fixture (18/16/13) sits at CV 0.13 and must stay quiet. 0.08 separates them with
        # room on both sides. A raw-stdev threshold cannot: 4 words of spread is metronomic
        # across 200-word sections and perfectly varied across 15-word ones.
        mean_section = statistics.mean(section_lengths) if section_lengths else 0
        cv = (metrics["sectionWordsStdDev"] / mean_section) if mean_section else 1.0
        if len(section_lengths) >= 3 and cv < 0.08:
            # WARN: low variance is a useful rhythm signal, not proof of bad prose.
            _add(warns, "uniform paragraph rhythm", metrics["sectionWordsStdDev"],
                 "Vary section length instead of repeating a template cadence.")

        lead_sentences = " ".join(sentence for _, _, sentence in _sentences(sections[0])[:2])
        announcement_count = int(bool(ANNOUNCEMENT_RE.match(sections[0])))
        # The number-or-actor half is script-shaped: "My read: the tape is thinner than it looks"
        # IS the take, in first person, and a caption has no room to seat evidence in its first
        # two sentences. The announcement half ("let's break it down") is wrong at any length and
        # stays on for captions.
        missing_lead_evidence = is_script and not (
            _has_number(lead_sentences) or _has_named_actor(lead_sentences))
        if announcement_count or missing_lead_evidence:
            # BLOCK: the first two sentences can be checked directly against the lead-with-the-take rule.
            reasons = []
            if announcement_count:
                reasons.append("opens with an announcement phrase")
            if missing_lead_evidence:
                reasons.append("first two sentences lack a number or named actor")
            _add(blocked, "lead with the take", max(announcement_count, int(missing_lead_evidence)),
                 "; ".join(reasons))

        if not metrics["firstPersonEditorialMarkers"]:
            # WARN: ownership is required when judging, but deterministic code cannot separate fact from judgment.
            _add(warns, "missing editorial owner", 1, "Add first-person ownership where the script makes a judgment.")

        if len(lengths) >= 3 and metrics["sentenceWordsStdDev"] < 2:
            # WARN: remove the old mean-length escape; variance itself is the signal.
            _add(warns, "uniform sentence rhythm", metrics["sentenceWordsStdDev"],
                 "Mix short spoken beats with longer explanations.")

        if repeated_ngrams:
            # WARN, not BLOCK. Whether a repeated phrase is a signature line ("the human cost
            # is real" x3) or an unremarkable fragment ("at the cutoff that") is a SEMANTIC
            # judgment, and this module states plainly that abstract-slogan semantics are not
            # covered deterministically. Measured 2026-07-20 across all eight shipped scripts:
            # every one of them tripped this, mixing genuine signature-line abuse with sentence
            # fragments. Blocking on it would red the daily lane on correct copy and train the
            # operator to bypass the gate — the exact failure this rebuild exists to fix.
            # Promote to BLOCK only behind an LLM judge that can tell a flourish from a fact.
            _add(warns, "slogan repetition", len(repeated_ngrams),
                 "Repeated cross-section n-grams: " + ", ".join(repr(value) for value in repeated_ngrams),
                 ngrams=repeated_ngrams)

    # Not covered deterministically: whether every scenario names a genuine trigger,
    # abstract-slogan semantics, inflated profundity, and fact-vs-judgment separation need an
    # LLM judge. Read-aloud quality and "would a trader say this?" remain irreducibly human checks.
    return {
        "verdict": "BLOCK" if blocked else "PASS",
        "checked_sections": len(sections),
        "blocked": blocked,
        "warns": warns,
        "metrics": metrics,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def _print_report(report: dict, out_path: Path | None = None) -> None:
    print(f"script_style_gate: {report['verdict']} -- {report['checked_sections']} sections, "
          f"{report['metrics']['words']} words")
    if report["warns"]:
        print(f"  {len(report['warns'])} warn(s):")
        for warning in report["warns"]:
            print(f"    - {warning['type']}: count={warning['count']} -- {warning['detail']}")
    if report["blocked"]:
        print(f"  {len(report['blocked'])} block(s):")
        for block in report["blocked"]:
            limit = f" limit={block['limit']}" if "limit" in block else ""
            print(f"    - {block['type']}: count={block['count']}{limit} -- {block['detail']}")
    if out_path:
        print(f"  report: {out_path}")


def _selftest_predictions() -> None:
    blocked = audit_text(
        "Brent will go to 100. WTI will hit 90. XLE will reach 95. "
        "I expect Brent at 100 by Friday. Crude is going to rally. "
        "The desk has a target of 105. WTI should reach 92. My target is 110."
    )
    finding = next(item for item in blocked["blocked"] if item["type"] == "prediction language")
    assert finding["count"] == len(PREDICTIVE_PATTERNS), finding
    legitimate = audit_text(
        "If Brent closes above 83, then WTI will hit 90. Above 81 I change my mind. "
        "The level that would invalidate this is 79. Watch for Monday's OPEC meeting."
    )
    assert not any(item["type"] == "prediction language" for item in legitimate["blocked"]), legitimate
    ambiguous = audit_text("If the Fed pauses, I wait; oil will hit 100.")
    assert any(item["type"] == "prediction language" for item in ambiguous["blocked"]), ambiguous


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("voiceover", type=Path, help="vo.txt or a production directory containing vo.txt")
    parser.add_argument("--out", type=Path, help="optional JSON receipt path")
    args = parser.parse_args()
    voiceover = args.voiceover / "vo.txt" if args.voiceover.is_dir() else args.voiceover
    out_path = args.out or voiceover.parent / "build" / "script-style-audit.json"
    try:
        report = audit_sections(parse_voiceover(voiceover))
    except (OSError, ValueError) as exc:
        report = audit_sections([])
        report["blocked"][0]["detail"] = f"Unable to inspect {voiceover}: {exc}"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _print_report(report, out_path)
    return 1 if report["verdict"] == "BLOCK" else 0


if __name__ == "__main__":
    raise SystemExit(main())
