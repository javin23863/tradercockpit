#!/usr/bin/env python3
"""Prepare the approved E1-E4 evidence visuals for the academic HyperFrames cut."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "OpenMontage" / "projects"
SHARED = PROJECTS / "_series-v4-shared" / "review-board"
VISUALS = ROOT / "productions" / "_series" / "visual-rebuild-previews"
VISUAL_RECEIPT = VISUALS / "receipt.json"
PACKAGE_SOURCE = Path(r"C:\tmp\linux-series-package-review-e1-e4-v4.html")
PACKAGE_BOARD = SHARED / "package-review-e1-e4-v4.html"
PACKAGE_APPROVAL = SHARED / "package-approval-e1-e4-v4.json"
SCRIPT_APPROVAL = SHARED / "script-approval-v6.json"
VOICE_APPROVAL = SHARED / "voice-route-approval-e1-e5-v7.json"

PROJECT_IDS = {
    "01": "series-v4-e01-backtest-search",
    "02": "series-v4-e02-spy-held-out",
    "03": "series-v4-e03-timing-session",
    "04": "series-v4-e04-futures-cost",
}

VISUAL_MAP = {
    "01": [
        "ep01-backtest-vs-strategy.svg",
        "ep01-golden-arithmetic.svg",
        "ep01-backtest-vs-strategy.svg",
        "ep02-selected-maximum.svg",
        "ep02-selected-maximum.svg",
        "ep01-holdout-boundary.svg",
        "ep03-cost-anatomy.svg",
        "ep01-holdout-boundary.svg",
        "ep01-backtest-vs-strategy.svg",
        "ep01-golden-arithmetic.svg",
    ],
    "02": [
        "ep02-ordered-holdout.svg",
        "ep02-oos-field-distribution.svg",
        "ep01-backtest-vs-strategy.svg",
        "ep02-ordered-holdout.svg",
        "ep02-oos-field-distribution.svg",
        "ep02-sample-uncertainty.svg",
        "ep02-selected-maximum.svg",
        "ep02-concentration-stress.svg",
        "ep02-walk-forward.svg",
        "ep02-ordered-holdout.svg",
    ],
    "03": [
        "ep03-field-transitions.svg",
        "ep03-field-transitions.svg",
        "ep03-field-transitions.svg",
        "ep03-fixed-ledger-formula.svg",
        "ep02-oos-field-distribution.svg",
        "ep01-profit-factor-near-misses.svg",
        "ep03-field-transitions.svg",
        "ep03-response-curves.svg",
        "ep03-fixed-ledger-formula.svg",
        "ep03-response-curves.svg",
        "ep03-field-transitions.svg",
    ],
    "04": [
        "ep03-cost-anatomy.svg",
        "ep03-field-transitions.svg",
        "ep03-cost-anatomy.svg",
        "ep03-fixed-ledger-formula.svg",
        "ep03-cost-drivers.svg",
        "ep03-response-curves.svg",
        "ep03-response-curves.svg",
        "ep03-cost-drivers.svg",
        "ep03-order-type-tradeoff.svg",
        "ep03-fixed-ledger-formula.svg",
        "ep03-field-transitions.svg",
    ],
}

PACKAGE_JSON = {
    "name": "tradercockpit-series-v4",
    "private": True,
    "type": "module",
    "scripts": {
        "dev": "npx --yes hyperframes@0.7.76 preview",
        "check": "npx --yes hyperframes@0.7.76 check",
        "render": "npx --yes hyperframes@0.7.76 render",
    },
}

HYPERFRAMES_JSON = {
    "$schema": "https://hyperframes.heygen.com/schema/hyperframes.json",
    "registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/main/registry",
    "paths": {
        "blocks": "compositions",
        "components": "compositions/components",
        "assets": "assets",
    },
    "media": {"autoProxy": True},
}

LEGACY_TOOLS = PROJECTS / "series-04-mc-param" / "tools"
GATE_TOOL_NAMES = (
    "slop_gate.py",
    "lexicon_gate.py",
    "presentation_gate.py",
    "intro_pace.py",
    "voice_consistency.py",
)

CHECK_FIGURES_WRAPPER = r'''#!/usr/bin/env python3
"""Run the exact-script/claim verifier used by the approved E1-E4 batch."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
raise SystemExit(subprocess.run(
    [sys.executable, str(ROOT / "tools" / "verify_series_script_candidates.py")],
    cwd=ROOT,
).returncode)
'''

BROLL_CONFLICTS_WRAPPER = r'''#!/usr/bin/env python3
"""Fail closed on B-roll conflicts for a declared graphics-only composition."""
from pathlib import Path
import json

