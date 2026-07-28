#!/usr/bin/env python3
"""Scheduled post-close lane: initialize -> Codex content -> readiness -> private runner."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

try:
    from tools.daily_production_init import eastern_now, production_path
    from tools.notify_telegram import send as send_telegram
except ModuleNotFoundError:  # direct `python tools/daily_lane.py` execution
    sys.path.insert(0, str(Path(__file__).parent))
    from daily_production_init import eastern_now, production_path
    from notify_telegram import send as send_telegram

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "OpenMontage" / ".venv" / "Scripts" / "python.exe"
INIT = ROOT / "tools" / "daily_production_init.py"
PREFLIGHT = ROOT / "tools" / "daily_preflight.py"
RUNNER = ROOT / "tools" / "daily_postclose.py"
VAULT = Path(r"C:\Users\MSI\Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit")
AGENT_TIMEOUT = 150 * 60
RUNNER_TIMEOUT = 3 * 60 * 60
TV_CDP_PORT = 9222
TV_LAUNCH_WAIT_S = 90
LOG_PATH: Path | None = None


def log(message: str) -> None:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    line = f"{stamp} {message}"
    print(line, flush=True)
    if LOG_PATH:
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def notify(message: str) -> None:
    """Best effort: Telegram failure is written to the run log, never hidden."""
    try:
        send_telegram(message)
        log("NOTIFY telegram sent")
    except BaseException as error:  # SystemExit is notify_telegram's fail-closed API
        log(f"NOTIFY FAILED: {type(error).__name__}: {error}")


def cdp_up(port: int = TV_CDP_PORT) -> bool:
    with socket.socket() as probe:
        probe.settimeout(1)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def ensure_tradingview() -> bool:
    """Charts-before-script needs TradingView Desktop on CDP :9222, and the lane's own
    'close TradingView before TTS' step leaves it down for the next day (2026-07-27:
    content stopped at the charts gate, no video shipped). Start it here, idempotently.
    """
    if cdp_up():
        log("STAGE tradingview OK already on CDP :%d" % TV_CDP_PORT)
        return True
    probe = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-AppxPackage TradingView.Desktop).InstallLocation"],
        capture_output=True, text=True, timeout=60,
    )
    exe = Path(probe.stdout.strip() or "nonexistent") / "TradingView.exe"
    # ponytail: WindowsApps blocks directory listing, so resolve the MSIX path via Get-AppxPackage.
    if not exe.is_file():
        log(f"STAGE tradingview MISSING TradingView Desktop (looked at {exe})")
        return False
    subprocess.Popen([str(exe), f"--remote-debugging-port={TV_CDP_PORT}"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(TV_LAUNCH_WAIT_S):
        if cdp_up():
            log("STAGE tradingview LAUNCHED")
            return True
        time.sleep(1)
    log(f"STAGE tradingview NO CDP after {TV_LAUNCH_WAIT_S}s")
    return False


def run_process(
    stage: str,
    argv: list[str],
    timeout: int,
    *,
    stdin_text: str | None = None,
    capture: bool = False,
) -> tuple[int, str]:
    """Run one stage with a logged PID and hard ceiling."""
    log(f"STAGE {stage} START timeout={timeout}s")
    output = ""
    try:
        if capture:
            process = subprocess.Popen(
                argv, cwd=ROOT, stdin=subprocess.PIPE if stdin_text is not None else None,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                encoding="utf-8", errors="replace", shell=False,
            )
            log(f"STAGE {stage} PID {process.pid}")
            output, _ = process.communicate(input=stdin_text, timeout=timeout)
        else:
            if LOG_PATH is None:
                raise RuntimeError("run log is not configured")
            with LOG_PATH.open("a", encoding="utf-8") as child_log:
                process = subprocess.Popen(
                    argv, cwd=ROOT, stdin=subprocess.PIPE if stdin_text is not None else None,
                    stdout=child_log, stderr=subprocess.STDOUT, text=True,
                    encoding="utf-8", errors="replace", shell=False,
                )
                log(f"STAGE {stage} PID {process.pid}")
                process.communicate(input=stdin_text, timeout=timeout)
        code = process.returncode
    except subprocess.TimeoutExpired:
        log(f"STAGE {stage} TIMEOUT; terminating PID {process.pid}")
        # Conservative automation choice: terminate only this exact child tree; never retry a
        # partly completed content/render stage without an operator reviewing its receipts.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"], cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
        )
        try:
            process.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
        code = 124
    except (OSError, RuntimeError) as error:
        log(f"STAGE {stage} SPAWN FAILED: {type(error).__name__}: {error}")
        code = 127

    if capture and output:
        for line in output.rstrip().splitlines():
            log(f"STAGE {stage} OUTPUT {line}")
    log(f"STAGE {stage} END exit={code}")
    return code, output


def agent_prompt(production: Path) -> str:
    return f"""Use the installed daily-news-video skill for the scheduled content step in:
{production}

