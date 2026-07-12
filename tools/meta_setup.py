#!/usr/bin/env python3
"""Turn ONE short-lived Meta user token into the 3 .env values publish.py needs.

Your only manual step: https://developers.facebook.com/tools/explorer → pick your app →
Generate Access Token with permissions:
  pages_show_list, pages_read_engagement, pages_manage_posts, publish_video,
  instagram_basic, instagram_content_publish
Copy that token, then run:

  python meta_setup.py --app-id APPID --app-secret SECRET --user-token SHORTLIVED

This exchanges it for a long-lived token, fetches your Page token (non-expiring) and
IG business id via the Graph API, and writes META_PAGE_ID / META_IG_USER_ID /
META_PAGE_TOKEN into OpenMontage/.env. No browser automation.
"""
import argparse
import re
import sys
from pathlib import Path

import requests

GRAPH = "https://graph.facebook.com/v25.0"
ENV = Path(__file__).parent.parent / "OpenMontage" / ".env"


def g(path, **params):
    r = requests.get(f"{GRAPH}/{path}", params=params, timeout=30).json()
    if "error" in r:
        sys.exit(f"Graph error at {path}: {r['error'].get('message')}")
    return r


def set_env(key, value):
    text = ENV.read_text()
    line = f"{key}={value}"
    if re.search(rf"(?m)^{key}=", text):
        text = re.sub(rf"(?m)^{key}=.*$", line, text)
    else:
        text += f"\n{line}\n"
    ENV.write_text(text)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--app-id", required=True)
    p.add_argument("--app-secret", required=True)
    p.add_argument("--user-token", required=True, help="short-lived token from Graph Explorer")
    args = p.parse_args()

    # 1. short-lived -> long-lived user token
    ll = g("oauth/access_token", grant_type="fb_exchange_token",
           client_id=args.app_id, client_secret=args.app_secret, fb_exchange_token=args.user_token)
    user_token = ll["access_token"]

    # 2. page id + page token (a page token derived from a long-lived user token does not expire)
    accts = g("me/accounts", access_token=user_token).get("data", [])
    if not accts:
        sys.exit("No Pages on this account. Create a Facebook Page and link your IG, then retry.")
    if len(accts) > 1:
        print("Multiple Pages found — using the first. Pages:")
        for a in accts:
            print(f"  {a['id']}  {a.get('name')}")
    page = accts[0]
    page_id, page_token = page["id"], page["access_token"]

    # 3. linked IG business account id
    ig = g(page_id, fields="instagram_business_account", access_token=page_token)
    ig_acct = ig.get("instagram_business_account", {}).get("id")
    if not ig_acct:
        print("WARNING: no Instagram business account linked to this Page. "
              "Link it (IG app → Settings → link Facebook Page) to enable IG Reels. FB will still work.")

    set_env("META_PAGE_ID", page_id)
    set_env("META_PAGE_TOKEN", page_token)
    if ig_acct:
        set_env("META_IG_USER_ID", ig_acct)

    print(f"\nWrote to {ENV}:")
    print(f"  META_PAGE_ID={page_id}  ({page.get('name')})")
    print(f"  META_IG_USER_ID={ig_acct or '(none — IG disabled)'}")
    print(f"  META_PAGE_TOKEN=<{len(page_token)} chars, non-expiring>")
    print("\nNext: fill B2_* in .env, then `python publish.py <video> --title ... --dry-run`")


if __name__ == "__main__":
    main()
