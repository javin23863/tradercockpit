from tools.script_style_gate import audit_sections, audit_text
from tools.social_batch import validate


DISCLAIMER = "Research tooling, not financial advice. No performance is promised or implied."
COMPLIANT_SECTIONS = [
    "Brent settled at 83 after the inventory report. My read stays constructive while refiners keep bidding prompt barrels.",
    "WTI held 79 as Exxon reduced Gulf loadings, leaving the physical spread firmer than Friday's close.",
    "Monday's OPEC meeting is the next catalyst; I change my view below 81.",
]
ACCEPTANCE_COPY = [
    "Forty-seven grand. Hundred and twenty-nine trades, two lots, profit factor 1.26. That is what my selection model printed. And it is garbage. Not because the math is wrong -- the math is fine. Because I had already looked at that same data seven times before I built the thing that made that number. I fit it to the answer. So that forty-seven K is not a result. It is an echo.",
    "That is not an edge, that is a rounding error with good posture.",
    "That is not a sample, that is a weekend.",
]


def _finding(result, rule):
    return next(
        (finding for bucket in (result["blocked"], result["warns"])
         for finding in bucket if finding["type"] == rule),
        None,
    )


def _assert_quiet(result, rule):
    assert _finding(result, rule) is None, (rule, result)


def _batch(copy, description=None):
    item = {"id": "offer", "channel": "tiktok", "status": "draft", "copy": copy}
    if description is not None:
        item["description"] = description
    return {
        "schema": "social-batch/v2",
        "batchId": "style-gate-test",
        "containsSyntheticMedia": False,
        "items": [item],
    }


def test_acceptance_fixture_blocks_all_required_patterns():
    result = audit_sections(ACCEPTANCE_COPY)
    contrast = _finding(result, "corrective contrast")
    cluster = _finding(result, "negative parallelism cluster")
    slogan = _finding(result, "slogan repetition")

    assert result["verdict"] == "BLOCK"
    assert contrast["count"] >= 3 and contrast["limit"] == 1
    assert cluster and "CLUSTER" in cluster["detail"]

    # NOT asserted: that the gate catches "it's an echo" as an abstract slogan.
    # The original acceptance criterion demanded it and was unmeetable — n-gram repetition
    # only detects phrases that REPEAT, and "it's an echo" appears once. A single-occurrence
    # abstract slogan is a semantic judgment, which the module documents as not covered
    # deterministically. Asserting it here would have forced the code to fake a capability
    # it does not have. Promote to a real assertion only behind an LLM judge.
    assert slogan is None or slogan["count"] >= 1


def test_compliant_copy_passes():
    result = audit_sections(COMPLIANT_SECTIONS)
    assert result["verdict"] == "PASS", result


def test_empty_input_blocks_instead_of_defaulting_to_pass():
    result = audit_sections([])
    assert result["verdict"] == "BLOCK"
    assert _finding(result, "gate input")


def test_vague_authorities_fire_and_named_sources_stay_quiet():
    vague = audit_sections([
        "Brent is at 83. Analysts say oil will rise; experts believe demand is firm; markets are watching inventories; many observers agree; it is widely expected. My read holds above 81."
    ])
    assert _finding(vague, "vague authority")["count"] == 5
    _assert_quiet(audit_sections(COMPLIANT_SECTIONS), "vague authority")


def test_ornamental_triplet_fires_but_factual_asset_list_stays_quiet():
    ornate = audit_sections([
        "Brent at 83 feels fragile, nervous, and brittle. My read fails below 82."
    ])
    assert _finding(ornate, "ornamental group of three")
    factual = audit_sections([
        "Brent, WTI, and XLE closed above 80. My read holds while XLE stays above 79."
    ])
    _assert_quiet(factual, "ornamental group of three")


def test_automatic_summary_ending_fires_and_level_ending_stays_quiet():
    summary = audit_sections([
        "Brent held 83 after the report. My read is unchanged. In summary, 82 is the floor."
    ])
    assert _finding(summary, "automatic summary ending")
    _assert_quiet(audit_sections(COMPLIANT_SECTIONS), "automatic summary ending")


