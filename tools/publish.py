#!/usr/bin/env python3
"""Publish one exact social-batch/v2 item after operator-held auth probes."""

import argparse
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

try:
    from tools.social_batch import ROOT, load as load_social_batch
except ModuleNotFoundError:  # direct `python tools/publish.py` execution
    from social_batch import ROOT, load as load_social_batch


HERE = Path(__file__).parent
for _env_path in filter(None, [
    Path(os.environ["TRADERCOCKPIT_ENV"]) if os.getenv("TRADERCOCKPIT_ENV") else None,
    HERE.parent / "OpenMontage" / ".env",
]):
    if _env_path.is_file():
        load_dotenv(_env_path)
        break
_KEYS_ENV = Path.home() / "Desktop" / "keys.env"
if _KEYS_ENV.exists():
    load_dotenv(_KEYS_ENV)

try:
    from tools.credential_custody import load_meta_env
except ModuleNotFoundError:
    from credential_custody import load_meta_env
load_meta_env()  # Meta publish creds live in operator custody, not the repo

GRAPH = "https://graph.facebook.com/v25.0"
LIVE_CHANNELS = {"youtube", "instagram", "facebook", "tiktok"}
LOG_SCHEMA = "tradercockpit-publish-log/v2"


def module_available(name):
    return importlib.util.find_spec(name) is not None


def youtube_readiness():
    if not all(module_available(name) for name in ("googleapiclient", "google_auth_oauthlib")):
        return {"status": "dependency-missing", "ready": False, "channelId": None}
    from upload_youtube import probe_auth

    return probe_auth()


def tiktok_readiness():
    from upload_tiktok import probe_auth

    return probe_auth()


def readiness_report():
    return {
        "youtube": youtube_readiness(),
        "instagram": {
            "status": "valid" if all([
                os.getenv("META_IG_USER_ID"), os.getenv("META_PAGE_TOKEN"),
                os.getenv("B2_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID"),
                os.getenv("B2_APP_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY"),
                os.getenv("B2_BUCKET"), os.getenv("B2_S3_ENDPOINT") or os.getenv("B2_ENDPOINT_URL"),
                module_available("boto3"),
            ]) else "absent",
            "ready": bool(all([
                os.getenv("META_IG_USER_ID"), os.getenv("META_PAGE_TOKEN"),
                os.getenv("B2_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID"),
                os.getenv("B2_APP_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY"),
                os.getenv("B2_BUCKET"), os.getenv("B2_S3_ENDPOINT") or os.getenv("B2_ENDPOINT_URL"),
                module_available("boto3"),
            ])),
        },
        "facebook": {
            "status": "valid" if os.getenv("META_PAGE_ID") and os.getenv("META_PAGE_TOKEN") else "absent",
            "ready": bool(os.getenv("META_PAGE_ID") and os.getenv("META_PAGE_TOKEN")),
        },
        "tiktok": tiktok_readiness(),
    }


def readiness_checks():
    return {platform: probe["ready"] for platform, probe in readiness_report().items()}


def graph_check(response):
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"Graph API: {data['error'].get('message')}")
    return data


