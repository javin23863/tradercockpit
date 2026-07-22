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
VELOCITY_LOG = ROOT / "social-ops" / "velocity-log.jsonl"
VELOCITY_FILE = ROOT / "social-ops" / "velocity-latest.json"
HOTDOG_FILE = ROOT / "social-ops" / "failure-mode-demand.json"
DRIVERS_FILE = ROOT / "social-ops" / "post-drivers.json"
REPORTS_DIR = ROOT / "social-ops" / "weekly"
PUBLISH_LOG = ROOT / "OpenMontage" / "projects" / "video-03-war-premium-derivatives" / "artifacts" / "publish_log.json"
GRAPH = "https://graph.facebook.com/v25.0"
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]
FAILURE_PHRASES = (
    "why my strategy stopped working",
    "my backtest lied",
    "overfitting",
    "curve fitting",
    "walk-forward vs holdout",
    "why backtests fail",
    "I lost money trading",
    "strategy died",
    "data mining bias",
    "out of sample failure",
)
NICHE_TERMS = (
    "trading", "trader", "backtest", "market", "stock", "forex", "futures",
    "crypto", "options", "quant", "algorithmic", "prop firm",
)
FAILURE_TITLE_TERMS = (
    "stopped working", "backtest", "overfit", "curve fit", "walk-forward", "walk forward",
    "holdout", "lost", "strategy died", "data mining", "out of sample", "alpha decay",
    "survivorship", "slippage", "execution cost", "transaction cost", "market impact",
)
SHOW_BIBLE_TERMS = {
    "overfitting": ("overfit", "curve fit", "walk-forward", "walk forward", "holdout", "data mining", "out of sample"),
    "survivorship": ("survivorship",),
    "execution-cost erosion": ("execution cost", "transaction cost", "slippage", "commission", "fees", "spread"),
    "alpha decay": ("alpha decay", "edge decay", "stopped working", "stopped performing", "strategy died"),
    "size-sensitivity": ("size sensitivity", "capacity", "market impact", "liquidity constraint"),
}


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


