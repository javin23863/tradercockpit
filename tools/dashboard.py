#!/usr/bin/env python3
"""OpenMontage pipeline dashboard — probes live state, writes dashboard.html, opens it.

Static file regenerated on every run (double-click dashboard.bat). No server.
--serve runs a localhost-only http.server that rebuilds the page on every GET,
with a 30s meta-refresh — live view while renders run (dashboard-live.bat).
Shows: publish-leg readiness, GPU, engine pins, recent renders, git state, quick links.
Never prints or embeds secret values — only presence booleans from publish.py --dry-run.

Run: python dashboard.py [--no-open | --serve]
"""
import html
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    from .growth_experiments import load_growth_summary
except ImportError:  # direct script execution
    from growth_experiments import load_growth_summary

HUB = Path(__file__).resolve().parent.parent
ENGINE = HUB / "OpenMontage"
PY = ENGINE / ".venv" / "Scripts" / "python.exe"
OUT = HUB / "dashboard.html"
SOCIAL = HUB / "social-ops" / "analytics-latest.json"
TARGETS = HUB / "social-ops" / "engagement-targets.json"

SAFE_ENV_KEYS = ["VIDEO_GEN_LOCAL_ENABLED", "VIDEO_GEN_LOCAL_MODEL", "B2_BUCKET", "B2_S3_ENDPOINT"]


