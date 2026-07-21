#!/usr/bin/env python3
"""Apply every audited YouTube metadata fix in one pass. Dry-run by default.

Built 2026-07-20 after a live audit found three defects that all need the same OAuth scope:

  1. VISIBILITY — the best-performing video on the channel (89 views) was PRIVATE while a
     0-view duplicate was public. Someone re-uploaded instead of repackaging, which threw away
     both the views and the algorithmic history. 15% of all channel views sat on hidden videos.
  2. TAGS — 10 of 19 public videos carry ZERO tags, including all four top performers.
  3. TITLES — pre-playbook slogan copy is still live. "siren" and "pressure chain" were the only
     two strings the previous style gate hardcoded, and one is in a live title.

Everything here is REVERSIBLE and receipted. Nothing is deleted; a de-duplicated twin is set
private, never removed — doctrine is "repackage, don't repost" and "never erase weak-but-factual
uploads".

    python tools/apply_channel_fixes.py            # dry run, shows every change
    python tools/apply_channel_fixes.py --apply    # execute, writes receipts

Requires token_channel.json (scope auth/youtube). If its refresh token is expired, run
`python tools/channel_seo.py` once to re-consent — that is an operator action by design.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

RECEIPTS = ROOT / "social-ops" / "channel-fix-receipts-2026-07-20.json"

# --- 1. VISIBILITY -----------------------------------------------------------------
# Order matters: promote FIRST, verify, only then demote the twin. Never reduce public
# content on an unverified promote.
PROMOTE = [
    ("Dy_XvwUi6Ng", "89 views, was hidden while its 0-view twin was public"),
    ("SHVn6IdgIUo", "3 views, was hidden while its 0-view twin was public"),
]
DEMOTE = [
    ("7RiqulLReco", "0-view duplicate of Dy_XvwUi6Ng"),
    ("SNdRs5l6rtc", "0-view duplicate of SNdRs5l6rtc's better twin SHVn6IdgIUo"),
]
# Deliberately NOT touched: the Hormuz-portfolio and oil-target groups already have the
# view-holding copy public. Correct as-is.

# --- 2. TITLES ---------------------------------------------------------------------
# Every replacement was checked through tools/script_style_gate.py before being written here.
# Rationale per line is in social-ops/live-copy-rewrites-2026-07-20.md.
TITLES = {
    "Don't Trade the Siren. Trade the Pressure Chain. #Shorts":
        "Oil +10%, Energy +4%: What Actually Moved #Shorts",
    "The market is pricing the Strait, not the end of the world #Shorts":
        "5 Tankers vs 130 a Day: What Hormuz Actually Closed #Shorts",
    "The Nasdaq Broke. The S&P Held.":
        "Nasdaq Broke 7431, S&P Held Its Band — The Divergence",
    "Iran Oil Deadline Day Meets a Cracking AI Trade":
        "Iran Deadline Day and TSMC's $403.50 Floor",
    "Iran War Widens as Oil Holds $84":
        "Oil Holds $84 as the Risk Premium Sticks",
    "Don't Trade the Siren: How the War Premium Travels":
        "How the War Premium Travels: Brent to Energy Equities",
}

# --- 3. TAGS -----------------------------------------------------------------------
# Drawn from the channel's OWN keyword set, which already matches the positioning
# ("backtest overfitting", "walk-forward analysis", "honest backtest"). Topic tags are
# added per-video by subject; no invented terms.
BASE_TAGS = ["market analysis", "trading", "stock market", "finance news"]
TOPIC_TAGS = {
    "oil": ["crude oil", "brent", "energy stocks", "oil price"],
    "hormuz": ["strait of hormuz", "geopolitics", "oil supply"],
    "nasdaq": ["nasdaq", "s&p 500", "market breadth", "index analysis"],
    "semis": ["semiconductors", "tsmc", "chip stocks"],
    "week": ["weekly recap", "market recap", "weekly close"],
    "bank": ["bank earnings", "earnings season", "net interest income"],
}


def topic_tags_for(title: str) -> list[str]:
    low = title.lower()
    tags = list(BASE_TAGS)
    for key, extra in TOPIC_TAGS.items():
        if key in low:
            tags += extra
    # YouTube counts total tag characters against a 500 limit; keep well inside it.
    out, seen = [], set()
    for tag in tags:
        if tag not in seen and sum(len(t) + 1 for t in out) + len(tag) < 450:
            out.append(tag)
            seen.add(tag)
    return out


def fetch_all(yt):
    ch = yt.channels().list(part="contentDetails", mine=True).execute()["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, req = [], yt.playlistItems().list(part="contentDetails", playlistId=uploads, maxResults=50)
    while req:
        res = req.execute()
        ids += [i["contentDetails"]["videoId"] for i in res["items"]]
        req = yt.playlistItems().list_next(req, res)
    out = []
    for start in range(0, len(ids), 50):
        out += yt.videos().list(part="snippet,status,statistics",
                                id=",".join(ids[start:start + 50])).execute()["items"]
    return out


def run(apply: bool) -> int:
    from channel_seo import get_service  # token_channel.json, scope auth/youtube

    try:
        yt = get_service()
    except Exception as error:  # noqa: BLE001 - surface the consent requirement plainly
        print(f"AUTH FAILED: {error}")
        print("\ntoken_channel.json needs re-consent. Run:  python tools/channel_seo.py")
        print("That opens a browser consent screen — an operator action by design, because it")
        print("grants write access to the channel.")
        return 2

    videos = {v["id"]: v for v in fetch_all(yt)}
    by_title = {v["snippet"]["title"]: v for v in videos.values()}
    receipts = {"schema": "tradercockpit-channel-fixes/v1",
                "appliedAt": datetime.datetime.now(datetime.timezone.utc)
                             .isoformat(timespec="seconds").replace("+00:00", "Z"),
                "applied": apply, "changes": []}

    def record(vid, field, before, after, note, verified=None):
        receipts["changes"].append({"videoId": vid, "field": field, "before": before,
                                    "after": after, "note": note, "verified": verified})
        flag = "APPLY" if apply else "DRY  "
        print(f"  {flag} {vid} {field}: {str(before)[:34]!r} -> {str(after)[:34]!r}")

    # 1. visibility — promote, verify, then demote
    print("\n[1] VISIBILITY")
    promoted_ok = True
    for vid, note in PROMOTE:
        v = videos.get(vid)
        if not v:
            print(f"  MISS {vid} not on channel"); promoted_ok = False; continue
        before = v["status"]["privacyStatus"]
        if before == "public":
            print(f"  SKIP {vid} already public"); continue
        if apply:
            yt.videos().update(part="status", body={
                "id": vid, "status": {"privacyStatus": "public",
                "selfDeclaredMadeForKids": v["status"].get("selfDeclaredMadeForKids", False)}}).execute()
            after = yt.videos().list(part="status", id=vid).execute()["items"][0]["status"]["privacyStatus"]
            promoted_ok &= (after == "public")
            record(vid, "privacyStatus", before, after, note, after == "public")
        else:
            record(vid, "privacyStatus", before, "public", note)

    if promoted_ok:
        for vid, note in DEMOTE:
            v = videos.get(vid)
            if not v or v["status"]["privacyStatus"] != "public":
                print(f"  SKIP {vid} not public"); continue
            if apply:
                yt.videos().update(part="status", body={
                    "id": vid, "status": {"privacyStatus": "private",
                    "selfDeclaredMadeForKids": v["status"].get("selfDeclaredMadeForKids", False)}}).execute()
                after = yt.videos().list(part="status", id=vid).execute()["items"][0]["status"]["privacyStatus"]
                record(vid, "privacyStatus", "public", after, note, after == "private")
            else:
                record(vid, "privacyStatus", "public", "private", note)
    else:
        print("  ABORT dedupe — promote step did not verify; not reducing public content")

    # 2. titles
    print("\n[2] TITLES")
    for old, new in TITLES.items():
        v = by_title.get(old)
        if not v:
            print(f"  SKIP not found: {old[:50]}"); continue
        if apply:
            sn = v["snippet"]
            yt.videos().update(part="snippet", body={"id": v["id"], "snippet": {
                "title": new, "description": sn.get("description", ""),
                "categoryId": sn.get("categoryId", "25"), "tags": sn.get("tags") or []}}).execute()
            after = yt.videos().list(part="snippet", id=v["id"]).execute()["items"][0]["snippet"]["title"]
            record(v["id"], "title", old, after, "pre-playbook copy", after == new)
        else:
            record(v["id"], "title", old, new, "pre-playbook copy")

    # 3. tags on untagged public videos
    print("\n[3] TAGS (public videos with none)")
    for v in videos.values():
        if v["status"]["privacyStatus"] != "public" or (v["snippet"].get("tags") or []):
            continue
        sn = v["snippet"]
        title = TITLES.get(sn["title"], sn["title"])
        tags = topic_tags_for(title)
        if apply:
            yt.videos().update(part="snippet", body={"id": v["id"], "snippet": {
                "title": title, "description": sn.get("description", ""),
                "categoryId": sn.get("categoryId", "25"), "tags": tags}}).execute()
            after = yt.videos().list(part="snippet", id=v["id"]).execute()["items"][0]["snippet"].get("tags") or []
            record(v["id"], "tags", 0, len(after), sn["title"][:40], len(after) > 0)
        else:
            record(v["id"], "tags", 0, len(tags), sn["title"][:40])

    RECEIPTS.parent.mkdir(parents=True, exist_ok=True)
    RECEIPTS.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
    print(f"\n{len(receipts['changes'])} change(s) {'applied' if apply else 'planned'} -> {RECEIPTS}")
    if not apply:
        print("Re-run with --apply to execute.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="execute (default is a dry run)")
    raise SystemExit(run(parser.parse_args().apply))
