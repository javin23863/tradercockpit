from tools import packaging_gate


def test_audit_accepts_current_contract_field_names():
    package = {
        "status": "approved",
        "title": "I Optimised the Golden Cross. That Was the Mistake.",
        "candidate_first_post_ident_sentence": "I optimised the Golden Cross, and that was the mistake.",
        "thumbnail": {"copy": ["$78,420 \u2192 -$9,229", "SAME STRATEGY"]},
    }
    rules = {
        "max_title_chars": 65,
        "thumb_elements": (2, 4),
        "thumb_words": (3, 5),
        "belief_allowed": True,
    }

    checks = packaging_gate.audit(package, None, rules, {"golden cross"})

    assert all(ok for _, ok, _ in checks)


def test_audit_blocks_script_before_current_package_approval(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()
    (artifacts / "vo.txt").write_text("legacy narration", encoding="utf-8")
    package = {
        "status": "candidate_awaiting_operator_package_approval",
        "title": "I Optimised the Golden Cross. That Was the Mistake.",
        "candidate_first_post_ident_sentence": "I optimised the Golden Cross, and that was the mistake.",
        "thumbnail": {"copy": ["$78,420 \u2192 -$9,229", "SAME STRATEGY"]},
    }
    rules = {
        "max_title_chars": 65,
        "thumb_elements": (2, 4),
        "thumb_words": (3, 5),
        "belief_allowed": True,
    }

    checks = packaging_gate.audit(package, tmp_path, rules, {"golden cross"})

    assert dict((name, ok) for name, ok, _ in checks)["(b)1 package BEFORE the script"] is False