def youtube_credentials(*, allow_refresh: bool = True) -> Any:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    credentials = Credentials.from_authorized_user_file(TOKEN_FILE, YOUTUBE_SCOPES)
    if not credentials.valid and credentials.refresh_token and allow_refresh:
        credentials.refresh(Request())
        TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    if not credentials.valid:
        raise RuntimeError("YouTube credential is not currently valid")
    return credentials


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
        from googleapiclient.discovery import build

        credentials = youtube_credentials()
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
        # lifetime counters for velocity sampling — analytics `posts` views are reporting-window
        # numbers and must never be diffed as a cumulative series
        lifetime_views = {post["id"]: post.get("views") for post in data_posts if post.get("id")}
        return {
            "status": "partial" if analytics_error else "ready",
            "fetchedAt": iso_now(),
            "lifetimeViews": lifetime_views,
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


SOURCE_PREFIX = {"youtube": "yt", "facebook": "fb", "instagram": "ig", "tiktok": "tt"}


def post_key(source_name: str, post: dict[str, Any]) -> str | None:
    post_id = post.get("id")
    return f"{SOURCE_PREFIX[source_name]}:{post_id}" if post_id else None


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def append_velocity_sample(sources: dict[str, dict[str, Any]]) -> None:
    views: dict[str, int] = {}
    for name, source in sources.items():
        lifetime = source.get("lifetimeViews") or {}
        for post in source.get("posts", []):
            key = post_key(name, post)
            value = lifetime.get(post.get("id"), post.get("views"))
            if key and isinstance(value, (int, float)):
                views[key] = int(value)
    if not views:
        return
    # ponytail: append-only JSONL, ~2KB/sample at 8/day = years before size matters; compact then
    with VELOCITY_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": iso_now(), "views": views}, ensure_ascii=False) + "\n")


def load_velocity_samples() -> list[dict[str, Any]]:
    if not VELOCITY_LOG.exists():
        return []
    samples = []
    for line in VELOCITY_LOG.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            record = json.loads(line)
            if not isinstance(record, dict) or not isinstance(record.get("views"), dict):
                continue
            sample_time(record)  # rejects missing/naive/unparseable timestamps
            record["views"] = {
                key: int(value) for key, value in record["views"].items()
                if isinstance(value, (int, float))
            }
            samples.append(record)
        except (json.JSONDecodeError, ValueError, TypeError):
            continue
    return samples


def sample_time(sample: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(str(sample.get("at", "")).replace("Z", "+00:00"))


def post_meta_from_snapshot() -> dict[str, dict[str, Any]]:
    try:
        snapshot = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    meta: dict[str, dict[str, Any]] = {}
    for name, source in snapshot.get("sources", {}).items():
        for post in source.get("posts", []):
            key = post_key(name, post)
            if key:
                meta[key] = {
                    "source": name,
                    "title": post.get("title"),
                    "url": post.get("url"),
                    "createdAt": post.get("createdAt"),
                    "views": post.get("views"),
                }
    return meta


def find_breakouts(meta: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Millie's viral-for-you test: own post at >=2x the trailing-20 median lifetime views."""
    import statistics

    breakouts = []
    for name in SOURCE_PREFIX:
        posts = [
            (key, item) for key, item in meta.items()
            if item["source"] == name and isinstance(item.get("views"), (int, float))
        ]
        if len(posts) < 5:
            continue
        posts.sort(key=lambda pair: str(pair[1].get("createdAt") or ""), reverse=True)
        trailing = [numeric(item.get("views")) for _, item in posts[:20]]
        median = statistics.median(trailing)
        for key, item in posts[:20]:
            views = numeric(item.get("views"))
            # explicit floors on top of the 2x-median rule: >=5-post baseline, >=20 views
            if median > 0 and views >= 2 * median and views >= 20:
                breakouts.append({
                    "key": key, "source": name, "title": item.get("title"), "url": item.get("url"),
                    "views": int(views), "medianTrailing20": round(median, 1),
                    "baselinePosts": len(trailing),
                    "multiple": round(views / median, 1),
                })
    breakouts.sort(key=lambda item: item["multiple"], reverse=True)
    return breakouts


def rate_per_hour(older: dict[str, Any], newer: dict[str, Any], key: str) -> float | None:
    if key not in older.get("views", {}) or key not in newer.get("views", {}):
        return None
    hours = (sample_time(newer) - sample_time(older)).total_seconds() / 3600
    if hours <= 0:  # clock skew / duplicate timestamps must not fabricate a rate
        return None
    return (newer["views"][key] - older["views"][key]) / hours


def compute_velocity() -> dict[str, Any]:
    samples = load_velocity_samples()
    meta = post_meta_from_snapshot()
    result: dict[str, Any] = {
        "schema": "tradercockpit-social-velocity/v1",
        "generatedAt": iso_now(),
        "samples": len(samples),
        "posts": [],
        "breakouts": find_breakouts(meta),
    }
    if len(samples) < 2:
        result["note"] = "Need at least two snapshots for velocity; keep the 3-hourly collector running."
        return result
    latest, prev = samples[-1], samples[-2]
    day_ago = next(
        (item for item in reversed(samples) if (sample_time(latest) - sample_time(item)).total_seconds() >= 22 * 3600),
        None,
    )
    posts = []
    for key in latest.get("views", {}):
        recent = rate_per_hour(prev, latest, key)
        if recent is None:
            continue
        prior = rate_per_hour(samples[-3], prev, key) if len(samples) >= 3 else None
        entry = {
            "key": key,
            "views": latest["views"][key],
            "perHourRecent": round(recent, 2),
            "perHour24h": round(rate_per_hour(day_ago, latest, key), 2) if day_ago and rate_per_hour(day_ago, latest, key) is not None else None,
            "spiking": bool(prior is not None and recent >= 5 and recent >= 3 * max(prior, 0.01)),
            **{field: meta.get(key, {}).get(field) for field in ("source", "title", "url")},
        }
        posts.append(entry)
    posts.sort(key=lambda item: item["perHourRecent"], reverse=True)
    result["posts"] = posts
    return result


def write_velocity() -> dict[str, Any]:
    velocity = compute_velocity()
    write_atomic(VELOCITY_FILE, json.dumps(velocity, indent=2, ensure_ascii=False) + "\n")
    return velocity


def failure_candidate(video: dict[str, Any], channel: dict[str, Any], phrases: list[str]) -> dict[str, Any] | None:
    title = str(video.get("snippet", {}).get("title") or "")
    title_lower = title.lower()
    channel_name = str(channel.get("snippet", {}).get("title") or "")
    niche_evidence = [term for term in NICHE_TERMS if term in f"{title} {channel_name}".lower()]
    # Conservative: description-only matches are excluded; a demand signal must be visible in the title.
    if not niche_evidence or not any(term in title_lower for term in FAILURE_TITLE_TERMS):
        return None
    subscribers = int(channel.get("statistics", {}).get("subscriberCount", 0) or 0)
    views = int(video.get("statistics", {}).get("viewCount", 0) or 0)
    # Shane's "under ~100k" is treated as a strict <100,000 gate; hidden/zero subs are unmeasurable.
    if subscribers <= 0 or subscribers >= 100_000 or views < 5 * subscribers:
        return None
    exact = [phrase for phrase in phrases if phrase.lower() in title_lower]
    phrasing = exact[0] if exact else phrases[0]
    modes = [mode for mode, terms in SHOW_BIBLE_TERMS.items() if any(term in title_lower for term in terms)]
    description = " ".join(str(video.get("snippet", {}).get("description") or "").split())
    return {
        "phrasing": phrasing,
        "observedViewSubscriberRatio": round(views / subscribers, 2),
        "sourceVideo": {
            "id": video.get("id"), "title": title, "url": f"https://youtu.be/{video.get('id')}",
            "viewCount": views, "publishedAt": video.get("snippet", {}).get("publishedAt"),
        },
        "sourceChannel": {
            "id": channel.get("id"), "name": channel_name, "subscriberCount": subscribers,
        },
        # Minimal operator context: direct API prose plus deterministic screen evidence.
        "context": {
            "matchedPhrasings": phrases,
            "signalClarity": "exact phrasing in title" if exact else "failure wording in title",
            "nicheEvidence": niche_evidence,
            "showBibleFailureModes": modes,
            "descriptionExcerpt": description[:300],
        },
    }


def rank_failure_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Ratio is the demand measure; title clarity is the conservative tie-breaker.
    ranked = sorted(candidates, key=lambda item: (
        item["observedViewSubscriberRatio"],
        item["context"]["signalClarity"] == "exact phrasing in title",
    ), reverse=True)
    for rank, item in enumerate(ranked, 1):
        item["rank"] = rank
    return ranked


def show_bible_cross_reference(finds: list[dict[str, Any]], complete: bool) -> list[dict[str, Any]]:
    cross_reference = []
    for mode in SHOW_BIBLE_TERMS:
        evidence = [
            {"rank": item["rank"], "videoId": item["sourceVideo"]["id"],
             "phrasing": item["phrasing"], "observedViewSubscriberRatio": item["observedViewSubscriberRatio"]}
            for item in finds if mode in item["context"]["showBibleFailureModes"]
        ]
        cross_reference.append({
            "failureMode": mode,
            "status": "demonstrated-demand" if evidence else (
                "internally-interesting-only" if complete else "no-signal-in-measured-queries"
            ),
            "evidence": evidence,
            "absenceNote": None if evidence else (
                "No qualifying title-level signal in this screen; this is not proof that no audience exists."
            ),
        })
    return cross_reference


def hotdog() -> dict[str, Any]:
    """Search failure-mode ideas, then apply Shane's 5x/sub-100k Hot Dog screen."""
    from googleapiclient.discovery import build

    # This lane is read-only: an expired credential fails closed instead of refreshing token state.
    youtube = build("youtube", "v3", credentials=youtube_credentials(allow_refresh=False), cache_discovery=False)
    coverage: list[dict[str, Any]] = []
    errors: list[str] = []
    video_phrases: dict[str, list[str]] = {}
    for phrase in FAILURE_PHRASES:
        try:
            response = youtube.search().list(
                part="snippet", q=f"{phrase} trading", type="video", order="viewCount",
                maxResults=25, relevanceLanguage="en",
            ).execute()
            ids = [item.get("id", {}).get("videoId") for item in response.get("items", [])]
            ids = [video_id for video_id in ids if video_id]
            coverage.append({"phrasing": phrase, "status": "measured", "resultsReturned": len(ids)})
            for video_id in ids:
                video_phrases.setdefault(video_id, []).append(phrase)
        except Exception as error:
            message = safe_error(error)
            coverage.append({"phrasing": phrase, "status": "failed", "error": message})
            errors.append(f"{phrase}: {message}")
    measured = sum(item["status"] == "measured" for item in coverage)
    if not measured:
        raise SystemExit(f"hotdog: every YouTube search.list call failed; output left untouched: {errors}")

    videos: dict[str, dict[str, Any]] = {}
    video_ids = list(video_phrases)
    for offset in range(0, len(video_ids), 50):
        response = youtube.videos().list(
            part="snippet,statistics", id=",".join(video_ids[offset:offset + 50]), maxResults=50,
        ).execute()
        videos.update({item["id"]: item for item in response.get("items", [])})
    channel_ids = list({item.get("snippet", {}).get("channelId") for item in videos.values()} - {None})
    channels: dict[str, dict[str, Any]] = {}
    for offset in range(0, len(channel_ids), 50):
        response = youtube.channels().list(
            part="snippet,statistics", id=",".join(channel_ids[offset:offset + 50]), maxResults=50,
        ).execute()
        channels.update({item["id"]: item for item in response.get("items", [])})

    finds = []
    for video_id, phrases in video_phrases.items():
        video = videos.get(video_id)
        channel = channels.get(video.get("snippet", {}).get("channelId")) if video else None
        if video and channel:
            candidate = failure_candidate(video, channel, phrases)
            if candidate:
                finds.append(candidate)
    finds = rank_failure_candidates(finds)
    complete = measured == len(FAILURE_PHRASES)
    payload = {
        "schema": "tradercockpit-failure-mode-demand/v1",
        "updatedAt": iso_now(),
        "status": "ok" if complete else "partial",
        "measurement": {
            "source": "live YouTube Data API v3 list responses",
            "search": "requested phrasing plus trading, ordered by view count, first 25 results",
            "qualification": "title-level failure wording; markets/trading/prop-firm/trading-tech; channel subscribers >0 and <100000; views >=5x subscribers",
            "ranking": "observed view/subscriber ratio descending; exact-title phrasing breaks ties",
        },
        "queryCoverage": coverage,
        "errors": errors,
        "finds": finds,
        "showBibleCrossReference": show_bible_cross_reference(finds, complete),
    }
    write_atomic(HOTDOG_FILE, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return payload


def hotdog_selftest() -> None:
    def video(video_id: str, title: str, views: int) -> dict[str, Any]:
        return {"id": video_id, "snippet": {"title": title, "description": "", "publishedAt": "2026-01-01T00:00:00Z"},
                "statistics": {"viewCount": str(views)}}

    def channel(channel_id: str, name: str, subscribers: int) -> dict[str, Any]:
        return {"id": channel_id, "snippet": {"title": name}, "statistics": {"subscriberCount": str(subscribers)}}

    exact = failure_candidate(video("five", "Why My Trading Strategy Stopped Working", 5000),
                              channel("c1", "Quant Trader", 1000), [FAILURE_PHRASES[0]])
    assert exact and exact["observedViewSubscriberRatio"] == 5.0
    assert failure_candidate(video("low", "Why My Trading Strategy Stopped Working", 4999),
                             channel("c1", "Quant Trader", 1000), [FAILURE_PHRASES[0]]) is None
    assert failure_candidate(video("large", "Why My Trading Strategy Stopped Working", 1_000_000),
                             channel("c2", "Quant Trader", 100_000), [FAILURE_PHRASES[0]]) is None
    assert failure_candidate(video("off", "Why My Business Strategy Stopped Working", 5000),
                             channel("c3", "Business School", 1000), [FAILURE_PHRASES[0]]) is None
    higher = failure_candidate(video("ten", "Why My Trading Strategy Stopped Working", 10_000),
                               channel("c1", "Quant Trader", 1000), [FAILURE_PHRASES[0]])
    assert higher and [item["sourceVideo"]["id"] for item in rank_failure_candidates([exact, higher])] == ["ten", "five"]
    print("social-analytics hotdog self-test: 5/5 PASS")


def load_drivers() -> dict[str, str]:
    if not DRIVERS_FILE.exists():
        DRIVERS_FILE.write_text(json.dumps({
            "_doc": "Map post key (yt:/ig:/fb:/tt:<id>) -> money|email|audience|fun (Millie's four drivers).",
        }, indent=2) + "\n", encoding="utf-8")
        return {}
    try:
        data = json.loads(DRIVERS_FILE.read_text(encoding="utf-8"))
        return {key: str(value).lower() for key, value in data.items() if not key.startswith("_")}
    except (OSError, json.JSONDecodeError):
        return {}


def md_link(title: Any, url: Any) -> str:
    text = str(title or "Untitled").replace("|", "/")[:80]
    return f"[{text}]({url})" if url else text


def report() -> Path:
    snapshot = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
    velocity = write_velocity()
    drivers = load_drivers()
    hotdog_payload: dict[str, Any] = {}
    if HOTDOG_FILE.exists():
        try:
            loaded = json.loads(HOTDOG_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                hotdog_payload = loaded
        except (OSError, json.JSONDecodeError):
            pass
    hotdog_finds = hotdog_payload.get("finds") or []
    window = snapshot.get("window", {})
    start, end = str(window.get("start", "")), str(window.get("end", ""))
    meta = post_meta_from_snapshot()
    lines = [
        f"# Social week {start} → {end}",
        "",
        f"Generated {iso_now()} by `tools/social_analytics.py report`. Feed for the Sunday review lane —",
        "playbook skills (Millie / Shane / Grow with Alex / GaryVee) interpret this; humans decide.",
        "",
        "## Totals",
        "",
    ]
    rollup = snapshot.get("rollup", {})
    for key, value in rollup.items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Shipped this window", ""]
    shipped = [
        (key, item) for key, item in meta.items()
        if start <= str(item.get("createdAt") or "")[:10] <= end
    ]
    if shipped:
        lines.append("| Post | Source | Views | Driver |")
        lines.append("|---|---|---|---|")
        for key, item in sorted(shipped, key=lambda pair: numeric(pair[1].get("views")), reverse=True):
            lines.append(f"| {md_link(item.get('title'), item.get('url'))} | {item['source']} | "
                         f"{int(numeric(item.get('views')))} | {drivers.get(key, '—')} |")
    else:
        lines.append("Nothing shipped in this window.")
    lines += ["", "## Velocity movers", ""]
    movers = [item for item in velocity.get("posts", []) if item["perHourRecent"] > 0][:5]
    if movers:
        for item in movers:
            flag = " **SPIKING**" if item.get("spiking") else ""
            lines.append(f"- {md_link(item.get('title'), item.get('url'))} ({item.get('source')}): "
                         f"{item['perHourRecent']}/hr recent, {item.get('perHour24h')}/hr 24h{flag}")
    else:
        lines.append(velocity.get("note") or "No positive movement between the last two samples.")
    lines += ["", "## Breakouts (≥2× trailing-20 median)", ""]
    if velocity.get("breakouts"):
        for item in velocity["breakouts"]:
            lines.append(f"- {md_link(item.get('title'), item.get('url'))} ({item['source']}): "
                         f"{item['views']} views = {item['multiple']}× median {item['medianTrailing20']}")
    else:
        lines.append("None this week.")
    lines += ["", "## Hot Dog failure-mode demand (videos ≥5× channel subs)", ""]
    if hotdog_finds:
        for item in hotdog_finds[:10]:
            video = item.get("sourceVideo", {})
            channel = item.get("sourceChannel", {})
            lines.append(f"- {md_link(video.get('title'), video.get('url'))} — {channel.get('name')}: "
                         f"{video.get('viewCount')} views vs {channel.get('subscriberCount')} subs "
                         f"({item.get('observedViewSubscriberRatio')}×; {item.get('phrasing')})")
    else:
        coverage = hotdog_payload.get("queryCoverage") or []
        measured = sum(item.get("status") == "measured" for item in coverage)
        if not hotdog_payload:
            lines.append("Screen has not run yet — run `hotdog`.")
        elif hotdog_payload.get("errors"):
            lines.append(f"0 finds; screen degraded — {measured}/{len(coverage)} phrasings measured, "
                         f"errors: {hotdog_payload['errors']}")
        else:
            lines.append("0 qualifying failure-mode videos from the measured searches — screen healthy; "
                         "absence is a programming signal.")
    lines += ["", "## Driver scores (views by declared intention)", ""]
    scores: dict[str, int] = {}
    untagged = 0
    for key, item in shipped:
        driver = drivers.get(key)
        if driver:
            scores[driver] = scores.get(driver, 0) + int(numeric(item.get("views")))
        else:
            untagged += 1
    for driver in ("money", "email", "audience", "fun"):
        if driver in scores:
            lines.append(f"- {driver}: {scores[driver]} views")
    lines.append(f"- untagged posts this window: {untagged}" if untagged else "- all shipped posts tagged")
    lines += ["", "## Collector decisions", ""]
    for decision in snapshot.get("decisions", []):
        lines.append(f"- **{decision.get('priority')}** — {decision.get('title')}: {decision.get('evidence')} "
                     f"→ {decision.get('action')}")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"social-week-{end}.md"
    write_atomic(out, "\n".join(lines) + "\n")
    return out


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
    append_velocity_sample(sources)
    write_velocity()
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["auth-youtube", "collect", "velocity", "hotdog", "report", "selftest"])
    args = parser.parse_args()
    if args.command == "auth-youtube":
        auth_youtube()
        return
    if args.command == "velocity":
        velocity = write_velocity()
        print(f"wrote {VELOCITY_FILE} ({velocity['samples']} samples, {len(velocity.get('posts', []))} posts, "
              f"{len(velocity.get('breakouts', []))} breakouts)")
        return
    if args.command == "hotdog":
        payload = hotdog()
        print(f"wrote {HOTDOG_FILE} ({len(payload.get('finds', []))} finds, errors={payload.get('errors', [])})")
        return
    if args.command == "selftest":
        hotdog_selftest()
        return
    if args.command == "report":
        out = report()
        print(f"wrote {out}")
        return
    snapshot = collect()
    statuses = ", ".join(f"{name}={source['status']}" for name, source in snapshot["sources"].items())
    print(f"wrote {SNAPSHOT_FILE}")
    print(statuses)


if __name__ == "__main__":
    main()
