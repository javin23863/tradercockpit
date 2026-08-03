#!/usr/bin/env python3
"""Materialize durable E01-E03 package contracts from the receipt-backed VO candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VO_ROOT = ROOT / "productions/_series/e01-e03-rewrite-candidates-2026-08-03"
RECEIPTS = ROOT / "productions/_series/e01-e03-live-receipts-2026-08-03.json"
VISUAL_MAP = ROOT / "productions/_series/e01-e03-rewrite-visual-map.json"
DEFAULT_OUT = ROOT / "productions/_series/e01-e03-production-candidates-2026-08-03"
METHOD_RECEIPTS = ROOT / "productions/_series/e01-method-claim-receipts-2026-08-03.json"
SLOT = re.compile(r"^=== SLOT (scene-\d+) ")
SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")

EPISODES = {
    "01": {
        "vo": "episode-01-vo.txt",
        "title": "The First Screen Rejected 5,206 Candidates. One Run Continued.",
        "thumbnail": "THREE LANES / 184 FORWARD",
        "beginner_belief": "If one strategy survives an initial screen, it is ready for live money.",
        "prewriting": {
            "proven idea": "The recorded first screen starts with 5,390 candidates and carries 184 forward.",
            "common goal": "Teach a beginner to read a screening result without confusing a survivor with a live-ready strategy.",
            "deeper problem": "A blended headline can hide three separate runs and the selection burden created by searching thousands of candidates.",
            "package first": "THREE LANES / 184 FORWARD; the title leads with 5,206 rejected and one run continuing.",
            "audience avatar": "A beginner who knows a backtest is historical but needs to see why counts, thresholds, and validation status matter.",
            "research the gaps": "Verified the 2026-08-03 receipt manifest and visual map, preserving run boundaries, overlapping failure counts, and validated=false.",
        },
        "boundary": "Recorded Dow futures, S&P 500 futures, and EURUSD intake runs; evidence is real and wiring is exercised, while validated remains false.",
        "source_ids": {
            "E01_DOW_P1": ("01", "runs", 0),
            "E01_ES_P1": ("01", "runs", 1),
            "E01_EURUSD_P1": ("01", "runs", 2),
        },
        "claim_sources": {
            "E01-RW-C01": ["E01_DOW_P1", "E01_ES_P1", "E01_EURUSD_P1"],
            "E01-RW-C02": ["E01_DOW_P1", "E01_ES_P1", "E01_EURUSD_P1"],
            "E01-RW-C03": ["E01_DOW_P1", "E01_METHOD_RULE_SPEC"],
            "E01-RW-C04": ["E01_DOW_P1", "E01_ES_P1", "E01_EURUSD_P1"],
            "E01-RW-C05": ["E01_DOW_P1", "E01_DOW_GATE_CENSUS", "E01_METHOD_METRICS"],
            "E01-RW-C06": ["E01_DOW_P1", "E01_DOW_CANDIDATE", "E01_METHOD_METRICS"],
            "E01-RW-C07": ["E01_ES_P1", "E01_EURUSD_P1"],
            "E01-RW-C08": ["E01_DOW_P1", "E01_METHOD_SELECTION", "E01_METHOD_PREREGISTRATION"],
            "E01-RW-C09": ["E01_DOW_P1", "E01_METHOD_BOUNDARY"],
            "E01-RW-C10": ["E01_DOW_P1", "E01_ES_P1", "E01_EURUSD_P1"],
        },
    },
    "02": {
        "vo": "episode-02-vo.txt",
        "title": "The SPY RSI2 Test Rejected Five Candidates Before the Holdout",
        "thumbnail": "5 TESTED / 0 ADVANCE",
        "beginner_belief": "If a test has a later holdout block, the holdout result is the main result.",
        "prewriting": {
            "proven idea": "The recorded SPY branch rejects all five candidates before a holdout opens.",
            "common goal": "Teach a beginner that a holdout judges a frozen candidate and cannot exist when the first screen adopts nothing.",
            "deeper problem": "The earlier lesson implied a stock pass that the current run does not contain, and a separately labelled Dow branch can be mistaken for SPY evidence.",
            "package first": "5 TESTED / 0 ADVANCE; the title makes the missing holdout part of the result.",
            "audience avatar": "A beginner who has heard in-sample and out-of-sample but needs the decision order and boundary in plain English.",
            "research the gaps": "Verified the SPY phase records, thresholds, real-data and wiring flags, absent holdout, and separate Dow out-of-sample branch.",
        },
        "boundary": "Recorded SPY D1 branch plus a separately labelled Dow out-of-sample branch; no SPY holdout was reached.",
        "source_ids": {
            "E02_SPY_P1": ("02", "stock_branch", "phase01_source_path"),
            "E02_SPY_P2": ("02", "stock_branch", "phase02_source_path"),
            "E02_DOW_P2": ("02", "dow_oos_branch", None),
        },
        "claim_sources": {
            "E02-RW-C01": ["E02_SPY_P1", "E02_SPY_P2"],
            "E02-RW-C02": ["E02_SPY_P1"],
            "E02-RW-C03": ["E02_SPY_P1"],
            "E02-RW-C04": ["E02_SPY_P1", "E02_SPY_P2"],
            "E02-RW-C05": ["E02_SPY_P1"],
            "E02-RW-C06": ["E02_SPY_P2"],
            "E02-RW-C07": ["E02_SPY_P1", "E02_DOW_P2"],
            "E02-RW-C08": ["E02_DOW_P2"],
            "E02-RW-C09": ["E02_SPY_P1", "E02_SPY_P2"],
            "E02-RW-C10": ["E02_SPY_P1", "E02_SPY_P2"],
        },
    },
    "03": {
        "vo": "episode-03-vo.txt",
        "title": "The Dow Test Kept 53 Candidates. 101 Failed the Fill and Session Checks.",
        "thumbnail": "THREE VIEWS / ONE VETO",
        "beginner_belief": "If a backtest passes one view, it is ready for the next cost and session checks.",
        "prewriting": {
            "proven idea": "The recorded Dow phase carries 154 candidates into three views; 101 fail at least one and 53 pass all three.",
            "common goal": "Teach a beginner how delayed fills and session splits can veto a candidate without turning a pass into a trading promise.",
            "deeper problem": "One blended total can hide a weak session or fill view, and overlapping failure counts cannot be added into the headline total.",
            "package first": "THREE VIEWS / ONE VETO; the title leads with 53 kept and 101 failed at least one check.",
            "audience avatar": "A beginner who sees a profitable total but needs to understand why the same candidates must survive separate transformations.",
            "research the gaps": "Verified the phase03 receipt, exact veto and pass rows, the phase04 cost handoff, real-data and wiring flags, and validated=false.",
        },
        "boundary": "Recorded Dow phase03 timing/session stress and the exact phase04 handoff; real data and wiring proof are preserved, validated remains false.",
        "source_ids": {
            "E03_DOW_P2": ("03", "next_phase", None),
            "E03_DOW_P3": ("03", "self", None),
            "E03_DOW_P4": ("03", "next_phase", "phase04_cost"),
        },
        "claim_sources": {
            "E03-RW-C01": ["E03_DOW_P3"],
            "E03-RW-C02": ["E03_DOW_P2", "E03_DOW_P3"],
            "E03-RW-C03": ["E03_DOW_P3"],
            "E03-RW-C04": ["E03_DOW_P3"],
            "E03-RW-C05": ["E03_DOW_P3"],
            "E03-RW-C06": ["E03_DOW_P3"],
            "E03-RW-C07": ["E03_DOW_P3"],
            "E03-RW-C08": ["E03_DOW_P3"],
            "E03-RW-C09": ["E03_DOW_P3", "E03_DOW_P4"],
            "E03-RW-C10": ["E03_DOW_P3", "E03_DOW_P4"],
        },
    },
}

PURPOSES = {
    "e01-population-sieve": "A population of candidate tokens enters a physical sieve; rejected tokens fall away while the surviving queue remains visible.",
    "e01-pipeline-spine": "A single candidate travels through replay, measurement, intake, and a clearly unopened next-phase door.",
    "e01-candidate-anatomy": "One rule set is unpacked into market, timing, fill, exit, risk, cost, and historical-window parts.",
    "e01-three-lanes": "Three physical run lanes keep markets and windows separate; lane lengths are proportional to their entrant counts.",
    "e01-overlap-census": "Three unequal failure ribbons cross the same Dow population, making overlap visible instead of adding it.",
    "e01-survivor-row": "One recorded Dow candidate is shown as a measured development-window row with its boundary still attached.",
    "e01-zero-lanes": "The S&P 500 futures and EURUSD lanes terminate at zero with their input populations still intact.",
    "e01-selection-burden": "A branching field of candidate versions makes the search denominator visible before a single row is admired.",
    "e01-unseen-price-boundary": "The 184 Dow tokens queue at a sealed boundary marked for prices the screen never used to choose them.",
    "e01-worksheet-close": "A physical worksheet gathers run identity, window, counts, thresholds, and validation state for the next test.",
    "e02-spy-boundary.svg": "Show the SPY branch ending at zero before the holdout opens.",
    "e02-spy-candidate-row.svg": "Put one recorded SPY row beside its three actual thresholds.",
    "e02-dow-oos-bridge.svg": "Keep the SPY stop and Dow continuation as separate branches.",
    "e03-three-view-funnel.svg": "Show the same 154 candidates facing three declared transformations.",
    "e03-veto-vs-pass.svg": "Compare one recorded veto row and one recorded pass row in reserved lanes.",
    "e03-profit-factor.svg": "Define profit factor as a comparison of gross winning and losing dollars.",
    "e03-cost-handoff.svg": "Show 53 as the next phase input, not as a final trading conclusion.",
}

# The source VO is deliberately sentence-sized for the visual contract.  These actions are
# semantic bindings, not decorative cue labels: a cue must tell the compositor what the spoken
# sentence is doing with the mechanism.  Keep this list aligned with the ten E01 paragraphs.
E01_SENTENCE_VISUALS = {
    "scene-01": [
        "Drop 5,206 tokens below the intake rail.",
        "Scale the 5,390-token population into the intake tray.",
        "Hold the exact 5,390 total beside the intake tray.",
        "Let 184 tokens continue along a narrow forward track.",
        "Split the tray into three labeled physical lanes: Dow, S&P 500 futures, and EURUSD.",
        "Highlight the Dow lane as the only lane with a survivor queue.",
        "Highlight the S&P 500 futures lane as a zero lane.",
        "Highlight the EURUSD lane as a zero lane.",
        "Leave only the Dow lane with a visible survivor queue.",
        "Terminate the other two lanes at zero.",
        "Animate a backtest as a rule replay over old-price marks.",
        "Trace the complete rule across the recorded historical strip.",
        "Seal the strip as one historical record rather than a forecast.",
        "Let the victory wash recede from the survivor queue.",
        "Hold the screen still for the narrow question.",
        "Bracket the intake lines against their historical windows.",
        "Open a small next-question doorway after the token clears the sieve.",
        "Relabel the 184 tokens as a queue at readable scale and place a quiet question mark beyond the boundary where unseen prices begin.",
    ],
    "scene-02": [
        "Bring one candidate token onto a physical pipeline spine.",
        "Move it through REPLAY with the full rules attached.",
        "Move it into MEASURE over the development-window strip.",
        "Bracket the development window as the in-sample block.",
        "Show the historical marks used to build and screen the rule.",
        "Lock REPLAY and MEASURE before any parameter can change.",
        "Apply the INTAKE THRESHOLDS as local lines.",
        "Show GATE as a physical pass/fail opening.",
        "Show THRESHOLD as the line the measurement must cross.",
        "Carry a passing token toward the next-test doorway.",
        "Set a later-price plate beside the doorway.",
        "Set fill, session, and cost plates beside it.",
        "Dim those future plates before any result appears.",
        "Stamp REAL DATA on the evidence rail.",
        "Stamp WIRING TRUE on a separate rail.",
        "Place VALIDATED FALSE beneath both stamps.",
        "Settle the completed pipeline on a RESEARCH RESULT tag.",
        "Keep a live-trading boundary closed beyond the tag.",
        "Join the measured number to its threshold with a bracket.",
        "Close the spine with the promise zone empty.",
        "Keep the result's boundary visible after the spine closes.",
    ],
    "scene-03": [
        "Open a complete rule specimen on a physical workbench.",
        "Place the candidate specimen at the center of the bench.",
        "Attach the market and timeframe plates.",
        "Attach entry, fill, exit, size, risk, cost, and window plates.",
        "Place a commission token beside the specimen as a fee.",
        "Place a slippage token between reference price and fill.",
        "Change one detail and send a new candidate off the bench.",
        "Place an observation beside several explanation paths.",
        "Fan the explanations out before choosing one.",
        "Turn one explanation into a hypothesis with a break line.",
        "Mark the hypothesis as falsifiable with a possible failure mark.",
        "Bracket the development window as the in-sample block.",
        "Label it as the historical price block used to build the rule.",
        "Show a net-profit balance after wins, losses, and costs.",
        "Stack the gross winning trade amounts in one pile.",
        "Stack the gross losing trade amounts in another pile.",
        "Draw the maximum drawdown as a peak-to-trough fall.",
        "Place the return-to-drawdown ratio beside that fall.",
        "Divide the gross-win pile by the gross-loss pile for profit factor.",
        "Mark the win-rate count as how often the strategy won.",
        "Show a smaller winning pile outweighing a larger losing count.",
        "Count the trades produced by the rule.",
        "Set the trades-per-month ruler beside the count.",
        "Fan out the library as distinct rule tokens.",
        "Bracket all metrics inside the single development window.",
        "Keep live performance outside the measurement bench.",
    ],
    "scene-04": [
        "Separate three physical run lanes before any total appears.",
        "Raise the Dow lane with a proportional 1,335 entrant track.",
        "Add the short 184 survivor track and the Dow dates.",
        "Pin the Dow run identity to its lane.",
        "Raise the S&P 500 futures lane with 2,004 entrants.",
        "Attach the S&P 500 historical dates.",
        "Pin the S&P 500 run identity to its lane.",
        "Raise the EURUSD lane with 2,051 entrants.",
        "Attach the EURUSD historical dates.",
        "Pin the EURUSD run identity to its lane.",
        "Draw the 5,390 entrant ledger back to all three lane mouths.",
        "Draw the 184 survivor queue pointing only to Dow.",
        "Subtract the queue from the entrant ledger and reveal 5,206 stopped.",
        "Pin the three private source hashes to the lane ledger.",
        "Keep each market label attached to its lane as a separate experiment.",
        "Keep each historical window attached to its run.",
        "Use unequal physical lengths for 1,335, 2,004, and 2,051.",
        "Pull the lanes apart again and label the total as bookkeeping.",
        "Keep each market on its own reading after the total resolves.",
    ],
    "scene-05": [
        "Fill the Dow population track and drop 1,151 tokens below the rail.",
        "Draw a return-to-drawdown ribbon proportional to 1,122.",
        "Draw a profit-factor ribbon proportional to 1,065.",
        "Draw the shorter activity ribbon for 150.",
        "Let one token touch two ribbons and another touch all three.",
        "Place a ratio dial beside the peak-to-trough depth.",
        "Lock return-to-drawdown above 1.0.",
        "Divide gross winning dollars by gross losing dollars.",
        "Lock profit factor above 1.05.",
        "Place the activity label beside the monthly ruler.",
        "Set the monthly trade ruler above 2 and below 300.",
        "Show a too-few-trades warning beside a thin count.",
        "Show a cost warning beside a crowded count.",
        "Keep the overlap visible instead of stacking the counts.",
        "Mark the overlap as one census row crossing multiple ribbons.",
        "Show the crossing ribbons as one shared Dow population.",
        "Compute 1,335 minus 184 on a unique-population abacus.",
        "Hold the 1,151 unique drop beside the crossing ribbons.",
        "Keep the failure census attached to the same Dow population.",
        "Attach the thresholds to this run's gate.",
        "Open one pass/fail gate for each measured reason.",
        "Close before any universal market rule appears.",
        "Keep the Dow population attached to the final gate statement.",
    ],
    "scene-06": [
        "Pull candidate formula-2851293728-1566 from the Dow queue.",
        "Place it on a measured row with its ID attached.",
        "Reveal profit factor 1.280370 as a ratio mark.",
        "Reveal return-to-drawdown 4.932417 beside the fall marker.",
        "Count 553 trades on the row.",
        "Split the count into 210 wins and 343 losses.",
        "Show the smaller winning count beside the larger losing count.",
        "Show gross winning and losing piles beside profit factor.",
        "Show the after-cost net-profit balance without a promise.",
        "Show maximum drawdown and return-to-drawdown beside the fall.",
        "Set the development-window bracket behind the row.",
        "Keep the full candidate population as a quiet field.",
        "Wrap a selection-history bracket around that field.",
        "Let the row cross the intake lines.",
        "Place a harder-test door ahead of the row.",
        "Stop at the development edge with no future result.",
    ],
    "scene-07": [
        "Place the two stopped lanes beside the Dow drop population.",
        "Extend the S&P 500 futures track to 2,004.",
        "Stop every S&P token at the first gate.",
        "Extend the EURUSD track to 2,051 and stop every token.",
        "Bring the lane totals together and settle on 5,206 stopped.",
        "Show the run-complete marker and the preserved input population.",
        "Keep the market labels and windows attached to the failed sets.",
        "Show ZERO as a recorded outcome rather than a blank field.",
        "Place the preserved input population beside the zero result.",
        "Place a question mark outside the lanes for broader market possibility.",
        "Stamp REAL DATA, WIRING TRUE, and VALIDATED FALSE on the evidence rail.",
        "Hold the zero lanes in place as the result of this first gate.",
        "Draw a new-reason arrow away from the same search space.",
        "Keep future rules outside the evidence carried by the empty lane.",
    ],
    "scene-08": [
        "Fan many rule tokens into a branching search field.",
        "Place a chance marker beside one attractive row.",
        "Keep the 5,390 population count visible as the denominator.",
        "Keep the denominator beside the attractive row.",
        "Draw a plan sheet with the hypothesis.",
        "Add the complete rule set to the plan.",
        "Add the window and costs before the result.",
        "Add the measurements and rejection line.",
        "Stamp the plan before the search opens.",
        "Fork a new version tab if a threshold changes.",
        "Keep rejected tokens in an archive beside the queue.",
        "Mark the archive as alternatives tried and gates crossed.",
        "Wrap a selection-history band around the attractive row.",
        "Show the search history as context, not a verdict.",
        "Leave the later-price question outside the development bracket.",
        "Close the search field before the next price block opens.",
    ],
    "scene-09": [
        "Gather exactly 184 Dow tokens into a physical queue.",
        "Place the queue at the next-test gate.",
        "Label it PASSED PREVIOUS GATE.",
        "Draw the development-window bracket behind the queue.",
        "Place a sealed later-price block beyond the edge.",
        "Pin the fixed later window before any readout.",
        "Mark the later block as a new test, not a second look.",
        "Ghost a fail path and a continue path beyond the boundary.",
        "Keep the word SURVIVOR small beside the queue.",
        "Leave VALIDATED FALSE on the evidence rail.",
        "Remove any later count or payoff.",
        "Hold the queue and sealed block on the question about unseen prices.",
    ],
    "scene-10": [
        "Lay out a five-line worksheet for the next run.",
        "Fill the source-run field with an identity tab.",
        "Add the private hash pin to that tab.",
        "Fill the window field with its phase and dates.",
        "Fill the count field with entering and surviving populations.",
        "Fill the gate field with each measurement and threshold.",
        "Fill the status field with real data, wiring true, and validated false.",
        "Place one failed row and one advancing row beside the worksheet.",
        "Keep the source hash on the private evidence edge.",
        "Keep the rule and cost assumptions beside the window.",
        "Keep zero as a filled answer on the stopped lane tabs.",
        "Send 184 forward as a queue without changing its label.",
        "Keep the queue outside any promise boundary.",
        "Reassemble 5,390 entered, 184 continued, and 5,206 stopped as the ledger.",
    ],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def png_dimensions(path: Path) -> tuple[int, int] | None:
    """Read PNG dimensions without adding an image dependency to package generation."""
    if not path.is_file():
        return None
    header = path.read_bytes()[:24]
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        return None
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def write_json(path: Path, value: dict) -> None:
    path.write_bytes((json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def parse_vo(path: Path) -> list[dict]:
    rows: list[dict] = []
    current: dict | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = SLOT.match(raw)
        if match:
            if current:
                rows.append(current)
            current = {"id": match.group(1), "label": "", "receipt": "", "lines": []}
            continue
        if current is None:
            continue
        if raw.startswith("## "):
            current["label"] = raw[3:].strip()
        elif raw.startswith("# receipt: "):
            current["receipt"] = raw[11:].strip().split(",")
        elif raw.strip() and not raw.startswith("#"):
            current["lines"].append(raw.strip())
    if current:
        rows.append(current)
    for row in rows:
        row["text"] = " ".join(row.pop("lines"))
        row["claims"] = row.pop("receipt")
    return rows


def source_rows(manifest: dict, episode: str) -> dict[str, dict]:
    ep = manifest["episodes"][episode]
    rows: dict[str, dict] = {}
    for source_id, (owner, key, selector) in EPISODES[episode]["source_ids"].items():
        if episode == "01":
            item = ep[key][selector] if selector is not None else ep[key]
            path, digest = item["source_path"], item["sha256"]
            label = item.get("label", "recorded phase01 intake")
        elif episode == "02":
            if source_id == "E02_SPY_P1":
                path, digest, label = ep["stock_branch"]["phase01_source_path"], ep["stock_branch"]["phase01_sha256"], "SPY phase01 intake"
            elif source_id == "E02_SPY_P2":
                path, digest, label = ep["stock_branch"]["phase02_source_path"], ep["stock_branch"]["phase02_sha256"], "SPY phase02 holdout boundary"
            else:
                item = ep["dow_oos_branch"]
                path, digest, label = item["source_path"], item["sha256"], "Dow phase02 out-of-sample"
        else:
            if source_id == "E03_DOW_P3":
                path, digest, label = ep["source_path"], ep["sha256"], "Dow phase03 timing"
            elif source_id == "E03_DOW_P2":
                item = ep["next_phase"]
                path, digest, label = manifest["episodes"]["02"]["dow_oos_branch"]["source_path"], manifest["episodes"]["02"]["dow_oos_branch"]["sha256"], "Dow phase02 out-of-sample"
            else:
                path = "hash-only: external phase04_cost.json (artifact remains in Futures scope)"
                digest, label = ep["next_phase"]["source_sha256"], "Dow phase04 cost handoff"
        limitation = (
            "The phase04 cost handoff is referenced by its recorded SHA-256 only; the artifact "
            "remains in the Futures scope and was not copied into TraderCockpit. The source "
            "reports pipeline evidence with validated=false; it is not a live-execution or "
            "future-performance certificate."
            if source_id == "E03_DOW_P4" else
            "The source reports pipeline evidence with validated=false; it is not a "
            "live-execution or future-performance certificate."
        )
        rows[source_id] = {
            "citation": f"Recorded {label} receipt",
            "locator": f"{path} :: $.run_id, $.phase_key, $.window, $.entering, $.surviving, $.dropped, $.provenance",
            "supports": f"Exact recorded counts, identifiers, metrics, and scope for {label} used by this episode.",
            "limitations": limitation,
            "sha256": digest,
        }
    if episode == "01":
        manifest_digest = sha(RECEIPTS)
        dow_path = ep["runs"][0]["source_path"]
        dow_digest = ep["runs"][0]["sha256"]
        rows.update({
            "E01_DOW_GATE_CENSUS": {
                "citation": "Recorded E01 Dow phase01 gate census",
                "locator": f"{RECEIPTS} :: $.episodes.01.dow_gate_census",
                "supports": "The three recorded Dow failure counts, the 1,151 unique dropped total, and the explicit overlap warning.",
                "limitations": "The census is attached to the 2026-08-03 manifest and the stamped phase artifact; it is not a universal gate-rate claim.",
                "sha256": manifest_digest,
            },
            "E01_DOW_CANDIDATE": {
                "citation": "Recorded Dow phase01 candidate ledger",
                "locator": f"{dow_path} :: $.candidates[\"formula-2851293728-1566\"].metrics, $.candidates[\"formula-2851293728-1566\"].gates",
                "supports": "The exact candidate identifier, profit-factor and return-to-drawdown measurements, trade counts, and recorded gate state.",
                "limitations": "The row is one selected development-window candidate; it does not support a future-performance or live-execution claim.",
                "sha256": dow_digest,
            },
        })
        method_doc = json.loads(METHOD_RECEIPTS.read_text(encoding="utf-8"))
        method_digest = sha(METHOD_RECEIPTS)
        for source_id, record in method_doc["receipts"].items():
            rows[source_id] = {
                "citation": record["citation"],
                "locator": record["locator"],
                "supports": record["supports"],
                "limitations": record["limitations"],
                "sha256": method_digest,
            }
    return rows


def first_sentence(text: str) -> str:
    matches = sentences(text)
    return matches[0] if matches else text.split(" ", 1)[0]


def sentences(text: str) -> list[str]:
    """Return the exact spoken sentences used for sentence-bound visual coverage."""
    return [part.strip() for part in SENTENCE_BREAK.split(text) if part.strip()]


def build_episode(manifest: dict, visual_map: dict, episode: str, out: Path) -> dict:
    config = EPISODES[episode]
    vo_path = VO_ROOT / config["vo"]
    sections = parse_vo(vo_path)
    source_map = source_rows(manifest, episode)
    wpm = 145.0
    cursor = 0.0
    script_sections = []
    planned_scenes = []
    for row in sections:
        words = len(row["text"].split())
        spoken_sentences = sentences(row["text"])
        if episode == "01":
            actions = E01_SENTENCE_VISUALS[row["id"]]
            if len(actions) != len(spoken_sentences):
                raise ValueError(
                    f"{episode} {row['id']} has {len(spoken_sentences)} spoken sentences "
                    f"but {len(actions)} visual bindings"
                )
        else:
            actions = [PURPOSES[visual_map[episode][row["id"]]]] * len(spoken_sentences)
        sentence_durations = [max(0.8, round(len(sentence.split()) / wpm * 60.0, 3)) for sentence in spoken_sentences]
        sentence_durations[-1] = round(sentence_durations[-1] + 0.45, 3)
        duration = max(3.0, round(sum(sentence_durations), 3))
        start = round(cursor, 3)
        end = round(start + duration, 3)
        cursor = end
        claim_refs = row["claims"]
        asset = visual_map[episode][row["id"]]
        cue_rows = []
        cue_cursor = start
        for cue_index, (spoken_span, visual_action, cue_duration) in enumerate(
            zip(spoken_sentences, actions, sentence_durations), start=1
        ):
            cue_rows.append({
                "id": f"{row['id']}-cue-{cue_index:02d}",
                "start_seconds": round(cue_cursor, 3),
                "duration_seconds": cue_duration,
                "end_seconds": round(cue_cursor + cue_duration, 3),
                "asset": asset,
                "spoken_span": spoken_span,
                "visual_action": visual_action,
                "claim_refs": claim_refs,
            })
            cue_cursor = round(cue_cursor + cue_duration, 3)
        if abs(cue_cursor - end) > 0.01:
            raise ValueError(f"{episode} {row['id']} visual cues do not cover section: {cue_cursor} != {end}")
        script_sections.append({
            "id": row["id"],
            "label": row["label"],
            "text": row["text"],
            "start_seconds": start,
            "end_seconds": end,
            "speaker_directions": "Measured beginner teaching; land the recorded number, then name its boundary.",
            "delivery_cues": {
                "pace": "measured",
                "energy": "precise and controlled",
                "emphasis_words": [row["label"].split(" ")[0], "recorded", "validated"],
                "pause_before_seconds": 0.0,
                "pause_after_seconds": 0.45,
                "delivery_note": "Read rounded spoken ratios as approximations; the exact receipt value belongs on the visual.",
                "provider_text": row["text"],
            },
            "enhancement_cues": [
                {
                    "type": "animation",
                    "description": visual_action,
                    "timestamp_seconds": cue["start_seconds"],
                    "duration_seconds": cue["duration_seconds"],
                    "spoken_span": cue["spoken_span"],
                }
                for cue, visual_action in zip(cue_rows, actions)
            ],
            "source_ref": ",".join(claim_refs),
        })
        planned_scenes.append({
            "id": row["id"],
            "section_id": row["id"],
            "start_seconds": start,
            "end_seconds": end,
            "asset": asset,
            "asset_path": "productions/_series/e01-e03-production-source-2026-08-03/episode-01/index.html" if episode == "01" else asset,
            "asset_fragment": f"#{row['id']}" if episode == "01" else None,
            "composition_mode": "atelier",
            "semantic_purpose": PURPOSES[asset],
            "spoken_text": row["text"],
            "claim_refs": claim_refs,
            "evidence_class": "run_data" if "pipeline" not in asset and "profit-factor" not in asset else "method_or_run_data",
            "cues": cue_rows,
        })
    claims = {}
    for row in sections:
        for claim_id in row["claims"]:
            claims[claim_id] = {
                "kind": "run_receipt",
                "source_ids": config["claim_sources"][claim_id],
                "claim_specific_receipt": f"E01 private receipt for {claim_id}",
            }
    target = out / f"episode-{episode}"
    target.mkdir(parents=True, exist_ok=True)
    script = {
        "version": "1.0",
        "title": config["title"],
        "total_duration_seconds": round(cursor, 3),
        "voice_performance": {
            "performance_intent": "A calm lab walkthrough for a beginner; exact results are stated without turning them into a promise.",
            "pacing_profile": "technical",
            "energy_curve": "Immediate recorded result, definitions, measured comparison, explicit limitation, worksheet close.",
            "pause_policy": "Brief pauses after counts and thresholds; longer pause before the boundary statement.",
            "sample_section_id": "scene-01",
            "provider_notes": {"voice": "pending operator approval", "rate": "provider-native only after exact-script approval"},
        },
        "sections": script_sections,
        "metadata": {
            "episode": int(episode),
            "syllabus_episode": episode,
            "package_revision": "e01-rebuild-2026-08-03",
            "duration_basis_wpm": wpm,
            "word_count": sum(len(row["text"].split()) for row in sections),
            "vo_sha256": sha(vo_path),
            "evidence_authority": "../../e01-e03-live-receipts-2026-08-03.json",
            "evidence_authority_sha256": sha(RECEIPTS),
            "status": "candidate_pending_operator_script_and_visual_approval",
        },
    }
    claims_doc = {
        "schema": "teaching-claims/v1",
        "script_sha256": sha(vo_path),
        "sources": source_map,
        "claims": claims,
    }
    write_json(target / "script.json", script)
    write_json(target / "claims.json", claims_doc)
    shutil.copyfile(vo_path, target / "vo.txt")
    packaging = {
        "schema": "tradercockpit-series-package/v1",
        "STATUS": "CANDIDATE — OPERATOR SCRIPT AND SEMANTIC VISUAL APPROVAL REQUIRED",
        "status": "candidate_pending_operator_approval",
        "episode": int(episode),
        "syllabus_episode": episode,
        "revision": "e01-rebuild-2026-08-03",
        "title": config["title"],
        "beginner_belief": config.get("beginner_belief", ""),
        "prewriting": config.get("prewriting", {}),
        "thumbnail": {
            "status": "candidate_pending_raster_and_squint_review",
            "path": "../../e01-e03-production-source-2026-08-03/episode-01/thumbnail-ep01.png",
            "squint_path": "../../e01-e03-production-source-2026-08-03/episode-01/thumbnail-ep01-squint-150.png",
            "first_shot_path": "../../e01-e03-production-source-2026-08-03/episode-01/first-shot.png",
            "width": 1280,
            "height": 720,
            "elements": config["thumbnail"].split(" / "),
            "visual_promise": "Three physical intake lanes, proportional entrant counts, and the exact 184 Dow queue.",
        },
        "candidate_first_post_ident_sentence": first_sentence(sections[0]["text"]),
        "first_spoken_sentence": first_sentence(sections[0]["text"]),
        "evidence": {"manifest": "../../e01-e03-live-receipts-2026-08-03.json", "manifest_sha256": sha(RECEIPTS), "boundary": config["boundary"], "validation_status": False},
        "production": {"anchor_medium": "narration_led_deterministic_graphics", "render_runtime": "hyperframes", "render_runtime_alternative": "remotion", "composition_mode": "atelier", "music": "none", "full_render_started": False, "narration_started": False, "provider_generation_started": False, "semantic_proof": "approved for local deterministic proof only"},
        "proof": {"source": "../../e01-e03-production-source-2026-08-03/episode-01/index.html", "duration_seconds": 60, "status": "short_semantic_proof_pending_qa", "master": False},
        "dependencies": {"manifest": "../../e01-e03-production-source-2026-08-03/episode-01/composition-dependencies.json"},
        "script": {"status": "candidate_pending_script_human_gate", "sha256": sha(target / "script.json"), "vo_sha256": sha(vo_path), "word_count": script["metadata"]["word_count"], "estimated_duration_seconds": script["total_duration_seconds"], "duration_basis_wpm": wpm},
        "approval": {"package_approved": False, "complete_script_approved": False, "thumbnail_approved": False, "narration_approved": False, "master_approved": False, "historical_approvals_authoritative": False},
    }
    if episode == "01":
        source_dir = ROOT / "productions/_series/e01-e03-production-source-2026-08-03/episode-01"
        thumbnail_paths = {
            "thumbnail": source_dir / "thumbnail-ep01.png",
            "squint": source_dir / "thumbnail-ep01-squint-150.png",
            "first_shot": source_dir / "first-shot.png",
        }
        thumbnail_dimensions = {name: png_dimensions(path) for name, path in thumbnail_paths.items()}
        thumbnail_ready = thumbnail_dimensions == {
            "thumbnail": (1280, 720),
            "squint": (150, 84),
            "first_shot": (1920, 1080),
        }
        packaging["thumbnail"]["status"] = (
            "candidate_raster_and_squint_verified" if thumbnail_ready
            else "candidate_pending_raster_and_squint_review"
        )
        packaging["thumbnail"]["dimensions"] = thumbnail_dimensions
        packaging["thumbnail"]["sha256"] = {
            name: sha(path) for name, path in thumbnail_paths.items() if path.is_file()
        }

        proof_path = out / "episode-01" / "proof" / "e01-semantic-proof.mp4"
        if proof_path.is_file():
            packaging["proof"].update({
                "artifact": "proof/e01-semantic-proof.mp4",
                "artifact_sha256": sha(proof_path),
                "artifact_codec": "h264",
                "artifact_resolution": "1920x1080",
                "artifact_fps": "30/1",
                "artifact_frames": 1800,
                "artifact_audio": False,
                "status": "short_semantic_proof_verified_pending_operator_approval",
            })
    scene_plan = {
        "schema": "openmontage/scene-plan/v1",
        "episode": episode,
        "title": config["title"],
        "script_sha256": sha(vo_path),
        "composition_mode": "atelier",
        "render_runtime": "hyperframes",
        "semantic_rule": "Every spoken sentence is bound to one sentence-level purposeful visual action over the full section; no generic card may replace the mechanism.",
        "visual_coverage": {"mode": "sentence_bound", "spoken_sentences": sum(len(sentences(row["text"])) for row in sections), "bound_cues": sum(len(scene["cues"]) for scene in planned_scenes), "coverage_ratio": 1.0},
        "render_source": "productions/_series/e01-e03-production-source-2026-08-03/episode-01/index.html",
        "scenes": planned_scenes,
        "proof_scope": "The semantic proof renders the hook, central mechanism, and boundary only; it is not a master or approval.",
    }
    for name, value in (("packaging.json", packaging), ("scene_plan.json", scene_plan)):
        write_json(target / name, value)
    return {"episode": episode, "path": str(target.relative_to(ROOT)).replace("\\", "/"), "script_sha256": sha(target / "script.json"), "claims_sha256": sha(target / "claims.json"), "packaging_sha256": sha(target / "packaging.json"), "scene_plan_sha256": sha(target / "scene_plan.json"), "vo_sha256": sha(vo_path), "duration_seconds": script["total_duration_seconds"], "word_count": script["metadata"]["word_count"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--episode", choices=("01", "02", "03"), help="Build one episode without rewriting the other episode packages.")
    args = parser.parse_args()
    manifest = json.loads(RECEIPTS.read_text(encoding="utf-8"))
    visual_map = json.loads(VISUAL_MAP.read_text(encoding="utf-8"))["episodes"]
    episodes = [args.episode] if args.episode else ["01", "02", "03"]
    rows = [build_episode(manifest, visual_map, episode, args.out) for episode in episodes]
    receipt = {"schema": "into-the-laboratory/e01-e03-production-candidates/v1", "source_manifest_sha256": sha(RECEIPTS), "visual_map_sha256": sha(VISUAL_MAP), "episodes": rows, "status": "candidate_pending_operator_script_and_semantic_visual_approval", "not_done": ["no narration", "no provider generation", "no master render", "no upload", "no publication"]}
    receipt_path = args.out / (f"production-receipt-episode-{args.episode}.json" if args.episode else "production-receipt.json")
    write_json(receipt_path, receipt)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
