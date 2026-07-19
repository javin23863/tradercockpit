#!/usr/bin/env python3
"""Read-only TraderCockpit Operator HQ.

Run: python tools/hq.py [--serve] [--no-open] [--check]
"""

import argparse
import html
import json
import os
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import URLError
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import urlopen

try:
    from .dashboard import leg_status
    from .growth_experiments import load_growth_summary
except ImportError:  # direct script execution
    from dashboard import leg_status
    from growth_experiments import load_growth_summary


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "operator-hq.html"
DEPARTMENTS = Path(r"C:\Users\MSI\Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit\GTM\Departments")
ANALYTICS = ROOT / "social-ops" / "analytics-latest.json"
OUTLIERS = ROOT / "social-ops" / "youtube-outlier-backlog.json"
MANAGER_URL = "http://127.0.0.1:8790/state"
HOST, PORT = "127.0.0.1", 8786
VIEWS = (
    ("departments", "Departments"),
    ("platforms", "Platforms"),
    ("ads", "Ads Pipeline"),
    ("kanban", "Kanban"),
    ("needs", "Needs You"),
)
PLATFORMS = (
    ("youtube", "YouTube"),
    ("instagram", "Instagram"),
    ("facebook", "Facebook"),
    ("tiktok", "TikTok"),
)


def esc(value):
    return html.escape(str(value if value is not None else ""))


def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig")), None
    except FileNotFoundError:
        return None, f"{path.relative_to(ROOT) if path.is_relative_to(ROOT) else path} is absent."
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return None, f"{path.name} is unreadable: {type(error).__name__}."


def parse_frontmatter(text):
    """Parse the flat scalar/list fields used by department pages, not general YAML."""
    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    result = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line or line[0].isspace() or line.lstrip().startswith("-"):
            continue
        key, separator, raw = line.partition(":")
        if not separator:
            continue
        raw = raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            result[key.strip()] = [item.strip().strip("\"'") for item in raw[1:-1].split(",") if item.strip()]
        else:
            result[key.strip()] = raw.strip("\"'")
    return result


def load_departments():
    if not DEPARTMENTS.is_dir():
        return [], f"Department directory is absent: {DEPARTMENTS}"
    rows, errors = [], []
    for path in sorted(DEPARTMENTS.glob("*.md"), key=lambda item: item.name.casefold()):
        try:
            data = parse_frontmatter(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError) as error:
            data = {}
            errors.append(f"{path.name}: {type(error).__name__}")
        rows.append({"path": path, "title": data.get("title") or path.stem, **data})
    return rows, "; ".join(errors) or None


def load_manager():
    try:
        with urlopen(MANAGER_URL, timeout=2) as response:  # noqa: S310 - fixed localhost URL
            payload = json.load(response)
        if not isinstance(payload, dict):
            raise ValueError("snapshot is not an object")
        return payload, None
    except (OSError, URLError, ValueError, json.JSONDecodeError) as error:
        return None, f"Manager is offline or invalid ({type(error).__name__})."


def load_growth():
    try:
        return load_growth_summary()
    except (OSError, ValueError) as error:
        return {"valid": False, "error": str(error)}


def latest_publish_entries():
    latest, errors = {}, []
    for path in sorted((ROOT / "productions").glob("*/publish_log.json")):
        data, error = read_json(path)
        if error:
            errors.append(error)
            continue
        entries = data.get("entries") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            errors.append(f"{path.parent.name}/publish_log.json has no entries list.")
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            platform = str(entry.get("platform", "")).lower()
            if platform not in dict(PLATFORMS):
                continue
            candidate = {**entry, "production": path.parent.name}
            if platform not in latest or str(candidate.get("timestamp", "")) > str(latest[platform].get("timestamp", "")):
                latest[platform] = candidate
    return latest, errors


def outlier_count():
    data, error = read_json(OUTLIERS)
    if error:
        return None, error
    if isinstance(data, list):
        return len(data), None
    if isinstance(data, dict):
        for key in ("items", "videos", "candidates", "backlog"):
            if isinstance(data.get(key), list):
                return len(data[key]), None
    return None, "youtube-outlier-backlog.json has no recognized item list."


def badge(text, kind="muted"):
    return f'<span class="badge {kind}">{esc(str(text).upper())}</span>'


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "—"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def safe_web_url(value):
    value = str(value or "")
    return value if value.startswith(("https://", "http://")) else ""


