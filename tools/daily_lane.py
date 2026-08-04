#!/usr/bin/env python3
"""Scheduled 16:00 US/Eastern lane: initialize -> Codex content -> readiness -> private runner."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

os.environ["PYTHONIOENCODING"] = "utf-8"
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")

try:
    from tools.daily_production_init import eastern_now, production_path
except ImportError:  # direct `python tools/daily_lane.py` execution
    sys.path.insert(0, str(Path(__file__).parent))
    from daily_production_init import eastern_now, production_path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / "OpenMontage" / ".venv" / "Scripts" / "python.exe"
INIT = ROOT / "tools" / "daily_production_init.py"
PREFLIGHT = ROOT / "tools" / "daily_preflight.py"
RUNNER = ROOT / "tools" / "daily_postclose.py"
VAULT = Path(r"C:\Users\MSI\Desktop\Obsidian Vault From VPS\tradercockpit\tradercockpit")
AGENT_TIMEOUT = 150 * 60
RUNNER_TIMEOUT = 3 * 60 * 60
LOG_PATH: Path | None = None


def log(message: str) -> None:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    line = f"{stamp} {message}"
    print(line, flush=True)
    if LOG_PATH:
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def notify(message: str) -> None:
    """Ping the operator. A lane that fails silently reads as a lane that never ran."""
    log(f"NOTIFY {message}")
    try:
        try:
            from tools.notify_telegram import send
        except ImportError:
            from notify_telegram import send
        send(f"TraderCockpit daily lane: {message}")
    # notify_telegram raises SystemExit (not Exception) on missing custody — catch both, or a
    # blocked lane exits 0 through the alert path and looks like a clean night.
    except (Exception, SystemExit) as error:
        log(f"NOTIFY telegram unavailable ({type(error).__name__}: {error}); log only")


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
- Charts come from the operator's OWN signed-in Chrome, reached with your Chrome browser
  capability (the chrome plugin / control-chrome skill). Do NOT start a browser yourself, do
  NOT attach to a CDP debugging port, and do NOT accept a second browser profile just because
  one is reachable: on 2026-08-03 a logged-out profile on :9222 was open, and taking it cost
  the entire night. Verify BEFORE capturing that the chart carries the operator's black theme
  and BOTH of his saved indicators. If either is missing, or the symbol carries an
  unauthenticated feed prefix (BATS:, SP_NAUTH:, NASDAQ_DLY:), stop and report the blocker —
  a guest chart is never a substitute.
- Do not create or draw trend lines or other custom chart overlays. Keep the operator's black
  chart and two indicators untouched; point out only the levels already visible on them.
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

    publish = [str(PYTHON), str(RUNNER)]
    assert "--at-publish-hour" not in publish and "--allow-public" not in publish
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

    if args.at_production_hour and now.hour != 16:
        log(f"LANE STAND_DOWN outside production hour; eastern_now={now:%Y-%m-%d %H:%M:%S}")
        return 0
    if Path(sys.executable).resolve() != PYTHON.resolve():
        detail = f"wrapper must run with {PYTHON}, got {sys.executable}"
        log(f"LANE BLOCKED {detail}")
        notify(f"TraderCockpit daily lane BLOCKED: {detail}. Nothing was published.")
        return 1

    def init_stage():
        # The lane does NOT open a browser. It used to launch its own Chrome profile on CDP
        # :9222 so the agent would find "a" TradingView — and on 2026-08-03 the agent found
        # exactly that: a logged-OUT profile serving the guest chart (BATS:AAPL, Volume only),
        # which correctly refused and cost the whole night. Codex reaches the operator's real
        # signed-in Chrome through its own extension, so handing it a second, emptier browser
        # only gave the wrong one a way to win. Chart eligibility is the agent's gate now.
        #
        # Preflight BEFORE any content work: a night that cannot be narrated, uploaded or
        # written to disk must refuse in seconds, not stall for hours like 2026-07-27.
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
        # Production starts at the close and completes when its gates and render complete.
        # Public auto-publish stays off: this is the complete runner argv by construction.
        code, _ = run_process(
            "daily-postclose", [str(PYTHON), str(RUNNER)],
            RUNNER_TIMEOUT,
        )
        return code == 0, f"daily_postclose exit={code}"

    code = run_chain(init_stage, agent_stage, check_stage, publish_stage)
    log(f"LANE END exit={code}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