Read .agents/skills/daily-news-video/SKILL.md and its canonical
.claude/skills/daily-news-video/SKILL.md, then drive that procedure against the real repository.
Follow all nine procedure steps where applicable to the content artifacts owed by
tools/daily_production_init.py; the wrapper owns runner actions (render, approval, publish).

Hard boundaries:
- Work only in this TraderCockpit checkout, its active ops vault, and this production folder.
- Use the real market-analysis and tradercockpit-free-media workflows at $0 external cost.
- Use OpenMontage\\.venv\\Scripts\\python.exe for every Python command.
- Charts-before-script is a hard order: capture completed-session working charts before vo.txt,
  and never cite an uncaptured chart.
- Run the existing claims and script-style gates. Do not weaken claims, editorial, visual_qa,
  script_style_gate, or script_approval.
- Exact-hash script approval is a hard gate. Never create, forge, or alter an approval receipt.
  If the current vo.txt lacks a valid approval for its exact hash, stop at absent/awaiting_human;
  do not write scene-plan.json or social-batch.json past that gate.
- Never run daily_postclose.py, render, publish, upload, register a task, commit, push, or pass
  --allow-public. Leave the runner-owned actions to this wrapper.
- Reuse existing assets and code; do not change pipeline/tooling files to make readiness pass.

