#!/usr/bin/env python3
"""TikTok Direct Post adapter with refreshable OAuth and provider read-back."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

try:
    from tools.credential_custody import credential_path
except ModuleNotFoundError:  # direct `python tools/upload_tiktok.py` execution
    from credential_custody import credential_path


OAUTH_URL = "https://open.tiktokapis.com/v2/oauth/token/"
CREATOR_INFO_URL = "https://open.tiktokapis.com/v2/post/publish/creator_info/query/"
DIRECT_POST_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"
CREDENTIAL_FILE = "tiktok-oauth.json"
PUBLIC_PRIVACY = "PUBLIC_TO_EVERYONE"
MIN_CHUNK = 5 * 1024 * 1024
UPLOAD_CHUNK = 32 * 1024 * 1024
MAX_VIDEO_SIZE = 4 * 1024 * 1024 * 1024


def _credential_file() -> Path:
    return credential_path(CREDENTIAL_FILE)


def _load_credentials() -> dict:
    path = _credential_file()
    if not path.is_file():
        raise FileNotFoundError(path)
    values = json.loads(path.read_text(encoding="utf-8"))
    required = {"client_key", "client_secret", "access_token", "refresh_token"}
    missing = sorted(required - values.keys())
    if missing:
        raise ValueError(f"TikTok OAuth credential is missing fields: {', '.join(missing)}")
    if "video.publish" not in str(values.get("scope", "")).split(","):
        raise ValueError("TikTok OAuth credential lacks video.publish scope")
    return values


def _save_credentials(values: dict) -> None:
    path = _credential_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(values, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _provider_json(response, action: str) -> dict:
    response.raise_for_status()
    payload = response.json()
    error = payload.get("error")
    if isinstance(error, str):
        raise RuntimeError(f"TikTok {action} failed: {error}")
    if isinstance(error, dict) and error.get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok {action} failed: {error.get('code')}")
    return payload


def _refresh_if_needed(credentials: dict, session, now: float) -> dict:
    expires_at = float(credentials.get("access_token_expires_at", 0))
    if expires_at > now + 600:
        return credentials
    refresh_expires_at = float(credentials.get("refresh_token_expires_at", 0))
    if refresh_expires_at and refresh_expires_at <= now:
        raise RuntimeError("TikTok refresh token is expired; authorization is required")
    response = session.post(
        OAUTH_URL,
        data={
            "client_key": credentials["client_key"],
            "client_secret": credentials["client_secret"],
            "grant_type": "refresh_token",
            "refresh_token": credentials["refresh_token"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    payload = _provider_json(response, "token refresh")
    if not payload.get("access_token") or not payload.get("refresh_token"):
        raise RuntimeError("TikTok token refresh returned no reusable token bundle")
    credentials.update({
        "access_token": payload["access_token"],
        "refresh_token": payload["refresh_token"],
        "access_token_expires_at": int(now) + int(payload.get("expires_in", 0)),
        "refresh_token_expires_at": int(now) + int(payload.get("refresh_expires_in", 0)),
        "open_id": payload.get("open_id", credentials.get("open_id")),
        "scope": payload.get("scope", credentials.get("scope")),
    })
    _save_credentials(credentials)
    return credentials


def refresh_auth(*, session=None, now=None) -> Path:
    """Silently refresh the operator-held TikTok token bundle if needed."""
    client = session or requests
    _refresh_if_needed(_load_credentials(), client, time.time() if now is None else now)
    return _credential_file()


def _authorized_credentials(session, now: float) -> dict:
    return _refresh_if_needed(_load_credentials(), session, now)


def _creator_info(session, credentials: dict) -> dict:
    response = session.post(
        CREATOR_INFO_URL,
        headers={
            "Authorization": f"Bearer {credentials['access_token']}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        timeout=30,
    )
    return _provider_json(response, "creator verification").get("data", {})


def probe_auth(user=None, *, session=None, now=None) -> dict:
    """Verify refreshable auth, provider read-back, and public-post eligibility."""
    del user  # retained only for compatibility with the retired cookie adapter
    client = session or requests
    clock = time.time() if now is None else now
    try:
        credentials = _authorized_credentials(client, clock)
        creator = _creator_info(client, credentials)
    except FileNotFoundError:
        return {"status": "absent", "ready": False, "readback": False}
    except OSError:
        return {"status": "custody-unavailable", "ready": False, "readback": False}
    except (ValueError, json.JSONDecodeError):
        return {"status": "credential-invalid", "ready": False, "readback": False}
    except (requests.RequestException, RuntimeError):
        return {"status": "verification-error", "ready": False, "readback": False}

    privacy = creator.get("privacy_level_options") or []
    is_public = PUBLIC_PRIVACY in privacy
    audit_approved = credentials.get("client_audit_status") == "approved"
    status = "valid" if is_public and audit_approved else (
        "private-only" if not is_public else "audit-required"
    )
    return {
        "status": status,
        "ready": status == "valid",
        "readback": True,
        "creatorUsername": creator.get("creator_username"),
        "privacyLevelOptions": privacy,
        "maxVideoPostDurationSec": creator.get("max_video_post_duration_sec"),
    }


def _chunk_plan(size: int) -> tuple[int, int]:
    if size <= 0:
        raise ValueError("TikTok video is empty")
    if size > MAX_VIDEO_SIZE:
        raise ValueError("TikTok video exceeds the 4 GB provider limit")
    if size <= 64 * 1024 * 1024:
        return size, 1
    chunk_size = UPLOAD_CHUNK
    return chunk_size, max(2, size // chunk_size)


def _upload_chunks(session, upload_url: str, path: Path, chunk_size: int, chunk_count: int) -> None:
    size = path.stat().st_size
    content_type = {
        ".mov": "video/quicktime",
        ".webm": "video/webm",
    }.get(path.suffix.lower(), "video/mp4")
    with path.open("rb") as source:
        offset = 0
        for index in range(chunk_count):
            length = chunk_size if index < chunk_count - 1 else size - offset
            data = source.read(length)
            if len(data) != length:
                raise RuntimeError("TikTok upload could not read the complete video chunk")
            response = session.put(
                upload_url,
                data=data,
                headers={
                    "Content-Type": content_type,
                    "Content-Length": str(length),
                    "Content-Range": f"bytes {offset}-{offset + length - 1}/{size}",
                },
                timeout=120,
            )
            response.raise_for_status()
            offset += length


def upload(
    video_path,
    title,
    user=None,
    ai_label: bool = True,
    *,
    privacy: str = PUBLIC_PRIVACY,
    session=None,
    sleep=time.sleep,
    now=None,
    max_polls: int = 120,
) -> dict:
    """Direct-post one approved video and return stable provider read-back evidence."""
    del user
    client = session or requests
    clock = time.time() if now is None else now
    path = Path(video_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if len(str(title).encode("utf-16-le")) // 2 > 2200:
        raise ValueError("TikTok caption exceeds the 2200 UTF-16-unit provider limit")
    if os.getenv("TIKTOK_AI_LABEL") is not None:
        ai_label = os.environ["TIKTOK_AI_LABEL"] == "1"

    credentials = _authorized_credentials(client, clock)
    if credentials.get("client_audit_status") != "approved":
        raise RuntimeError("TikTok public-posting audit is not recorded as approved")
    creator = _creator_info(client, credentials)
    privacy_options = creator.get("privacy_level_options") or []
    if privacy not in privacy_options:
        raise RuntimeError(f"TikTok creator does not currently allow {privacy}")

    size = path.stat().st_size
    chunk_size, chunk_count = _chunk_plan(size)
    headers = {
        "Authorization": f"Bearer {credentials['access_token']}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    init = _provider_json(client.post(
        DIRECT_POST_URL,
        headers=headers,
        json={
            "post_info": {
                "title": str(title),
                "privacy_level": privacy,
                "disable_comment": bool(creator.get("comment_disabled")),
                "disable_duet": bool(creator.get("duet_disabled")),
                "disable_stitch": bool(creator.get("stitch_disabled")),
                "brand_organic_toggle": True,
                "is_aigc": bool(ai_label),
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": size,
                "chunk_size": chunk_size,
                "total_chunk_count": chunk_count,
            },
        },
        timeout=30,
    ), "post initialization").get("data", {})
    publish_id, upload_url = init.get("publish_id"), init.get("upload_url")
    if not publish_id or not upload_url:
        raise RuntimeError("TikTok post initialization returned no publish ID or upload URL")
    _upload_chunks(client, upload_url, path, chunk_size, chunk_count)

    last_status = {}
    for _ in range(max_polls):
        last_status = _provider_json(client.post(
            STATUS_URL,
            headers=headers,
            json={"publish_id": publish_id},
            timeout=30,
        ), "post status").get("data", {})
        status = last_status.get("status")
        if status == "FAILED":
            raise RuntimeError(f"TikTok post processing failed: {last_status.get('fail_reason', 'unknown')}")
        if status == "PUBLISH_COMPLETE":
            ids = last_status.get("publicaly_available_post_id") or []
            if ids:
                post_id = str(ids[0])
                username = quote(str(creator.get("creator_username") or ""), safe="._-")
                url = f"https://www.tiktok.com/@{username}/video/{post_id}"
                return {
                    "status": "published",
                    "id": post_id,
                    "url": url,
                    "platformResponse": {
                        "publishId": publish_id,
                        "readback": {"id": post_id, "status": status},
                    },
                }
            break
        sleep(5)
    return {
        "status": "uploaded-unverified",
        "id": None,
        "url": None,
        "platformResponse": {
            "publishId": publish_id,
            "readback": {"id": None, "status": last_status.get("status", "timeout")},
        },
    }


if __name__ == "__main__":
    result = probe_auth()
    print(f"TikTok API readiness: {result['status']}")
    raise SystemExit(0 if result["ready"] else 1)
