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
import re
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
# ponytail: old TraderCockpit-Vault is tombstoned (read-only) — reports now live repo-local
VAULT = Path(r"C:\Users\MSI\Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit")
REPORTS = ROOT / "social-ops" / "reports"
LLM_CONFIG = ROOT / "tools" / "hq-llm.json"
HOST, PORT = "127.0.0.1", 8786
MANAGER_DASHBOARD = "http://127.0.0.1:8790"
ICT = timezone(timedelta(hours=7))
PY = sys.executable
OM_PY = str(ROOT / "OpenMontage" / ".venv" / "Scripts" / "python.exe")
DECISIONS = ROOT / "social-ops" / "operator-decisions.jsonl"
PINGED = ROOT / "social-ops" / "needs-you-pinged.json"
SKILL_CATALOG = ROOT / "social-ops" / "skill-catalog.json"

MANAGER_VIEWS = (
    ("today", "Today"),
    ("kanban", "Kanban"),
    ("features", "All Features"),
    ("risks", "Risks"),
    ("prop", "Prop RuleFit"),
)
LOCAL_VIEWS = (
    ("departments", "Departments"),
    ("platforms", "Platforms"),
    ("ads", "Ads Pipeline"),
    ("graph", "Knowledge Graph"),
    ("needs", "Needs You"),
)
GRAPH_HTML = ROOT / "graphify-out" / "graph.html"
CENTRAL_VIEWS = MANAGER_VIEWS + LOCAL_VIEWS

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
    "skills-refresh": {"label": "Refresh skill catalog", "argv": [PY, "tools/skill_catalog.py"]},
    # ponytail: cmd /c chain because run_job takes one argv; split into a script if this grows
    "graph-refresh": {"label": "Rebuild knowledge graph", "argv": ["cmd", "/c", "graphify update . && graphify export html"]},
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


# ---- any-LLM console — multi-turn chat state
CHATS = {}
CHATS_LOCK = threading.Lock()
MAX_CHAT_HISTORY = 40   # operator+apollo turns kept per chat
MAX_CHATS = 20          # oldest chat evicted once this many chats exist
TRANSCRIPT_CAP = 6000   # chars of stuffed transcript sent to non-session backends

MANAGER_RECEIPTS = Path(r"C:\Users\MSI\Documents\Manager\vault")
APOLLO_SYSTEM = f"""You are Apollo, the TraderCockpit operator's on-duty analyst. House Claims Ontology discipline applies (operator ruling 2026-07-13: everything Apollo says has an ontology receipt).
RECEIPT CONTRACT — non-negotiable:
- Every factual claim about our operations, metrics, pipelines, decisions, or history ends with a receipt tag in EXACTLY this literal format: [receipt: <path>] or [receipt: <path>#<anchor>]. Markdown links, backticked paths, or path:line mentions do NOT count as receipts — the audit gate only parses the [receipt: ...] tag and will BLOCK the reply without it.
- Valid receipt roots: this repo ({ROOT}), the ops vault ({VAULT}), Manager receipts ({MANAGER_RECEIPTS}), the vault knowledge graph ({ROOT / 'graphify-out' / 'graph.json'}#<node_id>).
- You have Read/Grep/Glob tools: open the source and verify BEFORE you assert. Never cite a file you did not read this turn.
- Nothing on disk supports the claim -> write exactly: NO RECEIPT — unverified. Never present an unreceipted number or status as fact.
- Opinions and suggestions are welcome but label them (e.g. "suggestion:") when mixed with facts.
Be terse, operator-grade. An independent receipt gate audits every reply; unreceipted numbers are BLOCKED."""

RECEIPT_RE = re.compile(r"\[receipt:\s*([^\]\s][^\]]*)\]")
# writers cite naturally as `path.md:12-34` — the gate verifies those too instead of fighting the style
PATH_CITE_RE = re.compile(r"`([^`\n]+?\.[A-Za-z0-9]{1,5})(?::[0-9][0-9,\-]*)?`")


def receipt_gate(reply):
    """Independent PASS/BLOCK stamp on a chat reply (Claims Ontology: citation emission alone
    leaves ~30% unsupported — the enforcement pass is the product). Checker shares no reasoning
    with the writer: it only resolves cited paths and sweeps for uncovered numbers.
    # ponytail: coverage = numbers-present vs receipts-present + path/node existence, not
    # per-number claim mapping — upgrade path is claims_gate-style region coverage."""
    receipts = RECEIPT_RE.findall(reply) + PATH_CITE_RE.findall(reply)
    dead = []
    for ref in receipts:
        path, _, frag = ref.partition("#")
        p = Path(path.strip().strip('"'))
        candidates = [p] if p.is_absolute() else [ROOT / p, VAULT / p, MANAGER_RECEIPTS / p]
        hit = next((c for c in candidates if c.exists()), None)
        if hit is None:
            dead.append(ref)
        elif frag and hit.name == "graph.json":
            try:
                nodes = {n.get("id") for n in json.loads(hit.read_text(encoding="utf-8")).get("nodes", [])}
                if frag.strip() not in nodes:
                    dead.append(ref)
            except (OSError, json.JSONDecodeError):
                dead.append(ref)
    body = PATH_CITE_RE.sub("", RECEIPT_RE.sub("", reply))
    try:
        from claims_gate import find_number_regions
        numbered = bool(find_number_regions(body))
    except Exception:  # gate must never die with the writer's output pending
        numbered = bool(re.search(r"\d", body))
    if dead:
        return "BLOCK", f"{len(dead)} dead receipt(s): " + ", ".join(dead[:3])
    if numbered and not receipts and "NO RECEIPT" not in reply:
        return "BLOCK", "number-bearing reply with zero receipts"
    if receipts:
        return "PASS", f"{len(receipts)} receipt(s) verified on disk"
    if numbered:
        return "PASS", "explicitly marked unverified"
    return "PASS", "no factual claims asserted"


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
    return DEFAULT_LLM


