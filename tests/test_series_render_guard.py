import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "series_guard", ROOT / ".codex/hooks/series_guard.py"
)
series_guard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(series_guard)


def payload(command: str, workdir: Path = ROOT) -> dict:
    return {
        "tool_name": "Bash",
        "cwd": str(ROOT),
        "tool_input": {"command": command, "workdir": str(workdir)},
    }


def test_exact_v49_stale_audio_concat_is_denied():
    command = (
        '& "OpenMontage\\.tools\\ffmpeg\\bin\\ffmpeg.exe" -y -f concat -safe 0 '
        '-i "C:\\tmp\\ep01-v48-concat.txt" -c copy -movflags +faststart '
        '"Into-the-Laboratory-Episode-01-v49-produced.mp4"'
    )
    decision = series_guard.pretool_decision(payload(command))
    assert decision["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "stale audio" in decision["hookSpecificOutput"]["permissionDecisionReason"]


def test_direct_opener_master_patch_is_denied():
    command = (
        "ffmpeg.exe -y -i episode-01-master.mp4 -map 0:a:0 "
        "Into-the-Laboratory-Episode-01-opener.mp4"
    )
    assert series_guard.pretool_decision(payload(command)) is not None


def test_bounded_review_extract_is_allowed():
    command = (
        "ffmpeg.exe -y -i episode-01-master.mp4 -t 22 -c copy "
        "ep01-splice-review.mp4"
    )
    assert series_guard.pretool_decision(payload(command)) is None


def test_series_contact_sheet_is_allowed():
    command = (
        "ffmpeg.exe -y -i episode-01-master.mp4 -frames:v 1 "
        "ep01-contact-sheet.jpg"
    )
    assert series_guard.pretool_decision(payload(command)) is None


def test_canonical_render_requires_current_preflight():
    project = ROOT / "OpenMontage/projects/series-v4-e01-backtest-search/hyperframes"
    command = "npm run render"
    denied = series_guard.pretool_decision(
        payload(command, project),
        verifier=lambda _: (_ for _ in ()).throw(series_guard.Blocked("missing receipt")),
    )
    assert denied is not None
    assert series_guard.pretool_decision(payload(command, project), verifier=lambda _: None) is None


def test_approved_pilot_render_uses_receipt_bound_exception():
    project = ROOT / "OpenMontage/projects/series-v4-e01-backtest-search/hyperframes"
    command = "hyperframes render . -c pilot/index.html -o ../artifacts/pilot-review/e01-pilot.mp4"
    assert series_guard.pretool_decision(
        payload(command, project),
        verifier=lambda _: (_ for _ in ()).throw(series_guard.Blocked("full render not approved")),
        pilot_verifier=lambda _project, _command: None,
    ) is None


def test_unapproved_pilot_render_is_denied():
    project = ROOT / "OpenMontage/projects/series-v4-e01-backtest-search/hyperframes"
    command = "hyperframes render . -c pilot/index.html -o ../artifacts/pilot-review/e01-pilot.mp4"
    decision = series_guard.pretool_decision(
        payload(command, project),
        pilot_verifier=lambda _project, _command: (_ for _ in ()).throw(
            series_guard.Blocked("missing pilot receipt")
        ),
    )
    assert decision is not None
    assert "missing pilot receipt" in decision["hookSpecificOutput"]["permissionDecisionReason"]


def test_pilot_named_output_without_pilot_composition_still_needs_full_preflight():
    project = ROOT / "OpenMontage/projects/series-v4-e01-backtest-search/hyperframes"
    command = "hyperframes render . -o ../artifacts/pilot-review/full-pilot.mp4"
    decision = series_guard.pretool_decision(
        payload(command, project),
        verifier=lambda _: (_ for _ in ()).throw(series_guard.Blocked("full preflight missing")),
    )
    assert decision is not None
    assert "pilot render must target" in decision["hookSpecificOutput"]["permissionDecisionReason"]


def test_non_series_ffmpeg_is_out_of_scope():
    assert series_guard.pretool_decision(payload("ffmpeg.exe -i daily.mp4 daily-final.mp4")) is None


def test_compaction_and_subagents_reinstate_series_contract():
    for event in ("SessionStart", "SubagentStart"):
        result = series_guard.hook({"hook_event_name": event})
        assert "series-script skill" in result["hookSpecificOutput"]["additionalContext"]