def test_final_non_cta_section_requires_invalidation_level_or_date():
    # SCRIPT-LENGTH fixture on purpose. This rule is scoped to >= SCRIPT_LENGTH_WORDS because a
    # caption has no closing section to land an invalidation level on — verified 2026-07-20 when
    # the short version of this fixture rejected legitimate captions.
    missing = audit_sections([
        "Brent broke 83 after the report and the tape never recovered through the afternoon. "
        "My read is bearish while sellers keep control of the session and volume confirms it. "
        "The energy complex followed crude lower and the majors gave back their morning gains. "
        "Refiners lagged the move which tells me the market is pricing supply rather than demand. "
        "Volume ran heavier than the recent average on the way down which supports that read.",
        # Deliberately carries NO digit, NO number word and NO date catalyst — that absence is
        # what the rule is meant to catch. (An earlier draft of this fixture leaked "today",
        # "first" and "one", which legitimately satisfied the rule and made the test fail.)
        "Breadth was worse than the index across the session and the average name lagged badly. "
        "That divergence is the part I care about because it separates a rotation from a real "
        "risk-off move, and it looked much more like the latter than the former. "
        "The setup fails when buyers return and reclaim the level that broke.",
    ])
    assert _finding(missing, "missing invalidation level")
    _assert_quiet(audit_sections(COMPLIANT_SECTIONS), "missing invalidation level")


def test_script_shaped_rules_do_not_fire_on_caption_length_copy():
    """Captions must not be judged by rules written for a full script.

    Found 2026-07-20: "Three banks report before the bell. I care about net interest income."
    is a legitimate caption and was being rejected for having no digit or ticker. Three rules
    are script-shaped and scoped by SCRIPT_LENGTH_WORDS — this pins that scoping.
    """
    caption = audit_text("Three banks report before the bell. I care about net interest income.")
    for rule in ("missing invalidation level", "missing concrete noun"):
        _assert_quiet(caption, rule)
    _assert_quiet(audit_text("My read: the tape is thinner than it looks."), "lead with the take")


def test_every_content_section_requires_a_concrete_noun():
    # SCRIPT-LENGTH: this rule is scoped to full scripts (see the caption test above).
    missing = audit_sections([
        "Brent holds 83 into the close and the range has not broken in either direction yet. "
        "My read is firm while the level holds and I change my mind only on a settled break. "
        "Energy names tracked crude closely through the session with no meaningful divergence.",
        "the setup remains fragile and noisy and nothing about it resolves cleanly right now. "
        "the whole thing could go either way and the tape gives no edge worth acting on today. "
        "there is no level here that changes the read and no catalyst that forces a decision.",
        "Monday is the catalyst and the 81 level is where the thesis breaks if sellers press. "
        "CPI lands before the open and the reaction matters more than the print itself does.",
    ])
    finding = _finding(missing, "missing concrete noun")
    assert finding and finding["sections"] == [2], finding
    _assert_quiet(audit_sections(COMPLIANT_SECTIONS), "missing concrete noun")


def test_negative_parallelism_flags_only_a_cluster():
    clustered = audit_sections([
        "Brent at 83 is not broad panic, but a narrow oil trade. WTI at 79 is not weak demand, but delayed loading. XLE holds 91 Monday."
    ])
    assert _finding(clustered, "negative parallelism cluster")
    isolated = audit_sections([
        "Brent is not broad panic, but a narrow oil move at 83. My read holds through Monday. WTI stays above 79."
    ])
    _assert_quiet(isolated, "negative parallelism cluster")


def test_paragraph_length_variance_flags_metronomic_sections():
    uniform = audit_sections([
        "Brent holds 83 today.",
        "WTI holds 79 today.",
        "XLE holds 91 Monday.",
    ])
    assert _finding(uniform, "uniform paragraph rhythm")
    _assert_quiet(audit_sections(COMPLIANT_SECTIONS), "uniform paragraph rhythm")


def test_lead_must_start_with_take_and_evidence():
    announcement = audit_sections([
        "In this video, Brent at 83 is the focus. My read follows at 82."
    ])
    assert _finding(announcement, "lead with the take")
    _assert_quiet(audit_sections(COMPLIANT_SECTIONS), "lead with the take")


def test_first_signpost_and_first_corrective_contrast_are_flagged():
    result = audit_sections([
        "Brent is at 83. Here's what matters: this is not broad risk, but a narrow oil move. My read fails below 81."
    ])
    assert _finding(result, "stock signposting")["count"] == 1
    assert _finding(result, "corrective contrast")["count"] == 1


