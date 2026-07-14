import sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, "tools")
from pathlib import Path
import requests
from dotenv import load_dotenv
load_dotenv("OpenMontage/.env")
from publish import publish_instagram, publish_facebook

G = "https://graph.facebook.com/v25.0"
tok = os.getenv("META_PAGE_TOKEN")
S = "productions/video-02-hormuz-v4/shorts"
TAGS = "#oil #brentcrude #hormuz #stockmarket #trading #investing #markets #energystocks #geopolitics #tradercockpit"

# clip -> (file, caption, old IG media id, old FB reel id)
CLIPS = [
 ("clip-006-segment-1",
  "Trump just put a 20% toll on every ship through the Strait of Hormuz - and oil ripped 10% in a day. Here's what it means for your portfolio. 🛢️ Full breakdown on the channel.",
  "17897786136498958", "1061795756535144"),
 ("clip-003-hook-3-so-how-high-can-crude",
  "How high can oil actually go? Every big desk's number - Goldman, JPMorgan, gov models - on one chart. $100 to $150. None of them models it sitting still. 📈",
  "18117531187912594", "1021488570615156"),
 ("clip-001-hook-1-is-the-straight-actually-closed-",
  "Is the Strait of Hormuz actually closed? Wrong question. The right one moves oil. 🚢",
  "18052395011534773", "897703199433476"),
 ("clip-002-hook-2-because-83-crude-flows-straight",
  "$83 crude flows straight into producer earnings. Exxon +4%, Chevron +3% on the day. The war-premium rotation, one chart deeper. ⛽",
  "18346383835172078", "27463594969973874"),
 ("clip-004-hook-4-but-the-headline-number-matters",
  "5 big banks report before the bell. The headline EPS matters less than 3 lines inside: net interest income, trading revenue, credit provisions. 🏦",
  "18239624254312401", "1344054473899934"),
]

# 1) delete old (both platforms)
for base, cap, ig_id, fb_id in CLIPS:
    for mid in (ig_id, fb_id):
        r = requests.delete(f"{G}/{mid}", params={"access_token": tok})
        print("del", mid, r.json())

# 2) post corrected to FB then IG
for base, cap, ig_id, fb_id in CLIPS:
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
print("\nDONE reels replace")
