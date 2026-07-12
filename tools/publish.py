#!/usr/bin/env python3
"""Publish one rendered video to YouTube + Instagram Reels + Facebook Reels.

Reads credentials from OpenMontage/.env (see SETUP-CREDS.md):
  YouTube:   client_secret.json next to this script (OAuth on first run)
  Meta:      META_PAGE_ID, META_IG_USER_ID, META_PAGE_TOKEN
  B2 (IG only — Meta ingests Reels from a public URL):
             B2_KEY_ID, B2_APP_KEY, B2_BUCKET, B2_S3_ENDPOINT

Usage:
  python publish.py video.mp4 --title "..." --caption "... #tags" \
      --platforms youtube instagram facebook [--privacy public] [--thumbnail t.png] [--dry-run]
"""
import argparse
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

HERE = Path(__file__).parent
load_dotenv(HERE.parent / "OpenMontage" / ".env")

GRAPH = "https://graph.facebook.com/v25.0"


def die(msg):
    sys.exit(f"ERROR: {msg}")


def graph_check(resp):
    data = resp.json()
    if "error" in data:
        die(f"Graph API: {data['error'].get('message')}")
    return data


def b2_public_url(video_path):
    """Upload to B2, return a presigned URL Meta can ingest (expires 6h)."""
    import boto3

    key_id, app_key = os.getenv("B2_KEY_ID"), os.getenv("B2_APP_KEY")
    bucket, endpoint = os.getenv("B2_BUCKET"), os.getenv("B2_S3_ENDPOINT")
    if not all([key_id, app_key, bucket, endpoint]):
        die("Instagram needs B2_KEY_ID/B2_APP_KEY/B2_BUCKET/B2_S3_ENDPOINT in .env (Meta ingests from URL)")
    s3 = boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=key_id, aws_secret_access_key=app_key)
    key = f"publish-staging/{Path(video_path).name}"
    s3.upload_file(str(video_path), bucket, key)
    return s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=6 * 3600)


def publish_instagram(video_path, caption):
    ig_user, token = os.getenv("META_IG_USER_ID"), os.getenv("META_PAGE_TOKEN")
    if not (ig_user and token):
        die("Set META_IG_USER_ID and META_PAGE_TOKEN in .env")
    url = b2_public_url(video_path)
    print("IG: staged on B2, creating media container...")
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
                   choices=["youtube", "instagram", "facebook"])
    p.add_argument("--dry-run", action="store_true", help="validate config + file, publish nothing")
    args = p.parse_args()

    video = Path(args.video)
    if not video.exists():
        die(f"no such file: {video}")

    if args.dry_run:
        checks = {
            "youtube": (HERE / "client_secret.json").exists() or (HERE / "token.json").exists(),
            "instagram": bool(os.getenv("META_IG_USER_ID") and os.getenv("META_PAGE_TOKEN") and os.getenv("B2_KEY_ID")),
            "facebook": bool(os.getenv("META_PAGE_ID") and os.getenv("META_PAGE_TOKEN")),
        }
        for plat in args.platforms:
            print(f"{plat}: {'ready' if checks[plat] else 'MISSING CREDS — see SETUP-CREDS.md'}")
        sys.exit(0 if all(checks[p] for p in args.platforms) else 1)

    results = {}
    if "youtube" in args.platforms:
        from upload_youtube import upload
        results["youtube"] = upload(str(video), args.title, args.description or args.caption,
                                    args.tags, privacy=args.privacy, thumbnail=args.thumbnail)
    if "facebook" in args.platforms:
        results["facebook"] = publish_facebook(video, args.caption)
    if "instagram" in args.platforms:
        results["instagram"] = publish_instagram(video, args.caption)

    print("\n=== published ===")
    for plat, link in results.items():
        print(f"{plat}: {link}")


if __name__ == "__main__":
    main()