def empty(message):
    return f'<div class="empty">{esc(message)}</div>'


def render_departments():
    departments, error = load_departments()
    cards = []
    for item in departments:
        status = str(item.get("status") or "unknown").lower()
        kind = "ok" if status == "active" else "warn" if status in {"dormant", "paused"} else "muted"
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []
        file_url = "file:///" + quote(item["path"].as_posix(), safe="/:")
        cards.append(
            '<article class="card department">'
            f'<div class="card-head"><a href="{esc(file_url)}"><h2>{esc(item["title"])}</h2></a>{badge(status, kind)}</div>'
            f'<p class="muted">Updated {esc(item.get("updated") or "not recorded")}</p>'
            f'<div class="tags">{"".join(f"<span>{esc(tag)}</span>" for tag in tags) or "<span>no tags recorded</span>"}</div>'
            f'<p><a href="{esc(file_url)}">Open department page</a></p></article>'
        )
    notice = empty(error) if error else ""
    content = "".join(cards) or empty(f"No department Markdown pages found in {DEPARTMENTS}.")
    return f'<section class="section-head"><div><h1>Departments</h1><p>Live status from vault frontmatter.</p></div></section>{notice}<div class="cards">{content}</div>'


def platform_metric(label, value):
    return f'<div class="metric"><strong>{esc(number(value))}</strong><small>{esc(label)}</small></div>'


def render_platforms():
    analytics, analytics_error = read_json(ANALYTICS)
    analytics = analytics if isinstance(analytics, dict) else {}
    sources, rollup = analytics.get("sources", {}), analytics.get("rollup", {})
    sources = sources if isinstance(sources, dict) else {}
    rollup = rollup if isinstance(rollup, dict) else {}
    latest, publish_errors = latest_publish_entries()
    try:
        legs = leg_status()
    except Exception as error:  # dashboard helper is an external status probe
        legs = {}
        publish_errors.append(f"Publish-leg probe failed: {type(error).__name__}.")
    backlog_count, backlog_error = outlier_count()
    view_keys = {
        "youtube": "youtubeWeeklyViews",
        "instagram": "instagramObservedViews",
        "facebook": "facebookObservedViews",
        "tiktok": "tiktokObservedViews",
    }
    cards = []
    for key, label in PLATFORMS:
        source = sources.get(key, {}) if isinstance(sources.get(key), dict) else {}
        if key == "tiktok":
            ready = source.get("status") == "ready"
            readiness = badge("session" if ready else "not ready", "ok" if ready else "warn")
        elif key in legs:
            readiness = badge("ready" if legs[key] else "not ready", "ok" if legs[key] else "warn")
        else:
            readiness = badge("unknown", "muted")
        followers = source.get("subscribers") if key == "youtube" else source.get("followers", source.get("fans"))
        posts = source.get("posts")
        post_count = len(posts) if isinstance(posts, list) else None
        account = source.get("account") or "No connected account in analytics snapshot."
        metrics = (
            platform_metric("observed views", rollup.get(view_keys[key]))
            + platform_metric("subscribers" if key == "youtube" else "followers", followers)
            + platform_metric("tracked posts", post_count)
        )
        desk = ""
        if key == "youtube":
            weekly = source.get("weekly") if isinstance(source.get("weekly"), dict) else {}
            desk = (
                '<div class="desk"><h3>YouTube Desk KPIs</h3><div class="metrics">'
                + platform_metric("weekly views", weekly.get("views"))
                + platform_metric("outlier ideas", backlog_count)
                + platform_metric("videos", source.get("videoCount"))
                + "</div>"
                + (f'<p class="muted">{esc(backlog_error)}</p>' if backlog_error else "")
                + "</div>"
            )
        receipt = latest.get(key)
        if receipt:
            raw_url = receipt.get("url")
            url = safe_web_url(raw_url)
            if not url and key == "facebook" and str(raw_url or "").startswith("/"):
                url = "https://www.facebook.com" + str(raw_url)
            link = f'<a href="{esc(url)}">open publication</a>' if url else "no publication URL"
            receipt_html = (
                '<div class="receipt"><strong>Latest publish receipt</strong>'
                f'<p>{badge(receipt.get("status", "unknown"), "ok" if receipt.get("status") == "published" else "warn")} '
                f'{esc(receipt.get("production"))} · {esc(receipt.get("timestamp") or "no timestamp")} · {link}</p></div>'
            )
        else:
            receipt_html = empty(f"No {label} publish receipt found in productions/*/publish_log.json.")
        cards.append(
            '<article class="card platform">'
            f'<div class="card-head"><div><h2>{esc(label)}</h2><p class="muted">{esc(account)}</p></div>{readiness}</div>'
            f'<div class="metrics">{metrics}</div>{desk}{receipt_html}</article>'
        )
    notices = [message for message in [analytics_error, *publish_errors] if message]
    notice_html = "".join(empty(message) for message in notices)
    generated = analytics.get("generatedAt") or "no analytics snapshot"
    return f'<section class="section-head"><div><h1>Platforms</h1><p>Analytics generated {esc(generated)} · live publish-leg readiness.</p></div></section>{notice_html}<div class="cards platform-grid">{"".join(cards)}</div>'


