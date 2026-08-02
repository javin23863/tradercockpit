#!/usr/bin/env python3
"""Run the fail-closed script-stage checks for current teaching Episodes 1-4."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "OpenMontage/.venv/Scripts/python.exe"
PROJECTS = (
    ("01", "series-v4-e01-backtest-search"),
    ("02", "series-v4-e02-spy-held-out"),
    ("03", "series-v4-e03-timing-session"),
    ("04", "series-v4-e04-futures-cost"),
)
APPROVAL = (
    ROOT
    / "OpenMontage/projects/_series-v4-shared/review-board/script-approval-v6.json"
)
SLOT = re.compile(r"^=== SLOT (scene-\d+) ")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slot_texts(vo: Path) -> dict[str, str]:
    texts: dict[str, list[str]] = {}
    current: str | None = None
    for raw in vo.read_text(encoding="utf-8").splitlines():
        match = SLOT.match(raw)
        if match:
            current = match.group(1)
            texts[current] = []
        elif current and raw.strip() and not raw.lstrip().startswith("#"):
            texts[current].append(raw.strip())
    return {scene: " ".join(lines) for scene, lines in texts.items()}


def run(label: str, args: list[str], expected: int = 0) -> str:
    result = subprocess.run(
        [str(PYTHON), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != expected:
        output = (result.stdout + result.stderr).strip()
        raise RuntimeError(f"{label}: exit {result.returncode}\n{output}")
    return result.stdout


def main() -> int:
    approval = json.loads(APPROVAL.read_text(encoding="utf-8"))
    approved = {row["episode"]: row for row in approval["approved_exact_hashes"]}
    for key in ("review_board", "review_manifest"):
        item = approval[key]
        if sha256(ROOT / item["path"]) != item["sha256"]:
            raise RuntimeError(f"{key} no longer matches the approved hash")

    for episode, project_id in PROJECTS:
        project = ROOT / "OpenMontage/projects" / project_id
        artifacts = project / "artifacts"
        vo_path = artifacts / "vo.txt"
        script_path = artifacts / "script.json"
        claims_path = artifacts / "claims.json"
        packaging_path = artifacts / "packaging.json"

        script = json.loads(script_path.read_text(encoding="utf-8"))
        spoken = slot_texts(vo_path)
        sections = {item["id"]: item for item in script["sections"]}
        if set(spoken) != set(sections):
            raise RuntimeError(f"E{episode}: script and VO scene IDs differ")
        for scene, text in spoken.items():
            if sections[scene]["text"] != text:
                raise RuntimeError(f"E{episode} {scene}: script text does not match VO")
            if sections[scene]["delivery_cues"]["provider_text"] != text:
                raise RuntimeError(f"E{episode} {scene}: provider text does not match VO")

        claims = json.loads(claims_path.read_text(encoding="utf-8"))
        if claims["script_sha256"] != sha256(vo_path):
            raise RuntimeError(f"E{episode}: claims receipt does not match VO hash")
        packaging = json.loads(packaging_path.read_text(encoding="utf-8"))
        if sha256(script_path) != approved[episode]["script_sha256"]:
            raise RuntimeError(f"E{episode}: script no longer matches approval")
        if sha256(vo_path) != approved[episode]["vo_sha256"]:
            raise RuntimeError(f"E{episode}: VO no longer matches approval")
        if packaging["script"]["sha256"] != sha256(script_path):
            raise RuntimeError(f"E{episode}: packaging does not match script hash")
        if packaging["script"]["vo_sha256"] != sha256(vo_path):
            raise RuntimeError(f"E{episode}: packaging does not match VO hash")
        if not packaging["approval"].get("narrator_decision_inherited"):
            raise RuntimeError(f"E{episode}: approved narrator was not inherited")
        if not packaging["approval"].get("complete_script_approved"):
            raise RuntimeError(f"E{episode}: exact script approval was not inherited")
        if packaging["approval"].get("exact_script_approval_sha256") != sha256(APPROVAL):
            raise RuntimeError(f"E{episode}: script approval receipt hash is stale")

        run(
            f"E{episode} academic/ontology",
            [
                "tools/teaching_claim_gate.py",
                "--script",
                str(vo_path),
                "--ontology",
                str(claims_path),
            ],
        )
        run(f"E{episode} arc", ["tools/script_arc_gate.py", str(project)])
        run(
            f"E{episode} terminology",
            [
                "tools/term_gate.py",
                "--production",
                str(project),
                "--episode",
                episode,
                "--strict",
            ],
        )
        run(
            f"E{episode} style",
            [
                "tools/script_style_gate.py",
                str(artifacts),
                "--out",
                str(artifacts / "build/script-style-gate.json"),
            ],
        )
        run(
            f"E{episode} AI-writing",
            [
                "tools/ai_writing_gate.py",
                str(artifacts),
                "--out",
                str(artifacts / "build/ai-writing-gate.json"),
            ],
        )
        run(
            f"E{episode} teaching register",
            ["tools/ai_tell_gate.py", str(artifacts), "--register", "teach"],
        )

        packaging_output = run(
            f"E{episode} packaging",
            ["tools/packaging_gate.py", str(packaging_path)],
            expected=1 if episode in {"02", "04"} else 0,
        )
        packaging_status = "PASS"
        if episode in {"02", "04"}:
            waiver = json.loads((artifacts / "waivers.json").read_text(encoding="utf-8"))
            rows = waiver.get("waivers", [])
            if (
                len(rows) != 1
                or rows[0].get("gate") != "packaging_gate"
                or rows[0].get("findings") != ["title is not a phase label"]
                or "BLOCK: 1 of 8" not in packaging_output
            ):
                raise RuntimeError(f"E{episode}: exact-title waiver does not cover the sole failure")
            packaging_status = "WAIVED exact operator-approved technical title"

        print(
            f"E{episode}: PASS — mirror, receipts, arc, strict terms, style, "
            f"AI-writing, teaching register; packaging {packaging_status}"
        )

    run("narrator inheritance", ["tools/verify_series_voice_inheritance.py"])
    print("series script candidates: PASS 4/4; exact-script approval bound 4/4")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
