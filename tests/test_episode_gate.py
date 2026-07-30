import json
import sys
import types
from pathlib import Path

import pytest

from tools import episode_gate
from tools import upload_youtube


def _write(path: Path, data: str | bytes = "x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        path.write_text(data, encoding="utf-8")
    return path


def _episode(tmp_path: Path):
    proj = tmp_path / "projects" / "series-01-test"
    art = proj / "artifacts"
    package = {
        "episode": 1,
        "syllabus_episode": "01",
        "title": "The Golden Cross Passed. That Was the Problem.",
        "release": {
            "privacy": "private",
            "category": "22",
            "containsSyntheticMedia": True,
            "captionLanguage": "en",
            "captionName": "English",
        },
    }
    _write(art / "packaging.json", json.dumps(package))
    script = _write(art / "vo.txt", "# receipt: C1\nA sourced sentence.\n")
    _write(art / "scenes.json", "{}")
    _write(art / "claims.json", "{}")
    capture = _write(art / "operator-capture.txt", "This is how I explain it.")
    passport = _write(art / "strategy-passport.json", json.dumps({
        "schema": "strategy-passport/v1",
        "strategy": {
            "asset_class": "equity",
            "instrument": "SPY",
            "venue": "NYSE Arca",
            "timeframe": "D1",
            "session_timezone": "America/New_York",
            "entry": "Close above SMA(200) and RSI(2) below 5.",
            "exits": ["Close above SMA(5)."],
            "sizing": "One test unit.",
            "costs": "Receipt-backed equity cost model.",
            "parameters": {"rsi_period": 2, "rsi_entry": 5, "exit_sma": 5},
        },
        "validation": {
            "phase": "out-of-sample",
            "test_window": "Receipt-defined historical window.",
            "settings": {"split": "ordered"},
            "thresholds": {"net": "> 0"},
            "result": {"survivors": 0},
        },
        "sources": [{
            "citation": "run.json",
            "locator": "$.phase02",
            "supports": "The candidate failed OOS.",
            "limitations": "One strategy and one asset.",
        }],
        "limitations": ["Teaching artifact, not a recommendation."],
    }))
    _write(art / "human-facing-review.json", json.dumps({
        "schema": "human-facing-review/v1",
        "script_sha256": episode_gate.sha256(script),
        "operator_capture_sha256": episode_gate.sha256(capture),
        "strategy_passport_sha256": episode_gate.sha256(passport),
        "protected_items_status": "PASS",
        "disclosure_status": "PASS",
        "independent_critic": {
            "reviewer": "critic-1",
            "status": "PASS",
            "unresolved_findings": [],
        },
        "operator_read_aloud": {
            "operator": "operator",
            "status": "APPROVED",
            "date": "2026-07-30",
        },
    }))
    _write(art / "operator-script-approval.json", json.dumps({
        "schema": "tradercockpit-series-script-approval/v1",
        "status": "approved",
        "script": "vo.txt",
        "scriptSha256": episode_gate.sha256(script),
        "reviewedBy": "operator",
        "reviewedAt": "2026-07-30T10:00:00+07:00",
        "approvalKind": "operator",
        "operatorReviewed": True,
        "attestations": {
            "readAloud": True,
            "phrasingATraderWouldSay": True,
            "factSeparatedFromJudgment": True,
        },
    }))
    _write(art / "_yt_desc.txt", "A sourced description.\n")
    _write(art / "_yt_tags.json", '["backtesting", "golden cross"]')
    _write(art / "thumbnail-ep01.html", "<p>PASS?</p>")
    thumb = _write(art / "thumbnail-ep01.png", b"png")
    _write(proj / "assets" / "subtitles.srt", "1\n00:00:00,000 --> 00:00:01,000\nWords\n")
    _write(proj / "hyperframes" / "index.html", "<main>Episode</main>")
    master = _write(proj / "master.mp4", b"master")
    _write(art / "operator-master-approval.json", json.dumps({
        "schema": "tradercockpit-series-master-approval/v1",
        "status": "approved",
        "master": "master.mp4",
        "sha256": episode_gate.sha256(master),
        "reviewedBy": "operator",
        "reviewedAt": "2026-07-30T10:30:00+07:00",
        "approvalKind": "operator",
        "operatorReviewed": True,
        "publicationAuthorized": False,
    }))
    return proj, art, master, thumb, package


def _certify(proj: Path, art: Path, master: Path):
    meta = episode_gate.episode_meta(art)
    release, inputs = episode_gate.release_contract(proj, art, meta, master=master)
    receipt = {
        "schema": "episode-gate/v2",
        "verdict": "GREEN",
        "partial": False,
        "source_only": False,
        "master_sha256": episode_gate.sha256(master),
        "inputs": inputs,
        "release": release,
        "blocked": [],
        "gates": {
            "release_contract": {"verdict": "PASS"},
            **{name: {"verdict": "PASS"} for name, *_ in episode_gate.CHAIN},
        },
        "waived": [],
    }
    _write(art / "build" / "gate-receipt.json", json.dumps(receipt))
    return release


def test_certification_binds_sources_and_exact_upload_values(tmp_path, monkeypatch):
    proj, art, master, thumb, package = _episode(tmp_path)
    monkeypatch.setattr(episode_gate, "OM", tmp_path)
    release = _certify(proj, art, master)

    assert episode_gate.verify(master, quiet=True) == 0
    copied = _write(tmp_path / "copied.mp4", master.read_bytes())
    assert episode_gate.verify(copied, quiet=True) == 1
    assert episode_gate.verify_release(
        master,
        title=package["title"],
        description=release["description"],
        tags=release["tags"],
        category="22",
        privacy="private",
        thumbnail=thumb,
        synthetic=True,
    ) == 0
    assert episode_gate.verify_release(
        master,
        title="Changed after certification",
        description=release["description"],
        tags=release["tags"],
        category="22",
        privacy="public",
        thumbnail=thumb,
        synthetic=False,
    ) == 1

    receipt_path = art / "build" / "gate-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["gates"] = {}
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert episode_gate.verify(master, quiet=True) == 1
    _certify(proj, art, master)

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["inputs"].pop("artifacts/claims.json")
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert episode_gate.verify(master, quiet=True) == 1
    _certify(proj, art, master)

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["gates"]["term_gate"] = {"verdict": "WAIVED"}
    receipt["waived"] = ["term_gate"]
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    assert episode_gate.verify(master, quiet=True) == 1
    _certify(proj, art, master)

    (art / "_yt_desc.txt").write_text("Drifted description.\n", encoding="utf-8")
    assert episode_gate.verify(master, quiet=True) == 1


def test_source_mode_runs_no_render_gate_and_cannot_certify(tmp_path, monkeypatch):
    proj, art, _, _, _ = _episode(tmp_path)
    for path in (
        art / "scenes.json",
        art / "thumbnail-ep01.html",
        art / "thumbnail-ep01.png",
        proj / "assets" / "subtitles.srt",
        proj / "hyperframes" / "index.html",
    ):
        path.unlink()
    seen = []
    monkeypatch.setattr(episode_gate, "CHAIN", (
        ("source_check", "repo", ["tools/source.py"], False),
        ("render_check", "repo", ["tools/render.py"], True),
    ))
    monkeypatch.setattr(episode_gate, "SOURCE_GATES", {"source_check"})
    monkeypatch.setattr(
        episode_gate,
        "run_gate",
        lambda name, *_: seen.append(name) or
        {"verdict": "PASS", "rc": 0, "detail": ""},
    )

    assert episode_gate.run(proj, None, None, source_only=True) == 0
    assert seen == ["source_check"]
    receipt = json.loads((art / "build" / "source-gate-receipt.json").read_text())
    assert receipt["source_only"] is True
    assert not (art / "build" / "gate-receipt.json").exists()


def test_quality_review_must_match_final_script_and_strategy_passport(tmp_path):
    _, art, _, _, _ = _episode(tmp_path)
    review_path = art / "human-facing-review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["protected_items_status"] = "WARN"
    review_path.write_text(json.dumps(review), encoding="utf-8")

    with pytest.raises(ValueError, match="protected_items_status"):
        episode_gate.quality_review_contract(art)


def test_script_approval_must_be_operator_reviewed(tmp_path):
    _, art, _, _, _ = _episode(tmp_path)
    approval_path = art / "operator-script-approval.json"
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    approval["operatorReviewed"] = False
    approval_path.write_text(json.dumps(approval), encoding="utf-8")

    with pytest.raises(ValueError, match="operator-reviewed"):
        episode_gate.quality_review_contract(art)


def test_certified_source_paths_cannot_escape_episode(tmp_path, monkeypatch):
    proj, art, master, _, _ = _episode(tmp_path)
    monkeypatch.setattr(episode_gate, "OM", tmp_path)
    _certify(proj, art, master)
    outside = _write(proj.parent / "outside.txt", "outside")
    receipt_path = art / "build" / "gate-receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["inputs"] = {"../outside.txt": episode_gate.sha256(outside)}
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    assert episode_gate.verify(master, quiet=True) == 1


def test_required_writing_and_claim_gates_are_in_the_chain():
    names = {name for name, *_ in episode_gate.CHAIN}
    assert {
        "teaching_claim_gate",
        "human_narration",
        "human_title",
        "human_description",
    } <= names
    assert "ai_writing_gate" not in names


def test_uploader_blocks_before_auth_when_public_values_are_not_certified(
    tmp_path, monkeypatch
):
    http = types.ModuleType("googleapiclient.http")
    http.MediaFileUpload = object
    google = types.ModuleType("googleapiclient")
    google.http = http
    monkeypatch.setitem(sys.modules, "googleapiclient", google)
    monkeypatch.setitem(sys.modules, "googleapiclient.http", http)
    seen = {}

    def reject(master, **values):
        seen.update(master=master, **values)
        return 1

    monkeypatch.setattr(upload_youtube.episode_gate, "verify_release", reject)
    monkeypatch.setattr(
        upload_youtube,
        "get_service",
        lambda **_: pytest.fail("authentication ran before release verification"),
    )
    video = _write(tmp_path / "master.mp4", b"master")

    with pytest.raises(SystemExit, match="not certified"):
        upload_youtube.upload(
            str(video),
            "Changed title",
            "Changed description",
            ["changed"],
            privacy="public",
            thumbnail=str(tmp_path / "thumb.png"),
            synthetic=False,
            approval_lane="series",
        )
    assert seen["title"] == "Changed title"
    assert seen["privacy"] == "public"
    assert seen["synthetic"] is False


def test_uploader_requires_exact_provider_metadata_readback(tmp_path, monkeypatch):
    http = types.ModuleType("googleapiclient.http")
    http.MediaFileUpload = lambda *_args, **_kwargs: object()
    google = types.ModuleType("googleapiclient")
    google.http = http
    monkeypatch.setitem(sys.modules, "googleapiclient", google)
    monkeypatch.setitem(sys.modules, "googleapiclient.http", http)
    monkeypatch.setattr(upload_youtube.episode_gate, "verify_release", lambda *_a, **_k: 0)
    caption_file = _write(tmp_path / "captions.srt", b"caption bytes")
    monkeypatch.setattr(
        upload_youtube.episode_gate,
        "read_release_receipt",
        lambda _master: (tmp_path, {
            "captions": caption_file.name,
            "captionLanguage": "en",
            "captionName": "English",
        }),
    )

    class Request:
        def __init__(self, response):
            self.response = response

        def execute(self):
            return self.response() if callable(self.response) else self.response

        def next_chunk(self):
            response = self.response() if callable(self.response) else self.response
            return None, response

    def service(readback_title, fail_final=False):
        state = {"privacy": "private", "insert_privacy": None, "list_calls": 0}

        def item():
            return {
                "id": "video-1",
                "snippet": {
                    "title": readback_title,
                    "description": "Description",
                    "tags": ["testing"],
                    "categoryId": "22",
                },
                "status": {
                    "privacyStatus": state["privacy"],
                    "selfDeclaredMadeForKids": False,
                    "containsSyntheticMedia": True,
                },
            }

        def insert(**kwargs):
            state["insert_privacy"] = kwargs["body"]["status"]["privacyStatus"]
            return Request({"id": "video-1"})

        def update(**kwargs):
            state["privacy"] = kwargs["body"]["status"]["privacyStatus"]
            return Request({"id": "video-1", "status": kwargs["body"]["status"]})

        def list_videos(**_kwargs):
            state["list_calls"] += 1
            if fail_final and state["list_calls"] == 2:
                def fail():
                    raise RuntimeError("final list failed")
                return Request(fail)
            return Request(lambda: {"items": [item()]})

        videos = types.SimpleNamespace(
            insert=insert,
            list=list_videos,
            update=update,
        )
        caption = {
            "id": "caption-1",
            "snippet": {
                "videoId": "video-1",
                "language": "en",
                "name": "English",
                "isDraft": False,
            },
        }
        captions = types.SimpleNamespace(
            insert=lambda **_kwargs: Request(caption),
            list=lambda **_kwargs: Request({"items": [caption]}),
            download=lambda **_kwargs: Request(caption_file.read_bytes()),
        )
        return types.SimpleNamespace(
            videos=lambda: videos,
            captions=lambda: captions,
            _state=state,
        )

    exact_service = service("Title")
    monkeypatch.setattr(upload_youtube, "get_service", lambda **_: exact_service)
    result = upload_youtube.upload(
        "master.mp4", "Title", "Description", ["testing"], synthetic=True,
        privacy="public", approval_lane="series",
    )
    assert result["id"] == "video-1"
    assert exact_service._state["insert_privacy"] == "private"
    assert exact_service._state["privacy"] == "public"

    monkeypatch.setattr(upload_youtube, "get_service", lambda **_: service("Changed"))
    with pytest.raises(RuntimeError, match="title"):
        upload_youtube.upload(
            "master.mp4", "Title", "Description", ["testing"], synthetic=True,
            privacy="public", approval_lane="series",
        )

    failing_service = service("Title", fail_final=True)
    monkeypatch.setattr(upload_youtube, "get_service", lambda **_: failing_service)
    with pytest.raises(RuntimeError, match="final list failed"):
        upload_youtube.upload(
            "master.mp4", "Title", "Description", ["testing"], synthetic=True,
            privacy="public", approval_lane="series",
        )
    assert failing_service._state["privacy"] == "private"


def test_social_batch_lane_requires_exact_approval_reference(monkeypatch):
    monkeypatch.setattr(
        upload_youtube,
        "get_service",
        lambda **_: pytest.fail("authentication ran before social approval verification"),
    )
    with pytest.raises(SystemExit, match="approval_ref"):
        upload_youtube.upload("master.mp4", "Title", approval_lane="social_batch")