def build_transcript(history, new_prompt, cap=TRANSCRIPT_CAP):
    """Pure: prior turns + the new prompt as a compact transcript, capped to the last `cap` chars.
    Used by non-session backends (codex/ollama-generate/openai) and by claude when it has no session."""
    lines = [f"{'Operator' if turn.get('role') == 'operator' else 'Apollo'}: {turn.get('text', '')}"
             for turn in history]
    lines.append(f"Operator: {new_prompt}")
    transcript = "\n".join(lines)
    return transcript[-cap:] if len(transcript) > cap else transcript


def _run_claude_cli(prompt, history, claude_session):
    """Real session continuity via `claude --resume`. No session yet -> transcript-stuffed fresh turn
    (still tries --output-format json, so a valid session can be recovered). JSON parse failure ->
    raw stdout as the reply and no session recorded, so the next turn falls back to transcript mode too."""
    import shutil
    exe = shutil.which("claude") or "claude"
    if claude_session:
        argv = [exe, "-p", prompt, "--resume", claude_session, "--output-format", "json"]
    else:
        stuffed = build_transcript(history, prompt) if history else prompt
        argv = [exe, "-p", stuffed, "--output-format", "json"]
    argv += ["--append-system-prompt", APOLLO_SYSTEM]
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=300, shell=False,
                          encoding="utf-8", errors="replace")
    raw = (proc.stdout or proc.stderr or "").strip()
    try:
        data = json.loads(raw)
        result = str(data.get("result") or "").strip()
        return (result or raw or "(no output)")[-8000:], (data.get("session_id") or None)
    except (json.JSONDecodeError, ValueError, TypeError):
        return (raw or "(no output)")[-8000:], None


def ask_llm(prompt, backend_name, history, claude_session):
    """One backend turn. Returns (backend_name, reply_text, new_claude_session_or_None).
    `history` is the chat's prior turns ([{"role": "operator"|"apollo", "text": ...}, ...]); the
    caller (handle_llm_turn) owns CHATS and appends this turn once the call returns."""
    config = llm_config()
    name = backend_name or config.get("default", "claude")
    backend = (config.get("backends") or {}).get(name)
    if not backend:
        return name, f"BLOCK: backend '{name}' is not configured in tools/hq-llm.json", None
    kind = backend.get("type")
    try:
        if name == "claude":
            reply, session_id = _run_claude_cli(prompt, history, claude_session)
            return name, reply, session_id
        if kind == "cli":
            import shutil
            argv = list(backend["argv"])
            argv[0] = shutil.which(argv[0]) or argv[0]  # npm shims need .cmd resolution on Windows
            stuffed = APOLLO_SYSTEM + "\n\n" + build_transcript(history, prompt)
            proc = subprocess.run([*argv, stuffed], cwd=ROOT, capture_output=True,
                                  text=True, timeout=300, shell=False,
                                  encoding="utf-8", errors="replace")
            return name, (proc.stdout or proc.stderr or "(no output)").strip()[-8000:], None
        if kind == "ollama":
            messages = [{"role": "system", "content": APOLLO_SYSTEM}]
            messages += [{"role": "user" if turn.get("role") == "operator" else "assistant",
                          "content": turn.get("text", "")} for turn in history]
            messages.append({"role": "user", "content": prompt})
            body = json.dumps({"model": backend.get("model"), "messages": messages, "stream": False}).encode()
            req = Request(backend.get("url", "http://127.0.0.1:11434") + "/api/chat",
                          data=body, headers={"Content-Type": "application/json"})
            with urlopen(req, timeout=300) as response:  # noqa: S310 - operator-configured local/loopback
                data = json.load(response)
            return name, (data.get("message") or {}).get("content", "(no response)")[-8000:], None
        if kind == "openai":
            key = ""
            key_env = backend.get("key_env")
            if key_env:
                from credential_custody import credential_path
                env_file = credential_path(backend.get("key_file", "telegram.env"))
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    if line.startswith(key_env + "="):
                        key = line.split("=", 1)[1].strip()
            stuffed = build_transcript(history, prompt)
            body = json.dumps({"model": backend.get("model"),
                               "messages": [{"role": "system", "content": APOLLO_SYSTEM},
                                            {"role": "user", "content": stuffed}]}).encode()
            req = Request(backend["base_url"].rstrip("/") + "/chat/completions", data=body,
                          headers={"Content-Type": "application/json",
                                   **({"Authorization": f"Bearer {key}"} if key else {})})
            with urlopen(req, timeout=300) as response:  # noqa: S310 - operator-configured endpoint
                data = json.load(response)
            return name, data["choices"][0]["message"]["content"][-8000:], None
        return name, f"BLOCK: unknown backend type '{kind}'", None
    except Exception as error:  # surfaced to the console, never crashes the shell
        return name, f"{type(error).__name__}: {error}", None


def handle_llm_turn(prompt, backend_name, chat_id):
    """Chat bookkeeping around ask_llm: resolve/create the chat (new uuid on missing/stale chat_id or
    a backend switch), run the turn, then persist history capped at MAX_CHAT_HISTORY."""
    config = llm_config()
    name = backend_name or config.get("default", "claude")
    with CHATS_LOCK:
        chat = CHATS.get(chat_id) if chat_id else None
        if chat is None or chat["backend"] != name:
            chat_id = uuid.uuid4().hex[:12]
            if len(CHATS) >= MAX_CHATS:
                CHATS.pop(next(iter(CHATS)))  # evict oldest
            chat = {"backend": name, "claude_session": None, "history": []}
            CHATS[chat_id] = chat
        history = list(chat["history"])
        claude_session = chat["claude_session"]

    backend, reply, new_session = ask_llm(prompt, name, history, claude_session)
    verdict, detail = receipt_gate(reply)
    reply = f"{reply}\n\nRECEIPT GATE: {verdict} — {detail}"

    with CHATS_LOCK:
        chat = CHATS.get(chat_id)
        if chat is not None:
            chat["history"].append({"role": "operator", "text": prompt})
            chat["history"].append({"role": "apollo", "text": reply})
            del chat["history"][:-MAX_CHAT_HISTORY]
            if backend == "claude":
                chat["claude_session"] = new_session
    return backend, reply, chat_id


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
    return operator, delegated, notes + growth_notes


