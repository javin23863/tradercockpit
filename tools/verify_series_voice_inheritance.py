#!/usr/bin/env python3
"""Fail when the current E1-E4 projects forget the approved shared narrator."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "productions/_series/higgsfield-qwen-john-narration-receipt.json"
PROJECTS = (
    "series-v4-e01-backtest-search",
    "series-v4-e02-spy-held-out",
    "series-v4-e03-timing-session",
    "series-v4-e04-futures-cost",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    expected = {
        "receipt_path": str(RECEIPT),
        "receipt_sha256": sha256(RECEIPT),
        "model": receipt["model"]["display_name"],
        "voice": receipt["model"]["voice"],
        "voice_id": receipt["model"]["voice_id"],
        "treatment": receipt["model"]["approved_treatment"],
    }
    errors: list[str] = []
    if receipt.get("status") != "completed":
        errors.append("shared narrator receipt is not completed")

    for project_id in PROJECTS:
        project = ROOT / "OpenMontage/projects" / project_id
        checkpoint = json.loads(
            (project / "checkpoint_script.json").read_text(encoding="utf-8")
        )
        inherited = checkpoint.get("metadata", {}).get("narrator_decision")
        if inherited != expected:
            errors.append(f"{project_id}: narrator decision was not inherited")
        if checkpoint.get("metadata", {}).get("operator_capture") == "missing":
            errors.append(f"{project_id}: obsolete operator-capture blocker remains")

        review_path = project / "artifacts/review_script.json"
        review_text = review_path.read_text(encoding="utf-8").lower()
        if "operator capture" in review_text or "voice capture" in review_text:
            errors.append(f"{project_id}: review still requests a capture")

        board_path = Path(checkpoint.get("metadata", {}).get("review_board_path", ""))
        if not board_path.is_file():
            errors.append(f"{project_id}: review board is missing")
        elif "voice capture" in board_path.read_text(encoding="utf-8").lower():
            errors.append(f"{project_id}: review board still requests a capture")

    if errors:
        print("series voice inheritance: BLOCK")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("series voice inheritance: PASS — Qwen Audio 3.0 / John / clean inherited 4/4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