def _b2_client():
    import boto3
    from botocore.config import Config

    key_id = os.getenv("B2_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
    app_key = os.getenv("B2_APP_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
    endpoint = os.getenv("B2_S3_ENDPOINT") or os.getenv("B2_ENDPOINT_URL")
    bucket = os.getenv("B2_BUCKET")
    if not all([key_id, app_key, bucket, endpoint]):
        raise RuntimeError("Instagram needs B2 staging credentials")
    match = re.search(r"s3\.([a-z0-9-]+)\.backblazeb2\.com", endpoint)
    config = Config(region_name=match.group(1) if match else "us-west-004", signature_version="s3v4")
    return boto3.client(
        "s3", endpoint_url=endpoint, aws_access_key_id=key_id,
        aws_secret_access_key=app_key, config=config,
    ), bucket


def b2_stage(video_path):
    s3, bucket = _b2_client()
    key = f"openmontage-staging/{Path(video_path).name}"
    s3.upload_file(str(video_path), bucket, key)
    return s3.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=6 * 3600
    ), key


def b2_cleanup(key):
    try:
        s3, bucket = _b2_client()
        s3.delete_object(Bucket=bucket, Key=key)
    except Exception:
        pass


def publish_instagram(video_path, caption):
    user, token = os.getenv("META_IG_USER_ID"), os.getenv("META_PAGE_TOKEN")
    if not (user and token):
        raise RuntimeError("Instagram credentials are absent")
    url, staged_key = b2_stage(video_path)
    try:
        create = graph_check(requests.post(f"{GRAPH}/{user}/media", data={
            "media_type": "REELS", "video_url": url, "caption": caption, "access_token": token,
        }))
        container = create["id"]
        for _ in range(60):
            status = graph_check(requests.get(
                f"{GRAPH}/{container}", params={"fields": "status_code", "access_token": token}
            ))["status_code"]
            if status == "FINISHED":
                break
            if status == "ERROR":
                raise RuntimeError("Instagram processing failed")
            time.sleep(10)
        else:
            raise RuntimeError("Instagram processing timed out")
        published = graph_check(requests.post(f"{GRAPH}/{user}/media_publish", data={
            "creation_id": container, "access_token": token,
        }))
    finally:
        b2_cleanup(staged_key)
    media_id = published.get("id")
    readback = graph_check(requests.get(
        f"{GRAPH}/{media_id}", params={"fields": "id,permalink", "access_token": token}
    ))
    if not media_id or readback.get("id") != media_id or not readback.get("permalink"):
        raise RuntimeError("Instagram returned no matching post read-back")
    return {
        "status": "published", "id": media_id, "url": readback["permalink"],
        "platformResponse": {"publish": published, "readback": readback},
    }


def publish_facebook(video_path, caption):
    page_id, token = os.getenv("META_PAGE_ID"), os.getenv("META_PAGE_TOKEN")
    if not (page_id and token):
        raise RuntimeError("Facebook credentials are absent")
    start = graph_check(requests.post(f"{GRAPH}/{page_id}/video_reels", data={
        "upload_phase": "start", "access_token": token,
    }))
    video_id = start["video_id"]
    with open(video_path, "rb") as video:
        binary = requests.post(start["upload_url"], data=video, headers={
            "Authorization": f"OAuth {token}", "offset": "0",
            "file_size": str(Path(video_path).stat().st_size),
        })
    if not binary.json().get("success"):
        raise RuntimeError("Facebook binary upload failed")
    finish = graph_check(requests.post(f"{GRAPH}/{page_id}/video_reels", data={
        "upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED",
        "description": caption, "access_token": token,
    }))
    readback = graph_check(requests.get(
        f"{GRAPH}/{video_id}", params={"fields": "id,permalink_url", "access_token": token}
    ))
    if readback.get("id") != video_id or not readback.get("permalink_url"):
        raise RuntimeError("Facebook returned no matching post read-back")
    return {
        "status": "published", "id": video_id, "url": readback["permalink_url"],
        "platformResponse": {"finish": finish, "readback": readback},
    }


def load_live_item(batch_path, item_id, requested_platform=None):
    data = load_social_batch(Path(batch_path))
    if data["schema"] != "social-batch/v2":
        raise ValueError("social-batch/v1 is historical evidence only and cannot publish")
    item = next((candidate for candidate in data["items"] if candidate["id"] == item_id), None)
    if item is None:
        raise ValueError(f"item not found: {item_id}")
    if item["status"] != "approved":
        raise ValueError(f"item status is {item['status']}, not approved")
    platform = item["channel"]
    if platform not in LIVE_CHANNELS:
        raise ValueError(f"item channel is not publishable: {platform}")
    if requested_platform and requested_platform != platform:
        raise ValueError(f"platform mismatch: item is {platform}, request is {requested_platform}")
    return data, item


def _asset(item):
    path = (ROOT / item["asset"]).resolve()
    if not path.is_file():
        raise ValueError("approved asset is missing")
    return path


def dispatch_publish(item):
    platform, asset = item["channel"], _asset(item)
    if platform == "youtube":
        from upload_youtube import upload

        return upload(
            str(asset), item["title"], item["copy"], privacy=item["privacy"],
            synthetic=item.get("containsSyntheticMedia", False), interactive=False,
        )
    if platform == "instagram":
        return publish_instagram(asset, item["copy"])
    if platform == "facebook":
        return publish_facebook(asset, item["copy"])
    from upload_tiktok import upload

    return upload(str(asset), item["copy"] or item["title"])


def _normalized_result(result):
    if isinstance(result, dict):
        platform_id = result.get("id")
        response = result.get("platformResponse") or {}
        readback = response.get("readback") or {}
        readback_ids = {readback.get("id"), *(
            item.get("id") for item in readback.get("items", []) if isinstance(item, dict)
        )}
        if (
            result.get("status") == "published"
            and platform_id
            and result.get("url")
            and platform_id in readback_ids
        ):
            return "published", platform_id, result["url"]
    return "uploaded-unverified", None, None


def write_publish_log(batch_path, batch_id, item, result=None, error=None):
    path = Path(batch_path).resolve().parent / "publish_log.json"
    if path.exists():
        log = json.loads(path.read_text(encoding="utf-8"))
        if log.get("schema") != LOG_SCHEMA or not isinstance(log.get("entries"), list):
            raise ValueError(f"refusing to overwrite incompatible publish log: {path}")
    else:
        log = {"schema": LOG_SCHEMA, "entries": []}
    status, platform_id, url = (
        ("failed", None, None) if error else _normalized_result(result)
    )
    entry = {
        "batchId": batch_id,
        "itemId": item["id"],
        "platform": item["channel"],
        "status": status,
        "platformId": platform_id,
        "url": url,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "platformResponse": result.get("platformResponse") if isinstance(result, dict) else None,
        "error": str(error) if error else None,
    }
    log["entries"].append(entry)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(log, indent=2), encoding="utf-8")
    temporary.replace(path)
    return entry


