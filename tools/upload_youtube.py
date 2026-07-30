#!/usr/bin/env python3
"""Operator-only YouTube uploader with channel and post read-back checks."""

import argparse
from pathlib import Path

try:
    from tools.credential_custody import credential_path
    from tools import episode_gate
except ImportError:  # direct `python tools/upload_youtube.py` execution
    from credential_custody import credential_path
    import episode_gate


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
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


def _metadata_mismatches(item, expected):
    snippet = item.get("snippet") or {}
    status = item.get("status") or {}
    observed = {
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "tags": snippet.get("tags") or [],
        "categoryId": snippet.get("categoryId"),
        "privacyStatus": status.get("privacyStatus"),
        "selfDeclaredMadeForKids": status.get("selfDeclaredMadeForKids"),
        "containsSyntheticMedia": status.get("containsSyntheticMedia"),
    }
    return [key for key, value in expected.items() if observed.get(key) != value]


def upload(video, title, description="", tags=None, category="22", privacy="private", thumbnail=None,
           synthetic=False, interactive=False, approval_lane=None, approval_ref=None):
    """Upload one video and return only after the inserted ID is read back.

    A series master must carry a GREEN gate receipt whose sha256 matches THIS file. That check
    lives here rather than in a runbook because a runbook is a thing a tired agent skips: ep03
    and ep04 were mastered by hand while `ai_tell_gate` was red, and nothing between the gate
    and the upload could tell. There is deliberately no override flag -- a bypass everyone
    knows about is not a gate. Clear the red or record an operator waiver.

    `approval_lane` is mandatory. Series uploads must stay under OpenMontage/projects and carry
    an exact episode receipt. Daily/social uploads reach this function only after publish.py has
    validated their exact-hash social batch.
    """
    caption_root = caption_contract = None
    if approval_lane == "series":
        if episode_gate.verify_release(
            Path(video),
            title=title,
            description=description,
            tags=tags,
            category=category,
            privacy=privacy,
            thumbnail=thumbnail,
            synthetic=synthetic,
        ) != 0:
            raise SystemExit(f"BLOCKED: {video} is not certified. Run:\n"
                             f"  py tools/episode_gate.py run <episode-dir> --master {video}")
        caption_root, caption_contract = episode_gate.read_release_receipt(Path(video))
    elif approval_lane == "social_batch":
        if not isinstance(approval_ref, dict):
            raise SystemExit("BLOCKED: social_batch uploads require an approval_ref")
        try:
            try:
                from tools import publish as publish_gate
            except ImportError:
                import publish as publish_gate
            batch, item = publish_gate.load_live_item(
                approval_ref["batch"], approval_ref["item_id"], "youtube"
            )
            approved_asset = publish_gate._asset(item)
            approved_thumbnail = publish_gate._thumbnail(item)
        except (KeyError, OSError, TypeError, ValueError) as exc:
            raise SystemExit(f"BLOCKED: invalid social_batch approval_ref: {exc}") from exc
        requested_thumbnail = str(Path(thumbnail).resolve()) if thumbnail else None
        social_values = {
            "asset": Path(video).resolve() == approved_asset,
            "title": title == item["title"],
            "description": description == item["copy"],
            "tags": (tags or []) == [],
            "category": str(category) == "22",
            "privacy": privacy == item["privacy"],
            "thumbnail": requested_thumbnail == approved_thumbnail,
            "synthetic": bool(synthetic) == bool(batch.get("containsSyntheticMedia", False)),
        }
        drift = sorted(key for key, matches in social_values.items() if not matches)
        if drift:
            raise SystemExit("BLOCKED: upload differs from social_batch approval: " +
                             ", ".join(drift))
        caption_root = publish_gate.ROOT
        caption_contract = {
            "captions": item["captions"],
            "captionLanguage": item["captionLanguage"],
            "captionName": item["captionName"],
        }
    else:
        raise SystemExit("BLOCKED: approval_lane must be 'series' or the validated "
                         "'social_batch' path in tools/publish.py")

    from googleapiclient.http import MediaFileUpload

    youtube = get_service(interactive=interactive)
    target_status = {
        "privacyStatus": privacy,
        "selfDeclaredMadeForKids": False,
        "containsSyntheticMedia": bool(synthetic),
    }
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": str(category),
        },
        "status": {**target_status, "privacyStatus": "private"},
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
    mismatches = _metadata_mismatches(items[0], {**body["snippet"], **body["status"]})
    if mismatches:
        raise RuntimeError("YouTube read-back differs from upload: " + ", ".join(mismatches))

    caption_response = caption_readback = None
    if caption_contract:
        caption_body = {
            "snippet": {
                "videoId": video_id,
                "language": caption_contract["captionLanguage"],
                "name": caption_contract["captionName"],
                "isDraft": False,
            }
        }
        caption_response = youtube.captions().insert(
            part="snippet",
            body=caption_body,
            media_body=MediaFileUpload(str(caption_root / caption_contract["captions"])),
        ).execute()
        caption_id = caption_response.get("id")
        caption_readback = youtube.captions().list(
            part="id,snippet", videoId=video_id, id=caption_id
        ).execute()
        caption_items = caption_readback.get("items") or []
        if len(caption_items) != 1 or caption_items[0].get("id") != caption_id:
            raise RuntimeError("YouTube caption upload returned no matching read-back track")
        caption_snippet = caption_items[0].get("snippet") or {}
        caption_mismatches = [
            key for key, value in caption_body["snippet"].items()
            if caption_snippet.get(key) != value
        ]
        if caption_mismatches:
            raise RuntimeError(
                "YouTube caption read-back differs from upload: " +
                ", ".join(caption_mismatches)
            )
        downloaded_captions = youtube.captions().download(id=caption_id).execute()
        caption_bytes = (caption_root / caption_contract["captions"]).read_bytes()
        if downloaded_captions != caption_bytes:
            raise RuntimeError("YouTube caption download differs from the certified SRT")

    thumbnail_response = None
    if thumbnail:
        thumbnail_response = youtube.thumbnails().set(
            videoId=video_id, media_body=MediaFileUpload(thumbnail)
        ).execute()
        if not (thumbnail_response.get("items") or []):
            raise RuntimeError("YouTube thumbnail upload returned no thumbnail read-back")

    promotion_response = None
    final_readback = None
    try:
        if privacy != "private":
            promotion_response = youtube.videos().update(
                part="status",
                body={"id": video_id, "status": target_status},
            ).execute()
        final_readback = youtube.videos().list(
            part="id,status,snippet,contentDetails", id=video_id
        ).execute()
        final_items = final_readback.get("items") or []
        final_mismatches = (
            ["id"] if len(final_items) != 1 or final_items[0].get("id") != video_id
            else _metadata_mismatches(final_items[0], {**body["snippet"], **target_status})
        )
        if thumbnail and final_items and not (
            final_items[0].get("contentDetails") or {}
        ).get("hasCustomThumbnail"):
            final_mismatches.append("thumbnail")
        if final_mismatches:
            raise RuntimeError(
                "YouTube final read-back differs from certification: " +
                ", ".join(sorted(set(final_mismatches)))
            )
    except Exception as error:
        if privacy != "private":
            try:
                youtube.videos().update(
                    part="status",
                    body={"id": video_id, "status": {
                        **target_status, "privacyStatus": "private"
                    }},
                ).execute()
                rollback = youtube.videos().list(
                    part="id,status", id=video_id
                ).execute()
                rollback_items = rollback.get("items") or []
                if (len(rollback_items) != 1 or
                        (rollback_items[0].get("status") or {}).get("privacyStatus") != "private"):
                    raise RuntimeError("private rollback did not read back")
            except Exception as rollback_error:
                raise RuntimeError(
                    f"YouTube video {video_id} public-state UNKNOWN after failed promotion; "
                    f"rollback also failed: {rollback_error}"
                ) from error
        raise
    return {
        "status": "published",
        "id": video_id,
        "url": f"https://youtu.be/{video_id}",
        "platformResponse": {
            "upload": response,
            "initialReadback": readback,
            "readback": final_readback,
            "captions": caption_response,
            "captionsReadback": caption_readback,
            "captionsContentVerified": bool(caption_contract),
            "thumbnail": thumbnail_response,
            "privacyPromotion": promotion_response,
        },
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
        args.privacy, args.thumbnail, args.synthetic, interactive=True, approval_lane="series",
    )
    print(result["url"])


if __name__ == "__main__":
    main()
