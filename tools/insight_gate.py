#!/usr/bin/env python3
"""Fail closed unless the brief's claim clears the insight bar.

The governing note is the ops vault `GTM/Pipeline/Video Format v2 — StockedUp Model.md`:

    If the video's core claim is available from the headline, it does not ship.
    Could a competent trader have reached this claim by reading the headline?

That note cited "Machine enforcement: MARKET-ANALYSIS-DOCTRINE.md §0.05". There is no
§0.05, and on 2026-08-04 a search of tools/ and every skill found no reference to the
insight bar at all. Eleven gates ran on the daily lane and not one asked whether the claim
was worth making — which is why the operator's 2026-07-28 rejection was "boring,
surface-level" while every gated rule held. Prose loses to gates; this file is the gate.

  python tools/insight_gate.py productions/daily-2026-08-04
  python tools/insight_gate.py --selftest

WHAT IS AND IS NOT LOAD-BEARING HERE, stated plainly so the next reader does not trust the
weak half. `answer` and `move` are DECLARATIONS: the same pass that writes the brief writes
them, so a writing agent can satisfy both by typing the expected words. They are cheap and
they catch the honest miss, not the motivated one.

The check that can actually say otherwise is the COMPARISON requirement. The doctrine's own
five qualifying moves are all comparisons — "a single-asset observation almost never
qualifies" — so the thesis must name at least two DISTINCT instruments that exist as
`subject` values in claims.yaml. That cannot be satisfied by wording: it needs two receipted
instruments to actually be in the brief's thesis. "Oil fell and stocks rallied" as a
one-instrument recap blocks here no matter how it is phrased.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

try:
    from tools.editorial_gate import INSTRUMENT_ALIASES, _instrument_subject
except ImportError:  # direct `python tools/insight_gate.py` execution
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from editorial_gate import INSTRUMENT_ALIASES, _instrument_subject  # noqa: E402

# The five moves from the governing note, in its order. A brief must name the one it used:
# picking a move is a design act, and "none of these" is the honest signature of a recap.
MOVES = {
    "what-did-not-move":      "1. What did NOT move",
    "damage-vs-mechanism":    "2. Where the damage landed vs where the mechanism says it should",
    "refused-to-unwind":      "3. The asset that refused to unwind",
    "front-end-vs-narrative": "4. The front end against the narrative",
    "dispersion":             "5. Dispersion between two things that should move together",
}
ANSWER_RE = re.compile(r"^\s*-?\s*insight-bar answer:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
MOVE_RE = re.compile(r"^\s*-?\s*insight-bar move:\s*([a-z-]+)", re.IGNORECASE | re.MULTILINE)
THESIS_RE = re.compile(r"^\s*-?\s*one portfolio thesis:\s*(.+?)(?=\n\s*-\s|\n\n|\Z)",
                       re.IGNORECASE | re.MULTILINE | re.DOTALL)
MIN_INSTRUMENTS = 2


def instruments_in(text):
    """Instruments named in prose, by the same lexicon editorial_gate speaks."""
    lowered = text.lower()
    found = set()
    for symbol, names in INSTRUMENT_ALIASES.items():
        if any(re.search(rf"(?<![\w&]){re.escape(name)}(?![\w&])", lowered) for name in names):
            found.add(_instrument_subject(symbol))
    return found


def receipted_subjects(production):
    path = Path(production) / "claims.yaml"
    if not path.is_file():
        return set()
    claims = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return {_instrument_subject(str(c.get("subject"))) for c in claims if c.get("subject")}


def check(production):
    root = Path(production)
    blocked = []
    brief = root / "analysis-brief.md"
    if not brief.is_file():
        return {"status": "BLOCK", "instruments": [], "move": None,
                "blocked": [{"detail": "analysis-brief.md is absent; the insight bar is "
                                       "answered in the brief BEFORE a script is drafted"}]}
    text = brief.read_text(encoding="utf-8")

    answer = ANSWER_RE.search(text)
    if not answer:
        blocked.append({"detail": "brief has no 'Insight-bar answer:' line"})
    elif not answer.group(1).strip().lower().startswith("no"):
        blocked.append({"detail": f"brief answers the headline test with "
                                  f"{answer.group(1).strip()[:80]!r}; a claim reachable from "
                                  f"the headline is a recap and does not ship"})

    move = MOVE_RE.search(text)
    move_key = move.group(1).strip().lower() if move else None
    if not move_key:
        blocked.append({"detail": "brief has no 'Insight-bar move:' line; name which of the "
                                  f"five qualifying moves the claim uses ({', '.join(MOVES)})"})
    elif move_key not in MOVES:
        blocked.append({"detail": f"unknown insight-bar move {move_key!r}; the governing note "
                                  f"lists {', '.join(MOVES)}"})

    thesis = THESIS_RE.search(text)
    if not thesis:
        blocked.append({"detail": "brief has no 'One portfolio thesis:' line to test"})
        named = set()
    else:
        scope = thesis.group(1) + ("\n" + answer.group(1) if answer else "")
        named = instruments_in(scope) & receipted_subjects(root)
        if len(named) < MIN_INSTRUMENTS:
            blocked.append({
                "detail": f"thesis names {len(named)} receipted instrument(s) "
                          f"({', '.join(sorted(named)) or 'none'}); every qualifying move is a "
                          f"COMPARISON, so at least {MIN_INSTRUMENTS} are required. A "
                          f"single-asset observation is the recap this gate exists to stop."})
    return {"status": "BLOCK" if blocked else "PASS", "instruments": sorted(named),
            "move": move_key, "blocked": blocked}


def selftest():
    import tempfile

    def brief(body, claims):
        tmp = Path(tempfile.mkdtemp())
        (tmp / "analysis-brief.md").write_text(body, encoding="utf-8")
        (tmp / "claims.yaml").write_text(yaml.safe_dump(claims), encoding="utf-8")
        return tmp

    two = [{"subject": "NASDAQ:NVDA", "predicate": "session_close", "value": 1},
           {"subject": "CBOE:VIX", "predicate": "session_close", "value": 2}]

    good = brief(
        "- Insight-bar answer: no, a competent trader could not reach this from the headline.\n"
        "- Insight-bar move: dispersion\n"
        "- One portfolio thesis: Nvidia was sold through the session while VIX closed above "
        "Friday.\n", two)
    assert check(good)["status"] == "PASS", check(good)

    # the negative pole that matters: one instrument, perfectly worded, still a recap
    recap = brief(
        "- Insight-bar answer: no, this is a deep structural read.\n"
        "- Insight-bar move: dispersion\n"
        "- One portfolio thesis: Nvidia fell hard on the session.\n", two)
    report = check(recap)
    assert report["status"] == "BLOCK" and "COMPARISON" in report["blocked"][0]["detail"], report

    # an instrument the claims ledger never receipted does not count toward the comparison
    unreceipted = brief(
        "- Insight-bar answer: no.\n- Insight-bar move: dispersion\n"
        "- One portfolio thesis: Nvidia sold off while gold extended.\n", two)
    assert check(unreceipted)["status"] == "BLOCK", check(unreceipted)

    # a self-declared recap blocks even with two instruments
    admits = brief(
        "- Insight-bar answer: yes, the headline carried it.\n- Insight-bar move: dispersion\n"
        "- One portfolio thesis: Nvidia fell while VIX rose.\n", two)
    assert check(admits)["status"] == "BLOCK", check(admits)

    for missing in ("- Insight-bar move: dispersion\n- One portfolio thesis: Nvidia and VIX.\n",
                    "- Insight-bar answer: no.\n- One portfolio thesis: Nvidia and VIX.\n",
                    "- Insight-bar answer: no.\n- Insight-bar move: telepathy\n"
                    "- One portfolio thesis: Nvidia and VIX diverged.\n"):
        assert check(brief(missing, two))["status"] == "BLOCK", missing

    assert check(Path(tempfile.mkdtemp()))["status"] == "BLOCK"   # no brief at all
    print("insight-gate selftest: 8/8 PASS")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("production", nargs="?")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        selftest()
        return 0
    if not args.production:
        parser.error("production is required")
    report = check(args.production)
    print(f"INSIGHT GATE {report['status']} — move={report['move'] or 'unnamed'}, "
          f"compared {report['instruments'] or 'nothing'}")
    for item in report["blocked"]:
        print(f"  - {item['detail']}")
    return 1 if report["blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
