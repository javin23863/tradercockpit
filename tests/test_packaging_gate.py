from tools import packaging_gate


RULES = {
    "max_title_chars": 65,
    "thumb_elements": (2, 4),
    "thumb_words": (3, 5),
    "belief_allowed": True,
}


def package():
    return {
        "status": "approved",
        "title": "I Optimised the Golden Cross. That Was the Mistake.",
        "candidate_first_post_ident_sentence": "I optimised the Golden Cross, and that was the mistake.",
        "thumbnail": {"copy": ["$78,420 \u2192 -$9,229", "SAME STRATEGY"]},
    }


def test_audit_accepts_current_contract_field_names():
    checks = packaging_gate.audit(package(), None, RULES, {"golden cross"})

    assert all(ok for _, ok, _ in checks)


def test_audit_blocks_script_before_current_package_approval(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "vo.txt").write_text("legacy narration", encoding="utf-8")
    candidate = {
        "status": "candidate_not_operator_approved",
        "title": "I Optimised the Golden Cross. That Was the Mistake.",
        "candidate_first_post_ident_sentence": "I optimised the Golden Cross, and that was the mistake.",
        "thumbnail": {"copy": ["$78,420 \u2192 -$9,229", "SAME STRATEGY"]},
    }

    checks = packaging_gate.audit(candidate, tmp_path, RULES, {"golden cross"})

    assert dict((name, ok) for name, ok, _ in checks)["(b)1 package BEFORE the script"] is False


def test_audit_rejects_conflicting_current_and_legacy_aliases():
    candidate = package()
    candidate["STATUS"] = "NOT_OPERATOR_APPROVED"
    candidate["first_spoken_sentence"] = "Stale opening."
    candidate["thumbnail"]["elements"] = ["STALE", "COPY HERE"]

    checks = packaging_gate.audit(candidate, None, RULES, {"golden cross"})

    assert dict((name, ok) for name, ok, _ in checks)["package field aliases do not conflict"] is False


def test_audit_requires_complete_episode_demand_screen(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "demand-screen.json").write_text(
        '{"schema":"tradercockpit-failure-mode-demand/v1","status":"partial",'
        '"queryCoverage":[{"phrasing":"one","status":"measured","resultsReturned":0},'
        '{"phrasing":"two","status":"failed"}],"errors":["failed"]}',
        encoding="utf-8",
    )

    checks = packaging_gate.audit(package(), tmp_path, RULES, {"golden cross"})

    assert dict((name, ok) for name, ok, _ in checks)["episode demand screen is complete"] is False


def test_audit_accepts_complete_episode_demand_screen(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "demand-screen.json").write_text(
        '{"schema":"tradercockpit-failure-mode-demand/v1","status":"ok",'
        '"queryCoverage":[{"phrasing":"one","status":"measured","resultsReturned":0},'
        '{"phrasing":"two","status":"measured","resultsReturned":3}],"errors":[]}',
        encoding="utf-8",
    )

    checks = packaging_gate.audit(package(), tmp_path, RULES, {"golden cross"})

    assert all(ok for _, ok, _ in checks)
