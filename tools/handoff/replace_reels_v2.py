# Round 2 replace (2026-07-14, "go"): delete the squeezed-render IG/FB reels,
# post the dual-treatment re-renders. Run from repo root with OpenMontage venv python.
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, "tools")
from pathlib import Path
import requests
from dotenv import load_dotenv
load_dotenv("OpenMontage/.env")
from publish import publish_instagram, publish_facebook

G = "https://graph.facebook.com/v25.0"
tok = os.getenv("META_PAGE_TOKEN")
ig_user = os.getenv("META_IG_USER_ID")
S = "productions/video-02-hormuz-v4/shorts"
TAGS = "#oil #brentcrude #hormuz #stockmarket #trading #investing #markets #energystocks #geopolitics #tradercockpit"

# clip base -> (caption, live IG shortcode, live FB video id)  [handoff §1, posted 2026-07-14]
CLIPS = [
 ("clip-006-segment-1",
  "Trump just put a 20% toll on every ship through the Strait of Hormuz - and oil ripped 10% in a day. Here's what it means for your portfolio. 🛢️ Full breakdown on the channel.",
  "Daw02rkgkU1", "4357168464496095"),
 ("clip-003-hook-3-so-how-high-can-crude",
  "How high can oil actually go? Every big desk's number - Goldman, JPMorgan, gov models - on one chart. $100 to $150. None of them models it sitting still. 📈",
  "Daw09z3lH84", "27470633242576762"),
 ("clip-001-hook-1-is-the-straight-actually-closed-",
  "Is the Strait of Hormuz actually closed? Wrong question. The right one moves oil. 🚢",
  "Daw1HvdDJs0", "1047470668194415"),
 ("clip-002-hook-2-because-83-crude-flows-straight",
  "$83 crude flows straight into producer earnings. Exxon +4%, Chevron +3% on the day. The war-premium rotation, one chart deeper. ⛽",
  "Daw1OVBjREf", "1058932556575181"),
 ("clip-004-hook-4-but-the-headline-number-matters",
  "5 big banks report before the bell. The headline EPS matters less than 3 lines inside: net interest income, trading revenue, credit provisions. 🏦",
  "Daw1UY9jPpY", "1083637374193768"),
]

# map IG shortcodes -> media ids
media = requests.get(f"{G}/{ig_user}/media", params={"fields": "id,shortcode", "limit": 50, "access_token": tok}).json()
sc2id = {m["shortcode"]: m["id"] for m in media.get("data", [])}
print("IG media found:", sc2id)

for base, cap, sc, fb_id in CLIPS:
    ig_id = sc2id.get(sc)
    for label, mid in (("IG", ig_id), ("FB", fb_id)):
        if not mid:
            print(f"del {label} {sc}: NOT FOUND, skip"); continue
        r = requests.delete(f"{G}/{mid}", params={"access_token": tok})
        print(f"del {label} {mid}:", r.json())

for base, cap, sc, fb_id in CLIPS:
    vid = Path(S) / f"{base}.vertical.mp4"
    caption = f"{cap} {TAGS}"
    print(f"\n=== {base} ===")
    try:
        print("FB:", publish_facebook(vid, caption))
    except SystemExit as e:
        print("FB FAIL:", e)
    try:
        print("IG:", publish_instagram(vid, caption))
    except SystemExit as e:
        print("IG FAIL:", e)
print("\nDONE reels replace v2")
