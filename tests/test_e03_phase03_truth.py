"""The E03 source guard must reject the historical 41/66 label swap."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.build_e03_timing_session_rebuild import (
    EXPECTED,
    EXPECTED_PHASE_SHA256,
    PHASE_SOURCE,
    assert_phase03_truth,
    derive_phase03_facts,
    sha256,
)
from tools.syllabus_gate import FORBIDDEN_LATER_RESULT


PACKAGE = Path(__file__).resolve().parents[1] / (
    "productions/_series/e01-e03-production-candidates-2026-08-03/episode-03"
)


def test_phase03_source_hash_and_counts_are_pinned() -> None:
    assert sha256(PHASE_SOURCE) == EXPECTED_PHASE_SHA256
    facts = derive_phase03_facts(json.loads(PHASE_SOURCE.read_text(encoding="utf-8")))
    assert_phase03_truth(facts)
    assert facts["failure_counts"] == EXPECTED["failures"]
    assert facts["unique_failures"] == 101
    assert facts["surviving"] == 53


def test_swapping_one_bar_and_session_half_one_is_rejected() -> None:
    facts = derive_phase03_facts(json.loads(PHASE_SOURCE.read_text(encoding="utf-8")))
    swapped = {**facts, "failure_counts": dict(facts["failure_counts"])}
    swapped["failure_counts"]["pf_entry_delay_1bar"] = 66
    swapped["failure_counts"]["pf_session_half_1"] = 41
    with pytest.raises(AssertionError, match="gate mapping drifted"):
        assert_phase03_truth(swapped)


def test_later_phase_payoff_notation_is_rejected() -> None:
    assert FORBIDDEN_LATER_RESULT.search("The later payoff was 7/2.")
    assert not FORBIDDEN_LATER_RESULT.search("This episode ends at 154 - 101 = 53.")


def test_impeccable_receipt_is_literal_empty_findings() -> None:
    receipt = json.loads((PACKAGE / "impeccable-receipt.json").read_text(encoding="utf-8"))
    assert receipt["status"] == "PASS"
    assert receipt["findings"] == []
