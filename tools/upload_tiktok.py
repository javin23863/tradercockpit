#!/usr/bin/env python3
"""Thin wrapper around makiisthenes/TiktokAutoUploader for publish.py.

The uploader is an UNOFFICIAL cookie/browser tool (clone lives outside this repo).
One-time, interactive: `python tools/upload_tiktok.py --login tradercockpit`.
The resulting cookie is written directly to operator credential custody.

Resolution order for the uploader checkout + its python:
  dir    : $TIKTOK_UPLOADER_DIR else ~/Desktop/TiktokAutoUploader else the legacy sibling checkout
  python : $TIKTOK_PYTHON        else  <dir>/.venv/Scripts/python.exe  else  "python"
User (TikTok account name given at login): $TIKTOK_USER else "tradercockpit".
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from tools.credential_custody import credential_path
except ModuleNotFoundError:  # direct `python tools/upload_tiktok.py` execution
    from credential_custody import credential_path

REPO = Path(__file__).resolve().parent.parent
_INSTALLED_DIR = Path.home() / "Desktop" / "TiktokAutoUploader"
_LEGACY_DIR = REPO.parent / "TiktokAutoUploader"
DEFAULT_DIR = _INSTALLED_DIR if _INSTALLED_DIR.exists() else _LEGACY_DIR
DEFAULT_USER = "tradercockpit"


def uploader_dir() -> Path:
    return Path(os.getenv("TIKTOK_UPLOADER_DIR", str(DEFAULT_DIR)))


def _python(d: Path) -> str:
    if os.getenv("TIKTOK_PYTHON"):
        return os.environ["TIKTOK_PYTHON"]
    venv = d / ".venv" / "Scripts" / "python.exe"       # win; POSIX below
    if venv.exists():
        return str(venv)
    venv_posix = d / ".venv" / "bin" / "python"
    if venv_posix.exists():
        return str(venv_posix)
    return "python"


def cookie_present(user: str = DEFAULT_USER) -> bool:
    """True only for an operator-held session, never a checkout-local cookie."""
    try:
        return credential_path(f"tiktok_session-{user}.cookie").is_file()
    except (OSError, ValueError):
        return False


def _uploader_env(user: str = DEFAULT_USER) -> dict[str, str]:
    """Point the uploader at operator custody and the operator's Chrome profile."""
    cookie = credential_path(f"tiktok_session-{user}.cookie")
    cookie.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["TIKTOK_COOKIES_DIR"] = str(cookie.parent)
    if os.name == "nt":
        local_app_data = Path(
            env.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
        )
        env.setdefault("TIKTOK_USE_REAL_PROFILE", "1")
        env.setdefault(
            "TIKTOK_CHROME_USER_DATA_DIR",
            str(local_app_data / "Google" / "Chrome" / "User Data"),
        )
        env.setdefault("TIKTOK_CHROME_PROFILE", "Default")
    return env


def refresh_auth(user: str = DEFAULT_USER) -> Path:
    """Capture the current Chrome TikTok session without uploading anything."""
    d = uploader_dir()
    if not d.exists():
        raise FileNotFoundError(f"TikTok uploader not found at {d}")
    cookie = credential_path(f"tiktok_session-{user}.cookie")
    proc = subprocess.run(
        [_python(d), "cli.py", "login", "-n", user],
        cwd=str(d),
        env=_uploader_env(user),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"TikTok session capture failed with exit code {proc.returncode}")
    if not cookie.is_file():
        raise RuntimeError("TikTok login completed without creating the custody cookie")
    return cookie


def probe_auth(user: str = DEFAULT_USER) -> dict:
    """The legacy uploader has no post read-back, so live publishing stays disabled."""
    if not cookie_present(user):
        return {"status": "absent", "ready": False, "readback": False}
    return {"status": "readback-unavailable", "ready": False, "readback": False}


def upload(video_path, title, user: str = DEFAULT_USER, ai_label: bool = True) -> dict:
    """Upload one local mp4 to TikTok. A clean exit remains unverified.

    `title` doubles as the caption — put hashtags here (TikTok reads tags from it).
    ai_label defaults True: our VO/visuals are AI-assisted, so disclose it (parallels
    the YouTube --synthetic flag). Set env TIKTOK_AI_LABEL=0 to override.
    """
    d = uploader_dir()
    if not d.exists():
        raise FileNotFoundError(
            f"TikTok uploader not found at {d}. Clone it and set TIKTOK_UPLOADER_DIR, "
            "or see ops/SEO-SOCIAL.md for setup."
        )
    if not cookie_present(user):
        raise RuntimeError(
            f"No TikTok session for '{user}'. Run one-time: "
            f"python tools/upload_tiktok.py --login {user}"
        )

    # The tool resolves -v only against its VideosDirPath/, so stage the file there.
    videos = d / "VideosDirPath"
    videos.mkdir(exist_ok=True)
    src = Path(video_path)
    staged = videos / src.name
    if staged.resolve() != src.resolve():
        shutil.copy2(src, staged)

    if os.getenv("TIKTOK_AI_LABEL") is not None:
        ai_label = os.environ["TIKTOK_AI_LABEL"] == "1"

    cmd = [_python(d), "cli.py", "upload", "-u", user, "-v", src.name,
           "-t", title, "-ai", "1" if ai_label else "0"]
    proc = subprocess.run(
        cmd,
        cwd=str(d),
        env=_uploader_env(user),
        capture_output=True,
        text=True,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0 or "[-] Video does not exist" in out or "Error" in out:
        raise RuntimeError(f"TikTok upload failed:\n{out[-800:]}")
    # The tool returns no stable post ID/URL and has no read-back API.
    return {
        "status": "uploaded-unverified",
        "id": None,
        "url": None,
        "platformResponse": {"uploaderExitCode": proc.returncode},
    }


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--login":
        u = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_USER
        refresh_auth(u)
        print(f"cookie[{u}]  : saved in operator credential custody")
        raise SystemExit(0)
    # ponytail: smallest runnable check — report readiness, don't post.
    u = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USER
    d = uploader_dir()
    print(f"uploader dir : {d}  ({'present' if d.exists() else 'MISSING'})")
    print(f"python       : {_python(d)}")
    print(
        f"cookie[{u}]  : "
        f"{'present — ready' if cookie_present(u) else f'MISSING — run tools/upload_tiktok.py --login {u}'}"
    )
