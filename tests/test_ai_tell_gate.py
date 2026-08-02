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
