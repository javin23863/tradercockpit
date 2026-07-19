from tools.script_style_gate import audit_sections


def test_plain_owned_voice_passes():
    result = audit_sections([
        "Brent gave back half the morning spike. My read is simple: energy traders still care, but the rest of the tape does not. Watch eighty-three; below it, the premium is leaking."
    ])
    assert result["status"] == "PASS"


def test_process_jargon_and_slogan_repetition_warn():
    result = audit_sections([
        "This chart is verified in TradingView. The source owns the event record. Do not trade the siren. Trade the pressure chain. The pressure chain matters because sirens are loud. The pressure chain is the setup, not the siren."
    ])
    rules = {warning["rule"] for warning in result["warnings"]}
    assert result["status"] == "WARN"
    assert "verification jargon" in rules
    assert "source-ownership metaphor" in rules
    assert "slogan repetition" in rules


def test_one_earned_contrast_is_allowed():
    result = audit_sections(["This is not broad panic. It is a narrow oil trade, and I want Brent above eighty-eight before I change that view."])
    assert not any(warning["rule"] == "corrective contrast" for warning in result["warnings"])
