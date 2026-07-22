#!/usr/bin/env python3
"""Surface and rank comment-worthy posts on watchlist accounts.

Doctrine (GTM/Social-Media-Library/Content Machine Team Brief.md, Stage 5):
  "Hard rule: no AI-generated comments, no cold-pitch DMs - ever.
   This stage is deliberately human."

Comments stay human: this tool never drafts comment text, never comments,
follows or DMs. Auto-LIKE of ranked niche targets is the one permitted write
action (operator ruling 2026-07-21), YouTube only, capped per run, ledgered in
social-ops/liked-videos.json so a video is never rated twice.

Commands:
  python tools/engagement.py scan            # watchlist -> social-ops/engagement-targets.json
  python tools/engagement.py scan --like 10  # scan, then like top 10 unliked YouTube targets
  python tools/engagement.py selftest        # assert-based ranking check, no network

Use OpenMontage/.venv/Scripts/python.exe so the Google client libraries resolve.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from tools.social_analytics import (
        ENV_FILE, ROOT, TOOLS, credential_path, dotenv_values, graph_get,
        iso_now, numeric, safe_error, write_atomic, youtube_credentials,
    )
except ModuleNotFoundError:  # direct `python tools/engagement.py` execution
    from social_analytics import (
        ENV_FILE, ROOT, TOOLS, credential_path, dotenv_values, graph_get,
        iso_now, numeric, safe_error, write_atomic, youtube_credentials,
    )

# ponytail: reuse the vetted competitor watchlist (same {"channels": [...]} shape)
# rather than maintaining a second list. Split only if engagement targets diverge
# from the Hot Dog screen set.
WATCHLIST_FILE = ROOT / "social-ops" / "competitor-watchlist.json"
ENGAGEMENT_WATCHLIST_FILE = ROOT / "social-ops" / "engagement-watchlist.json"
TARGETS_FILE = ROOT / "social-ops" / "engagement-targets.json"
LIKED_FILE = ROOT / "social-ops" / "liked-videos.json"

# Our niche vocabulary. Topical fit is a plain keyword hit count against
# title+description — no LLM scores anything here, by design.
NICHE_TERMS = (
    "macro", "fed", "rates", "yield", "treasury", "inflation", "cpi", "liquidity",
    "futures", "es ", "s&p", "spx", "nasdaq", "vix", "volatility", "options",
    "risk", "position sizing", "drawdown", "backtest", "systematic", "quant",
    "credit", "dollar", "oil", "gold", "recession", "earnings", "breadth",
)


def hours_since(timestamp: Any) -> float | None:
    try:
        posted = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if posted.tzinfo is None:
        return None
    return (datetime.now(timezone.utc) - posted).total_seconds() / 3600


def topical_fit(text: str) -> int:
    lowered = (text or "").lower()
    return sum(1 for term in NICHE_TERMS if term in lowered)


def score_post(post: dict[str, Any]) -> dict[str, Any]:
    """Reply-worthiness from observable signals only. No LLM, no content model.

    Three factors, multiplied so a zero on any one kills the target:

      recency   exp(-age_hours / 24). A comment is worth writing in the window
                where it is still visible; a 24h-old post scores ~0.37 of fresh,
                a 3-day-old one ~0.05. Posts with no parseable timestamp score 0
                (unknown age = unrankable, not "assume fresh").

      velocity  log1p(engagement per hour since posting). Comments+likes per hour
                proxies "conversation is live right now" better than raw totals,
                which just reward old posts. log1p compresses so one viral post
                cannot monopolise the whole list. Comments are weighted 3x likes:
                a like is not a conversation, a comment thread is where a reply
                actually gets read. Age is floored at 1h so a 5-minute-old post
                does not report an absurd per-hour rate.

      fit       1 + niche keyword hits, capped at 4. Keeps the ranking pointed at
                posts we can say something credible about. Floor of 1 means an
                off-topic post is merely deprioritised, never excluded — the
                operator may still see a reason we cannot encode.

    ponytail: flat keyword list, not embeddings. Upgrade path if the list starts
    missing obvious targets: hand-tune NICHE_TERMS first, embeddings never.
    """
    age = hours_since(post.get("createdAt"))
    if age is None or age < 0:
        return {"score": 0.0, "ageHours": None, "engagementPerHour": None, "topicalFit": 0,
                "why": "no parseable publish timestamp"}
    engagement = numeric(post.get("likes")) + 3 * numeric(post.get("comments"))
    per_hour = engagement / max(age, 1.0)
    fit = min(topical_fit(f"{post.get('title', '')} {post.get('description', '')}"), 3)
    recency = math.exp(-age / 24)
    score = recency * math.log1p(per_hour) * (1 + fit)
    return {
        "score": round(score, 4),
        "ageHours": round(age, 1),
        "engagementPerHour": round(per_hour, 2),
        "topicalFit": fit,
        "why": f"{age:.0f}h old, {per_hour:.1f} weighted engagement/hr, {fit} niche keyword hits",
    }


def rank(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = [{**post, **score_post(post)} for post in posts]
    live = [item for item in scored if item["score"] > 0]
    live.sort(key=lambda item: item["score"], reverse=True)
    return live


def collect_youtube_watchlist(channels: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    from googleapiclient.discovery import build

    youtube = build("youtube", "v3", credentials=youtube_credentials(), cache_discovery=False)
    posts: list[dict[str, Any]] = []
    errors: list[str] = []
    for ref in channels:
        try:
            params: dict[str, Any] = {"part": "snippet,contentDetails"}
            params["forHandle" if ref.startswith("@") else "id"] = ref
            items = youtube.channels().list(**params).execute().get("items", [])
            if not items:
                errors.append(f"{ref}: channel not found")
                continue
            channel = items[0]
            uploads = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
            if not uploads:
                continue
            playlist = youtube.playlistItems().list(
                part="contentDetails", playlistId=uploads, maxResults=10,
            ).execute()
            ids = [item.get("contentDetails", {}).get("videoId") for item in playlist.get("items", [])]
            ids = [value for value in ids if value]
            if not ids:
                continue
            videos = youtube.videos().list(
                part="snippet,statistics", id=",".join(ids), maxResults=10,
            ).execute().get("items", [])
            for video in videos:
                snippet = video.get("snippet", {})
                stats = video.get("statistics", {})
                posts.append({
                    "platform": "youtube",
                    "account": channel.get("snippet", {}).get("title") or ref,
                    "id": video.get("id"),
                    "title": snippet.get("title"),
                    "description": (snippet.get("description") or "")[:400],
                    "createdAt": snippet.get("publishedAt"),
                    "url": f"https://youtu.be/{video.get('id')}",
                    "views": int(stats.get("viewCount", 0) or 0),
                    "likes": int(stats.get("likeCount", 0) or 0),
                    "comments": int(stats.get("commentCount", 0) or 0),
                })
        except Exception as error:
            errors.append(f"{ref}: {safe_error(error)}")
    return posts, errors


def collect_tiktok_cdp() -> tuple[list[dict[str, Any]], list[str]]:
    """Our own TikTok Studio rows via the logged-in debug Chrome on 9333.

    Reuses tools/tiktok_analytics_cdp.cjs verbatim — that script only reads the
    DOM and never clicks a mutating control. A dead profile fails visibly rather
    than silently yielding an empty list.
    """
    try:
        result = subprocess.run(
            ["node", str(TOOLS / "tiktok_analytics_cdp.cjs")],
            cwd=ROOT, capture_output=True, text=True, timeout=45,
            encoding="utf-8", errors="replace",
        )
        payload = json.loads(result.stdout or "{}")
    except Exception as error:
        return [], [f"tiktok: CDP profile on 127.0.0.1:9333 unreachable — {safe_error(error)}"]
    if payload.get("status") != "ready":
        return [], [f"tiktok: CDP collector unavailable — {payload.get('error', 'unknown')}. "
                    "Start the debug Chrome profile on port 9333."]
    posts = []
    for post in payload.get("posts", []):
        posts.append({
            "platform": "tiktok",
            "account": payload.get("account"),
            "id": post.get("id"),
            "title": post.get("title"),
            "description": "",
            # Studio renders a "Jul 18" label, not an ISO stamp; unparseable ages
            # score 0 in score_post, which is the honest outcome.
            "createdAt": post.get("createdLabel"),
            "url": post.get("url"),
            "views": post.get("views"),
            "likes": post.get("likes"),
            "comments": post.get("comments"),
        })
    return posts, []


def pick_likes(targets: list[dict[str, Any]], liked: set[str], count: int) -> list[str]:
    """Top-N unliked YouTube video ids, ranked order. Pure — selftested."""
    picks: list[str] = []
    for item in targets:
        if len(picks) >= count:
            break
        video_id = item.get("id")
        if item.get("platform") == "youtube" and video_id and video_id not in liked:
            picks.append(video_id)
    return picks


def auto_like(targets: list[dict[str, Any]], count: int) -> tuple[list[str], list[str]]:
    """Rate top-N unliked YouTube targets 'like'. Ledger prevents re-rating.

    operator ruling 2026-07-21: auto-like permitted. Comments/DMs/follows stay
    human per Stage 5 doctrine — this function only ever calls videos().rate.

    Uses the channel token (token_channel.json, full youtube scope — videos.rate
    accepts it) via channel_seo.get_service, so the read-only analytics token
    stays untouched and no new consent is needed.
    """
    try:
        liked = set(json.loads(LIKED_FILE.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        liked = set()
    picks = pick_likes(targets, liked, count)
    if not picks:
        return [], []
    try:
        from tools.channel_seo import get_service
    except ModuleNotFoundError:
        from channel_seo import get_service
    youtube = get_service()
    done: list[str] = []
    errors: list[str] = []
    for video_id in picks:
        try:
            youtube.videos().rate(id=video_id, rating="like").execute()
            done.append(video_id)
            liked.add(video_id)
        except Exception as error:
            errors.append(f"like {video_id}: {safe_error(error)}")
    if done:
        write_atomic(LIKED_FILE, json.dumps(sorted(liked), indent=2) + "\n")
    return done, errors


def engagement_watchlist(platform: str) -> list[str]:
    try:
        data = json.loads(ENGAGEMENT_WATCHLIST_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return [entry["handle"] for entry in data.get(platform, [])
            if isinstance(entry, dict) and isinstance(entry.get("handle"), str)]


def collect_tiktok_watchlist(handles: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Watchlist accounts' recent posts via the logged-in debug Chrome on 9333.

    Read-only page visits; snowflake ids give real timestamps so these rank
    honestly. A dead profile fails visibly per handle.
    """
    if not handles:
        return [], []
    try:
        result = subprocess.run(
            ["node", str(TOOLS / "tiktok_watchlist_cdp.cjs"), *handles],
            cwd=ROOT, capture_output=True, text=True, timeout=600,
            encoding="utf-8", errors="replace",
        )
        payload = json.loads(result.stdout or "{}")
    except Exception as error:
        return [], [f"tiktok-watchlist: CDP profile on 127.0.0.1:9333 unreachable — {safe_error(error)}"]
    if payload.get("status") != "ready":
        return [], [f"tiktok-watchlist: collector unavailable — {payload.get('error', 'unknown')}. "
                    "Start the debug Chrome profile on port 9333."]
    return payload.get("posts", []), [f"tiktok-watchlist: {e}" for e in payload.get("errors", [])]


