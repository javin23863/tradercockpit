#!/usr/bin/env python3
"""Apollo HQ OS — Jarvis-parity operator shell over the verified hq.py views.

Run: python tools/hq_os.py [--no-open]   (serves http://127.0.0.1:8786)

- GET  /                 HUD (vitals rail · Apollo + directives + artifact trail · skills rail)
- GET  /?view=<name>     hq.py dashboard views; view=needs is overridden by Needs You v2 below
- GET  /jobs             runner job states (JSON)
- POST /run/<action>     HARD-allowlisted local actions only (no publish/credential/approval)
- POST /llm              {"prompt": ..., "backend": ...} — talk to ANY configured LLM backend
- POST /decide           Needs You v2: operator clicks YES/NO/HOLD → appended receipt in
                         social-ops/operator-decisions.jsonl + Telegram confirmation. Only items
                         that pass the operator triage predicate get buttons; everything else
                         lands in the delegated PM↔Sol queue with no click surface.

LLM backends live in tools/hq-llm.json (cli argv / ollama / openai-compatible with the API key
named in operator custody, never inline). Localhost only. Voice loop is Phase 2.
"""
import hashlib
import json
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).parent))
import hq  # verified dashboard core (views, loaders) — reused, not modified

ROOT = hq.ROOT
VAULT = Path(r"C:\Users\MSI\Desktop\TraderCockpit-Vault")
REPORTS = VAULT / "wiki" / "reports"
LLM_CONFIG = ROOT / "tools" / "hq-llm.json"
HOST, PORT = "127.0.0.1", 8786
ICT = timezone(timedelta(hours=7))
PY = sys.executable
OM_PY = str(ROOT / "OpenMontage" / ".venv" / "Scripts" / "python.exe")
DECISIONS = ROOT / "social-ops" / "operator-decisions.jsonl"
PINGED = ROOT / "social-ops" / "needs-you-pinged.json"

# ---- skills runner (hard allowlist; nothing here publishes, approves, or touches credentials)
ACTIONS = {
    "morning-rundown": {"label": "Morning rundown", "argv": [PY, "tools/morning_rundown.py"]},
    "thread-board": {"label": "Codex thread board", "argv": [PY, "tools/thread_board.py", "24"]},
    "growth-report": {"label": "Growth report", "argv": [PY, "tools/growth_experiments.py", "report", "--json"]},
    "analytics-collect": {"label": "Collect analytics", "argv": [OM_PY, "tools/social_analytics.py", "collect"]},
    "hotdog-screen": {"label": "Hot Dog competitor screen", "argv": [OM_PY, "tools/social_analytics.py", "hotdog"]},
    "social-weekly-report": {"label": "Weekly social report", "argv": [OM_PY, "tools/social_analytics.py", "report"]},
    "publish-dry-run": {"label": "Publish readiness", "argv": [OM_PY, "tools/publish.py", "--dry-run"], "ok_codes": (0, 1)},
    "hq-static-regen": {"label": "Regen static HQ", "argv": [PY, "tools/hq.py", "--no-open"]},
}
JOBS = {}
JOBS_LOCK = threading.Lock()


