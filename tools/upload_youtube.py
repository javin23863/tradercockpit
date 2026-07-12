#!/usr/bin/env python3
"""Upload a video to YouTube via the Data API v3.

One-time setup: put OAuth client_secret.json next to this script (see COMPLEMENTS.md).
First run opens a browser for consent; token cached in token.json.

Usage:
  python upload_youtube.py video.mp4 --title "My Video" --description "..." \
      --tags tag1 tag2 --privacy unlisted --thumbnail thumb.png
"""
import argparse
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
HERE = Path(__file__).parent


def get_service():
    creds = None
    token = HERE / "token.json"
    if token.exists():
        creds = Credentials.from_authorized_user_file(token, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret = HERE / "client_secret.json"
            if not secret.exists():
                sys.exit(f"Missing {secret} — see COMPLEMENTS.md for the 5-minute Google Cloud setup.")
            creds = InstalledAppFlow.from_client_secrets_file(secret, SCOPES).run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(video, title, description="", tags=None, category="22", privacy="private", thumbnail=None):
    """Upload one video; returns the YouTube URL."""
    yt = get_service()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category,
        },
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(video, chunksize=8 * 1024 * 1024, resumable=True)
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"  {int(status.progress() * 100)}%", flush=True)
    video_id = response["id"]
    print(f"Uploaded: https://youtu.be/{video_id}")

    if thumbnail:
        yt.thumbnails().set(videoId=video_id, media_body=MediaFileUpload(thumbnail)).execute()
        print("Thumbnail set.")
    return f"https://youtu.be/{video_id}"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("video")
    p.add_argument("--title", required=True)
    p.add_argument("--description", default="")
    p.add_argument("--tags", nargs="*", default=[])
    p.add_argument("--category", default="22", help="YouTube category id (22=People & Blogs, 27=Education, 28=Sci/Tech)")
    p.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    p.add_argument("--thumbnail", help="optional PNG/JPG thumbnail")
    args = p.parse_args()
    upload(args.video, args.title, args.description, args.tags, args.category, args.privacy, args.thumbnail)


if __name__ == "__main__":
    main()
