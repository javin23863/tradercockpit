#!/usr/bin/env python
"""Validate a Work-prepared social batch and emit only human-approved items."""

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

try:
    from tools import script_style_gate
    from tools.script_approval import load_production_approval, load_script_approval
except ModuleNotFoundError:  # direct `python tools/social_batch.py` execution
    import script_style_gate
    from script_approval import load_production_approval, load_script_approval

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = {"youtube", "instagram", "facebook", "tiktok", "email"}
STATUSES = {"draft", "approved", "rejected"}
SCHEMAS = {"social-batch/v1", "social-batch/v2"}
CAPTION_MODES = {"native", "burned", "none"}
PRIVACY = {"private", "unlisted", "public"}
REQUIRED_DISCLAIMER = "Research tooling, not financial advice. No performance is promised or implied."
DISCLAIMER_RE = re.compile(
    r"\bResearch\s+tooling,\s*not\s+financial\s+advice\.\s*"
    r"No\s+performance\s+is\s+promised\s+or\s+implied\.",
    re.IGNORECASE,
)
SCENE_PLAN_SCHEMA = "tradercockpit-scene-plan/v1"
SYNTHETIC_KIND_WORDS = {"generated", "synthetic"}
NON_SYNTHETIC_KINDS = {
    "news", "official-footage", "source-chart-sequence", "tradingview", "tradingview-sequence",
}


def inside_repo(value):
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError as error:
        raise ValueError("paths must stay inside TraderCockpit") from error
    return path


def _check_synthetic_disclosure(plan, contains_synthetic_media):
    # True is safe over-disclosure. False must be supported by a complete kind declaration.
    if contains_synthetic_media:
        return
    if not isinstance(plan, dict) or plan.get("schema") != SCENE_PLAN_SCHEMA:
        raise ValueError(f"containsSyntheticMedia=false requires a {SCENE_PLAN_SCHEMA} scene-plan")
    beats = plan.get("beats")
    if not isinstance(beats, list) or not beats:
        raise ValueError("containsSyntheticMedia=false requires a non-empty scene-plan beats list")
    for index, beat in enumerate(beats):
        visual = beat.get("visual") if isinstance(beat, dict) else None
        kind = visual.get("kind") if isinstance(visual, dict) else None
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError(
                f"containsSyntheticMedia=false cannot be verified: scene-plan beats[{index}].visual.kind is required"
            )
        normalized = re.sub(r"\s+", " ", kind).strip().lower()
        if SYNTHETIC_KIND_WORDS.intersection(re.findall(r"[a-z]+", normalized)):
            raise ValueError(
                f"containsSyntheticMedia must be true: scene-plan beats[{index}] uses {kind!r} visual media"
            )
        if normalized not in NON_SYNTHETIC_KINDS:
            # Conservative default: a new kind needs an explicit classification before a false declaration.
            raise ValueError(
                f"containsSyntheticMedia=false cannot be verified: scene-plan beats[{index}] "
                f"uses unclassified visual kind {kind!r}"
            )
    # Not covered deterministically: current scene-plan visuals carry no source/model/seed/license
    # or synthetic provenance. This checks explicit kind declarations, not pixels or mislabeled assets.


def _require_synthetic_disclosure(production_approval_path, contains_synthetic_media):
    if contains_synthetic_media:
        return
    plan_path = production_approval_path.parent / "scene-plan.json"
    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"containsSyntheticMedia=false cannot be verified from {plan_path}"
        ) from error
    _check_synthetic_disclosure(plan, contains_synthetic_media)