def run(cmd, cwd=None, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return f"(unavailable: {e})"


def leg_status():
    # ponytail: --dry-run only checks the video arg exists, so pass this script as the file
    out = run([str(PY), str(HUB / "tools" / "publish.py"), __file__, "--title", "x", "--dry-run"])
    legs = {}
    for line in out.splitlines():
        k, _, v = line.partition(":")
        if k.strip() in ("youtube", "instagram", "facebook"):
            legs[k.strip()] = "ready" in v
    return legs


def gpu_status():
    out = run(["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu",
               "--format=csv,noheader"], timeout=15).strip()
    return out or "(no GPU info)"


def env_pins():
    pins = {}
    env = ENGINE / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8", errors="ignore").splitlines():
            k, _, v = line.partition("=")
            if k.strip() in SAFE_ENV_KEYS and v.strip():
                pins[k.strip()] = v.strip()
    return pins


def git_state():
    head = run(["git", "-C", str(HUB), "log", "-1", "--format=%h %ad %s", "--date=short"]).strip()
    dirty = run(["git", "-C", str(HUB), "status", "--porcelain"]).strip()
    remote = run(["git", "-C", str(HUB), "remote", "get-url", "origin"]).strip()
    return head, ("dirty" if dirty else "clean"), remote


def renders():
    files = []
    proj = ENGINE / "projects"
    if proj.exists():
        for f in proj.rglob("*"):
            if f.suffix.lower() in (".mp4", ".wav") and f.is_file():
                files.append(f)
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return files[:20]


def wan_running():
    # ponytail: any extra python process = "generating"; swap for a pidfile if false positives annoy
    out = run(["powershell", "-NoProfile", "-Command",
               "(Get-Process python -ErrorAction SilentlyContinue | Measure-Object).Count"]).strip()
    try:
        return int(out.splitlines()[-1]) > 1  # >1 = something besides this dashboard's parent
    except ValueError:
        return False


def badge(ok, yes="READY", no="MISSING"):
    cls, txt = ("ok", yes) if ok else ("bad", no)
    return f'<span class="badge {cls}">{txt}</span>'


def fmt_number(value):
    if not isinstance(value, (int, float)):
        return "—"
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def load_social():
    try:
        return json.loads(SOCIAL.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def render_social(snapshot):
    if not snapshot:
        return '<section><h2>Weekly social performance</h2><div class="empty">No snapshot yet. Run <code>OpenMontage\\.venv\\Scripts\\python.exe tools\\social_analytics.py collect</code>.</div></section>'
    sources = snapshot.get("sources", {})
    rollup = snapshot.get("rollup", {})
    youtube = sources.get("youtube", {})
    kpis = [
        ("YouTube", rollup.get("youtubeWeeklyViews"), "7-day views" if youtube.get("status") == "ready" else "new-video observed views", youtube.get("account")),
        ("Facebook", rollup.get("facebookObservedViews"), "observed reel plays", sources.get("facebook", {}).get("account")),
        ("Instagram", rollup.get("instagramObservedViews"), "observed reel views", sources.get("instagram", {}).get("account")),
        ("TikTok", rollup.get("tiktokObservedViews"), "Studio post views", sources.get("tiktok", {}).get("account")),
    ]
    cards = "".join(
        f'<article class="kpi"><div class="kpi-platform">{html.escape(platform)}</div><div class="kpi-value">{fmt_number(value)}</div>'
        f'<div class="kpi-label">{html.escape(label)}</div><div class="muted">{html.escape(account or "not connected")}</div></article>'
        for platform, value, label, account in kpis
    )
    weekly = youtube.get("weekly") or {}
    youtube_quality = ""
    if youtube.get("status") == "ready" and weekly:
        engagement = sum(weekly.get(key) or 0 for key in ("likes", "comments", "shares"))
        net_subscribers = (weekly.get("subscribersGained") or 0) - (weekly.get("subscribersLost") or 0)
        average_percentage = weekly.get("averageViewPercentage")
        percentage_text = f"{average_percentage:.2f}%" if isinstance(average_percentage, (int, float)) else "—"
        youtube_quality = f'''<h3>YouTube audience quality</h3>
<div class="kpis youtube-quality">
<article class="kpi"><div class="kpi-value">{fmt_number(weekly.get("estimatedMinutesWatched"))}</div><div class="kpi-label">estimated watch minutes</div></article>
<article class="kpi"><div class="kpi-value">{fmt_number(weekly.get("averageViewDuration"))}s</div><div class="kpi-label">average view duration</div></article>
<article class="kpi"><div class="kpi-value">{percentage_text}</div><div class="kpi-label">average percentage viewed</div></article>
<article class="kpi"><div class="kpi-value">{fmt_number(engagement)}</div><div class="kpi-label">likes + comments + shares</div><div class="muted">{net_subscribers:+g} net subscribers</div></article>
</div>'''
    status_rows = "".join(
        f'<tr><td>{html.escape(name.title())}</td><td><span class="badge {"ok" if source.get("status") == "ready" else "warn"}">{html.escape(str(source.get("status", "unknown")).upper())}</span></td>'
        f'<td>{html.escape(source.get("measurement") or source.get("error") or source.get("analyticsError") or "live source connected")}</td></tr>'
        for name, source in sources.items()
    )
    posts = []
    for platform, source in sources.items():
        ranked = sorted(source.get("posts", []), key=lambda post: post.get("views") or 0, reverse=True)[:3]
        for post in ranked:
            engagement = sum(post.get(key) or 0 for key in ("likes", "comments", "shares", "saves"))
            posts.append((platform, post, engagement))
    post_rows = "".join(
        f'<tr><td>{html.escape(platform.title())}</td><td><a href="{html.escape(post.get("url") or "#")}">{html.escape((post.get("title") or post.get("id") or "Untitled")[:94])}</a></td>'
        f'<td>{fmt_number(post.get("views"))}</td><td>{fmt_number(engagement)}</td><td>{html.escape(post.get("privacy") or post.get("type") or "tracked")}</td></tr>'
        for platform, post, engagement in sorted(posts, key=lambda item: item[1].get("views") or 0, reverse=True)
    ) or '<tr><td colspan="5">No post-level data returned.</td></tr>'
    decisions = "".join(
        f'<article class="decision"><span class="badge warn">{html.escape(item.get("priority", "next").upper())}</span>'
        f'<h3>{html.escape(item.get("title", ""))}</h3><p>{html.escape(item.get("evidence", ""))}</p><p class="action">{html.escape(item.get("action", ""))}</p></article>'
        for item in snapshot.get("decisions", [])
    )
    daily = youtube.get("daily", [])
    max_views = max((row.get("views") or 0 for row in daily), default=0)
    bars = "".join(
        f'<div class="bar-row"><span>{html.escape(str(row.get("day", ""))[5:])}</span><div class="bar" style="width:{((row.get("views") or 0) / max_views * 100) if max_views else 0:.1f}%"></div><strong>{fmt_number(row.get("views"))}</strong></div>'
        for row in daily
    ) or '<div class="empty">YouTube daily retention and watch-time trend will appear after the Analytics API is enabled.</div>'
    caveats = "".join(f"<li>{html.escape(note)}</li>" for note in snapshot.get("caveats", []))
    window = snapshot.get("window", {})
    return f'''
<section class="social">
<div class="section-head"><div><h2>Weekly social performance</h2><p class="muted">Window {html.escape(window.get("start", "?"))} to {html.escape(window.get("end", "?"))} · refreshed {html.escape(snapshot.get("generatedAt", "unknown"))}</p></div><span class="badge ok">{rollup.get("connectedSources", 0)}/4 CONNECTED</span></div>
<div class="kpis">{cards}</div>
{youtube_quality}
<div class="split"><div><h3>YouTube daily views</h3><div class="bars">{bars}</div></div><div><h3>Source health</h3><table><tr><th>source</th><th>status</th><th>measurement</th></tr>{status_rows}</table></div></div>
<h3>Top observed posts</h3><table><tr><th>platform</th><th>content</th><th>views</th><th>engagement</th><th>state</th></tr>{post_rows}</table>
<h3>Next weekly decisions</h3><div class="decisions">{decisions}</div>
<details><summary>Measurement caveats</summary><ul>{caveats}</ul></details>
</section>'''


def render_engagement():
    """Stage 5 worklist. Read-only lister — the operator writes every comment by hand."""
    try:
        payload = json.loads(TARGETS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ('<section><h2>Engagement targets</h2><div class="empty">No scan yet. Run '
                '<code>OpenMontage\\.venv\\Scripts\\python.exe tools\\engagement.py scan</code>.</div></section>')
    rows = "".join(
        f'<tr><td>{html.escape(str(target.get("platform", "")))}<br><span class="muted">{html.escape(str(target.get("account") or ""))}</span></td>'
        f'<td><a href="{html.escape(str(target.get("url") or "#"))}" target="_blank">{html.escape(str(target.get("title") or "Untitled")[:110])}</a></td>'
        f'<td>{target.get("ageHours")}h</td>'
        f'<td>{fmt_number(target.get("views"))} / {fmt_number(target.get("likes"))} / {fmt_number(target.get("comments"))}</td>'
        f'<td>{target.get("engagementPerHour")}</td>'
        f'<td><strong>{target.get("score")}</strong><br><span class="muted">{html.escape(str(target.get("why") or ""))}</span></td></tr>'
        for target in payload.get("targets", [])
    ) or '<tr><td colspan="6">No live targets ranked in the last scan.</td></tr>'
    errors = "".join(f"<li>{html.escape(str(item))}</li>" for item in payload.get("errors", []))
    return f'''<section class="engagement">
<div class="section-head"><div><h2>Engagement targets</h2><p class="muted">Scanned {html.escape(str(payload.get("generatedAt", "unknown")))} · {payload.get("postsSeen", 0)} posts seen across {payload.get("accountsConfigured", 0)} accounts</p></div><span class="badge ok">READ-ONLY</span></div>
<div class="empty">Stage 5 is deliberately human: <strong>no AI-generated comments, no cold-pitch DMs — ever.</strong> This list ranks where to spend the daily block; you write every reply yourself.</div>
<table><tr><th>where</th><th>post</th><th>age</th><th>views / likes / comments</th><th>eng/hr</th><th>score</th></tr>{rows}</table>
<p class="muted">Rank = {html.escape(str(payload.get("ranking", "")))}</p>
{f"<details><summary>Scan errors</summary><ul>{errors}</ul></details>" if errors else ""}
</section>'''


def load_growth():
    try:
        return load_growth_summary()
    except ValueError as error:
        return {"valid": False, "error": str(error)}


def render_growth(summary):
    if not summary.get("valid"):
        error = html.escape(str(summary.get("error", "Growth manifest is unavailable.")))
        return f'''<section class="growth">
<div class="section-head"><div><h2>Growth experiments</h2><p class="muted">File-backed experiment and learning contract</p></div><span class="badge bad">BLOCKED</span></div>
<div class="empty"><strong>Growth contract invalid:</strong> {error}<br><code>py tools\\growth_experiments.py validate</code></div>
</section>'''

    library_rows = "".join(
        f'<tr><td>{html.escape(category)}</td><td>{counts.get("active", 0)}</td>'
        f'<td>{counts.get("hypothesis", 0)}</td><td>{counts.get("blocked", 0)}</td></tr>'
        for category, counts in summary.get("libraryCounts", {}).items()
    )
    experiment_rows = []
    for experiment in summary.get("experiments", []):
        assembly = " / ".join(str(value) for value in experiment.get("assembly", {}).values())
        median = experiment.get("primaryMedian")
        metric_value = "—" if median is None else f"{median:.2f}"
        advisory = experiment.get("advisory", {})
        advisory_verdict = str(advisory.get("verdict", "insufficient_evidence"))
        verdict_class = "ok" if advisory_verdict == "reuse" else "bad" if advisory_verdict == "kill" else "warn"
        decision = experiment.get("decision", {})
        blockers = experiment.get("blockers", [])
        experiment_rows.append(
            f'<tr><td><strong>{html.escape(str(experiment.get("id", "")))}</strong><br>'
            f'<span class="muted">{html.escape(str(experiment.get("surface", "")))} · {html.escape(str(experiment.get("state", "")))}</span></td>'
            f'<td>{html.escape(str(experiment.get("hypothesis", "")))}<br><span class="muted">{html.escape(assembly)}</span></td>'
            f'<td>{experiment.get("observationCount", 0)}<br><span class="muted">{html.escape(str(experiment.get("primaryMetric", "")))}: {metric_value}</span></td>'
            f'<td><span class="badge {verdict_class}">{html.escape(advisory_verdict.upper())}</span><br><span class="muted">{html.escape(str(advisory.get("reason", "")))}</span></td>'
            f'<td>{html.escape(str(decision.get("verdict", "pending")))}<br><span class="muted">{html.escape("; ".join(str(item) for item in blockers) or "no blockers")}</span></td></tr>'
        )
    experiment_table = "".join(experiment_rows) or '<tr><td colspan="5">No experiments declared.</td></tr>'
    return f'''<section class="growth">
<div class="section-head"><div><h2>Growth experiments</h2><p class="muted">Updated {html.escape(str(summary.get("updatedAt", "unknown")))} · advisory only</p></div><div><span class="badge ok">VALID</span> <span class="badge ok">PAID DISABLED</span></div></div>
<h3>Component library</h3><table><tr><th>library</th><th>active</th><th>hypothesis</th><th>blocked</th></tr>{library_rows}</table>
<h3>Experiment ledger</h3><table><tr><th>experiment</th><th>hypothesis / assembly</th><th>evidence</th><th>advisory</th><th>operator / blockers</th></tr>{experiment_table}</table>
</section>'''


def build_page(refresh=0):
    legs = leg_status()
    pins = env_pins()
    head, tree, remote = git_state()
    gpu = gpu_status()
    vids = renders()
    wan_out = ENGINE / "projects" / "wan_smoke.mp4"
    wan = badge(True, "DONE") if wan_out.exists() else (
        '<span class="badge warn">GENERATING</span>' if wan_running() else badge(False, "NOT RUN"))
    social_snapshot = load_social()
    social = render_social(social_snapshot)
    growth = render_growth(load_growth())
    tiktok_api = (social_snapshot or {}).get("sources", {}).get("tiktok", {}).get("status") == "ready"

    leg_rows = "".join(
        f"<tr><td>{p}</td><td>{badge(legs.get(p, False))}</td><td>{note}</td></tr>"
        for p, note in [
            ("youtube", "OAuth token cached — publish.py --platforms youtube"),
            ("instagram", "Meta business account + Page token connected"),
            ("facebook", "Meta Page token connected"),
        ]) + f'<tr><td>tiktok</td><td>{badge(tiktok_api, "API", "SETUP")}' \
             '</td><td>official Content Posting API; refreshable OAuth + exact approved item + ID/URL read-back</td></tr>'

    vid_rows = "".join(
        f'<tr><td><a href="file:///{html.escape(str(f).replace(chr(92), "/"))}">{html.escape(f.name)}</a></td>'
        f"<td>{f.stat().st_size / 1e6:.1f} MB</td>"
        f"<td>{datetime.fromtimestamp(f.stat().st_mtime):%Y-%m-%d %H:%M}</td>"
        f"<td>{html.escape(str(f.parent.relative_to(ENGINE)))}</td></tr>"
        for f in vids) or "<tr><td colspan=4>no renders yet</td></tr>"

    pin_rows = "".join(f"<tr><td>{k}</td><td><code>{html.escape(v)}</code></td></tr>" for k, v in pins.items())

    meta_refresh = f'<meta http-equiv="refresh" content="{refresh}">' if refresh else ""
    page = f"""<!doctype html><html><head><meta charset="utf-8">{meta_refresh}
<title>TraderCockpit Operations</title>
<style>
 body{{background:#0d1015;color:#d8dce2;font:14px/1.5 'Segoe UI',sans-serif;max-width:1180px;margin:2rem auto;padding:0 1rem}}
 h1{{font-size:1.6rem}} h2{{font-size:1.05rem;color:#8ab4f8;margin-top:2rem;border-bottom:1px solid #2a2e35;padding-bottom:.45rem}} h3{{font-size:.9rem;color:#aeb7c4;margin:1.2rem 0 .5rem}}
 table{{border-collapse:collapse;width:100%}} td,th{{padding:.35rem .6rem;border-bottom:1px solid #23262c;text-align:left}}
 a{{color:#8ab4f8;text-decoration:none}} a:hover{{text-decoration:underline}}
 code,pre{{background:#1e2127;padding:.1rem .35rem;border-radius:4px}}
 .badge{{padding:.1rem .5rem;border-radius:10px;font-size:.75rem;font-weight:600}}
 .ok{{background:#1e3a29;color:#6fd18b}} .bad{{background:#3a1e1e;color:#e07a7a}} .warn{{background:#3a331e;color:#e0c26f}}
 .muted{{color:#7a8089;font-size:.85rem}}
 section{{margin:1.25rem 0 2.25rem}} .section-head{{display:flex;align-items:end;justify-content:space-between;gap:1rem}}
 .section-head h2{{margin-bottom:.15rem}} .section-head p{{margin:0}}
 .kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem;margin:1rem 0}}
 .kpi{{background:#151a22;border:1px solid #252c37;border-radius:10px;padding:.85rem 1rem}}
 .kpi-platform{{color:#8ab4f8;font-weight:600}} .kpi-value{{font-size:1.8rem;font-weight:700;margin:.25rem 0}} .kpi-label{{font-size:.82rem}}
 .split{{display:grid;grid-template-columns:1fr 1.35fr;gap:1.2rem}}
 .bar-row{{display:grid;grid-template-columns:44px 1fr 45px;gap:.5rem;align-items:center;margin:.4rem 0}} .bar{{height:12px;background:linear-gradient(90deg,#ff9f1c,#ffcc70);min-width:2px;border-radius:2px}}
 .decisions{{display:grid;grid-template-columns:repeat(2,1fr);gap:.7rem}} .decision{{background:#151a22;border-left:3px solid #ff9f1c;padding:.8rem 1rem}} .decision h3{{margin:.55rem 0 .2rem;color:#e5e9ef}} .decision p{{margin:.2rem 0}} .decision .action{{color:#ffcc70}}
 .empty{{padding:1rem;background:#151a22;color:#8e97a4;border-radius:6px}} details{{margin-top:1rem;color:#8e97a4}}
 @media(max-width:800px){{.kpis,.split,.decisions{{grid-template-columns:1fr 1fr}}}} @media(max-width:540px){{.kpis,.split,.decisions{{grid-template-columns:1fr}}}}
</style></head><body>
<h1>TraderCockpit Operations &mdash; <span class="muted">generated {datetime.now():%Y-%m-%d %H:%M}</span></h1>

{social}

{render_engagement()}

{growth}

<h2>Publish legs</h2>
<table><tr><th>platform</th><th>status</th><th>notes</th></tr>{leg_rows}</table>

<h2>Local GPU generation</h2>
<table>
<tr><td>GPU</td><td colspan=2><code>{html.escape(gpu)}</code></td></tr>
<tr><td>WAN 2.1 1.3B smoke</td><td>{wan}</td><td class="muted">{html.escape(str(wan_out))}</td></tr>
{pin_rows}
</table>

<h2>Recent renders</h2>
<table><tr><th>file</th><th>size</th><th>modified</th><th>where</th></tr>{vid_rows}</table>

<h2>Repo</h2>
<table>
<tr><td>HEAD</td><td><code>{html.escape(head)}</code> ({tree})</td></tr>
<tr><td>remote</td><td><a href="{html.escape(remote)}">{html.escape(remote)}</a></td></tr>
</table>

<h2>Commands</h2>
<table>
<tr><td>publish</td><td><code>python tools\\publish.py video.mp4 --title "..." --caption "..." --platforms youtube</code></td></tr>
<tr><td>dry-run creds check</td><td><code>python tools\\publish.py x --title x --dry-run</code></td></tr>
<tr><td>Meta creds fill</td><td><code>python tools\\meta_setup.py --app-id .. --app-secret .. --user-token ..</code></td></tr>
<tr><td>validate growth experiments</td><td><code>py tools\\growth_experiments.py validate</code></td></tr>
<tr><td>report growth experiments</td><td><code>py tools\\growth_experiments.py report --json</code></td></tr>
<tr><td>production dashboard</td><td><code>cd OpenMontage &amp;&amp; python -m backlot open</code> (per-video board)</td></tr>
<tr><td>refresh this page</td><td>re-run <code>dashboard.bat</code>, or <code>dashboard-live.bat</code> for auto-refresh every 30s</td></tr>
</table>

<h2>Docs</h2>
<p>
<a href="file:///{HUB.as_posix()}/ops/SETUP-CREDS.md">ops/SETUP-CREDS.md</a> &middot;
<a href="file:///{HUB.as_posix()}/ops/COMPLEMENTS.md">ops/COMPLEMENTS.md</a> &middot;
<a href="file:///{HUB.as_posix()}/openmontage/SKILL.md">SKILL.md</a> &middot;
<a href="file:///{HUB.as_posix()}/archive/RUNTIMES">archive/RUNTIMES/</a> &middot;
<a href="file:///{ENGINE.as_posix()}/AGENT_GUIDE.md">AGENT_GUIDE.md</a>
</p>
</body></html>"""

    return page


def serve(port=8788):
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = build_page(refresh=30).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    # localhost only — never expose creds-adjacent status on the LAN
    srv = HTTPServer(("127.0.0.1", port), Handler)
    if "--no-open" not in sys.argv:
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{port}")
    print(f"live dashboard at http://127.0.0.1:{port} — Ctrl+C to stop")
    srv.serve_forever()


def main():
    if "--serve" in sys.argv:
        serve()
        return
    OUT.write_text(build_page(), encoding="utf-8")
    print(f"wrote {OUT}")
    if "--no-open" not in sys.argv:
        os.startfile(OUT)  # noqa


if __name__ == "__main__":
    main()
