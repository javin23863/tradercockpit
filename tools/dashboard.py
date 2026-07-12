#!/usr/bin/env python3
"""OpenMontage pipeline dashboard — probes live state, writes dashboard.html, opens it.

Static file regenerated on every run (double-click dashboard.bat). No server.
Shows: publish-leg readiness, GPU, engine pins, recent renders, git state, quick links.
Never prints or embeds secret values — only presence booleans from publish.py --dry-run.

Run: python dashboard.py [--no-open]
"""
import html
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HUB = Path(__file__).resolve().parent.parent
ENGINE = HUB / "OpenMontage"
PY = ENGINE / ".venv" / "Scripts" / "python.exe"
OUT = HUB / "dashboard.html"

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


def main():
    legs = leg_status()
    pins = env_pins()
    head, tree, remote = git_state()
    gpu = gpu_status()
    vids = renders()
    wan_out = ENGINE / "projects" / "wan_smoke.mp4"
    wan = badge(True, "DONE") if wan_out.exists() else (
        '<span class="badge warn">GENERATING</span>' if wan_running() else badge(False, "NOT RUN"))

    leg_rows = "".join(
        f"<tr><td>{p}</td><td>{badge(legs.get(p, False))}</td><td>{note}</td></tr>"
        for p, note in [
            ("youtube", "OAuth token cached — publish.py --platforms youtube"),
            ("instagram", "needs META_IG_USER_ID + META_PAGE_TOKEN (run meta_setup.py)"),
            ("facebook", "needs META_PAGE_ID + META_PAGE_TOKEN (run meta_setup.py)"),
        ]) + '<tr><td>tiktok</td><td><span class="badge warn">MANUAL</span>' \
             '</td><td>no free self-owned API — Upload-Post / Postiz, see COMPLEMENTS.md</td></tr>'

    vid_rows = "".join(
        f'<tr><td><a href="file:///{html.escape(str(f).replace(chr(92), "/"))}">{html.escape(f.name)}</a></td>'
        f"<td>{f.stat().st_size / 1e6:.1f} MB</td>"
        f"<td>{datetime.fromtimestamp(f.stat().st_mtime):%Y-%m-%d %H:%M}</td>"
        f"<td>{html.escape(str(f.parent.relative_to(ENGINE)))}</td></tr>"
        for f in vids) or "<tr><td colspan=4>no renders yet</td></tr>"

    pin_rows = "".join(f"<tr><td>{k}</td><td><code>{html.escape(v)}</code></td></tr>" for k, v in pins.items())

    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>OpenMontage Pipeline</title>
<style>
 body{{background:#14161a;color:#d8dce2;font:14px/1.5 'Segoe UI',sans-serif;max-width:960px;margin:2rem auto;padding:0 1rem}}
 h1{{font-size:1.4rem}} h2{{font-size:1rem;color:#8ab4f8;margin-top:2rem;border-bottom:1px solid #2a2e35;padding-bottom:.3rem}}
 table{{border-collapse:collapse;width:100%}} td,th{{padding:.35rem .6rem;border-bottom:1px solid #23262c;text-align:left}}
 a{{color:#8ab4f8;text-decoration:none}} a:hover{{text-decoration:underline}}
 code,pre{{background:#1e2127;padding:.1rem .35rem;border-radius:4px}}
 .badge{{padding:.1rem .5rem;border-radius:10px;font-size:.75rem;font-weight:600}}
 .ok{{background:#1e3a29;color:#6fd18b}} .bad{{background:#3a1e1e;color:#e07a7a}} .warn{{background:#3a331e;color:#e0c26f}}
 .muted{{color:#7a8089;font-size:.85rem}}
</style></head><body>
<h1>OpenMontage Pipeline &mdash; <span class="muted">generated {datetime.now():%Y-%m-%d %H:%M}</span></h1>

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
<tr><td>production dashboard</td><td><code>cd OpenMontage &amp;&amp; python -m backlot open</code> (per-video board)</td></tr>
<tr><td>refresh this page</td><td>re-run <code>dashboard.bat</code></td></tr>
</table>

<h2>Docs</h2>
<p>
<a href="file:///{HUB.as_posix()}/SETUP-CREDS.md">SETUP-CREDS.md</a> &middot;
<a href="file:///{HUB.as_posix()}/COMPLEMENTS.md">COMPLEMENTS.md</a> &middot;
<a href="file:///{HUB.as_posix()}/openmontage/SKILL.md">SKILL.md</a> &middot;
<a href="file:///{HUB.as_posix()}/RUNTIMES">RUNTIMES/</a> &middot;
<a href="file:///{ENGINE.as_posix()}/AGENT_GUIDE.md">AGENT_GUIDE.md</a>
</p>
</body></html>"""

    OUT.write_text(page, encoding="utf-8")
    print(f"wrote {OUT}")
    if "--no-open" not in sys.argv:
        os.startfile(OUT)  # noqa


if __name__ == "__main__":
    main()