Finish all safely reachable content work, preserve receipts, and report the exact blocker if the
approval gate or any evidence/quality gate stops the procedure. A partial folder is failure, not
permission to skip ahead.
"""


def codex_command(production: Path, codex: str) -> list[str]:
    command = [
        codex, "exec", "--strict-config", "-m", "gpt-5.6-sol",
        "-c", 'model_reasoning_effort="xhigh"',
        "-c", "sandbox_workspace_write.network_access=true",
        "-s", "workspace-write", "-C", str(ROOT),
    ]
    if VAULT.is_dir():
        command += ["--add-dir", str(VAULT)]
    command += [
        "--color", "never", "--output-last-message",
        str(production / "build" / "daily-agent-last-message.txt"), "-",
    ]
    return command


def run_chain(init_stage, agent_stage, check_stage, publish_stage, alert=notify) -> int:
    """Pure orchestration seam; injected stages make the safety branches self-testable."""
    for name, stage in (
        ("initialization", init_stage),
        ("agent content step", agent_stage),
        ("readiness check", check_stage),
        ("post-close runner", publish_stage),
    ):
        ok, detail = stage()
        if not ok:
            if detail.startswith("AWAITING_HUMAN"):
                alert(f"TraderCockpit daily lane {detail}. Nothing was published.")
                return 0
            alert(f"TraderCockpit daily lane BLOCKED at {name}: {detail}. Nothing was published.")
            return 1
    return 0


def wait_for_publish_hour(run_day) -> tuple[bool, str]:
    log("STAGE publish-hour-wait START target=18:00 US/Eastern")
    heartbeat = -1
    while True:
        now = eastern_now()
        if now.date() != run_day or now.hour > 18 or now.hour < 16:
            detail = f"missed 18:00 ET window; eastern_now={now:%Y-%m-%d %H:%M:%S}"
            log(f"STAGE publish-hour-wait END {detail}")
            return False, detail
        if now.hour == 18:
            log("STAGE publish-hour-wait END publish hour reached")
            return True, "18:00 ET reached"
        minute_bucket = now.minute // 5
        if minute_bucket != heartbeat:
            heartbeat = minute_bucket
            log(f"STAGE publish-hour-wait HEARTBEAT eastern_now={now:%Y-%m-%d %H:%M:%S}")
        time.sleep(60)


def selftest() -> None:
    assert os.environ["PYTHONIOENCODING"] == "utf-8"
    print("daily-lane UTF-8 smoke: \ufffd")

    def exercise(agent_ok: bool, ready: bool):
        calls, alerts = [], []

        def stage(name, result):
            return lambda: (calls.append(name) or result)

        code = run_chain(
            stage("init", (True, "initialized")),
            stage("agent", (agent_ok, "agent failed")),
            stage("check", (ready, "not ready")),
            stage("publish", (True, "runner called")),
            alerts.append,
        )
        return code, calls, alerts

    code, calls, alerts = exercise(False, True)
    assert code == 1 and calls == ["init", "agent"] and alerts, (code, calls, alerts)
    code, calls, alerts = exercise(True, False)
    assert code == 1 and calls == ["init", "agent", "check"] and alerts, (code, calls, alerts)
    code = run_chain(
        lambda: (True, "initialized"),
        lambda: (True, "content complete"),
        lambda: (False, "AWAITING_HUMAN exact-hash script approval"),
        lambda: (True, "runner called"),
        lambda message: None,
    )
    assert code == 0, code
    code, calls, alerts = exercise(True, True)
    assert code == 0 and calls == ["init", "agent", "check", "publish"] and not alerts

    publish = [str(PYTHON), str(RUNNER), "--at-publish-hour"]
    assert publish[-1] == "--at-publish-hour" and "--allow-public" not in publish
    command = codex_command(Path("productions/daily-test"), "codex.cmd")
    assert command[-1] == "-" and "workspace-write" in command and "gpt-5.6-sol" in command
    assert 'model_reasoning_effort="xhigh"' in command
    prompt = agent_prompt(Path("productions/daily-test"))
    assert prompt.index("Charts-before-script") < prompt.index("Exact-hash script approval")
    print("daily-lane self-test: 4/4 safety branches PASS")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--at-production-hour", action="store_true",
        help="stand down unless it is the 16:00 US/Eastern hour (for paired DST triggers)",
    )
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)
    if args.selftest:
        selftest()
        return 0

    now = eastern_now()
    run_day = now.date()
    production = production_path(now)
    global LOG_PATH
    LOG_PATH = ROOT / "productions" / "_runs" / f"daily-lane-{run_day:%Y-%m-%d}.log"
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log(f"LANE START eastern_day={run_day} executable={sys.executable}")

    resume = now.hour == 17 and production.is_dir()
    if args.at_production_hour and now.hour != 16 and not resume:
        # Conservative DST choice: paired local triggers are expected; the non-16:00 ET trigger
        # is redundant. At 17:00, an existing production gets one approval-resume attempt.
        log(f"LANE STAND_DOWN outside start/resume window; eastern_now={now:%Y-%m-%d %H:%M:%S}")
        return 0
    if Path(sys.executable).resolve() != PYTHON.resolve():
        detail = f"wrapper must run with {PYTHON}, got {sys.executable}"
        log(f"LANE BLOCKED {detail}")
        notify(f"TraderCockpit daily lane BLOCKED: {detail}. Nothing was published.")
        return 1

    def init_stage():
        if not ensure_tradingview():
            return False, (
                f"TradingView Desktop is not reachable on CDP :{TV_CDP_PORT}; "
                "charts-before-script would block the whole content step"
            )
        # Preflight AFTER the launch attempt (it probes, it does not start anything) and
        # BEFORE any content work: a night that cannot be narrated, uploaded or written to
        # disk must refuse in seconds, not stall for hours and look like 2026-07-27.
        code, output = run_process("preflight", [str(PYTHON), str(PREFLIGHT)], 180, capture=True)
        if code != 0:
            refusals = [line for line in output.splitlines() if "BLOCK" in line]
            return False, "preflight refused: " + "; ".join(refusals or [f"exit={code}"])
        code, output = run_process(
            "production-init", [str(PYTHON), str(INIT), "--init"], 60, capture=True,
        )
        expected = f"{production.name}: {'READY' if code == 0 else 'NOT READY'}"
        ok = code in (0, 1) and production.is_dir() and expected in output.splitlines()
        # --init exit 1 honestly means the newly minted folder is not ready yet.
        return ok, "initialized" if ok else (
            f"--init exit={code}; folder exists={production.is_dir()}; contract line absent"
        )

    def agent_stage():
        codex = shutil.which("codex.cmd") or shutil.which("codex")
        if not codex:
            return False, "codex CLI is absent from PATH"
        code, _ = run_process(
            "codex-content", codex_command(production, codex), AGENT_TIMEOUT,
            stdin_text=agent_prompt(production),
        )
        return code == 0, f"Codex exit={code}"

    def check_stage():
        code, output = run_process(
            "production-check", [str(PYTHON), str(INIT), "--check", "--json"],
            60, capture=True,
        )
        try:
            readiness = json.loads(output)
        except json.JSONDecodeError as error:
            return False, f"--check returned invalid JSON: {error}"
        missing_files = {item["file"] for item in readiness.get("missing", [])}
        missing = ", ".join(sorted(missing_files))
        ok = code == 0 and readiness.get("ready") is True
        approval_checkpoint = (
            missing_files == {"scene-plan.json", "social-batch.json"}
            and not (production / "script-approval.json").exists()
            and all((production / path).is_file() for path in (
                "vo.txt", "build/claims-gate.json", "build/script-style-audit.json",
            ))
        )
        if approval_checkpoint:
            return False, (
                f"AWAITING_HUMAN exact-hash script approval for {production / 'vo.txt'}; "
                "resume will run after script-approval.json exists"
            )
        return ok, "READY" if ok else f"NOT READY (exit={code}; missing={missing or 'unknown'})"

    def publish_stage():
        on_time, detail = wait_for_publish_hour(run_day)
        if not on_time:
            return False, detail
        # Public auto-publish stays off: this is the complete runner argv by construction.
        code, _ = run_process(
            "daily-postclose", [str(PYTHON), str(RUNNER), "--at-publish-hour"],
            RUNNER_TIMEOUT,
        )
        return code == 0, f"daily_postclose exit={code}"

    code = run_chain(init_stage, agent_stage, check_stage, publish_stage)
    log(f"LANE END exit={code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
