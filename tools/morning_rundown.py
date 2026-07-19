#!/usr/bin/env python3
"""Morning rundown: one dated vault report from the live operating surfaces.

Composes: vault hot cache head, latest analytics rollup, Manager health + top
needs, latest publish receipts, and today's automation schedule. Writes
TraderCockpit-Vault/wiki/reports/rundown-<stamp>.md and prints the path.
Stdlib only; read-only everywhere except the report file.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
VAULT = Path(r"C:\Users\MSI\Desktop\TraderCockpit-Vault")
REPORTS = VAULT / "wiki" / "reports"
ICT = timezone(timedelta(hours=7))

sys.path.insert(0, str(Path(__file__).parent))
from hq import latest_publish_entries, load_manager, read_json, ANALYTICS  # noqa: E402


def schedule_today(now):
    lanes = [
        ("Weekday market authority", (0, 1, 2, 3, 4), 17, 30),
        ("Saturday weekly recap", (5,), 17, 30),
        ("Sunday social review", (6,), 18, 0),
    ]
    lines = []
    for name, days, hour, minute in lanes:
        if now.weekday() in days:
            at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            state = "done or in flight" if now >= at else f"in {at - now}".split(".")[0]
            lines.append(f"- {name} at {at:%H:%M} ICT ({state})")
    return lines or ["- No automation lane scheduled today."]


def main():
    now = datetime.now(ICT)
    REPORTS.mkdir(parents=True, exist_ok=True)
    parts = [f"---\ntype: report\ncreated: {now:%Y-%m-%d}\ntags: [rundown, report]\n---\n",
             f"# Morning Rundown — {now:%Y-%m-%d %H:%M} ICT\n"]

    analytics, err = read_json(ANALYTICS)
    rollup = (analytics or {}).get("rollup", {}) if isinstance(analytics, dict) else {}
    parts.append("## Platforms (last snapshot)\n")
    if rollup:
        parts.append(
            f"- YouTube weekly views {rollup.get('youtubeWeeklyViews', '?')} · IG {rollup.get('instagramObservedViews', '?')}"
            f" · FB {rollup.get('facebookObservedViews', '?')} · TikTok {rollup.get('tiktokObservedViews', '?')}"
            f" (generated {(analytics or {}).get('generatedAt', 'unknown')})")
    else:
        parts.append(f"- Analytics snapshot unavailable: {err}")

    latest, _ = latest_publish_entries()
    parts.append("\n## Latest publish receipts\n")
    if latest:
        for platform, entry in sorted(latest.items()):
            parts.append(f"- {platform}: {entry.get('status')} · {entry.get('production')} · {entry.get('timestamp')} · {entry.get('url') or 'no URL'}")
    else:
        parts.append("- No publish receipts found.")

    manager, m_err = load_manager()
    parts.append("\n## Manager\n")
    if manager:
        metrics = manager.get("metrics", {})
        parts.append(f"- Revision {manager.get('revision')} · healthy={manager.get('healthy')} · issues: {'; '.join(manager.get('issues', [])) or 'none'}")
        parts.append(f"- Sol decision queue {metrics.get('sol_decision_queues', '?')} · acceptance backlog {metrics.get('acceptance_backlog', '?')}")
        needs = [n for n in manager.get("nodes", []) if isinstance(n, dict) and (n.get("lifecycle") == "verify" or n.get("blocked"))]
        for node in needs[:5]:
            parts.append(f"- NEEDS YOU: {node.get('id')} — {node.get('title')}")
        if len(needs) > 5:
            parts.append(f"- …and {len(needs) - 5} more in the HQ Needs You view")
    else:
        parts.append(f"- {m_err}")

    parts.append("\n## Today\n")
    parts.extend(schedule_today(now))

    hot = VAULT / "_meta" / "hot.md"
    if hot.is_file():
        head = [l for l in hot.read_text(encoding="utf-8-sig").splitlines() if l.strip()][:14]
        parts.append("\n## Vault hot cache (head)\n")
        parts.extend(f"> {line}" for line in head)

    out = REPORTS / f"rundown-{now:%Y-%m-%d-%H%M}.md"
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
