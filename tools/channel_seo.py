#!/usr/bin/env python3
"""Apply TraderCockpit channel SEO (description + keywords) via YouTube Data API.

Needs the broader 'youtube' scope (channel branding), not just youtube.upload —
first run opens browser consent and caches token_channel.json separately so the
upload token keeps working untouched.

Run: python channel_seo.py [--dry-run]
"""
import argparse
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/youtube"]
HERE = Path(__file__).parent

DESCRIPTION = """Every trading strategy the internet sells you — coded honestly and executed through 12 phases of statistical torture. ICT, SMC, supply & demand, price action: if it can be written as falsifiable rules, it enters the gauntlet. Monte-Carlo shuffles, walk-forward, cost stress at 3x slippage, deflated Sharpe — whatever survives, survives. Whatever dies, dies on camera.

No signals. No courses. No lambo. A research machine that refuses to say "validated" until the receipts exist — and publishes the kill list either way.

Research instrument, paper-only by design. Nothing here is financial advice and no performance is promised or implied.

Run the mini-gauntlet: https://javin23863.github.io/soical/"""

KEYWORDS = ('"trading strategy backtest" "ICT trading tested" "smart money concepts" SMC '
            '"quant trading" "algorithmic trading" "monte carlo trading" "walk-forward analysis" '
            '"backtest overfitting" "futures trading" "trading strategy tested" "honest backtest"')


def get_service():
    creds = None
    token = HERE / "token_channel.json"
    if token.exists():
        creds = Credentials.from_authorized_user_file(token, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret = HERE / "client_secret.json"
            if not secret.exists():
                sys.exit(f"Missing {secret}")
            creds = InstalledAppFlow.from_client_secrets_file(secret, SCOPES).run_local_server(
                port=8766, open_browser=True,
                authorization_prompt_message="OPEN THIS URL TO APPROVE (channel scope): {url}")
        token.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.dry_run:
        print("Would set description:\n" + DESCRIPTION)
        print("\nWould set keywords:\n" + KEYWORDS)
        return

    yt = get_service()
    chans = yt.channels().list(part="id,brandingSettings", mine=True).execute()["items"]
    if not chans:
        sys.exit("no channel on this account")
    ch = chans[0]
    branding = ch["brandingSettings"]
    branding.setdefault("channel", {})
    branding["channel"]["description"] = DESCRIPTION
    branding["channel"]["keywords"] = KEYWORDS
    branding["channel"]["unsubscribedTrailer"] = branding["channel"].get("unsubscribedTrailer", "")
    yt.channels().update(part="brandingSettings",
                         body={"id": ch["id"], "brandingSettings": branding}).execute()
    print(f"Channel SEO applied to {ch['id']}: description + keywords set.")


if __name__ == "__main__":
    main()
