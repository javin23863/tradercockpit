#!/usr/bin/env python3
"""Block Into the Laboratory renders that bypass the approved script and gate chain."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
PROJECTS = ROOT / "OpenMontage" / "projects"
PREFLIGHT_NAME = "series-render-preflight.json"
SERIES_MARKERS = re.compile(
    r"into[- _]the[- _]laboratory|series-v4-e0[1-5]|series-0[1-5]-|"
    r"episode-0[1-5](?:\D|$)|productions[/\\]_series[/\\]masters",
    re.IGNORECASE,
)
CANONICAL_RENDER = re.compile(
    r"\b(?:npm|npx|pnpm|yarn)\b[^\r\n]*\brender\b|"
    r"\b(?:hyperframes|remotion)\b[^\r\n]*\brender\b",
    re.IGNORECASE,
)
PILOT_COMPOSITION = re.compile(
    r"(?:^|\s)(?:-c|--composition(?:=|\s+))\s*[\"']?pilot(?:[/\\]index\.html)?(?:[\"']|\s|$)",
    re.IGNORECASE,
)
PILOT_OUTPUT = re.compile(
    r"(?:^|\s)(?:-o|--output(?:=|\s+))\s*[\"']?[^\r\n\"']*(?:pilot|proof|review)[^\r\n\"']*\.mp4(?:[\"']|\s|$)",
    re.IGNORECASE,
)
FFMPEG = re.compile(r"\bffmpeg(?:\.exe)?\b", re.IGNORECASE)
VIDEO = re.compile(r"\.(?:mp4|mov|mkv|webm)\b", re.IGNORECASE)
MEDIA = re.compile(
    r"[^\s\"']+\.(?:mp4|mov|mkv|webm|wav|mp3|aac|flac|png|jpe?g|gif)\b",
    re.IGNORECASE,
)
REVIEW_OUTPUT = re.compile(r"(?:review|proof|preview|contact|frame|thumb)", re.IGNORECASE)
SERIES_CONTEXT = (
    "INTO THE LABORATORY HOOK ACTIVE. For any teaching-series work, use the installed "
    "series-script skill before substantive action, then reconcile the live artifacts with "
    "the three existing vault authorities named in AGENTS.md. The graph is discovery only. "
    "Do not hand-splice or re-mux a candidate/master. Before the canonical HyperFrames render, "
    "run `py .codex/hooks/series_guard.py preflight <episode-project>`. Automated GREEN is "
    "technical evidence only; show the operator a short playable semantic proof before a master."
)


class Blocked(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    if not path.is_file():
        raise Blocked(f"missing {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Blocked(f"unreadable {path}: {exc}") from exc


def inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def resolve_project(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    if not inside(path, PROJECTS) or not (path / "artifacts" / "packaging.json").is_file():
        raise Blocked(f"{path} is not an episode project under {PROJECTS}")
    return path


def slot_texts(vo: Path) -> dict[str, str]:
    slots: dict[str, list[str]] = {}
    current: str | None = None
    for raw in vo.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^=== SLOT (scene-\d+) ", raw)
        if match:
            current = match.group(1)
            slots[current] = []
        elif current and raw.strip() and not raw.lstrip().startswith("#"):
            slots[current].append(raw.strip())
    return {scene: " ".join(lines) for scene, lines in slots.items()}


def binding(project: Path) -> dict:
    """Bind exact approved script text to every audio file the composition loads."""
    project = resolve_project(project)
    artifacts = project / "artifacts"
    packaging_path = artifacts / "packaging.json"
    script_path = artifacts / "script.json"
    vo_path = artifacts / "vo.txt"
    index_path = project / "hyperframes" / "index.html"
    packaging = load_json(packaging_path)
    script = load_json(script_path)

    approval_path = ROOT / packaging.get("approval", {}).get("exact_script_approval", "")
    approval = load_json(approval_path)
    if sha256(approval_path) != packaging["approval"].get("exact_script_approval_sha256"):
        raise Blocked("exact-script approval receipt hash is stale")
    episode = f"{int(packaging['episode']):02d}"
    approved = {row["episode"]: row for row in approval["approved_exact_hashes"]}.get(episode)
    if not approved:
        raise Blocked(f"script approval has no Episode {episode} row")
    script_hash, vo_hash = sha256(script_path), sha256(vo_path)
    if script_hash != approved["script_sha256"] or vo_hash != approved["vo_sha256"]:
        raise Blocked("current script or VO does not match the operator-approved exact hash")
    if packaging.get("script", {}).get("sha256") != script_hash:
        raise Blocked("packaging script hash is stale")
    if packaging.get("script", {}).get("vo_sha256") != vo_hash:
        raise Blocked("packaging VO hash is stale")

    spoken = slot_texts(vo_path)
    sections = {row["id"]: row for row in script["sections"]}
    if spoken.keys() != sections.keys():
        raise Blocked("script.json and vo.txt scene IDs differ")
    for scene_id, text in spoken.items():
        section = sections[scene_id]
        if section.get("text") != text or section.get("delivery_cues", {}).get("provider_text") != text:
            raise Blocked(f"{scene_id} script, VO, and provider text differ")

    narration_path = ROOT / packaging.get("approval", {}).get("narrator_receipt", "")
    narration = load_json(narration_path)
    if sha256(narration_path) != packaging["approval"].get("narrator_receipt_sha256"):
        raise Blocked("narrator receipt hash is stale")
    if narration.get("status") != "completed":
        raise Blocked("narrator receipt is not completed")
    entries = [row for row in narration.get("entries", []) if row.get("project_id") == project.name]
    by_scene = {row["scene_id"]: row for row in entries}
    if len(entries) != len(by_scene) or by_scene.keys() != sections.keys():
        raise Blocked("narrator receipt does not cover every current scene exactly once")

    files = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in (packaging_path, script_path, vo_path, approval_path, narration_path, index_path)
    }
    expected_sources = []
    for scene_id, section in sections.items():
        entry = by_scene[scene_id]
        provider_text = section["delivery_cues"]["provider_text"]
        provider_hash = hashlib.sha256(provider_text.encode("utf-8")).hexdigest()
        if entry.get("script_sha256") != script_hash or entry.get("provider_text_sha256") != provider_hash:
            raise Blocked(f"{scene_id} narration was generated from a different script")
        clean = (ROOT / entry["clean_path"]).resolve()
        if not inside(clean, project) or sha256(clean) != entry.get("clean_sha256"):
            raise Blocked(f"{scene_id} canonical narration bytes do not match the provider receipt")
        loaded = project / "hyperframes" / "assets" / "audio" / "qwen-john" / f"{scene_id}.wav"
        if not loaded.is_file() or sha256(loaded) != entry.get("clean_sha256"):
            raise Blocked(f"{scene_id} composition audio is stale or substituted")
        for path in (clean, loaded):
            files[str(path.relative_to(ROOT)).replace("\\", "/")] = sha256(path)
        expected_sources.append(f"assets/audio/qwen-john/{scene_id}.wav")

    index = index_path.read_text(encoding="utf-8")
    sources = re.findall(r"<audio\b[^>]*\bsrc=[\"']([^\"']+)[\"']", index, flags=re.IGNORECASE)
    if sources != expected_sources:
        raise Blocked("composition audio tags do not match the approved scene order and files")

    canonical = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {"sha256": hashlib.sha256(canonical).hexdigest(), "files": files}


def run_preflight(project: Path) -> Path:
    project = resolve_project(project)
    bound = binding(project)
    sys.path.insert(0, str(ROOT))
    from tools import episode_gate

    artifacts = project / "artifacts"
    meta = episode_gate.episode_meta(artifacts)
    waivers = episode_gate.load_waivers(artifacts)
    substitutions = {
        "art": str(artifacts),
        "proj": str(project),
        "master": "",
        **meta,
    }
    results, blocked = {}, []
    for name, where, argv, needs_master in episode_gate.CHAIN:
        if needs_master:
            continue
        result = episode_gate.run_gate(name, where, argv, project, substitutions)
        if result["verdict"] == "BLOCK" and name in waivers and episode_gate.covered(result, waivers[name]):
            result["verdict"] = "WAIVED"
            result["waiver"] = waivers[name]
        elif result["verdict"] == "BLOCK":
            blocked.append(name)
        results[name] = result
        print(f"{result['verdict']:>7} {name}")
    if blocked:
        raise Blocked(f"source gate chain blocked: {', '.join(blocked)}")

    source = episode_gate.source_fingerprint(project)
    receipt = {
        "schema": "tradercockpit-series-render-preflight/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "verdict": "PASS",
        "project": str(project),
        "binding_sha256": bound["sha256"],
        "source_tree_sha256": source["sha256"],
        "source_file_count": source["file_count"],
        "gates": results,
        "render_boundary": "canonical HyperFrames render only; direct FFmpeg master assembly blocked",
    }
    output = artifacts / "build" / PREFLIGHT_NAME
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: script -> narration -> composition bound; source gates passed -> {output}")
    return output


def verify_preflight(project: Path) -> None:
    project = resolve_project(project)
    receipt_path = project / "artifacts" / "build" / PREFLIGHT_NAME
    receipt = load_json(receipt_path)
    if receipt.get("verdict") != "PASS" or receipt.get("project") != str(project):
        raise Blocked("render preflight receipt is not a PASS for this project")
    if receipt.get("binding_sha256") != binding(project)["sha256"]:
        raise Blocked("script or narration changed after render preflight")
    sys.path.insert(0, str(ROOT))
    from tools import episode_gate

    source = episode_gate.source_fingerprint(project)
    if receipt.get("source_tree_sha256") != source["sha256"]:
        raise Blocked("composition or render asset changed after render preflight")


def verify_pilot_render(project: Path, command: str) -> None:
    """Allow only the operator-approved four-shot proof before the full asset gate."""
    project = resolve_project(project)
    if not PILOT_COMPOSITION.search(command) or not PILOT_OUTPUT.search(command):
        raise Blocked("pilot render must target pilot/index.html and a pilot/proof/review MP4")

    artifacts = project / "artifacts"
    approval = load_json(artifacts / "scene-plan-approval-v52.json")
    if (
        approval.get("status") != "approved"
        or approval.get("operator_response_verbatim") != "approve"
        or "four-shot representative pilot s03-02 through s03-05 only" not in approval.get("scope", "")
    ):
        raise Blocked("four-shot pilot approval receipt is absent or out of scope")

    expected = approval.get("approved_exact_hashes", {})
    bound = {
        "script_sha256": artifacts / "script.json",
        "scene_plan_sha256": artifacts / "scene_plan.json",
        "shot_list_sha256": artifacts / "shot-list-v52.md",
        "art_direction_sha256": artifacts / "art-direction-v52.md",
    }
    for key, path in bound.items():
        if expected.get(key) != sha256(path):
            raise Blocked(f"pilot approval no longer matches {path.name}")

    checkpoint = load_json(project / "checkpoint_assets.json")
    metadata = checkpoint.get("metadata", {})
    if (
        checkpoint.get("stage") != "assets"
        or checkpoint.get("status") != "in_progress"
        or metadata.get("scope") != "representative-pilot-only"
        or metadata.get("pilot_shot_ids") != ["s03-02", "s03-03", "s03-04", "s03-05"]
        or metadata.get("pilot_render_authorized") is not True
        or metadata.get("full_batch_authorized") is not False
        or metadata.get("render_authorized") is not False
    ):
        raise Blocked("assets checkpoint does not authorize only the representative pilot")


def project_from_command(command: str, workdir: Path) -> Path:
    for candidate in (workdir, *workdir.parents):
        if inside(candidate, PROJECTS) and (candidate / "artifacts" / "packaging.json").is_file():
            return candidate
    lowered = command.lower().replace("\\", "/")
    matches = [path for path in PROJECTS.iterdir() if path.is_dir() and path.name.lower() in lowered]
    if len(matches) != 1:
        raise Blocked("series render project is ambiguous; run from the episode project")
    return matches[0]


def series_command(command: str, workdir: Path) -> bool:
    normalized = f"{workdir} {command}".replace("\\", "/")
    return bool(SERIES_MARKERS.search(normalized)) or any(
        part.lower().startswith("series-") for part in workdir.parts
    )


def deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"BLOCKED — Into the Laboratory render guard: {reason}",
        }
    }


def pretool_decision(
    payload: dict,
    verifier: Callable[[Path], None] = verify_preflight,
    pilot_verifier: Callable[[Path, str], None] = verify_pilot_render,
) -> dict | None:
    if payload.get("tool_name") != "Bash":
        return None
    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    workdir = Path(tool_input.get("workdir") or payload.get("cwd") or ROOT).resolve()
    if not series_command(command, workdir):
        return None

    if CANONICAL_RENDER.search(command):
        try:
            project = project_from_command(command, workdir)
            if PILOT_COMPOSITION.search(command) or PILOT_OUTPUT.search(command):
                pilot_verifier(project, command)
            else:
                verifier(project)
        except Blocked as exc:
            return deny(f"{exc}. Run `py .codex/hooks/series_guard.py preflight <episode-project>`. ")
        return None

    media_paths = MEDIA.findall(command)
    if FFMPEG.search(command) and media_paths and VIDEO.search(media_paths[-1]):
        last = media_paths[-1]
        is_bounded_review = bool(REVIEW_OUTPUT.search(last)) and bool(
            re.search(r"(?:^|\s)-(?:t|frames:v)\s", command, re.IGNORECASE)
        )
        if is_bounded_review:
            return None
        return deny(
            "direct FFmpeg series assembly/re-mux is forbidden because it can reuse stale audio. "
            "Repair the composition source and use its canonical render command"
        )

    if (
        media_paths
        and VIDEO.search(media_paths[-1])
        and re.search(r"candidate|master|produced", command, re.IGNORECASE)
    ):
        return deny("candidate/master video creation must use the canonical composition render")
    return None


def hook(payload: dict) -> dict | None:
    event = payload.get("hook_event_name")
    if event == "PreToolUse":
        return pretool_decision(payload)
    if event == "UserPromptSubmit":
        if SERIES_MARKERS.search(str(payload.get("prompt") or "")):
            return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": SERIES_CONTEXT}}
        return None
    if event in {"SessionStart", "SubagentStart"}:
        return {"hookSpecificOutput": {"hookEventName": event, "additionalContext": SERIES_CONTEXT}}
    return None


def demo() -> int:
    stale = {
        "tool_name": "Bash",
        "cwd": str(ROOT),
        "tool_input": {
            "command": (
                'ffmpeg.exe -y -f concat -i C:\\tmp\\ep01-v48-concat.txt -c copy '
                'Into-the-Laboratory-Episode-01-v49-produced.mp4'
            )
        },
    }
    review = {
        "tool_name": "Bash",
        "cwd": str(ROOT),
        "tool_input": {
            "command": (
                'ffmpeg.exe -y -i episode-01-master.mp4 -t 22 -c copy '
                'ep01-splice-review.mp4'
            )
        },
    }
    assert pretool_decision(stale) is not None
    assert pretool_decision(review) is None
    print("series guard demo: PASS — stale-audio v49 concat denied; bounded review extract allowed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("hook", "preflight", "verify", "binding", "demo"))
    parser.add_argument("project", nargs="?", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "hook":
            try:
                payload = json.load(sys.stdin)
            except Exception:
                return 0
            result = hook(payload)
            if result:
                print(json.dumps(result))
            return 0
        if args.mode == "demo":
            return demo()
        if args.project is None:
            parser.error(f"{args.mode} requires an episode project")
        if args.mode == "preflight":
            run_preflight(args.project)
        elif args.mode == "verify":
            verify_preflight(args.project)
            print("series render preflight: PASS and current")
        else:
            result = binding(args.project)
            print(f"series script/audio binding: PASS — {result['sha256']}")
        return 0
    except Blocked as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
