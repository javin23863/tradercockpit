#!/usr/bin/env python3
"""Thin wrapper around makiisthenes/TiktokAutoUploader for publish.py.

The uploader is an UNOFFICIAL cookie/browser tool (clone lives outside this repo).
One-time, interactive: `python cli.py login -n tradercockpit` (opens Chrome).
After that, cookies in CookiesDir/ let uploads run headless-ish.

Resolution order for the uploader checkout + its python:
  dir    : $TIKTOK_UPLOADER_DIR  else  ../TiktokAutoUploader (sibling of this repo)
  python : $TIKTOK_PYTHON        else  <dir>/.venv/Scripts/python.exe  else  "python"
User (TikTok account name given at login): $TIKTOK_USER else "tradercockpit".
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent          # OpenMontage-Skill/
DEFAULT_DIR = REPO.parent / "TiktokAutoUploader"        # sibling checkout
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
    """True if a login session cookie exists for `user` (dry-run readiness)."""
    d = uploader_dir()
    if not d.exists():
        return False
    cookies = d / "CookiesDir"
    return cookies.is_dir() and any(
        p.name == f"tiktok_session-{user}.cookie" for p in cookies.iterdir()
    )


def upload(video_path, title, user: str = DEFAULT_USER, ai_label: bool = True) -> str:
    """Upload one local mp4 to TikTok. Returns a status string. Raises on hard failure.

    `title` doubles as the caption — put hashtags here (TikTok reads tags from it).
    ai_label defaults True: our VO/visuals are AI-assisted, so disclose it (parallels
    the YouTube --synthetic flag). Set env TIKTOK_AI_LABEL=0 to override.
    """
    d = uploader_dir()
    if not d.exists():
        raise FileNotFoundError(
            f"TikTok uploader not found at {d}. Clone it and set TIKTOK_UPLOADER_DIR, "
            "or see SEO-SOCIAL.md for setup."
        )
    if not cookie_present(user):
        raise RuntimeError(
            f"No TikTok session for '{user}'. Run one-time: "
            f'cd "{d}" && python cli.py login -n {user}'
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
    proc = subprocess.run(cmd, cwd=str(d), capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    if proc.returncode != 0 or "[-] Video does not exist" in out or "Error" in out:
        raise RuntimeError(f"TikTok upload failed:\n{out[-800:]}")
    # tool prints progress, not a stable URL; success = clean exit
    return f"TikTok: uploaded '{src.name}' as @{user} (check the app for the live link)"


if __name__ == "__main__":
    # ponytail: smallest runnable check — report readiness, don't post.
    u = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USER
    d = uploader_dir()
    print(f"uploader dir : {d}  ({'present' if d.exists() else 'MISSING'})")
    print(f"python       : {_python(d)}")
    print(f"cookie[{u}]  : {'present — ready' if cookie_present(u) else 'MISSING — run cli.py login'}")