def render_ads(summary):
    paid = summary.get("paidActivation", "unknown")
    paid_badge = "" if paid == "enabled" else '<span class="paid-disabled">PAID ACTIVATION DISABLED</span>'
    if not summary.get("valid"):
        return (
            f'<section class="section-head"><div><h1>Ads Pipeline</h1><p>Read-only growth contract.</p></div>{paid_badge}</section>'
            + empty(f"Growth summary is unavailable: {summary.get('error', 'unknown error')}")
        )
    library_counts = summary.get("libraryCounts", {})
    experiment_counts = summary.get("experimentStateCounts", {})
    experiments = summary.get("experiments", [])
    library_states = {
        state: sum(counts.get(state, 0) for counts in library_counts.values() if isinstance(counts, dict))
        for state in ("active", "hypothesis", "blocked")
    }
    observations = [item for experiment in experiments for item in experiment.get("observations", [])]
    metrics_count = sum(bool(item.get("hasMetrics")) for item in observations)
    decisions = sum((experiment.get("decision") or {}).get("verdict") not in {None, "", "pending"} for experiment in experiments)
    total_experiments = sum(experiment_counts.values())
    stages = (
        ("Hopper", experiment_counts.get("proposed", 0), "proposed ideas"),
        ("Libraries", sum(library_states.values()), " · ".join(f"{key} {value}" for key, value in library_states.items())),
        ("Experiment", total_experiments, " · ".join(f"{key} {value}" for key, value in experiment_counts.items())),
        ("Batch", len(observations), "referenced batch items"),
        ("Approval", "—", "not tracked by growth summary"),
        ("Publish", "—", "not tracked by growth summary"),
        ("Metrics", metrics_count, "items with joined metrics"),
        ("Decision", decisions, "operator decisions recorded"),
    )
    flow = "".join(
        f'<article class="stage"><small>STAGE {index}</small><h2>{esc(name)}</h2><strong>{esc(count)}</strong><p>{esc(note)}</p></article>'
        for index, (name, count, note) in enumerate(stages, 1)
    )
    return (
        f'<section class="section-head"><div><h1>Ads Pipeline</h1><p>Growth contract updated {esc(summary.get("updatedAt", "unknown"))}.</p></div>{paid_badge}</section>'
        f'<div class="pipeline">{flow}</div>'
        '<p class="muted">Approval and publish remain deliberately uncounted until those receipts join the growth summary; zero would falsely claim that nothing shipped.</p>'
    )


def manager_card(node):
    data = node.get("data") if isinstance(node.get("data"), dict) else {}
    blocked = f'<p class="blocked">Blocked: {esc(data.get("blocker") or "reason not recorded")}</p>' if node.get("blocked") else ""
    return (
        '<article class="work-card">'
        f'<small>{esc(node.get("id", "unknown id"))}</small><h3>{esc(node.get("title", "Untitled"))}</h3>'
        f'<div class="tags"><span>{esc(data.get("owner", "unknown owner"))}</span><span>{esc(data.get("effort", "unknown effort"))}</span></div>'
        f'<p>{esc(data.get("next_action") or "No next action recorded.")}</p>{blocked}</article>'
    )


