from tools.episode_gate import (
    CHAIN,
    compact_gate_detail,
    covered,
    declared_narration_dir,
    source_fingerprint,
)


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


def test_voice_gate_uses_narration_declared_by_the_edit(tmp_path):
    artifacts = tmp_path / "artifacts"
    narration = tmp_path / "hyperframes" / "assets" / "audio" / "narration-marcus"
    artifacts.mkdir()
    narration.mkdir(parents=True)
    (narration / "scene-01.wav").write_bytes(b"wav")
    (artifacts / "packaging.json").write_text(
        '{"episode":2,"syllabus_episode":"02"}', encoding="utf-8"
    )
    (artifacts / "claims.json").write_text("{}", encoding="utf-8")
    (artifacts / "edit_decisions.json").write_text(
        '{"audio":{"narration":{"segments":['
        '{"path":"hyperframes/assets/audio/narration-marcus/scene-01.wav"}'
        ']}}}',
        encoding="utf-8",
    )

    declared = declared_narration_dir(tmp_path)
    voice_args = next(argv for name, _, argv, _ in CHAIN if name == "voice_consistency")

    assert declared == str(narration)
    assert voice_args == [
        "tools/voice_consistency.py",
        "{narration_dir}",
        "--vo",
        "{art}/vo.txt",
    ]
