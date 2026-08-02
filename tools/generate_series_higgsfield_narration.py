#!/usr/bin/env python
"""Generate and clean approved Higgsfield narration for Into the Laboratory."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPENMONTAGE = ROOT / "OpenMontage"
PROJECTS = OPENMONTAGE / "projects"
RECEIPT = (
    ROOT
    / "productions"
    / "_series"
    / "higgsfield-qwen-john-narration-v5-receipt.json"
)
V4_RECEIPT = ROOT / "productions/_series/higgsfield-qwen-john-narration-v4-receipt.json"
LEGACY_RECEIPT = ROOT / "productions/_series/higgsfield-qwen-john-narration-receipt.json"
ROUTE_APPROVAL = (
    PROJECTS / "_series-v4-shared/review-board/voice-route-approval-e1-e5-v7.json"
)
SCRIPT_APPROVAL = (
    PROJECTS / "_series-v4-shared/review-board/script-approval-v6.json"
)
PROJECT_IDS = {
    "01": "series-v4-e01-backtest-search",
    "02": "series-v4-e02-spy-held-out",
    "03": "series-v4-e03-timing-session",
    "04": "series-v4-e04-futures-cost",
    "05": "series-04-mc-param",
}
VOICE_ID = "6b528d43-c056-4a2f-9d82-1591a7ba13b0"
SAMPLE_SHA256 = "6d4fa9e01a2183a973829c166f6c0119a7030b28bf9275a0a2e59aa5aca1dfe7"
ACOUSTIC_REPAIR_INSTRUCTIONS = {
    ("03", "scene-05"): (
        "Calm John clean delivery near 150 words per minute. Read exactly; preserve "
        "every word, number, and limitation."
    ),
    ("04", "scene-01"): (
        "Calm John clean delivery near 155 words per minute. Read exactly; preserve "
        "every word, number, and limitation."
    ),
    ("04", "scene-05"): (
        "Calm John clean delivery in a steady lower register near 155 words per minute. "
        "Read exactly; preserve every number."
    ),
    ("04", "scene-11"): (
        "Calm John clean delivery in a steady lower register near 155 words per minute. "
        "Read exactly; preserve every number."
    ),
}
SAMPLE_PATH = (
    "../series-04-mc-param/artifacts/voice-auditions/"
    "ep04-qwen-john-clean.wav"
)
MODEL = "Qwen Audio 3.0 TTS Flash"
JOB_TYPE = "qwen_audio_tts"
ESTIMATED_CREDITS_PER_SECTION = 0.09

MARCUS_PROJECT_ID = "series-01-backtest-is-not-a-strategy"
MARCUS_PROJECT = PROJECTS / MARCUS_PROJECT_ID
MARCUS_VOICE_ID = "6f98d3dd-324f-4845-8c28-c1d1647a06cd"
MARCUS_INSTRUCTION = (
    "Calm American male educator. Keep one natural steady pace from first word "
    "to last. No slow ending. Read exactly. No hype."
)
MARCUS_SAMPLE_RECEIPT = (
    ROOT
    / "productions/_series/"
    "quant-atlas-marcus-historical-provider-native-sample-receipt.json"
)
MARCUS_PROOF_APPROVAL = (
    ROOT
    / "productions/_series/"
    "quant-atlas-marcus-historical-proof-approval-receipt.json"
)
MARCUS_RECEIPT = (
    ROOT
    / "productions/_series/higgsfield-qwen-marcus-episode-01-receipt.json"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def run_json(command: list[str], attempts: int = 2) -> object:
    if command[0] == "higgsfield":
        launcher = shutil.which("higgsfield")
        if not launcher:
            raise RuntimeError("higgsfield is required")
        command = (
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", launcher]
            + command[1:]
            if Path(launcher).suffix.lower() == ".ps1"
            else [launcher] + command[1:]
        )
    for attempt in range(attempts):
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        if attempt + 1 == attempts:
            raise RuntimeError(
                f"{' '.join(command[:4])} failed: {result.stderr.strip()}"
            )
        time.sleep(2)
    raise AssertionError("unreachable")


def account_status() -> dict:
    data = run_json(["higgsfield", "account", "status", "--json"])
    return {
        "plan": data.get("subscription_plan_type"),
        "credits": data.get("credits"),
    }


def require_route_approval() -> str:
    if not ROUTE_APPROVAL.is_file():
        raise RuntimeError(
            "Missing exact E1-E5 Higgsfield route approval; "
            "run tools/record_series_voice_route_approval.py"
        )
    approval = json.loads(ROUTE_APPROVAL.read_text(encoding="utf-8"))
    selection = approval.get("selection", {})
    expected = {
        "provider": "Higgsfield",
        "model": MODEL,
        "job_type": JOB_TYPE,
        "voice_character": "John",
        "treatment": "clean",
        "subscription_credit_use_authorized": True,
        "new_subscription_or_top_up_authorized": False,
    }
    if approval.get("scope") != {"episodes": [1, 2, 3, 4, 5], "episode_5": True}:
        raise RuntimeError("Higgsfield route approval has the wrong episode scope")
    if any(selection.get(key) != value for key, value in expected.items()):
        raise RuntimeError("Higgsfield route approval no longer matches this generator")
    if (
        approval.get("canonical_script_approval", {}).get("sha256")
        != sha256(SCRIPT_APPROVAL)
    ):
        raise RuntimeError("Higgsfield route approval is stale against script approval")
    canonical = []
    for number, project_id in PROJECT_IDS.items():
        artifacts = PROJECTS / project_id / "artifacts"
        canonical.append({
            "episode": int(number),
            "script_path": str((artifacts / "script.json").relative_to(ROOT)).replace("\\", "/"),
            "script_sha256": sha256(artifacts / "script.json"),
            "vo_path": str((artifacts / "vo.txt").relative_to(ROOT)).replace("\\", "/"),
            "vo_sha256": sha256(artifacts / "vo.txt"),
        })
    if approval.get("episode_canonical") != canonical:
        raise RuntimeError("Higgsfield route approval is stale against an E1-E5 script")
    return sha256(ROUTE_APPROVAL)


def narration_instruction(section: dict) -> str:
    directions = section["speaker_directions"]
    if directions.startswith("Cold open"):
        instruction = (
            "Calm, direct cold open. No greeting. Land the claim, then settle. "
            "Read exactly; preserve every word and number. No hype."
        )
    elif directions.startswith("Resolve calmly"):
        instruction = (
            "Calm, useful resolution without triumph or sales cadence. Read exactly; "
            "preserve every word, number, and limitation. No hype."
        )
    else:
        instruction = (
            "Calm, measured educator speaking to one trader. Read exactly; preserve "
            "every word, number, and limitation. No hype or sarcasm."
        )
    assert len(instruction) <= 128
    return instruction


def spoken_provider_text(text: str) -> str:
    """Keep technical labels in the script while making Qwen pronounce them unambiguously."""
    text = re.sub(
        r"\bA 70/30 split\b",
        "A split of seventy percent in-sample and thirty percent out-of-sample",
        text,
        flags=re.IGNORECASE,
    )
    for label, spoken in {
        "p50": "P fifty",
        "p95": "P ninety five",
    }.items():
        text = re.sub(rf"\b{label}\b", spoken, text, flags=re.IGNORECASE)
    return text


def tasks() -> list[dict]:
    planned = []
    for episode, project_id in PROJECT_IDS.items():
        project = PROJECTS / project_id
        script_path = project / "artifacts" / "script.json"
        script = json.loads(script_path.read_text(encoding="utf-8"))
        for index, section in enumerate(script["sections"]):
            canonical_text = section["delivery_cues"]["provider_text"]
            text = spoken_provider_text(canonical_text)
            instruction = ACOUSTIC_REPAIR_INSTRUCTIONS.get(
                (episode, section["id"]), narration_instruction(section)
            )
            assert len(instruction) <= 128
            planned.append({
                "episode": episode,
                "project_id": project_id,
                "project": project,
                "section_index": index,
                "scene_id": section["id"],
                "text": text,
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "canonical_text_sha256": hashlib.sha256(
                    canonical_text.encode()
                ).hexdigest(),
                "pronunciation_expanded": text != canonical_text,
                "script_sha256": sha256(script_path),
                "instruction": instruction,
                "pause_after_seconds": section["delivery_cues"]["pause_after_seconds"],
            })
    return planned


def loudnorm_measure(raw: Path) -> dict:
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(raw),
            "-af", "highpass=f=70,loudnorm=I=-16:LRA=11:TP=-1.5:print_format=json",
            "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)
    for candidate in reversed(re.findall(r"\{.*?\}", result.stderr, re.DOTALL)):
        try:
            data = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if "input_i" in data:
            return data
    raise RuntimeError("FFmpeg did not return loudnorm measurements")


def clean_audio(raw: Path, clean: Path) -> None:
    measure = loudnorm_measure(raw)
    clean.parent.mkdir(parents=True, exist_ok=True)
    filt = (
        "highpass=f=70,"
        "loudnorm=I=-16:LRA=11:TP=-1.5:"
        f"measured_I={measure['input_i']}:"
        f"measured_TP={measure['input_tp']}:"
        f"measured_LRA={measure['input_lra']}:"
        f"measured_thresh={measure['input_thresh']}:"
        f"offset={measure['target_offset']}:linear=true:print_format=summary"
    )
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-hide_banner", "-nostats", "-i", str(raw),
            "-af", filt, "-ar", "48000", "-ac", "1", "-c:a", "pcm_s24le",
            str(clean),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)


def probe(path: Path) -> dict:
    data = run_json([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=codec_name,sample_rate,channels",
        "-of", "json", str(path),
    ])
    stream = data["streams"][0]
    return {
        "duration_seconds": round(float(data["format"]["duration"]), 6),
        "bytes": int(data["format"]["size"]),
        "codec": stream["codec_name"],
        "sample_rate_hz": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
    }


def generate_one(task: dict, job: dict | None = None) -> dict:
    audio_root = (
        task["project"] / "assets" / "audio" / task.get("audio_subdir", "narration")
    )
    voice_id = task.get("voice_id", VOICE_ID)
    raw = audio_root / "raw" / (
        task["scene_id"] + ".wav"
    )
    clean = audio_root / (
        task["scene_id"] + ".wav"
    )
    if job is None:
        job = run_json([
            "higgsfield", "generate", "create", JOB_TYPE,
            "--prompt", task["text"],
            "--instruction", task["instruction"],
            "--voice_type", "preset",
            "--voice_id", voice_id,
            "--format", "wav",
            "--sample_rate", "24000",
            "--language", "en",
            "--seed", "0",
            "--speech_rate", "1",
            "--pitch_rate", "1",
            "--volume", "50",
            "--wait",
            "--json",
        ], attempts=2)[0]
    raw.parent.mkdir(parents=True, exist_ok=True)
    temporary = raw.with_suffix(".wav.tmp")
    urllib.request.urlretrieve(job["result_url"], temporary)
    os.replace(temporary, raw)
    clean_audio(raw, clean)
    media = probe(clean)
    return {
        "episode": task["episode"],
        "project_id": task["project_id"],
        "section_index": task["section_index"],
        "scene_id": task["scene_id"],
        "script_sha256": task["script_sha256"],
        "provider_text_sha256": task["canonical_text_sha256"],
        "render_text_sha256": task["text_sha256"],
        "pronunciation_expanded": task["pronunciation_expanded"],
        "instruction": task["instruction"],
        "voice_id": voice_id,
        "pause_after_seconds": task["pause_after_seconds"],
        "job_id": job["id"],
        "result_url": job["result_url"],
        "raw_path": str(raw.relative_to(ROOT)).replace("\\", "/"),
        "raw_sha256": sha256(raw),
        "clean_path": str(clean.relative_to(ROOT)).replace("\\", "/"),
        "clean_sha256": sha256(clean),
        **media,
        "estimated_credits": ESTIMATED_CREDITS_PER_SECTION,
    }


def marcus_episode_one_tasks() -> tuple[list[dict], dict, dict]:
    """Load the exact approved proof route and the current Episode 1 script."""
    sample = json.loads(MARCUS_SAMPLE_RECEIPT.read_text(encoding="utf-8"))
    approval = json.loads(MARCUS_PROOF_APPROVAL.read_text(encoding="utf-8"))
    proof_receipt = ROOT / approval["approved_proof"]["receipt"]
    proof = json.loads(proof_receipt.read_text(encoding="utf-8"))
    script_path = MARCUS_PROJECT / "artifacts" / "script.json"
    script = json.loads(script_path.read_text(encoding="utf-8"))

    expected = {
        "job_type": JOB_TYPE,
        "model": MODEL,
        "voice": "Marcus",
        "voice_id": MARCUS_VOICE_ID,
        "instruction": MARCUS_INSTRUCTION,
    }
    provider = sample["provider"]
    if any(provider.get(key) != value for key, value in expected.items()):
        raise RuntimeError("Marcus sample receipt no longer matches the approved route")
    if sample["script"]["sha256"] != sha256(script_path):
        raise RuntimeError("Marcus proof approval is stale against the Episode 1 script")
    if approval["approved_proof"]["receipt_sha256"] != sha256(proof_receipt):
        raise RuntimeError("Marcus proof approval receipt hash is stale")
    proof_path = ROOT / approval["approved_proof"]["path"]
    if (
        approval["approved_proof"]["sha256"] != sha256(proof_path)
        or proof["render"]["sha256"] != sha256(proof_path)
    ):
        raise RuntimeError("The approved Marcus proof video has changed")
    sample_master = ROOT / sample["assets"]["mastered"]["path"]
    if sample["assets"]["mastered"]["sha256"] != sha256(sample_master):
        raise RuntimeError("The approved Marcus Scene 01 master has changed")

    planned = []
    for index, section in enumerate(script["sections"]):
        text = section["delivery_cues"]["provider_text"]
        planned.append(
            {
                "episode": "01",
                "project_id": MARCUS_PROJECT_ID,
                "project": MARCUS_PROJECT,
                "section_index": index,
                "scene_id": section["id"],
                "text": text,
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "canonical_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "pronunciation_expanded": False,
                "script_sha256": sha256(script_path),
                "instruction": MARCUS_INSTRUCTION,
                "pause_after_seconds": section["delivery_cues"][
                    "pause_after_seconds"
                ],
                "voice_id": MARCUS_VOICE_ID,
                "audio_subdir": "narration-marcus",
            }
        )
    if len(planned) != 13 or planned[0]["text"] != sample["script"]["text"]:
        raise RuntimeError("Episode 1 no longer matches the approved 13-scene proof scope")
    return planned, sample, approval


def approved_marcus_sample_entry(task: dict, sample: dict) -> dict:
    source = ROOT / sample["assets"]["mastered"]["path"]
    target = task["project"] / "assets/audio/narration-marcus/scene-01.wav"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file() or sha256(target) != sha256(source):
        shutil.copy2(source, target)
    media = probe(target)
    return {
        "episode": "01",
        "project_id": MARCUS_PROJECT_ID,
        "section_index": 0,
        "scene_id": "scene-01",
        "script_sha256": task["script_sha256"],
        "provider_text_sha256": task["canonical_text_sha256"],
        "render_text_sha256": task["text_sha256"],
        "pronunciation_expanded": False,
        "instruction": MARCUS_INSTRUCTION,
        "voice_id": MARCUS_VOICE_ID,
        "pause_after_seconds": task["pause_after_seconds"],
        "job_id": sample["provider"]["job_id"],
        "result_url": sample["provider"]["result_url"],
        "raw_path": sample["assets"]["raw"]["path"],
        "raw_sha256": sample["assets"]["raw"]["sha256"],
        "clean_path": str(target.relative_to(ROOT)).replace("\\", "/"),
        "clean_sha256": sha256(target),
        **media,
        "estimated_credits": 0,
        "reused_approved_sample": True,
    }


def update_marcus_manifest(
    entries: list[dict], account_before: dict, account_after: dict, sample: dict
) -> None:
    path = MARCUS_PROJECT / "artifacts" / "asset_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["assets"] = [
        asset for asset in manifest["assets"] if asset["type"] != "narration"
    ]
    timing = []
    cursor = 0.0
    sample_path = os.path.relpath(
        ROOT / sample["assets"]["mastered"]["path"], MARCUS_PROJECT
    ).replace("\\", "/")
    for entry in sorted(entries, key=lambda item: item["section_index"]):
        head = 0.20 if entry["section_index"] == 0 else 0.15
        narration_start = round(cursor + head, 6)
        narration_end = round(narration_start + entry["duration_seconds"], 6)
        scene_end = round(narration_end + 0.35, 6)
        timing.append(
            {
                "scene_id": entry["scene_id"],
                "start_seconds": narration_start,
                "narration_end_seconds": narration_end,
                "pause_after_seconds": 0.35,
                "end_seconds": scene_end,
            }
        )
        cursor = scene_end
        local_clean = ROOT / entry["clean_path"]
        manifest["assets"].append(
            {
                "id": f"narration-{entry['scene_id']}",
                "type": "narration",
                "path": os.path.relpath(local_clean, MARCUS_PROJECT).replace(
                    "\\", "/"
                ),
                "source_tool": f"Higgsfield {MODEL} plus FFmpeg clean mastering",
                "scene_id": entry["scene_id"],
                "model": MODEL,
                "cost_usd": 0,
                "duration_seconds": entry["duration_seconds"],
                "format": "wav",
                "subtype": "qwen_marcus_provider_native_clean",
                "generation_summary": (
                    f"Higgsfield job {entry['job_id']}; raw sha256="
                    f"{entry['raw_sha256']}; clean sha256={entry['clean_sha256']}; "
                    "70 Hz high-pass and two-pass EBU R128 normalization; no tempo "
                    "or pitch transform."
                ),
                "provider": "Higgsfield",
                "license": "Generated under the operator's existing Max Plan",
                "voice_performance": {
                    "source_section_id": entry["scene_id"],
                    "delivery_cues_applied": True,
                    "provider_text_used": True,
                    "provider_settings": {
                        "job_type": JOB_TYPE,
                        "voice_id": MARCUS_VOICE_ID,
                        "voice": "Marcus",
                        "language": "en",
                        "seed": 0,
                        "sample_rate_hz": 24000,
                        "speech_rate": 1,
                        "pitch_rate": 1,
                        "volume": 50,
                        "local_tempo_transform": False,
                    },
                    "sample_approved": True,
                    "sample_path": sample_path,
                    "review_notes": (
                        "Operator approved the exact provider-native Marcus proof; "
                        "this full batch remains pending exact-asset listening review."
                    ),
                },
            }
        )
    used = round(account_before["credits"] - account_after["credits"], 2)
    manifest["total_cost_usd"] = 0
    manifest["metadata"]["status"] = "assets_ready_for_human_review"
    manifest["metadata"]["narration"] = {
        "provider": "Higgsfield Qwen",
        "voice": "Marcus",
        "approved_treatment": "provider-native steady take",
        "batch_status": "completed_awaiting_exact_asset_review",
        "approved_sample_path": sample_path,
        "approved_sample_sha256": sample["assets"]["mastered"]["sha256"],
        "proof_approval_receipt": str(MARCUS_PROOF_APPROVAL.relative_to(ROOT)).replace(
            "\\", "/"
        ),
        "model": MODEL,
        "job_type": JOB_TYPE,
        "voice_id": MARCUS_VOICE_ID,
        "sections": len(entries),
        "total_clean_audio_seconds": round(
            sum(entry["duration_seconds"] for entry in entries), 6
        ),
        "measured_timing_map": timing,
        "account_credits_before": account_before["credits"],
        "account_credits_after": account_after["credits"],
        "account_credit_delta": round(
            account_after["credits"] - account_before["credits"], 2
        ),
        "actual_batch_credits_used": used,
        "external_incremental_cost_usd": 0,
        "billing_mode": "existing Higgsfield Max subscription credits",
        "cash_spend_usd": 0,
        "top_up": False,
    }
    atomic_json(path, manifest)

    packaging_path = MARCUS_PROJECT / "artifacts" / "packaging.json"
    packaging = json.loads(packaging_path.read_text(encoding="utf-8"))
    packaging.setdefault("approval", {}).update(
        {
            "current_script_narration": "generated; awaiting exact-asset review",
            "narrator_receipt": str(MARCUS_RECEIPT.relative_to(ROOT)).replace(
                "\\", "/"
            ),
            "narrator_receipt_sha256": sha256(MARCUS_RECEIPT),
        }
    )
    atomic_json(packaging_path, packaging)


def generate_marcus_episode_one(workers: int, dry_run: bool) -> int:
    planned, sample, approval = marcus_episode_one_tasks()
    remaining_words = sum(len(task["text"].split()) for task in planned[1:])
    sample_rate = sample["credits"]["included_credits_used"] / sample["script"][
        "words"
    ]
    estimate = round(remaining_words * sample_rate, 2)
    if dry_run:
        print(
            f"PASS: approved Marcus Episode 1 route; 1 exact sample + 12 pending "
            f"takes; about {estimate:.2f} included Max-plan credits; $0 cash"
        )
        return 0
    if not all(shutil.which(tool) for tool in ("higgsfield", "ffmpeg", "ffprobe")):
        raise RuntimeError("higgsfield, ffmpeg, and ffprobe are required")

    old = (
        json.loads(MARCUS_RECEIPT.read_text(encoding="utf-8"))
        if MARCUS_RECEIPT.is_file()
        else {}
    )
    existing = {("01", "scene-01"): approved_marcus_sample_entry(planned[0], sample)}
    for task in planned[1:]:
        for entry in old.get("entries", []):
            clean = ROOT / entry["clean_path"]
            if (
                entry.get("scene_id") == task["scene_id"]
                and entry.get("render_text_sha256") == task["text_sha256"]
                and entry.get("instruction") == MARCUS_INSTRUCTION
                and entry.get("voice_id") == MARCUS_VOICE_ID
                and clean.is_file()
                and sha256(clean) == entry.get("clean_sha256")
            ):
                existing[("01", task["scene_id"])] = entry
                break
    pending = [
        task for task in planned if ("01", task["scene_id"]) not in existing
    ]
    if len(existing) == 13 and old.get("status") == "completed":
        update_marcus_manifest(
            list(existing.values()), old["account_before"], old["account_after"], sample
        )
        print("PASS: reused 13/13 exact Marcus Episode 1 narration assets")
        return 0

    before = old.get("account_before") or account_status()
    used_job_ids = {entry["job_id"] for entry in existing.values()}
    recoverable = {}
    if pending:
        for task in pending:
            for job in run_json(
                ["higgsfield", "generate", "list", "--audio", "--size", "100", "--json"]
            ):
                params = job.get("params", {})
                if (
                    job["id"] not in used_job_ids
                    and job.get("job_type") == JOB_TYPE
                    and job.get("status") == "completed"
                    and job.get("result_url")
                    and params.get("voice_id") == MARCUS_VOICE_ID
                    and params.get("prompt") == task["text"]
                    and params.get("instruction") == MARCUS_INSTRUCTION
                    and params.get("speech_rate") == 1
                    and params.get("pitch_rate") == 1
                ):
                    recoverable[("01", task["scene_id"])] = job
                    used_job_ids.add(job["id"])
                    break
    state = {
        "schema": "tradercockpit.higgsfield-qwen-marcus-episode-01/v1",
        "created_at": old.get("created_at", datetime.now(timezone.utc).isoformat()),
        "status": "in_progress",
        "proof_approval": {
            "path": str(MARCUS_PROOF_APPROVAL.relative_to(ROOT)).replace("\\", "/"),
            "sha256": sha256(MARCUS_PROOF_APPROVAL),
            "operator_message": approval["operator_message"],
        },
        "model": {
            "display_name": MODEL,
            "job_type": JOB_TYPE,
            "voice": "Marcus",
            "voice_id": MARCUS_VOICE_ID,
            "instruction": MARCUS_INSTRUCTION,
            "speech_rate": 1,
            "pitch_rate": 1,
            "local_tempo_transform": False,
        },
        "processing": (
            "70 Hz high-pass; two-pass EBU R128 normalization to -16 LUFS, "
            "-1.5 dBTP; 48 kHz mono 24-bit PCM; no tempo or pitch transform."
        ),
        "account_before": before,
        "entries": sorted(existing.values(), key=lambda item: item["section_index"]),
        "recovered_provider_jobs": len(recoverable),
        "estimated_included_credits": estimate,
        "external_incremental_cost_usd": 0,
        "billing_mode": "existing Higgsfield Max subscription credits",
        "top_up": False,
    }
    atomic_json(MARCUS_RECEIPT, state)
    lock = threading.Lock()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                generate_one, task, recoverable.get(("01", task["scene_id"]))
            ): task
            for task in pending
        }
        for future in concurrent.futures.as_completed(futures):
            entry = future.result()
            with lock:
                existing[("01", entry["scene_id"])] = entry
                state["entries"] = sorted(
                    existing.values(), key=lambda item: item["section_index"]
                )
                atomic_json(MARCUS_RECEIPT, state)
            print(
                f"EP01 {entry['scene_id']} {entry['duration_seconds']:.3f}s "
                f"{entry['clean_sha256']}"
            )
    entries = sorted(existing.values(), key=lambda item: item["section_index"])
    if len(entries) != 13:
        raise RuntimeError(f"Marcus Episode 1 batch incomplete: {len(entries)}/13")
    after = account_status()
    state.update(
        {
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "account_after": after,
            "account_credit_delta": round(after["credits"] - before["credits"], 2),
            "actual_credits_used": round(before["credits"] - after["credits"], 2),
            "entries": entries,
        }
    )
    atomic_json(MARCUS_RECEIPT, state)
    update_marcus_manifest(entries, before, after, sample)
    print(
        "PASS: 13/13 Episode 1 Marcus narration assets; "
        f"credit delta {state['account_credit_delta']}; $0 cash"
    )
    return 0


def update_manifests(entries: list[dict], account_before: dict, account_after: dict) -> None:
    for episode, project_id in PROJECT_IDS.items():
        project = PROJECTS / project_id
        path = project / "artifacts" / "asset_manifest.json"
        manifest = (
            json.loads(path.read_text(encoding="utf-8"))
            if path.exists()
            else {
                "version": "1.0",
                "assets": [],
                "total_cost_usd": 0,
                "metadata": {
                    "status": "narration_ready_scene_assets_pending",
                    "narration": {
                        "provider": "Higgsfield Qwen",
                        "voice": "John",
                        "approved_treatment": "clean",
                        "clean_deeper": "rejected_by_operator",
                        "approved_sample_path": SAMPLE_PATH,
                        "approved_sample_sha256": SAMPLE_SHA256,
                    },
                },
            }
        )
        manifest["assets"] = [
            asset for asset in manifest["assets"] if asset["type"] != "narration"
        ]
        episode_entries = sorted(
            (entry for entry in entries if entry["episode"] == episode),
            key=lambda item: item["section_index"],
        )
        cursor = 3.0
        timing = []
        for entry in episode_entries:
            scene_id = entry["scene_id"]
            section = json.loads(
                (project / "artifacts" / "script.json").read_text(encoding="utf-8")
            )["sections"][entry["section_index"]]
            local_clean = ROOT / entry["clean_path"]
            start = round(cursor, 6)
            end = round(start + entry["duration_seconds"], 6)
            timing.append({
                "scene_id": scene_id,
                "start_seconds": start,
                "narration_end_seconds": end,
                "pause_after_seconds": entry["pause_after_seconds"],
                "end_seconds": round(end + entry["pause_after_seconds"], 6),
            })
            cursor = end + entry["pause_after_seconds"]
            manifest["assets"].append({
                "id": f"narration-{scene_id}",
                "type": "narration",
                "path": os.path.relpath(local_clean, project).replace("\\", "/"),
                "source_tool": f"Higgsfield {MODEL} plus FFmpeg clean mastering",
                "scene_id": scene_id,
                "model": MODEL,
                "cost_usd": 0,
                "duration_seconds": entry["duration_seconds"],
                "format": "wav",
                "subtype": "qwen_john_clean",
                "generation_summary": (
                    f"Higgsfield job {entry['job_id']}; raw sha256="
                    f"{entry['raw_sha256']}; clean sha256={entry['clean_sha256']}; "
                    "70 Hz high-pass and two-pass EBU R128 normalization."
                ),
                "provider": "Higgsfield",
                "license": "Generated under the operator's existing Max Plan",
                "voice_performance": {
                    "source_section_id": scene_id,
                    "delivery_cues_applied": True,
                    "provider_text_used": True,
                    "provider_settings": {
                        "job_type": JOB_TYPE,
                        "voice_id": VOICE_ID,
                        "voice": "John",
                        "language": "en",
                        "seed": 0,
                        "sample_rate_hz": 24000,
                        "speech_rate": 1,
                        "pitch_rate": 1,
                        "volume": 50,
                    },
                    "sample_approved": True,
                    "sample_path": manifest["metadata"]["narration"][
                        "approved_sample_path"
                    ],
                    "review_notes": (
                        "Operator selected Qwen/John clean and rejected clean-deeper."
                    ),
                },
            })
        manifest["total_cost_usd"] = 0
        manifest["metadata"]["status"] = "assets_ready_for_human_review"
        manifest["metadata"]["narration"].update({
            "batch_status": "completed",
            "model": MODEL,
            "job_type": JOB_TYPE,
            "voice_id": VOICE_ID,
            "sections": len(episode_entries),
            "total_clean_audio_seconds": round(
                sum(entry["duration_seconds"] for entry in episode_entries), 6
            ),
            "measured_timing_map": timing,
            "account_credits_before": account_before["credits"],
            "account_credits_after": account_after["credits"],
            "account_credit_delta": round(
                account_after["credits"] - account_before["credits"], 2
            ),
            "actual_batch_credits_used": round(
                account_before["credits"] - account_after["credits"], 2
            ),
            "estimated_credits": round(
                len(episode_entries) * ESTIMATED_CREDITS_PER_SECTION, 2
            ),
            "external_incremental_cost_usd": 0,
            "billing_mode": "existing Higgsfield subscription credits",
        })
        atomic_json(path, manifest)

        packaging_path = project / "artifacts" / "packaging.json"
        packaging = json.loads(packaging_path.read_text(encoding="utf-8"))
        packaging["approval"].update({
            "current_script_narration": "ready from current exact approved scripts",
            "narrator_receipt": str(RECEIPT.relative_to(ROOT)).replace("\\", "/"),
            "narrator_receipt_sha256": sha256(RECEIPT),
        })
        atomic_json(packaging_path, packaging)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--episode-one-marcus",
        action="store_true",
        help="generate only the proof-approved Marcus narration for Episode 1",
    )
    args = parser.parse_args()
    if args.episode_one_marcus:
        return generate_marcus_episode_one(args.workers, args.dry_run)
    planned = tasks()
    assert spoken_provider_text("p05 p50 p95") == "p05 P fifty P ninety five"
    assert spoken_provider_text("A 70/30 split is not a law.") == (
        "A split of seventy percent in-sample and thirty percent out-of-sample is not a law."
    )
    assert len(planned) == 57
    assert len({(task["episode"], task["scene_id"]) for task in planned}) == 57
    route_approval_sha256 = require_route_approval()
    if args.dry_run:
        print(
            "PASS: 57 unique approved E1-E5 Higgsfield/Qwen/John narration "
            f"sections ready — route {route_approval_sha256}"
        )
        return 0
    if not shutil.which("higgsfield") or not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("higgsfield, ffmpeg, and ffprobe are required")

    existing = {}
    old = {}
    if RECEIPT.exists():
        old = json.loads(RECEIPT.read_text(encoding="utf-8"))
    prior_entries = []
    for receipt_path in (RECEIPT, V4_RECEIPT, LEGACY_RECEIPT):
        if receipt_path.is_file():
            prior_entries.extend(
                json.loads(receipt_path.read_text(encoding="utf-8")).get("entries", [])
            )
    for task in planned:
        for entry in prior_entries:
            clean = ROOT / entry["clean_path"]
            if (
                entry.get("project_id") == task["project_id"]
                and entry.get("scene_id") == task["scene_id"]
                and entry.get(
                    "render_text_sha256", entry.get("provider_text_sha256")
                ) == task["text_sha256"]
                and entry.get("instruction") == task["instruction"]
                and clean.is_file()
                and sha256(clean) == entry.get("clean_sha256")
            ):
                reused = dict(entry)
                reused.update({
                    "episode": task["episode"],
                    "section_index": task["section_index"],
                    "script_sha256": task["script_sha256"],
                    "provider_text_sha256": task["canonical_text_sha256"],
                    "render_text_sha256": task["text_sha256"],
                    "pronunciation_expanded": task["pronunciation_expanded"],
                    "pause_after_seconds": task["pause_after_seconds"],
                })
                existing[(task["episode"], task["scene_id"])] = reused
                break
    pending = [
        task for task in planned
        if (task["episode"], task["scene_id"]) not in existing
    ]
    before = old.get("account_before") or account_status()
    used_job_ids = {entry["job_id"] for entry in existing.values()}
    recoverable = {}
    if pending:
        provider_jobs = run_json([
            "higgsfield", "generate", "list", "--audio", "--size", "100", "--json",
        ])
        for task in pending:
            for job in provider_jobs:
                params = job.get("params", {})
                if (
                    job["id"] not in used_job_ids
                    and job.get("job_type") == JOB_TYPE
                    and job.get("status") == "completed"
                    and job.get("result_url")
                    and params.get("voice_id") == VOICE_ID
                    and params.get("seed") == 0
                    and params.get("prompt") == task["text"]
                    and params.get("instruction") == task["instruction"]
                ):
                    recoverable[(task["episode"], task["scene_id"])] = job
                    used_job_ids.add(job["id"])
                    break
    state = {
        "schema": "tradercockpit.higgsfield-qwen-john-narration/v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "in_progress",
        "route_approval": {
            "path": str(ROUTE_APPROVAL.relative_to(ROOT)).replace("\\", "/"),
            "sha256": route_approval_sha256,
        },
        "model": {
            "display_name": MODEL,
            "job_type": JOB_TYPE,
            "voice": "John",
            "voice_id": VOICE_ID,
            "approved_treatment": "clean",
            "clean_deeper": "rejected_by_operator",
            "approved_sample_sha256": SAMPLE_SHA256,
        },
        "processing": (
            "70 Hz high-pass; two-pass EBU R128 normalization to -16 LUFS, "
            "-1.5 dBTP; 48 kHz mono 24-bit PCM; no denoising."
        ),
        "account_before": before,
        "entries": list(existing.values()),
        "recovered_provider_jobs": (
            old.get("recovered_provider_jobs", 0) + len(recoverable)
        ),
        "estimated_credits": round(
            len(planned) * ESTIMATED_CREDITS_PER_SECTION, 2
        ),
        "external_incremental_cost_usd": 0,
        "billing_mode": "existing Higgsfield subscription credits",
    }
    atomic_json(RECEIPT, state)
    lock = threading.Lock()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                generate_one,
                task,
                recoverable.get((task["episode"], task["scene_id"])),
            ): task
            for task in pending
        }
        for future in concurrent.futures.as_completed(futures):
            entry = future.result()
            with lock:
                existing[(entry["episode"], entry["scene_id"])] = entry
                state["entries"] = sorted(
                    existing.values(),
                    key=lambda item: (item["episode"], item["section_index"]),
                )
                atomic_json(RECEIPT, state)
            print(
                f"EP{entry['episode']} {entry['scene_id']} "
                f"{entry['duration_seconds']:.3f}s {entry['clean_sha256']}"
            )
    after = account_status()
    entries = sorted(
        existing.values(),
        key=lambda item: (item["episode"], item["section_index"]),
    )
    if len(entries) != 57:
        raise RuntimeError(f"narration batch incomplete: {len(entries)}/57")
    state["status"] = "completed"
    state["completed_at"] = datetime.now(timezone.utc).isoformat()
    state["account_after"] = after
    state["account_credit_delta"] = round(
        after["credits"] - before["credits"], 2
    )
    state["actual_credits_used"] = round(
        before["credits"] - after["credits"], 2
    )
    state["entries"] = entries
    atomic_json(RECEIPT, state)
    update_manifests(entries, before, after)
    print(
        f"PASS: 57/57 approved E1-E5 Qwen/John clean narration assets; "
        f"credit delta {state['account_credit_delta']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