def render_kanban(manager, error):
    if not manager:
        return (
            '<section class="section-head"><div><h1>Kanban</h1><p>Manager work-item lifecycle.</p></div></section>'
            + empty(f"{error} Start it from C:\\Users\\MSI\\Documents\\Manager with: py manager.py serve")
        )
    kanban = manager.get("kanban")
    if not isinstance(kanban, dict):
        return '<section class="section-head"><div><h1>Kanban</h1></div></section>' + empty("Manager snapshot has no kanban dictionary.")
    order = [state for state in ("inbox", "ready", "active", "verify", "done", "parked") if state in kanban]
    order.extend(state for state in kanban if state not in order)
    columns = "".join(
        f'<section class="column"><div class="column-head"><h2>{esc(state.title())}</h2>{badge(len(items) if isinstance(items, list) else 0)}</div>'
        f'{"".join(manager_card(node) for node in items if isinstance(node, dict)) if isinstance(items, list) else empty("Invalid column data.")}'
        f'{empty("No work items.") if isinstance(items, list) and not items else ""}</section>'
        for state in order
        for items in [kanban.get(state)]
    )
    return (
        f'<section class="section-head"><div><h1>Kanban</h1><p>Manager revision {esc(manager.get("revision", "unknown"))} · generated {esc(manager.get("generated_at", "unknown"))}.</p></div></section>'
        f'<div class="board">{columns or empty("Manager returned no Kanban columns.")}</div>'
    )


def manager_needs(manager):
    items = []
    for node in (manager or {}).get("nodes", []):
        if not isinstance(node, dict) or not (node.get("lifecycle") == "verify" or node.get("blocked") is True):
            continue
        data = node.get("data") if isinstance(node.get("data"), dict) else {}
        options = []
        if node.get("lifecycle") == "verify":
            options.extend(("Accept the recorded evidence and move this item to done.", "Return it to active and name the missing receipt or correction."))
        if node.get("blocked") is True:
            blocker = data.get("blocker") or data.get("next_action") or "the recorded blocker"
            options.extend((f"Resolve: {blocker}", "Keep it blocked and confirm the next review date."))
        items.append({
            "source": "Manager",
            "title": node.get("title") or node.get("id") or "Untitled Manager item",
            "detail": f"{node.get('id', 'unknown id')} · lifecycle {node.get('lifecycle', 'unknown')}" + (" · blocked" if node.get("blocked") else ""),
            "options": options,
        })
    return items


def file_needs():
    items, notes = [], []
    for path in sorted((ROOT / "productions").glob("*/script-approval.json")):
        data, error = read_json(path)
        if error:
            notes.append(error)
            continue
        status = str(data.get("status", "unknown")).lower() if isinstance(data, dict) else "unknown"
        if status == "approved":
            continue
        items.append({
            "source": "Script approval",
            "title": path.parent.name,
            "detail": f"Status {status}. {data.get('nextGate') or 'No next gate recorded.'}",
            "options": (
                "Approve the exact script hash after review.",
                "Request a revision and require a new hash.",
                "Reject it with concrete reasons and keep production blocked.",
            ),
        })
    for path in sorted((ROOT / "productions").glob("*/social-batch.json")):
        data, error = read_json(path)
        if error:
            notes.append(error)
            continue
        batch_items = data.get("items") if isinstance(data, dict) else None
        if not isinstance(batch_items, list):
            notes.append(f"{path.parent.name}/social-batch.json has no items list.")
            continue
        for item in batch_items:
            if not isinstance(item, dict) or str(item.get("status", "")).lower() != "draft":
                continue
            channel = item.get("channel") or "unknown channel"
            items.append({
                "source": "Social draft",
                "title": item.get("title") or item.get("id") or path.parent.name,
                "detail": f"{path.parent.name} · {channel} · {item.get('asset') or 'no asset recorded'}",
                "options": (
                    f"Approve this exact asset and copy hash for {channel}.",
                    "Request an edit and require a new item/hash.",
                    "Drop the draft from this publication batch.",
                ),
            })
    return items, notes


def experiment_needs(summary):
    items = []
    if not summary.get("valid"):
        return items, [f"Growth summary unavailable: {summary.get('error', 'unknown error')}"]
    for experiment in summary.get("experiments", []):
        advisory = experiment.get("advisory") if isinstance(experiment.get("advisory"), dict) else {}
        decision = experiment.get("decision") if isinstance(experiment.get("decision"), dict) else {}
        verdict = advisory.get("verdict")
        if not verdict or decision.get("verdict") not in {None, "", "pending"}:
            continue
        if verdict in {"kill", "iterate", "reuse"}:
            options = (f"Accept the advisory {verdict} verdict with an operator reason.", "Choose a different kill / iterate / reuse verdict and record why.", "Keep pending and collect more evidence.")
        elif verdict == "blocked":
            options = ("Resolve the listed blockers and run the experiment.", "Keep it blocked and set a review date.", "Kill the experiment with an operator reason.")
        else:
            options = ("Keep pending and collect the missing evidence.", "Review and lock the baseline thresholds.", "Kill the experiment with an operator reason.")
        items.append({
            "source": "Growth experiment",
            "title": experiment.get("id") or "Unnamed experiment",
            "detail": f"Advisory: {verdict}. {advisory.get('reason') or 'No reason recorded.'}",
            "options": options,
        })
    return items, []


