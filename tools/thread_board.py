"""Codex thread board: what every recent thread is doing, from session rollouts."""
import json, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.home() / ".codex" / "sessions"
HOURS = float(sys.argv[1]) if len(sys.argv) > 1 else 36

now = datetime.now(timezone.utc)
rows = []
for f in ROOT.rglob("rollout-*.jsonl"):
    age_h = (now - datetime.fromtimestamp(f.stat().st_mtime, timezone.utc)).total_seconds() / 3600
    if age_h > HOURS:
        continue
    meta, first_user, last_asst, turns = {}, None, None, 0
    try:
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                try:
                    j = json.loads(line)
                except Exception:
                    continue
                t = j.get("type")
                p = j.get("payload", {})
                if t == "session_meta":
                    src = p.get("source")
                    meta = {
                        "cwd": p.get("cwd", "?"),
                        "source": src if isinstance(src, str) else json.dumps(src)[:40],
                        "thread_source": p.get("thread_source", "?"),
                        "originator": p.get("originator", "?"),
                    }
                elif t == "event_msg" and p.get("type") == "user_message":
                    m = p.get("message", "")
                    if m and not m.startswith("<") and first_user is None:
                        first_user = m[:180]
                    turns += 1
                elif t == "response_item" and p.get("type") == "message" and p.get("role") == "assistant":
                    txt = "".join(c.get("text", "") for c in p.get("content", []) if isinstance(c, dict))
                    if txt:
                        last_asst = txt[-500:] if len(txt) > 500 else txt
    except OSError:
        continue
    if meta.get("thread_source") == "subagent":
        continue  # guardian/judge helpers, noise
    rows.append({
        "file": f.name[:60],
        "age_h": round(age_h, 1),
        "cwd": meta.get("cwd", "?"),
        "originator": meta.get("originator", "?"),
        "turns": turns,
        "first_user": (first_user or "(no user msg)")[:170],
        "last_asst": (last_asst or "(no assistant msg)")[:400],
    })

rows.sort(key=lambda r: r["age_h"])
print(f"{len(rows)} threads active in last {HOURS}h\n")
for r in rows:
    print("=" * 90)
    print(f"[{r['age_h']}h ago] {r['cwd']}  ({r['originator']}, {r['turns']} user turns)  {r['file']}")
    print(f"  TASK: {r['first_user']}")
    print(f"  LAST: {r['last_asst'][:380]}")
