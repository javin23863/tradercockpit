"""Deterministic acceptance checks for the E02 operator-review candidate.

The test reads only regenerated E02 artifacts.  It does not touch Futures sources, rerun a
backtest, or make an approval decision.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / "productions" / "_series" / "e02-rebuild-candidate-2026-08-03" / "episode-02"
ART = EP / "artifacts"
SOURCE = ROOT / "productions" / "_series" / "e02-rebuild-source-2026-08-03" / "episode-02"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_pinned_facts_and_assignment_discrepancy() -> None:
    facts = load(ART / "facts_receipt.json")
    spy = facts["spy"]
    dow = facts["dow"]

    assert facts["verification"] == {
        "external_files_read": True,
        "all_pinned_hashes_match": True,
        "external_files_modified": False,
        "rerun_backtest": False,
    }
    assert spy["entering"] == 5
    assert spy["surviving"] == 0
    assert spy["dropped"] == 5
    assert spy["later_entering"] == 0
    assert spy["later_surviving"] == 0
    assert spy["later_window"] is None
    assert spy["holdout_status"] == "not reached"
    assert spy["candidate"] == {
        "pf": 0.806004,
        "pf_threshold": 1.3,
        "ret_dd": -0.420205,
        "ret_dd_threshold": 4,
        "trades_per_month": 0.392308,
        "trades_per_month_threshold": 2,
    }
    assert dow["oos_entering"] == 184
    assert dow["oos_surviving"] == 154
    assert dow["oos_dropped"] == 30
    assert dow["intake_entering"] == 1335
    assert dow["intake_surviving"] == 184
    assert dow["candidate_entering_oos"] == 184
    assert dow["candidate"] == {
        "is_net": 16727.8,
        "is_pf": 1.28037,
        "oos_net": -4897.4,
        "oos_pf": 0.813381,
        "oos_ret_dd": -0.563866,
        "oos_wins": 29,
        "oos_losses": 72,
    }
    assert facts["assignment_discrepancies"] == [{
        "field": "dow.candidate.oos_pf",
        "assignment_requested": 0.81324,
        "hash_bound_source": 0.813381,
        "decision": "use_hash_bound_source",
        "reason": "The pinned phase02_oos JSON reports metrics.pf=0.813381; 0.81324 is not present in the pinned row.",
    }]
    for source_id, expected in {
        "RUN_SPY_PHASE01": "59e2257a5bb6b13c6cce2a4f5b22702b396d06e79651b3fb09be341e1eb7bcc1",
        "RUN_SPY_PHASE02": "640532043b74c60c7ec30a5e14973c3ae6860f6b0a6540e2025b41bf93f2069e",
        "RUN_DOW_PHASE01": "19899535054e5b9dd7b6be6275b3017110b79de2f1079ea7ac5850afb48f235d",
        "RUN_DOW_PHASE02": "21d1c7c563acaecb869ab3d49e05a3fed2516c33a3d611e7d330c219f8605dd0",
        "RUN_SPY_LEDGER": "fba810bfac8e1703521e37344ea1535e785fc3afe93f15a9a4da08d68b26c545",
        "RUN_SPY_MANIFEST": "fa3d87216305d471153632d447146455f8744ebe3823761ff121f63e11b3cdfb",
    }.items():
        assert facts["sources"][source_id]["sha256"] == expected
    assert facts["sources"]["RUN_SPY_LEDGER"]["pointers"]["exit_rule_assumption"].endswith("/lineage/explanation/assumptions/0")
    assert facts["sources"]["RUN_SPY_MANIFEST"]["pointers"]["candidate"] == "/candidates_provenance/0"
    assert facts["sources"]["RUN_SPY_MANIFEST"]["pointers"]["candidate_id"] == "/candidates_provenance/0/id"


def test_sentence_visual_coverage_and_claim_bindings() -> None:
    visual = load(ART / "scene_visual_map.json")
    claims = load(ART / "claims.json")
    script = load(ART / "script.json")
    semantic = load(ART / "visual_semantic_receipt.json")

    assert visual["sentence_bound_visual_required"] is True
    assert visual["coverage"]["spoken_sentences"] == visual["coverage"]["visual_cues"]
    assert visual["coverage"]["uncovered_sentences"] == []
    assert len(visual["sections"]) == 14
    assert len(claims["claims"]) == 14
    assert script["total_words"] == visual["total_words"]
    assert semantic["verified"] is True
    assert len(semantic["scenes"]) == 14
    assert all(scene["missing_markers"] == [] for scene in semantic["scenes"].values())
    assert script["total_duration_seconds"] == visual["total_duration_seconds"]

    for section in visual["sections"]:
        assert section["claim_refs"]
        assert section["sentence_cues"]
        for cue in section["sentence_cues"]:
            assert cue["sentence_bound"] is True
            assert cue["asset"].startswith("hyperframes/assets/scene-")
            assert cue["spoken_span"].strip()
            assert cue["visual_action"].strip()
            assert cue["end_seconds"] > cue["start_seconds"]

    by_id = {section["section_id"]: section["sentence_cues"] for section in visual["sections"]}
    inequality_actions = [cue["visual_action"] for cue in by_id["scene-05"]]
    assert "0.806004" in inequality_actions[1]
    assert "-0.420205" in inequality_actions[3]
    assert "0.392308" in inequality_actions[5]
    assert all("false" in inequality_actions[index] for index in (7, 8, 9))
    scene04_actions = [cue["visual_action"] for cue in by_id["scene-04"]]
    assert "200-day" in scene04_actions[2] and "2-day RSI" in scene04_actions[2]
    assert "short moving-average exit" in scene04_actions[3]
    assert "D1" in scene04_actions[4]
    assert "200-day lineage" in scene04_actions[5]
    assert "warmup" in scene04_actions[6]
    assert "setup" in scene04_actions[7] and "not a trade result" in scene04_actions[7]
    assert "gate path" in scene04_actions[8]
    assert "run identity" in scene04_actions[9]
    scene09_actions = [cue["visual_action"] for cue in by_id["scene-09"]]
    assert "0.813381" in scene09_actions[2]
    assert "29 wins" in scene09_actions[3]
    assert "0.81324" in scene09_actions[4]
    assert "0.813381" in scene09_actions[5]
    assert "SPY lane" in scene09_actions[7]
    assert any("remaining 183" in action for action in scene09_actions)

    # A one-cue-per-sentence count is not enough: these anchors keep the action list aligned
    # with the current spoken order after a source rewrite.
    assert "1996-07-12" in by_id["scene-01"][1]["spoken_span"]
    assert "1996-07-12" in by_id["scene-01"][1]["visual_action"]
    assert "Dow futures" in by_id["scene-01"][7]["spoken_span"]
    assert "Dow lane" in by_id["scene-01"][7]["visual_action"]
    assert "zero in and zero out" in by_id["scene-07"][1]["spoken_span"]
    assert "both the entering and surviving" in by_id["scene-07"][1]["visual_action"]
    assert "154 continue" in by_id["scene-08"][2]["spoken_span"]
    assert "154 tokens" in by_id["scene-08"][2]["visual_action"]
    assert "White's data-snooping" in by_id["scene-10"][5]["spoken_span"]
    assert "White's data-snooping" in by_id["scene-10"][5]["visual_action"]
    assert "+$16,727.80" in by_id["scene-14"][3]["spoken_span"]
    assert "+$16,727.80" in by_id["scene-14"][3]["visual_action"]


def test_candidate_hashes_and_boundaries() -> None:
    receipt = load(ART / "candidate_receipt.json")
    packaging = load(ART / "packaging.json")
    claims = load(ART / "claims.json")
    source_vo = SOURCE / "vo.txt"
    generated_vo = ART / "vo.txt"
    root_vo = EP / "vo.txt"

    assert sha256(source_vo) == receipt["source_vo_sha256"]
    assert sha256(generated_vo) == receipt["generated_vo_sha256"]
    assert sha256(generated_vo) == sha256(root_vo)
    assert claims["script_sha256"] == sha256(generated_vo)
    assert packaging["script"]["vo_sha256"] == sha256(generated_vo)
    script = load(ART / "script.json")
    source_ref = (ART / script["source_vo"]).resolve()
    assert source_ref.is_file()
    assert source_ref == (SOURCE / "vo.txt").resolve()
    for claim in claims["claims"].values():
        academic_ref = (ART / claim["private_receipt"]["academic_receipts"]).resolve()
        assert academic_ref.is_file()
        assert academic_ref == (SOURCE / "academic_receipts.json").resolve()
    assert receipt["candidate_only"] is True
    assert packaging["approval"]["complete_script_approved"] is False
    assert packaging["approval"]["operator_exact_hash_approval"] is False

    body = "\n".join(line for line in generated_vo.read_text(encoding="utf-8").splitlines()
                      if not line.lstrip().startswith("#") and not line.startswith("==="))
    assert not re.search(r"154\s*(?:→|->|to)\s*53", body, re.IGNORECASE)
    assert "fill timing or trading hours" in body.lower()
    assert body.rstrip().endswith("fill timing or trading hours?")
    assert "unitless ratio" in body
    assert "wiring proof is true" in body
    assert "current receipts do not establish" in body


def test_thumbnail_and_hyperframes_contract() -> None:
    packaging = load(ART / "packaging.json")
    html = (EP / "hyperframes" / "index.html").read_text(encoding="utf-8")
    thumb = (ART / "thumbnail-ep02.html").read_text(encoding="utf-8")

    assert packaging["thumbnail"]["dimensions"] == "1280x720"
    assert packaging["thumbnail"]["matching_first_shot"] == "hyperframes/assets/scene-01.svg"
    assert "5 → 0" in thumb
    assert "SEALED" in thumb
    assert "184 → 154" in thumb
    scene05 = (EP / "hyperframes" / "assets" / "scene-05.svg").read_text(encoding="utf-8")
    assert scene05.count("unitless ratio") == 2
    assert "rate · trades / month" in scene05
    assert 'data-composition-id="e02-semantic-proof-candidate"' in html
    assert 'data-width="1920"' in html
    assert 'data-height="1080"' in html
    assert 'data-start="0"' in html
    assert 'data-duration="20"' in html
    assert '.clip{position:absolute;inset:0;width:1920px;height:1080px;opacity:1}' in html
    assert "window.__timelines['e02-semantic-proof-candidate']" in html
    assert html.count('class="clip"') == 4
