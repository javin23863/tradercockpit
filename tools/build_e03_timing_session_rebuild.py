#!/usr/bin/env python3
"""Build the operator-review E03 timing/session candidate from the pinned phase03 run.

This is deliberately an E03-only route.  It does not call the older E01-E03 batch builder,
because that builder consumed a copied failure-count mapping and carried the phase04 payoff
into the E03 lesson.  The phase JSON is the authority; every durable artifact is regenerated
from it and from the E03 source VO.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from collections import OrderedDict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT / "productions/_series/e01-e03-live-receipts-2026-08-03.json"
INPUT_ROOT = ROOT / "productions/_series/e03-timing-session-rebuild-2026-08-03"
VO_SOURCE = INPUT_ROOT / "episode-03-vo.txt"
DERIVED_RECEIPT = INPUT_ROOT / "phase03-derived-receipt.json"
VISUAL_MAP_SOURCE = INPUT_ROOT / "visual-map.json"
PACKAGE_ROOT = ROOT / "productions/_series/e01-e03-production-candidates-2026-08-03"
PACKAGE = PACKAGE_ROOT / "episode-03"
SOURCE_ROOT = ROOT / "productions/_series/e01-e03-production-source-2026-08-03"
SOURCE = SOURCE_ROOT / "episode-03"
GSAP_ASSET = SOURCE / "assets/gsap.min.js"
PHASE_SOURCE = Path(
    r"C:\Users\MSI\repos\futures\runtime\validation\robustness"
    r"\rb-20260725T133803-b44bd92c\phases\phase03_timing.json"
)
PHASE_CODE = Path(
    r"C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline"
    r"\phases\phase03_timing.py"
)
METRICS_CODE = Path(
    r"C:\Users\MSI\repos\futures\packages\esq\robustness_pipeline\metrics.py"
)
CONFIG_SOURCE = Path(r"C:\Users\MSI\repos\futures\configs\robustness_fast_lib2.yaml")
SYLLABUS_SOURCE = Path(
    r"C:\Users\MSI\Documents\tradercockpit\OpenMontage\projects"
    r"\series-01-backtest-is-not-a-strategy\docs\syllabus.md"
)
OM_PROJECT = ROOT / "OpenMontage/projects/series-e03-timing-session-rebuild"
OM_ARTIFACTS = OM_PROJECT / "artifacts"
OM_HYPERFRAMES = OM_PROJECT / "hyperframes"
OM_PROOF = OM_HYPERFRAMES / "proofs" / "semantic-proof.html"

EXPECTED_PHASE_SHA256 = "BFBB0196138521F2CF87A840B9FC83BFFE8F073A3C0A0C953BC4E2C27E62621E"
EXPECTED_GSAP_SHA256 = "96C01B81F44A3290E2B4532F55E2C9534B2ADC43273A19F3756B2CB41F0FD0B6"
EXPECTED = {
    "entering": 154,
    "failures": {
        "pf_entry_delay_1bar": 41,
        "pf_session_half_1": 66,
        "pf_session_half_2": 23,
    },
    "unique_failures": 101,
    "surviving": 53,
}
ROW_VETO = "formula-2309285457-3105"
ROW_PASS = "formula-2309285457-3088"
TITLE = "154 Entered. 101 Failed. 53 Cleared Every Check."
THUMB_ELEMENTS = ["THREE VIEWS", "ONE VETO"]
SCHEMA_VERSION = "into-the-laboratory/e03-timing-session-rebuild/v1"

GATE_TO_STATE = OrderedDict(
    (
        ("pf_entry_delay_1bar", "fill"),
        ("pf_session_half_1", "session-half-1"),
        ("pf_session_half_2", "session-half-2"),
    )
)
SCENE_TO_STATE = {
    "scene-01": "opening",
    "scene-02": "funnel",
    "scene-03": "fill",
    "scene-04": "latency",
    "scene-05": "split",
    "scene-06": "regime",
    "scene-07": "strips",
    "scene-08": "union",
    "scene-09": "veto",
    "scene-10": "profit-factor",
    "scene-11": "pass",
    "scene-12": "survivors",
    "scene-13": "pipeline",
    "scene-14": "worksheet",
    "scene-15": "close",
}
STATE_ORDER = [
    "opening",
    "funnel",
    "fill",
    "latency",
    "split",
    "regime",
    "strips",
    "union",
    "veto",
    "profit-factor",
    "pass",
    "survivors",
    "pipeline",
    "worksheet",
    "close",
]
STATE_PURPOSE = {
    "opening": "Aligned fill and session strips introduce the three views and the one-veto rule.",
    "funnel": "A fixed candidate rail makes the 154-entry cohort visible before any failure set is counted.",
    "fill": "A signal-to-fill arrow makes the one-bar-later fill stress concrete.",
    "latency": "Two axes separate time latency from price slippage without conflating them.",
    "split": "A median-hour divider creates two session halves from the same trade stream.",
    "regime": "Clock segments are shown as conditions that can carry or weaken a result.",
    "strips": "Three aligned strips show 41, 66, and 23 failure sets against the same 154 candidates.",
    "union": "Overlapping sets and inclusion-exclusion arithmetic show why the union is 101.",
    "veto": "The exact 3105 row visibly turns red on session half 1 while the other views stay green.",
    "profit-factor": "Gross winning and losing dollars define PF as one diagnostic with a threshold.",
    "pass": "The exact 3088 row keeps all three values above 1.000000.",
    "survivors": "The union subtraction resolves into 154 minus 101 equals 53.",
    "pipeline": "Real-data and wiring proof are separated from the false validated flag.",
    "worksheet": "A beginner can reproduce the three sets, union, and veto rule as a small worksheet.",
    "close": "The lesson ends at 53 and names cost stress as the next question without importing later results.",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def write_text_lf(path: Path, text: str) -> None:
    """Write generated text with stable UTF-8/LF bytes on every host."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def write_json(path: Path, value: object) -> None:
    write_text_lf(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def require_file(path: Path) -> None:
    if not path.is_file():
        raise SystemExit(f"BLOCK: required source is missing: {path}")


def parse_vo(path: Path) -> list[dict]:
    """Parse the source VO and require one receipt-bound paragraph per sentence cue."""
    marker = re.compile(r"^#\s*receipt:\s*([A-Za-z0-9._,-]+)\s*$")
    slot_marker = re.compile(r"^=== SLOT\s+(\S+)")
    rows: list[dict] = []
    slot_id = ""
    label = ""
    receipt: str | None = None
    spoken: list[str] = []

    def flush() -> None:
        nonlocal receipt, spoken
        text = " ".join(line.strip() for line in spoken if line.strip()).strip()
        spoken = []
        if not text:
            return
        if not slot_id:
            raise ValueError(f"spoken paragraph before a SLOT: {text[:80]}")
        if receipt is None:
            raise ValueError(f"spoken paragraph has no receipt: {text[:100]}")
        rows.append({"slot": slot_id, "label": label, "text": text, "receipt": receipt})
        receipt = None

    for raw in path.read_text(encoding="utf-8").splitlines() + [""]:
        line = raw.strip()
        slot = slot_marker.match(line)
        if slot:
            flush()
            slot_id = slot.group(1)
            label = ""
            continue
        if line.startswith("## "):
            flush()
            label = line[3:].strip()
            continue
        found = marker.match(line)
        if found:
            flush()
            receipt = found.group(1)
            continue
        if not line or line.startswith("#") or line.startswith("["):
            flush()
            continue
        spoken.append(line)
    flush()

    if not rows:
        raise ValueError(f"no receipt-bound paragraphs in {path}")
    ids = [row["receipt"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("receipt IDs must be unique")
    if rows[0]["text"] != TITLE:
        raise ValueError("the first spoken sentence must exactly match the package title")
    unknown_slots = sorted({row["slot"] for row in rows} - set(SCENE_TO_STATE))
    if unknown_slots:
        raise ValueError(f"VO uses unknown slots: {unknown_slots}")
    return rows


def derive_phase03_facts(payload: dict) -> dict:
    """Derive failure sets from candidate gate booleans, never from copied summary prose."""
    candidates = payload.get("candidates")
    if not isinstance(candidates, dict) or not candidates:
        raise ValueError("phase03 source has no candidate object")
    candidate_ids = set(candidates)
    entering = set(payload.get("entering", []))
    if entering != candidate_ids:
        raise ValueError("phase03 entering IDs do not equal candidate IDs")

    failure_sets: dict[str, set[str]] = {}
    for gate_name in GATE_TO_STATE:
        failed = {
            candidate_id
            for candidate_id, candidate in candidates.items()
            if not bool(candidate.get("gates", {}).get(gate_name, {}).get("pass"))
        }
        failure_sets[gate_name] = failed

    union = set().union(*failure_sets.values())
    survivors = candidate_ids - union
    pairwise = {
        f"{left}+{right}": len(failure_sets[left] & failure_sets[right])
        for index, left in enumerate(GATE_TO_STATE)
        for right in list(GATE_TO_STATE)[index + 1 :]
    }
    triple = len(set.intersection(*failure_sets.values()))
    facts = {
        "phase_key": payload.get("phase_key"),
        "phase_label": payload.get("phase_label"),
        "run_id": payload.get("run_id"),
        "program_id": payload.get("program_id"),
        "window": payload.get("window"),
        "candidate_ids": sorted(candidate_ids),
        "failure_sets": {key: sorted(value) for key, value in failure_sets.items()},
        "failure_counts": {key: len(value) for key, value in failure_sets.items()},
        "unique_failures": len(union),
        "survivor_ids": sorted(survivors),
        "surviving": len(survivors),
        "pairwise_intersections": pairwise,
        "triple_intersection": triple,
        "examples": {
            ROW_VETO: candidate_record(candidates[ROW_VETO]),
            ROW_PASS: candidate_record(candidates[ROW_PASS]),
        },
        "provenance": payload.get("provenance", {}),
        "source_declared_counts": {
            "entering": len(payload.get("entering", [])),
            "dropped": len(payload.get("dropped", [])),
            "surviving": len(payload.get("surviving", [])),
        },
    }
    return facts


def candidate_record(candidate: dict) -> dict:
    detail = candidate.get("detail", {})
    gates = candidate.get("gates", {})
    detail_names = {
        "pf_entry_delay_1bar": "entry_delay_1bar",
        "pf_session_half_1": "session_half_1",
        "pf_session_half_2": "session_half_2",
    }
    gate_values = OrderedDict()
    for gate_name in GATE_TO_STATE:
        metric = detail.get(detail_names[gate_name], {})
        gate_values[gate_name] = {
            "pf": metric.get("pf"),
            "gross_win": metric.get("gross_win"),
            "gross_loss": metric.get("gross_loss"),
            "n": metric.get("n"),
            "pass": bool(gates.get(gate_name, {}).get("pass")),
            "threshold": gates.get(gate_name, {}).get("threshold"),
        }
    return {"verdict": candidate.get("verdict"), "views": gate_values}


def assert_phase03_truth(facts: dict, expected: dict | None = None) -> None:
    expected = expected or EXPECTED
    if len(facts["candidate_ids"]) != expected["entering"]:
        raise AssertionError(f"entering count drifted: {len(facts['candidate_ids'])}")
    if facts["failure_counts"] != expected["failures"]:
        raise AssertionError(
            "phase03 gate mapping drifted: "
            f"actual={facts['failure_counts']} expected={expected['failures']}"
        )
    if facts["unique_failures"] != expected["unique_failures"]:
        raise AssertionError(f"unique failures drifted: {facts['unique_failures']}")
    if facts["surviving"] != expected["surviving"]:
        raise AssertionError(f"survivors drifted: {facts['surviving']}")
    if facts["pairwise_intersections"] != {
        "pf_entry_delay_1bar+pf_session_half_1": 24,
        "pf_entry_delay_1bar+pf_session_half_2": 5,
        "pf_session_half_1+pf_session_half_2": 0,
    }:
        raise AssertionError(f"overlap geometry drifted: {facts['pairwise_intersections']}")
    if facts["triple_intersection"] != 0:
        raise AssertionError("the phase03 output unexpectedly gained a three-way overlap")
    veto = facts["examples"][ROW_VETO]["views"]
    expected_veto = {
        "pf_entry_delay_1bar": 1.123246,
        "pf_session_half_1": 0.986603,
        "pf_session_half_2": 1.494639,
    }
    if {key: value["pf"] for key, value in veto.items()} != expected_veto:
        raise AssertionError(f"veto row drifted: {veto}")
    passed = facts["examples"][ROW_PASS]["views"]
    expected_pass = {
        "pf_entry_delay_1bar": 1.080180,
        "pf_session_half_1": 1.156412,
        "pf_session_half_2": 1.151833,
    }
    if {key: value["pf"] for key, value in passed.items()} != expected_pass:
        raise AssertionError(f"pass row drifted: {passed}")
    if facts["source_declared_counts"] != {
        "entering": 154,
        "dropped": 101,
        "surviving": 53,
    }:
        raise AssertionError(f"source declared lists drifted: {facts['source_declared_counts']}")


def repair_live_receipt_manifest(facts: dict) -> None:
    """Repair only the E03 summary fields; retain E01/E02 and all source hashes."""
    # Keep the hand-maintained E01/E02 formatting and byte surface intact.  A whole-file JSON
    # re-serialization made an E03-only correction look like an E01/E02 rewrite in review.
    text = RECEIPTS.read_text(encoding="utf-8")
    episode_start = text.index('"03": {')
    episode_end = text.index('"shared_e04_authority"', episode_start)
    prefix, episode, suffix = text[:episode_start], text[episode_start:episode_end], text[episode_end:]
    episode = re.sub(
        r'("title_candidate":\s*)"[^"]*"',
        rf'\g<1>"{TITLE}"',
        episode,
        count=1,
    )
    episode = re.sub(
        r'("pf_entry_delay_1bar":\s*)66(,\s*\n\s*"pf_session_half_1":\s*)41',
        r'\g<1>41\g<2>66',
        episode,
        count=1,
    )
    episode = re.sub(
        r'"next_phase":\s*\{.*?\n\s*\},?',
        '"next_phase": {\n'
        '        "phase": "phase04_cost",\n'
        '        "source_sha256": "38408093f40b4f2b98b4cb3d0b28bf2f3fb1812ebb25d39b53420c52e5d164be",\n'
        '        "status": "next question only; no phase04 result belongs in E03"\n'
        '      }',
        episode,
        count=1,
        flags=re.S,
    )
    updated = prefix + episode + suffix
    if updated != text:
        write_text_lf(RECEIPTS, updated)


def source_receipt(facts: dict) -> dict:
    require_file(PHASE_SOURCE)
    require_file(PHASE_CODE)
    require_file(METRICS_CODE)
    require_file(CONFIG_SOURCE)
    require_file(SYLLABUS_SOURCE)
    require_file(GSAP_ASSET)
    if sha256(GSAP_ASSET) != EXPECTED_GSAP_SHA256:
        raise SystemExit(f"BLOCK: GSAP asset drifted: {sha256(GSAP_ASSET)} != {EXPECTED_GSAP_SHA256}")
    return {
        "schema": "e03-phase03-private-receipt/v1",
        "phase_source": {
            "path": str(PHASE_SOURCE),
            "sha256": sha256(PHASE_SOURCE),
            "required_sha256": EXPECTED_PHASE_SHA256,
            "locator": "#/candidates/*/gates and #/candidates/*/detail",
        },
        "methodology_source": {
            "path": str(PHASE_CODE),
            "sha256": sha256(PHASE_CODE),
            "locators": ["#module-docstring", "#_delayed_replay_twice", "#_split_session_halves", "#_measure_timing"],
        },
        "profit_factor_source": {
            "path": str(METRICS_CODE),
            "sha256": sha256(METRICS_CODE),
            "locator": "#compute_metrics:82-126",
        },
        "gate_config_source": {
            "path": str(CONFIG_SOURCE),
            "sha256": sha256(CONFIG_SOURCE),
            "locator": "thresholds.phase03",
        },
        "syllabus_source": {
            "path": str(SYLLABUS_SOURCE),
            "sha256": sha256(SYLLABUS_SOURCE),
            "locator": "## Ep03 — phase03_timing",
        },
        "render_dependency": {
            "name": "GSAP",
            "version": "3.13.0",
            "path": str(GSAP_ASSET),
            "sha256": EXPECTED_GSAP_SHA256,
            "license": "GSAP standard license; local pinned asset for deterministic rendering",
        },
        "run": {
            "run_id": facts["run_id"],
            "phase_key": facts["phase_key"],
            "phase_label": facts["phase_label"],
            "program_id": facts["program_id"],
            "window": facts["window"],
        },
        "derived": {
            "entering": len(facts["candidate_ids"]),
            "failure_counts": facts["failure_counts"],
            "unique_failures": facts["unique_failures"],
            "surviving": facts["surviving"],
            "pairwise_intersections": facts["pairwise_intersections"],
            "triple_intersection": facts["triple_intersection"],
            "arithmetic": "154 - 101 = 53",
            "failure_sets": facts["failure_sets"],
            "survivor_ids": facts["survivor_ids"],
        },
        "examples": facts["examples"],
        "provenance": facts["provenance"],
        "drift_checks": [
            "derive all three failure sets from candidate gate booleans",
            "assert expected mapping 41 one-bar / 66 session-half-1 / 23 session-half-2",
            "assert union 101 and survivor count 53",
            "assert the two pinned candidate rows and all six PF values",
        ],
    }


def state_label(state: str) -> str:
    return {
        "opening": "THREE VIEWS / ONE VETO",
        "funnel": "START WITH THE SAME COHORT",
        "fill": "THE FILL CAN ARRIVE ONE BAR LATER",
        "latency": "TIME AND PRICE ARE DIFFERENT",
        "split": "CUT THE SESSION AT THE MEDIAN HOUR",
        "regime": "A CLOCK SEGMENT CAN CARRY A RESULT",
        "strips": "THREE FAILURE SETS / ONE COHORT",
        "union": "COUNT THE UNION ONCE",
        "veto": "ONE WEAK VIEW VETOES THE ROW",
        "profit-factor": "PROFIT FACTOR IS ONE DIAGNOSTIC",
        "pass": "A PASS NEEDS THREE GREEN VALUES",
        "survivors": "154 - 101 = 53",
        "pipeline": "REAL DATA / WIRED / NOT VALIDATED",
        "worksheet": "REPEAT THE TEST AS A SET WORKSHEET",
        "close": "NEXT QUESTION: COST STRESS",
    }[state]


def t(x: float, y: float, text_value: str, cls: str = "body", anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}">{html.escape(str(text_value))}</text>'


def line(x1: float, y1: float, x2: float, y2: float, cls: str = "hairline") -> str:
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}" />'


def base_group(state: str, body: str) -> str:
    return (
        f'<g id="state-{state}" class="state" aria-label="{html.escape(state_label(state))}">'
        f"{t(54, 58, state_label(state), 'eyebrow')}"
        f"{body}</g>"
    )


def opening_group(facts: dict) -> str:
    strips = []
    labels = [
        ("FILL +1 BAR", facts["failure_counts"]["pf_entry_delay_1bar"], "fail"),
        ("SESSION HALF 1", facts["failure_counts"]["pf_session_half_1"], "fail"),
        ("SESSION HALF 2", facts["failure_counts"]["pf_session_half_2"], "fail"),
    ]
    entering = len(facts["candidate_ids"])
    unique_failures = facts["unique_failures"]
    surviving = facts["surviving"]
    for index, (label, count, cls) in enumerate(labels):
        y = 350 + index * 70
        strips.append(line(290, y, 1040, y, "track"))
        strips.append(line(290, y, 290 + 750 * count / entering, y, "failure-line"))
        strips.append(t(270, y + 8, label, "label", "end"))
        strips.append(t(1080, y + 8, f"{count} FAIL", cls, "start"))
    body = (
        t(54, 158, "THREE VIEWS", "hero")
        + t(54, 270, "ONE VETO", "hero accent")
        + t(54, 318, f"The same {entering} candidates face three transformations.", "subhead")
        + "".join(strips)
        + t(54, 566, "One candidate can fail more than one strip.", "body")
        + t(54, 624, f"The union fails {unique_failures}. The remainder is {surviving}.", "equation")
        + '<circle cx="1136" cy="574" r="58" class="veto-ring" />'
        + t(1136, 568, "ONE", "veto-text", "middle")
        + t(1136, 598, "WEAK VIEW", "veto-small", "middle")
    )
    return base_group("opening", body)


def funnel_group(facts: dict) -> str:
    entering = len(facts["candidate_ids"])
    body = (
        t(54, 154, f"{entering} CANDIDATES ENTER", "hero-small")
        + t(54, 198, "The list stays fixed while the views change.", "subhead")
        + '<rect x="54" y="286" width="1172" height="64" rx="32" class="cohort-track" />'
        + '<rect x="54" y="286" width="1172" height="64" rx="32" class="cohort-fill" />'
        + t(54, 404, "same rule", "label")
        + t(340, 404, "same evidence window", "label")
        + t(680, 404, "new fill/session view", "label")
        + line(170, 430, 1110, 430, "gold-line")
        + t(54, 544, "A screening pass opens another question.", "equation")
        + t(54, 598, "It does not become a live-trading promise.", "body")
    )
    return base_group("funnel", body)


def fill_group() -> str:
    body = (
        t(54, 150, "FILL = THE PRICE THE ORDER RECEIVES", "hero-small")
        + t(54, 196, "The stress moves the entry one bar later in the same direction.", "subhead")
        + t(128, 324, "SIGNAL", "label", "middle")
        + t(638, 324, "FILL", "label", "middle")
        + line(190, 308, 560, 308, "gold-line")
        + '<polygon points="560,308 526,286 526,330" class="gold-fill" />'
        + line(710, 308, 1118, 308, "failure-line")
        + '<polygon points="1118,308 1084,286 1084,330" class="failure-fill" />'
        + t(375, 376, "frozen signal price", "body", "middle")
        + t(910, 376, "one bar later", "fail", "middle")
        + line(190, 508, 1118, 508, "track")
        + t(54, 570, "Slippage is the price gap between the assumption and the fill.", "equation")
        + t(54, 624, "The proxy stresses the assumption; it does not impersonate a broker.", "body")
    )
    return base_group("fill", body)


def latency_group() -> str:
    body = (
        t(54, 150, "LATENCY = TIME", "hero-small")
        + t(54, 214, "SLIPPAGE = PRICE", "hero-small accent")
        + line(120, 362, 1110, 362, "gold-line")
        + t(120, 420, "signal", "label")
        + t(850, 420, "response", "label")
        + '<circle cx="120" cy="362" r="12" class="gold-dot" /><circle cx="850" cy="362" r="12" class="gold-dot" />'
        + t(54, 524, "A one-bar shift is a timing stress for the fill assumption.", "equation")
        + t(54, 586, "It is not a claim that every order waits one bar.", "body")
    )
    return base_group("latency", body)


def split_group() -> str:
    body = (
        t(54, 150, "SPLIT SAMPLE", "hero-small")
        + t(54, 196, "Separate the same trade stream at the median entry hour.", "subhead")
        + '<rect x="90" y="310" width="1020" height="46" rx="23" class="cohort-track" />'
        + '<rect x="90" y="310" width="506" height="46" rx="23" class="half-one" />'
        + '<rect x="604" y="310" width="506" height="46" rx="23" class="half-two" />'
        + line(604, 270, 604, 430, "median-line")
        + t(350, 440, "SESSION HALF 1", "label", "middle")
        + t(860, 440, "SESSION HALF 2", "label", "middle")
        + t(604, 252, "MEDIAN ENTRY HOUR", "eyebrow", "middle")
        + t(54, 548, "Each half gets its own profit-factor check.", "equation")
        + t(54, 606, "A blended average can hide a clock effect.", "body")
    )
    return base_group("split", body)


def regime_group() -> str:
    body = (
        t(54, 150, "REGIME = A DIFFERENT MARKET CONDITION", "hero-small")
        + t(54, 196, "Hours change the mix of prices, volatility, and participation.", "subhead")
        + '<path d="M90 430 C220 370 260 472 386 420 S560 348 684 408 S870 486 1000 386 S1090 370 1160 342" class="curve" />'
        + line(90, 500, 1160, 500, "track")
        + t(90, 552, "quiet", "label")
        + t(564, 552, "median hour", "label", "middle")
        + t(1160, 552, "active", "label", "end")
        + t(54, 624, "The split can expose concentration; it cannot promise the next regime.", "body")
    )
    return base_group("regime", body)


def strips_group(facts: dict) -> str:
    labels = [
        ("ONE-BAR FILL", facts["failure_counts"]["pf_entry_delay_1bar"]),
        ("SESSION HALF 1", facts["failure_counts"]["pf_session_half_1"]),
        ("SESSION HALF 2", facts["failure_counts"]["pf_session_half_2"]),
    ]
    entering = len(facts["candidate_ids"])
    body = t(54, 142, "THREE FAILURE SETS / ONE COHORT", "hero-small") + t(
        54, 188, f"Each strip starts from the same {entering} candidates.", "subhead"
    )
    for index, (label, count) in enumerate(labels):
        y = 286 + index * 94
        body += t(260, y + 8, label, "label", "end")
        body += line(300, y, 1020, y, "track")
        body += line(300, y, 300 + 720 * count / entering, y, "failure-line")
        body += t(1060, y + 8, f"{count}", "fail")
        body += t(1110, y + 8, "fail", "label")
    largest_gate = max(labels, key=lambda item: item[1])
    body += t(54, 626, f"The largest strip is {largest_gate[0].lower()}: {largest_gate[1]} candidates.", "equation")
    return base_group("strips", body)


def union_group(facts: dict) -> str:
    counts = facts["failure_counts"]
    fill_count = counts["pf_entry_delay_1bar"]
    half_one_count = counts["pf_session_half_1"]
    half_two_count = counts["pf_session_half_2"]
    overlaps = facts["pairwise_intersections"]
    fill_half_one = overlaps["pf_entry_delay_1bar+pf_session_half_1"]
    fill_half_two = overlaps["pf_entry_delay_1bar+pf_session_half_2"]
    union_size = facts["unique_failures"]
    body = (
        t(54, 138, "OVERLAP IS PART OF THE RESULT", "hero-small")
        + '<circle cx="390" cy="372" r="142" class="set-one" /><circle cx="610" cy="372" r="142" class="set-two" /><circle cx="500" cy="514" r="142" class="set-three" />'
        + t(350, 322, fill_count, "set-number", "middle")
        + t(650, 322, half_one_count, "set-number", "middle")
        + t(500, 568, half_two_count, "set-number", "middle")
        + t(500, 370, fill_half_one, "overlap-number", "middle")
        + t(558, 454, fill_half_two, "overlap-number", "middle")
        + t(54, 650, f"{fill_count} + {half_one_count} + {half_two_count} - {fill_half_one} - {fill_half_two} = {union_size} unique failures", "equation")
        + t(54, 692, "No three-way overlap appears in this recorded output.", "body")
    )
    return base_group("union", body)


def veto_group(facts: dict) -> str:
    row = facts["examples"][ROW_VETO]["views"]
    values = [row[key]["pf"] for key in GATE_TO_STATE]
    names = ["FILL +1 BAR", "SESSION HALF 1", "SESSION HALF 2"]
    body = (
        t(54, 136, "FORMULA-2309285457-3105", "hero-small")
        + t(54, 184, "One weak view makes the row fail.", "subhead")
        + '<rect x="54" y="254" width="1172" height="82" rx="18" class="row-card" />'
        + t(92, 306, "VETO", "fail")
        + t(260, 306, "session half 1", "label")
        + t(538, 306, "0.986603", "fail")
        + t(790, 306, "threshold", "label")
        + t(956, 306, "1.000000", "body")
    )
    for index, (name, value) in enumerate(zip(names, values)):
        x = 240 + index * 320
        color_class = "fail" if index == 1 else "pass"
        body += t(x, 472, name, "label", "middle") + t(x, 548, f"{value:.6f}", color_class, "middle")
    body += t(54, 644, "1.123246   /   0.986603   /   1.494639", "equation")
    return base_group("veto", body)


def pf_group() -> str:
    body = (
        t(54, 150, "PROFIT FACTOR", "hero-small")
        + t(54, 212, "PF = GROSS WINNING DOLLARS / GROSS LOSING DOLLARS", "equation")
        + line(168, 352, 1100, 352, "gold-line")
        + t(170, 426, "gross wins", "label")
        + t(760, 426, "gross losses", "label")
        + t(54, 540, "Above 1 means winning dollars exceed losing dollars in that ledger.", "body")
        + t(54, 598, "PF is one diagnostic; it does not summarize drawdown or cost.", "subhead")
    )
    return base_group("profit-factor", body)


def pass_group(facts: dict) -> str:
    row = facts["examples"][ROW_PASS]["views"]
    body = (
        t(54, 136, "FORMULA-2309285457-3088", "hero-small")
        + t(54, 184, "All three views clear the same threshold.", "subhead")
        + '<rect x="54" y="254" width="1172" height="82" rx="18" class="pass-card" />'
        + t(92, 306, "PASS", "pass")
        + t(260, 306, "three green values", "label")
    )
    names = ["FILL +1 BAR", "SESSION HALF 1", "SESSION HALF 2"]
    for index, gate_name in enumerate(GATE_TO_STATE):
        x = 240 + index * 320
        body += t(x, 472, names[index], "label", "middle") + t(
            x, 548, f"{row[gate_name]['pf']:.6f}", "pass", "middle"
        )
    body += t(54, 644, "1.080180   /   1.156412   /   1.151833", "equation")
    return base_group("pass", body)


def survivors_group(facts: dict) -> str:
    entering = len(facts["candidate_ids"])
    unique_failures = facts["unique_failures"]
    surviving = facts["surviving"]
    body = (
        t(54, 150, "THE SURVIVOR EQUATION", "hero-small")
        + t(54, 278, entering, "big-number")
        + t(280, 278, "-", "operator")
        + t(390, 278, unique_failures, "big-number fail")
        + t(620, 278, "=", "operator")
        + t(760, 278, surviving, "big-number pass")
        + t(54, 360, "entering", "label")
        + t(390, 360, "unique failures", "label")
        + t(760, 360, "phase survivors", "label")
        + line(54, 470, 1090, 470, "gold-line")
        + t(54, 556, "A survivor has cleared this phase's three views.", "equation")
        + t(54, 616, "It has not become validated.", "body")
    )
    return base_group("survivors", body)


def pipeline_group(facts: dict) -> str:
    body = (
        t(54, 146, "THREE DIFFERENT STATEMENTS", "hero-small")
        + '<rect x="54" y="246" width="344" height="190" rx="18" class="pass-card" />'
        + '<rect x="468" y="246" width="344" height="190" rx="18" class="pass-card" />'
        + '<rect x="882" y="246" width="344" height="190" rx="18" class="row-card" />'
        + t(226, 300, "REAL DATA", "pass", "middle")
        + t(226, 352, "provenance", "label", "middle")
        + t(640, 300, "WIRED", "pass", "middle")
        + t(640, 352, "connections exercised", "label", "middle")
        + t(1054, 300, "VALIDATED", "fail", "middle")
        + t(1054, 352, "false", "label", "middle")
        + t(54, 558, "A real run and a working pipeline are evidence of execution.", "equation")
        + t(54, 616, "They are not the same as clearing every later gate.", "body")
    )
    return base_group("pipeline", body)


def worksheet_group(facts: dict) -> str:
    entering = len(facts["candidate_ids"])
    body = (
        t(54, 144, "REPEATABLE WORKSHEET", "hero-small")
        + t(92, 264, "01", "step")
        + t(230, 264, f"write the {entering} entering IDs", "body")
        + t(92, 350, "02", "step")
        + t(230, 350, "make three failure sets", "body")
        + t(92, 436, "03", "step")
        + t(230, 436, "mark any PF at or below 1.0", "body")
        + t(92, 522, "04", "step")
        + t(230, 522, "union the sets once", "body")
        + t(92, 608, "05", "step")
        + t(230, 608, "keep a veto row and a pass row", "body")
    )
    return base_group("worksheet", body)


def close_group(facts: dict) -> str:
    entering = len(facts["candidate_ids"])
    unique_failures = facts["unique_failures"]
    surviving = facts["surviving"]
    body = (
        t(54, 164, f"{entering} - {unique_failures} =", "equation")
        + t(54, 300, surviving, "big-number pass")
        + t(330, 300, "phase survivors", "hero-small")
        + line(54, 392, 1110, 392, "gold-line")
        + t(54, 500, "NEXT QUESTION", "eyebrow")
        + t(54, 582, "COST STRESS", "hero accent")
        + t(54, 636, "How much of the 53 remains when assumptions rise?", "subhead")
    )
    return base_group("close", body)


def visual_states(facts: dict) -> dict[str, str]:
    return {
        "opening": opening_group(facts),
        "funnel": funnel_group(facts),
        "fill": fill_group(),
        "latency": latency_group(),
        "split": split_group(),
        "regime": regime_group(),
        "strips": strips_group(facts),
        "union": union_group(facts),
        "veto": veto_group(facts),
        "profit-factor": pf_group(),
        "pass": pass_group(facts),
        "survivors": survivors_group(facts),
        "pipeline": pipeline_group(facts),
        "worksheet": worksheet_group(facts),
        "close": close_group(facts),
    }


def css(asset_prefix: str = "", width: int = 1280, height: int = 720) -> str:
    styles = """
@font-face{font-family:plex;font-style:normal;font-weight:400;src:url('assets/fonts/ibm-plex-sans-400.ttf') format('truetype');font-display:block}
@font-face{font-family:plex;font-style:normal;font-weight:700;src:url('assets/fonts/ibm-plex-sans-700.ttf') format('truetype');font-display:block}
*{box-sizing:border-box}html,body{margin:0;width:1280px;height:720px;overflow:hidden;background:#0b1012;color:#edf4ee;font-family:plex,Arial,sans-serif}#root{position:absolute;inset:0;width:1280px;height:720px;overflow:hidden;background:#0b1012}svg{display:block;width:1280px;height:720px;background:#0b1012}text{font-family:plex,Arial,sans-serif;letter-spacing:.018em}.state{opacity:0}.eyebrow{font-size:18px;font-weight:700;fill:#a4c7bd;letter-spacing:.12em}.hero{font-size:78px;font-weight:700;fill:#edf4ee;letter-spacing:.02em}.hero-small{font-size:42px;font-weight:700;fill:#edf4ee;letter-spacing:.025em}.accent{fill:#ff5c67}.subhead{font-size:23px;font-weight:400;fill:#afbeb8}.body{font-size:24px;font-weight:400;fill:#d5e0d9}.label{font-size:18px;font-weight:700;fill:#a4c7bd;letter-spacing:.08em}.equation{font-size:30px;font-weight:700;fill:#f4c95d}.fail{fill:#ff5c67;font-size:28px;font-weight:700}.pass{fill:#5bdd94;font-size:28px;font-weight:700}.veto-text{fill:#ff5c67;font-size:20px;font-weight:700;letter-spacing:.08em}.veto-small{fill:#ffb0b3;font-size:12px;font-weight:700;letter-spacing:.08em}.track{stroke:#293739;stroke-width:12;stroke-linecap:round}.failure-line{stroke:#ff5c67;stroke-width:12;stroke-linecap:round}.gold-line{stroke:#f4c95d;stroke-width:4;stroke-linecap:round}.hairline{stroke:#293739;stroke-width:2}.gold-fill{fill:#f4c95d}.failure-fill{fill:#ff5c67}.gold-dot{fill:#f4c95d}.veto-ring{fill:#26181b;stroke:#ff5c67;stroke-width:4}.cohort-track{fill:#182427}.cohort-fill{fill:#5bdd94}.half-one{fill:#5bdd94}.half-two{fill:#68a5ff}.median-line{stroke:#f4c95d;stroke-width:4;stroke-dasharray:8 8}.curve{fill:none;stroke:#68a5ff;stroke-width:8;stroke-linecap:round}.row-card{fill:#26181b;stroke:#ff5c67;stroke-width:2}.pass-card{fill:#122a21;stroke:#5bdd94;stroke-width:2}.big-number{font-size:110px;font-weight:700;fill:#edf4ee}.operator{font-size:88px;font-weight:400;fill:#f4c95d}.step{font-size:28px;font-weight:700;fill:#f4c95d}.set-one{fill:#ff5c67;fill-opacity:.18;stroke:#ff5c67;stroke-width:3}.set-two{fill:#68a5ff;fill-opacity:.18;stroke:#68a5ff;stroke-width:3}.set-three{fill:#5bdd94;fill-opacity:.18;stroke:#5bdd94;stroke-width:3}.set-number{font-size:34px;font-weight:700;fill:#edf4ee}.overlap-number{font-size:22px;font-weight:700;fill:#f4c95d}
""".strip()
    return (
        styles
        .replace("width:1280px;height:720px", f"width:{width}px;height:{height}px")
        .replace("assets/fonts/", f"{asset_prefix}assets/fonts/")
    )


def html_document(facts: dict, timeline: list[tuple[str, float]], duration: float, proof: bool) -> str:
    canvas_width, canvas_height = (1280, 720) if proof else (1920, 1080)
    states = visual_states(facts)
    selected = [state for state, _ in timeline]
    first_state = timeline[0][0]
    groups = "".join(states[state] for state in selected)
    # Keep the opening state visible for raw source/runtime captures.  The
    # thumbnail has the same opening group at opacity 1, while a paused GSAP
    # timeline otherwise leaves every `.state` at the CSS fallback opacity 0
    # until a player seeks it.  This is a source-level scale/readiness fix for
    # the first-shot contract, not a crop or a relabelled proof image.
    opening_marker = f'<g id="state-{first_state}" class="state"'
    groups = groups.replace(
        opening_marker,
        f'<g id="state-{first_state}" class="state" style="opacity:1"',
        1,
    )
    timeline_js = json.dumps(timeline, separators=(",", ":"))
    fade_js = "".join(
        f'tl.to("#state-{state}",{{opacity:1,duration:.24}}, {start:.3f});'
        f'tl.to("#state-{previous}",{{opacity:0,duration:.24}}, {start:.3f});'
        for (previous, _), (state, start) in zip(timeline, timeline[1:])
    )
    script = (
        "window.__timelines=window.__timelines||{};"
        "const tl=gsap.timeline({paused:true,defaults:{ease:'none'}});"
        f'tl.set("#state-{first_state}",{{opacity:1}},0);{fade_js}'
        # A paused GSAP timeline does not apply a zero-time `set` until it is
        # rendered.  Raw first-shot capture happens before HyperFrames seeks
        # the timeline, so without this explicit zero-progress render the
        # source composition is a correctly-sized black canvas while the
        # thumbnail (which hard-codes opacity) looks healthy.  Keep the
        # runtime handshake in the shared source rather than repairing a
        # derived screenshot or cropping the evidence.
        "tl.progress(0);"
        f'window.__timelines["e03-timing-session"] = tl;'
        f'window.__e03Timeline = {timeline_js};'
    )
    label = "E03 semantic proof" if proof else "E03 timing session composition"
    # HyperFrames serves every composition from the project root; nested proof
    # files must still use root-relative asset URLs for preview and render parity.
    asset_prefix = ""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{html.escape(label)}</title></head><body>"
        f'<script src="{asset_prefix}assets/gsap.min.js"></script>'
        f'<div id="root" data-composition-id="e03-timing-session" data-start="0" '
        f'data-width="{canvas_width}" data-height="{canvas_height}" data-fps="30" '
        f'data-duration="{duration:.3f}">'
        f"<style>{css(asset_prefix, canvas_width, canvas_height)}</style>"
        f'<svg id="e03-timing-session-track" class="clip" data-start="0" '
        f'data-duration="{duration:.3f}" data-track-index="0" viewBox="0 0 1280 720" '
        f'role="img" aria-label="{html.escape(label)}">'
        '<rect width="1280" height="720" fill="#0b1012" />'
        f"{groups}</svg></div><script>{script}</script></body></html>"
    )


def thumbnail_html(facts: dict) -> str:
    group = opening_group(facts)
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        "<title>E03 thumbnail</title></head><body>"
        f"<style>{css()} .state{{opacity:1}}</style>"
        '<div id="root"><svg viewBox="0 0 1280 720" role="img" '
        'aria-label="Three views, one veto"><rect width="1280" height="720" fill="#0b1012" />'
        f"{group}</svg></div></body></html>"
    )