def collect_instagram_watchlist(usernames: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Watchlist accounts' recent posts via the official Business Discovery API.

    Reuses the custody Meta creds already powering social_analytics collect.
    Personal (non-business/creator) targets error per row — visible, prunable.
    """
    if not usernames:
        return [], []
    env = dict(dotenv_values(ENV_FILE))
    meta_env = credential_path("meta.env")
    if meta_env.is_file():
        env.update(dotenv_values(meta_env))
    user_id, token = env.get("META_IG_USER_ID"), env.get("META_PAGE_TOKEN")
    if not user_id or not token:
        return [], ["instagram-watchlist: missing META_IG_USER_ID/META_PAGE_TOKEN in custody env"]
    posts: list[dict[str, Any]] = []
    errors: list[str] = []
    for username in usernames:
        try:
            fields = (f"business_discovery.username({username})"
                      "{username,followers_count,media.limit(10)"
                      "{id,caption,timestamp,permalink,like_count,comments_count}}")
            discovery = graph_get(str(user_id), str(token), fields=fields).get("business_discovery", {})
            for item in discovery.get("media", {}).get("data", []):
                caption = item.get("caption") or ""
                posts.append({
                    "platform": "instagram",
                    "account": f"@{discovery.get('username', username)}",
                    "id": item.get("id"),
                    "title": caption.splitlines()[0][:140] if caption else "Untitled post",
                    "description": caption[:400],
                    "createdAt": item.get("timestamp"),
                    "url": item.get("permalink"),
                    "views": None,
                    "likes": item.get("like_count"),
                    "comments": item.get("comments_count"),
                })
        except Exception as error:
            errors.append(f"instagram-watchlist {username}: {safe_error(error)}")
    return posts, errors


def scan(limit: int) -> dict[str, Any]:
    try:
        watchlist = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"scan: watchlist unreadable, prior targets left untouched: {safe_error(error)}")
    channels = [ref for ref in (watchlist.get("channels") or []) if isinstance(ref, str) and ref.strip()]
    tiktok_handles = engagement_watchlist("tiktok")
    instagram_handles = engagement_watchlist("instagram")
    posts, errors = collect_youtube_watchlist(channels)
    for extra_posts, extra_errors in (
        collect_tiktok_cdp(),
        collect_tiktok_watchlist(tiktok_handles),
        collect_instagram_watchlist(instagram_handles),
    ):
        posts += extra_posts
        errors += extra_errors
    ranked = rank(posts)[:limit]
    payload = {
        "schema": "tradercockpit-engagement-targets/v1",
        "generatedAt": iso_now(),
        "writeActions": "auto-like only (operator ruling 2026-07-21) — never comments, follows, DMs, or drafts text",
        "accountsConfigured": {"youtube": len(channels), "tiktok": len(tiktok_handles),
                               "instagram": len(instagram_handles)},
        "postsSeen": len(posts),
        "ranking": "recency exp(-h/24) x log1p(weighted engagement/hr) x (1 + niche keyword hits, capped 3)",
        "errors": errors,
        "targets": [
            {key: item.get(key) for key in (
                "platform", "account", "id", "title", "url", "createdAt", "ageHours",
                "views", "likes", "comments", "engagementPerHour", "topicalFit",
                "score", "why", "description",
            )}
            for item in ranked
        ],
        "operatorNote": "Stage 5 is deliberately human. Read the post, then write your own comment.",
    }
    write_atomic(TARGETS_FILE, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return payload


def selftest() -> None:
    now = datetime.now(timezone.utc)

    def post(hours: float, likes: int, comments: int, title: str = "market update") -> dict[str, Any]:
        stamp = now.timestamp() - hours * 3600
        return {
            "createdAt": datetime.fromtimestamp(stamp, timezone.utc).isoformat().replace("+00:00", "Z"),
            "likes": likes, "comments": comments, "title": title, "description": "",
        }

    fresh, stale = score_post(post(2, 100, 50)), score_post(post(96, 100, 50))
    assert fresh["score"] > stale["score"], (fresh, stale)

    hot, cold = score_post(post(6, 400, 200)), score_post(post(6, 4, 2))
    assert hot["score"] > cold["score"], (hot, cold)

    on_topic = score_post(post(6, 100, 50, "Fed cuts rates, VIX and S&P futures react"))
    off_topic = score_post(post(6, 100, 50, "my new desk setup tour"))
    assert on_topic["score"] > off_topic["score"], (on_topic, off_topic)
    assert on_topic["topicalFit"] >= 2 and off_topic["topicalFit"] == 0

    # comments outweigh likes at equal raw engagement — a thread beats a tap
    assert score_post(post(6, 0, 100))["score"] > score_post(post(6, 100, 0))["score"]

    # unrankable / dead posts are excluded, never assumed fresh
    assert score_post({"createdAt": None, "likes": 999, "comments": 999})["score"] == 0.0
    assert score_post({"createdAt": "Jul 18", "likes": 9})["score"] == 0.0  # TikTok Studio label
    assert score_post(post(1, 0, 0))["score"] == 0.0  # zero engagement -> log1p(0) = 0

    # a 5-minute-old post cannot fabricate a 12x per-hour rate (age floored at 1h)
    assert score_post(post(0.08, 10, 0))["engagementPerHour"] == 10.0

    ranked = rank([post(200, 5, 1), post(3, 300, 120, "CPI print and rates"), post(50, 10, 2)])
    assert [item["score"] for item in ranked] == sorted(
        (item["score"] for item in ranked), reverse=True)
    assert "CPI" in ranked[0]["title"]

    # like picker: ranked order, ledger skip, count cap, youtube-only, needs id
    targets = [
        {"platform": "youtube", "id": "a", "score": 9},
        {"platform": "tiktok", "id": "t", "score": 8},
        {"platform": "youtube", "id": "b", "score": 7},
        {"platform": "youtube", "id": "c", "score": 5},
        {"platform": "youtube", "score": 4},  # no id -> skipped
    ]
    assert pick_likes(targets, set(), 10) == ["a", "b", "c"]
    assert pick_likes(targets, {"a"}, 10) == ["b", "c"]
    assert pick_likes(targets, set(), 2) == ["a", "b"]
    assert pick_likes([], set(), 10) == []

    print(f"selftest ok — {len(NICHE_TERMS)} niche terms, ranking + like-picker assertions all pass")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["scan", "selftest"])
    parser.add_argument("--limit", type=int, default=40, help="max targets written (default 40)")
    parser.add_argument("--like", type=int, default=0, metavar="N",
                        help="after scan, like top N unliked YouTube targets (default 0 = off)")
    args = parser.parse_args()
    if args.command == "selftest":
        selftest()
        return
    payload = scan(args.limit)
    print(f"wrote {TARGETS_FILE} ({len(payload['targets'])} targets from {payload['postsSeen']} posts seen)")
    if args.like > 0:
        done, like_errors = auto_like(payload["targets"], args.like)
        payload["errors"] += like_errors
        print(f"liked {len(done)} videos ({len(like_errors)} errors), ledger {LIKED_FILE.name}")
    for error in payload["errors"]:
        print(f"  ! {error}", file=sys.stderr)
    if not payload["targets"] and payload["errors"]:
        raise SystemExit("scan: no targets and all sources errored — see above")


if __name__ == "__main__":
    main()
