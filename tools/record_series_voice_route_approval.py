#!/usr/bin/env python3
"""Bind the operator's E1-E5 Higgsfield/Qwen/John/clean selection."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "OpenMontage/projects"
SHARED = PROJECTS / "_series-v4-shared"
APPROVAL = SHARED / "review-board/voice-route-approval-e1-e5-v7.json"
PRIOR_APPROVAL = SHARED / "review-board/voice-route-approval-e1-e5-v6.json"
SCRIPT_APPROVAL = SHARED / "review-board/script-approval-v6.json"
REFERENCE = (
    PROJECTS
    / "series-04-mc-param/artifacts/voice-auditions/ep04-qwen-john-clean.wav"
)
PROJECT_IDS = (
    "series-v4-e01-backtest-search",
    "series-v4-e02-spy-held-out",
    "series-v4-e03-timing-session",
    "series-v4-e04-futures-cost",
    "series-04-mc-param",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    canonical = [
        {
            "episode": number,
            "script_path": str(
                (PROJECTS / project_id / "artifacts/script.json").relative_to(ROOT)
            ).replace("\\", "/"),
            "script_sha256": sha256(PROJECTS / project_id / "artifacts/script.json"),
            "vo_path": str(
                (PROJECTS / project_id / "artifacts/vo.txt").relative_to(ROOT)
            ).replace("\\", "/"),
            "vo_sha256": sha256(PROJECTS / project_id / "artifacts/vo.txt"),
        }
        for number, project_id in enumerate(PROJECT_IDS, start=1)
    ]
    if not APPROVAL.exists():
        atomic_json(
            APPROVAL,
            {
                "schema": "tradercockpit-series-voice-route-approval/v1",
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "source_thread_id": "019fb10f-e09f-7b23-8998-d5d2b2e90a3f",
                "operator_responses_verbatim": [
                    "john clean",
                    (
                        "Why are you worried about the local when I chose the other one? "
                        "We're using Hicksfield. You have to get the free nonsense out of "
                        "the path."
                    ),
                    (
                        "Remove the free. When we're trying to do the YouTube series. "
                        "We're not doing it for free. We have Hatesville for a reason."
                    ),
                    "Complete all five episodes. Complete all five episodes.",
                ],
                "scope": {"episodes": [1, 2, 3, 4, 5], "episode_5": True},
                "selection": {
                    "provider": "Higgsfield",
                    "model": "Qwen Audio 3.0 TTS Flash",
                    "job_type": "qwen_audio_tts",
                    "voice_character": "John",
                    "treatment": "clean",
                    "generation_route": "existing Higgsfield subscription",
                    "piper_rejected": True,
                    "local_chatterbox_rejected": True,
                    "subscription_credit_use_authorized": True,
                    "new_subscription_or_top_up_authorized": False,
                },
                "supersedes": {
                    "path": str(PRIOR_APPROVAL.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": sha256(PRIOR_APPROVAL),
                    "reason": (
                        "Bind all five exact scripts after the operator's out-of-sample "
                        "terminology correction while preserving the approved E1 70/30 "
                        "technical label; pronunciation expansion remains provider-only."
                    ),
                },
                "canonical_script_approval": {
                    "path": str(SCRIPT_APPROVAL.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": sha256(SCRIPT_APPROVAL),
                },
                "episode_canonical": canonical,
                "post_approval_corrections": [
                    {
                        "episode": 2,
                        "operator_verbatim": (
                            "Stop calling it a later window. It's the out-of-sample."
                        ),
                        "change": (
                            "Use in-sample and out-of-sample in the remaining explanatory "
                            "sentence instead of later data."
                        ),
                    }
                ],
                "approved_reference": {
                    "path": str(REFERENCE.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": sha256(REFERENCE),
                },
                "boundaries": [
                    (
                        "This approves Higgsfield Qwen Audio 3.0 TTS Flash, John, "
                        "clean for the current exact E1-E5 scripts."
                    ),
                    "Existing Higgsfield subscription credits may be consumed.",
                    "No new subscription, credit top-up, or metered API purchase is approved.",
                    "This rejects Piper for the E1-E5 narration batch.",
                    "This rejects local Chatterbox as the active E1-E5 narration route.",
                    "This does not approve upload or publication.",
                ],
            },
        )

    receipt = json.loads(APPROVAL.read_text(encoding="utf-8"))
    for key, path in (
        ("approved_reference", REFERENCE),
        ("canonical_script_approval", SCRIPT_APPROVAL),
        ("supersedes", PRIOR_APPROVAL),
    ):
        if receipt[key]["sha256"] != sha256(path):
            raise RuntimeError(f"{key} no longer matches the selected voice receipt")
    if receipt.get("episode_canonical") != canonical:
        raise RuntimeError("An E1-E5 canonical script changed after voice authorization")
    approval_sha = sha256(APPROVAL)

    for number, project_id in enumerate(PROJECT_IDS, start=1):
        artifacts = PROJECTS / project_id / "artifacts"
        decision_path = artifacts / "decision_log.json"
        decision_log = json.loads(decision_path.read_text(encoding="utf-8"))
        decision_id = f"e{number:02d}-v4-d005"
        if not any(row["decision_id"] == decision_id for row in decision_log["decisions"]):
            decision_log["decisions"].append(
                {
                    "decision_id": decision_id,
                    "stage": "assets",
                    "category": "voice_selection",
                    "subject": "Narration TTS provider",
                    "options_considered": [
                        {
                            "option_id": "higgsfield-qwen-john-clean",
                            "label": "Higgsfield Qwen Audio 3.0 / John / clean",
                            "score": 1.0,
                            "reason": (
                                "This is the operator-selected subscription route and "
                                "approved John clean character."
                            ),
                        },
                        {
                            "option_id": "local-chatterbox-john-clean",
                            "label": "Local Chatterbox clone / John / clean",
                            "score": 0.0,
                            "reason": "A local approximation was attempted.",
                            "rejected_because": (
                                "The operator explicitly corrected the route to Higgsfield."
                            ),
                        },
                        {
                            "option_id": "piper-lessac-clean",
                            "label": "Local Piper / Lessac / clean",
                            "score": 0.0,
                            "reason": "The local comparison was available immediately.",
                            "rejected_because": "The operator selected John clean.",
                        },
                    ],
                    "selected": "higgsfield-qwen-john-clean",
                    "reason": (
                        "The operator selected John clean and explicitly required "
                        "Higgsfield for the YouTube series."
                    ),
                    "user_visible": True,
                    "user_approved": True,
                    "confidence": 1.0,
                    "approval_receipt": str(APPROVAL.relative_to(ROOT)).replace("\\", "/"),
                    "approval_receipt_sha256": approval_sha,
                }
            )
            atomic_json(decision_path, decision_log)

        packaging_path = artifacts / "packaging.json"
        packaging = json.loads(packaging_path.read_text(encoding="utf-8"))
        packaging.setdefault("approval", {}).update(
            {
                "voice_route_approved": True,
                "voice_route": "Higgsfield Qwen Audio 3.0 TTS Flash / John / clean",
                "voice_route_approval": str(APPROVAL.relative_to(ROOT)).replace("\\", "/"),
                "voice_route_approval_sha256": approval_sha,
                "current_script_narration": (
                    "pending Higgsfield generation from the current exact approved scripts"
                ),
                "narrator_receipt": (
                    "productions/_series/"
                    "higgsfield-qwen-john-narration-v5-receipt.json"
                ),
                "narrator_receipt_sha256": None,
            }
        )
        atomic_json(packaging_path, packaging)

    for project_id in PROJECT_IDS:
        artifacts = PROJECTS / project_id / "artifacts"
        decision_log = json.loads(
            (artifacts / "decision_log.json").read_text(encoding="utf-8")
        )
        latest = [
            row
            for row in decision_log["decisions"]
            if row["category"] == "voice_selection"
            and row["subject"] == "Narration TTS provider"
        ][-1]
        assert latest["selected"] == "higgsfield-qwen-john-clean"
        packaging = json.loads(
            (artifacts / "packaging.json").read_text(encoding="utf-8")
        )
        assert packaging["approval"]["voice_route_approval_sha256"] == approval_sha

    print(f"series Higgsfield/Qwen/John/clean route: PASS 5/5 — {approval_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