def state_timeline(rows: list[dict], proof: bool) -> tuple[list[tuple[str, float]], float, dict[str, tuple[float, float]]]:
    """Make every receipt-bound sentence occupy a mapped visual interval."""
    cursor = 0.0
    row_timing: dict[str, tuple[float, float]] = {}
    first_for_state: dict[str, float] = {}
    for row in rows:
        duration = max(2.6, round(len(row["text"].split()) / 170 * 60 + 0.35, 3))
        start, end = round(cursor, 3), round(cursor + duration, 3)
        row_timing[row["receipt"]] = (start, end)
        state = SCENE_TO_STATE[row["slot"]]
        first_for_state.setdefault(state, start)
        cursor = end
    if proof:
        return [(state, start) for state, start in [("opening", 0.0), ("strips", 6.0), ("union", 12.0), ("veto", 18.0), ("close", 24.0)]], 30.0, row_timing
    timeline = [(state, round(first_for_state[state], 3)) for state in STATE_ORDER if state in first_for_state]
    return timeline, round(cursor, 3), row_timing


def claim_source_ids(claim_id: str) -> tuple[str, str]:
    n = int(claim_id.split("C", 1)[1])
    if n in {1, 2, 4, 5, 25, 26, 27, 28, 46, 47, 48}:
        return "run_receipt", "S_PHASE03_COUNTS"
    if n in {3, 29, 30, 31, 32, 33}:
        return "run_receipt", "S_PHASE03_UNION"
    if n in {6, 23, 49, 51, 52, 59, 60, 61}:
        return "run_receipt", "S_PHASE03_BOUNDARY"
    if n in {7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24}:
        return "academic", "S_PHASE03_METHOD"
    if n in {34, 35, 36, 37}:
        return "run_receipt", "S_ROW_3105"
    if n in {38, 39, 40, 41}:
        return "academic", "S_PROFIT_FACTOR"
    if n in {42, 43, 44, 45}:
        return "run_receipt", "S_ROW_3088"
    if n in {50, 53}:
        return "run_receipt", "S_PHASE03_SOURCE"
    if 54 <= n <= 58 or n == 62:
        return "delivery", ""
    raise ValueError(f"unmapped claim ID: {claim_id}")


