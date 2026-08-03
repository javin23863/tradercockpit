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
SLOT = re.compile(r"^=== SLOT (scene-\d+) ")
SENTENCE = re.compile(r".+?[.!?](?:\s|$)")

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
            "E01_DOW_P2": ("02", "dow_oos_branch", None),
        },
        "claim_sources": {
            "E01-RW-C01": ["E01_DOW_P1", "E01_ES_P1", "E01_EURUSD_P1"],
            "E01-RW-C02": ["E01_DOW_P1", "E01_ES_P1", "E01_EURUSD_P1"],
            "E01-RW-C03": ["E01_DOW_P1"],
            "E01-RW-C04": ["E01_DOW_P1", "E01_ES_P1", "E01_EURUSD_P1"],
            "E01-RW-C05": ["E01_DOW_P1"],
            "E01-RW-C06": ["E01_DOW_P1"],
            "E01-RW-C07": ["E01_ES_P1", "E01_EURUSD_P1"],
            "E01-RW-C08": ["E01_DOW_P1"],
            "E01-RW-C09": ["E01_DOW_P1", "E01_DOW_P2"],
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
    "e01-pipeline-map.svg": "Show the complete rule set moving through replay, a declared gate, and a next test.",
    "e01-run-lanes.svg": "Keep Dow, S&P 500 futures, and EURUSD counts in separate lanes while showing the aggregate.",
    "e01-dow-gate-census.svg": "Show overlapping Dow failure modes without summing them into a false total.",
    "e01-candidate-ledger.svg": "Hold one recorded candidate beside its next-phase result.",
    "e02-spy-boundary.svg": "Show the SPY branch ending at zero before the holdout opens.",
    "e02-spy-candidate-row.svg": "Put one recorded SPY row beside its three actual thresholds.",
    "e02-dow-oos-bridge.svg": "Keep the SPY stop and Dow continuation as separate branches.",
    "e03-three-view-funnel.svg": "Show the same 154 candidates facing three declared transformations.",
    "e03-veto-vs-pass.svg": "Compare one recorded veto row and one recorded pass row in reserved lanes.",
    "e03-profit-factor.svg": "Define profit factor as a comparison of gross winning and losing dollars.",
    "e03-cost-handoff.svg": "Show 53 as the next phase input, not as a final trading conclusion.",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
            owner_ep = manifest["episodes"]["02"] if source_id == "E01_DOW_P2" else ep
            item = owner_ep[key] if selector is None else owner_ep[key][selector]
            path, digest = item["source_path"], item["sha256"]
            label = item.get("label", "Dow phase02 out-of-sample")
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
            "locator": path,
            "supports": f"Exact recorded counts, identifiers, metrics, and scope for {label} used by this episode.",
            "limitations": limitation,
            "sha256": digest,
        }
    return rows


def first_sentence(text: str) -> str:
    match = SENTENCE.match(text)
    return match.group(0).strip() if match else text.split(" ", 1)[0]


