#!/usr/bin/env python3
"""Operator-only YouTube uploader with channel and post read-back checks."""

import argparse
from pathlib import Path

try:
    from tools.credential_custody import credential_path
except ModuleNotFoundError:  # direct `python tools/upload_youtube.py` execution
    from credential_custody import credential_path


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
EXPECTED_CHANNEL_ID = "UCBc6RR49Qk5vtDQaw8BjH3A"


def _google():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    return Request, Credentials, InstalledAppFlow, build


def _authenticate(interactive=False):
    token = credential_path("token.json")
    try:
        token_exists = token.is_file()
    except OSError:
        token_exists = False
    if not token_exists and not interactive:
        return {"status": "absent", "ready": False, "channelId": None}, None

    Request, Credentials, InstalledAppFlow, build = _google()
    prior_status = "valid"
    try:
        credentials = Credentials.from_authorized_user_file(token, SCOPES) if token_exists else None
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                token.write_text(credentials.to_json(), encoding="utf-8")
                prior_status = "refreshable-expired"
            elif interactive:
                secret = credential_path("client_secret.json")
                if not secret.is_file():
                    return {"status": "absent", "ready": False, "channelId": None}, None
                credentials = InstalledAppFlow.from_client_secrets_file(secret, SCOPES).run_local_server(port=0)
                token.write_text(credentials.to_json(), encoding="utf-8")
            else:
                return {"status": "revoked", "ready": False, "channelId": None}, None
        youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        response = youtube.channels().list(part="id", mine=True).execute()
    except Exception as error:
        status = "revoked" if token_exists else "absent"
        return {"status": status, "ready": False, "channelId": None, "error": str(error)}, None

    items = response.get("items") or []
    channel_id = items[0].get("id") if len(items) == 1 else None
    if channel_id != EXPECTED_CHANNEL_ID:
        return {
            "status": "channel-mismatch",
            "ready": False,
            "channelId": channel_id,
            "expectedChannelId": EXPECTED_CHANNEL_ID,
        }, None
    return {"status": prior_status, "ready": True, "channelId": channel_id}, youtube


def probe_auth():
    """Return absent/refreshable-expired/revoked/valid plus expected-channel proof."""
    return _authenticate(interactive=False)[0]


def get_service(interactive=False):
    probe, youtube = _authenticate(interactive=interactive)
    if not probe["ready"]:
        raise RuntimeError(f"YouTube authentication blocked: {probe['status']}")
    return youtube


def upload(video, title, description="", tags=None, category="22", privacy="private", thumbnail=None,
           synthetic=False, interactive=False):
    """Upload one video and return only after the inserted ID is read back."""
    from googleapiclient.http import MediaFileUpload

    youtube = get_service(interactive=interactive)
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
            "containsSyntheticMedia": bool(synthetic),
        },
    }
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(video, chunksize=8 * 1024 * 1024, resumable=True),
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  {int(status.progress() * 100)}%", flush=True)
    video_id = response.get("id")
    readback = youtube.videos().list(part="id,status,snippet", id=video_id).execute()
    items = readback.get("items") or []
    if not video_id or len(items) != 1 or items[0].get("id") != video_id:
        raise RuntimeError("YouTube upload returned no matching read-back video")

    if thumbnail:
        youtube.thumbnails().set(
            videoId=video_id, media_body=MediaFileUpload(thumbnail)
        ).execute()
    return {
        "status": "published",
        "id": video_id,
        "url": f"https://youtu.be/{video_id}",
        "platformResponse": {"upload": response, "readback": readback},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", default="")
    parser.add_argument("--tags", nargs="*", default=[])
    parser.add_argument("--category", default="22")
    parser.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    parser.add_argument("--thumbnail")
    parser.add_argument("--synthetic", action="store_true")
    args = parser.parse_args()
    result = upload(
        str(args.video), args.title, args.description, args.tags, args.category,
        args.privacy, args.thumbnail, args.synthetic, interactive=True,
    )
    print(result["url"])


if __name__ == "__main__":
    main()