def claims_doc(receipt: dict, rows: list[dict], script_hash: str) -> dict:
    phase = receipt["phase_source"]
    sources = {
        "S_PHASE03_SOURCE": {
            "citation": "Pinned phase03 timing JSON private receipt",
            "locator": f"{phase['path']}#sha256={phase['sha256']}",
            "supports": "The exact phase source identity, run identity, and hash binding used by E03.",
            "limitations": "This is a candidate-grade recorded run, not a live-execution or future-performance certificate.",
            "sha256": phase["sha256"],
        },
        "S_PHASE03_COUNTS": {
            "citation": "Derived phase03 candidate gate sets",
            "locator": f"{DERIVED_RECEIPT}#/derived/failure_counts and /derived/surviving",
            "supports": "154 entering, 41 one-bar failures, 66 session-half-1 failures, 23 session-half-2 failures, 101 unique failures, and 53 survivors.",
            "limitations": "Counts describe this run and these three thresholds only; they do not validate a strategy.",
            "sha256": sha256(DERIVED_RECEIPT),
        },
        "S_PHASE03_UNION": {
            "citation": "Derived phase03 overlap and union geometry",
            "locator": f"{DERIVED_RECEIPT}#/derived/pairwise_intersections and /derived/arithmetic",
            "supports": "Failure-set overlap and the inclusion-exclusion arithmetic that produces 101 unique failures.",
            "limitations": "The union is a count of candidate IDs, not a sum of trades or dollars.",
            "sha256": sha256(DERIVED_RECEIPT),
        },
        "S_PHASE03_METHOD": {
            "citation": "Phase03 timing/session implementation and docstring",
            "locator": f"{PHASE_CODE}#module-docstring;#_delayed_replay_twice;#_split_session_halves;#_measure_timing",
            "supports": "The one-bar same-direction delay, median-hour intraday split, and the distinction between fill stress and session splitting.",
            "limitations": "The proxy does not estimate every broker's latency or execution quality.",
            "sha256": sha256(PHASE_CODE),
        },
        "S_PROFIT_FACTOR": {
            "citation": "Robustness metric implementation",
            "locator": f"{METRICS_CODE}#compute_metrics:82-126",
            "supports": "PF is gross winning dollars divided by gross losing dollars and is returned as one metric per ledger.",
            "limitations": "PF alone does not encode drawdown, account size, path, or cost assumptions.",
            "sha256": sha256(METRICS_CODE),
        },
        "S_ROW_3105": {
            "citation": "Pinned phase03 veto candidate row",
            "locator": f"{PHASE_SOURCE}#/candidates/{ROW_VETO}/detail",
            "supports": "The three exact PF values for the candidate that fails session half 1.",
            "limitations": "One candidate row illustrates the gate; it is not a population estimate.",
            "sha256": phase["sha256"],
        },
        "S_ROW_3088": {
            "citation": "Pinned phase03 passing candidate row",
            "locator": f"{PHASE_SOURCE}#/candidates/{ROW_PASS}/detail",
            "supports": "The three exact PF values for the candidate that passes all phase03 views.",
            "limitations": "A phase03 pass is candidate-grade and does not imply validation or live readiness.",
            "sha256": phase["sha256"],
        },
        "S_PHASE03_BOUNDARY": {
            "citation": "Pinned phase03 provenance and validation flags",
            "locator": f"{DERIVED_RECEIPT}#/provenance and /run",
            "supports": "The recorded run's real-data provenance, wiring proof, and validated=false boundary.",
            "limitations": "Real-data and wiring evidence do not clear later cost, parameter, sequence, or governance questions.",
            "sha256": sha256(DERIVED_RECEIPT),
        },
    }
    claims = {}
    for row in rows:
        kind, source_id = claim_source_ids(row["receipt"])
        if kind == "delivery":
            claims[row["receipt"]] = {
                "kind": kind,
                "source_ids": [],
                "why_non_claim": "Reproduction instruction or lesson boundary; it introduces no new empirical number.",
            }
        else:
            claims[row["receipt"]] = {"kind": kind, "source_ids": [source_id]}
    return {
        "schema": "teaching-claims/v1",
        # teaching_claim_gate compares its script hash as the canonical lowercase hex form;
        # source and phase receipts remain uppercase because those are the production hashes.
        "script_sha256": script_hash.lower(),
        "sources": sources,
        "claims": claims,
        "receipt_binding": {
            "phase03_source_sha256": phase["sha256"],
            "derived_receipt_sha256": sha256(DERIVED_RECEIPT),
            "source_route": "tools/build_e03_timing_session_rebuild.py",
        },
    }