# ---- one shared design system: HUD, Needs You and every framed view render from this string
# (plain constant → single braces; interpolated as {BASE_CSS} inside each renderer's f-string)
BASE_CSS = """
:root{
  --bg:#070a07;--bg-glow:#241706;--panel:#0f150f;--panel-2:#131c13;--raise:#182218;
  --line:#233223;--line-2:#31462f;--hair:#16211648;
  --text:#eef7ee;--muted:#93a893;--faint:#6c7f6c;
  --accent:#ffb347;--accent-2:#ff9a2a;--ok:#57d3a0;--warn:#ffbe55;--danger:#ff6f6f;
  --r1:9px;--r2:12px;--r3:16px;
}
*{box-sizing:border-box}
body{margin:0;color:var(--text);font:14px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  background:radial-gradient(1100px 420px at 50% -10%,var(--bg-glow) 0,transparent 60%),var(--bg);
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:inherit;text-decoration:none}
::selection{background:var(--accent);color:#171006}
.num{font-variant-numeric:tabular-nums;font-feature-settings:"tnum" 1}
.muted{color:var(--muted)}
.empty{border:1px dashed #2f4a2f;border-radius:var(--r2);color:var(--muted);padding:12px;margin:6px 0;font-size:13px}
.badge{display:inline-flex;align-items:center;border-radius:999px;padding:2px 8px;font-size:10px;font-weight:800;letter-spacing:.06em;background:#233544;color:#b6c8d5;vertical-align:middle}
.badge.warn{background:#4a3614;color:#ffd17c}
.badge.muted{background:#233544;color:#b6c8d5}

/* top bar + grouped nav */
.topbar{display:flex;align-items:center;justify-content:space-between;gap:14px 26px;flex-wrap:wrap;
  padding:12px 22px;border-bottom:1px solid var(--line);
  background:linear-gradient(180deg,rgba(255,179,71,.045),transparent)}
.brand{display:flex;align-items:baseline;gap:10px;white-space:nowrap}
.brand h1{margin:0;font-size:16px;letter-spacing:.18em;font-weight:800}
.brand .ac{color:var(--accent)}
.brand small{color:var(--muted);font-size:12px;letter-spacing:.02em}
.nav{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.nav .home{padding:7px 14px;border-radius:var(--r1);border:1px solid var(--line);color:var(--muted);
  font-size:12.5px;font-weight:700;letter-spacing:.03em;transition:background .15s,border-color .15s,color .15s}
.nav .home:hover{border-color:var(--line-2);color:var(--text)}
.nav .home.selected{background:var(--accent);border-color:var(--accent);color:#171006}
.navgroup{display:flex;align-items:center;gap:8px}
.navgroup .glabel{font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:var(--faint);font-weight:800}
.seg{display:flex;background:var(--panel);border:1px solid var(--line);border-radius:var(--r1);overflow:hidden}
.seg a{padding:7px 12px;color:var(--muted);font-size:12.5px;border-left:1px solid var(--line);white-space:nowrap;
  transition:background .15s,color .15s}
.seg a:first-child{border-left:0}
.seg a:hover{background:var(--raise);color:var(--text)}
.seg a.selected{background:var(--accent);color:#171006;font-weight:700}
.nav .needs{display:inline-flex;align-items:center;gap:8px;padding:7px 13px;border-radius:var(--r1);
  border:1px solid var(--line);color:var(--muted);font-size:12.5px;font-weight:700;
  transition:background .15s,border-color .15s,color .15s}
.nav .needs:hover{border-color:var(--line-2);color:var(--text)}
.nav .needs.alert{border-color:#7a5416;color:var(--accent);background:rgba(255,179,71,.06)}
.nav .needs.selected{background:var(--accent);border-color:var(--accent);color:#171006}
.nav .needs .cnt{background:var(--danger);color:#2b0707;border-radius:999px;padding:1px 7px;font-size:11px;font-weight:800}
.nav .needs.alert .cnt{background:var(--accent);color:#171006}
.nav .needs.selected .cnt{background:#171006;color:var(--accent)}

/* panels + HUD grid */
.wrap{max-width:1720px;margin:0 auto;padding:18px 22px}
.panel{background:linear-gradient(160deg,var(--panel-2),var(--panel));border:1px solid var(--line);
  border-radius:var(--r3);padding:15px}
.panel>h2{margin:0 0 12px;font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--faint);
  font-weight:800;display:flex;align-items:center;justify-content:space-between;gap:10px}
.panel>h2 small{font-weight:600;letter-spacing:.02em;text-transform:none;color:var(--muted);font-size:11px}
.hud{display:grid;grid-template-columns:264px minmax(0,1fr) 320px;gap:16px;align-items:start}
.col{display:flex;flex-direction:column;gap:14px;min-width:0}
@media(max-width:1180px){.hud{grid-template-columns:1fr}}

/* vitals */
.vital{display:flex;align-items:baseline;justify-content:space-between;gap:12px;padding:8px 2px;border-bottom:1px solid var(--hair)}
.vital:last-child{border-bottom:0}
.vital small{color:var(--muted);font-size:12px}
.vital strong{font-size:17px;font-weight:700;font-variant-numeric:tabular-nums}
.vital.warn strong{color:var(--danger);letter-spacing:.08em;text-shadow:0 0 14px rgba(255,111,111,.35)}

/* apollo strip */
.apollo{display:flex;align-items:center;gap:14px}
.orb{width:46px;height:46px;flex:none;border-radius:50%;
  background:radial-gradient(circle at 38% 34%,#ffe9b0 0,var(--accent-2) 45%,#8a3c00 80%,#3a1800 100%);
  box-shadow:0 0 20px 4px rgba(255,154,42,.35),inset -5px -7px 15px rgba(80,20,0,.6);
  animation:breathe 5s ease-in-out infinite}
@keyframes breathe{50%{box-shadow:0 0 30px 8px rgba(255,154,42,.5),inset -5px -7px 15px rgba(80,20,0,.6)}}
.apollo .who{font-weight:700;font-size:15px}
.apollo .sub{color:var(--muted);font-size:12.5px;margin-top:2px}
.apollo .sub b{color:var(--accent);font-weight:600}

/* llm console (multi-turn chat) */
.console h2{align-items:center}
.console .new-chat{padding:5px 12px;border-radius:999px;border:1px solid var(--line);background:transparent;
  color:var(--muted);font:inherit;font-size:11px;font-weight:700;cursor:pointer;transition:background .15s,border-color .15s,color .15s}
.console .new-chat:hover{border-color:var(--line-2);color:var(--text)}
.console textarea{width:100%;min-height:90px;resize:vertical;background:#0b110b;border:1px solid var(--line);
  border-radius:var(--r2);color:var(--text);padding:12px;font:inherit;line-height:1.5;transition:border-color .15s}
.console textarea:focus{outline:0;border-color:var(--accent)}
.console textarea:disabled{opacity:.55;cursor:not-allowed}
.console .row{display:flex;align-items:center;gap:10px;margin-top:10px}
.console select{background:#0b110b;color:var(--text);border:1px solid var(--line);border-radius:var(--r1);
  padding:9px 10px;font:inherit;transition:border-color .15s}
.console select:focus{outline:0;border-color:var(--accent)}
.console .spacer{flex:1}
.btn-primary{background:var(--accent);color:#171006;border:0;border-radius:var(--r1);padding:10px 24px;
  font:inherit;font-weight:800;cursor:pointer;transition:filter .15s}
.btn-primary:hover{filter:brightness(1.07)}
.btn-primary:disabled{opacity:.6;cursor:not-allowed;filter:none}
#llm-out{display:flex;flex-direction:column;gap:8px;background:#0b110b;border:1px solid var(--line);
  border-radius:var(--r2);padding:12px;max-height:340px;overflow:auto;margin-bottom:10px}
#llm-out:empty{display:none}
.msg{display:flex}
.msg.operator{justify-content:flex-end}
.msg.apollo{justify-content:flex-start}
.bubble{max-width:82%;padding:9px 12px;border-radius:var(--r2);font-size:13px;line-height:1.5;
  white-space:pre-wrap;word-wrap:break-word}
.msg.operator .bubble{background:rgba(255,179,71,.16);border:1px solid rgba(255,179,71,.32)}
.msg.apollo .bubble{background:var(--raise);border:1px solid var(--line)}
#llm-thinking{margin:0 0 10px;color:var(--muted);font-size:12px;font-style:italic}

/* directives + artifact trail */
.directives{margin:0;padding:0;list-style:none}
.directives li{padding:9px 0;border-bottom:1px solid var(--hair)}
.directives li:last-child{border-bottom:0}
.directives .t{display:block;font-weight:600}
.directives .d{display:block;color:var(--muted);font-size:12px;margin-top:2px}
.decide-all{display:inline-block;margin-top:11px;color:var(--accent);font-weight:600;font-size:13px}
.decide-all:hover{text-decoration:underline}
.artifact{display:flex;align-items:center;gap:9px;padding:8px 0;border-bottom:1px solid var(--hair);font-size:13px}
.artifact:last-child{border-bottom:0}
.artifact a{color:var(--accent);flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.artifact a:hover{text-decoration:underline}
.artifact time{color:var(--faint);font-size:11px;font-variant-numeric:tabular-nums;white-space:nowrap}

/* one-click actions (id-anchored so JS className swaps keep the base style) */
.actions{display:flex;flex-direction:column;gap:7px}
button[id^="btn-"]{display:block;width:100%;text-align:left;margin:0;padding:10px 12px;border-radius:var(--r1);
  border:1px solid var(--line);background:var(--raise);color:var(--text);font:inherit;font-weight:600;font-size:13px;
  cursor:pointer;transition:background .15s,border-color .15s,color .15s}
button[id^="btn-"]:hover{border-color:var(--accent);background:#1c2a1c}
button[id^="btn-"].running{border-color:var(--warn);color:var(--warn)}
button[id^="btn-"].done{border-color:var(--ok);color:var(--ok)}
button[id^="btn-"].failed{border-color:var(--danger);color:var(--danger)}
#jobs{margin-top:9px;display:flex;flex-direction:column}
#jobs .job{font-size:12px;color:var(--muted);padding:5px 0;border-top:1px solid var(--hair)}

/* skills rail */
.skill-tools{display:flex;flex-direction:column;gap:9px;margin-bottom:10px}
.chips{display:flex;gap:6px;flex-wrap:wrap}
.chip{padding:5px 11px;border-radius:999px;border:1px solid var(--line);background:transparent;color:var(--muted);
  font:inherit;font-size:11.5px;font-weight:600;cursor:pointer;transition:background .15s,border-color .15s,color .15s}
.chip:hover{border-color:var(--line-2);color:var(--text)}
.chip.on{background:var(--accent);border-color:var(--accent);color:#171006}
.chip b{font-weight:800;opacity:.75;margin-left:3px;font-variant-numeric:tabular-nums}
.chip.on b{opacity:.9}
.skill-search{width:100%;background:#0b110b;color:var(--text);border:1px solid var(--line);border-radius:var(--r1);
  padding:9px 11px;font:inherit;font-size:13px;transition:border-color .15s}
.skill-search:focus{outline:0;border-color:var(--accent)}
.skill-list{display:flex;flex-direction:column;gap:1px;max-height:560px;overflow:auto;margin:0 -5px;padding:0 5px}
.skill-entry{display:block;width:100%;text-align:left;background:transparent;border:0;border-radius:var(--r1);
  padding:8px 9px;color:var(--text);font:inherit;cursor:pointer;transition:background .12s}
.skill-entry:hover{background:var(--raise)}
.skill-entry .top{display:flex;align-items:center;gap:9px}
.skill-entry .dot{width:8px;height:8px;border-radius:50%;flex:none;background:var(--faint);box-shadow:0 0 0 3px rgba(108,127,108,.12)}
.skill-entry.gated .dot{background:var(--accent);box-shadow:0 0 0 3px rgba(255,179,71,.15)}
.skill-entry.missing .dot{background:#33432f;box-shadow:none}
.skill-entry .nm{font-weight:600;font-size:13px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.skill-entry.missing .nm{color:var(--muted)}
.skill-entry .uses{margin-left:auto;flex:none;background:#1c3327;color:#8ee3b5;border-radius:999px;
  padding:1px 7px;font-size:10.5px;font-weight:700;font-variant-numeric:tabular-nums}
.skill-entry .desc{color:var(--muted);font-size:11.5px;line-height:1.4;margin-top:3px;padding-left:17px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.skill-entry:hover .desc{white-space:normal}
.skill-entry.missing{opacity:.5;cursor:not-allowed}
.skill-entry[hidden]{display:none}

/* schedule + wire */
.lane{display:grid;grid-template-columns:1fr auto;gap:2px 12px;padding:8px 0;border-bottom:1px solid var(--hair)}
.lane:last-child{border-bottom:0}
.lane .nm{font-size:12.5px}
.lane .in{color:var(--accent);font-weight:700;text-align:right;font-variant-numeric:tabular-nums}
.lane .at{grid-column:1/-1;color:var(--faint);font-size:11px}
.wire small{color:var(--faint);font-size:10px;letter-spacing:.1em;text-transform:uppercase}
.wire p{margin:6px 0 0;font-size:13px;line-height:1.45}

/* needs you page */
.needs-wrap{max-width:1320px;margin:0 auto;padding:18px 22px}
.needs-head h1{margin:0;font-size:22px;display:flex;align-items:center;gap:10px}
.needs-head p{margin:6px 0 0;color:var(--muted);font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px;margin:16px 0}
.need{display:flex;flex-direction:column;gap:8px;background:linear-gradient(160deg,var(--panel-2),var(--panel));
  border:1px solid var(--line);border-radius:var(--r3);padding:16px}
.need.done{opacity:.55}
.need h2{margin:0;font-size:15px}
.need .meta{color:var(--muted);font-size:12px}
.need ul{margin:2px 0 0;padding-left:18px;color:var(--muted);font-size:13px;display:flex;flex-direction:column;gap:4px}
.decide{display:flex;gap:8px;margin-top:6px;flex-wrap:wrap}
.decide input{flex:1;min-width:150px;background:#0b110b;border:1px solid var(--line);border-radius:var(--r1);
  color:var(--text);padding:9px;font:inherit;transition:border-color .15s}
.decide input:focus{outline:0;border-color:var(--accent)}
.decide button{border:0;border-radius:var(--r1);padding:9px 18px;font:inherit;font-weight:800;cursor:pointer;transition:filter .15s}
.decide button:hover{filter:brightness(1.08)}
.yes{background:var(--ok);color:#06281a}.no{background:var(--danger);color:#2b0707}.hold{background:var(--warn);color:#2b1d06}
.decided{color:var(--ok);font-weight:600;font-size:13px;margin:0}
.qhead{margin:28px 0 8px;color:var(--faint);font-size:11px;letter-spacing:.16em;text-transform:uppercase;
  display:flex;align-items:center;gap:9px}
.drow{display:flex;flex-direction:column;gap:2px;padding:10px 2px;border-bottom:1px solid var(--hair)}
.drow strong{font-weight:600;font-size:13px}
.drow small{color:var(--muted);font-size:12px}

/* framed view: nav stays put, iframe fills the rest */
body.framed{display:flex;flex-direction:column;height:100vh;overflow:hidden}
.framed .topbar{flex:none}
.framed iframe{flex:1;width:100%;border:0;background:#071018;display:block}
"""