def collect_needs(manager, summary):
    local, notes = file_needs()
    experiments, growth_notes = experiment_needs(summary)
    return manager_needs(manager) + local + experiments, notes + growth_notes


def render_needs(items, notes, manager_error):
    groups = []
    for item in items:
        options = "".join(f"<li>{esc(option)}</li>" for option in item["options"])
        groups.append(
            '<article class="need">'
            f'<div class="card-head">{badge(item["source"], "warn")}</div><h2>{esc(item["title"])}</h2>'
            f'<p>{esc(item["detail"])}</p><h3>Options</h3><ul>{options}</ul></article>'
        )
    notices = ([manager_error] if manager_error else []) + notes
    notice_html = "".join(empty(note) for note in notices if note)
    content = "".join(groups) or empty("Nothing currently awaits an operator decision in the readable sources.")
    return f'<section class="section-head"><div><h1>Needs You {badge(len(items), "warn")}</h1><p>Approvals and decisions only the operator can make.</p></div></section>{notice_html}<div class="cards">{content}</div>'


def build_page(view="departments", refresh=30):
    valid_views = {name for name, _ in VIEWS}
    view = view if view in valid_views else "departments"
    manager, manager_error = load_manager()
    growth = load_growth()
    needs, needs_notes = collect_needs(manager, growth)
    nav = "".join(
        f'<a class="{"selected" if name == view else ""}" href="/?view={name}">{esc(label)}'
        f'{f" <span>{len(needs)}</span>" if name == "needs" else ""}</a>'
        for name, label in VIEWS
    )
    if view == "platforms":
        content = render_platforms()
    elif view == "ads":
        content = render_ads(growth)
    elif view == "kanban":
        content = render_kanban(manager, manager_error)
    elif view == "needs":
        content = render_needs(needs, needs_notes, manager_error)
    else:
        content = render_departments()
    meta = f'<meta http-equiv="refresh" content="{refresh}">' if refresh else ""
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{meta}
<title>Operator HQ · {esc(dict(VIEWS)[view])}</title><style>
:root{{--bg:#071018;--panel:#101c27;--panel2:#142433;--line:#263c4e;--text:#ecf5fb;--muted:#91a7b8;--accent:#57d3a0;--warn:#ffbe55;--danger:#ff6f6f}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at 90% 0,#153047 0,transparent 34%),var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}}
header,main{{max-width:1600px;margin:auto;padding:20px}} header{{display:flex;align-items:center;gap:24px;justify-content:space-between;flex-wrap:wrap;border-bottom:1px solid var(--line)}}
.brand h1,.section-head h1{{margin:0}} .brand p,.section-head p{{margin:.2rem 0;color:var(--muted)}} nav{{display:flex;gap:8px;flex-wrap:wrap}}
nav a{{color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:8px 12px;text-decoration:none}} nav a span{{background:var(--warn);color:#171006;border-radius:999px;padding:1px 6px}}
nav a.selected{{color:#071018;background:var(--accent);border-color:var(--accent)}} a{{color:#79cfff;text-decoration:none}} a:hover{{text-decoration:underline}}
.section-head,.card-head,.column-head{{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}} .section-head{{margin:8px 0 18px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}} .card,.need,.column,.stage{{background:linear-gradient(145deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:14px;padding:16px}}
.card h2,.need h2,.stage h2,.column h2{{margin:.2rem 0}} .card p,.need p{{margin:.45rem 0}} .badge{{display:inline-block;border-radius:999px;padding:3px 8px;font-size:11px;font-weight:800;letter-spacing:.04em}}
.badge.ok{{background:#153e31;color:#7ce3b7}} .badge.warn{{background:#4a3614;color:#ffd17c}} .badge.muted{{background:#233544;color:#b6c8d5}} .muted{{color:var(--muted)}}
.tags span{{display:inline-block;background:#1d3040;color:#bed2df;border-radius:999px;padding:3px 7px;margin:0 5px 5px 0;font-size:12px}} .empty{{background:#101c27;border:1px dashed #385064;border-radius:12px;color:var(--muted);padding:14px;margin:10px 0}}
.platform-grid{{grid-template-columns:repeat(2,minmax(320px,1fr))}} .metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:14px 0}} .metric{{background:#0b1620;border-radius:10px;padding:10px}} .metric strong,.metric small{{display:block}} .metric strong{{font-size:23px}} .metric small{{color:var(--muted)}}
.desk,.receipt{{border-top:1px solid var(--line);margin-top:12px;padding-top:10px}} .paid-disabled{{background:var(--danger);color:#210606;border-radius:9px;padding:10px 14px;font-weight:900;letter-spacing:.08em}}
.pipeline{{display:grid;grid-template-columns:repeat(8,minmax(150px,1fr));gap:24px;overflow:auto;padding:8px 0 18px}} .stage{{min-height:180px;position:relative}} .stage:not(:last-child)::after{{content:'→';position:absolute;right:-20px;top:70px;color:var(--accent);font-size:24px}} .stage>strong{{font-size:38px;color:var(--accent)}} .stage p,.stage small{{color:var(--muted)}}
.board{{display:grid;grid-template-columns:repeat(6,minmax(240px,1fr));gap:12px;overflow:auto}} .column{{min-height:420px;padding:12px}} .work-card{{background:#0b1620;border:1px solid var(--line);border-radius:10px;padding:11px;margin:10px 0}} .work-card h3{{margin:.25rem 0}} .blocked{{color:var(--danger)}}
.need ul{{padding-left:20px}} .need li{{margin:.45rem 0}} code{{background:#0b1620;padding:2px 5px;border-radius:5px}}
@media(max-width:800px){{.platform-grid{{grid-template-columns:1fr}} .board{{grid-template-columns:repeat(6,280px)}} header{{align-items:flex-start}}}} @media(max-width:520px){{.metrics{{grid-template-columns:1fr}}}}
</style></head><body><header><div class="brand"><h1>Operator HQ</h1><p>Read-only · refreshes every 30 seconds · {esc(datetime.now().astimezone().isoformat(timespec="seconds"))}</p></div><nav>{nav}</nav></header><main>{content}</main></body></html>'''


class ReadOnlyHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/":
            payload, status, content_type = b"not found", 404, "text/plain; charset=utf-8"
        else:
            view = parse_qs(parsed.query).get("view", ["departments"])[0]
            payload, status, content_type = build_page(view).encode("utf-8"), 200, "text/html; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self' file:; style-src 'unsafe-inline'")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def reject_write(self):
        self.send_response(405)
        self.send_header("Allow", "GET")
        self.send_header("Content-Length", "0")
        self.end_headers()

    do_POST = do_PUT = do_PATCH = do_DELETE = reject_write

    def log_message(self, *args):
        return


def serve(no_open=False):
    server = ThreadingHTTPServer((HOST, PORT), ReadOnlyHandler)
    if not no_open:
        webbrowser.open(f"http://{HOST}:{PORT}")
    print(f"Operator HQ at http://{HOST}:{PORT} — Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def self_check():
    sample = {
        "id": "check.verify",
        "title": "Verify item appears",
        "lifecycle": "verify",
        "blocked": False,
        "data": {},
    }
    parsed = parse_frontmatter("---\nstatus: active\ntags: [one, two]\n---\n# Test")
    assert parsed == {"status": "active", "tags": ["one", "two"]}
    assert manager_needs({"nodes": [sample]})[0]["title"] == "Verify item appears"
    assert "Verify item appears" in render_kanban({"revision": 1, "generated_at": "now", "kanban": {"verify": [sample]}}, None)
    print("hq: PASS — frontmatter, verify Needs You, and Kanban rendering")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true", help=f"serve read-only on http://{HOST}:{PORT}")
    parser.add_argument("--no-open", action="store_true", help="do not open a browser")
    parser.add_argument("--check", action="store_true", help="run the in-file rendering check")
    args = parser.parse_args(argv)
    if args.check:
        self_check()
        return
    if args.serve:
        serve(args.no_open)
        return
    OUT.write_text(build_page(refresh=30), encoding="utf-8")
    print(f"wrote {OUT}")
    if not args.no_open:
        os.startfile(OUT)  # noqa: S606


if __name__ == "__main__":
    main()
