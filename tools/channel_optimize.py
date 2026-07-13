#!/usr/bin/env python3
"""Finance-niche channel optimization via YouTube Data API (uses token_channel.json).

Sets: country=US, defaultLanguage=en, uploads banner, sets branding watermark,
creates the three strategy playlists. Idempotent — safe to rerun.
"""
from pathlib import Path

from googleapiclient.http import MediaFileUpload

from channel_seo import get_service

HERE = Path(__file__).parent
BRAND = HERE / "visuals" / "brand"

PLAYLISTS = [
    ("Today in Markets",
     "Daily market news: what moved, why, and what it means for your portfolio."),
    ("Chokepoints",
     "Geopolitics deep-dives on the flashpoints moving oil, indices, and rates."),
    ("The Gauntlet — strategies executed on camera",
     "Famous trading strategies coded honestly and run through 12 phases of statistical torture. Whatever survives, survives."),
]


def main():
    yt = get_service()
    ch = yt.channels().list(part="id,brandingSettings", mine=True).execute()["items"][0]
    cid, branding = ch["id"], ch["brandingSettings"]

    # locale — US = deepest finance CPM pool; language for search/captions matching
    branding.setdefault("channel", {})
    branding["channel"]["country"] = "US"
    branding["channel"]["defaultLanguage"] = "en"

    banner = BRAND / "banner.png"
    if banner.exists():
        up = yt.channelBanners().insert(media_body=MediaFileUpload(str(banner))).execute()
        branding["image"] = {"bannerExternalUrl": up["url"]}
        print("banner uploaded")

    yt.channels().update(part="brandingSettings",
                         body={"id": cid, "brandingSettings": branding}).execute()
    print("country=US, defaultLanguage=en, branding applied")

    wm = BRAND / "watermark.png"
    if wm.exists():
        yt.watermarks().set(channelId=cid,
                            body={"timing": {"type": "offsetFromStart", "offsetMs": 0}},
                            media_body=MediaFileUpload(str(wm))).execute()
        print("watermark set (all videos)")

    existing = {p["snippet"]["title"] for p in yt.playlists().list(
        part="snippet", mine=True, maxResults=50).execute().get("items", [])}
    for title, desc in PLAYLISTS:
        if title in existing:
            print(f"playlist exists: {title}")
            continue
        yt.playlists().insert(part="snippet,status", body={
            "snippet": {"title": title, "description": desc},
            "status": {"privacyStatus": "public"},
        }).execute()
        print(f"playlist created: {title}")


if __name__ == "__main__":
    main()
