from datetime import datetime, timezone
from types import SimpleNamespace

from tools import daily_lane


def test_tradingview_falls_back_to_chrome_web(monkeypatch, tmp_path):
    chrome = tmp_path / "Google" / "Chrome" / "Application" / "chrome.exe"
    chrome.parent.mkdir(parents=True)
    chrome.touch()
    monkeypatch.setenv("PROGRAMFILES", str(tmp_path))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.setattr(
        daily_lane.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout="")
    )
    launches = []
    monkeypatch.setattr(daily_lane.subprocess, "Popen", lambda argv, **kwargs: launches.append(argv))
    ports = iter((False, True))
    monkeypatch.setattr(daily_lane, "cdp_up", lambda: next(ports))
    monkeypatch.setattr(daily_lane.time, "sleep", lambda _: None)

    assert daily_lane.ensure_tradingview()
    assert launches == [[
        str(chrome),
        "--remote-debugging-port=9222",
        f"--user-data-dir={tmp_path / 'local' / 'TraderCockpit' / 'TradingView-Chrome'}",
        "--no-first-run",
        "--no-default-browser-check",
        "https://www.tradingview.com/chart/",
    ]]
    prompt = daily_lane.agent_prompt(tmp_path / "daily-test")
    assert "dedicated Google Chrome CDP profile" in prompt
    assert "operator's two indicators are absent, stop" in prompt


def test_paired_trigger_hours_resolve_to_market_close():
    summer = daily_lane.eastern_now(datetime(2026, 7, 30, 20, 0, tzinfo=timezone.utc))
    winter = daily_lane.eastern_now(datetime(2026, 1, 29, 21, 0, tzinfo=timezone.utc))

    assert summer.hour == winter.hour == 16


def test_lane_has_no_fixed_publish_hour():
    daily_lane.selftest()