def central_nav(needs=0, selected=None):
    """One grouped nav for every page: HUD · Manager group · Studio group · Needs You alert."""
    def link(name, label):
        cls = ' class="selected"' if name == selected else ""
        return f'<a{cls} href="/?view={name}">{hq.esc(label)}</a>'
    manager = "".join(link(name, label) for name, label in MANAGER_VIEWS)
    studio = "".join(link(name, label) for name, label in LOCAL_VIEWS if name != "needs")
    home_sel = " selected" if selected == "hud" else ""
    needs_sel = " selected" if selected == "needs" else ""
    alert = " alert" if needs else ""
    count = f'<span class="cnt num">{needs}</span>' if needs else ""
    return (
        f'<nav class="nav"><a class="home{home_sel}" href="/">HUD</a>'
        f'<span class="navgroup"><span class="glabel">Manager</span><span class="seg">{manager}</span></span>'
        f'<span class="navgroup"><span class="glabel">Studio</span><span class="seg">{studio}</span></span>'
        f'<a class="needs{needs_sel}{alert}" href="/?view=needs">Needs You{count}</a></nav>'
    )


def render_framed_view(view, label, target):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Apollo HQ OS · {hq.esc(label)}</title><style>{BASE_CSS}</style></head>
<body class="framed">
<div class="topbar"><div class="brand"><h1><a href="/"><span class="ac">APOLLO</span> HQ OS</a></h1><small>· {hq.esc(label)}</small></div>{central_nav(selected=view)}</div>
<iframe title="{hq.esc(label)}" src="{target}"></iframe></body></html>'''


def render_manager_view(view):
    return render_framed_view(view, dict(MANAGER_VIEWS)[view], f"{MANAGER_DASHBOARD}/?view={view}")


def render_local_view(view):
    target = "/graph" if view == "graph" else f"/_hq?view={view}"
    return render_framed_view(view, dict(LOCAL_VIEWS)[view], target)


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
                     f'<h2>{esc(item["title"])}</h2><p class="meta">{esc(item["detail"])}</p><ul>{options}</ul>{action}</article>')

    rows = "".join(f'<div class="drow"><strong>{esc(item["title"])}</strong><small>{esc(item["detail"])}</small></div>'
                   for item in delegated) or '<div class="empty">Delegated queue is empty.</div>'
    notices = "".join(f'<div class="empty">{esc(note)}</div>' for note in ([manager_error] if manager_error else []) + notes if note)
    content = "".join(cards) or '<div class="empty">Nothing awaits an operator click. Delegated work continues below.</div>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Needs You · {len(pending)}</title><style>{BASE_CSS}</style></head><body>
<div class="topbar"><div class="brand"><h1><a href="/"><span class="ac">APOLLO</span> HQ OS</a></h1><small>· Needs You</small></div>{central_nav(len(pending), "needs")}</div>
<div class="needs-wrap">
<div class="needs-head"><h1>Needs You {badge(len(pending), "warn")}</h1><p>Only clickable operator decisions. Receipts land in social-ops/operator-decisions.jsonl.</p></div>
{notices}<div class="cards">{content}</div>
<h2 class="qhead">Delegated queue — PM ↔ Sol decide these {badge(len(delegated), "muted")}</h2>{rows}</div>
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


def load_skill_catalog():
    catalog, error = hq.read_json(SKILL_CATALOG)
    if not isinstance(catalog, dict) or not isinstance(catalog.get("skills"), list):
        return {"summary": {"skills": 0, "installed": 0, "claude_used": 0, "missing": 0, "gated": 0}, "skills": []}, error or "Skill catalog is invalid."
    return catalog, error


def render_hud():
    esc, badge, number = hq.esc, hq.badge, hq.number
    manager, manager_error = hq.load_manager()
    growth = hq.load_growth()
    operator, delegated, _ = collect_needs_v2(manager, growth)
    needs = [item for item in operator if not item.get("decision")]
    analytics, _ = hq.read_json(hq.ANALYTICS)
    rollup = (analytics or {}).get("rollup", {}) if isinstance(analytics, dict) else {}
    now = datetime.now(ICT)
    skill_catalog, skill_error = load_skill_catalog()
    skill_summary = skill_catalog.get("summary", {})

    vitals = "".join(
        f'<div class="vital"><small>{esc(label)}</small><strong class="num">{esc(number(rollup.get(key)))}</strong></div>'
        for key, label in (("youtubeWeeklyViews", "YouTube weekly views"), ("instagramObservedViews", "Instagram views"),
                           ("facebookObservedViews", "Facebook views"), ("tiktokObservedViews", "TikTok views")))
    if manager:
        metrics = manager.get("metrics", {})
        vitals += (f'<div class="vital"><small>Manager health</small><strong>{"OK" if manager.get("healthy") else "ISSUES"}</strong></div>'
                   f'<div class="vital"><small>Sol queue</small><strong class="num">{esc(metrics.get("sol_decision_queues", "—"))}</strong></div>')
    else:
        vitals += '<div class="vital warn"><small>Manager</small><strong>OFFLINE</strong></div>'
    vitals += (f'<div class="vital"><small>Needs You (clickable)</small><strong class="num">{len(needs)}</strong></div>'
               f'<div class="vital"><small>Delegated queue</small><strong class="num">{len(delegated)}</strong></div>')

    directives = "".join(f'<li><span class="t">{esc(item["title"])}</span><span class="d">{esc(item["detail"])}</span></li>'
                         for item in needs[:3]) or '<li><span class="t">No operator directives pending.</span></li>'

    trail = "".join(
        f'<div class="artifact">{badge(label)}<a href="{esc(obsidian_link(path))}">{esc(path.stem)}</a>'
        f'<time>{datetime.fromtimestamp(mtime, ICT):%m-%d %H:%M}</time></div>'
        for mtime, label, path in artifact_trail()) or '<div class="empty">No artifacts yet — run a skill.</div>'

    buttons = "".join(f'<button onclick="runSkill(\'{name}\')" id="btn-{name}">{esc(spec["label"])}</button>'
                      for name, spec in ACTIONS.items())
    skill_cards = []
    for item in skill_catalog.get("skills", []):
        name = str(item.get("name") or "unknown")
        mode = str(item.get("hud_mode") or "missing")
        count = int(item.get("claude_used_count") or 0)
        sources = ", ".join(item.get("source_kinds") or []) or "history only"
        gate = str(item.get("gate_reason") or "")
        desc = str(item.get("description") or "No description recorded.")
        used = f'<span class="uses num">×{count}</span>' if count else ""
        disabled = " disabled" if mode == "missing" else ""
        skill_cards.append(
            f'<button class="skill-entry {esc(mode)}" data-skill="{esc(name)}" data-gate="{esc(gate)}" '
            f'data-mode="{esc(mode)}" data-used="{1 if count else 0}" '
            f'title="{esc(mode.upper())} · {esc(sources)} — {esc(desc)}" onclick="loadSkill(this)"{disabled}>'
            f'<span class="top"><span class="dot"></span><span class="nm">{esc(name)}</span>{used}</span>'
            f'<span class="desc">{esc(desc)}</span></button>'
        )
    catalog_status = f'{esc(skill_summary.get("skills", 0))} workflows'
    skill_cards = "".join(skill_cards) or '<div class="empty">No catalog yet. Use Refresh skill catalog.</div>'
    if skill_error:
        skill_cards = f'<div class="empty">{esc(skill_error)}</div>' + skill_cards
    s = skill_summary
    chips = ('<div class="chips">'
             f'<button class="chip on" data-filter="all" onclick="setSkillFilter(\'all\',this)">All <b>{esc(s.get("skills", 0))}</b></button>'
             f'<button class="chip" data-filter="used" onclick="setSkillFilter(\'used\',this)">Used <b>{esc(s.get("claude_used", 0))}</b></button>'
             f'<button class="chip" data-filter="gated" onclick="setSkillFilter(\'gated\',this)">Gated <b>{esc(s.get("gated", 0))}</b></button>'
             f'<button class="chip" data-filter="missing" onclick="setSkillFilter(\'missing\',this)">Missing <b>{esc(s.get("missing", 0))}</b></button>'
             '</div>')
    schedule = "".join(f'<div class="lane"><span class="nm">{esc(name)}</span><span class="in">{esc(when)}</span>'
                       f'<span class="at">{at:%a %H:%M} ICT</span></div>'
                       for name, at, when in next_runs(now)) or '<div class="empty">No runs scheduled.</div>'
    prod, headline = latest_brief()
    wire = f'<div class="wire"><small>LATEST BRIEF · {esc(prod)}</small><p>{esc(headline)}</p></div>' if headline else ""
    backends = ", ".join(llm_config().get("backends", {}))
    backend_options = "".join(f'<option value="{esc(b)}">{esc(b)}</option>' for b in llm_config().get("backends", {}))

    nav = central_nav(len(needs), "hud")
    offline = f'<div class="empty">{esc(manager_error)}</div>' if manager_error else ""
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Apollo HQ OS</title><style>{BASE_CSS}</style></head><body>
<div class="topbar"><div class="brand"><h1><span class="ac">APOLLO</span> HQ OS</h1><small>{now:%A %Y-%m-%d %H:%M} ICT · localhost only</small></div>{nav}</div>
<div class="wrap"><div class="hud">
<div class="col">
  <div class="panel"><h2>Vitals</h2>{vitals}</div>
  <div class="panel"><h2>Schedule</h2>{schedule}</div>
  {f'<div class="panel"><h2>Wire</h2>{wire}</div>' if wire else ''}
</div>
<div class="col">
  <div class="panel apollo"><div class="orb"></div><div><div class="who">Apollo — analyst on duty</div><div class="sub">backends: <b>{esc(backends)}</b></div></div></div>
  {offline}
  <div class="panel console"><h2>Talk to any LLM<button class="new-chat" onclick="newChat()">New chat</button></h2>
    <div class="chat-log" id="llm-out"></div>
    <p id="llm-thinking" hidden>Apollo is thinking…</p>
    <textarea id="llm-prompt" placeholder="Ask Apollo — routes to the selected backend… (Enter to send, Shift+Enter for a newline)" onkeydown="llmKeydown(event)"></textarea>
    <div class="row"><select id="llm-backend" onchange="newChat()">{backend_options}</select><span class="spacer"></span>
    <button class="btn-primary" id="llm-send" onclick="askLLM()">Send</button></div></div>
  <div class="panel"><h2>Directives — your clicks only</h2><ol class="directives">{directives}</ol>
    <a class="decide-all" href="/?view=needs">Decide all {len(needs)} → delegated queue: {len(delegated)}</a></div>
  <div class="panel"><h2>Artifact trail</h2>{trail}</div>
</div>
<div class="col">
  <div class="panel"><h2>Safe one-click actions</h2><div class="actions">{buttons}</div><div id="jobs"></div></div>
  <div class="panel"><h2>Skills <small>{catalog_status}</small></h2>
    <div class="skill-tools">{chips}
      <input class="skill-search" id="skill-search" type="search" placeholder="Search skills…" oninput="filterSkills()"></div>
    <div class="skill-list" id="skill-list">{skill_cards}</div></div>
</div>
</div></div>
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
function loadSkill(button) {{
  const prompt = document.getElementById('llm-prompt');
  const gate = button.dataset.gate;
  prompt.value = 'Use $' + button.dataset.skill + ' for: ' + (gate ? '[GATED — ' + gate + '] ' : '');
  prompt.focus();
  prompt.scrollIntoView({{behavior: 'smooth', block: 'center'}});
}}
let skillFilter = 'all';
function setSkillFilter(f, el) {{
  skillFilter = f;
  document.querySelectorAll('.chip').forEach(c => c.classList.toggle('on', c === el));
  filterSkills();
}}
function filterSkills() {{
  const query = document.getElementById('skill-search').value.toLowerCase();
  document.querySelectorAll('.skill-entry').forEach(button => {{
    const okText = button.textContent.toLowerCase().includes(query);
    let okChip = true;
    if (skillFilter === 'used') okChip = button.dataset.used === '1';
    else if (skillFilter === 'gated') okChip = button.dataset.mode === 'gated';
    else if (skillFilter === 'missing') okChip = button.dataset.mode === 'missing';
    button.hidden = !(okText && okChip);
  }});
}}
let chatId = null;
function newChat() {{
  chatId = null;
  document.getElementById('llm-out').innerHTML = '';
}}
function appendMsg(role, text) {{
  const out = document.getElementById('llm-out');
  const row = document.createElement('div');
  row.className = 'msg ' + role;
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  bubble.textContent = text;
  row.appendChild(bubble);
  out.appendChild(row);
  out.scrollTop = out.scrollHeight;
}}
function llmKeydown(event) {{
  if (event.key === 'Enter' && !event.shiftKey) {{ event.preventDefault(); askLLM(); }}
}}
async function askLLM() {{
  const promptBox = document.getElementById('llm-prompt');
  const prompt = promptBox.value.trim();
  if (!prompt) return;
  const backend = document.getElementById('llm-backend').value;
  appendMsg('operator', prompt);
  promptBox.value = '';
  promptBox.disabled = true;
  document.getElementById('llm-send').disabled = true;
  document.getElementById('llm-thinking').hidden = false;
  try {{
    const res = await fetch('/llm', {{method: 'POST', headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{prompt, backend, chat_id: chatId}})}});
    const data = await res.json();
    chatId = data.chat_id || chatId;
    appendMsg('apollo', '[' + data.backend + '] ' + data.reply);
  }} catch (err) {{
    appendMsg('apollo', 'error: ' + err);
  }} finally {{
    promptBox.disabled = false;
    document.getElementById('llm-send').disabled = false;
    document.getElementById('llm-thinking').hidden = true;
    promptBox.focus();
  }}
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
        elif parsed.path == "/graph":
            if GRAPH_HTML.is_file():
                self._send(GRAPH_HTML.read_bytes())
            else:
                self._send('<body style="background:#070a07;color:#93a893;font:14px system-ui;padding:40px">'
                           'No graph yet — run "Rebuild knowledge graph" from the HUD.</body>')
        elif parsed.path == "/_hq":
            view = parse_qs(parsed.query).get("view", ["departments"])[0]
            self._send(hq.build_page(view))
        elif parsed.path == "/" and "view" in parse_qs(parsed.query):
            view = parse_qs(parsed.query)["view"][0]
            if view in dict(MANAGER_VIEWS):
                self._send(render_manager_view(view))
            elif view in dict(LOCAL_VIEWS) and view != "needs":
                self._send(render_local_view(view))
            else:
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
            chat_id_in = str(data.get("chat_id") or "") or None
            if not prompt:
                self._send(json.dumps({"backend": "-", "reply": "empty prompt", "chat_id": chat_id_in or ""}),
                          content_type="application/json")
                return
            backend, reply, chat_id = handle_llm_turn(prompt, data.get("backend"), chat_id_in)
            self._send(json.dumps({"backend": backend, "reply": reply, "chat_id": chat_id}), content_type="application/json")
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

    # graph view: framed page targets /graph, viewer file present
    assert 'src="/graph"' in render_local_view("graph"), "graph view must frame /graph"
    assert GRAPH_HTML.is_file(), "graphify-out/graph.html missing — run graphify export html"

    # build_transcript: pure function, output shape + capping
    transcript = build_transcript(
        [{"role": "operator", "text": "hi"}, {"role": "apollo", "text": "hello"}], "next")
    assert transcript == "Operator: hi\nApollo: hello\nOperator: next", "transcript shape wrong"
    long_history = [{"role": "operator", "text": "x" * 100} for _ in range(200)]
    capped = build_transcript(long_history, "tail", cap=500)
    assert len(capped) <= 500 and capped.endswith("Operator: tail"), "transcript cap broken"

    # chat bookkeeping: simulate two /llm-style calls with a monkeypatched ask_llm (no subprocess)
    global ask_llm
    real_ask_llm = ask_llm

    def fake_ask_llm(prompt, name, history, claude_session):
        session = f"sess-{len(history) // 2 + 1}" if name == "claude" else None
        return name, f"echo:{prompt}|hist={len(history)}", session

    ask_llm = fake_ask_llm
    try:
        CHATS.clear()
        backend, reply, chat_id = handle_llm_turn("hello", "claude", None)
        assert backend == "claude" and reply.startswith("echo:hello|hist=0"), "first turn wrong"
        assert "RECEIPT GATE:" in reply, "gate stamp missing from reply"
        assert chat_id in CHATS and CHATS[chat_id]["claude_session"] == "sess-1", "session not recorded"
        backend2, reply2, chat_id2 = handle_llm_turn("again", "claude", chat_id)
        assert chat_id2 == chat_id, "same backend must continue the chat, not start a new one"
        assert reply2.startswith("echo:again|hist=2"), "second turn didn't see prior history"
        assert len(CHATS[chat_id]["history"]) == 4, "history should hold 2 turns (4 entries) so far"
        backend3, reply3, chat_id3 = handle_llm_turn("switch", "codex", chat_id)
        assert chat_id3 != chat_id, "backend switch must start a new chat"

        CHATS[chat_id]["history"] = [{"role": "operator", "text": str(i)} for i in range(50)]
        handle_llm_turn("cap-check", "claude", chat_id)
        assert len(CHATS[chat_id]["history"]) == MAX_CHAT_HISTORY, "history must cap at MAX_CHAT_HISTORY"

        CHATS.clear()
        for i in range(MAX_CHATS + 5):
            handle_llm_turn(f"msg{i}", "claude", None)
        assert len(CHATS) <= MAX_CHATS, "CHATS must evict oldest beyond MAX_CHATS"
    finally:
        ask_llm = real_ask_llm

    # receipt gate: fail-closed on unreceipted numbers and dead paths
    assert receipt_gate("Sol queue is 16 [receipt: tools/hq_os.py]")[0] == "PASS", "live receipt must PASS"
    assert receipt_gate("Sol queue is 16")[0] == "BLOCK", "unreceipted number must BLOCK"
    assert receipt_gate("Sol queue is 16 [receipt: tools/nope_does_not_exist.py]")[0] == "BLOCK", "dead receipt must BLOCK"
    assert receipt_gate("Good evening, operator.")[0] == "PASS", "small talk must PASS"
    assert receipt_gate("Sol queue might be 16 — NO RECEIPT — unverified")[0] == "PASS", "flagged-unverified must PASS"
    assert receipt_gate("9 actions in `tools/hq_os.py:67-77`.")[0] == "PASS", "backtick path:line cite must PASS"
    assert receipt_gate("9 actions in `tools/ghost_file.py:1`.")[0] == "BLOCK", "dead backtick cite must BLOCK"

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