def run_job(job_id, action):
    spec = ACTIONS[action]
    with JOBS_LOCK:
        JOBS[job_id].update(status="running", started=time.time())
    try:
        proc = subprocess.run(spec["argv"], cwd=ROOT, capture_output=True, text=True, timeout=900)
        output = ((proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")).strip()
        ok = proc.returncode in spec.get("ok_codes", (0,))
        report = None
        if ok and output:
            REPORTS.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now(ICT).strftime("%Y-%m-%d-%H%M%S")
            if action == "morning-rundown" and Path(output.splitlines()[-1]).is_file():
                report = output.splitlines()[-1]
            else:
                path = REPORTS / f"{action}-{stamp}.md"
                path.write_text(f"# {spec['label']} — {stamp} ICT\n\n```\n{output[-12000:]}\n```\n", encoding="utf-8")
                report = str(path)
        with JOBS_LOCK:
            JOBS[job_id].update(status="done" if ok else "failed", finished=time.time(),
                                tail=output[-1200:], report=report, code=proc.returncode)
    except (OSError, subprocess.TimeoutExpired) as error:
        with JOBS_LOCK:
            JOBS[job_id].update(status="failed", finished=time.time(), tail=f"{type(error).__name__}: {error}"[-800:])


# ---- any-LLM console
DEFAULT_LLM = {
    "default": "claude",
    "backends": {
        "claude": {"type": "cli", "argv": ["claude", "-p"]},
        "codex": {"type": "cli", "argv": ["codex", "exec", "--skip-git-repo-check"]},
        "ollama": {"type": "ollama", "url": "http://127.0.0.1:11434", "model": "gemma3:12b"},
    },
}


def llm_config():
    if LLM_CONFIG.is_file():
        try:
            return json.loads(LLM_CONFIG.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            pass
    LLM_CONFIG.write_text(json.dumps(DEFAULT_LLM, indent=2), encoding="utf-8")
    return DEFAULT_LLM


def ask_llm(prompt, backend_name=None):
    config = llm_config()
    name = backend_name or config.get("default", "claude")
    backend = (config.get("backends") or {}).get(name)
    if not backend:
        return name, f"BLOCK: backend '{name}' is not configured in tools/hq-llm.json"
    kind = backend.get("type")
    try:
        if kind == "cli":
            import shutil
            argv = list(backend["argv"])
            argv[0] = shutil.which(argv[0]) or argv[0]  # npm shims need .cmd resolution on Windows
            proc = subprocess.run([*argv, prompt], cwd=ROOT, capture_output=True,
                                  text=True, timeout=300, shell=False)
            return name, (proc.stdout or proc.stderr or "(no output)").strip()[-8000:]
        if kind == "ollama":
            body = json.dumps({"model": backend.get("model"), "prompt": prompt, "stream": False}).encode()
            req = Request(backend.get("url", "http://127.0.0.1:11434") + "/api/generate",
                          data=body, headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=300) as response:  # noqa: S310 - operator-configured local/loopback
                return name, json.load(response).get("response", "(no response)")[-8000:]
        if kind == "openai":
            key = ""
            key_env = backend.get("key_env")
            if key_env:
                from credential_custody import credential_path
                env_file = credential_path(backend.get("key_file", "telegram.env"))
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith(key_env + "="):
                        key = line.split("=", 1)[1].strip()
            body = json.dumps({"model": backend.get("model"),
                               "messages": [{"role": "user", "content": prompt}]}).encode()
            req = Request(backend["base_url"].rstrip("/") + "/chat/completions", data=body,
                          headers={"Content-Type": "application/json",
                                   **({"Authorization": f"Bearer {key}"} if key else {})})
            with urlopen(req, timeout=300) as response:  # noqa: S310 - operator-configured endpoint
                data = json.load(response)
            return name, data["choices"][0]["message"]["content"][-8000:]
        return name, f"BLOCK: unknown backend type '{kind}'"
    except Exception as error:  # surfaced to the console, never crashes the shell
        return name, f"{type(error).__name__}: {error}"


# ---- Needs You v2: only truly-operator decisions get buttons; the rest is the delegated queue
def _telegram(text):
    try:
        import notify_telegram
        notify_telegram.send(text)
    except BaseException:  # attention ping is best-effort; never breaks a decision or a render
        pass


def _item_id(source, title, detail):
    return hashlib.sha1(f"{source}|{title}|{detail}".encode("utf-8")).hexdigest()[:12]


def load_decisions():
    decisions = {}
    if DECISIONS.is_file():
        for line in DECISIONS.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
                decisions[record["id"]] = record
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return decisions


def record_decision(item, verdict, note, telegram=True):
    record = {"schema": "operator-decision/v1", "id": item["id"], "source": item["source"],
              "title": item["title"], "detail": item["detail"], "verdict": verdict, "note": note,
              "at": datetime.now(ICT).isoformat(timespec="seconds")}
    DECISIONS.parent.mkdir(parents=True, exist_ok=True)
    with DECISIONS.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")
    if telegram:
        threading.Thread(target=_telegram, daemon=True, args=(
            f"Decision receipted: {verdict.upper()} — {item['source']}: {item['title']}"
            + (f"\nNote: {note}" if note else "") + "\nAgent applies it next.",)).start()
    return record


def collect_needs_v2(manager, growth):
    """Split everything awaiting a human into operator-clickable vs delegated PM<->Sol items."""
    operator, delegated = [], []
    for node in (manager or {}).get("nodes", []):
        if not isinstance(node, dict) or not (node.get("lifecycle") == "verify" or node.get("blocked") is True):
            continue
        data = node.get("data") if isinstance(node.get("data"), dict) else {}
        text = " ".join(str(data.get(key) or "") for key in ("blocker", "next_action", "acceptance")).lower()
        entry = {"source": "Manager", "title": node.get("title") or node.get("id") or "Untitled",
                 "detail": f"{node.get('id', 'unknown id')} · lifecycle {node.get('lifecycle', 'unknown')}"
                           + (" · blocked" if node.get("blocked") else ""),
                 "options": (f"Resolve: {data.get('blocker') or data.get('next_action') or 'recorded blocker'}",
                             "Keep held and confirm the review date.")}
        if data.get("needs_operator") is True or "operator" in text:
            operator.append(entry)
        else:
            delegated.append(entry)
    local, notes = hq.file_needs()
    experiments, growth_notes = hq.experiment_needs(growth)
    operator.extend(local + experiments)  # approvals, drafts, growth verdicts are operator-only by contract
    decisions = load_decisions()
    for item in operator:
        item["id"] = _item_id(item["source"], item["title"], item["detail"])
        item["decision"] = decisions.get(item["id"])
    ping_new(operator)
    return operator, delegated, notes + growth_notes


def ping_new(operator_items, telegram=True):
    try:
        pinged = set(json.loads(PINGED.read_text(encoding="utf-8"))) if PINGED.is_file() else set()
    except (OSError, json.JSONDecodeError, TypeError):
        pinged = set()
    fresh = [item for item in operator_items if item["id"] not in pinged and not item.get("decision")]
    if not fresh:
        return
    lines = "\n".join(f"- [{item['source']}] {item['title']}" for item in fresh[:8])
    more = f"\n…and {len(fresh) - 8} more" if len(fresh) > 8 else ""
    if telegram:
        threading.Thread(target=_telegram, daemon=True, args=(
            f"NEEDS YOU — {len(fresh)} new decision(s):\n{lines}{more}\nhttp://{HOST}:{PORT}/?view=needs",)).start()
    pinged.update(item["id"] for item in fresh)
    PINGED.parent.mkdir(parents=True, exist_ok=True)
    PINGED.write_text(json.dumps(sorted(pinged)), encoding="utf-8")


def render_needs_v2():
    esc, badge = hq.esc, hq.badge
    manager, manager_error = hq.load_manager()
    operator, delegated, notes = collect_needs_v2(manager, hq.load_growth())
    pending = [item for item in operator if not item.get("decision")]

    cards = []
    for item in operator:
        options = "".join(f"<li>{esc(option)}</li>" for option in item.get("options", ()))
        decision = item.get("decision")
        if decision:
            action = (f'<p class="decided">DECIDED {esc(decision.get("verdict", "?").upper())} · {esc(decision.get("at", ""))}'
                      + (f' · note: {esc(decision.get("note"))}' if decision.get("note") else "")
                      + " — receipted, agent applies it.</p>")
        else:
            action = (f'<div class="decide"><input id="note-{item["id"]}" placeholder="optional note">'
                      f'<button class="yes" onclick="decide(\'{item["id"]}\',\'yes\')">YES</button>'
                      f'<button class="no" onclick="decide(\'{item["id"]}\',\'no\')">NO</button>'
                      f'<button class="hold" onclick="decide(\'{item["id"]}\',\'hold\')">HOLD</button></div>')
        cards.append(f'<article class="need{" done" if decision else ""}"><div>{badge(item["source"], "warn")}</div>'
                     f'<h2>{esc(item["title"])}</h2><p>{esc(item["detail"])}</p><ul>{options}</ul>{action}</article>')

    rows = "".join(f'<div class="drow"><strong>{esc(item["title"])}</strong><small class="muted">{esc(item["detail"])}</small></div>'
                   for item in delegated) or '<div class="empty">Delegated queue is empty.</div>'
    notices = "".join(f'<div class="empty">{esc(note)}</div>' for note in ([manager_error] if manager_error else []) + notes if note)
    content = "".join(cards) or '<div class="empty">Nothing awaits an operator click. Delegated work continues below.</div>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Needs You · {len(pending)}</title><style>
:root{{--bg:#070a07;--panel:#101710;--line:#2a3c2a;--text:#eef7ee;--muted:#93a893;--warn:#ffbe55;--danger:#ff6f6f;--ok:#57d3a0}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,sans-serif}}
header,main{{max-width:1300px;margin:auto;padding:16px 22px}}header{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;border-bottom:1px solid var(--line)}}
header h1{{margin:0}}header p{{margin:.2rem 0;color:var(--muted)}}nav a{{color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:6px 11px;text-decoration:none;margin-left:6px}}
.cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px;margin:14px 0}}
.need{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}}.need.done{{opacity:.55}}
.need h2{{margin:.3rem 0}}.need ul{{padding-left:20px;color:var(--muted)}}.need li{{margin:.35rem 0}}
.badge{{display:inline-block;border-radius:999px;padding:3px 8px;font-size:11px;font-weight:800}}.badge.warn{{background:#4a3614;color:#ffd17c}}.badge.muted{{background:#233544;color:#b6c8d5}}
.decide{{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}}.decide input{{flex:1;min-width:140px;background:#0c120c;border:1px solid var(--line);border-radius:8px;color:var(--text);padding:8px}}
.decide button{{border:0;border-radius:8px;padding:9px 18px;font-weight:800;cursor:pointer}}.yes{{background:var(--ok);color:#06281a}}.no{{background:var(--danger);color:#2b0707}}.hold{{background:var(--warn);color:#2b1d06}}
.decided{{color:var(--ok);font-weight:700}}.empty{{border:1px dashed #3a523a;border-radius:10px;color:var(--muted);padding:12px;margin:8px 0}}
.drow{{padding:8px 2px;border-bottom:1px solid #1c2a1c}}.drow small{{display:block}}.muted{{color:var(--muted)}}
h2.qhead{{margin:26px 0 6px;color:var(--muted);font-size:13px;letter-spacing:.14em;text-transform:uppercase}}
</style></head><body>
<header><div><h1>Needs You {badge(len(pending), "warn")}</h1><p>Only clickable operator decisions. Receipts land in social-ops/operator-decisions.jsonl.</p></div>
<nav><a href="/">HUD</a><a href="/?view=kanban">Kanban</a></nav></header>
<main>{notices}<div class="cards">{content}</div>
<h2 class="qhead">Delegated queue — PM ↔ Sol decide these {badge(len(delegated), "muted")}</h2>{rows}</main>
<script>
async function decide(id, verdict) {{
  const note = (document.getElementById('note-' + id) || {{value: ''}}).value;
  const res = await fetch('/decide', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{id, verdict, note}})}});
  const data = await res.json();
  if (data.error) {{ alert(data.error); return; }}
  location.reload();
}}
</script></body></html>'''


# ---- HUD data
def next_runs(now):
    lanes = [("Weekday authority", (0, 1, 2, 3, 4), 17, 30), ("Saturday recap", (5,), 17, 30), ("Sunday review", (6,), 18, 0)]
    rows = []
    for name, days, hour, minute in lanes:
        for ahead in range(8):
            day = now + timedelta(days=ahead)
            if day.weekday() in days:
                at = day.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if at > now:
                    delta = at - now
                    hours, rem = divmod(int(delta.total_seconds()), 3600)
                    rows.append((name, at, f"in {hours}h {rem // 60:02d}m" if hours else f"in {rem // 60}m"))
                    break
        else:
            continue
    return rows


def artifact_trail(limit=8):
    items = []
    for base, label in ((REPORTS, "report"), (Path(r"C:\Users\MSI\Documents\Manager\vault\receipts"), "receipt")):
        if not base.is_dir():
            continue
        for path in base.glob("**/*.md"):
            items.append((path.stat().st_mtime, label, path))
    items.sort(reverse=True)
    return items[:limit]


def obsidian_link(path):
    try:
        rel = path.relative_to(VAULT)
        return f"obsidian://open?vault={quote(VAULT.name)}&file={quote(rel.as_posix())}"
    except ValueError:
        return "file:///" + quote(path.as_posix(), safe="/:")


def latest_brief():
    briefs = sorted((ROOT / "productions").glob("*/analysis-brief.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not briefs:
        return None, None
    first = next((l.lstrip("# ").strip() for l in briefs[0].read_text(encoding="utf-8-sig").splitlines() if l.startswith("#")), briefs[0].parent.name)
    return briefs[0].parent.name, first


def render_hud():
    esc, badge, number = hq.esc, hq.badge, hq.number
    manager, manager_error = hq.load_manager()
    growth = hq.load_growth()
    operator, delegated, _ = collect_needs_v2(manager, growth)
    needs = [item for item in operator if not item.get("decision")]
    analytics, _ = hq.read_json(hq.ANALYTICS)
    rollup = (analytics or {}).get("rollup", {}) if isinstance(analytics, dict) else {}
    now = datetime.now(ICT)

    vitals = "".join(
        f'<div class="vital"><small>{esc(label)}</small><strong>{esc(number(rollup.get(key)))}</strong></div>'
        for key, label in (("youtubeWeeklyViews", "YouTube weekly views"), ("instagramObservedViews", "Instagram views"),
                           ("facebookObservedViews", "Facebook views"), ("tiktokObservedViews", "TikTok views")))
    if manager:
        metrics = manager.get("metrics", {})
        vitals += (f'<div class="vital"><small>Manager health</small><strong>{"OK" if manager.get("healthy") else "ISSUES"}</strong></div>'
                   f'<div class="vital"><small>Sol queue</small><strong>{esc(metrics.get("sol_decision_queues", "—"))}</strong></div>')
    else:
        vitals += f'<div class="vital warn"><small>Manager</small><strong>OFFLINE</strong></div>'
    vitals += (f'<div class="vital"><small>Needs You (clickable)</small><strong>{len(needs)}</strong></div>'
               f'<div class="vital"><small>Delegated queue</small><strong>{len(delegated)}</strong></div>')

    directives = "".join(f'<li><strong>{esc(item["title"])}</strong><br><small class="muted">{esc(item["detail"])}</small></li>'
                         for item in needs[:3]) or "<li>No operator directives pending.</li>"

    trail = "".join(
        f'<div class="artifact"><span>{badge(label)}</span> <a href="{esc(obsidian_link(path))}">{esc(path.stem)}</a>'
        f'<small class="muted"> · {datetime.fromtimestamp(mtime, ICT):%m-%d %H:%M}</small></div>'
        for mtime, label, path in artifact_trail()) or '<div class="empty">No artifacts yet — run a skill.</div>'

    buttons = "".join(f'<button onclick="runSkill(\'{name}\')" id="btn-{name}">{esc(spec["label"])}</button>'
                      for name, spec in ACTIONS.items())
    schedule = "".join(f'<div class="lane"><span>{esc(name)}</span><strong>{esc(when)}</strong><small class="muted">{at:%a %H:%M} ICT</small></div>'
                       for name, at, when in next_runs(now))
    prod, headline = latest_brief()
    wire = f'<div class="wire"><small>LATEST BRIEF · {esc(prod)}</small><p>{esc(headline)}</p></div>' if headline else ""
    backends = ", ".join(llm_config().get("backends", {}))

    nav = "".join(f'<a href="/?view={name}">{esc(label)}{f" <span>{len(needs)}</span>" if name == "needs" else ""}</a>'
                  for name, label in hq.VIEWS)
    offline = f'<div class="empty">{esc(manager_error)}</div>' if manager_error else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Apollo HQ OS</title><style>
:root{{--bg:#070a07;--panel:#101710;--panel2:#16211664;--line:#2a3c2a;--text:#eef7ee;--muted:#93a893;--accent:#ffb347;--sun:#ff9a2a;--warn:#ffbe55;--danger:#ff6f6f}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 50% -10%,#2b1c08 0,transparent 45%),var(--bg);color:var(--text);font:14px/1.5 system-ui,sans-serif}}
header{{display:flex;justify-content:space-between;align-items:center;gap:16px;flex-wrap:wrap;padding:14px 22px;border-bottom:1px solid var(--line)}}
header h1{{margin:0;font-size:20px;letter-spacing:.12em}}header p{{margin:0;color:var(--muted)}}nav{{display:flex;gap:8px;flex-wrap:wrap}}
nav a{{color:var(--muted);border:1px solid var(--line);border-radius:999px;padding:6px 11px;text-decoration:none;font-size:13px}}nav a span{{background:var(--warn);color:#171006;border-radius:999px;padding:1px 6px}}
main{{display:grid;grid-template-columns:260px 1fr 300px;gap:16px;max-width:1700px;margin:auto;padding:16px 22px}}
.rail,.center{{display:flex;flex-direction:column;gap:12px}}.panel{{background:linear-gradient(150deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:14px;padding:14px}}
.panel h2{{margin:0 0 10px;font-size:12px;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}}
.vital{{display:flex;justify-content:space-between;align-items:baseline;padding:7px 2px;border-bottom:1px solid #1c2a1c}}.vital strong{{font-size:19px}}.vital small{{color:var(--muted)}}.vital.warn strong{{color:var(--danger)}}
.orb{{width:150px;height:150px;border-radius:50%;margin:6px auto;background:radial-gradient(circle at 38% 34%,#ffe9b0 0,var(--sun) 42%,#8a3c00 78%,#3a1800 100%);box-shadow:0 0 55px 12px rgba(255,154,42,.45), inset -14px -18px 40px rgba(80,20,0,.6);animation:breathe 5s ease-in-out infinite}}
@keyframes breathe{{50%{{box-shadow:0 0 75px 20px rgba(255,154,42,.6), inset -14px -18px 40px rgba(80,20,0,.6)}}}}
.center .apollo{{text-align:center}}.apollo p{{color:var(--muted);margin:.3rem 0 0}}
ol.directives{{margin:0;padding-left:20px}}ol.directives li{{margin:.5rem 0}}
.artifact{{padding:7px 0;border-bottom:1px solid #1c2a1c}}.artifact a{{color:#ffd28f;text-decoration:none}}.artifact a:hover{{text-decoration:underline}}
.badge{{display:inline-block;border-radius:999px;padding:2px 7px;font-size:10px;font-weight:800;letter-spacing:.05em;background:#233544;color:#b6c8d5}}
button{{display:block;width:100%;margin:6px 0;padding:10px;border-radius:10px;border:1px solid var(--line);background:#182518;color:var(--text);font-weight:700;cursor:pointer;text-align:left}}
button:hover{{border-color:var(--accent)}}button.running{{border-color:var(--warn);color:var(--warn)}}button.done{{border-color:#57d3a0}}button.failed{{border-color:var(--danger)}}
.lane{{display:flex;justify-content:space-between;gap:8px;padding:6px 0;border-bottom:1px solid #1c2a1c}}.lane strong{{color:var(--accent)}}
.wire p{{margin:.3rem 0 0}}textarea{{width:100%;min-height:64px;background:#0c120c;border:1px solid var(--line);border-radius:10px;color:var(--text);padding:9px;font:inherit}}
select{{background:#0c120c;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:7px}}
#llm-out{{white-space:pre-wrap;background:#0c120c;border:1px solid var(--line);border-radius:10px;padding:10px;max-height:300px;overflow:auto;margin-top:8px;display:none}}
.empty{{border:1px dashed #3a523a;border-radius:10px;color:var(--muted);padding:10px;margin:6px 0}}.muted{{color:var(--muted)}}
#jobs .job{{font-size:12px;color:var(--muted);padding:4px 0}}
@media(max-width:1100px){{main{{grid-template-columns:1fr}}}}
</style></head><body>
<header><div><h1>APOLLO HQ OS</h1><p>{now:%A %Y-%m-%d %H:%M} ICT · localhost only</p></div><nav><a href="/">HUD</a>{nav}</nav></header>
<main>
<div class="rail">
  <div class="panel"><h2>Vitals</h2>{vitals}</div>
  <div class="panel"><h2>Schedule</h2>{schedule}</div>
  {f'<div class="panel"><h2>Wire</h2>{wire}</div>' if wire else ''}
</div>
<div class="center">
  <div class="panel apollo"><div class="orb"></div><p>Apollo — analyst on duty. Ask below or run a skill.</p></div>
  {offline}
  <div class="panel"><h2>Directives — your clicks only</h2><ol class="directives">{directives}</ol><p><a href="/?view=needs" style="color:#ffd28f">Decide all {len(needs)} → (delegated queue: {len(delegated)})</a></p></div>
  <div class="panel"><h2>Talk to any LLM <small class="muted">({esc(backends)})</small></h2>
    <textarea id="llm-prompt" placeholder="Ask Apollo (routes to the selected backend)…"></textarea>
    <div style="display:flex;gap:8px;margin-top:8px"><select id="llm-backend">{"".join(f'<option value="{esc(b)}">{esc(b)}</option>' for b in llm_config().get("backends", {}))}</select>
    <button style="width:auto" onclick="askLLM()">Send</button></div><div id="llm-out"></div></div>
  <div class="panel"><h2>Artifact trail</h2>{trail}</div>
</div>
<div class="rail">
  <div class="panel"><h2>Skills</h2>{buttons}<div id="jobs"></div></div>
</div>
</main>
<script>
async function runSkill(name) {{
  const btn = document.getElementById('btn-' + name);
  btn.className = 'running'; btn.disabled = true;
  const res = await fetch('/run/' + name, {{method: 'POST'}});
  const job = await res.json();
  poll(job.id, name);
}}
async function poll(id, name) {{
  const btn = document.getElementById('btn-' + name);
  const res = await fetch('/jobs'); const jobs = await res.json();
  const job = jobs[id];
  if (!job) return;
  if (job.status === 'running' || job.status === 'queued') {{ setTimeout(() => poll(id, name), 1500); return; }}
  btn.className = job.status; btn.disabled = false;
  const div = document.getElementById('jobs');
  div.innerHTML = '<div class="job">' + name + ': ' + job.status + (job.report ? ' — report saved to vault (see trail after refresh)' : '') + '</div>' + div.innerHTML;
}}
async function askLLM() {{
  const out = document.getElementById('llm-out');
  out.style.display = 'block'; out.textContent = 'thinking…';
  const res = await fetch('/llm', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{prompt: document.getElementById('llm-prompt').value, backend: document.getElementById('llm-backend').value}})}});
  const data = await res.json();
  out.textContent = '[' + data.backend + ']\\n' + data.reply;
}}
</script></body></html>'''


class OSHandler(BaseHTTPRequestHandler):
    def _send(self, payload, status=200, content_type="text/html; charset=utf-8"):
        body = payload if isinstance(payload, bytes) else payload.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/jobs":
            with JOBS_LOCK:
                self._send(json.dumps(JOBS), content_type="application/json")
        elif parsed.path == "/" and "view" in parse_qs(parsed.query):
            view = parse_qs(parsed.query)["view"][0]
            self._send(render_needs_v2() if view == "needs" else hq.build_page(view))
        elif parsed.path == "/":
            self._send(render_hud())
        else:
            self._send("not found", 404, "text/plain; charset=utf-8")

    def do_POST(self):  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path.startswith("/run/"):
            action = parsed.path[len("/run/"):]
            if action not in ACTIONS:
                self._send(json.dumps({"error": "action not allowlisted"}), 403, "application/json")
                return
            job_id = uuid.uuid4().hex[:10]
            with JOBS_LOCK:
                JOBS[job_id] = {"id": job_id, "action": action, "status": "queued"}
            threading.Thread(target=run_job, args=(job_id, action), daemon=True).start()
            self._send(json.dumps({"id": job_id}), content_type="application/json")
        elif parsed.path == "/llm":
            length = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                data = {}
            prompt = str(data.get("prompt", "")).strip()
            if not prompt:
                self._send(json.dumps({"backend": "-", "reply": "empty prompt"}), content_type="application/json")
                return
            backend, reply = ask_llm(prompt, data.get("backend"))
            self._send(json.dumps({"backend": backend, "reply": reply}), content_type="application/json")
        elif parsed.path == "/decide":
            length = int(self.headers.get("Content-Length", 0))
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                data = {}
            verdict = str(data.get("verdict", "")).lower()
            if verdict not in {"yes", "no", "hold"}:
                self._send(json.dumps({"error": "verdict must be yes/no/hold"}), 400, "application/json")
                return
            manager, _ = hq.load_manager()
            operator, _, _ = collect_needs_v2(manager, hq.load_growth())
            item = next((entry for entry in operator if entry["id"] == data.get("id")), None)
            if not item:
                self._send(json.dumps({"error": "stale or unknown item — refresh the page"}), 404, "application/json")
                return
            if item.get("decision"):
                self._send(json.dumps({"error": "already decided — refresh the page"}), 409, "application/json")
                return
            record = record_decision(item, verdict, str(data.get("note", ""))[:500])
            self._send(json.dumps(record), content_type="application/json")
        else:
            self._send("not found", 404, "text/plain; charset=utf-8")

    def log_message(self, *args):
        return


def selftest():
    """Smallest check that fails if the decision path breaks: id, receipt append, dedupe ping."""
    import tempfile
    global DECISIONS, PINGED
    tmp = Path(tempfile.mkdtemp())
    DECISIONS, PINGED = tmp / "decisions.jsonl", tmp / "pinged.json"
    item = {"id": _item_id("Test", "Dummy approval", "detail"), "source": "Test",
            "title": "Dummy approval", "detail": "detail"}
    assert item["id"] == _item_id("Test", "Dummy approval", "detail"), "id not stable"
    record_decision(item, "yes", "selftest note", telegram=False)
    loaded = load_decisions()
    assert loaded[item["id"]]["verdict"] == "yes" and loaded[item["id"]]["note"] == "selftest note"
    ping_new([dict(item, decision=None)], telegram=False)
    assert item["id"] in set(json.loads(PINGED.read_text(encoding="utf-8"))), "ping dedupe state missing"
    before = PINGED.read_text(encoding="utf-8")
    ping_new([dict(item, decision=None)], telegram=False)
    assert PINGED.read_text(encoding="utf-8") == before, "re-pinged an already-pinged item"
    print("selftest OK")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    no_open = "--no-open" in sys.argv
    server = ThreadingHTTPServer((HOST, PORT), OSHandler)
    if not no_open:
        webbrowser.open(f"http://{HOST}:{PORT}")
    print(f"Apollo HQ OS at http://{HOST}:{PORT} — Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
