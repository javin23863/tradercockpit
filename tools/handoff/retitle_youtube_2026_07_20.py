#!/usr/bin/env python3
"""Apply the audited 2026-07-20 YouTube title-only rewrites."""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from tools.credential_custody import credential_path
from tools.script_style_gate import audit_text
from tools.upload_youtube import EXPECTED_CHANNEL_ID


SCOPES = ["https://www.googleapis.com/auth/youtube"]
RECEIPT = Path("social-ops/retitle-receipts.json")
LANDING_URL = "https://javin23863.github.io/tradercockpit/"
REWRITES = {
    "HW8VpcxvdAY": (
        "Don't Trade the Siren. Trade the Pressure Chain. #Shorts",
        "Oil +10%, Energy +4%: What Actually Moved #Shorts",
    ),
    "D3FMz1Nncqg": (
        "The market is pricing the Strait, not the end of the world #Shorts",
        "5 Tankers vs 130 a Day: What Hormuz Actually Closed #Shorts",
    ),
    "IQJsq4EYQXA": (
        "The Nasdaq Broke. The S&P Held.",
        "Nasdaq Broke 7431, S&P Held Its Band — The Divergence",
    ),
    "33cnTUL4ga4": (
        "Iran Oil Deadline Day Meets a Cracking AI Trade",
        "Iran Deadline Day and TSMC's $403.50 Floor",
    ),
    "J2EBBMDoKhc": (
        "Iran War Widens as Oil Holds $84",
        "Oil Holds $84 as the Risk Premium Sticks",
    ),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def write_receipt(receipt: dict) -> None:
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    temporary = RECEIPT.with_suffix(".tmp")
    temporary.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, RECEIPT)


def get_service():
    token = credential_path("token_channel.json")
    if not token.is_file():
        raise RuntimeError(f"missing non-interactive channel token: {token}")
    credentials = Credentials.from_authorized_user_file(token, SCOPES)
    if not credentials.valid and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        token.write_text(credentials.to_json(), encoding="utf-8")
    if not credentials.valid:
        raise RuntimeError("channel token is invalid; interactive authorization is intentionally disabled")
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def public_videos(youtube) -> list[dict]:
    channels = youtube.channels().list(part="id,contentDetails", mine=True).execute().get("items", [])
    if len(channels) != 1 or channels[0].get("id") != EXPECTED_CHANNEL_ID:
        raise RuntimeError(f"channel mismatch: expected {EXPECTED_CHANNEL_ID!r}, got {[x.get('id') for x in channels]!r}")
    uploads = channels[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, page_token = [], None
    while True:
        page = youtube.playlistItems().list(
            part="contentDetails", playlistId=uploads, maxResults=50, pageToken=page_token
        ).execute()
        ids.extend(item["contentDetails"]["videoId"] for item in page.get("items", []))
        page_token = page.get("nextPageToken")
        if not page_token:
            break
    videos = youtube.videos().list(
        part="snippet,status,statistics", id=",".join(ids), maxResults=50
    ).execute().get("items", [])
    return [video for video in videos if video["status"]["privacyStatus"] == "public"]


def update_body(video: dict, title: str) -> dict:
    before = video["snippet"]
    snippet = {
        "title": title,
        "description": before.get("description", ""),
        "categoryId": before["categoryId"],
    }
    for field in ("tags", "defaultLanguage", "defaultAudioLanguage"):
        if field in before:
            snippet[field] = before[field]
    return {"id": video["id"], "snippet": snippet}


def self_check() -> None:
    sample = {"id": "video", "snippet": {
        "title": "old", "description": "keep", "categoryId": "25", "tags": ["keep"],
        "defaultLanguage": "en", "publishedAt": "read-only",
    }}
    assert update_body(sample, "new") == {"id": "video", "snippet": {
        "title": "new", "description": "keep", "categoryId": "25", "tags": ["keep"],
        "defaultLanguage": "en",
    }}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="perform the five title-only updates")
    args = parser.parse_args()

    gates = {video_id: audit_text(after) for video_id, (_, after) in REWRITES.items()}
    blocked = {video_id: report for video_id, report in gates.items() if report["verdict"] != "PASS"}
    if blocked:
        raise RuntimeError(f"style gate blocked rewrites: {blocked}")
    self_check()

    youtube = get_service()
    videos = public_videos(youtube)
    if len(videos) != 14:
        raise RuntimeError(f"expected exactly 14 public videos, found {len(videos)}")
    by_id = {video["id"]: video for video in videos}
    missing = sorted(set(REWRITES) - set(by_id))
    if missing:
        raise RuntimeError(f"target videos are not public: {missing}")

    changes = []
    for video_id, (expected_before, after) in REWRITES.items():
        actual_before = by_id[video_id]["snippet"]["title"]
        if actual_before != expected_before:
            raise RuntimeError(
                f"title drift for {video_id}: expected {expected_before!r}, found {actual_before!r}"
            )
        changes.append({
            "videoId": video_id,
            "url": f"https://youtu.be/{video_id}",
            "before": actual_before,
            "after": after,
            "styleGate": gates[video_id]["verdict"],
            "status": "planned" if args.apply else "dry-run",
        })

    gaps = []
    for video in videos:
        snippet, statistics = video["snippet"], video.get("statistics", {})
        description = snippet.get("description", "")
        comment_count = int(statistics.get("commentCount", 0))
        gaps.append({
            "videoId": video["id"],
            "url": f"https://youtu.be/{video['id']}",
            "title": snippet["title"],
            "emptyDescription": not description.strip(),
            "hasLandingLink": LANDING_URL in description,
            "commentCount": comment_count,
            "pinnedComment": False if comment_count == 0 else "not exposed by YouTube Data API",
        })

    receipt = {
        "schema": "tradercockpit-youtube-title-retitles/v1",
        "generatedAt": now(),
        "source": "social-ops/live-copy-rewrites-2026-07-20.md",
        "channelId": EXPECTED_CHANNEL_ID,
        "publicVideoCount": len(videos),
        "applyRequested": args.apply,
        "changes": changes,
        "descriptionAndPinnedCommentAudit": gaps,
    }
    write_receipt(receipt)
    if not args.apply:
        print(json.dumps(receipt, indent=2, ensure_ascii=False))
        return 0

    for change in changes:
        video_id = change["videoId"]
        video = by_id[video_id]
        mutable_before = update_body(video, change["before"])["snippet"]
        youtube.videos().update(
            part="snippet", body=update_body(video, change["after"])
        ).execute()
        readback = youtube.videos().list(part="snippet,status", id=video_id).execute()["items"][0]
        mutable_after = update_body(readback, readback["snippet"]["title"])["snippet"]
        change["readback"] = readback["snippet"]["title"]
        change["status"] = "applied" if change["readback"] == change["after"] else "readback-mismatch"
        change["nonTitleFieldsUnchanged"] = {
            field: mutable_before.get(field) == mutable_after.get(field)
            for field in set(mutable_before) | set(mutable_after)
            if field != "title"
        }
        change["visibilityUnchanged"] = readback["status"]["privacyStatus"] == video["status"]["privacyStatus"]
        change["verifiedAt"] = now()
        write_receipt(receipt)
        if change["status"] != "applied" or not all(change["nonTitleFieldsUnchanged"].values()) or not change["visibilityUnchanged"]:
            raise RuntimeError(f"read-back verification failed for {video_id}; see {RECEIPT}")

    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
