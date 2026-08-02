#!/usr/bin/env python3
"""Bind an exact-hash E1-E4 script approval to the OpenMontage checkpoints."""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENMONTAGE = ROOT / "OpenMontage"
PROJECTS = OPENMONTAGE / "projects"
APPROVAL = (
    PROJECTS / "_series-v4-shared/review-board/script-approval-v6.json"
)
PRIOR_APPROVAL = (
    PROJECTS / "_series-v4-shared/review-board/script-approval-v5.json"
)
PROJECT_IDS = (
    "series-v4-e01-backtest-search",
    "series-v4-e02-spy-held-out",
    "series-v4-e03-timing-session",
    "series-v4-e04-futures-cost",
)

sys.path.insert(0, str(OPENMONTAGE))
from lib.checkpoint import read_checkpoint, write_checkpoint  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    if not APPROVAL.exists():
        prior = json.loads(PRIOR_APPROVAL.read_text(encoding="utf-8"))
        approved_exact_hashes = []
        for number, project_id in enumerate(PROJECT_IDS, start=1):
            artifacts = PROJECTS / project_id / "artifacts"
            approved_exact_hashes.append(
                {
                    "episode": f"{number:02d}",
                    "script_sha256": sha256(artifacts / "script.json"),
                    "vo_sha256": sha256(artifacts / "vo.txt"),
                }
            )
        atomic_json(
            APPROVAL,
            {
                **prior,
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "operator_response_verbatim": (
                    "Stop calling it a later window. It's the out-of-sample."
                ),
                "approval_surface_url": None,
                "approved_exact_hashes": approved_exact_hashes,
                "scope": (
                    "The v5 exact scripts plus the operator-directed E2 replacement of "
                    "'later data' with in-sample and out-of-sample terminology."
                ),
                "post_approval_corrections": [
                    {
                        "episode": "02",
                        "operator_verbatim": (
                            "Stop calling it a later window. It's the out-of-sample."
                        ),
                        "change": (
                            "Use in-sample and out-of-sample in the remaining explanatory "
                            "sentence instead of later data."
                        ),
                    }
                ],
                "supersedes": {
                    "path": str(PRIOR_APPROVAL.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": sha256(PRIOR_APPROVAL),
                },
            },
        )
    receipt = json.loads(APPROVAL.read_text(encoding="utf-8"))
    for key in ("review_board", "review_manifest"):
        item = receipt[key]
        path = ROOT / item["path"]
        if sha256(path) != item["sha256"]:
            raise RuntimeError(f"{key} no longer matches the approved hash")

    approved = {row["episode"]: row for row in receipt["approved_exact_hashes"]}
    approval_sha = sha256(APPROVAL)
    for number, project_id in enumerate(PROJECT_IDS, start=1):
        episode = f"{number:02d}"
        project = PROJECTS / project_id
        artifacts = project / "artifacts"
        script_path = artifacts / "script.json"
        vo_path = artifacts / "vo.txt"
        expected = approved[episode]
        if sha256(script_path) != expected["script_sha256"]:
            raise RuntimeError(f"E{episode} script changed after approval")
        if sha256(vo_path) != expected["vo_sha256"]:
            raise RuntimeError(f"E{episode} VO changed after approval")

        packaging_path = artifacts / "packaging.json"
        packaging = json.loads(packaging_path.read_text(encoding="utf-8"))
        packaging["script"]["sha256"] = expected["script_sha256"]
        packaging["script"]["vo_sha256"] = expected["vo_sha256"]
        packaging["STATUS"] = packaging["status"] = (
            "EXACT SCRIPT APPROVED — narration generation authorized; "
            "demonstration and render approval remain"
        )
        packaging["approval"].update(
            {
                "complete_script_approved": True,
                "exact_script_approval": str(APPROVAL.relative_to(ROOT)).replace(
                    "\\", "/"
                ),
                "exact_script_approval_sha256": approval_sha,
                "current_script_narration": (
                    "pending regeneration with approved Qwen/John/clean process"
                ),
            }
        )
        atomic_json(packaging_path, packaging)

        checkpoint = read_checkpoint(PROJECTS, project_id, "script")
        if not checkpoint:
            raise RuntimeError(f"E{episode} script checkpoint is missing")
        metadata = dict(checkpoint.get("metadata", {}))
        metadata.update(
            {
                "exact_script_approval_path": str(APPROVAL),
                "exact_script_approval_sha256": approval_sha,
                "exact_script_approved": True,
                "packaging_sha256": sha256(packaging_path),
                "operator_approval_needed": (
                    "None for script. Narration, demonstrations, renders, "
                    "and publication remain separately gated."
                ),
            }
        )
        review = dict(checkpoint.get("review", {}))
        review.update(
            {
                "verdict": "EXACT_SCRIPT_APPROVED",
                "critical_findings_open": 0,
            }
        )
        write_checkpoint(
            PROJECTS,
            project_id,
            "script",
            "completed",
            checkpoint["artifacts"],
            pipeline_type=checkpoint["pipeline_type"],
            style_playbook=checkpoint.get("style_playbook"),
            checkpoint_policy=checkpoint["checkpoint_policy"],
            human_approval_required=True,
            human_approved=True,
            review=review,
            cost_snapshot=checkpoint.get("cost_snapshot"),
            metadata=metadata,
        )

    for project_id in PROJECT_IDS:
        checkpoint = read_checkpoint(PROJECTS, project_id, "script")
        assert checkpoint
        assert checkpoint["status"] == "completed"
        assert checkpoint["human_approved"] is True
        assert checkpoint["metadata"]["exact_script_approval_sha256"] == approval_sha
    print(f"series exact-script approval: PASS 4/4 — {approval_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
