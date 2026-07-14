# Private the 5 squeezed YT Shorts, upload the 5 corrected re-renders.
# Uploads cost 1600 quota units each (daily cap 10,000) -> 5 uploads = 8000 units.
# Run from repo root with the OpenMontage venv python.
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.path.insert(0, "tools")
from pathlib import Path
from upload_youtube import get_service, upload

S = Path("productions/video-02-hormuz-v4/shorts")
TAGS = ["oil", "brent crude", "hormuz", "stock market", "investing", "energy stocks", "trading"]
LONGFORM = "https://youtu.be/IJjUNeuJSNE"

# live (defective) short id -> (file base, title, description hook)
CLIPS = [
    ("FmZB2dj5eHY", "clip-006-segment-1",
     "Trump's 20% Hormuz Toll Sent Oil Up 10% #shorts",
     "Trump just put a 20% toll on every ship through the Strait of Hormuz - and oil ripped 10% in a day. What it means for your portfolio."),
    ("EQ7pUZF68Jc", "clip-003-hook-3-so-how-high-can-crude",
     "How High Can Oil Actually Go? $100-$150 #shorts",
     "Every big desk's number - Goldman, JPMorgan, government models - on one chart. None of them models it sitting still."),
    ("vweIA4Bc3ak", "clip-001-hook-1-is-the-straight-actually-closed-",
     "Is the Strait of Hormuz Actually Closed? #shorts",
     "Wrong question. The right one moves oil: 5 vessels last week vs 130 a day before the war."),
    ("MUPr0x8-cAc", "clip-002-hook-2-because-83-crude-flows-straight",
     "$83 Crude Flows Straight Into Producer Earnings #shorts",
     "Exxon +4%, Chevron +3% on the day. The war-premium rotation, one chart deeper."),
    ("tzBCVGqMEvI", "clip-004-hook-4-but-the-headline-number-matters",
     "5 Big Banks Report: Watch These 3 Lines #shorts",
     "The headline EPS matters less than net interest income, trading revenue, and credit provisions."),
]

svc = get_service()

# 1) private the defective ones
for vid, *_ in CLIPS:
    try:
        svc.videos().update(part="status", body={"id": vid, "status": {
            "privacyStatus": "private", "selfDeclaredMadeForKids": False}}).execute()
        print("privated", vid)
    except Exception as e:
        print("privatize FAIL", vid, str(e)[:120])

# 2) upload corrected
for _, base, title, hook in CLIPS:
    f = S / f"{base}.vertical.mp4"
    desc = f"{hook}\n\nFull breakdown: {LONGFORM}\n\n#shorts #oil #stockmarket #investing #markets\n\nNot financial advice."
    print(f"\n=== {title}")
    try:
        r = upload(str(f), title, desc, TAGS, "25", "public")
        print("uploaded:", r)
    except Exception as e:
        print("UPLOAD FAIL:", str(e)[:200])
print("\nDONE yt shorts replace")
