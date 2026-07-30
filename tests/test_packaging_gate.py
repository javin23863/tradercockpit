from tools import packaging_gate


RULES = {
    "max_title_chars": 65,
    "thumb_elements": (2, 4),
    "thumb_words": (3, 5),
    "belief_allowed": True,
    "public_method_result_allowed": True,
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


def test_audit_allows_searched_method_name_with_concrete_result():
    candidate = package()
    candidate["title"] = "Monte Carlo Backtest: We Moved the Exits. 28 of 46 Failed."
    candidate["candidate_first_post_ident_sentence"] = (
        "We moved the exits, and 28 of 46 strategies failed this Monte Carlo backtest."
    )
    candidate["beginner_belief"] = "The best optimizer setting is trustworthy."
    candidate["title_result"] = {
        "statement": "28 of 46 failed",
        "source": "artifacts/evidence/result.json",
        "sha256": "a" * 64,
    }

    checks = packaging_gate.audit(candidate, None, RULES, {"golden cross"})

    phase_check = next(ok for name, ok, _ in checks if name.startswith("(a)1"))
    assert phase_check is True


def test_audit_rejects_bare_public_method_topic():
    candidate = package()
    candidate["title"] = "Monte Carlo Backtest Explained"
    candidate["candidate_first_post_ident_sentence"] = "This Monte Carlo backtest is explained."
    candidate["beginner_belief"] = "The best optimizer setting is trustworthy."

    checks = packaging_gate.audit(candidate, None, RULES, {"golden cross"})

    phase_check = next(ok for name, ok, _ in checks if name.startswith("(a)1"))
    assert phase_check is False


def test_audit_rejects_internal_phase_codes_and_numbers():
    for title in (
        "phase06_mc_param: 28 of 46 Failed",
        "Phase 6: 28 of 46 Failed",
    ):
        candidate = package()
        candidate["title"] = title
        candidate["candidate_first_post_ident_sentence"] = title

        checks = packaging_gate.audit(candidate, None, RULES, {"golden cross"})

        phase_check = next(ok for name, ok, _ in checks if name.startswith("(a)1"))
        assert phase_check is False


def test_audit_rejects_numeric_public_method_non_results():
    for title in (
        "Monte Carlo Backtest 2026",
        "Monte Carlo Backtest Explained in 5 Minutes",
    ):
        candidate = package()
        candidate["title"] = title
        candidate["candidate_first_post_ident_sentence"] = title
        candidate["beginner_belief"] = "The best optimizer setting is trustworthy."

        checks = packaging_gate.audit(candidate, None, RULES, {"golden cross"})

        phase_check = next(ok for name, ok, _ in checks if name.startswith("(a)1"))
        assert phase_check is False


def test_audit_rejects_under_bound_public_method_result():
    candidate = package()
    candidate["title"] = "Monte Carlo Backtest: We Moved the Exits. 28 of 46 Failed."
    candidate["candidate_first_post_ident_sentence"] = (
        "We moved the exits, and 28 of 46 strategies failed this Monte Carlo backtest."
    )
    candidate["beginner_belief"] = "The best optimizer setting is trustworthy."
    candidate["title_result"] = {
        "statement": "28 failed",
        "source": "artifacts/evidence/result.json",
        "sha256": "a" * 64,
    }

    checks = packaging_gate.audit(candidate, None, RULES, {"golden cross"})

    result_check = next(ok for name, ok, _ in checks if "result is hash-bound" in name)
    assert result_check is False


def test_audit_verifies_public_method_title_result_source_hash(tmp_path):
    evidence = tmp_path / "artifacts" / "evidence"
    evidence.mkdir(parents=True)
    source = evidence / "result.json"
    source.write_text('{"result":{"entered":46,"failed":28}}', encoding="utf-8")
    candidate = package()
    candidate["title"] = "Monte Carlo Backtest: We Moved the Exits. 28 of 46 Failed."
    candidate["candidate_first_post_ident_sentence"] = (
        "We moved the exits, and 28 of 46 strategies failed this Monte Carlo backtest."
    )
    candidate["beginner_belief"] = "The best optimizer setting is trustworthy."
    candidate["title_result"] = {
        "statement": "28 of 46 failed",
        "source": "artifacts/evidence/result.json#/result",
        "sha256": packaging_gate.hashlib.sha256(source.read_bytes()).hexdigest(),
    }

    checks = packaging_gate.audit(candidate, tmp_path, RULES, {"golden cross"})

    result_check = next(ok for name, ok, _ in checks if "result is hash-bound" in name)
    assert result_check is True

    candidate["title_result"]["sha256"] = "0" * 64
    checks = packaging_gate.audit(candidate, tmp_path, RULES, {"golden cross"})
    result_check = next(ok for name, ok, _ in checks if "result is hash-bound" in name)
    assert result_check is False


def test_audit_rejects_pointerless_and_invalid_array_title_result_sources(tmp_path):
    evidence = tmp_path / "artifacts" / "evidence"
    evidence.mkdir(parents=True)
    source = evidence / "result.json"
    source.write_text('{"results":[{"entered":46,"failed":28}]}', encoding="utf-8")
    candidate = package()
    candidate["title"] = "Monte Carlo Backtest: We Moved the Exits. 28 of 46 Failed."
    candidate["candidate_first_post_ident_sentence"] = (
        "We moved the exits, and 28 of 46 strategies failed this Monte Carlo backtest."
    )
    candidate["beginner_belief"] = "The best optimizer setting is trustworthy."
    candidate["title_result"] = {
        "statement": "28 of 46 failed",
        "source": "artifacts/evidence/result.json",
        "sha256": packaging_gate.hashlib.sha256(source.read_bytes()).hexdigest(),
    }

    for locator in ("", "#/results/-1", "#/results/01"):
        candidate["title_result"]["source"] = f"artifacts/evidence/result.json{locator}"
        checks = packaging_gate.audit(candidate, tmp_path, RULES, {"golden cross"})
        result_check = next(ok for name, ok, _ in checks if "result is hash-bound" in name)
        assert result_check is False


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
