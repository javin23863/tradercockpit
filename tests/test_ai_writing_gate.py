import json

import pytest

from tools import ai_writing_gate
from tools.ai_writing_gate import audit_text
from tools.social_batch import validate


DISCLAIMER = "Research tooling, not financial advice. No performance is promised or implied."
CLEAN_COPY = (
    "Brent settled at 83 after the inventory report. My read stays constructive while "
    "refiners keep bidding prompt barrels. I change my view below 81, with Monday's "
    f"OPEC meeting the next catalyst. {DISCLAIMER}"
)


def _types(result):
    return {finding["type"] for finding in result["blocked"]}


def test_shipped_style_market_copy_passes():
    result = audit_text(CLEAN_COPY)
    assert result["verdict"] == "PASS", result


def test_chatbot_tells_block():
    result = audit_text(
        "Certainly! Let me think step by step. Experts say we must delve into the "
        "intricate tapestry of price action. I hope this helps! "
        "As of my last update, only time will tell."
    )
    assert result["verdict"] == "BLOCK"
    assert {"chatbot", "cutoff-disclaimer", "vague-attribution", "tier1"} <= _types(result)


def test_lone_house_banned_word_blocks_where_the_detector_alone_would_not():
    """The reconciliation guard: no-ai-slop bans these outright, the detector needs a cluster."""
    copy = ("Our research tools empower you to read the tape. The S&P closed at 6,340, "
            f"down 0.8%. I care about 6,300 into Thursday's CPI print. {DISCLAIMER}")
    assert not any(issue["type"] in ("tier1", "tier2")
                   for issue in ai_writing_gate.analyze(copy)["issues"])
    assert "house-banned" in _types(audit_text(copy))


def test_elevated_is_market_vocabulary_not_the_banned_verb():
    """'volatility is elevated' ships; 'elevate the experience' does not."""
    assert "house-banned" not in _types(audit_text(
        f"Gold is lower and volatility is elevated but still contained at 14.2. {DISCLAIMER}"))
    assert "house-banned" in _types(audit_text(
        f"These tools elevate the trading experience for every subscriber. {DISCLAIMER}"))


def test_gate_blocks_when_it_cannot_inspect(monkeypatch):
    """Fail-closed: an unrunnable detector is a BLOCK, never a silent pass."""
    monkeypatch.setattr(ai_writing_gate, "analyze", lambda *a, **k: None)
    result = audit_text(CLEAN_COPY)
    assert result["verdict"] == "BLOCK"
    assert _types(result) == {"gate input"}


def test_empty_copy_blocks():
    assert audit_text("   ")["verdict"] == "BLOCK"


SLOP_THAT_PASSES_DOCTRINE = (
    "Our research tools empower you to read the tape. The S&P closed at 6,340, down 0.8%. "
    f"I care about 6,300 into Thursday's CPI print. {DISCLAIMER}"
)


def test_social_batch_rejects_ai_slop_copy():
    """The wiring, and the reason for a second gate.

    This copy is clean by TraderCockpit doctrine -- it leads with evidence, owns a judgment,
    names no vague authority, predicts nothing -- so script_style_gate passes it. It still
    contains a word no-ai-slop bans outright. Before this gate existed, it shipped.
    """
    from tools import script_style_gate
    assert script_style_gate.audit_text(SLOP_THAT_PASSES_DOCTRINE)["verdict"] == "PASS"

    batch = {
        "schema": "social-batch/v2",
        "batchId": "2026-07-28-test",
        "items": [{
            "id": "slop", "channel": "youtube", "status": "draft",
            "copy": SLOP_THAT_PASSES_DOCTRINE,
        }],
    }
    with pytest.raises(ValueError, match="ai writing gate BLOCK"):
        validate(json.loads(json.dumps(batch)))
