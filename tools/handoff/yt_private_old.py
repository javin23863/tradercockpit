# Private the 5 defective YT Shorts. videos().update needs the full 'youtube' scope
# (token_channel.json) — token.json is upload-only and 403s on update.
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, "tools")
from channel_seo import get_service  # token_channel.json, scope=youtube

OLD = ["FmZB2dj5eHY", "EQ7pUZF68Jc", "vweIA4Bc3ak", "MUPr0x8-cAc", "tzBCVGqMEvI"]
svc = get_service()

for vid in OLD:
    try:
        r = svc.videos().update(part="status", body={
            "id": vid, "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}).execute()
        print("privated", vid, "->", r["status"]["privacyStatus"])
    except Exception as e:
        print("FAIL", vid, str(e)[:160])

live = svc.videos().list(part="status,snippet", id=",".join(OLD)).execute()
for it in live.get("items", []):
    print(it["id"], it["status"]["privacyStatus"], "|", it["snippet"]["title"][:45])
