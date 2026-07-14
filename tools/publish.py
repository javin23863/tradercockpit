#!/usr/bin/env python3
"""Publish one rendered video to YouTube + Instagram Reels + Facebook Reels.

Reads credentials from OpenMontage/.env (see SETUP-CREDS.md):
  YouTube:   client_secret.json next to this script (OAuth on first run)
  Meta:      META_PAGE_ID, META_IG_USER_ID, META_PAGE_TOKEN
  B2 (IG only — Meta ingests Reels from a public URL):
             B2_KEY_ID, B2_APP_KEY, B2_BUCKET, B2_S3_ENDPOINT

Usage:
  python publish.py video.mp4 --title "..." --caption "... #tags" \
      --platforms youtube instagram facebook tiktok [--privacy public] [--thumbnail t.png] [--dry-run]

TikTok is opt-in (not in the default set) and uses the sibling makiisthenes/TiktokAutoUploader
checkout (unofficial, cookie-based; one-time `cli.py login`). See tools/upload_tiktok.py.
"""
import argparse
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE.parent / "OpenMontage" / ".env")
_KEYS_ENV = Path.home() / "Desktop" / "keys.env"
if _KEYS_ENV.exists():
    load_dotenv(_KEYS_ENV)  # existing B2/S3 creds; consumed in-process, never printed

GRAPH = "https://graph.facebook.com/v25.0"


def die(msg):
    sys.exit(f"ERROR: {msg}")


def graph_check(resp):
    data = resp.json()
    if "error" in data:
        die(f"Graph API: {data['error'].get('message')}")
    return data


def _b2_client():
    import boto3
    from botocore.config import Config

    key_id = os.getenv("B2_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
    app_key = os.getenv("B2_APP_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
    endpoint = os.getenv("B2_S3_ENDPOINT") or os.getenv("B2_ENDPOINT_URL")
    bucket = os.getenv("B2_BUCKET")
    if not all([key_id, app_key, bucket, endpoint]):
        die("Instagram needs B2 creds (run b2_setup.py; keys come from keys.env or env)")
    # B2 S3 presigned URLs need the region (e.g. us-west-004) in the SigV4 signature
    m = re.search(r"s3\.([a-z0-9-]+)\.backblazeb2\.com", endpoint)
    region = m.group(1) if m else "us-west-004"
    cfg = Config(region_name=region, signature_version="s3v4")
    return boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=key_id,
                        aws_secret_access_key=app_key, config=cfg), bucket


def b2_stage(video_path):
    """Upload to B2, return (presigned_url, key) for cleanup. URL expires 6h."""
    s3, bucket = _b2_client()
    key = f"openmontage-staging/{Path(video_path).name}"
    s3.upload_file(str(video_path), bucket, key)
    url = s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=6 * 3600)
    return url, key


def b2_cleanup(key):
    try:
        s3, bucket = _b2_client()
        s3.delete_object(Bucket=bucket, Key=key)
    except Exception:
        pass  # transient staging object; 6h presign already expired anyway


def publish_instagram(video_path, caption):
    ig_user, token = os.getenv("META_IG_USER_ID"), os.getenv("META_PAGE_TOKEN")
    if not (ig_user and token):
        die("Set META_IG_USER_ID and META_PAGE_TOKEN in .env")
    url, staged_key = b2_stage(video_path)
    print("IG: staged on B2, creating media container...")
    try:
        container = graph_check(requests.post(f"{GRAPH}/{ig_user}/media", data={
            "media_type": "REELS", "video_url": url, "caption": caption, "access_token": token,
        }))["id"]
        for _ in range(60):  # Meta processing can take minutes
            status = graph_check(requests.get(f"{GRAPH}/{container}",
                                              params={"fields": "status_code", "access_token": token}))["status_code"]
            if status == "FINISHED":
                break
            if status == "ERROR":
                die("IG processing failed — check video specs (9:16, ≤90s, h264/aac)")
            time.sleep(10)
        else:
            die("IG processing timed out")
        media_id = graph_check(requests.post(f"{GRAPH}/{ig_user}/media_publish", data={
            "creation_id": container, "access_token": token,
        }))["id"]
    finally:
        b2_cleanup(staged_key)
    permalink = graph_check(requests.get(f"{GRAPH}/{media_id}",
                                         params={"fields": "permalink", "access_token": token})).get("permalink", media_id)
    print(f"IG Reel published: {permalink}")
    return permalink