def build_visual_map(rows: list[dict], row_timing: dict[str, tuple[float, float]]) -> dict:
    cues = []
    for index, row in enumerate(rows, start=1):
        start, end = row_timing[row["receipt"]]
        state = SCENE_TO_STATE[row["slot"]]
        cues.append(
            {
                "id": f"cue-{index:03d}",
                "sentence_id": row["receipt"],
                "slot": row["slot"],
                "start_seconds": start,
                "end_seconds": end,
                "spoken_span": row["text"],
                "visual_state": state,
                "visual_path": "productions/_series/e01-e03-production-source-2026-08-03/episode-03/index.html",
                "purpose": STATE_PURPOSE[state],
                "evidence_class": "deterministic_run_data_or_method",
                "claim_refs": [row["receipt"]],
            }
        )
    return {
        "schema": "into-the-laboratory/e03-sentence-visual-map/v1",
        "episode": 3,
        "title": TITLE,
        "rule": "Every receipt-bound spoken sentence occupies a full visual interval with a purpose-built state.",
        "source_route": "tools/build_e03_timing_session_rebuild.py",
        "cues": cues,
        "state_purposes": STATE_PURPOSE,
    }


def package_documents(facts: dict, rows: list[dict], row_timing: dict[str, tuple[float, float]], source_hash: str, claims: dict, visual_map: dict, full_duration: float) -> dict:
    script_sections = []
    scenes_by_slot: OrderedDict[str, list[dict]] = OrderedDict()
    for row in rows:
        start, end = row_timing[row["receipt"]]
        state = SCENE_TO_STATE[row["slot"]]
        section = {
            "id": row["receipt"],
            "slot": row["slot"],
            "label": row["label"],
            "text": row["text"],
            "start_seconds": start,
            "end_seconds": end,
            "speaker_directions": "Plain beginner teaching; state the mechanism, then its boundary.",
            "source_ref": row["receipt"],
            "visual": {
                "path": "productions/_series/e01-e03-production-source-2026-08-03/episode-03/index.html",
                "kind": "deterministic-teaching-composition",
                "fit": "contain",
                "purpose": STATE_PURPOSE[state],
                "visibleSubjects": [state, "E03 timing/session mechanism"],
                "evidenceUse": "recorded-run-derived",
            },
        }
        script_sections.append(section)
        scenes_by_slot.setdefault(row["slot"], []).append(row)

    scenes = []
    for slot, slot_rows in scenes_by_slot.items():
        start = row_timing[slot_rows[0]["receipt"]][0]
        end = row_timing[slot_rows[-1]["receipt"]][1]
        state = SCENE_TO_STATE[slot]
        scenes.append(
            {
                "id": slot,
                "section_id": slot,
                "start_seconds": start,
                "end_seconds": end,
                "asset": f"state-{state}",
                "composition_mode": "atelier",
                "semantic_purpose": STATE_PURPOSE[state],
                "spoken_text": " ".join(row["text"] for row in slot_rows),
                "claim_refs": [row["receipt"] for row in slot_rows],
                "cues": [
                    {
                        "id": f"{row['receipt']}-visual",
                        "start_seconds": row_timing[row["receipt"]][0],
                        "end_seconds": row_timing[row["receipt"]][1],
                        "duration_seconds": round(row_timing[row["receipt"]][1] - row_timing[row["receipt"]][0], 3),
                        "asset": f"state-{state}",
                        "spoken_span": row["text"],
                        "visual_action": STATE_PURPOSE[state],
                        "claim_refs": [row["receipt"]],
                    }
                    for row in slot_rows
                ],
            }
        )

    script = {
        "version": "1.0",
        "title": TITLE,
        "total_duration_seconds": full_duration,
        "voice_performance": {
            "performance_intent": "Measured, curious beginner teaching; exact values are read as evidence, never as a promise.",
            "pacing_profile": "technical-teaching",
            "energy_curve": "Immediate result, mechanism, overlap crisis, exact rows, boundary close.",
            "pause_policy": "Brief pause after each count and exact PF; longer pause before the 53 boundary.",
            "provider_status": "not authorized before operator approval",
        },
        "sections": script_sections,
        "metadata": {
            "episode": 3,
            "syllabus_episode": "03",
            "package_revision": "e03-timing-session-rebuild-2026-08-03",
            "duration_basis_wpm": 170,
            "word_count": sum(len(row["text"].split()) for row in rows),
            "vo_sha256": source_hash,
            "phase03_source_sha256": EXPECTED_PHASE_SHA256,
            "evidence_authority": "phase03-derived-receipt.json",
            "status": "candidate_pending_operator_script_visual_thumbnail_and_proof_approval",
        },
    }
    packaging = {
        "schema": "tradercockpit-series-package/v1",
        "STATUS": "CANDIDATE — OPERATOR SCRIPT, VISUAL, THUMBNAIL, AND PROOF APPROVAL REQUIRED",
        "status": "candidate_pending_operator_approval",
        "episode": 3,
        "syllabus_episode": "03",
        "revision": "e03-timing-session-rebuild-2026-08-03",
        "title": TITLE,
        "beginner_belief": "If a backtest passes one view, it is ready for the next cost and session checks.",
        "prewriting": {
            "proven idea": "The pinned Dow phase03 JSON carries 154 candidates into three views; 101 fail at least one and 53 pass all three.",
            "common goal": "Teach a beginner how a delayed fill and session split can veto a candidate without turning a pass into a promise.",
            "deeper problem": "Three failure counts overlap, so adding 41, 66, and 23 would inflate the unique-failure result.",
            "package first": "THREE VIEWS / ONE VETO; the title leads with 53 kept and 101 failed at least one view.",
            "audience avatar": "A beginner who sees a profitable total but needs to understand why the same candidate must clear each fill and session view.",
            "research the gaps": "Recomputed the exact phase03 JSON hash, candidate gate sets, union geometry, exact veto/pass rows, and real/wiring/validated boundary.",
        },
        "thumbnail": {
            "status": "candidate; 1280x720 rendered and 150px squint emitted",
            "elements": THUMB_ELEMENTS,
            "visual_promise": "Aligned fill/session strips plus one visibly weak view; no later-phase result.",
            "html": "thumbnail-ep03.html",
        },
        "candidate_first_post_ident_sentence": TITLE,
        "first_spoken_sentence": TITLE,
        "evidence": {
            "phase03_source": str(PHASE_SOURCE),
            "phase03_source_sha256": EXPECTED_PHASE_SHA256,
            "derived_receipt": "phase03-derived-receipt.json",
            "boundary": "E03 ends at 53 phase03 survivors; cost stress is named only as the next question; validated remains false.",
            "validation_status": False,
            "real_data": bool(facts["provenance"].get("data_source") == "real"),
            "wiring_proof": bool(facts["provenance"].get("wiring_proof") is True),
        },
        "production": {
            "anchor_medium": "narration_led_deterministic_graphics",
            "render_runtime": "hyperframes",
            "render_runtime_version": "0.7.90",
            "composition_mode": "atelier",
            "music": "none",
            "full_render_started": False,
            "semantic_proof_only": True,
        },
        "script": {
            "status": "candidate_pending_script_human_gate",
            "sha256": "generated-after-script-write",
            "vo_sha256": source_hash,
            "word_count": script["metadata"]["word_count"],
            "estimated_duration_seconds": full_duration,
            "duration_basis_wpm": 170,
        },
        "approval": {
            "package_approved": False,
            "complete_script_approved": False,
            "thumbnail_approved": False,
            "semantic_proof_approved": False,
            "narration_approved": False,
            "master_approved": False,
            "historical_approvals_authoritative": False,
        },
    }
    scene_plan = {
        "schema": "openmontage/scene-plan/v1",
        "episode": "03",
        "title": TITLE,
        "script_sha256": source_hash,
        "composition_mode": "atelier",
        "render_runtime": "hyperframes",
        "semantic_rule": "Every receipt-bound sentence is mapped to a purpose-built deterministic visual state; no generic card replaces the mechanism.",
        "scenes": scenes,
        "proof_scope": "Short semantic proof only: opening, aligned strips, overlap/union, veto row, and 53 boundary. No narration or master.",
    }
    edit_decisions = {
        "schema": "openmontage/edit-decisions/v1",
        "metadata": {"gate_profile": "board-led-explainer", "episode": 3, "approval_status": "candidate"},
        "audio": {"narration": {"status": "not generated", "segments": []}, "music": {"status": "none"}},
        "cuts": [{"id": scene["id"], "in_seconds": scene["start_seconds"], "out_seconds": scene["end_seconds"], "type": "deterministic-teaching-composition"} for scene in scenes],
        "full_render_started": False,
    }
    academic_timing = {
        "schema": "into-the-laboratory/academic-edit-timing/v1",
        "episode": 3,
        "duration_seconds": full_duration,
        "sentence_cues": visual_map["cues"],
        "coverage": {"spoken_sentences": len(rows), "mapped_sentences": len(visual_map["cues"]), "unmapped": []},
    }
    return {"script": script, "packaging": packaging, "scene_plan": scene_plan, "edit_decisions": edit_decisions, "academic_timing": academic_timing}