def approval_fingerprint(batch_id, item, contains_synthetic_media=False, schema="social-batch/v1"):
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
        "containsSyntheticMedia": contains_synthetic_media,
    }
    if schema == "social-batch/v1":
        script_approval_path = inside_repo(item.get("scriptApproval", ""))
        load_script_approval(script_approval_path)
        payload.update({
            "scriptApproval": item.get("scriptApproval"),
            "scriptApprovalSha256": hashlib.sha256(script_approval_path.read_bytes()).hexdigest(),
        })
    elif schema == "social-batch/v2":
        production_approval_path = inside_repo(item.get("productionApproval", ""))
        load_production_approval(production_approval_path)
        _require_synthetic_disclosure(production_approval_path, contains_synthetic_media)
        payload.update({
            "schema": "social-approval/v2",
            "title": item.get("title"),
            "captionMode": item.get("captionMode"),
            "privacy": item.get("privacy"),
            "productionApproval": item.get("productionApproval"),
            "productionApprovalSha256": hashlib.sha256(production_approval_path.read_bytes()).hexdigest(),
            "publicationAuthorized": item.get("publicationAuthorized"),
            "reviewedBy": item.get("reviewedBy"),
            "reviewedAt": item.get("reviewedAt"),
        })
    else:
        raise ValueError(f"unsupported batch schema: {schema}")
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate(data):
    if not isinstance(data, dict) or data.get("schema") not in SCHEMAS:
        raise ValueError(f"schema must be one of: {', '.join(sorted(SCHEMAS))}")
    schema = data["schema"]
    if not isinstance(data.get("batchId"), str) or not data["batchId"].strip():
        raise ValueError("batchId is required")
    if not isinstance(data.get("containsSyntheticMedia", False), bool):
        raise ValueError("containsSyntheticMedia must be true or false")
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
            raise ValueError(f"{tag}.channel must be one of: {', '.join(sorted(CHANNELS))}")
        if item.get("status") not in STATUSES:
            raise ValueError(f"{tag}.status must be draft, approved, or rejected")
        if not isinstance(item.get("copy"), str):
            raise ValueError(f"{tag}.copy must be a string")
        if schema == "social-batch/v2":
            # v1 remains readable historical evidence; only v2 can reach a live boundary.
            surfaces = {"copy": item["copy"]}
            if "description" in item:
                if not isinstance(item["description"], str):
                    raise ValueError(f"{tag}.description must be a string")
                surfaces["description"] = item["description"]
            for field, surface in surfaces.items():
                # BLOCK: this exact boundary is the legal minimum for every live offer surface.
                if not DISCLAIMER_RE.search(surface):
                    raise ValueError(f"{tag}.{field} is missing the required research-tooling disclaimer")
                style = script_style_gate.audit_text(surface)
                # BLOCK deterministic violations; heuristic warns remain editorial review signals.
                if style["verdict"] != "PASS":
                    details = ", ".join(f"{finding['type']} x{finding['count']}" for finding in style["blocked"])
                    raise ValueError(f"{tag}.{field} script style gate BLOCK: {details}")

        if item["status"] == "approved":
            if schema == "social-batch/v1":
                continue  # historical evidence; live and ready paths reject v1
            fields = [
                "asset", "reviewedBy", "reviewedAt", "claimsGate", "approvalSha256",
                "productionApproval", "title", "captionMode", "privacy",
            ]
            for field in fields:
                if not isinstance(item.get(field), str) or not item[field].strip():
                    raise ValueError(f"{tag}.{field} is required for approval")
            if schema == "social-batch/v2":
                if item["captionMode"] not in CAPTION_MODES:
                    raise ValueError(f"{tag}.captionMode must be one of: {', '.join(sorted(CAPTION_MODES))}")
                if item["privacy"] not in PRIVACY:
                    raise ValueError(f"{tag}.privacy must be one of: {', '.join(sorted(PRIVACY))}")
                if item["channel"] == "youtube" and item["captionMode"] != "native":
                    raise ValueError(f"{tag}: YouTube requires the caption-free master and native captions")
                if item.get("publicationAuthorized") is not True:
                    raise ValueError(f"{tag}.publicationAuthorized must be true")
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
            expected = approval_fingerprint(
                data["batchId"], item, data.get("containsSyntheticMedia", False), schema
            )
            if item["approvalSha256"] != expected:
                raise ValueError(f"{tag}.approvalSha256 does not match the reviewed copy, asset, and claims gate")
    return data


def load(path):
    try:
        return validate(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as error:
        raise ValueError("batch is not valid JSON") from error


def selftest():
    compliant_copy = f"Brent settled at 83. My read holds above 81.\n\n{REQUIRED_DISCLAIMER}"
    base = {
        "schema": "social-batch/v1", "batchId": "test",
        "containsSyntheticMedia": False, "items": [],
    }
    validate(base)
    try:
        validate({**base, "schema": "social-batch/v3"})
        raise AssertionError("unsupported schema should fail")
    except ValueError:
        pass
    try:
        validate({
            **base, "schema": "social-batch/v2",
            "items": [{"id": "x", "channel": "tiktok", "status": "approved", "copy": compliant_copy}],
        })
        raise AssertionError("incomplete approval should fail")
    except ValueError:
        pass
    parity = {
        **base,
        "items": [
            {"id": channel, "channel": channel, "status": "draft", "copy": compliant_copy}
            for channel in sorted(CHANNELS)
        ],
    }
    assert {item["channel"] for item in validate(parity)["items"]} == CHANNELS
    real_plan = {
        "schema": SCENE_PLAN_SCHEMA,
        "beats": [{"visual": {"kind": "news"}}],
    }
    _check_synthetic_disclosure(real_plan, False)
    synthetic_plan = {
        "schema": SCENE_PLAN_SCHEMA,
        "beats": [{"visual": {"kind": "ai-generated-image"}}],
    }
    _check_synthetic_disclosure(synthetic_plan, True)
    try:
        _check_synthetic_disclosure(synthetic_plan, False)
        raise AssertionError("generated visual with a false disclosure should fail")
    except ValueError as error:
        assert "containsSyntheticMedia must be true" in str(error)
    try:
        _check_synthetic_disclosure({
            "schema": SCENE_PLAN_SCHEMA,
            "beats": [{"visual": {}}],
        }, False)
        raise AssertionError("missing visual kind should fail closed")
    except ValueError as error:
        assert "cannot be verified" in str(error)
    try:
        _check_synthetic_disclosure({
            "schema": SCENE_PLAN_SCHEMA,
            "beats": [{"visual": {"kind": "ai-image"}}],
        }, False)
        raise AssertionError("unclassified visual kind should fail closed")
    except ValueError as error:
        assert "unclassified visual kind" in str(error)
    print("social-batch self-test: 9/9 PASS")


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
        print(approval_fingerprint(
            data["batchId"], item, data.get("containsSyntheticMedia", False), data["schema"]
        ))
        return
    approved = [item for item in data["items"] if item["status"] == "approved"]
    if args.command == "ready":
        if data["schema"] != "social-batch/v2":
            raise SystemExit("BLOCK: social-batch/v1 is historical evidence only")
        if not approved:
            raise SystemExit("BLOCK: no human-approved items")
        print(json.dumps({
            "schema": "social-ready/v1", "batchId": data["batchId"],
            "containsSyntheticMedia": data.get("containsSyntheticMedia", False),
            "items": approved,
        }, indent=2))
    else:
        print(f"social-batch: PASS — {len(data['items'])} items, {len(approved)} approved")


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        raise SystemExit(f"BLOCK: {error}") from error
