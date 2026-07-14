#!/usr/bin/env python
"""Validate a Work-prepared social batch and emit only human-approved items."""

import argparse
import hashlib
import json
import tempfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = {"youtube", "tiktok", "email"}
STATUSES = {"draft", "approved", "rejected"}


def inside_repo(value):
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as error:
        raise ValueError("paths must stay inside TraderCockpit") from error
    return path


def approval_fingerprint(batch_id, item):
    asset_path = inside_repo(item.get("asset", ""))
    gate_path = inside_repo(item.get("claimsGate", ""))
    if not asset_path.is_file():
        raise ValueError("asset does not exist")
    if not gate_path.is_file():
        raise ValueError("claimsGate does not exist")
    payload = {
        "schema": "social-approval/v1",
        "batchId": batch_id,
        "id": item.get("id"),
        "channel": item.get("channel"),
        "copy": item.get("copy"),
        "asset": item.get("asset"),
        "assetSha256": hashlib.sha256(asset_path.read_bytes()).hexdigest(),
        "claimsGate": item.get("claimsGate"),
        "claimsGateSha256": hashlib.sha256(gate_path.read_bytes()).hexdigest(),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate(data):
    if not isinstance(data, dict) or data.get("schema") != "social-batch/v1":
        raise ValueError('schema must be "social-batch/v1"')
    if not isinstance(data.get("batchId"), str) or not data["batchId"].strip():
        raise ValueError("batchId is required")
    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("items must be an array")

    seen = set()
    for index, item in enumerate(items):
        tag = f"items[{index}]"
        if not isinstance(item, dict):
            raise ValueError(f"{tag} must be an object")
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id.strip() or item_id in seen:
            raise ValueError(f"{tag}.id must be non-empty and unique")
        seen.add(item_id)
        if item.get("channel") not in CHANNELS:
            raise ValueError(f"{tag}.channel must be youtube, tiktok, or email")
        if item.get("status") not in STATUSES:
            raise ValueError(f"{tag}.status must be draft, approved, or rejected")
        if not isinstance(item.get("copy"), str):
            raise ValueError(f"{tag}.copy must be a string")

        if item["status"] == "approved":
            for field in ("asset", "reviewedBy", "reviewedAt", "claimsGate", "approvalSha256"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise ValueError(f"{tag}.{field} is required for approval")
            try:
                reviewed_at = datetime.fromisoformat(item["reviewedAt"].replace("Z", "+00:00"))
            except ValueError as error:
                raise ValueError(f"{tag}.reviewedAt must be an ISO-8601 timestamp") from error
            if reviewed_at.tzinfo is None:
                raise ValueError(f"{tag}.reviewedAt must include a timezone")
            if not inside_repo(item["asset"]).is_file():
                raise ValueError(f"{tag}.asset does not exist")
            gate_path = inside_repo(item["claimsGate"])
            try:
                gate = json.loads(gate_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ValueError(f"{tag}.claimsGate is not readable JSON") from error
            if gate.get("verdict") != "PASS":
                raise ValueError(f"{tag}.claimsGate must have verdict PASS")
            if gate.get("blocked") != []:
                raise ValueError(f"{tag}.claimsGate must have no blocked claims")
            checked = gate.get("checked_sections")
            if isinstance(checked, bool) or not isinstance(checked, int) or checked < 1:
                raise ValueError(f"{tag}.claimsGate must record checked_sections")
            expected = approval_fingerprint(data["batchId"], item)
            if item["approvalSha256"] != expected:
                raise ValueError(f"{tag}.approvalSha256 does not match the reviewed copy, asset, and claims gate")
    return data


def load(path):
    try:
        return validate(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as error:
        raise ValueError("batch is not valid JSON") from error


def selftest():
    base = {"schema": "social-batch/v1", "batchId": "test", "items": []}
    validate(base)
    try:
        validate({**base, "schema": "social-batch/v2"})
        raise AssertionError("unsupported schema should fail")
    except ValueError:
        pass
    try:
        validate({**base, "items": [{"id": "x", "channel": "tiktok", "status": "approved", "copy": "x"}]})
        raise AssertionError("incomplete approval should fail")
    except ValueError:
        pass

    with tempfile.TemporaryDirectory(dir=ROOT) as folder:
        temp = Path(folder)
        asset = temp / "clip.mp4"
        gate = temp / "gate.json"
        asset.write_bytes(b"test")
        gate.write_text('{"verdict":"PASS","checked_sections":1,"blocked":[]}', encoding="utf-8")
        relative_asset = asset.relative_to(ROOT).as_posix()
        relative_gate = gate.relative_to(ROOT).as_posix()
        item = {
            "id": "x", "channel": "tiktok", "status": "approved", "copy": "x",
            "asset": relative_asset, "reviewedBy": "operator", "reviewedAt": "2026-07-15T00:00:00Z",
            "claimsGate": relative_gate,
        }
        item["approvalSha256"] = approval_fingerprint(base["batchId"], item)
        approved = {**base, "items": [item]}
        assert len([item for item in validate(approved)["items"] if item["status"] == "approved"]) == 1
        item["copy"] = "changed after approval"
        try:
            validate(approved)
            raise AssertionError("post-approval edits should fail")
        except ValueError:
            pass
    print("social-batch self-test: 4/4 PASS")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("validate", "fingerprint", "ready", "selftest"))
    parser.add_argument("batch", nargs="?", type=Path)
    parser.add_argument("--item", dest="item_id")
    args = parser.parse_args()
    if args.command == "selftest":
        selftest()
        return
    if not args.batch:
        parser.error("batch path is required")
    data = load(args.batch)
    if args.command == "fingerprint":
        if not args.item_id:
            parser.error("fingerprint requires --item ID")
        item = next((candidate for candidate in data["items"] if candidate["id"] == args.item_id), None)
        if item is None:
            raise ValueError(f"item not found: {args.item_id}")
        print(approval_fingerprint(data["batchId"], item))
        return
    approved = [item for item in data["items"] if item["status"] == "approved"]
    if args.command == "ready":
        if not approved:
            raise SystemExit("BLOCK: no human-approved items")
        print(json.dumps({"schema": "social-ready/v1", "batchId": data["batchId"], "items": approved}, indent=2))
    else:
        print(f"social-batch: PASS — {len(data['items'])} items, {len(approved)} approved")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        raise SystemExit(f"BLOCK: {error}") from error
