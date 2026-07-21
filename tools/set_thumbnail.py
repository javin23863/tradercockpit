"""Set (or replace) the thumbnail on an existing YouTube video, with read-back.

Usage:
    python tools/set_thumbnail.py <videoId> <thumbnail.png>

The repackaging half of the 2026-07-21 thumbnail fix: publish.py now sets
thumbnails at upload time; this covers videos that went live before the fix.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from upload_youtube import get_service  # noqa: E402


def set_thumbnail(video_id, thumbnail):
    from googleapiclient.http import MediaFileUpload

    if not Path(thumbnail).is_file():
        raise SystemExit(f"thumbnail not found: {thumbnail}")
    youtube = get_service(interactive=False)
    youtube.thumbnails().set(
        videoId=video_id, media_body=MediaFileUpload(thumbnail)
    ).execute()
    readback = youtube.videos().list(part="snippet", id=video_id).execute()
    items = readback.get("items") or []
    if len(items) != 1 or items[0].get("id") != video_id:
        raise SystemExit("read-back did not return the video")
    url = items[0]["snippet"]["thumbnails"].get("high", {}).get("url")
    print(f"thumbnail set on {video_id}; read-back high: {url}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    set_thumbnail(sys.argv[1], sys.argv[2])
