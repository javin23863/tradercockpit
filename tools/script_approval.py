#!/usr/bin/env python3
"""Fail-closed operator approval for the exact narration script."""

import hashlib
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "tradercockpit-script-approval/v1"
PRODUCTION_SCHEMA = "tradercockpit-production-approval/v1"
FRAMING_SOURCES = {"Bloomberg", "Al Jazeera"}


def _inside_repo(value: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("script approval path is required")
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as error:
        raise ValueError("script approval paths must stay inside TraderCockpit") from error
    return path


def load_script_approval(receipt_path: Path) -> dict:
    try:
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"missing or unreadable script approval: {receipt_path}") from error
    if data.get("schema") != SCHEMA:
        raise ValueError(f"script approval schema must be {SCHEMA}")
    if data.get("status") != "approved":
        raise ValueError(f"script approval status is {data.get('status', 'missing')}")
    script = _inside_repo(data.get("script", ""))
    if not script.is_file():
        raise ValueError("approved script does not exist")
    actual = hashlib.sha256(script.read_bytes()).hexdigest()
    if data.get("scriptSha256") != actual:
        raise ValueError("script changed after operator approval")
    if not isinstance(data.get("reviewedBy"), str) or not data["reviewedBy"].strip():
        raise ValueError("script approval reviewedBy is required")
    try:
        reviewed_at = datetime.fromisoformat(data["reviewedAt"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, ValueError) as error:
        raise ValueError("script approval reviewedAt must be ISO-8601") from error
    if reviewed_at.tzinfo is None:
        raise ValueError("script approval reviewedAt must include a timezone")
    return data


def require_script_approval(production: Path) -> dict:
    return load_script_approval(production.resolve() / "script-approval.json")


def _exact_file(data: dict, path_field: str, hash_field: str) -> Path:
    path = _inside_repo(data.get(path_field, ""))
    if not path.is_file():
        raise ValueError(f"production approval {path_field} does not exist")
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if data.get(hash_field) != actual:
        raise ValueError(f"production approval {path_field} changed after operator approval")
    return path


def load_production_approval(receipt_path: Path) -> dict:
    """Validate the exact topic/source material and the existing script approval."""
    try:
        data = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"missing or unreadable production approval: {receipt_path}") from error
    if data.get("schema") != PRODUCTION_SCHEMA:
        raise ValueError(f"production approval schema must be {PRODUCTION_SCHEMA}")
    if data.get("status") != "approved":
        raise ValueError(f"production approval status is {data.get('status', 'missing')}")

    brief = _exact_file(data, "analysisBrief", "analysisBriefSha256")
    sources = _exact_file(data, "sourceReceipt", "sourceReceiptSha256")
    script_approval = _exact_file(data, "scriptApproval", "scriptApprovalSha256")
    load_script_approval(script_approval)

    framing = data.get("framingSources")
    if not isinstance(framing, list) or not framing:
        raise ValueError("production approval requires Bloomberg or Al Jazeera framing")
    if any(source not in FRAMING_SOURCES for source in framing):
        raise ValueError("production approval framingSources must be Bloomberg or Al Jazeera")
    approved_text = (brief.read_text(encoding="utf-8") + "\n" + sources.read_text(encoding="utf-8")).lower()
    if any(source.lower() not in approved_text for source in framing):
        raise ValueError("declared framing source is absent from the approved topic material")

    if not isinstance(data.get("reviewedBy"), str) or not data["reviewedBy"].strip():
        raise ValueError("production approval reviewedBy is required")
    try:
        reviewed_at = datetime.fromisoformat(data["reviewedAt"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, ValueError) as error:
        raise ValueError("production approval reviewedAt must be ISO-8601") from error
    if reviewed_at.tzinfo is None:
        raise ValueError("production approval reviewedAt must include a timezone")
    return data


def require_production_approval(production: Path) -> dict:
    return load_production_approval(production.resolve() / "production-approval.json")
