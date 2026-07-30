from pathlib import Path

import pytest

from tools import human_facing_gate


@pytest.mark.parametrize(
    ("surface_kind", "context_mode"),
    [
        ("teaching_narration", "personal"),
        ("youtube_title", "marketing"),
        ("youtube_description", "marketing"),
        ("public_doc", "technical"),
    ],
)
def test_supported_surfaces_delegate_without_rewriting(
    monkeypatch, surface_kind, context_mode
):
    seen = {}

    def fake_audit(text, mode):
        seen.update(text=text, mode=mode)
        return {"verdict": "PASS", "blocked": [], "warns": [], "metrics": {}}

    monkeypatch.setattr(human_facing_gate.ai_writing_gate, "audit_text", fake_audit)
    original = "Keep every claim and disclosure exactly as written."
    report = human_facing_gate.audit_text(original, surface_kind)

    assert seen == {"text": original, "mode": context_mode}
    assert report["verdict"] == "PASS"
    assert report["surface_kind"] == surface_kind
    assert report["scope"] == {
        "rewrites_text": False,
        "checks_claim_accuracy": False,
        "checks_required_disclosures": False,
    }


def test_unsupported_surface_blocks_without_running_detector(monkeypatch):
    monkeypatch.setattr(
        human_facing_gate.ai_writing_gate,
        "audit_text",
        lambda *_: pytest.fail("unsupported surface reached detector"),
    )

    report = human_facing_gate.audit_text("Copy", "internal_receipt")

    assert report["verdict"] == "BLOCK"
    assert report["blocked"][0]["type"] == "unsupported surface kind"


def test_existing_detector_block_is_preserved(monkeypatch):
    blocked = {
        "verdict": "BLOCK",
        "blocked": [{"type": "chatbot", "count": 1, "detail": "chatbot register"}],
        "warns": [],
        "metrics": {"words": 12},
    }
    monkeypatch.setattr(
        human_facing_gate.ai_writing_gate, "audit_text", lambda *_: blocked
    )

    report = human_facing_gate.audit_text(
        "Certainly! I hope this helps with your trading.", "youtube_description"
    )

    assert report["verdict"] == "BLOCK"
    assert report["blocked"] == blocked["blocked"]


def test_cli_audits_top_level_json_string_without_duplication(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda *_args, **_kwargs: '{"title": "I Moved the Exit Settings"}',
    )

    def fake_audit(text, surface_kind):
        seen.update(text=text, surface_kind=surface_kind)
        return {"verdict": "PASS", "blocked": []}

    monkeypatch.setattr(human_facing_gate, "audit_text", fake_audit)

    assert human_facing_gate.main(
        ["youtube_title", "packaging.json", "--json-key", "title"]
    ) == 0
    assert seen == {
        "text": "I Moved the Exit Settings",
        "surface_kind": "youtube_title",
    }


@pytest.mark.parametrize(
    "document",
    ['{"description": "No title"}', '{"title": 46}', '["not", "an", "object"]'],
)
def test_cli_blocks_missing_or_non_string_json_key(monkeypatch, capsys, document):
    monkeypatch.setattr(Path, "read_text", lambda *_args, **_kwargs: document)

    assert human_facing_gate.main(
        ["youtube_title", "packaging.json", "--json-key", "title", "--json"]
    ) == 1
    assert '"type": "gate input"' in capsys.readouterr().out


def test_cli_blocks_unreadable_input(capsys):
    missing = Path("__human_facing_gate_missing_test_input__.txt")

    assert human_facing_gate.main(["public_doc", str(missing), "--json"]) == 1
    assert '"type": "gate input"' in capsys.readouterr().out