PROJECT = Path(__file__).resolve().parent.parent
index = (PROJECT / "hyperframes" / "index.html").read_text(encoding="utf-8")
edit = json.loads((PROJECT / "artifacts" / "edit_decisions.json").read_text(encoding="utf-8"))
if 'id="broll-' in index:
    raise SystemExit("BLOCK: B-roll exists but this graphics-only gate cannot score its conflicts")
if any("broll" in str(value).lower() for value in edit["metadata"]["visual_routes"]):
    raise SystemExit("BLOCK: edit declares B-roll but index has no scoreable B-roll clips")
print("PASS: graphics-only edit declares and contains no B-roll, so blind B-roll conflicts are impossible")
'''

NO_MUSIC_WRAPPER = r'''#!/usr/bin/env python3
"""Verify the approved no-music decision instead of pretending a bed exists."""
from pathlib import Path
import json
import re

PROJECT = Path(__file__).resolve().parent.parent
edit = json.loads((PROJECT / "artifacts" / "edit_decisions.json").read_text(encoding="utf-8"))
index = (PROJECT / "hyperframes" / "index.html").read_text(encoding="utf-8")
if edit["metadata"].get("music") != "none":
    raise SystemExit("BLOCK: music decision is not explicitly 'none'")
music_audio = [
    tag for tag in re.findall(r"<audio\b[^>]*>", index, flags=re.I)
    if "narration-" not in tag
]
if music_audio:
    raise SystemExit(f"BLOCK: no-music edit contains {len(music_audio)} non-narration audio clip(s)")
