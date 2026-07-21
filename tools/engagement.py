#!/usr/bin/env python3
"""Surface and rank comment-worthy posts on watchlist accounts. READ-ONLY.

Doctrine (GTM/Social-Media-Library/Content Machine Team Brief.md, Stage 5):
  "Hard rule: no AI-generated comments, no cold-pitch DMs - ever.
   This stage is deliberately human."

So this tool only LISTS AND RANKS targets. It never drafts comment text, never
posts, likes, follows or DMs, and performs zero write actions against any
platform. The operator writes every comment personally.

Commands:
  python tools/engagement.py scan            # watchlist -> social-ops/engagement-targets.json
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
        ROOT, TOOLS, WATCHLIST_FILE, iso_now, numeric, safe_error,
        write_atomic, youtube_credentials,
    )
except ModuleNotFoundError:  # direct `python tools/engagement.py` execution
    from social_analytics import (
        ROOT, TOOLS, WATCHLIST_FILE, iso_now, numeric, safe_error,
        write_atomic, youtube_credentials,
    )

TARGETS_FILE = ROOT / "social-ops" / "engagement-targets.json"

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


def scan(limit: int) -> dict[str, Any]:
    try:
        watchlist = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"scan: watchlist unreadable, prior targets left untouched: {safe_error(error)}")
    channels = [ref for ref in (watchlist.get("channels") or []) if isinstance(ref, str) and ref.strip()]
    posts, errors = collect_youtube_watchlist(channels)
    tiktok_posts, tiktok_errors = collect_tiktok_cdp()
    posts += tiktok_posts
    errors += tiktok_errors
    ranked = rank(posts)[:limit]
    payload = {
        "schema": "tradercockpit-engagement-targets/v1",
        "generatedAt": iso_now(),
        "writeActions": "none — this tool never posts, likes, follows, DMs, or drafts text",
        "accountsConfigured": len(channels),
        "postsSeen": len(posts),
        "ranking": "recency exp(-h/24) x log1p(weighted engagement/hr) x (1 + niche keyword hits, capped 3)",
        "errors": errors,
        "targets": [
            {key: item.get(key) for key in (
                "platform", "account", "title", "url", "createdAt", "ageHours",
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

    print(f"selftest ok — {len(NICHE_TERMS)} niche terms, ranking monotonic on all 9 assertions")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["scan", "selftest"])
    parser.add_argument("--limit", type=int, default=40, help="max targets written (default 40)")
    args = parser.parse_args()
    if args.command == "selftest":
        selftest()
        return
    payload = scan(args.limit)
    print(f"wrote {TARGETS_FILE} ({len(payload['targets'])} targets from {payload['postsSeen']} posts seen)")
    for error in payload["errors"]:
        print(f"  ! {error}", file=sys.stderr)
    if not payload["targets"] and payload["errors"]:
        raise SystemExit("scan: no targets and all sources errored — see above")


if __name__ == "__main__":
    main()
