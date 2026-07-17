#!/usr/bin/env python3
"""Collect source-backed weekly social analytics without exposing credentials.

Commands:
  python tools/social_analytics.py auth-youtube
  python tools/social_analytics.py collect

Use OpenMontage/.venv/Scripts/python.exe so the Google client libraries resolve.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests
from dotenv import dotenv_values


ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
ENV_FILE = ROOT / "OpenMontage" / ".env"
try:
    from tools.credential_custody import credential_path
except ModuleNotFoundError:  # direct `python tools/social_analytics.py` execution
    from credential_custody import credential_path

TOKEN_FILE = credential_path("token.json")
CLIENT_FILE = credential_path("client_secret.json")
SNAPSHOT_FILE = ROOT / "social-ops" / "analytics-latest.json"
HISTORY_FILE = ROOT / "social-ops" / "analytics-history.json"
PUBLISH_LOG = ROOT / "OpenMontage" / "projects" / "video-03-war-premium-derivatives" / "artifacts" / "publish_log.json"
GRAPH = "https://graph.facebook.com/v25.0"
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_error(error: Exception | str) -> str:
    """Keep actionable error text while refusing token-bearing URLs."""
    text = str(error).replace("\r", " ").replace("\n", " ")
    if "access_token=" in text:
        text = text.split("access_token=", 1)[0] + "access_token=<redacted>"
    return text[:300]


def google_error(error: Exception) -> tuple[str, str | None]:
    try:
        payload = json.loads(error.content)
        detail = payload.get("error", {})
        reasons = [item.get("reason") for item in detail.get("errors", []) if item.get("reason")]
        return str(detail.get("message") or safe_error(error))[:300], reasons[0] if reasons else None
    except Exception:
        return safe_error(error), None


def graph_get(path: str, token: str, **params: Any) -> dict[str, Any]:
    response = requests.get(
        f"{GRAPH}/{path.lstrip('/')}",
        params={**params, "access_token": token},
        timeout=30,
    )
    data = response.json()
    if "error" in data:
        raise RuntimeError(data["error"].get("message", "Meta Graph API error"))
    return data


def metric_value(item: dict[str, Any]) -> Any:
    values = item.get("values") or []
    if values:
        return values[0].get("value")
    return item.get("value")


def collect_facebook(env: dict[str, str | None]) -> dict[str, Any]:
    page_id, token = env.get("META_PAGE_ID"), env.get("META_PAGE_TOKEN")
    if not page_id or not token:
        return {"status": "missing_credentials", "posts": []}
    try:
        page = graph_get(str(page_id), str(token), fields="id,name,followers_count,fan_count")
        videos = graph_get(
            f"{page_id}/videos",
            str(token),
            fields="id,title,description,created_time,permalink_url,length,views",
            limit=25,
        ).get("data", [])
        posts = []
        for video in videos:
            insights = graph_get(f"{video['id']}/video_insights", str(token), limit=100).get("data", [])
            metrics = {item.get("name"): metric_value(item) for item in insights if item.get("name")}
            plays = metrics.get("fb_reels_total_plays")
            if plays is None:
                plays = metrics.get("blue_reels_play_count", video.get("views"))
            reactions = metrics.get("post_video_likes_by_reaction_type") or {}
            social = metrics.get("post_video_social_actions") or {}
            permalink = video.get("permalink_url") or f"/reel/{video.get('id')}"
            if permalink.startswith("/"):
                permalink = f"https://www.facebook.com{permalink}"
            posts.append({
                "id": video.get("id"),
                "title": video.get("title") or (video.get("description") or "Untitled video").splitlines()[0][:140],
                "createdAt": video.get("created_time"),
                "url": permalink,
                "views": plays,
                "uniqueImpressions": metrics.get("post_impressions_unique"),
                "replays": metrics.get("fb_reels_replay_count"),
                "averageWatchMs": metrics.get("post_video_avg_time_watched"),
                "watchTimeMs": metrics.get("post_video_view_time"),
                "followers": metrics.get("post_video_followers"),
                "likes": sum(v for v in reactions.values() if isinstance(v, (int, float))) if isinstance(reactions, dict) else None,
                "comments": social.get("COMMENT") if isinstance(social, dict) else None,
                "shares": social.get("SHARE") if isinstance(social, dict) else None,
            })
        return {
            "status": "ready",
            "fetchedAt": iso_now(),
            "account": page.get("name"),
            "followers": page.get("followers_count"),
            "fans": page.get("fan_count"),
            "posts": posts,
        }
    except Exception as error:
        return {"status": "error", "error": safe_error(error), "posts": []}


def collect_instagram(env: dict[str, str | None]) -> dict[str, Any]:
    user_id, token = env.get("META_IG_USER_ID"), env.get("META_PAGE_TOKEN")
    if not user_id or not token:
        return {"status": "missing_credentials", "posts": []}
    try:
        account = graph_get(str(user_id), str(token), fields="id,username,followers_count,media_count")
        media = graph_get(
            f"{user_id}/media",
            str(token),
            fields="id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count",
            limit=25,
        ).get("data", [])
        posts = []
        metrics_request = "views,reach,likes,comments,saved,shares,total_interactions,ig_reels_avg_watch_time,ig_reels_video_view_total_time"
        for item in media:
            metrics: dict[str, Any] = {}
            if item.get("media_product_type") == "REELS":
                payload = graph_get(f"{item['id']}/insights", str(token), metric=metrics_request)
                metrics = {entry.get("name"): metric_value(entry) for entry in payload.get("data", []) if entry.get("name")}
            posts.append({
                "id": item.get("id"),
                "title": (item.get("caption") or "Untitled post").splitlines()[0][:140],
                "createdAt": item.get("timestamp"),
                "url": item.get("permalink"),
                "type": item.get("media_product_type") or item.get("media_type"),
                "views": metrics.get("views"),
                "reach": metrics.get("reach"),
                "likes": metrics.get("likes", item.get("like_count")),
                "comments": metrics.get("comments", item.get("comments_count")),
                "saves": metrics.get("saved"),
                "shares": metrics.get("shares"),
                "interactions": metrics.get("total_interactions"),
                "averageWatchMs": metrics.get("ig_reels_avg_watch_time"),
                "watchTimeMs": metrics.get("ig_reels_video_view_total_time"),
            })
        return {
            "status": "ready",
            "fetchedAt": iso_now(),
            "account": f"@{account.get('username')}" if account.get("username") else None,
            "followers": account.get("followers_count"),
            "mediaCount": account.get("media_count"),
            "posts": posts,
        }
    except Exception as error:
        return {"status": "error", "error": safe_error(error), "posts": []}


def token_scopes() -> set[str]:
    if not TOKEN_FILE.exists():
        return set()
    try:
        return set(json.loads(TOKEN_FILE.read_text(encoding="utf-8")).get("scopes") or [])
    except (OSError, json.JSONDecodeError):
        return set()


def auth_youtube() -> None:
    if not CLIENT_FILE.exists():
        raise SystemExit(f"Missing {CLIENT_FILE}")
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_FILE, YOUTUBE_SCOPES)
    credentials = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    print("YouTube analytics authorization saved; scopes:")
    for scope in sorted(credentials.scopes or YOUTUBE_SCOPES):
        print(f"- {scope}")


def table_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    headers = [header["name"] for header in payload.get("columnHeaders", [])]
    return [dict(zip(headers, row)) for row in payload.get("rows", [])]


def youtube_data_posts(youtube: Any, channel: dict[str, Any]) -> list[dict[str, Any]]:
    uploads = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
    if not uploads:
        return []
    ids: list[str] = []
    token = None
    while len(ids) < 50:
        payload = youtube.playlistItems().list(
            part="contentDetails", playlistId=uploads, maxResults=min(50, 50 - len(ids)), pageToken=token,
        ).execute()
        ids.extend(item.get("contentDetails", {}).get("videoId") for item in payload.get("items", []))
        ids = [value for value in ids if value]
        token = payload.get("nextPageToken")
        if not token:
            break
    if not ids:
        return []
    items = youtube.videos().list(
        part="snippet,statistics,contentDetails", id=",".join(ids), maxResults=50,
    ).execute().get("items", [])
    posts = []
    for item in items:
        stats = item.get("statistics", {})
        posts.append({
            "id": item.get("id"),
            "title": item.get("snippet", {}).get("title") or item.get("id"),
            "createdAt": item.get("snippet", {}).get("publishedAt"),
            "url": f"https://youtu.be/{item.get('id')}",
            "duration": item.get("contentDetails", {}).get("duration"),
            "views": int(stats.get("viewCount", 0)) if stats.get("viewCount") else 0,
            "likes": int(stats.get("likeCount", 0)) if stats.get("likeCount") else 0,
            "comments": int(stats.get("commentCount", 0)) if stats.get("commentCount") else 0,
        })
    return posts


def collect_youtube(start_date: str, end_date: str) -> dict[str, Any]:
    missing = set(YOUTUBE_SCOPES) - token_scopes()
    if missing:
        return {
            "status": "needs_authorization",
            "missingScopes": sorted(missing),
            "action": "OpenMontage/.venv/Scripts/python.exe tools/social_analytics.py auth-youtube",
            "posts": [],
            "daily": [],
        }
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, YOUTUBE_SCOPES)
        if not credentials.valid and credentials.refresh_token:
            credentials.refresh(Request())
            TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
        youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        analytics = build("youtubeAnalytics", "v2", credentials=credentials, cache_discovery=False)
        channel_items = youtube.channels().list(part="snippet,statistics,contentDetails", mine=True).execute().get("items", [])
        if not channel_items:
            raise RuntimeError("Authorized Google account has no YouTube channel")
        channel = channel_items[0]
        data_posts = youtube_data_posts(youtube, channel)
        metrics = "views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,subscribersGained,subscribersLost,likes,comments,shares"
        analytics_error = None
        analytics_reason = None
        try:
            daily_payload = analytics.reports().query(
                ids="channel==MINE", startDate=start_date, endDate=end_date,
                metrics=metrics, dimensions="day", sort="day",
            ).execute()
            video_payload = analytics.reports().query(
                ids="channel==MINE", startDate=start_date, endDate=end_date,
                metrics=metrics, dimensions="video", sort="-views", maxResults=50,
            ).execute()
        except Exception as error:
            analytics_error, analytics_reason = google_error(error)
            daily_payload, video_payload = {}, {}
        video_rows = table_rows(video_payload)
        video_ids = [str(row["video"]) for row in video_rows]
        titles: dict[str, dict[str, Any]] = {}
        if video_ids:
            items = youtube.videos().list(
                part="snippet,statistics", id=",".join(video_ids[:50]), maxResults=50
            ).execute().get("items", [])
            titles = {item["id"]: item for item in items}
        posts = []
        for row in video_rows:
            video_id = str(row.pop("video"))
            item = titles.get(video_id, {})
            posts.append({
                "id": video_id,
                "title": item.get("snippet", {}).get("title") or video_id,
                "createdAt": item.get("snippet", {}).get("publishedAt"),
                "url": f"https://youtu.be/{video_id}",
                **row,
            })
        daily = table_rows(daily_payload)
        totals = {name: 0 for name in metrics.split(",")}
        weighted_views = 0
        for row in daily:
            for name in totals:
                value = row.get(name)
                if name in {"averageViewDuration", "averageViewPercentage"}:
                    continue
                if isinstance(value, (int, float)):
                    totals[name] += value
            views = row.get("views") or 0
            weighted_views += views
            for name in ("averageViewDuration", "averageViewPercentage"):
                if isinstance(row.get(name), (int, float)):
                    totals[name] += row[name] * views
        if weighted_views:
            totals["averageViewDuration"] /= weighted_views
            totals["averageViewPercentage"] /= weighted_views
        if analytics_error:
            period_start = datetime.fromisoformat(start_date).date()
            period_end = datetime.fromisoformat(end_date).date()
            period_posts = []
            for post in data_posts:
                try:
                    published = datetime.fromisoformat(post["createdAt"].replace("Z", "+00:00")).date()
                except (AttributeError, TypeError, ValueError):
                    continue
                if period_start <= published <= period_end:
                    period_posts.append(post)
            totals["views"] = sum(post.get("views", 0) for post in period_posts)
            totals["likes"] = sum(post.get("likes", 0) for post in period_posts)
            totals["comments"] = sum(post.get("comments", 0) for post in period_posts)
            posts = data_posts
        stats = channel.get("statistics", {})
        return {
            "status": "partial" if analytics_error else "ready",
            "fetchedAt": iso_now(),
            "account": channel.get("snippet", {}).get("title"),
            "channelId": channel.get("id"),
            "subscribers": int(stats.get("subscriberCount", 0)) if stats.get("subscriberCount") else None,
            "channelViews": int(stats.get("viewCount", 0)) if stats.get("viewCount") else None,
            "videoCount": int(stats.get("videoCount", 0)) if stats.get("videoCount") else None,
            "weekly": totals,
            "daily": daily,
            "posts": posts,
            "measurement": "publication-window lifetime counters" if analytics_error else "YouTube Analytics reporting window",
            "analyticsError": analytics_error,
            "analyticsReason": analytics_reason,
            "analyticsAction": (
                "https://console.developers.google.com/apis/api/youtubeanalytics.googleapis.com/overview?project=462706233859"
                if analytics_reason == "accessNotConfigured" else None
            ),
        }
    except Exception as error:
        return {"status": "error", "error": safe_error(error), "posts": [], "daily": []}


def collect_tiktok() -> dict[str, Any]:
    script = TOOLS / "tiktok_analytics_cdp.cjs"
    try:
        result = subprocess.run(
            ["node", str(script)], cwd=ROOT, capture_output=True, text=True, timeout=45,
        )
        payload = json.loads(result.stdout or "{}")
        if not payload:
            raise RuntimeError(result.stderr or "TikTok collector returned no data")
        return payload
    except Exception as error:
        return {"status": "unavailable", "error": safe_error(error), "posts": []}


def numeric(value: Any) -> float:
    return float(value) if isinstance(value, (int, float)) else 0.0


def source_total(source: dict[str, Any], key: str = "views") -> int:
    return int(sum(numeric(post.get(key)) for post in source.get("posts", [])))


def make_decisions(sources: dict[str, dict[str, Any]], has_prior: bool) -> list[dict[str, str]]:
    decisions: list[dict[str, str]] = []
    youtube = sources["youtube"]
    if youtube.get("status") == "needs_authorization":
        decisions.append({
            "priority": "blocking", "title": "Finish YouTube analytics consent",
            "evidence": "The cached token can upload but cannot read channel or retention analytics.",
            "action": youtube["action"],
        })
    elif youtube.get("status") == "partial" and youtube.get("analyticsAction"):
        decisions.append({
            "priority": "setup", "title": "Enable YouTube retention reporting",
            "evidence": "YouTube read access works, but the Google project has the YouTube Analytics API disabled.",
            "action": youtube["analyticsAction"],
        })
    elif youtube.get("status") == "ready":
        retention = numeric(youtube.get("weekly", {}).get("averageViewPercentage"))
        if retention and retention < 35:
            decisions.append({
                "priority": "test", "title": "Tighten the first 15 seconds",
                "evidence": f"YouTube average percentage viewed is {retention:.1f}% for the reporting window.",
                "action": "Test a shorter cold open and move the pressure-chain payoff before the first chart transition.",
            })
    tiktok = sources["tiktok"]
    public_posts = [post for post in tiktok.get("posts", []) if post.get("privacy") == "Everyone"]
    if len(public_posts) >= 2:
        ranked = sorted(public_posts, key=lambda post: numeric(post.get("views")), reverse=True)
        if numeric(ranked[0].get("views")) >= max(10, numeric(ranked[1].get("views")) * 2):
            decisions.append({
                "priority": "repeat", "title": "Reuse the winning TikTok hook structure",
                "evidence": f"“{ranked[0].get('title', '')[:72]}” leads the next post by more than 2× on views.",
                "action": "Keep the same immediate consequence-first setup, but apply it to the next verified market transmission chain.",
            })
    if not has_prior:
        decisions.append({
            "priority": "baseline", "title": "Treat this as baseline week",
            "evidence": "Meta and TikTok expose lifetime counters; one scheduled follow-up is required before weekly deltas are trustworthy.",
            "action": "Do not overfit to one snapshot. Compare the same counters at the next weekly review before changing cadence.",
        })
    if not decisions:
        decisions.append({
            "priority": "hold", "title": "Hold the format until the next weekly delta",
            "evidence": "No connected metric crossed a predefined action threshold.",
            "action": "Keep cadence and change only one hook variable in the next batch.",
        })
    return decisions[:4]


def load_history() -> list[dict[str, Any]]:
    try:
        value = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return value if isinstance(value, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def collect() -> dict[str, Any]:
    today = datetime.now().date()
    end = today - timedelta(days=1)
    start = end - timedelta(days=6)
    env = {key: value for key, value in dotenv_values(ENV_FILE).items()}
    # Meta creds live in operator custody, not the repo; absent file = absent creds
    meta_env = credential_path("meta.env")
    if meta_env.is_file():
        env.update(dotenv_values(meta_env))
    sources = {
        "youtube": collect_youtube(start.isoformat(), end.isoformat()),
        "facebook": collect_facebook(env),
        "instagram": collect_instagram(env),
        "tiktok": collect_tiktok(),
    }
    history = load_history()
    prior = next((item for item in reversed(history) if item.get("window", {}).get("end") != end.isoformat()), None)
    snapshot = {
        "schema": "tradercockpit-social-analytics/v1",
        "generatedAt": iso_now(),
        "window": {"start": start.isoformat(), "end": end.isoformat(), "timezone": "Asia/Bangkok"},
        "sources": sources,
        "rollup": {
            "youtubeWeeklyViews": int(numeric(sources["youtube"].get("weekly", {}).get("views"))),
            "facebookObservedViews": source_total(sources["facebook"]),
            "instagramObservedViews": source_total(sources["instagram"]),
            "tiktokObservedViews": source_total(sources["tiktok"]),
            "connectedSources": sum(source.get("status") in {"ready", "partial"} for source in sources.values()),
        },
        "priorSnapshotAt": prior.get("generatedAt") if prior else None,
        "decisions": make_decisions(sources, prior is not None),
        "caveats": [
            "YouTube reporting can lag the most recent days; the requested end date is yesterday.",
            "Facebook, Instagram, and TikTok post counters are point-in-time observations. Weekly deltas become comparable after the next scheduled snapshot.",
            "No credentials, access tokens, client secrets, or cookies are written into this artifact.",
        ],
    }
    SNAPSHOT_FILE.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    history = [item for item in history if item.get("window", {}).get("end") != end.isoformat()]
    history.append(snapshot)
    HISTORY_FILE.write_text(json.dumps(history[-104:], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["auth-youtube", "collect"])
    args = parser.parse_args()
    if args.command == "auth-youtube":
        auth_youtube()
        return
    snapshot = collect()
    statuses = ", ".join(f"{name}={source['status']}" for name, source in snapshot["sources"].items())
    print(f"wrote {SNAPSHOT_FILE}")
    print(statuses)


if __name__ == "__main__":
    main()
