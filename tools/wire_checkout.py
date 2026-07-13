#!/usr/bin/env python3
"""Wire the real Lemon Squeezy checkout into everything that references it.

Run ONCE after the LS store + product exist (see SETUP-LEMONSQUEEZY.md):

    python tools/wire_checkout.py https://tradercockpit.lemonsqueezy.com/buy/<uuid>

Patches:
  docs/index.html                                   buy button href (keeps ?embed=1)
  <futures>/apps/cockpit/frontend/src/views/Activation.tsx   BUY_URL

Then commit/push soical yourself and rebuild the customer exe for Activation.tsx
to take effect. Idempotent: re-running with the same URL is a no-op.
"""
import re
import sys
from pathlib import Path

HUB = Path(__file__).resolve().parents[1]
INDEX = HUB / "docs" / "index.html"
ACTIVATION = Path(r"C:\Users\MSI\repos\futures\apps\cockpit\frontend\src\views\Activation.tsx")


def main() -> int:
    if len(sys.argv) != 2 or "lemonsqueezy.com" not in sys.argv[1]:
        print(__doc__)
        return 2
    url = sys.argv[1].split("?")[0].rstrip("/")
    if "/buy/" not in url:
        print(f"expected a .../buy/<uuid> share link, got: {url}")
        return 2

    html = INDEX.read_text(encoding="utf-8")
    new_html, n = re.subn(
        r'href="https://[^"]*lemonsqueezy\.com/buy/[^"]*"',
        f'href="{url}?embed=1&media=0"', html, count=1)
    if n:
        INDEX.write_text(new_html, encoding="utf-8")
    print(f"index.html: {'patched' if n else 'NO buy href found (already wired?)'}")

    tsx = ACTIVATION.read_text(encoding="utf-8")
    store_root = url.split("/buy/")[0]
    new_tsx, n = re.subn(
        r'const BUY_URL = "[^"]*";.*', f'const BUY_URL = "{store_root}";', tsx, count=1)
    if n:
        ACTIVATION.write_text(new_tsx, encoding="utf-8")
    print(f"Activation.tsx: {'patched' if n else 'NO BUY_URL line found'}")

    print("\nnext: git -C", HUB, "add docs/index.html && commit && push;"
          " rebuild customer exe for the app-side link.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