print("PASS: music is explicitly none and the composition contains narration only")
'''


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def record_package_approval() -> str:
    if not PACKAGE_SOURCE.is_file():
        raise RuntimeError(f"missing approved package board: {PACKAGE_SOURCE}")
    PACKAGE_BOARD.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(PACKAGE_SOURCE, PACKAGE_BOARD)
    board_sha = sha256(PACKAGE_BOARD)
    if not PACKAGE_APPROVAL.exists():
        atomic_json(
            PACKAGE_APPROVAL,
            {
                "schema": "tradercockpit-series-package-approval/v1",
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "source_thread_id": "019fb10f-e09f-7b23-8998-d5d2b2e90a3f",
                "operator_response_verbatim": "Approved. Continue.",
                "scope": {
                    "episodes": [1, 2, 3, 4],
                    "locks": [
                        "titles",
                        "plain-English promises",
                        "thumbnail directions",
                        "E1-to-E5 teaching order",
                    ],
                },
                "review_board": {
                    "path": str(PACKAGE_BOARD.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": board_sha,
                },
                "boundaries": [
                    "The later exact-script approval binds the spoken words.",
                    "The later Higgsfield route approval binds narration.",
                    "No upload or publication is approved.",
                ],
            },
        )
    approval = json.loads(PACKAGE_APPROVAL.read_text(encoding="utf-8"))
    if approval["review_board"]["sha256"] != board_sha:
        raise RuntimeError("package approval no longer matches its review board")
    return sha256(PACKAGE_APPROVAL)


def provenance_classes(receipt: dict) -> dict[str, str]:
    return {
        name: label
        for label, names in receipt["labels"].items()
        for name in names
    }


def prepare_episode(
    episode: str,
    project_id: str,
    receipt: dict,
    classes: dict[str, str],
    package_approval_sha: str,
) -> None:
    project = PROJECTS / project_id
    artifacts = project / "artifacts"
    script = json.loads((artifacts / "script.json").read_text(encoding="utf-8"))
    manifest = json.loads((artifacts / "asset_manifest.json").read_text(encoding="utf-8"))
    sections = script["sections"]
    names = VISUAL_MAP[episode]
    if len(sections) != len(names):
        raise RuntimeError(f"{project_id}: visual map does not match script sections")

    narration = [asset for asset in manifest["assets"] if asset["type"] == "narration"]
    narration_by_scene = {asset["scene_id"]: asset for asset in narration}
    section_ids = [section["id"] for section in sections]
    if set(narration_by_scene) != set(section_ids):
        raise RuntimeError(f"{project_id}: narration does not match current script")

    math_dir = project / "hyperframes" / "assets" / "math"
    math_dir.mkdir(parents=True, exist_ok=True)
    visual_assets = []
    scenes = []
    for index, (section, name) in enumerate(zip(sections, names)):
        source = VISUALS / name
        expected = receipt["outputs"][name]
        if sha256(source) != expected:
            raise RuntimeError(f"{name}: visual hash mismatch")
        shutil.copy2(source, math_dir / name)
        cue = section.get("enhancement_cues", [{}])[0].get(
            "description", f"Explain {section['label']} with deterministic evidence."
        )
        relative_source = os.path.relpath(source, project).replace("\\", "/")
        visual_assets.append(
            {
                "id": f"visual-{section['id']}",
                "type": "diagram",
                "path": relative_source,
                "source_tool": "TraderCockpit deterministic math renderer",
                "scene_id": section["id"],
                "cost_usd": 0,
                "resolution": "1920x1080",
                "format": "svg",
                "subtype": "animated_math",
                "generation_summary": (
                    f"Approved deterministic source {name}; sha256={expected}; "
                    f"class={classes[name]}."
                ),
                "provider": "TraderCockpit",
                "license": "TraderCockpit-owned",
            }
        )
        scenes.append(
            {
                "id": section["id"],
                "type": "animation",
                "description": cue,
                "start_seconds": section["start_seconds"],
                "end_seconds": section["end_seconds"],
                "script_section_id": section["id"],
                "framing": (
                    "Full-frame deterministic evidence with separate headline and "
                    "plot regions."
                ),
                "movement": (
                    "Reveal axes, marks, and comparisons only when narration names them."
                ),
                "transition_in": "Evidence marks reveal from black.",
                "transition_out": "Hard cut after the relationship resolves.",
                "overlay_notes": (
                    "Red means measured failure, green means measured pass, and amber "
                    "means caution or proximity. Headlines never cover plots or test cells."
                ),
                "shot_language": {
                    "shot_size": "wide" if index == 0 else "insert",
                    "camera_movement": "static",
                    "lens_mm": 35,
                    "lighting_key": "low_key",
                    "depth_of_field": "deep",
                    "color_temperature": "neutral",
                },
                "shot_intent": cue,
                "narrative_role": (
                    "introduce_subject"
                    if index == 0
                    else "resolution"
                    if index == len(sections) - 1
                    else "deliver_payload"
                ),
                "information_role": cue,
                "hero_moment": index in {0, 1, len(sections) - 1},
                "texture_keywords": ["instrument", "vector", "deterministic"],
                "required_assets": [
                    {
                        "type": "animated_math",
                        "description": (
                            f"{relative_source} sha256={expected}; "
                            f"provenance={classes[name]}."
                        ),
                        "source": "source",
                    }
                ],
            }
        )

    manifest["assets"] = narration + visual_assets
    manifest["total_cost_usd"] = 0
    manifest["metadata"]["status"] = "assets_ready_for_compose"
    manifest["metadata"]["visual_receipt"] = {
        "path": str(VISUAL_RECEIPT.relative_to(ROOT)).replace("\\", "/"),
        "sha256": sha256(VISUAL_RECEIPT),
    }
    manifest["metadata"]["package_approval"] = {
        "path": str(PACKAGE_APPROVAL.relative_to(ROOT)).replace("\\", "/"),
        "sha256": package_approval_sha,
    }
    atomic_json(artifacts / "asset_manifest.json", manifest)

    scene_plan = {
        "version": "1.0",
        "style_playbook": "TraderCockpit Academic Instrument",
        "scenes": scenes,
        "metadata": {
            "status": "approved_for_candidate_compose",
            "exact_script_approval": {
                "path": str(SCRIPT_APPROVAL.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(SCRIPT_APPROVAL),
            },
            "package_approval": {
                "path": str(PACKAGE_APPROVAL.relative_to(ROOT)).replace("\\", "/"),
                "sha256": package_approval_sha,
            },
            "voice_route_approval": {
                "path": str(VOICE_APPROVAL.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(VOICE_APPROVAL),
            },
        },
    }
    atomic_json(artifacts / "scene_plan.json", scene_plan)

    hyperframes = project / "hyperframes"
    atomic_json(hyperframes / "package.json", PACKAGE_JSON)
    atomic_json(hyperframes / "hyperframes.json", HYPERFRAMES_JSON)
    atomic_json(
        hyperframes / "meta.json",
        {
            "id": project_id,
            "name": project_id,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        },
    )

    tools_dir = project / "tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    for name in GATE_TOOL_NAMES:
        source = LEGACY_TOOLS / name
        target = tools_dir / name
        text = source.read_text(encoding="utf-8")
        if name == "voice_consistency.py":
            text = text.replace(
                'default=ROOT / "hyperframes" / "assets" / "audio" / "v1"',
                'default=ROOT / "hyperframes" / "assets" / "audio" / "qwen-john"',
            )
        target.write_text(text, encoding="utf-8")
    (tools_dir / "check_figures.py").write_text(
        CHECK_FIGURES_WRAPPER, encoding="utf-8"
    )
    (tools_dir / "broll_conflicts.py").write_text(
        BROLL_CONFLICTS_WRAPPER, encoding="utf-8"
    )
    (tools_dir / "check_bed.py").write_text(NO_MUSIC_WRAPPER, encoding="utf-8")

    decision_path = artifacts / "decision_log.json"
    decisions = json.loads(decision_path.read_text(encoding="utf-8"))
    decision_id = f"e{episode}-v4-d006"
    if not any(row["decision_id"] == decision_id for row in decisions["decisions"]):
        decisions["decisions"].append(
            {
                "decision_id": decision_id,
                "stage": "assets",
                "category": "visual_system",
                "subject": "Teaching-series evidence visuals",
                "options_considered": [
                    {
                        "option_id": "approved-deterministic-evidence-visuals",
                        "label": "Approved deterministic evidence visuals",
                        "score": 1.0,
                        "reason": (
                            "Reuses reviewed, hash-bound charts and method diagrams "
                            "with red/green/amber semantics."
                        ),
                    },
                    {
                        "option_id": "new-hosted-generation",
                        "label": "New hosted generated visuals",
                        "score": 0.0,
                        "reason": "Could add atmosphere.",
                        "rejected_because": (
                            "Factual charts and equations must remain deterministic."
                        ),
                    },
                ],
                "selected": "approved-deterministic-evidence-visuals",
                "reason": "The operator approved the corrected E1-E4 package direction.",
                "user_visible": True,
                "user_approved": True,
                "confidence": 1.0,
                "approval_receipt": str(PACKAGE_APPROVAL.relative_to(ROOT)).replace(
                    "\\", "/"
                ),
                "approval_receipt_sha256": package_approval_sha,
            }
        )
        atomic_json(decision_path, decisions)

    sys.path.insert(0, str(ROOT / "OpenMontage"))
    from lib.checkpoint import write_checkpoint

    for stage, artifact_name, artifact in (
        ("scene_plan", "scene_plan", scene_plan),
        ("assets", "asset_manifest", manifest),
    ):
        write_checkpoint(
            PROJECTS,
            project_id,
            stage,
            "completed",
            {artifact_name: artifact},
            pipeline_type="hybrid",
            human_approval_required=True,
            human_approved=True,
            metadata={
                "operator_approval": {
                    "path": str(PACKAGE_APPROVAL.relative_to(ROOT)).replace("\\", "/"),
                    "sha256": package_approval_sha,
                }
            },
        )


def check(selected: set[str] | None = None) -> None:
    approval = json.loads(PACKAGE_APPROVAL.read_text(encoding="utf-8"))
    if approval["review_board"]["sha256"] != sha256(PACKAGE_BOARD):
        raise RuntimeError("package approval board mismatch")
    receipt = json.loads(VISUAL_RECEIPT.read_text(encoding="utf-8"))
    for episode, project_id in PROJECT_IDS.items():
        if selected is not None and episode not in selected:
            continue
        project = PROJECTS / project_id
        script = json.loads(
            (project / "artifacts" / "script.json").read_text(encoding="utf-8")
        )
        manifest = json.loads(
            (project / "artifacts" / "asset_manifest.json").read_text(encoding="utf-8")
        )
        scene_plan = json.loads(
            (project / "artifacts" / "scene_plan.json").read_text(encoding="utf-8")
        )
        ids = {section["id"] for section in script["sections"]}
        if ids != {scene["id"] for scene in scene_plan["scenes"]}:
            raise RuntimeError(f"{project_id}: scene plan mismatch")
        by_type = {
            kind: {asset["scene_id"] for asset in manifest["assets"] if asset["type"] == kind}
            for kind in ("narration", "diagram")
        }
        if ids != by_type["narration"] or ids != by_type["diagram"]:
            raise RuntimeError(f"{project_id}: asset manifest mismatch")
        for name in set(VISUAL_MAP[episode]):
            target = project / "hyperframes" / "assets" / "math" / name
            if sha256(target) != receipt["outputs"][name]:
                raise RuntimeError(f"{project_id}: installed {name} mismatch")
        for stage in ("scene_plan", "assets"):
            checkpoint = json.loads(
                (project / f"checkpoint_{stage}.json").read_text(encoding="utf-8")
            )
            if checkpoint["status"] != "completed" or not checkpoint["human_approved"]:
                raise RuntimeError(f"{project_id}: {stage} checkpoint not approved")
        for name in (
            *GATE_TOOL_NAMES,
            "check_figures.py",
            "broll_conflicts.py",
            "check_bed.py",
        ):
            if not (project / "tools" / name).is_file():
                raise RuntimeError(f"{project_id}: missing gate tool {name}")
    count = len(selected or PROJECT_IDS)
    print(f"series-v4 composition preparation: PASS {count}/{count}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--episode", action="append", choices=sorted(PROJECT_IDS))
    args = parser.parse_args()
    selected = set(args.episode or PROJECT_IDS)
    if args.check:
        check(selected)
        return 0
    package_approval_sha = record_package_approval()
    receipt = json.loads(VISUAL_RECEIPT.read_text(encoding="utf-8"))
    classes = provenance_classes(receipt)
    for episode, project_id in PROJECT_IDS.items():
        if episode not in selected:
            continue
        prepare_episode(episode, project_id, receipt, classes, package_approval_sha)
    check(selected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