def build_episode(manifest: dict, visual_map: dict, episode: str, out: Path) -> dict:
    config = EPISODES[episode]
    vo_path = VO_ROOT / config["vo"]
    sections = parse_vo(vo_path)
    source_map = source_rows(manifest, episode)
    wpm = 160.0
    cursor = 0.0
    script_sections = []
    planned_scenes = []
    for row in sections:
        words = len(row["text"].split())
        duration = max(3.0, round(words / wpm * 60.0 + 0.5, 3))
        start = round(cursor, 3)
        end = round(start + duration, 3)
        cursor = end
        claim_refs = row["claims"]
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
            "enhancement_cues": [{
                "type": "animation",
                "description": "Purpose-built factual composition: " + PURPOSES[visual_map[episode][row["id"]]],
                "timestamp_seconds": start,
            }],
            "source_ref": ",".join(claim_refs),
        })
        asset = visual_map[episode][row["id"]]
        planned_scenes.append({
            "id": row["id"],
            "section_id": row["id"],
            "start_seconds": start,
            "end_seconds": end,
            "asset": asset,
            "composition_mode": "atelier",
            "semantic_purpose": PURPOSES[asset],
            "spoken_text": row["text"],
            "claim_refs": claim_refs,
            "evidence_class": "run_data" if "pipeline" not in asset and "profit-factor" not in asset else "method_or_run_data",
            "cues": [{
                "id": f"{row['id']}-cue-01",
                "start_seconds": start,
                "duration_seconds": min(8.0, duration),
                "asset": asset,
                "spoken_span": first_sentence(row["text"]),
                "visual_action": PURPOSES[asset],
            }],
        })
    claims = {}
    for row in sections:
        for claim_id in row["claims"]:
            claims[claim_id] = {"kind": "run_receipt", "source_ids": config["claim_sources"][claim_id]}
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
            "package_revision": "e01-e03-production-start-2026-08-03",
            "duration_basis_wpm": wpm,
            "word_count": sum(len(row["text"].split()) for row in sections),
            "vo_sha256": sha(vo_path),
            "evidence_authority": "../../e01-e03-live-receipts-2026-08-03.json",
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
        "revision": "e01-e03-production-start-2026-08-03",
        "title": config["title"],
        "beginner_belief": config.get("beginner_belief", ""),
        "prewriting": config.get("prewriting", {}),
        "thumbnail": {"status": "candidate", "elements": config["thumbnail"].split(" / "), "visual_promise": "Evidence-bound mechanism, not a generic card."},
        "candidate_first_post_ident_sentence": first_sentence(sections[0]["text"]),
        "first_spoken_sentence": first_sentence(sections[0]["text"]),
        "evidence": {"manifest": "../../e01-e03-live-receipts-2026-08-03.json", "boundary": config["boundary"], "validation_status": False},
        "production": {"anchor_medium": "narration_led_deterministic_graphics", "render_runtime": "hyperframes", "render_runtime_alternative": "remotion", "composition_mode": "atelier", "music": "none", "full_render_started": False},
        "script": {"status": "candidate_pending_script_human_gate", "sha256": sha(target / "script.json"), "vo_sha256": sha(vo_path), "word_count": script["metadata"]["word_count"], "estimated_duration_seconds": script["total_duration_seconds"], "duration_basis_wpm": wpm},
        "approval": {"package_approved": False, "complete_script_approved": False, "thumbnail_approved": False, "narration_approved": False, "master_approved": False, "historical_approvals_authoritative": False},
    }
    scene_plan = {
        "schema": "openmontage/scene-plan/v1",
        "episode": episode,
        "title": config["title"],
        "script_sha256": sha(vo_path),
        "composition_mode": "atelier",
        "render_runtime": "hyperframes",
        "semantic_rule": "Every section is bound to a purpose-built deterministic composition and a receipt claim; no generic card may replace the mechanism.",
        "scenes": planned_scenes,
        "proof_scope": "The semantic proof renders the hook, central mechanism, and boundary only; it is not a master or approval.",
    }
    for name, value in (("packaging.json", packaging), ("scene_plan.json", scene_plan)):
        write_json(target / name, value)
    return {"episode": episode, "path": str(target.relative_to(ROOT)).replace("\\", "/"), "script_sha256": sha(target / "script.json"), "claims_sha256": sha(target / "claims.json"), "packaging_sha256": sha(target / "packaging.json"), "scene_plan_sha256": sha(target / "scene_plan.json"), "vo_sha256": sha(vo_path), "duration_seconds": script["total_duration_seconds"], "word_count": script["metadata"]["word_count"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    manifest = json.loads(RECEIPTS.read_text(encoding="utf-8"))
    visual_map = json.loads(VISUAL_MAP.read_text(encoding="utf-8"))["episodes"]
    rows = [build_episode(manifest, visual_map, episode, args.out) for episode in ("01", "02", "03")]
    receipt = {"schema": "into-the-laboratory/e01-e03-production-candidates/v1", "source_manifest_sha256": sha(RECEIPTS), "visual_map_sha256": sha(VISUAL_MAP), "episodes": rows, "status": "candidate_pending_operator_script_and_semantic_visual_approval", "not_done": ["no narration", "no provider generation", "no master render", "no upload", "no publication"]}
    write_json(args.out / "production-receipt.json", receipt)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
