from tools.episode_gate import compact_gate_detail, covered, source_fingerprint


def test_scoped_waiver_matches_preserved_failure_line():
    output = (
        "FAIL  (a)1 title is not a phase label\n"
        + ("diagnostic context\n" * 200)
        + "BLOCK: 1 of 8 packaging rules fail."
    )
    result = {"detail": compact_gate_detail(output)}
    waiver = {"findings": ["title is not a phase label"]}

    assert covered(result, waiver)


def test_source_fingerprint_changes_with_loaded_composition(tmp_path):
    project = tmp_path / "episode"
    composition = project / "hyperframes" / "compositions" / "scene-01.html"
    composition.parent.mkdir(parents=True)
    composition.write_text("<p>before</p>", encoding="utf-8")
    before = source_fingerprint(project)

    composition.write_text("<p>after</p>", encoding="utf-8")
    after = source_fingerprint(project)

    assert before["file_count"] == after["file_count"] == 1
    assert before["sha256"] != after["sha256"]