def publish_batch_item(batch_path, item_id, requested_platform=None):
    data, item = load_live_item(batch_path, item_id, requested_platform)
    probe = readiness_report()[item["channel"]]
    if not probe["ready"]:
        error = RuntimeError(f"{item['channel']} authentication blocked: {probe['status']}")
        write_publish_log(batch_path, data["batchId"], item, error=error)
        raise error
    try:
        result = dispatch_publish({
            **item, "containsSyntheticMedia": data.get("containsSyntheticMedia", False)
        })
    except Exception as error:
        write_publish_log(batch_path, data["batchId"], item, error=error)
        raise
    entry = write_publish_log(batch_path, data["batchId"], item, result=result)
    if entry["status"] != "published":
        raise RuntimeError(f"{item['channel']} upload is uploaded-unverified; no live ID/URL read-back")
    return entry


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path)
    parser.add_argument("--item")
    parser.add_argument("--platform", choices=sorted(LIVE_CHANNELS))
    parser.add_argument("--dry-run", action="store_true", help="probe only; never upload")
    args = parser.parse_args(argv)

    if args.dry_run:
        if bool(args.batch) != bool(args.item):
            parser.error("--batch and --item must be supplied together")
        platforms = [args.platform] if args.platform else sorted(LIVE_CHANNELS)
        if args.batch:
            _, item = load_live_item(args.batch, args.item, args.platform)
            platforms = [item["channel"]]
        report = readiness_report()
        for platform in platforms:
            print(f"{platform}: {report[platform]['status']}")
        return 0 if all(report[platform]["ready"] for platform in platforms) else 1

    if not args.batch or not args.item:
        parser.error("live publishing requires --batch and --item")
    try:
        entry = publish_batch_item(args.batch, args.item, args.platform)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as error:
        raise SystemExit(f"ERROR: {error}") from error
    print(f"published {entry['platform']}: {entry['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
