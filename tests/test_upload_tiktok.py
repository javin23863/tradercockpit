import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import upload_tiktok  # noqa: E402


class TikTokSessionCustodyTests(unittest.TestCase):
    def test_uploader_environment_uses_operator_custody(self):
        with tempfile.TemporaryDirectory() as folder:
            cookie = Path(folder) / "tiktok_session-tradercockpit.cookie"
            with patch.object(upload_tiktok, "credential_path", return_value=cookie):
                env = upload_tiktok._uploader_env()
            self.assertEqual(str(cookie.parent), env["TIKTOK_COOKIES_DIR"])
            if os.name == "nt":
                self.assertEqual("1", env["TIKTOK_USE_REAL_PROFILE"])
                self.assertEqual("Default", env["TIKTOK_CHROME_PROFILE"])

    def test_refresh_auth_captures_session_without_uploading(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            uploader = root / "uploader"
            uploader.mkdir()
            cookie = root / "custody" / "tiktok_session-tradercockpit.cookie"

            def fake_run(command, **kwargs):
                self.assertEqual("login", command[2])
                self.assertEqual(str(cookie.parent), kwargs["env"]["TIKTOK_COOKIES_DIR"])
                cookie.write_text("test-cookie", encoding="utf-8")
                return subprocess.CompletedProcess(command, 0)

            with patch.object(upload_tiktok, "uploader_dir", return_value=uploader), patch.object(
                upload_tiktok, "credential_path", return_value=cookie
            ), patch.object(upload_tiktok, "_python", return_value="python"), patch.object(
                upload_tiktok.subprocess, "run", side_effect=fake_run
            ):
                self.assertEqual(cookie, upload_tiktok.refresh_auth())

    def test_upload_reads_the_same_custody_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            uploader = root / "uploader"
            uploader.mkdir()
            video = root / "clip.mp4"
            video.write_bytes(b"video")
            cookie = root / "custody" / "tiktok_session-tradercockpit.cookie"
            cookie.parent.mkdir()
            cookie.write_text("test-cookie", encoding="utf-8")
            completed = subprocess.CompletedProcess([], 0, stdout="", stderr="")

            with patch.object(upload_tiktok, "uploader_dir", return_value=uploader), patch.object(
                upload_tiktok, "credential_path", return_value=cookie
            ), patch.object(upload_tiktok, "_python", return_value="python"), patch.object(
                upload_tiktok.subprocess, "run", return_value=completed
            ) as run:
                upload_tiktok.upload(video, "caption")

            self.assertEqual(str(cookie.parent), run.call_args.kwargs["env"]["TIKTOK_COOKIES_DIR"])


if __name__ == "__main__":
    unittest.main()
