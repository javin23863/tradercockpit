from unittest.mock import patch

from tools import ai_tell_gate


def test_long_script_uses_length_matched_corpus_limits():
    thresholds = {
        "limits": {"copula": 5.0, "unseen": 46.2, "outOfRegister": 34},
        "sampleWords": 1450,
    }
    matched = {"copula": 5.1, "unseen": 48.0, "outOfRegister": 40}
    with patch.object(
        ai_tell_gate, "calibrated_limits", return_value=(matched, 70)
    ) as calibrate:
        limits, documents = ai_tell_gate.limits_for_words(1501, thresholds)
        assert limits == matched and documents == 70
        calibrate.assert_called_once_with(1501)
    assert ai_tell_gate.limits_for_words(1450, thresholds) == (thresholds["limits"], None)


def test_teach_domain_vocabulary_preserves_raw_novelty_without_blocking_subject_words():
    profile = {
        "unigrams": {"ordinary": 2, "language": 2},
        "bigrams": {"ordinary language": 2},
        "documents": 2,
        "words": 100,
    }
    limits = {"copula": 100.0, "unseen": 60.0, "outOfRegister": 2}
    previous = ai_tell_gate.REG
    ai_tell_gate.REG = "teach"
    try:
        report = ai_tell_gate.score(
            "ordinary language plainword rareword return-to-drawdown",
            profile,
            limits,
        )
    finally:
        ai_tell_gate.REG = previous

    assert report["verdict"] == "PASS", report
    assert report["metrics"]["rawUnseenBigramPct"] == 75.0
    assert report["metrics"]["unseenBigramPct"] == 50.0
    assert report["metrics"]["domainExemptBigramCount"] == 1
    assert "return-to-drawdown" in report["rawOutOfRegister"]
    assert "return-to-drawdown" not in report["outOfRegister"]
    assert report["domainVocabulary"]["register"] == "teach"
