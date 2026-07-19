#!/usr/bin/env python3
"""Operator attention primitive: send an approval/attention ping via Telegram.

Token lives in operator custody (telegram.env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).
Usage:
  py tools/notify_telegram.py "message text"        # send
  py tools/notify_telegram.py --whoami              # discover chat id (operator must message the bot first)
Never prints the token. Stdlib only.
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

try:
    from tools.credential_custody import credential_path
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).parent))
    from credential_custody import credential_path


def _env():
    path = credential_path("telegram.env")
    if not path.is_file():
        raise SystemExit("BLOCK: telegram.env absent from operator custody")
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    if "TELEGRAM_BOT_TOKEN" not in values:
        raise SystemExit("BLOCK: TELEGRAM_BOT_TOKEN missing from telegram.env")
    return values


def _api(token, method, params=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params or {}).encode()
    with urllib.request.urlopen(url, data=data, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def whoami():
    env = _env()
    result = _api(env["TELEGRAM_BOT_TOKEN"], "getUpdates")
    chats = {}
    for update in result.get("result", []):
        message = update.get("message") or update.get("edited_message") or {}
        chat = message.get("chat") or {}
        if chat.get("id"):
            chats[chat["id"]] = chat.get("username") or chat.get("first_name") or "?"
    if not chats:
        print("no updates: send any message to the bot in Telegram first, then rerun --whoami")
        return 1
    for chat_id, name in chats.items():
        print(f"chat_id={chat_id} ({name})")
    print(f"add to custody telegram.env: TELEGRAM_CHAT_ID={next(iter(chats))}")
    return 0


def send(text):
    env = _env()
    chat_id = env.get("TELEGRAM_CHAT_ID")
    if not chat_id:
        raise SystemExit("BLOCK: TELEGRAM_CHAT_ID missing - run --whoami after messaging the bot")
    result = _api(env["TELEGRAM_BOT_TOKEN"], "sendMessage", {"chat_id": chat_id, "text": text[:4000]})
    if not result.get("ok"):
        raise SystemExit(f"BLOCK: sendMessage failed: {result.get('description', 'unknown')}")
    print(f"sent message_id={result['result']['message_id']}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--whoami":
        raise SystemExit(whoami())
    if len(sys.argv) > 1 and sys.argv[1].strip():
        raise SystemExit(send(sys.argv[1]))
    raise SystemExit(__doc__)