def publish_facebook(video_path, caption):
    page_id, token = os.getenv("META_PAGE_ID"), os.getenv("META_PAGE_TOKEN")
    if not (page_id and token):
        die("Set META_PAGE_ID and META_PAGE_TOKEN in .env")
    start = graph_check(requests.post(f"{GRAPH}/{page_id}/video_reels", data={
        "upload_phase": "start", "access_token": token,
    }))
    video_id = start["video_id"]
    size = Path(video_path).stat().st_size
    with open(video_path, "rb") as f:
        r = requests.post(start["upload_url"], data=f, headers={
            "Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size),
        })
    if not r.json().get("success"):
        die(f"FB binary upload failed: {r.text[:300]}")
    graph_check(requests.post(f"{GRAPH}/{page_id}/video_reels", data={
        "upload_phase": "finish", "video_id": video_id, "video_state": "PUBLISHED",
        "description": caption, "access_token": token,
    }))
    print(f"FB Reel published: video id {video_id}")
    return f"https://www.facebook.com/reel/{video_id}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video")
    p.add_argument("--title", required=True, help="YouTube title")
    p.add_argument("--description", default="", help="YouTube description (defaults to caption)")
    p.add_argument("--caption", default="", help="IG/FB caption incl. hashtags")
    p.add_argument("--tags", nargs="*", default=[])
    p.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"], help="YouTube privacy")
    p.add_argument("--thumbnail")
    p.add_argument("--platforms", nargs="+", default=["youtube", "instagram", "facebook"],
                   choices=["youtube", "instagram", "facebook", "tiktok"])
    p.add_argument("--synthetic", action="store_true",
                   help="declare altered/synthetic (AI VO / AI visuals) on YouTube upload")
    p.add_argument("--dry-run", action="store_true", help="validate config + file, publish nothing")
    args = p.parse_args()

    video = Path(args.video)
    if not video.exists():
        die(f"no such file: {video}")

    if args.dry_run:
        from upload_tiktok import cookie_present
        checks = {
            "youtube": (HERE / "client_secret.json").exists() or (HERE / "token.json").exists(),
            "instagram": bool(os.getenv("META_IG_USER_ID") and os.getenv("META_PAGE_TOKEN")
                              and (os.getenv("B2_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID"))
                              and os.getenv("B2_BUCKET")),
            "facebook": bool(os.getenv("META_PAGE_ID") and os.getenv("META_PAGE_TOKEN")),
            "tiktok": cookie_present(),
        }
        for plat in args.platforms:
            print(f"{plat}: {'ready' if checks[plat] else 'MISSING CREDS — see SETUP-CREDS.md'}")
        sys.exit(0 if all(checks[p] for p in args.platforms) else 1)

    results = {}
    if "youtube" in args.platforms:
        from upload_youtube import upload
        results["youtube"] = upload(str(video), args.title, args.description or args.caption,
                                    args.tags, privacy=args.privacy, thumbnail=args.thumbnail,
                                    synthetic=args.synthetic)
    if "facebook" in args.platforms:
        results["facebook"] = publish_facebook(video, args.caption)
    if "instagram" in args.platforms:
        results["instagram"] = publish_instagram(video, args.caption)
    if "tiktok" in args.platforms:
        from upload_tiktok import upload as tiktok_upload
        results["tiktok"] = tiktok_upload(str(video), args.caption or args.title)

    print("\n=== published ===")
    for plat, link in results.items():
        print(f"{plat}: {link}")


if __name__ == "__main__":
    main()
