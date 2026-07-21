import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen


TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import hq_os  # noqa: E402


class CentralOsHttpTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.pinged = Path(self.tempdir.name) / "needs-you-pinged.json"
        self.decisions = Path(self.tempdir.name) / "operator-decisions.jsonl"
        self.manager = {
            "revision": 7,
            "generated_at": "2026-07-18T12:00:00Z",
            "healthy": True,
            "metrics": {"sol_decision_queues": 1},
            "nodes": [
                {
                    "id": "decision.example",
                    "title": "Example operator decision",
                    "lifecycle": "verify",
                    "blocked": False,
                    "data": {"needs_operator": True, "next_action": "Choose yes or no"},
                }
            ],
            "kanban": {state: [] for state in ("inbox", "ready", "active", "verify", "done", "parked")},
        }
        self.skills = {
            "summary": {"skills": 3, "installed": 2, "claude_used": 2, "missing": 1, "gated": 1},
            "skills": [
                {"name": "market-analysis", "description": "Analyze markets.", "source_kinds": ["project"], "available": True,
                 "claude_used_count": 4, "hud_mode": "prompt", "gate_reason": None},
                {"name": "tiktok-upload", "description": "Publish video.", "source_kinds": ["shared"], "available": True,
                 "claude_used_count": 1, "hud_mode": "gated", "gate_reason": "public upload and credentials"},
                {"name": "loop", "description": "History-only workflow.", "source_kinds": [], "available": False,
                 "claude_used_count": 0, "hud_mode": "missing", "gate_reason": "not installed"},
            ],
        }
        self.patches = [
            patch.object(hq_os, "PINGED", self.pinged),
            patch.object(hq_os, "DECISIONS", self.decisions),
            patch.object(hq_os, "_telegram", lambda _text: None),
            patch.object(hq_os.hq, "load_manager", lambda: (self.manager, None)),
            patch.object(hq_os.hq, "load_growth", lambda: {"valid": True, "experiments": []}),
            patch.object(hq_os.hq, "file_needs", lambda: ([], [])),
            patch.object(hq_os.hq, "experiment_needs", lambda _growth: ([], [])),
            patch.object(hq_os, "load_skill_catalog", lambda: (self.skills, None)),
        ]
        for item in self.patches:
            item.start()
        self.server = hq_os.ThreadingHTTPServer(("127.0.0.1", 0), hq_os.OSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        for item in reversed(self.patches):
            item.stop()
        self.tempdir.cleanup()

    def get(self, path):
        with urlopen(self.base_url + path, timeout=2) as response:
            self.assertEqual(response.status, 200)
            return response.read().decode("utf-8")

    def test_hud_is_the_single_navigation_surface_for_portfolio_views(self):
        page = self.get("/")

        for view in ("today", "kanban", "features", "risks", "prop", "needs"):
            self.assertIn(f'href="/?view={view}"', page)

    def test_manager_portfolio_views_stay_inside_the_central_os(self):
        page = self.get("/?view=features")

        self.assertIn("All Features", page)
        self.assertIn('src="http://127.0.0.1:8790/?view=features"', page)
        self.assertIn('href="/"', page)

    def test_local_workflow_views_keep_the_central_navigation(self):
        page = self.get("/?view=departments")

        self.assertIn("APOLLO HQ OS", page)
        self.assertIn('href="/?view=today"', page)
        self.assertIn('src="/_hq?view=departments"', page)

    def test_browsing_the_hud_does_not_write_or_notify(self):
        self.get("/")

        self.assertFalse(self.pinged.exists())
        self.assertFalse(self.decisions.exists())

    def test_hud_lists_codex_and_claude_skills_without_auto_running_them(self):
        page = self.get("/")

        self.assertIn('id="skill-search"', page)
        self.assertIn('data-skill="market-analysis"', page)
        self.assertIn("CLAUDE ×4", page)
        self.assertIn('class="skill-entry gated"', page)
        self.assertIn('data-skill="loop"', page)
        self.assertIn("onclick=\"loadSkill(this)\" disabled", page)


if __name__ == "__main__":
    unittest.main()