def build(facts: dict, rows: list[dict]) -> dict:
    source_hash = sha256(VO_SOURCE)
    write_json(DERIVED_RECEIPT, source_receipt(facts))
    repair_live_receipt_manifest(facts)
    timeline, full_duration, row_timing = state_timeline(rows, proof=False)
    proof_timeline, proof_duration, _ = state_timeline(rows, proof=True)
    visual_map = build_visual_map(rows, row_timing)
    write_json(VISUAL_MAP_SOURCE, visual_map)
    claims = claims_doc(json.loads(DERIVED_RECEIPT.read_text(encoding="utf-8")), rows, source_hash)
    documents = package_documents(facts, rows, row_timing, source_hash, claims, visual_map, full_duration)

    PACKAGE.mkdir(parents=True, exist_ok=True)
    write_text_lf(PACKAGE / "vo.txt", VO_SOURCE.read_text(encoding="utf-8"))
    write_json(PACKAGE / "script.json", documents["script"])
    documents["packaging"]["script"]["sha256"] = sha256(PACKAGE / "script.json")
    write_json(PACKAGE / "claims.json", claims)
    write_json(PACKAGE / "packaging.json", documents["packaging"])
    write_json(PACKAGE / "scene_plan.json", documents["scene_plan"])
    write_json(PACKAGE / "edit_decisions.json", documents["edit_decisions"])
    write_json(PACKAGE / "academic_edit_timing.json", documents["academic_timing"])
    write_json(PACKAGE / "scene_visual_map.json", visual_map)
    write_text_lf(PACKAGE / "thumbnail-ep03.html", thumbnail_html(facts))
    write_json(PACKAGE / "phase03-derived-receipt.json", json.loads(DERIVED_RECEIPT.read_text(encoding="utf-8")))

    SOURCE.mkdir(parents=True, exist_ok=True)
    source_index = html_document(facts, timeline, full_duration, proof=False)
    write_text_lf(SOURCE / "index.html", source_index)
    if (SOURCE_ROOT / "assets/fonts").is_dir():
        for font in (SOURCE_ROOT / "assets/fonts").glob("*.ttf"):
            (SOURCE / "assets/fonts").mkdir(parents=True, exist_ok=True)
            shutil.copy2(font, SOURCE / "assets/fonts" / font.name)

    OM_HYPERFRAMES.mkdir(parents=True, exist_ok=True)
    OM_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    om_root_assets = OM_PROJECT / "assets"
    om_root_assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(GSAP_ASSET, om_root_assets / "gsap.min.js")
    root_font_dir = om_root_assets / "fonts"
    root_font_dir.mkdir(parents=True, exist_ok=True)
    for font in (SOURCE / "assets/fonts").glob("*.ttf"):
        shutil.copy2(font, root_font_dir / font.name)
    (OM_HYPERFRAMES / "assets").mkdir(parents=True, exist_ok=True)
    shutil.copy2(GSAP_ASSET, OM_HYPERFRAMES / "assets/gsap.min.js")
    font_dir = OM_HYPERFRAMES / "assets/fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    for font in (SOURCE / "assets/fonts").glob("*.ttf"):
        shutil.copy2(font, font_dir / font.name)
    write_text_lf(OM_HYPERFRAMES / "index.html", source_index)
    proof_html = html_document(facts, proof_timeline, proof_duration, proof=True)
    legacy_proof = OM_HYPERFRAMES / "semantic-proof.html"
    if legacy_proof.is_file():
        legacy_proof.unlink()
    write_text_lf(OM_PROOF, proof_html)
    write_text_lf(OM_ARTIFACTS / "vo.txt", VO_SOURCE.read_text(encoding="utf-8"))
    for name, value in (
        ("script.json", documents["script"]),
        ("packaging.json", documents["packaging"]),
        ("scene_plan.json", documents["scene_plan"]),
        ("claims.json", claims),
        ("edit_decisions.json", documents["edit_decisions"]),
        ("academic_edit_timing.json", documents["academic_timing"]),
        ("scene_visual_map.json", visual_map),
        ("phase03-derived-receipt.json", json.loads(DERIVED_RECEIPT.read_text(encoding="utf-8"))),
    ):
        write_json(OM_ARTIFACTS / name, value)
    (OM_PROJECT / "docs").mkdir(parents=True, exist_ok=True)
    if SYLLABUS_SOURCE.is_file():
        shutil.copy2(SYLLABUS_SOURCE, OM_PROJECT / "docs/syllabus.md")
    write_json(OM_PROJECT / "project.json", {"version": "1.0", "project_id": "series-e03-timing-session-rebuild", "title": TITLE, "pipeline_type": "animation", "style_playbook": "atelier"})

    receipt = {
        "schema": SCHEMA_VERSION,
        "episode": 3,
        "title": TITLE,
        "status": "candidate_pending_operator_script_visual_thumbnail_and_proof_approval",
        "source_route": "tools/build_e03_timing_session_rebuild.py",
        "phase03_source_sha256": EXPECTED_PHASE_SHA256,
        "gsap_sha256": EXPECTED_GSAP_SHA256,
        "derived_receipt_sha256": sha256(DERIVED_RECEIPT),
        "vo_sha256": source_hash,
        "visual_map_sha256": sha256(VISUAL_MAP_SOURCE),
        "source_html_sha256": sha256(SOURCE / "index.html"),
        "thumbnail_html_sha256": sha256(PACKAGE / "thumbnail-ep03.html"),
        "full_duration_seconds": full_duration,
        "word_count": documents["script"]["metadata"]["word_count"],
        "sentence_visual_coverage": documents["academic_timing"]["coverage"],
        "semantic_proof": {
            "project": str(OM_PROJECT),
            "composition": "hyperframes/proofs/semantic-proof.html",
            "duration_seconds": proof_duration,
            "not_narrated": True,
            "not_master": True,
        },
        "not_done": ["no narration", "no provider generation", "no full master render", "no upload", "no publication"],
    }
    write_json(PACKAGE / "e03-rebuild-receipt.json", receipt)
    return receipt


def main() -> int:
    global PHASE_SOURCE
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase-source", type=Path, default=PHASE_SOURCE)
    args = parser.parse_args()
    PHASE_SOURCE = args.phase_source
    require_file(PHASE_SOURCE)
    actual_sha = sha256(PHASE_SOURCE)
    if actual_sha != EXPECTED_PHASE_SHA256:
        raise SystemExit(f"BLOCK: phase03 SHA-256 drifted: {actual_sha} != {EXPECTED_PHASE_SHA256}")
    payload = json.loads(PHASE_SOURCE.read_text(encoding="utf-8"))
    facts = derive_phase03_facts(payload)
    assert_phase03_truth(facts)
    rows = parse_vo(VO_SOURCE)
    receipt = build(facts, rows)
    print(json.dumps(receipt, indent=2))
    print(f"PASS: E03 derived from {EXPECTED_PHASE_SHA256}; 154 -> 53 with 101 unique failures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