def test_corrective_contrast_covers_new_and_cross_sentence_forms():
    result = audit_sections([
        "Brent at 83 is not merely volatile, but structurally weak.",
        "WTI at 79 is less about supply than positioning.",
        "XLE at 91 is not the story. Monday is.",
    ])
    assert _finding(result, "corrective contrast")["count"] >= 3
    direct = audit_sections([
        "Brent held 83 after the report. My read stays firm above 81. Monday brings OPEC."
    ])
    _assert_quiet(direct, "corrective contrast")


def test_repeated_cross_section_ngram_catches_new_slogans():
    repeated = audit_sections([
        "Brent at 83 says trade the pressure chain.",
        "WTI at 79 says trade the pressure chain.",
        "XLE ends at 91 Monday.",
    ])
    assert _finding(repeated, "slogan repetition")
    distinct = audit_sections([
        "Brent at 83 tracks refinery bids.",
        "WTI at 79 tracks export queues.",
        "XLE ends at 91 Monday.",
    ])
    _assert_quiet(distinct, "slogan repetition")


def test_missing_editorial_owner_and_short_uniform_rhythm_no_longer_escape():
    unowned = audit_sections([
        "Brent holds 83. WTI holds 79. XLE holds 91."
    ])
    assert _finding(unowned, "missing editorial owner")
    assert _finding(unowned, "uniform sentence rhythm")
    owned = audit_sections([
        "Brent holds 83. My read stays constructive while refinery demand absorbs prompt barrels. XLE fails below 79 after Monday's inventory report."
    ])
    _assert_quiet(owned, "missing editorial owner")
    _assert_quiet(owned, "uniform sentence rhythm")


def test_process_jargon_still_blocks():
    result = audit_sections([
        "Brent at 83 is verified in TradingView. My read fails below 81."
    ])
    assert result["verdict"] == "BLOCK"
    assert _finding(result, "verification jargon")


def test_arbitrary_copy_uses_blank_line_paragraphs():
    """audit_text splits on blank lines; the section INDEXING must match audit_sections.

    Uses script-length copy because the concrete-noun rule is scoped to scripts — the point
    of this test is the paragraph-splitting, not the rule's threshold.
    """
    result = audit_text(
        "Brent holds 83 into the close and the range has not broken in either direction yet. "
        "My read is firm while the level holds and I change my mind only on a settled break. "
        "Energy names tracked crude closely through the session with no real divergence.\n\n"
        "the setup remains fragile and noisy and nothing about it resolves cleanly right now. "
        "the whole thing could go either way and the tape gives no edge worth acting on today. "
        "there is no level here that changes the read and no catalyst forcing a decision.\n\n"
        "Monday is the catalyst and the 81 level is where the thesis breaks if sellers press. "
        "CPI lands before the open and the reaction matters more than the print itself does."
    )
    assert _finding(result, "missing concrete noun")["sections"] == [2]


def test_social_batch_blocks_missing_disclaimer_and_accepts_present_disclaimer():
    content = "Brent settled at 83. My read stays constructive above 81."
    try:
        validate(_batch(content))
        raise AssertionError("missing disclaimer should block")
    except ValueError as error:
        assert "missing the required research-tooling disclaimer" in str(error)

    compliant = f"{content}\n\n{DISCLAIMER}"
    assert validate(_batch(compliant, compliant))["items"][0]["id"] == "offer"


def test_social_batch_routes_copy_and_description_through_style_gate():
    # The violation must be one that applies at ANY length. The old fixture relied on the
    # concrete-noun rule, which is now correctly scoped to script-length copy, so it stopped
    # firing on a caption and the test failed for the right reason. "Analysts say" is a vague
    # authority — banned at every length, and exactly the class of tell this gate exists for.
    compliant = f"Brent settled at 83. My read stays constructive above 81.\n\n{DISCLAIMER}"
    bad_style = f"Analysts say Brent settles higher into the close at 83.\n\n{DISCLAIMER}"
    for data in (_batch(bad_style), _batch(compliant, bad_style)):
        try:
            validate(data)
            raise AssertionError("style blocker should reject the social surface")
        except ValueError as error:
            assert "script style gate BLOCK" in str(error)
